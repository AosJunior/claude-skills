"""Folha de contato com o segundo carimbado (o ffmpeg do Homebrew vem sem drawtext).

Uso:
  python3 briefings/folha.py --video <render.mp4> --saida <pasta>/<prefixo>   (1 quadro por segundo, em t = 0,5; 1,5; …)
  python3 briefings/folha.py --quadros <pasta de PNG do snapshot> --saida <pasta>/<prefixo>
Grava <prefixo>-01.jpg, -02.jpg… em grade 8×3, 300 px por quadro, com o tempo no canto.
"""
import argparse, glob, os, re, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

COLS, ROWS, W = 8, 3, 300
H = W * 1920 // 1080


FONTES = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",   # Mac
          "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf",                           # Windows
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",   # Linux
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]


def fonte(tam):
    for f in FONTES:
        if os.path.exists(f):
            return ImageFont.truetype(f, tam)
    try:   # as versões novas do Pillow trazem uma fonte própria que aceita tamanho
        return ImageFont.load_default(tam)
    except TypeError:
        return ImageFont.load_default()


def quadros_do_video(video, pasta):
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                         "default=nw=1:nk=1", video]).decode())
    # o quadro mais perto de cada t = k + 0,5 (o filtro fps arredondava e a folha saía 0,5 s atrasada do carimbo)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf",
                    f"select='lt(abs(mod(t\\,1)-0.5)\\,0.0167)',scale={W}:-2", "-fps_mode", "vfr",
                    os.path.join(pasta, "q%03d.png")], check=True)
    fs = sorted(glob.glob(os.path.join(pasta, "q*.png")))
    return [(f, 0.5 + i) for i, f in enumerate(fs) if 0.5 + i <= dur]


def quadros_do_snapshot(pasta):
    out = []
    for f in glob.glob(os.path.join(pasta, "frame-*-at-*s.png")):
        m = re.search(r"-at-([\d.]+)s\.png$", f)
        out.append((f, float(m.group(1))))
    return sorted(out, key=lambda x: x[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video"); ap.add_argument("--quadros"); ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    tmp = tempfile.mkdtemp()
    qs = quadros_do_video(a.video, tmp) if a.video else quadros_do_snapshot(a.quadros)
    f = fonte(26)
    n = COLS * ROWS
    for k in range(0, len(qs), n):
        folha = Image.new("RGB", (COLS * W, ROWS * H), (20, 20, 20))
        d = ImageDraw.Draw(folha)
        for i, (arq, t) in enumerate(qs[k:k + n]):
            im = Image.open(arq).convert("RGB").resize((W, H))
            x, y = (i % COLS) * W, (i // COLS) * H
            folha.paste(im, (x, y))
            rot = f"{t:.1f}s".replace(".", ",")
            d.rectangle([x, y, x + 92, y + 36], fill=(0, 0, 0))
            d.text((x + 8, y + 4), rot, font=f, fill=(255, 220, 90))
        nome = f"{a.saida}-{k // n + 1:02d}.jpg"
        folha.save(nome, quality=86)
        print(nome)


main()
