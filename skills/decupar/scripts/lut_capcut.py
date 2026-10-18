# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26", "scipy>=1.11", "opencv-python-headless>=4.8,<5"]
# ///
"""/decupar: LUT de cor copiado de um vídeo que a pessoa já exportou do CapCut (ou de outro editor).

Uso:  uv run "<skill>/scripts/lut_capcut.py" "<bruto>" "<exportação do editor>" "<saída.cube>"
      ... --comparar "<outro.cube>"   mede também outro LUT nos mesmos quadros de validação

A exportação é o mesmo bruto, cortado e com a cor que a pessoa gosta, na mesma velocidade e no mesmo
enquadramento (zoom leve serve). O script:
  1. casa os dois vídeos: o som acha o tempo de cada trecho, a imagem acha o quadro exato;
  2. ajusta um LUT 33×33×33 (mínimos quadrados, interpolação tetraédrica igual à do ffmpeg, suavizado);
  3. aplica o LUT com o ffmpeg em trechos que ficaram fora do ajuste e mede a diferença de cor (ΔE00).
Grava o .cube e, ao lado, <nome>-comparacao.jpg (bruto | bruto + LUT | exportação). Quem chama é a
/minha-edicao, uma vez por pessoa; a saída vai para marca/cor/ e o cortes.json usa {"look": {"lut": ...}}.
Última linha: JSON com o ΔE00 e o resultado (até 2 "aceita"; de 2 a 3 "atenção", a pessoa olha a
comparação; acima de 3 "refaz").
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import scipy.sparse as sp
from scipy.ndimage import distance_transform_edt
from scipy.sparse.linalg import cg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import checar_ffmpeg, fmt_num, hwaccel, sair, sondar, utf8  # noqa: E402

N = 33                     # LUT 33³
TAXA = 4000                # Hz; som leve para casar os tempos (voz ainda reconhecível)
CANDIDATOS = 60            # momentos da exportação testados
FORA = 5                   # trechos inteiros que ficam fora do ajuste, para validar
AMOSTRAS = 100_000         # pixels por quadro no ajuste
BORDA = 24                 # px da borda que não entram (vinheta, moldura)


def ffmpeg_bytes(cmd, cwd=None):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", *map(str, cmd)], capture_output=True, cwd=cwd)
    if r.returncode != 0:
        sair(f"O ffmpeg falhou:\n{r.stderr.decode(errors='replace')[-800:]}")
    return r.stdout


def som(video, faixa):
    raw = ffmpeg_bytes(["-i", video, "-map", f"0:a:{faixa}", "-vn", "-ac", "1", "-ar", TAXA, "-f", "s16le", "-"])
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def quadros(video, ss, n, w, h, hw=()):
    """n quadros a partir do primeiro com tempo >= ss, em w×h RGB (a conversão padrão do ffmpeg, a do render)."""
    raw = ffmpeg_bytes([*hw, "-ss", f"{max(0.0, ss):.6f}", "-i", video, "-frames:v", n,
                        "-vf", f"scale={w}:{h},format=rgb24", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    return np.frombuffer(raw, np.uint8)[: len(raw) // (w * h * 3) * (w * h * 3)].reshape(-1, h, w, 3)


def ncc(a, b):
    a = cv2.resize(cv2.cvtColor(a, cv2.COLOR_RGB2GRAY), (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)
    b = cv2.resize(cv2.cvtColor(b, cv2.COLOR_RGB2GRAY), (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)
    a, b = a[30:-30, 20:-20] - a[30:-30, 20:-20].mean(), b[30:-30, 20:-20] - b[30:-30, 20:-20].mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))


# ---------------------------------------------------------------- 1. casar os vídeos

def cortes_da_exportacao(ref, info_r):
    """Emendas da exportação: salto grande de imagem entre um quadro e o seguinte."""
    w, h = 64, max(2, int(round(64 * info_r["altura"] / info_r["largura"] / 2)) * 2)
    raw = ffmpeg_bytes(["-i", ref, "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-pix_fmt", "gray", "-"])
    f = np.frombuffer(raw, np.uint8)[: len(raw) // (w * h) * (w * h)].reshape(-1, h, w).astype(np.float32)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    fps = info_r["fps_num"] / info_r["fps_den"]
    return (np.where(d > max(6 * np.median(d), 4))[0] + 1) / fps, len(f) / fps


def casar_som(sb, sr, emendas, dur):
    """Para momentos da exportação longe das emendas: onde o mesmo som está no bruto (correlação normalizada)."""
    n = 1 << int(np.ceil(np.log2(len(sb) + 2 * TAXA * 2)))
    S = np.fft.rfft(sb, n)
    cs = np.concatenate([[0], np.cumsum(sb.astype(np.float64) ** 2)])
    out = []
    for t in np.linspace(2, dur - 2, CANDIDATOS):
        antes, depois = emendas[emendas <= t], emendas[emendas > t]
        a0 = antes[-1] if len(antes) else 0.0
        a1 = depois[0] if len(depois) else dur
        if t - a0 < 0.4 or a1 - t < 0.4:
            continue
        w0, w1 = max(a0 + 0.05, t - 1.0), min(a1 - 0.05, t + 1.0)
        if w1 - w0 < 0.8:
            continue
        tm = sr[int(w0 * TAXA): int(w1 * TAXA)]
        if len(tm) < TAXA // 2 or np.std(tm) < 1e-3:
            continue
        c = np.fft.irfft(S * np.fft.rfft(tm[::-1], n), n)[len(tm) - 1: len(sb)]
        e = np.sqrt(np.maximum(cs[len(tm):] - cs[:-len(tm)], 0)) + 1e-9
        c = c[: len(e)] / e[: len(c)] / (np.linalg.norm(tm) + 1e-9)
        k = int(np.argmax(c))
        c2 = c.copy()
        c2[max(0, k - TAXA // 2): k + TAXA // 2] = 0
        if c[k] > 1.5 * c2.max():
            out.append({"t": float(t), "desloc": k / TAXA - w0})
    return out


def casar_quadros(bruto, ref, info_b, info_r, pares):
    """Quadro exato: compara o quadro da exportação com 7 quadros do bruto em volta do tempo achado pelo som."""
    fb = info_b["fps_num"] / info_b["fps_den"]
    fr = info_r["fps_num"] / info_r["fps_den"]
    W, H = info_r["largura"], info_r["altura"]
    hw = hwaccel()

    def um(p):
        i = int(round(p["t"] * fr))
        r = quadros(ref, (i - 0.5) / fr, 1, W, H)
        j0 = max(0, int(round((p["t"] + p["desloc"]) * fb)) - 3)
        bs = quadros(bruto, (j0 - 0.5) / fb, 7, W, H, hw)
        if not len(r) or not len(bs):
            return None
        notas = [ncc(r[0], b) for b in bs]
        m = int(np.argmax(notas))
        if notas[m] < 0.9:
            return None
        return {**p, "ref": r[0], "bruto": bs[m], "t_bruto": (j0 + m) / fb, "trecho": round(p["desloc"] * 2) / 2}

    with ThreadPoolExecutor(4) as ex:
        return [x for x in ex.map(um, pares) if x is not None]


def alinhar(p):
    """Zoom ou deslocamento leve do editor: acha a transformação (ECC, nas bordas) e alinha o bruto."""
    def prep(im):
        g = cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255, (0, 0), 1.5)
        return cv2.resize(g, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    M = np.eye(2, 3, dtype=np.float32)
    try:
        cc, M = cv2.findTransformECC(prep(p["ref"]), prep(p["bruto"]), M, cv2.MOTION_AFFINE,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-6), None, 5)
    except cv2.error:
        return None
    if cc < 0.9:
        return None
    M[:, 2] *= 2
    h, w = p["ref"].shape[:2]
    valido = np.ones((h, w), bool)
    if np.abs(M - np.eye(2, 3)).max() > 1e-3 or np.abs(M[:, 2]).max() > 0.5:
        flags = cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP
        p["bruto"] = cv2.warpAffine(p["bruto"], M, (w, h), flags=flags)
        valido = cv2.warpAffine(np.ones((h, w), np.uint8), M, (w, h), flags=cv2.INTER_NEAREST + cv2.WARP_INVERSE_MAP) > 0
        valido = cv2.erode(valido.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    p["M"], p["valido"] = M, valido
    return p


# ---------------------------------------------------------------- 2. ajustar o LUT

def plano(im):
    """Pixels de área lisa (sem borda forte): neles o par bruto × exportação é a mesma cor, sem erro de alinhamento."""
    g = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gm = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
    m = cv2.dilate(gm, np.ones((5, 5), np.uint8)) < 40
    m[:BORDA] = m[-BORDA:] = False
    m[:, :BORDA] = m[:, -BORDA:] = False
    return m


def amostras(p, n, rng):
    a, b = p["bruto"], p["ref"]
    m = plano(a) & p["valido"] & (b.max(2) < 254) & (b.min(2) > 0)   # saída estourada não ensina nada
    yy, xx = np.nonzero(m)
    sel = rng.choice(len(yy), min(n, len(yy)), replace=False)
    af = cv2.GaussianBlur(a.astype(np.float32), (0, 0), 1.0)
    bf = cv2.GaussianBlur(b.astype(np.float32), (0, 0), 1.0)
    return af[yy[sel], xx[sel]] / 255.0, bf[yy[sel], xx[sel]] / 255.0


def tetra(x):
    """Vértices e pesos da interpolação tetraédrica do lut3d do ffmpeg (índice = (r*N + g)*N + b)."""
    s = np.clip(x, 0, 1) * (N - 1)
    p = np.minimum(np.floor(s).astype(int), N - 2)
    d = s - p
    ordem = np.argsort(-d, axis=1, kind="stable")
    ds = np.take_along_axis(d, ordem, 1)
    M = len(x)
    v = np.zeros((M, 4, 3), int)
    v[:, 0] = p
    v[:, 1] = p
    v[np.arange(M), 1, ordem[:, 0]] += 1
    v[:, 2] = v[:, 1]
    v[np.arange(M), 2, ordem[:, 1]] += 1
    v[:, 3] = p + 1
    w = np.stack([1 - ds[:, 0], ds[:, 0] - ds[:, 1], ds[:, 1] - ds[:, 2], ds[:, 2]], 1)
    return (v[..., 0] * N + v[..., 1]) * N + v[..., 2], w


def laplaciano():
    ii = np.arange(N ** 3).reshape(N, N, N)
    rows, cols, vals = [], [], []
    for ax in range(3):
        a = np.take(ii, range(0, N - 1), axis=ax).ravel()
        b = np.take(ii, range(1, N), axis=ax).ravel()
        rows += [a, b, a, b]
        cols += [a, b, b, a]
        vals += [np.ones_like(a), np.ones_like(b), -np.ones_like(a), -np.ones_like(a)]
    return sp.csr_matrix((np.concatenate(vals).astype(float), (np.concatenate(rows), np.concatenate(cols))),
                         shape=(N ** 3, N ** 3))


def grade():
    r, g, b = np.meshgrid(*[np.linspace(0, 1, N)] * 3, indexing="ij")
    return np.stack([r.ravel(), g.ravel(), b.ravel()], 1)


def ajustar(X, Y, Xf, Yf):
    """min |A L - y|² + λ|Lap L|² + μ|L - P|² por canal. A = pesos tetraédricos; P = transformação afim global,
    puxada só onde não há dado (cores que o vídeo não mostrou). Escolhe λ, μ pelo erro fora do ajuste e, entre os
    quase iguais, o LUT mais monótono (sem inversão de brilho)."""
    n3 = N ** 3
    coef = np.linalg.lstsq(np.c_[np.ones(len(X)), X], Y, rcond=None)[0]
    P = np.c_[np.ones(n3), grade()] @ coef
    flat, w = tetra(X)
    A = sp.csr_matrix((w.ravel(), (np.repeat(np.arange(len(X)), 4), flat.ravel())), shape=(len(X), n3))
    AtA, AtY = (A.T @ A).tocsr(), A.T @ Y
    dens = np.bincount(flat.ravel(), w.ravel(), n3).reshape(N, N, N)
    rampa = (np.clip(distance_transform_edt(dens < 1.0) / 3.0, 0, 1) ** 2).ravel()
    Lp = laplaciano()
    LtL = (Lp.T @ Lp).tocsr()
    ff, wf = tetra(Xf)
    luma = np.array([0.2126, 0.7152, 0.0722])
    res = []
    for lam, mu in [(1.0, 0.0), (1.0, 0.03), (1.0, 0.3), (1.0, 3.0), (0.3, 0.3), (3.0, 0.3)]:
        reg = lam * len(X) / n3
        d = mu * reg * rampa + 1e-6 * reg
        H = (AtA + reg * LtL + sp.diags(d)).tocsr()
        pre = sp.diags(1 / H.diagonal())   # gradiente conjugado: o mesmo LUT da fatoração, uns 15x mais rápido
        L = np.stack([cg(H, AtY[:, c] + d * P[:, c], x0=P[:, c], rtol=1e-10, maxiter=5000, M=pre)[0]
                      for c in range(3)], 1)
        erro = np.abs((L[ff] * wf[..., None]).sum(1) - Yf).mean() * 255
        G = L.reshape(N, N, N, 3) @ luma
        inversao = float(np.mean([(np.diff(G, axis=a) < -0.5 / 255).mean() for a in range(3)]))
        res.append((erro, inversao, lam, L))
    melhor = min(r[0] for r in res)
    return min([r for r in res if r[0] <= melhor + 0.03], key=lambda r: (r[1], -r[2]))[3]


def gravar_cube(L, caminho, titulo):
    Lw = np.clip(L + 0.5 / 255, 0, 1).reshape(N, N, N, 3)   # +0,5/255: o lut3d trunca na saída de 8 bits
    linhas = [f'TITLE "{titulo}"', f"LUT_3D_SIZE {N}", "DOMAIN_MIN 0 0 0", "DOMAIN_MAX 1 1 1"]
    for b in range(N):
        for g in range(N):
            for r in range(N):
                linhas.append("{:.6f} {:.6f} {:.6f}".format(*Lw[r, g, b]))
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- 3. validar com o ffmpeg

def lab(im):
    return cv2.cvtColor(im.astype(np.float32) / 255, cv2.COLOR_RGB2Lab)


def de2000(l1, l2):
    L1, a1, b1 = l1[..., 0], l1[..., 1], l1[..., 2]
    L2, a2, b2 = l2[..., 0], l2[..., 1], l2[..., 2]
    Cb = (np.hypot(a1, b1) + np.hypot(a2, b2)) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p, h2p = np.degrees(np.arctan2(b1, a1p)) % 360, np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where(C1p * C2p == 0, 0, dh)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh) / 2)
    Lbp, Cbp, hs = (L1 + L2) / 2, (C1p + C2p) / 2, h1p + h2p
    hbp = np.where(C1p * C2p == 0, hs, np.where(np.abs(h1p - h2p) <= 180, hs / 2,
                                                 np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)))
    T = (1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp))
         + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63)))
    dth = 30 * np.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / np.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -np.sin(np.radians(2 * dth)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


def com_lut(bruto, p, info_b, pasta, nome="lut.cube"):
    """O quadro do bruto passado pelo LUT com o ffmpeg, igual ao cortar.py (escala e lut3d tetraédrico).
    Roda com a pasta do lut.cube como pasta atual: o filtro lê o nome curto, sem caminho para escapar."""
    fb = info_b["fps_num"] / info_b["fps_den"]
    h, w = p["ref"].shape[:2]
    raw = ffmpeg_bytes([*hwaccel(), "-ss", f"{p['t_bruto'] - 0.5 / fb:.6f}", "-i", bruto, "-frames:v", "1",
                        "-vf", f"scale={w}:{h},lut3d=file={nome}:interp=tetrahedral,format=rgb24",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], cwd=pasta)
    im = np.frombuffer(raw, np.uint8)[: h * w * 3].reshape(h, w, 3)
    if not p["valido"].all():   # o editor deu zoom: alinha igual ao quadro do ajuste
        im = cv2.warpAffine(im, p["M"], (w, h), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
    return im


# ---------------------------------------------------------------- principal

def main():
    utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    outro = None
    if "--comparar" in sys.argv:
        outro = Path(sys.argv[sys.argv.index("--comparar") + 1]).expanduser()
        args.remove(sys.argv[sys.argv.index("--comparar") + 1])
    if len(args) != 3:
        sair(__doc__)
    t0 = time.time()
    checar_ffmpeg()
    bruto, ref, saida = Path(args[0]).expanduser(), Path(args[1]).expanduser(), Path(args[2]).expanduser()
    for p in (bruto, ref):
        if not p.is_file():
            sair(f"Não achei o arquivo: {p}")
    if saida.suffix.lower() != ".cube":
        sair("A saída precisa terminar em .cube.")
    info_b, info_r = sondar(bruto), sondar(ref)
    if info_b["faixa_audio"] is None or info_r["faixa_audio"] is None:
        sair("Os dois vídeos precisam ter som: é pelo som que eu acho o mesmo momento nos dois.")
    rb, rr = info_b["largura"] / info_b["altura"], info_r["largura"] / info_r["altura"]
    if abs(rb - rr) / rr > 0.03:
        sair("A exportação tem outro formato de quadro que o bruto (por exemplo, horizontal × vertical). "
             "Exporte do editor no mesmo formato do bruto.")
    print("Casando a exportação com o bruto (som e imagem)...", flush=True)
    emendas, dur = cortes_da_exportacao(ref, info_r)
    pares = casar_som(som(bruto, info_b["faixa_audio"]), som(ref, info_r["faixa_audio"]), emendas, dur)
    pares = [p for p in (alinhar(p) for p in casar_quadros(bruto, ref, info_b, info_r, pares)) if p]
    trechos = sorted({p["trecho"] for p in pares})
    if len(pares) < 8 or len(trechos) < 3:
        sair(f"Achei só {len(pares)} momentos iguais nos dois vídeos. Confira se a exportação é desse bruto, "
             "na mesma velocidade (1×) e sem trocar o enquadramento.")
    fora_t = [trechos[i] for i in np.linspace(1, len(trechos) - 2, min(FORA, len(trechos) - 2)).round().astype(int)]
    fora = []
    for t in fora_t:
        ks = [p for p in pares if p["trecho"] == t]
        fora.append(ks[len(ks) // 2])
    treino = [p for p in pares if p["trecho"] not in fora_t]
    print(f"{len(pares)} quadros casados em {len(trechos)} trechos · {len(treino)} no ajuste, "
          f"{len(fora)} trechos de fora para validar · {fmt_num(time.time() - t0)} s", flush=True)
    rng = np.random.default_rng(0)
    X, Y = map(np.concatenate, zip(*[amostras(p, AMOSTRAS, rng) for p in treino]))
    Xf, Yf = map(np.concatenate, zip(*[amostras(p, AMOSTRAS // 2, rng) for p in fora]))
    t1 = time.time()
    L = ajustar(X, Y, Xf, Yf)
    print(f"LUT ajustado em {fmt_num(time.time() - t1)} s ({len(X)} pixels)", flush=True)
    saida.parent.mkdir(parents=True, exist_ok=True)
    gravar_cube(L, saida, f"LUT copiado de {ref.name}")
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copyfile(saida, Path(tmp) / "lut.cube")
        if outro:
            shutil.copyfile(outro, Path(tmp) / "outro.cube")
        linhas, sem, com, com_outro = [], [], [], []
        for p in fora:
            lr = lab(p["ref"])
            m = np.zeros(p["ref"].shape[:2], bool)
            m[8:-8, 8:-8] = True
            m &= p["valido"]
            out = com_lut(bruto, p, info_b, tmp)
            sem.append(float(de2000(lab(p["bruto"]), lr)[m].mean()))
            com.append(float(de2000(lab(out), lr)[m].mean()))
            if outro:
                com_outro.append(float(de2000(lab(com_lut(bruto, p, info_b, tmp, "outro.cube")), lr)[m].mean()))
            linhas.append([cv2.resize(x, (360, int(360 * x.shape[0] / x.shape[1])), interpolation=cv2.INTER_AREA)
                           for x in (p["bruto"], out, p["ref"])])
    folha = np.vstack([np.hstack(r) for r in linhas[:3]])
    cv2.imwrite(str(saida.with_name(saida.stem + "-comparacao.jpg")), cv2.cvtColor(folha, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 88])
    d_com, d_sem = float(np.mean(com)), float(np.mean(sem))
    print(f"ΔE00 médio fora do ajuste: {fmt_num(d_com, 2)} com o LUT · {fmt_num(d_sem, 2)} sem LUT "
          f"(abaixo de 2 a diferença quase não se vê)")
    print(f"Por trecho: {' · '.join(fmt_num(x, 2) for x in com)}")
    if outro:
        print(f"{outro.name} nos mesmos quadros: {fmt_num(float(np.mean(com_outro)), 2)} "
              f"({' · '.join(fmt_num(x, 2) for x in com_outro)})")
    # régua do contrato (3.3): até 2 aceita; de 2 a 3, a pessoa olha a comparação e decide; acima de 3, refaz
    resultado = "refaz" if d_com > 3 or d_com >= d_sem else ("aceita" if d_com <= 2 else "atenção")
    if resultado == "refaz":
        print("ATENÇÃO: o LUT não chegou perto da exportação (ΔE00 acima de 3). Confira se os dois vídeos são o mesmo "
              "trecho; a exportação pode ter efeito que não é de cor (máscara, vinheta, filtro em parte do quadro).")
    elif resultado == "atenção":
        print("ATENÇÃO: ΔE00 entre 2 e 3. Mostre a comparação à pessoa antes de gravar o LUT na marca.")
    print(f"LUT: {saida} · comparação: {saida.stem}-comparacao.jpg (bruto | com o LUT | exportação)")
    print(f"Pronto em {fmt_num(time.time() - t0)} s.")
    print(json.dumps({"de00_com_lut": round(d_com, 3), "de00_sem_lut": round(d_sem, 3), "quadros": len(pares),
                      "resultado": resultado, "comparacao": str(saida.with_name(saida.stem + "-comparacao.jpg"))},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
