"""Funções comuns da /decupar. Só biblioteca padrão; roda igual no Mac e no Windows."""
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from fractions import Fraction
from pathlib import Path

VIDEO = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mts", ".3gp"}
AUDIO_EVITAR = {"apple_apac"}          # áudio espacial do iPhone: não serve para transcrever nem para cortar
PADROES = [Fraction(24000, 1001), Fraction(24), Fraction(25), Fraction(30000, 1001), Fraction(30),
           Fraction(50), Fraction(60000, 1001), Fraction(60)]
CAP_PALAVRA = 1.0                      # s; o Whisper estica palavra por cima de pausa: limita a duração


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


def slug(nome):
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_-]+", "-", s).strip("-")[:40] or "video"


def fmt_tempo(s):
    """83.456 -> "01:23,46" (minuto:segundo,centésimos)."""
    cs = int(round(max(0.0, float(s)) * 100))
    return f"{cs // 6000:02d}:{cs // 100 % 60:02d},{cs % 100:02d}"


def fmt_dur(s):
    s = int(round(float(s)))
    return f"{s // 60} min {s % 60:02d} s" if s >= 60 else f"{s} s"


def fmt_num(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


def fracao(txt):
    try:
        n, _, d = str(txt or "0/1").partition("/")
        f = Fraction(int(n), int(d or 1))
        return f if f > 0 else None
    except (ValueError, ZeroDivisionError):
        return None


def taxa(r_frame_rate, avg_frame_rate):
    """Taxa de quadros padrão mais próxima (celular Android costuma gravar com taxa variável)."""
    r, m = fracao(r_frame_rate), fracao(avg_frame_rate)
    base = m if (m and (not r or r > 65 or abs(float(r) - float(m)) > 1)) else (r or m or Fraction(30))
    return min(PADROES, key=lambda p: abs(float(p) - float(base)))


def sondar(video):
    """Duração, tamanho de exibição (já girado), taxa, rotação, faixa de áudio e cor do vídeo."""
    r = rodar(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", video])
    if r.returncode != 0:
        sair(f"Não consegui abrir o vídeo (o arquivo pode estar incompleto ou ainda baixando): {video}")
    d = json.loads(r.stdout or "{}")
    vs = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"
               and not (s.get("disposition") or {}).get("attached_pic")), None)
    if not vs:
        sair(f"Esse arquivo não tem imagem de vídeo: {video}")
    audios = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
    boas = [i for i, a in enumerate(audios) if a.get("codec_name") not in AUDIO_EVITAR]
    faixa = next((i for i in boas if int(audios[i].get("channels") or 0) in (1, 2)), boas[0] if boas else None)
    rot = 0
    for sd in vs.get("side_data_list") or []:
        if "rotation" in sd:
            rot = round(float(sd["rotation"]))
    if not rot and (vs.get("tags") or {}).get("rotate"):
        rot = -int(vs["tags"]["rotate"])
    rot = (rot + 180) % 360 - 180
    w, h = int(vs.get("width") or 0), int(vs.get("height") or 0)
    dw, dh = (h, w) if abs(rot) == 90 else (w, h)
    fps = taxa(vs.get("r_frame_rate"), vs.get("avg_frame_rate"))
    a = audios[faixa] if faixa is not None else {}
    fmt = d.get("format", {})
    return {
        "arquivo": str(Path(video).resolve()),
        "nome": Path(video).name,
        "duracao": round(float(fmt.get("duration") or vs.get("duration") or 0), 3),
        "largura": dw, "altura": dh, "largura_arq": w, "altura_arq": h,
        "rotacao": rot,
        "marca": str((fmt.get("tags") or {}).get("major_brand") or "").strip().upper(),
        "fps_num": fps.numerator, "fps_den": fps.denominator,
        "faixa_audio": faixa,
        "canais": int(a.get("channels") or 0),
        "canais_antes": sum(int(audios[i].get("channels") or 0) for i in range(faixa or 0)),
        "taxa_audio": int(a.get("sample_rate") or 48000),
        "transferencia": vs.get("color_transfer") or "",
        "hdr": (vs.get("color_transfer") or "") in ("arib-std-b67", "smpte2084"),
    }


def chave_palavra(w):
    """Palavra sem acento, caixa e pontuação ("Vocês," -> "voces"): é assim que as âncoras comparam."""
    s = unicodedata.normalize("NFKD", str(w)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def achar_marca(pasta):
    """Sobe a partir da pasta do vídeo até achar marca/estilo.md (ou chegar à raiz do disco).
    Devolve a pasta marca/ ou None. Igual em todas as skills do kit (contrato, seção 1)."""
    p = Path(os.path.abspath(Path(pasta).expanduser()))
    for d in (p, *p.parents):
        if (d / "marca" / "estilo.md").is_file():
            return d / "marca"
    return None


def texto_marca(marca):
    return f"Marca: {marca}" if marca else "Marca: nenhuma"


def resolver(caminho, base, marca):
    """Caminho escrito num JSON: "marca/..." vale contra a pasta de edição; o resto, contra a pasta do JSON."""
    c = str(caminho).replace("\\", "/")
    if c.startswith("marca/"):
        return (marca.parent / c) if marca else None
    p = Path(c).expanduser()
    return p if p.is_absolute() else Path(base) / p


def orientacao(info):
    return "vertical" if info["altura"] > info["largura"] else "horizontal"


def pasta_decupagem(video):
    """<pasta do vídeo>/decupagem/. Se ela já for de outro vídeo, decupagem-<nome>/.
    Atalho (symlink) para o bruto: a decupagem nasce ao lado do atalho, não ao lado do original."""
    atalho = Path(os.path.abspath(Path(video).expanduser()))
    video = Path(video).resolve()
    base = atalho.parent / "decupagem"
    marca = base / ".dados" / "info.json"
    if marca.exists():
        try:
            if ler_json(marca).get("arquivo") != str(video):
                base = video.parent / f"decupagem-{slug(video.stem)}"
        except Exception:
            pass
    return base


def achar_pasta(arg):
    """Aceita a pasta de decupagem ou o próprio vídeo."""
    p = Path(os.path.abspath(Path(arg).expanduser()))
    if p.is_file() and p.suffix.lower() in VIDEO:
        p = pasta_decupagem(p)
    if not (p / ".dados" / "info.json").exists():
        sair(f"Não achei a decupagem em {p}. Rode primeiro o transcrever.py com o vídeo.")
    return p


def tamanho(info, final=False, vertical=False):
    """Prévia: 1080 de altura. Final: 1080 no lado curto (1080×1920 no vertical). Nunca aumenta.
    vertical=True: recorte 9:16 de um vídeo horizontal (prévia 608×1080, final 1080×1920)."""
    if vertical:
        return (1080, 1920) if final else (608, 1080)
    w, h = info["largura"], info["altura"]
    esc = min(1080, min(w, h)) / min(w, h) if final else min(1080, h) / h
    return max(2, int(round(w * esc / 2)) * 2), max(2, int(round(h * esc / 2)) * 2)


def hwaccel():
    if sys.platform == "darwin":
        return ["-hwaccel", "videotoolbox"]
    if sys.platform.startswith("win"):
        return ["-hwaccel", "auto"]
    return []


def encoder(modo):
    """modo: "proxy", "previa" ou "final"."""
    r = rodar(["ffmpeg", "-hide_banner", "-encoders"])
    if sys.platform == "darwin" and "h264_videotoolbox" in r.stdout:
        taxa = {"proxy": "5M", "previa": "3M", "final": "10M"}[modo]
        return ["-c:v", "h264_videotoolbox", "-b:v", taxa, "-profile:v", "high"]
    if "libx264" in r.stdout:
        preset = {"proxy": "ultrafast", "previa": "veryfast", "final": "fast"}[modo]
        crf = {"proxy": "20", "previa": "23", "final": "19"}[modo]
        return ["-c:v", "libx264", "-preset", preset, "-crf", crf]
    return ["-c:v", "mpeg4", "-q:v", "3"]


def assinatura_video(arquivo):
    st = Path(arquivo).stat()
    return {"tamanho": st.st_size, "mtime": int(st.st_mtime)}


def proxy_valido(dados, info):
    """Cópia leve do vídeo (feita junto com a transcrição) que acelera a prévia e as correções."""
    px, meta = Path(dados) / "proxy.mov", Path(dados) / "proxy.json"
    if not (px.exists() and meta.exists()):
        return None
    try:
        m = ler_json(meta)
        ok = {k: m.get(k) for k in ("tamanho", "mtime")} == assinatura_video(info["arquivo"])
        return px if ok and [m.get("largura"), m.get("altura")] == list(tamanho(info)) else None
    except Exception:
        return None
