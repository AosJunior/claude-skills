"""Funções comuns da /sonorizar. Só biblioteca padrão; roda igual no Mac e no Windows."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# achar a marca, caminhos marca/ e âncoras na fala: contrato.py, igual nas 4 skills do kit
import contrato
from contrato import ErroContrato, achar_marca, caminho, chave, segundos, texto_marca  # noqa: F401

AUDIO = {".wav", ".mp3", ".m4a", ".aac", ".aif", ".aiff", ".flac", ".ogg", ".opus"}
VIDEO = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}
SR = 48000


def utf8():
    """Saída em UTF-8 até no console do Windows (senão "→" e acentos derrubam o script)."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


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


def ler_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


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


class Ancoras:
    """As âncoras do contrato (contrato.py) pelo palavras-corte.json. `tempo` levanta ErroContrato (um ValueError)
    com a mensagem pronta; `arquivo` é o palavras-corte.json usado (None sem ele)."""

    def __init__(self, palavras_json=None):
        self.a = contrato.Ancoras.de_corte(palavras_json)
        self.arquivo = palavras_json if self.a.sem_fala is None else None

    def tempo(self, v, borda="inicio"):
        """Segundos no vídeo cortado (encostados na emenda a menos de 3 quadros, como a /inserir faz com as camadas).
        `borda` = "fim" para `ate`: "F15" e "F15:palavra" valem o fim."""
        return self.a.tempo(v, fim=(borda == "fim"))


def ler_creditos(arq):
    """Tabela de créditos em Markdown -> {nome do arquivo: {titulo, autor, fonte, licenca}}.

    Lê a tabela que tem a coluna "Arquivo" (e as que existirem entre Título, Autor, Fonte, ID e Licença)."""
    arq = Path(arq)
    if not arq.is_file():
        return {}
    nomes = {"arquivo": "arquivo", "titulo": "titulo", "autor": "autor", "artista": "autor", "fonte": "fonte",
             "licenca": "licenca", "id": "id"}
    out, cab = {}, None
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if not linha.strip().startswith("|"):
            cab = None
            continue
        cel = [c.strip() for c in linha.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cel if c):
            continue
        if cab is None:
            cab = [nomes.get(chave(c)) for c in cel]
            continue
        d = {k: c.strip("`").strip() for k, c in zip(cab, cel) if k}
        if d.get("arquivo"):
            if d.get("id") and d.get("licenca") and d["id"] not in d["licenca"]:
                d["licenca"] += f" · ID {d['id']}"
            out[Path(d.pop("arquivo")).name.lower()] = d
    return out
