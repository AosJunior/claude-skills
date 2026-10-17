"""Funções comuns da /sonorizar. Só biblioteca padrão; roda igual no Mac e no Windows."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

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
