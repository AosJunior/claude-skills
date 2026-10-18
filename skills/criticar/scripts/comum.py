"""Funções comuns da /criticar. Só biblioteca padrão; roda igual no Mac e no Windows."""
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

VIDEO = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}
IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}


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


def sair(msg, codigo=1):
    print(msg)
    sys.exit(codigo)


def checar_ffmpeg():
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sair("Falta o ffmpeg neste computador. Mac: brew install ffmpeg · Windows: winget install Gyan.FFmpeg "
             "(no Windows, feche e abra o Claude depois de instalar).")


def ler_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def gravar_json(p, d):
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def fmt_tempo(s):
    """83.456 -> "01:23,46" (minuto:segundo,centésimos)."""
    cs = int(round(max(0.0, float(s)) * 100))
    return f"{cs // 6000:02d}:{cs // 100 % 60:02d},{cs % 100:02d}"


def fmt_num(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


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


def token(w):
    """Palavra sem acento, caixa nem pontuação (a comparação de texto da seção 2 do contrato)."""
    s = unicodedata.normalize("NFKD", str(w).lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s)


def achar_marca(pasta):
    """Sobe a partir da pasta do vídeo até achar marca/estilo.md (contrato, seção 1)."""
    p = Path(pasta).resolve()
    for d in [p, *p.parents]:
        if (d / "marca" / "estilo.md").is_file():
            return d / "marca"
    return None


def sondar(video):
    """Duração, tamanho, quadros por segundo e se tem som."""
    r = rodar(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", video])
    if r.returncode != 0:
        sair(f"Não consegui abrir o vídeo (o arquivo pode estar incompleto ou ainda baixando): {video}")
    d = json.loads(r.stdout or "{}")
    vs = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"
               and not (s.get("disposition") or {}).get("attached_pic")), None)
    if not vs:
        sair(f"Esse arquivo não tem imagem de vídeo: {video}")
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    n, _, den = str(vs.get("avg_frame_rate") or vs.get("r_frame_rate") or "30/1").partition("/")
    try:
        fps = float(n) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        fps = 30.0
    rot = 0
    for sd in vs.get("side_data_list") or []:
        if "rotation" in sd:
            rot = round(float(sd["rotation"]))
    w, h = int(vs.get("width") or 0), int(vs.get("height") or 0)
    if abs(rot) == 90:
        w, h = h, w
    return {"arquivo": str(Path(video).resolve()), "duracao": float((d.get("format") or {}).get("duration") or 0),
            "fps": fps if 5 < fps < 121 else 30.0, "largura": w, "altura": h, "tem_audio": a is not None}


def ler_srt(p):
    """Lista de {de, ate, texto} de um .srt."""
    txt = Path(p).read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n")
    out = []
    for bloco in re.split(r"\n\s*\n", txt.strip()):
        ls = [x for x in bloco.split("\n") if x.strip()]
        for i, l in enumerate(ls):
            m = re.match(r"\s*(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", l)
            if m:
                g = [int(x) for x in m.groups()]
                de = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 10 ** len(m.group(4))
                ate = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 10 ** len(m.group(8))
                out.append({"de": de, "ate": ate, "texto": " ".join(ls[i + 1:]).strip()})
                break
    return out


def relativo(base, caminho, marca=None):
    """Caminho de um JSON: `marca/...` vale contra a pasta da marca; o resto, contra a pasta do JSON."""
    c = str(caminho)
    if marca and c.replace("\\", "/").startswith("marca/"):
        return Path(marca).parent / c
    p = Path(c).expanduser()
    return p if p.is_absolute() else (Path(base) / p)
