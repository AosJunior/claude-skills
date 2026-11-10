# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy"]
# ///
"""/reel-novela, mixagem: a voz na frente, a trilha nivelada por uma curva-alvo e os efeitos, em -14 LUFS.

Uso:
  uv run "<skill>/scripts/mixar.py" <mix.json>                  vídeo inteiro com trilha → "saida"
  uv run "<skill>/scripts/mixar.py" <mix.json> --sem-trilha     voz e efeitos, sem a música → "saida_sem_trilha"
  uv run "<skill>/scripts/mixar.py" <mix.json> --trecho 0 8     só esse pedaço, para ouvir rápido → "saida_trecho"
  (--trecho e --sem-trilha combinam.)

Cadeia:
- Voz: só passa-altas (70 Hz) e compressor suave (2:1), levada a -16 LUFS na narração inteira.
- Trilha: um nivelador leva o loudness momentâneo (400 ms) da música a uma curva-alvo em LU relativos à voz:
  "sob_fala" (-20,3) durante a fala; "respiro" (-7,5) nos respiros de 0,5 s ou mais, nas viradas e depois da última
  palavra; "mergulho" (-36) nos 0,35 s antes de cada revelação, e a música volta no ataque dela. Num respiro curto o
  patamar sobe até -5 para a janela de 400 ms ler o respiro. A curva calculada fica em .dados/curva-trilha.json.
- Efeitos: o pico de cada um vai a -12 + vol dBFS. O barramento dos efeitos tem limitador (teto_efeitos, -1 dBFS),
  que também cede onde a soma com voz e trilha passaria do teto final. A voz e a trilha não passam por ele.
- Master: ganho linear até -14 LUFS (medido com o ebur128, como um loudnorm linear) e limitador de pico
  verdadeiro (-1,5 dBTP, com 0,3 dB de folga para o AAC). Nada de compressão no master.
Os níveis de referência saem dos arquivos inteiros, então um --trecho sai com o mesmo nível relativo do vídeo
inteiro. A imagem é copiada sem recompressão; a saída é gravada num temporário e trocada no fim.

mix.json (caminhos relativos à pasta dele; o padrão é sequencia/som/mix.json):
{
  "video": "../motion/renders/<slug>-1080.mp4",
  "voz": "../motion/narracao.wav",
  "saida": "../exports/<slug>-epNN.mp4",
  "saida_sem_trilha": "medida/<slug>-epNN-sem-trilha.mp4",
  "trilha": {
    "arquivo": "trilha/trilha-editada.wav",
    "palavras": "../motion/briefings/palavras-voz.json",
    "viradas": "../../brutos/narracao/narracao-blocos.json",
    "revelacoes": [12.4, 31.0, 58.2]
  },
  "efeitos": "efeitos.json"
}
  (<slug>: o nome da pasta da série sem o AAAA-MM-DD- do começo, como o entregar.py nomeia o render. A saída sem
  trilha é só para medir: fica em sequencia/som/medida/, fora de exports/, que guarda só o final.)
Opcionais:
  saida_sem_trilha  sem ele, o --sem-trilha grava em medida/<nome da "saida">-sem-trilha.mp4, ao lado do mix.json
  saida_trecho      prévia do --trecho (padrão ../previas/previa-trecho.mp4; "-sem-trilha" no nome sem a música)
  teto_efeitos      teto do barramento dos efeitos em dBFS (padrão -1)
  trilha.viradas    lista de instantes (s, tempo real) ou o narracao-blocos.json (vale o "fim" de cada bloco
                    menos o último): a pausa entre blocos sobe como respiro mesmo se for menor que 0,5 s
  trilha.revelacoes instantes (s, tempo real) das revelações: mergulho antes, a música volta no ataque
  trilha.crescendos [[ini, fim, LU no início, LU no fim], ...]: troca o "sob_fala" por uma rampa (ex.: o CTA)
  trilha.fora       [[ini, fim], ...] em segundos de tempo real: a música sai (alvo -60 LU, com a mesma rampa nas
                    bordas) e volta depois. Vale para o trecho em que outra voz toca sem música (a aula da novela):
                    ali não há palavras no palavras-voz.json, e sem isto a curva trataria o trecho como respiro e
                    subiria a música. É aplicado por último, depois das revelações.
  trilha.inicio     segundo da música que cai no 0 do vídeo (padrão 0)
  trilha.fim        onde a música acaba (padrão: a duração do vídeo; num piloto curto, a do vídeo inteiro)
  trilha.fade_in    0,05 s · trilha.fade_out 0,5 s
  trilha.sob_fala -20,3 · trilha.respiro -7,5 · trilha.mergulho -36 · trilha.pausa_min 0,495 (LU e s)
  trilha.alvo       curva pronta [[t, LU], ...] ou o caminho de um JSON com ela, no lugar da calculada
Cada efeito do efeitos.json (montado pelo efeitos.py): {"t", "som", "vol", "dur"?, "so_com_trilha"?, "motivo"}.
"""
import os
import platform
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True   # sem __pycache__ dentro da skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (HOP, SR, ajuda, checar_ffmpeg, db_para_lin, ff, gravar_audio, gravar_json, ler_audio,  # noqa: E402
                   ler_json, lufs_de, medir, momentaneo, pico_tp_de, sair, segundos, sondar, utf8, voz_tratada)
ajuda(__doc__)   # --help sai antes de importar numpy: funciona sem o uv ter baixado nada
import numpy as np  # noqa: E402

ALVO_LUFS, ALVO_TP = -14.0, -1.5
FORA_LU = -60.0        # alvo da música nas janelas "fora" (a música sai)
TP_MARGEM = 0.3        # o AAC da entrega pode passar uns décimos do pico do WAV
PICO_EFEITO = -12.0    # pico de cada efeito: -12 + vol dBFS

PADRAO_TRILHA = {"sob_fala": -20.3, "respiro": -7.5, "mergulho": -36.0, "pausa_min": 0.495,
                 "folga": 0.15, "rampa": 0.04, "janela": 0.4, "antes": 0.35, "rampa_mergulho": 0.06,
                 "teto_respiro_curto": -5.0}


# ---------------------------------------------------------------------------------------------------------------
# curva-alvo da trilha
# ---------------------------------------------------------------------------------------------------------------
def ler_viradas(v, cam):
    """Instantes das viradas de cena: a lista do mix.json, ou o fim de cada bloco do narracao-blocos.json cujo bloco
    seguinte é de outra cena (sem "cena" nos blocos, todo fim de bloco conta)."""
    if not v:
        return []
    if isinstance(v, str):
        blocos = ler_json(cam(v))
        return [float(a["fim"]) for a, b in zip(blocos, blocos[1:])
                if a.get("cena") is None or a.get("cena") != b.get("cena")]
    return [float(x) for x in v]


def curva_alvo(palavras, dur, viradas, revelacoes, crescendos, P, fora=()):
    """Curva [[t, LU relativos à voz], ...] a cada 10 ms, compactada nos pontos onde a inclinação muda.
    `fora`: janelas [ini, fim] em que a música sai (-60 LU), aplicadas depois de tudo."""
    ts = np.round(np.arange(int(round(dur * 100)) + 1) / 100, 2)
    base = np.full(len(ts), P["sob_fala"], dtype=float)
    for t0, t1, a, b in crescendos:
        m = (ts >= t0) & (ts <= t1)
        base[m] = a + (b - a) * (ts[m] - t0) / max(t1 - t0, 1e-6)
    g = base.copy()
    w = sorted(palavras, key=lambda p: p["ini"])
    pausas = []
    for a, b in zip(w, w[1:]):
        gap = b["ini"] - a["fim"]
        virada = any(a["fim"] - 0.3 <= v <= b["ini"] + 0.3 for v in viradas)
        if gap >= P["pausa_min"] or (virada and gap > 2 * (P["folga"] + P["rampa"])):
            pausas.append((a["fim"], b["ini"]))
    pausas.append((w[-1]["fim"], dur + 1.0))   # o fim: a música sobe depois da última palavra
    respiros = []
    for p0, p1 in pausas:
        t0, t1 = p0 + P["folga"], p1 - P["folga"]
        if t1 - t0 < 2 * P["rampa"]:
            continue
        dentro = [r for r in revelacoes if t0 < r < t1]
        if not dentro and any(t1 > r - 0.6 and t0 < r for r in revelacoes):
            continue   # o mergulho da revelação logo depois manda: a música não sobe antes de afundar
        d = t1 - t0 - P["rampa"]
        meio = base[min(len(ts) - 1, int(round((t0 + t1) / 2 * 100)))]
        pat = P["respiro"]
        if d < P["janela"]:   # respiro curto: o patamar sobe o que falta para a janela de 400 ms ler o respiro
            e = (P["janela"] * 10 ** (P["respiro"] / 10) - (P["janela"] - d) * 10 ** (meio / 10)) / d
            pat = min(P["teto_respiro_curto"], 10 * np.log10(max(e, 1e-12)))
        m = (ts >= t0) & (ts <= t1)
        k = np.clip(np.minimum((ts[m] - t0) / P["rampa"], (t1 - ts[m]) / P["rampa"]), 0, 1)
        g[m] = base[m] + (pat - base[m]) * k
        respiros.append((t0, t1, pat))
    for r in revelacoes:
        m = (ts >= r - P["antes"]) & (ts < r)
        k = np.clip((ts[m] - (r - P["antes"])) / P["rampa_mergulho"], 0, 1)
        g[m] = g[m] + (P["mergulho"] - g[m]) * k
        for t0, t1, pat in respiros:   # revelação dentro de um respiro: a música volta inteira no ataque
            if t0 < r < t1:
                g[(ts >= r) & (ts <= t1 - P["rampa"])] = pat
    for f0, f1 in fora:
        m = (ts >= f0) & (ts <= f1)
        k = np.clip(np.minimum((ts[m] - f0) / P["rampa"], (f1 - ts[m]) / P["rampa"]), 0, 1)
        g[m] = g[m] + (FORA_LU - g[m]) * k
    respiros = [r for r in respiros if not any(f0 <= r[0] and r[1] <= f1 for f0, f1 in fora)]
    pts = [[float(ts[0]), round(float(g[0]), 2)]]
    for i in range(1, len(ts) - 1):
        if abs((g[i + 1] - g[i]) - (g[i] - g[i - 1])) > 1e-3:
            pts.append([float(ts[i]), round(float(g[i]), 2)])
    pts.append([float(ts[-1]), round(float(g[-1]), 2)])
    return pts, respiros


def nivelar(m, voz, alvo, n, voz_ref):
    """Ganho (dB, por amostra) que leva o loudness momentâneo da música à curva-alvo (LU relativos à voz).

    Referência da voz: média de energia do momentâneo da voz inteira nas falas (janelas acima de -30 LUFS). O ganho
    segue o volume de curto prazo da própria música (golpes de metal e percussão não passam do alvo) e é corrigido
    onde a música medida ainda passa do alvo."""
    from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
    mv = momentaneo(voz_ref)
    V = 10 * np.log10(np.mean(10 ** (mv[mv > -30] / 10)))
    h = int(HOP * SR)
    k = (len(voz) + h - 1) // h          # um ponto a cada HOP, como o momentaneo()
    t = np.arange(k) * HOP
    p = sorted(alvo)
    A = V + np.interp(t, [a for a, _ in p], [b for _, b in p])
    mm = momentaneo(m)
    estavel = (maximum_filter1d(A, 41) - minimum_filter1d(A, 41) < 0.5).astype(int)
    # o volume da música entra pelo máximo em ±50 ms (um golpe de metal já baixa o ganho antes de chegar);
    # a curva-alvo entra sem filtro, para os respiros curtos subirem inteiros
    G = np.clip(A - uniform_filter1d(maximum_filter1d(mm, 11), 5), -60, 30)

    def aplicar(G):
        return np.interp(np.arange(n) / SR, t, G)
    for _ in range(3):
        med = momentaneo(m * db_para_lin(aplicar(G))[:, None])
        exc = np.maximum(med - A, 0)                   # só corrige para baixo onde passou,
        exc[estavel == 0] = 0                          # e só onde a janela de 400 ms inteira tem o mesmo alvo
        if exc.max() < 0.3:
            break
        G = G - uniform_filter1d(minimum_filter1d(-exc, 21) * -1, 5)
    print(f"Nivelador: voz nas falas {V:.1f} LUFS; ganho da música de {G.min():.1f} a {G.max():.1f} dB")
    return aplicar(G)


# ---------------------------------------------------------------------------------------------------------------
# limitadores
# ---------------------------------------------------------------------------------------------------------------
def suavizar_ganho(g, soltura):
    """Desce na hora e sobe com a soltura (s)."""
    a = np.exp(-1 / (soltura * SR))
    out = np.empty_like(g)
    prev = 1.0
    for i in range(len(g)):
        v = g[i]
        prev = v if v < prev else a * prev + (1 - a) * v
        out[i] = prev
    return out


def limitar(x, teto_db, resto=None, teto_soma_db=None, ataque=0.002, soltura=0.08):
    """Limitador com antecipação no barramento dos efeitos.

    O pico dos efeitos não passa de teto_db dBFS. Com `resto` (voz + trilha) e `teto_soma_db`, o detector olha a soma:
    os efeitos cedem só onde voz + trilha + efeitos passariam do teto da soma."""
    from numpy.lib.stride_tricks import sliding_window_view
    m = np.abs(x).max(1)
    need = np.minimum(1.0, 10 ** (teto_db / 20) / np.maximum(m, 1e-9))
    if resto is not None:
        c = 10 ** (teto_soma_db / 20)
        soma = np.abs(resto + x * need[:, None]).max(1)
        livre = np.maximum(c - np.abs(resto).max(1), 0.0)
        need = np.where(soma > c, np.minimum(need, livre / np.maximum(m, 1e-9)), need)
    la = int(ataque * SR)
    pad = np.pad(need, (0, la), constant_values=1.0)
    g = sliding_window_view(pad, la + 1).min(1)[: len(need)]
    return x * suavizar_ganho(g, soltura)[:, None]


def limitar_master(x, teto_dbtp, antecipa=0.005, soltura=0.15):
    """Limitador de pico verdadeiro no master: detecção com sobreamostragem 4x, antecipação de 5 ms e soltura de
    150 ms. Só age onde o pico passa do teto."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    from scipy.signal import resample_poly
    up = np.abs(resample_poly(x, 4, 1, axis=0)).max(1)
    pk = up[: (len(up) // 4) * 4].reshape(-1, 4).max(1)
    pk = np.pad(pk, (0, len(x) - len(pk)), mode="edge")
    need = np.minimum(1.0, 10 ** (teto_dbtp / 20) / np.maximum(pk, 1e-9))
    if need.min() >= 1.0:
        return x, np.ones(len(x))
    L = int(antecipa * SR)
    g = uniform_filter1d(minimum_filter1d(need, 2 * L + 1), L + 1)
    g = np.minimum(g, need)
    out = suavizar_ganho(g, soltura)
    return x * out[:, None], out


def relatar_limitador(g, ini=0.0):
    db = 20 * np.log10(np.maximum(g, 1e-9))
    ativo = db < -0.05
    if not ativo.any():
        print("Limitador do master: não agiu.")
        return
    idx = np.flatnonzero(ativo)
    grupos = np.split(idx, np.flatnonzero(np.diff(idx) > int(0.2 * SR)) + 1)
    pontos = [(ini + gr[np.argmin(db[gr])] / SR, db[gr].min(), len(gr) / SR) for gr in grupos]
    print(f"Limitador do master: {len(pontos)} pontos, {ativo.mean() * 100:.1f} % do tempo; "
          f"redução máxima {db.min():.1f} dB")
    for t, d, du in sorted(pontos, key=lambda p: p[1])[:6]:
        print(f"   {t:6.2f} s: {d:5.1f} dB ({du * 1000:.0f} ms)")


# ---------------------------------------------------------------------------------------------------------------
def main():
    utf8()
    ajuda(__doc__)
    checar_ffmpeg()
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        sair(__doc__)
    cfgp = Path(args[0]).expanduser().resolve()
    if not cfgp.is_file():
        sair(f"Não achei o mapa da mixagem: {cfgp}")
    base = cfgp.parent
    cfg = ler_json(cfgp)
    cam = lambda x: (Path(x).expanduser() if Path(x).expanduser().is_absolute() else base / x)  # noqa: E731
    sem_trilha = "--sem-trilha" in args
    trecho = "--trecho" in args
    if sem_trilha and not cfg.get("saida_sem_trilha") and cfg.get("saida"):
        cfg["saida_sem_trilha"] = f"medida/{Path(cfg['saida']).stem}-sem-trilha.mp4"
    for chave in ("video", "voz", "saida_sem_trilha" if sem_trilha else "saida"):
        if not cfg.get(chave):
            sair(f"Falta \"{chave}\" no {cfgp.name}.")
    video = cam(cfg["video"])
    if not video.is_file():
        sair(f"Não achei o vídeo: {video}")
    dur = sondar(video)["duracao"]
    ini, fim = 0.0, dur
    if trecho:
        i = args.index("--trecho")
        try:
            ini, fim = segundos(args[i + 1]), min(dur, segundos(args[i + 2]))
        except (IndexError, ValueError):
            sair("Use --trecho INÍCIO FIM, em segundos ou mm:ss (ex.: --trecho 0 8).")
        if not 0 <= ini < fim:
            sair("O --trecho precisa de início menor que o fim, dentro do vídeo.")
    n = int(round(dur * SR))

    # voz: passa-altas e compressor suave, levada a -16 LUFS na narração inteira
    voz_inteira = voz_tratada(cam(cfg["voz"]))
    voz = np.pad(voz_inteira, ((0, max(0, n - len(voz_inteira))), (0, 0)))[:n]
    mix = voz.copy()

    tr = cfg.get("trilha")
    if tr and not sem_trilha:
        P = dict(PADRAO_TRILHA)
        P.update({k: float(tr[k]) for k in PADRAO_TRILHA if k in tr})
        musica = cam(tr["arquivo"])
        if not musica.is_file():
            sair(f"Não achei a trilha: {musica}")
        m = ler_audio(musica, ini=float(tr.get("inicio", 0)) or None)
        m = np.pad(m, ((0, max(0, n - len(m))), (0, 0)))[:n]
        if "alvo" in tr:
            alvo = tr["alvo"]
            if isinstance(alvo, str):
                alvo = ler_json(cam(alvo))
            print("Curva da trilha: a do mix.json (\"alvo\").")
        else:
            if not tr.get("palavras"):
                sair("Falta \"trilha.palavras\" (o palavras-voz.json) para calcular a curva da trilha.")
            palavras = ler_json(cam(tr["palavras"]))
            viradas = ler_viradas(tr.get("viradas"), cam)
            revel = [float(r) for r in tr.get("revelacoes", [])]
            cresc = [[float(v) for v in c] for c in tr.get("crescendos", [])]
            fora = [[float(v) for v in c] for c in tr.get("fora", [])]
            alvo, respiros = curva_alvo(palavras, dur, viradas, revel, cresc, P, fora)
            (base / ".dados").mkdir(exist_ok=True)
            gravar_json(base / ".dados" / "curva-trilha.json", alvo, indent=None)
            print(f"Curva da trilha: {P['sob_fala']:+.1f} LU sob a fala, {P['respiro']:+.1f} em {len(respiros)} "
                  f"respiros, mergulho antes de {len(revel)} revelações, música fora em {len(fora)} janelas ({len(alvo)} pontos em .dados/curva-trilha.json)")
        g = nivelar(m, voz, alvo, n, voz_inteira)
        fi, fo = float(tr.get("fade_in", 0.05)), float(tr.get("fade_out", 0.5))
        ts = np.arange(n) / SR
        fim_trilha = float(tr.get("fim", dur))
        fade = np.clip(ts / max(fi, 1e-3), 0, 1) * np.clip((fim_trilha - ts) / max(fo, 1e-3), 0, 1)
        mix += m * (db_para_lin(g) * fade)[:, None]
    elif sem_trilha:
        print("Sem trilha: só voz e efeitos.")

    efs = cfg.get("efeitos", [])
    if isinstance(efs, str):
        if cam(efs).exists():
            efs = ler_json(cam(efs))
        else:
            print(f"Aviso: {cam(efs)} ainda não existe; mixando sem efeitos.")
            efs = []
    cache = {}
    camada = np.zeros_like(voz)
    usados = 0
    for e in efs:
        if e.get("so_com_trilha") and sem_trilha:
            continue
        s = e["som"]
        if s not in cache:
            if not cam(s).is_file():
                sair(f"Não achei o som {cam(s)} (efeito em {e.get('t')} s). Rode o efeitos.py de novo.")
            x = ler_audio(cam(s))
            cache[s] = (x, float(np.abs(x).max()) + 1e-9)
        x, pico = cache[s]
        if e.get("dur"):
            x = x[: int(float(e["dur"]) * SR)].copy()
            k = min(len(x), int(0.012 * SR))
            x[-k:] *= np.linspace(1, 0, k)[:, None]
        ganho = float(db_para_lin(PICO_EFEITO + float(e.get("vol", 0)))) / pico
        p0 = int(round(float(e["t"]) * SR))
        if p0 >= n:
            continue
        x = x[: n - p0]
        camada[p0:p0 + len(x)] += x * ganho
        usados += 1

    # barramento dos efeitos: limitador com teto; cede só onde a soma passaria do teto final
    a, b = int(ini * SR), int(fim * SR)
    teto = float(cfg.get("teto_efeitos", -1.0))
    base_mix = mix
    tem_ef = bool(np.abs(camada).max() > 0)
    ef = limitar(camada, teto) if tem_ef else camada
    ganho = 0.0
    for _ in range(3):
        mix = base_mix + ef
        ganho = ALVO_LUFS - lufs_de(mix[a:b])
        tp = pico_tp_de(mix[a:b]) + ganho
        if tp <= ALVO_TP - 0.1 or not tem_ef:
            break
        ef = limitar(camada, teto, base_mix, ALVO_TP - ganho - 0.8)
    print(f"Efeitos: {usados} · teto {teto:.1f} dBFS · ganho até -14 LUFS {ganho:+.1f} dB")

    # volume de publicação: ganho linear até -14 LUFS (o loudnorm linear, com a medida do ebur128, que acerta até
    # num trecho curto e nunca cai no modo dinâmico); quem segura o pico em -1,5 dBTP é o limitador do master
    final = mix[a:b] * float(db_para_lin(ganho))
    final, gm = limitar_master(final, ALVO_TP - TP_MARGEM)
    relatar_limitador(gm, ini)
    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        gravar_audio(tmp / "mix.wav", final, codec="pcm_s16le")

        if trecho:
            padrao = "../previas/previa-trecho.mp4"
            saida = cam(cfg.get("saida_trecho", padrao))
            if sem_trilha:
                saida = saida.with_name(saida.stem + "-sem-trilha" + saida.suffix)
            saida.parent.mkdir(parents=True, exist_ok=True)
            vcodec = (["-c:v", "h264_videotoolbox", "-b:v", "8M"] if platform.system() == "Darwin"
                      else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"])
            ff(["-ss", f"{ini:.3f}", "-t", f"{fim - ini:.3f}", "-i", video, "-i", tmp / "mix.wav", "-map", "0:v:0",
                "-map", "1:a:0", *vcodec, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-shortest",
                "-movflags", "+faststart", saida])
            final_p = saida
        else:
            final_p = cam(cfg["saida_sem_trilha"] if sem_trilha else cfg["saida"])
            final_p.parent.mkdir(parents=True, exist_ok=True)
            saida = final_p.with_name(final_p.stem + ".tmp" + final_p.suffix)
            ff(["-i", video, "-i", tmp / "mix.wav", "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                "-b:a", "256k", "-ar", str(SR), "-t", f"{dur:.3f}", "-movflags", "+faststart", saida])
    med = medir(saida)
    if not trecho:
        try:
            os.replace(saida, final_p)
        except PermissionError:
            sair(f"Não consegui trocar {final_p.name}: feche o vídeo no player e rode de novo. "
                 f"A mixagem nova está em {saida}.")
    print(f"Pronto: {final_p.resolve()}\nVolume final: {med['lufs']:.1f} LUFS · pico {med['true_peak']:.1f} dBTP")


if __name__ == "__main__":
    main()
