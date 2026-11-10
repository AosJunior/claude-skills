"""Funções comuns dos scripts da /reel-novela. Rodam igual no Mac e no Windows.

A parte de texto e ffmpeg usa só a biblioteca padrão. As funções de áudio (`ler_audio`, `momentaneo`...) importam
numpy e scipy só quando são chamadas: quem as usa declara essas dependências no próprio cabeçalho.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

AUDIO = {".wav", ".mp3", ".m4a", ".aac", ".aif", ".aiff", ".flac", ".ogg", ".opus"}
VIDEO = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}
SR = 48000

# Cadeia da voz na mixagem: só passa-altas e compressor suave (2:1). Tratamento mais pesado subiu o ruído e foi
# reprovado. O medir.py e o ganho_voz.py refazem a mesma cadeia para comparar a entrega com a narração.
CADEIA_VOZ = "highpass=f=70,acompressor=threshold=-24dB:ratio=2:attack=8:release=200:makeup=1"
VOZ_LUFS = -16.0


def utf8():
    """Saída em UTF-8 até no console do Windows (senão "→" e acentos derrubam o script)."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def ajuda(doc):
    """Com -h ou --help, imprime a docstring do script e sai."""
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(doc)
        sys.exit(0)


def rodar(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def ff(args):
    r = rodar(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y", *args])
    if r.returncode != 0:
        sair("O ffmpeg parou com erro:\n" + r.stderr.strip()[-1500:])
    return r


def sair(msg, codigo=1):
    print(msg)
    sys.exit(codigo)


def checar_ffmpeg():
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sair("Falta o ffmpeg neste computador. Mac: brew install ffmpeg · Windows: winget install Gyan.FFmpeg "
             "(no Windows, feche e abra o Claude depois de instalar).")


def checar_node():
    if not shutil.which("node"):
        sair("Falta o Node neste computador (o mesmo do HyperFrames). Mac: brew install node · "
             "Windows: winget install OpenJS.NodeJS.LTS")


def ler_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def gravar_json(p, dados, indent=1):
    Path(p).write_text(json.dumps(dados, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def segundos(v):
    """83.4, "83.4", "01:23,40" ou "1:23.4" -> segundos."""
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(",", ".")
    if ":" in t:
        m, s = t.rsplit(":", 1)
        h = 0
        if ":" in m:
            h, m = m.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    return float(t)


def fmt_tempo(s):
    cs = int(round(max(0.0, float(s)) * 100))
    return f"{cs // 6000:02d}:{cs // 100 % 60:02d},{cs % 100:02d}"


def fmt_num(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


def sondar(arq):
    """Duração e faixas de um arquivo de áudio ou vídeo."""
    r = rodar(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", arq])
    if r.returncode != 0:
        sair(f"Não consegui abrir o arquivo (pode estar incompleto ou ainda baixando): {arq}")
    d = json.loads(r.stdout or "{}")
    ss = d.get("streams", [])
    a = next((s for s in ss if s.get("codec_type") == "audio"), None)
    v = next((s for s in ss if s.get("codec_type") == "video"
              and not (s.get("disposition") or {}).get("attached_pic")), None)
    return {
        "duracao": float((d.get("format") or {}).get("duration") or 0),
        "tem_audio": a is not None,
        "tem_video": v is not None,
        "canais": int((a or {}).get("channels") or 0),
        "largura": int((v or {}).get("width") or 0),
        "altura": int((v or {}).get("height") or 0),
    }


def medir(arq=None, filtro=None, entradas=None):
    """Loudness integrado (LUFS), pico verdadeiro (dBTP) e pico de amostra (dBFS) com o ebur128.

    `entradas` + `filtro` medem a saída de um filter_complex (rótulo final [m]) sem gravar arquivo."""
    if entradas is None:
        entradas = ["-i", str(arq)]
        filtro = "[0:a:0]anull[m]"
    r = rodar(["ffmpeg", "-hide_banner", "-nostdin", "-nostats", *entradas, "-filter_complex",
               f"{filtro};[m]ebur128=peak=true+sample:framelog=quiet[o]", "-map", "[o]", "-f", "null", "-"])
    resumo = r.stderr[r.stderr.rfind("Summary:"):]

    def pega(rotulo):
        m = re.search(rotulo + r":\s*(-?[0-9.]+|-inf)", resumo)
        return float(m.group(1)) if m and m.group(1) != "-inf" else -99.0
    return {"lufs": pega(r"\bI"), "true_peak": pega(r"True peak:\s*Peak"), "pico": pega(r"Sample peak:\s*Peak")}


# ---------------------------------------------------------------------------------------------------------------
# texto
# ---------------------------------------------------------------------------------------------------------------
def sem_acento(t):
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", sem_acento(str(t)).lower()).strip("-") or "x"


# ---------------------------------------------------------------------------------------------------------------
# chave do ElevenLabs: do ambiente ou de um arquivo; nunca vai para a tela
# ---------------------------------------------------------------------------------------------------------------
def chave_eleven(arquivo=None):
    """ELEVENLABS_API_KEY do ambiente ou de um arquivo (só a chave, ou linhas NOME=valor, com ou sem `export`)."""
    if arquivo:
        p = Path(arquivo).expanduser()
        if not p.is_file():
            sair(f"Não achei o arquivo da chave: {p}")
        linhas = p.read_text(encoding="utf-8", errors="replace").splitlines()
        for linha in linhas:
            linha = linha.strip()
            if linha.startswith("export "):
                linha = linha[7:].strip()
            if linha.startswith("ELEVENLABS_API_KEY="):
                return linha.split("=", 1)[1].strip().strip('"').strip("'")
        soltas = [x.strip() for x in linhas if x.strip() and not x.strip().startswith("#") and "=" not in x]
        if len(soltas) == 1:
            return soltas[0]
        sair(f"O arquivo {p.name} não tem a linha ELEVENLABS_API_KEY=...")
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not k:
        sair("Falta a chave do ElevenLabs. Defina ELEVENLABS_API_KEY no ambiente ou passe --chave-arquivo "
             "<arquivo com a linha ELEVENLABS_API_KEY=...>. A chave nunca é impressa.")
    return k


# ---------------------------------------------------------------------------------------------------------------
# áudio (numpy e scipy entram só aqui)
# ---------------------------------------------------------------------------------------------------------------
def ler_audio(arq, filtro=None, ini=None, dur=None, canais=2, sr=SR):
    """Áudio em float32, forma (amostras, canais), na taxa `sr`."""
    import numpy as np
    cmd = ["ffmpeg", "-v", "error", "-nostdin"]
    if ini:
        cmd += ["-ss", f"{ini:.3f}"]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", str(arq)]
    if filtro:
        cmd += ["-af", filtro]
    cmd += ["-ac", str(canais), "-ar", str(sr), "-f", "f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        sair(f"Não consegui ler o áudio de {arq}:\n" + r.stderr.decode("utf-8", "replace")[-800:])
    return np.frombuffer(r.stdout, dtype=np.float32).reshape(-1, canais).copy()


def gravar_audio(arq, x, sr=SR, codec="pcm_f32le"):
    """Grava um array (amostras, canais) em WAV."""
    import numpy as np
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = x[:, None]
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "f32le", "-ar", str(sr), "-ac", str(x.shape[1]),
                    "-i", "pipe:0", "-c:a", codec, str(arq)], input=np.ascontiguousarray(x).tobytes(), check=True)


def _ebur128(x, sr=SR):
    import numpy as np
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = x[:, None]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-nostdin", "-f", "f32le", "-ar", str(sr), "-ac",
                        str(x.shape[1]), "-i", "pipe:0", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       input=np.ascontiguousarray(x).tobytes(), capture_output=True)
    s = r.stderr.decode("utf-8", "replace")
    return s[s.rfind("Summary:"):]


def lufs_de(x, sr=SR):
    """Loudness integrado de um array (ebur128 do ffmpeg)."""
    m = re.search(r"\bI:\s*(-?[0-9.]+)", _ebur128(x, sr))
    return float(m.group(1)) if m else -99.0


def pico_tp_de(x, sr=SR):
    """Pico verdadeiro (dBTP) de um array (ebur128 do ffmpeg)."""
    m = re.search(r"Peak:\s*(-?[0-9.]+|-inf)", _ebur128(x, sr))
    return float(m.group(1)) if m and m.group(1) != "-inf" else -99.0


def db_para_lin(db):
    import numpy as np
    return 10 ** (np.asarray(db) / 20)


HOP = 0.01   # passo das medidas de loudness momentâneo (s)


def momentaneo(x, sr=SR, hop=HOP):
    """Loudness momentâneo (janela de 400 ms, ponderação K da BS.1770) a cada `hop`, centrado no instante. Em dB."""
    import numpy as np
    from scipy.signal import lfilter
    if sr != 48000:
        sair("momentaneo() espera áudio a 48 kHz.")
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    y = lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)
    p = (y ** 2).sum(1)
    c = np.concatenate([[0.0], np.cumsum(p)])
    h, j = int(hop * sr), int(0.4 * sr)
    centros = np.arange(0, len(p), h)
    a = np.clip(centros - j // 2, 0, len(p))
    b = np.clip(centros + j // 2, 0, len(p))
    e = (c[b] - c[a]) / j
    return -0.691 + 10 * np.log10(e + 1e-12)


def media_energia(db):
    """Média em energia de valores em dB."""
    import numpy as np
    db = np.asarray(db, dtype=np.float64)
    return float(10 * np.log10(np.mean(10 ** (db / 10)))) if db.size else -99.0


def voz_tratada(arq_voz):
    """A narração com a cadeia da mixagem (passa-altas e compressor suave), levada a -16 LUFS, em estéreo."""
    v = ler_audio(arq_voz, CADEIA_VOZ)
    return v * float(db_para_lin(VOZ_LUFS - lufs_de(v)))


def voz_da_entrega(entrega, voz, inicio=0.0):
    """(entrega, voz tratada) alinhadas: lê a entrega, corta a voz em `inicio` (prévia de trecho) e acha o atraso do
    AAC por correlação. `voz` é o caminho da narração ou a voz tratada já lida (mono). Arrays em float64."""
    import numpy as np
    from scipy.signal import correlate
    y = ler_audio(entrega).astype(np.float64)
    if isinstance(voz, (str, Path)):
        voz = voz_tratada(voz).astype(np.float64)[:, 0]
    v = voz[int(round(inicio * SR)):]
    n = min(len(y), len(v))
    if n < SR:
        sair(f"{Path(entrega).name}: menos de 1 s em comum com a narração. Confira o --inicio.")
    y, v = y[:n], v[:n]
    e = uniform_energia(v, int(0.5 * SR))
    c0 = int(np.argmax(e))                      # meio segundo de fala forte, no meio de uma janela de 10 s
    a, b = max(0, c0 - 5 * SR), min(n, c0 + 5 * SR)
    cc = correlate(y.mean(1)[a:b], v[a:b], mode="full", method="fft")
    lags = np.arange(-(b - a) + 1, b - a)
    m = np.abs(lags) <= 4800                    # até 100 ms
    lag = int(lags[m][np.argmax(cc[m])])
    return np.roll(y, -lag), v, lag


def uniform_energia(x, janela):
    import numpy as np
    from scipy.ndimage import uniform_filter1d
    return uniform_filter1d(np.asarray(x, dtype=np.float64) ** 2, janela)


def segmentos_de_fala(v, minimo_pausa=0.1):
    """Máscara de fala a cada HOP, pela energia da própria narração (voz de IA, sem ruído): quadros de 10 ms acima de
    35 dB abaixo do nível forte da fala, com buracos menores que `minimo_pausa` fechados."""
    import numpy as np
    h = int(HOP * SR)
    k = len(v) // h
    rms = 10 * np.log10(np.mean(np.asarray(v[:k * h], dtype=np.float64).reshape(k, h) ** 2, axis=1) + 1e-20)
    return fechar_buracos(rms > np.percentile(rms, 95) - 35, minimo_pausa)


def fechar_buracos(fala, minimo_pausa):
    """Fecha os buracos da máscara de fala (a cada HOP) menores que `minimo_pausa` s (oclusiva, fim de sílaba)."""
    fala = fala.copy()
    k, i = len(fala), 0
    while i < k:
        if not fala[i]:
            j = i
            while j < k and not fala[j]:
                j += 1
            if 0 < i and j < k and (j - i) * HOP < minimo_pausa:
                fala[i:j] = True
            i = j
        else:
            i += 1
    return fala


def arquivo_palavras(voz, args):
    """O palavras-voz.json: o de --palavras, ou o que estiver ao lado da narração (ou em briefings/ ao lado dela)."""
    if "--palavras" in args:
        p = Path(args[args.index("--palavras") + 1]).expanduser()
        if not p.is_file():
            sair(f"Não achei {p}")
        return p
    d = Path(voz).expanduser().resolve().parent
    for p in (d / "palavras-voz.json", d / "briefings" / "palavras-voz.json"):
        if p.is_file():
            return p
    return None
