# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26", "opencv-python-headless>=4.9"]
# ///
"""/inserir: motor de composição. Monta, num render só, a tela dividida, as camadas (vídeo, imagem, faixa, html)
atrás da pessoa (com a máscara), no topo da dividida e na frente, os cartões e a legenda.

Quem chama é o inserir.py (compor(plano)); não é para rodar à mão. O vídeo sai em blocos codificados em paralelo,
cada bloco uma vez só (uma geração de compressão), emendados sem recodificar, com o áudio do vídeo cortado (e o
áudio das camadas que pedem som).

Plano (tempos em segundos do vídeo cortado; caminhos absolutos):
  {"video", "saida", "dados", "fps", "fps_txt", "quadros", "crf", "preset", "trabalhadores",
   "divididas": [{"id", "de", "ate", "corte", "laterais", "pessoa": [{"de", "recorte_y", "escala"}]}],
   "camadas":   [{"id", "tipo": "video"|"imagem", "lugar": "topo"|"atras"|"frente", "de", "ate",
                  "x", "y", "w", "h", "rot", "raio", "sombra", "entra", "sai", "cheia",
                  "arquivo" (imagem) | "trechos": [{"de", "ate", "arquivo", "src", "caixa", "dur"}] (vídeo)}],
   "cartoes":   [{"png", "de", "ate"}],          PNG 1080x1920 transparente (cartão de inserção)
   "legendas":  [{"png", "de", "ate", "x", "y"}], PNG recortado e onde ele entra
   "mascaras":  [{"q0", "q1", "arquivo"}],        máscara cinza (0 = fundo, 255 = pessoa), quadros q0..q1-1
   "audio":     [{"arquivo", "src", "de", "ate", "ganho"}]}
Ordem de pintura: vídeo (ou dividida com o topo) → camadas atrás da pessoa → cartões → camadas da frente → legenda.
"""
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

W, H = 1080, 1920
HW = sys.platform == "darwin" and os.environ.get("INSERIR_SEM_HW") != "1"   # decodifica no chip do Mac


def ffmpeg_cor(arq):
    """Matriz e faixa de cor do arquivo (para a conversão YUV↔RGB não mudar a cor)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=color_space,color_range,height", "-of", "json", str(arq)], capture_output=True, text=True)
    try:
        s = json.loads(r.stdout)["streams"][0]
    except Exception:
        return "bt709", "tv"
    m = s.get("color_space") or ""
    m = {"bt709": "bt709", "smpte170m": "smpte170m", "bt470bg": "bt470", "bt2020nc": "bt2020", "bt2020c": "bt2020"}.get(
        m, "bt709" if (s.get("height") or 1080) >= 720 else "smpte170m")
    return m, ("pc" if s.get("color_range") == "pc" else "tv")


class Leitor:
    """Lê quadros de um arquivo em sequência, já no tamanho pedido. No fim do arquivo (ou de `limite` segundos),
    repete o último quadro."""

    def __init__(self, arq, w, h, ini=0.0, fps_txt="30", cinza=False, caixa=None, cobrir=True, limite=None):
        self.w, self.h, self.cinza = w, h, cinza
        fil = []
        if caixa:
            fil.append(f"crop={int(caixa[2])}:{int(caixa[3])}:{int(caixa[0])}:{int(caixa[1])}")
        fil.append(f"fps={fps_txt}")
        if cinza:
            fil.append(f"scale={w}:{h}")
        else:
            m, rng = ffmpeg_cor(arq)
            dim = f"{w}:{h}:force_original_aspect_ratio=increase" if cobrir else f"{w}:{h}"
            fil.append(f"scale={dim}:in_color_matrix={m}:in_range={rng}:flags=bicubic")
            if cobrir:
                fil.append(f"crop={w}:{h}")
        cmd = ["ffmpeg", "-v", "error", "-nostdin"]
        if HW and not cinza:
            cmd += ["-hwaccel", "videotoolbox"]
        if ini > 0:
            cmd += ["-ss", f"{ini:.4f}"]
        cmd += ["-i", str(arq)]
        if limite:
            cmd += ["-t", f"{max(limite, 0.04):.4f}"]
        cmd += ["-an", "-vf", ",".join(fil), "-f", "rawvideo", "-pix_fmt", "gray" if cinza else "rgb24", "-"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 7)
        self.n = w * h * (1 if cinza else 3)
        self.buf = bytearray(self.n)
        self.q = np.frombuffer(self.buf, np.uint8).reshape((h, w) if cinza else (h, w, 3))
        self.tem = False

    def ler(self):
        """O próximo quadro (o mesmo array, reaproveitado), ou None se o arquivo não tinha nenhum quadro."""
        mv, lidos = memoryview(self.buf), 0
        while lidos < self.n:
            k = self.p.stdout.readinto(mv[lidos:])
            if not k:
                break
            lidos += k
        if lidos == self.n:
            self.tem = True
        return self.q if self.tem else None

    def fechar(self):
        try:
            self.p.kill()
            self.p.wait()
        except Exception:
            pass


def suave(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def borrar(src, w, h, sigma=28.0, escuro=0.78):
    """O quadro ampliado para cobrir w×h, borrado e escurecido. O borrão é feito em 1/4 da resolução (rápido)."""
    sh, sw = src.shape[:2]
    k = max(w / sw, h / sh)
    pw, ph = max(4, int(round(sw * k / 4))), max(4, int(round(sh * k / 4)))
    peq = cv2.resize(src, (pw, ph), interpolation=cv2.INTER_AREA)
    ox, oy = (pw - w // 4) // 2, (ph - h // 4) // 2
    peq = peq[oy:oy + h // 4, ox:ox + w // 4]
    peq = cv2.GaussianBlur(peq, (0, 0), sigma / 4)
    out = cv2.resize(peq, (w, h), interpolation=cv2.INTER_LINEAR)
    return cv2.convertScaleAbs(out, alpha=escuro)


def codificador(P):
    """No Mac, o codificador de vídeo do chip (rápido e sem pesar na CPU); fora dele, o libx264."""
    if P.get("codificador") == "videotoolbox":
        return ["-c:v", "h264_videotoolbox", "-b:v", P.get("taxa", "16M"), "-profile:v", "high"]
    return ["-c:v", "libx264", "-preset", P.get("preset", "veryfast"), "-crf", str(P.get("crf", 17)),
            "-threads", str(P.get("threads_x264", 0))]


def misturar(fundo, pec, peso):
    """fundo = pec·peso + fundo·(1-peso), em uint8 (peso float32 0..1, já do tamanho da região)."""
    return cv2.blendLinear(pec, fundo, peso, 1.0 - peso)


def canto_redondo(w, h, r):
    m = np.zeros((h, w), np.uint8)
    if r <= 0:
        m[:] = 255
        return m
    r = min(r, w // 2, h // 2)
    cv2.rectangle(m, (r, 0), (w - r - 1, h - 1), 255, -1)
    cv2.rectangle(m, (0, r), (w - 1, h - r - 1), 255, -1)
    for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)):
        cv2.circle(m, (cx, cy), r, 255, -1, lineType=cv2.LINE_AA)
    return m


def caixa_girada(x, y, w, h, rot=0.0, escala=1.0):
    """[x0, y0, x1, y1] da peça girada em torno do centro (para a geometria e para a área que muda)."""
    cx, cy = x + w / 2, y + h / 2
    a = math.radians(rot)
    hw = (abs(w * math.cos(a)) + abs(h * math.sin(a))) * escala / 2
    hh = (abs(w * math.sin(a)) + abs(h * math.cos(a))) * escala / 2
    return [cx - hw, cy - hh, cx + hw, cy + hh]


class Peca:
    """Uma camada pronta para colar: alfa fixo (canto arredondado ou o alfa do PNG), giro, escala do pop e sombra.
    A geometria de cada escala fica guardada: depois da entrada, todo quadro reaproveita a mesma."""

    def __init__(self, c, alfa):
        self.c = c
        self.alfa = alfa.astype(np.float32) / 255.0
        self.x, self.y = float(c["x"]), float(c["y"])
        self.w, self.h = alfa.shape[1], alfa.shape[0]
        self.rot = float(c.get("rot") or 0)
        self.sombra = float(c.get("sombra") or 0)
        self.cache = {}

    def geom(self, escala):
        k = round(escala, 3)
        g = self.cache.get(k)
        if g:
            return g
        margem = (14 + 3 * 18 + 4) if self.sombra > 0 else 2
        b = caixa_girada(self.x, self.y, self.w, self.h, self.rot, escala)
        x0, y0 = int(max(0, math.floor(b[0] - margem))), int(max(0, math.floor(b[1] - margem)))
        x1, y1 = int(min(W, math.ceil(b[2] + margem))), int(min(H, math.ceil(b[3] + margem)))
        if x1 <= x0 or y1 <= y0:
            self.cache[k] = g = (None,)
            return g
        reto = abs(self.rot) < 1e-3 and abs(escala - 1) < 1e-3 and float(self.x).is_integer() and float(self.y).is_integer()
        if reto:
            M = None
            a = np.zeros((y1 - y0, x1 - x0), np.float32)
            px, py = int(self.x) - x0, int(self.y) - y0
            sx0, sy0 = max(0, -px), max(0, -py)
            sx1, sy1 = min(self.w, (x1 - x0) - px), min(self.h, (y1 - y0) - py)
            a[py + sy0:py + sy1, px + sx0:px + sx1] = self.alfa[sy0:sy1, sx0:sx1]
        else:
            cx, cy = self.x + self.w / 2, self.y + self.h / 2
            M = cv2.getRotationMatrix2D((self.w / 2, self.h / 2), -self.rot, escala)
            M[0, 2] += cx - self.w / 2 - x0
            M[1, 2] += cy - self.h / 2 - y0
            a = cv2.warpAffine(self.alfa, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=0)
        s = None
        if self.sombra > 0:   # sombra: o alfa borrado (em 1/4) e descido 14 px
            ph, pw = max(2, a.shape[0] // 4), max(2, a.shape[1] // 4)
            s = cv2.GaussianBlur(cv2.resize(a, (pw, ph), interpolation=cv2.INTER_AREA), (0, 0), 18 / 4)
            s = cv2.resize(s, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_LINEAR)
            s = np.roll(s, 14, axis=0)
            s[:14] = 0
            s *= self.sombra
        g = (x0, y0, x1, y1, M, a, s)
        self.cache[k] = g
        return g

    def colar(self, img, rgb, escala, alfa):
        g = self.geom(escala)
        if g[0] is None or alfa <= 0.001:
            return
        x0, y0, x1, y1, M, a, s = g
        reg = img[y0:y1, x0:x1]
        if s is not None:
            sa = s * alfa if alfa < 1 else s
            reg[:] = misturar(reg, np.zeros_like(reg), sa)
        if M is None:
            pec = np.zeros_like(reg)
            px, py = int(self.x) - x0, int(self.y) - y0
            sx0, sy0 = max(0, -px), max(0, -py)
            sx1, sy1 = min(self.w, (x1 - x0) - px), min(self.h, (y1 - y0) - py)
            pec[py + sy0:py + sy1, px + sx0:px + sx1] = rgb[sy0:sy1, sx0:sx1]
        else:
            pec = cv2.warpAffine(rgb, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=0)
        reg[:] = misturar(reg, pec, a * alfa if alfa < 1 else a)

    def caixa(self, escala=1.0):
        g = self.geom(escala)
        return None if g[0] is None else g[:4]


def anim(c, t):
    """(escala, alfa) da camada no tempo t: pop = escala 0,82→1 com alfa; número = só alfa."""
    u, pop = 1.0, False
    e = c.get("entra") or {}
    if e.get("dur", 0) > 0:
        u = suave((t - c["de"]) / e["dur"])
        pop = pop or e.get("efeito") == "pop"
    s = c.get("sai") or {}
    if s.get("dur", 0) > 0:
        v = suave((c["ate"] - t) / s["dur"])
        if v < u:
            u = v
            pop = s.get("efeito") == "pop"
    return (0.82 + 0.18 * u) if pop else 1.0, u


def ler_png(p):
    """PNG/JPG → (rgb uint8, alfa uint8)."""
    img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise SystemExit(f"Não consegui abrir a imagem {p}.")
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    if img.shape[2] == 3:
        img = np.dstack([img, np.full(img.shape[:2], 255, np.uint8)])
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
    return np.ascontiguousarray(img[..., :3]), np.ascontiguousarray(img[..., 3])


def recortar_alfa(rgb, a):
    """Corta o PNG de tela cheia na área que tem desenho. Devolve (rgb, alfa, x, y)."""
    ys, xs = np.nonzero(a > 0)
    if not len(xs):
        return rgb[:1, :1], a[:1, :1], 0, 0
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return np.ascontiguousarray(rgb[y0:y1, x0:x1]), np.ascontiguousarray(a[y0:y1, x0:x1]), int(x0), int(y0)


class Sobre:
    """PNG parado por cima (cartão ou legenda): rgb, peso e posição, prontos para misturar."""

    def __init__(self, png, x=0, y=0, cortar=True):
        rgb, a = ler_png(png)
        if cortar:
            rgb, a, dx, dy = recortar_alfa(rgb, a)
            x, y = x + dx, y + dy
        self.x, self.y = int(x), int(y)
        x0, y0 = max(0, self.x), max(0, self.y)
        x1, y1 = min(W, self.x + rgb.shape[1]), min(H, self.y + rgb.shape[0])
        self.r = (x0, y0, x1, y1)
        rgb = rgb[y0 - self.y:y1 - self.y, x0 - self.x:x1 - self.x]
        a = a[y0 - self.y:y1 - self.y, x0 - self.x:x1 - self.x]
        self.cheio = bool((a == 255).all())
        self.rgb = np.ascontiguousarray(rgb)
        self.peso = a.astype(np.float32) / 255.0

    def colar(self, img):
        x0, y0, x1, y1 = self.r
        if x1 <= x0 or y1 <= y0:
            return
        if self.cheio:
            img[y0:y1, x0:x1] = self.rgb
        else:
            reg = img[y0:y1, x0:x1]
            reg[:] = misturar(reg, self.rgb, self.peso)


# ---------------------------------------------------------------- um bloco

def preparar(P):
    fps = P["fps"]
    q = lambda t: int(round(float(t) * fps))
    divs = [dict(d, q0=q(d["de"]), q1=q(d["ate"]), pessoa=sorted(
        [dict(p, q0=q(p["de"])) for p in d["pessoa"]], key=lambda p: p["q0"])) for d in P.get("divididas", [])]
    cams = []
    for c in P.get("camadas", []):
        c = dict(c, q0=q(c["de"]), q1=q(c["ate"]))
        if c["tipo"] == "video":
            c["trechos"] = [dict(s, q0=q(s["de"]), q1=q(s["ate"])) for s in c["trechos"]]
        cams.append(c)
    cartoes = [dict(x, q0=q(x["de"]), q1=q(x["ate"])) for x in P.get("cartoes", [])]
    legs = [dict(x, q0=q(x["de"]), q1=q(x["ate"])) for x in P.get("legendas", [])]
    masc = P.get("mascaras", [])
    return divs, cams, cartoes, legs, masc


def bloco(P, k):
    cv2.setNumThreads(2)
    fps, ft = P["fps"], P["fps_txt"]
    i0, i1 = P["blocos"][k]
    divs, cams, cartoes, legs, masc = preparar(P)
    # só o que aparece neste bloco
    vivo = lambda x: x["q0"] < i1 and x["q1"] > i0
    divs, cams = [d for d in divs if vivo(d)], [c for c in cams if vivo(c)]
    cartoes, legs = [c for c in cartoes if vivo(c)], [x for x in legs if vivo(x)]
    masc = [m for m in masc if m["q0"] < i1 and m["q1"] > i0]
    pecas, sobres, leitores = {}, {}, {}

    saida = Path(P["dados"]) / "blocos" / f"b-{k:03d}.mp4"
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", ft,
         "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", *codificador(P),
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
         "-an", str(saida)], stdin=subprocess.PIPE)
    lv = Leitor(P["video"], W, H, max(0.0, (i0 - 0.25) / fps) if i0 else 0.0, ft)
    lm = None

    def sobre(x, cortar=True):
        key = (x["png"], x.get("x", 0), x.get("y", 0))
        if key not in sobres:
            sobres[key] = Sobre(x["png"], x.get("x", 0), x.get("y", 0), cortar)
        return sobres[key]

    def peca_de(c):
        if c["id"] not in pecas:
            if c["tipo"] == "imagem":
                rgb, a = ler_png(c["arquivo"])
                if c.get("cheia"):
                    rgb, a, dx, dy = recortar_alfa(rgb, a)
                    c = dict(c, x=c.get("x", 0) + dx, y=c.get("y", 0) + dy)
                elif c.get("w") and (rgb.shape[1] != int(c["w"]) or (c.get("h") and rgb.shape[0] != int(c["h"]))):
                    w = int(c["w"])
                    h = int(c.get("h") or round(rgb.shape[0] * w / rgb.shape[1]))
                    rgb = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA)
                    a = cv2.resize(a, (w, h), interpolation=cv2.INTER_AREA)
                pecas[c["id"]] = (Peca(c, a), rgb)
            else:
                a = canto_redondo(int(c["w"]), int(c["h"]), int(c.get("raio") or 0))
                pecas[c["id"]] = (Peca(c, a), None)
        return pecas[c["id"]]

    def quadro_video(c, i):
        """Quadro da camada de vídeo no índice i (abre o leitor do trecho na primeira vez)."""
        s = next((s for s in c["trechos"] if s["q0"] <= i < s["q1"]), c["trechos"][-1])
        key = (c["id"], id(s))
        if key not in leitores:
            for kk in [kk for kk in leitores if kk[0] == c["id"]]:
                leitores.pop(kk).fechar()
            off = (i - s["q0"]) / fps
            lim = None
            if s.get("dur"):
                if off >= s["dur"]:
                    off = max(0.0, s["dur"] - 1.0 / fps)
                lim = s["dur"] - off
            leitores[key] = Leitor(s["arquivo"], int(c["w"]), int(c["h"]), s["src"] + off, ft, caixa=s.get("caixa"),
                                   limite=lim)
        q = leitores[key].ler()
        return q if q is not None else np.zeros((int(c["h"]), int(c["w"]), 3), np.uint8)

    t_ini = time.time()
    for i in range(i0, i1):
        t = i / fps
        img = lv.ler()
        if img is None:
            break
        m = None
        mm = next((m for m in masc if m["q0"] <= i < m["q1"]), None)
        if mm is not None:
            if lm is None or lm[0] is not mm:
                if lm:
                    lm[1].fechar()
                lm = (mm, Leitor(mm["arquivo"], W, H, max(0.0, (i - mm["q0"] - 0.25) / fps) if i > mm["q0"] else 0.0,
                                 ft, cinza=True))
            m = lm[1].ler()
        ativas = [c for c in cams if c["q0"] <= i < c["q1"]]
        for kk in [kk for kk in leitores if not any(c["id"] == kk[0] for c in ativas)]:
            leitores.pop(kk).fechar()
        div = next((d for d in divs if d["q0"] <= i < d["q1"]), None)
        cs = [x for x in cartoes if x["q0"] <= i < x["q1"]]
        ls = [x for x in legs if x["q0"] <= i < x["q1"]]
        if not (ativas or div or cs or ls):
            enc.stdin.write(img.data)          # quadro sem nada por cima passa direto
            continue
        frames = {c["id"]: quadro_video(c, i) for c in ativas if c["tipo"] == "video"}
        if div:
            corte = int(div.get("corte", H // 2))
            p = [p for p in div["pessoa"] if p["q0"] <= i] or div["pessoa"][:1]
            p = p[-1]
            e, ry = float(p.get("escala") or 1.0), int(p.get("recorte_y") or 0)
            tela = np.zeros_like(img)
            hb = H - corte
            if abs(e - 1) > 1e-3:
                # só as linhas que viram a janela são reduzidas (a pessoa menor, com laterais borradas)
                ry = max(0, min(ry, int(H * e) - hb))
                ya, yb = int(ry / e), min(H, int(math.ceil((ry + hb) / e)))
                faixa = cv2.resize(img[ya:yb], (int(round(W * e)), hb), interpolation=cv2.INTER_AREA)[:, :W]
                fundo = borrar(faixa, W, hb) if div.get("laterais", "borrado") == "borrado" else np.zeros((hb, W, 3), np.uint8)
                x0 = (W - faixa.shape[1]) // 2
                fundo[:faixa.shape[0], x0:x0 + faixa.shape[1]] = faixa
                tela[corte:] = fundo
            else:
                ry = max(0, min(ry, H - hb))
                tela[corte:] = img[ry:ry + hb]
            for c in ativas:
                if c.get("lugar") == "topo":
                    # vídeo nítido no centro; nas laterais, o mesmo vídeo ampliado e borrado
                    q = frames[c["id"]] if c["tipo"] == "video" else peca_de(c)[1]
                    q = q[:corte, :W]
                    fundo = borrar(q, W, corte)
                    x0, y0 = (W - q.shape[1]) // 2, (corte - q.shape[0]) // 2
                    fundo[y0:y0 + q.shape[0], x0:x0 + q.shape[1]] = q
                    tela[:corte] = fundo
            img = tela
        else:
            atras = [c for c in ativas if c.get("lugar") == "atras"]
            if atras and m is not None:
                caixas = []
                for c in atras:
                    pc, rgb = peca_de(c)
                    caixas.append(pc.caixa(anim(c, t)[0]))
                caixas = [b for b in caixas if b]
                if caixas:
                    x0, y0 = min(b[0] for b in caixas), min(b[1] for b in caixas)
                    x1, y1 = max(b[2] for b in caixas), max(b[3] for b in caixas)
                    orig = img[y0:y1, x0:x1].copy()
                    for c in atras:
                        pc, rgb = peca_de(c)
                        esc, alfa = anim(c, t)
                        pc.colar(img, frames[c["id"]] if c["tipo"] == "video" else rgb, esc, alfa)
                    peso = m[y0:y1, x0:x1].astype(np.float32) * (1 / 255.0)
                    img[y0:y1, x0:x1] = misturar(img[y0:y1, x0:x1], orig, peso)
        for x in cs:
            sobre(x, cortar=True).colar(img)
        for c in ativas:
            if c.get("lugar", "frente") == "frente":
                pc, rgb = peca_de(c)
                esc, alfa = anim(c, t)
                pc.colar(img, frames[c["id"]] if c["tipo"] == "video" else rgb, esc, alfa)
        for x in ls:
            sobre(x).colar(img)
        enc.stdin.write(np.ascontiguousarray(img).data)
    lv.fechar()
    if lm:
        lm[1].fechar()
    for l in leitores.values():
        l.fechar()
    enc.stdin.close()
    enc.wait()
    if enc.returncode:
        raise SystemExit(f"O ffmpeg falhou ao gravar o bloco {k}.")
    print(f"bloco {k}: {i1 - i0} quadros em {time.time() - t_ini:.1f} s", flush=True)


# ---------------------------------------------------------------- o vídeo inteiro

def compor(P):
    """Divide em blocos, compõe em paralelo, emenda sem recodificar e põe o áudio. Devolve o tempo gasto (s)."""
    t0 = time.time()
    dados = Path(P["dados"])
    (dados / "blocos").mkdir(parents=True, exist_ok=True)
    for f in (dados / "blocos").glob("b-*.mp4"):
        f.unlink()
    n = P["quadros"]
    trab = P.get("trabalhadores") or max(1, min(6, (os.cpu_count() or 4) // 2))
    tam = max(90, math.ceil(n / (trab * 2)))
    P["blocos"] = [(a, min(n, a + tam)) for a in range(0, n, tam)]
    P.setdefault("threads_x264", max(1, (os.cpu_count() or 4) // trab))
    plano = dados / "compor.json"
    plano.write_text(json.dumps(P, ensure_ascii=False), encoding="utf-8")
    fila, rodando, feitos, erro = list(range(len(P["blocos"]))), [], 0, None
    while fila or rodando:
        while fila and len(rodando) < trab:
            k = fila.pop(0)
            rodando.append((k, subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--bloco", str(plano), str(k)],
                                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
        for k, p in list(rodando):
            if p.poll() is not None:
                saida = p.stdout.read()
                rodando.remove((k, p))
                if p.returncode:
                    erro = erro or saida[-1500:]
                feitos += 1
                print(f"  {feitos}/{len(P['blocos'])} blocos", flush=True)
        time.sleep(0.05)
    if erro:
        raise SystemExit("A composição falhou:\n" + erro)
    lista = dados / "blocos" / "lista.txt"
    lista.write_text("".join(f"file 'b-{k:03d}.mp4'\n" for k in range(len(P["blocos"]))), encoding="utf-8")
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-i", P["video"]]
    sons = P.get("audio") or []
    for s in sons:
        cmd += ["-ss", f"{s['src']:.3f}", "-t", f"{s['ate'] - s['de']:.3f}", "-i", s["arquivo"]]
    if sons:
        fil = [f"[1:a]aresample=48000[a0]"]
        for j, s in enumerate(sons, 2):
            ms = int(round(s["de"] * 1000))
            fil.append(f"[{j}:a]aresample=48000,volume={s['ganho']}dB,adelay={ms}:all=1[a{j - 1}]")
        fil.append("".join(f"[a{j}]" for j in range(len(sons) + 1)) +
                   f"amix=inputs={len(sons) + 1}:normalize=0:duration=first[a]")
        cmd += ["-filter_complex", ";".join(fil), "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a?", "-c:a", "copy" if P.get("audio_codec") == "aac" else "aac"]
    cmd += ["-c:v", "copy", "-t", f"{n / P['fps']:.4f}", "-movflags", "+faststart", P["saida"]]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("O ffmpeg falhou ao emendar os blocos:\n" + r.stderr[-1500:])
    return time.time() - t0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--bloco":
        bloco(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")), int(sys.argv[3]))
    else:
        print("compor.py é chamado pelo inserir.py. Rode o inserir.py.")
        sys.exit(1)
