"""Funções comuns da /inserir. Roda igual no Mac e no Windows."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def utf8():
    """Saída em UTF-8 até no console do Windows (senão acento e "→" derrubam o script)."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def sair(msg, codigo=1):
    print(msg)
    sys.exit(codigo)


def rodar(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def checar_ffmpeg():
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sair("Falta o ffmpeg neste computador. Mac: brew install ffmpeg · Windows: winget install Gyan.FFmpeg "
             "(no Windows, feche e abra o Claude depois de instalar).")


def ler_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sair(f"{Path(p).name} tem um erro de escrita na linha {e.lineno}, coluna {e.colno}: {e.msg}.")


def fmt_tempo(s):
    """83.456 -> "01:23,46" (minuto:segundo,centésimos)."""
    cs = int(round(max(0.0, float(s)) * 100))
    return f"{cs // 6000:02d}:{cs // 100 % 60:02d},{cs % 100:02d}"


def fmt_num(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


def tempo(v, onde=""):
    """Aceita segundos (12.5), "mm:ss,cc" ou "mm:ss.cc"."""
    if isinstance(v, (int, float)):
        return float(v)
    m = re.fullmatch(r"\s*(?:(\d+):)?(\d+)(?:[.,](\d+))?\s*", str(v))
    if not m:
        sair(f"{onde}: não entendi o tempo {v!r}. Use \"01:23,45\" ou segundos (83.45).")
    mi, se, fr = m.groups()
    return int(mi or 0) * 60 + int(se) + (float("0." + fr) if fr else 0.0)


def ler_srt(p):
    """[(ini, fim, texto)] de um .srt."""
    blocos = []
    txt = Path(p).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    for b in re.split(r"\n\s*\n", txt.strip()):
        linhas = b.strip().split("\n")
        for i, l in enumerate(linhas):
            m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", l)
            if m:
                g = [int(x) for x in m.groups()]
                ini = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
                fim = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
                texto = " ".join(linhas[i + 1:]).strip()
                if texto:
                    blocos.append((ini, fim, texto))
                break
    return blocos


def srt_tempo(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def info_video(p):
    r = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
               "-of", "json", p])
    if r.returncode:
        sair(f"Não consegui abrir o vídeo {p}.")
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    n, _, q = v["r_frame_rate"].partition("/")
    return {"dur": float(d["format"]["duration"]), "w": v["width"], "h": v["height"],
            "fps": float(n) / float(q or 1), "audio": a["codec_name"] if a else None}


def navegador(pw):
    """Abre o Chromium do Playwright; na primeira vez da máquina, baixa o navegador sozinho."""
    try:
        return pw.chromium.launch()
    except Exception as e:
        if "Executable doesn't exist" not in str(e) and "playwright install" not in str(e):
            raise
    print("Primeira vez: baixando o navegador que desenha os cartões (uns 150 MB, 1 a 3 min)...", flush=True)
    r = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    if r.returncode:
        sair("Não consegui baixar o navegador. Confira a internet e rode de novo.")
    return pw.chromium.launch()
