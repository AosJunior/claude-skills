"""/criticar: a imagem. Uma passada pelo vídeo inteiro acha os cortes e os quadros soltos e guarda os
quadros das folhas (1 por segundo + os quadros em volta de cada corte)."""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from comum import fmt_tempo, rodar

TW, TH = 288, 512            # quadro guardado (9:16); a medida de corte usa 72×128 (blocos de 4×4)
VOLTA = 2                    # quadros guardados de cada lado de um corte
CORTE_MIN = 15.0             # diferença média (0–255, em 72×128) que conta como corte seco
SOLTO_MAX = 3                # pedaço entre dois cortes com menos quadros que isto = quadro solto
MISTURA_MAX = 1.2            # pedaço que é mistura dos vizinhos (fade, pop) não é quadro solto


FONTES = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
          "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def fonte(tam):
    """Fonte com acentos para os rótulos (a padrão do Pillow não tem "ê")."""
    for f in FONTES:
        if Path(f).is_file():
            return ImageFont.truetype(f, tam)
    try:
        return ImageFont.load_default(size=tam)
    except TypeError:                      # Pillow antigo
        return ImageFont.load_default()


def ler_quadros(video, info):
    """Decodifica o vídeo uma vez. Devolve as diferenças entre quadros vizinhos, os cortes e os quadros
    guardados {n: RGB 288×512}."""
    fps, dur = info["fps"], info["duracao"]
    total_est = int(round(dur * fps))
    por_segundo = {min(int(s * fps), max(0, total_est - 1)) for s in range(int(np.ceil(dur)))}
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-map", "0:v:0",
                          "-vf", f"scale={TW}:{TH}:flags=area,format=rgb24", "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    tam = TW * TH * 3
    guardar, guardados, buf = set(por_segundo), {}, {}
    difs, prev, n = [], None, 0
    while True:
        raw = p.stdout.read(tam)
        if len(raw) < tam:
            break
        rgb = np.frombuffer(raw, np.uint8).reshape(TH, TW, 3)
        cinza = (rgb @ np.array([0.299, 0.587, 0.114], np.float32)).reshape(TH // 4, 4, TW // 4, 4).mean((1, 3))
        if prev is not None:
            d = float(np.abs(cinza - prev).mean())
            difs.append(d)
            if d >= CORTE_MIN:                      # corte entre n-1 e n: guarda n-2..n+2
                for k in range(n - VOLTA, n + VOLTA + 1):
                    guardar.add(k)
                for k in list(buf):
                    if k in guardar:
                        guardados[k] = buf[k]
        prev = cinza
        buf[n] = rgb
        buf.pop(n - VOLTA - 1, None)
        if n in guardar:
            guardados[n] = rgb
        n += 1
    p.wait()
    difs = np.array(difs, np.float32)
    return {"difs": difs, "quadros": n, "guardados": guardados, "por_segundo": sorted(k for k in por_segundo if k < n)}


def cortes_e_soltos(q, fps):
    """Cortes secos (n = primeiro quadro do plano novo) e quadros soltos: um pedaço de menos de 3 quadros
    entre dois cortes secos, que não é mistura dos vizinhos (a mistura é fade ou pop de inserção)."""
    d = q["difs"]
    cortes = [int(k) + 1 for k in np.where(d >= CORTE_MIN)[0]]
    G = q["guardados"]

    def cinza(k):
        return G[k].astype(np.float32).mean(2) if k in G else None

    soltos = []
    for a, b in zip(cortes, cortes[1:]):
        if b - a >= SOLTO_MAX:
            continue
        antes, depois = cinza(a - 1), cinza(b)
        meio = [cinza(k) for k in range(a, b)]
        if antes is None or depois is None or any(m is None for m in meio):
            continue
        seg = np.mean(meio, axis=0)
        vizinhos = float(np.abs(depois - antes).mean())
        mistura = float(np.abs(seg - 0.5 * (antes + depois)).mean()) / (vizinhos / 2 + 1e-6)
        if mistura > MISTURA_MAX:
            soltos.append({"t": round(a / fps, 3), "quadro": a, "quadros": b - a,
                           "entra": round(float(d[a - 1]), 1), "sai": round(float(d[b - 1]), 1),
                           "mistura": round(mistura, 2)})
    return cortes, soltos


def _rotulo(dr, x, y, txt, tam, cor=(255, 230, 0)):
    f = fonte(tam)
    bb = dr.textbbox((x + 4, y + 2), txt, font=f)
    dr.rectangle([x, y, bb[2] + 4, bb[3] + 3], fill=(0, 0, 0))
    dr.text((x + 4, y + 2), txt, fill=cor, font=f)


def _marcas_zona(dr, x, y, w, h, zona, altura):
    """Tracinhos vermelhos na borda do quadro nas linhas da zona segura (não cobrem a imagem)."""
    for z in zona:
        yy = y + int(round(z / altura * h))
        dr.line([x - 6, yy, x - 1, yy], fill=(255, 40, 40), width=3)
        dr.line([x + w, yy, x + w + 5, yy], fill=(255, 40, 40), width=3)


def folhas(q, info, cortes, soltos, pasta, zona):
    """critica/folha-NN.jpg (1 quadro por segundo, 30 s por folha) e critica/folha-cortes-NN.jpg
    (cada corte numa linha: 2 quadros antes, o primeiro do plano novo e 2 depois)."""
    fps, G = info["fps"], q["guardados"]
    for velho in Path(pasta).glob("folha-*.jpg"):
        velho.unlink()
    feitas = []
    cols, linhas, pad, w, h = 6, 5, 14, TW, TH
    seg = q["por_segundo"]
    for i in range(0, len(seg), cols * linhas):
        bloco = seg[i:i + cols * linhas]
        rows = (len(bloco) + cols - 1) // cols
        im = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad) + pad + 40), (28, 28, 28))
        dr = ImageDraw.Draw(im)
        _rotulo(dr, pad, 6, f"{fmt_tempo(bloco[0] / fps)} a {fmt_tempo(bloco[-1] / fps)} · 1 quadro por segundo · "
                            f"tracinhos vermelhos = zona segura de {zona[0]} a {zona[1]} px", 22, (230, 230, 230))
        for j, k in enumerate(bloco):
            x, y = pad + (j % cols) * (w + pad), 40 + pad + (j // cols) * (h + pad)
            im.paste(Image.fromarray(G[k]), (x, y))
            _marcas_zona(dr, x, y, w, h, zona, info["altura"] or 1920)
            _rotulo(dr, x, y, fmt_tempo(k / fps), 20)
        nome = Path(pasta) / f"folha-{len(feitas) + 1:02d}.jpg"
        im.save(nome, quality=86)
        feitas.append(nome.name)
    # cortes: 1 linha por corte
    w2, h2, por_folha = 180, 320, 8
    soltos_q = {s["quadro"] for s in soltos}
    lista = [c for c in cortes if all(k in G for k in range(c - VOLTA, c + VOLTA + 1))]
    nc = 0
    for i in range(0, len(lista), por_folha):
        bloco = lista[i:i + por_folha]
        larg = 150 + (2 * VOLTA + 1) * (w2 + 8)
        im = Image.new("RGB", (larg, len(bloco) * (h2 + 12) + 46), (28, 28, 28))
        dr = ImageDraw.Draw(im)
        _rotulo(dr, 8, 6, "Cortes: 2 quadros antes, o 1º do plano novo (borda amarela) e 2 depois. "
                          "Vermelho = quadro solto.", 20, (230, 230, 230))
        for r, c in enumerate(bloco):
            y = 46 + r * (h2 + 12)
            _rotulo(dr, 8, y + h2 // 2 - 14, fmt_tempo(c / fps), 22)
            for j, k in enumerate(range(c - VOLTA, c + VOLTA + 1)):
                x = 150 + j * (w2 + 8)
                im.paste(Image.fromarray(G[k]).resize((w2, h2), Image.BILINEAR), (x, y))
                if k in soltos_q:
                    dr.rectangle([x - 3, y - 3, x + w2 + 2, y + h2 + 2], outline=(255, 40, 40), width=5)
                elif k == c:
                    dr.rectangle([x - 2, y - 2, x + w2 + 1, y + h2 + 1], outline=(255, 210, 0), width=3)
        nc += 1
        nome = Path(pasta) / f"folha-cortes-{nc:02d}.jpg"
        im.save(nome, quality=86)
        feitas.append(nome.name)
    cobertos = len(seg)
    return feitas, {"segundos": cobertos, "duracao": info["duracao"],
                    "cortes": len(cortes), "cortes_na_folha": len(lista),
                    "completa": cobertos >= int(np.ceil(info["duracao"] - 1e-6)) and len(lista) == len(cortes)}


def quadro(video, t, largura=None):
    """Um quadro em resolução cheia (ou na largura pedida), como imagem PIL."""
    vf = ["-vf", f"scale={largura}:-2"] if largura else []
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(video), "-frames:v", "1",
                        *vf, "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return None
    from io import BytesIO
    return Image.open(BytesIO(r.stdout)).convert("RGB")


def ampliar(video, t, caixa, saida, folga=30):
    """Recorte em resolução cheia, ampliado até uns 900 px de largura, para ler letra por letra."""
    im = quadro(video, t)
    if im is None:
        return False
    if caixa:
        x, y, w, h = [int(round(v)) for v in caixa]
        im = im.crop((max(0, x - folga), max(0, y - folga), min(im.width, x + w + folga),
                      min(im.height, y + h + folga)))
    esc = max(1.0, min(3.0, 900 / max(1, im.width)))
    if esc > 1:
        im = im.resize((int(im.width * esc), int(im.height * esc)), Image.LANCZOS)
    im.save(saida, quality=92)
    return True


def folha_referencia(video, info, refs, saida):
    """Referência × resultado: para cada vídeo da marca e para o resultado, uma linha com o gancho
    (0,5 s, 1,5 s, 2,5 s) e o corpo (25 %, 50 %, 75 %)."""
    def linha(v, dur):
        ts = [0.5, 1.5, 2.5, dur * 0.25, dur * 0.5, dur * 0.75]
        return [(t, quadro(v, min(t, max(0.0, dur - 0.1)), 240)) for t in ts]

    linhas = []
    for r in refs:
        if r.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            try:
                linhas.append((f"referência · {r.name}", [(None, Image.open(r).convert("RGB"))]))
            except Exception:
                pass
            continue
        dr = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", r])
        try:
            dur = float(dr.stdout.strip())
        except ValueError:
            continue
        linhas.append((f"referência · {r.name}", linha(r, dur)))
    linhas.append(("RESULTADO", linha(video, info["duracao"])))
    w, h, pad = 240, 427, 10
    im = Image.new("RGB", (220 + 6 * (w + pad), len(linhas) * (h + 30) + 20), (28, 28, 28))
    dr = ImageDraw.Draw(im)
    for i, (nome, qs) in enumerate(linhas):
        y = 20 + i * (h + 30)
        _rotulo(dr, 8, y + h // 2 - 14, nome[:24], 18, (255, 230, 0) if nome == "RESULTADO" else (230, 230, 230))
        for j, (t, q) in enumerate(qs):
            if q is None:
                continue
            q = q.copy()
            q.thumbnail((w, h))
            x = 220 + j * (w + pad)
            im.paste(q, (x, y))
            if t is not None:
                _rotulo(dr, x, y, fmt_tempo(t), 16)
    im.save(saida, quality=86)
    return len(linhas) - 1
