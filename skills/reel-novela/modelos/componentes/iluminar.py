"""Pinta a luz do lugar no sprite, na resolução de origem (o HTML amplia com vizinho mais próximo).

Três perfis, pelo código de luz da bíblia:

- quente     jantar, festa: ambiente quente (#f1c697), lado esquerdo mais escuro, contorno creme da luminária
             em cima e à direita, contorno laranja da vela embaixo (queixo, mangas, copo).
- fria       cozinha no fim de tarde, escritório: ambiente frio e um pouco mais escuro, contorno branco-azulado da
             janela ou da lâmpada fria em cima e à esquerda.
- tela-azul  o telefone no rosto, no escuro: ambiente bem escuro e azul, contorno ciano forte nas bordas viradas para
             baixo e para a frente (queixo, mãos, peito), mais forte embaixo, e o rosto clareado de baixo para cima.

O contorno fica só dentro da silhueta: borda = pixel opaco cujo vizinho deslocado é transparente. O 1º pixel da
borda é o traço escuro do desenho e fica como está; a luz entra logo depois dele (senão a figura lê como adesivo).

Precisa de numpy e Pillow (com o uv: uv run --with numpy --with pillow python iluminar.py …).

Uso:
  python3 iluminar.py <entrada.png> <saida.png> --perfil quente|fria|tela-azul [--fim-visivel <linha>]
  --fim-visivel  a última linha do sprite que aparece no quadro (no busto, a cintura); padrão: a altura toda.
                 A luz de baixo cresce até ela.
"""
import argparse
import sys

if any(a in ("-h", "--help") for a in sys.argv[1:]):   # a ajuda sai antes de importar numpy e Pillow
    print(__doc__)
    sys.exit(0)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402


def borda(alfa, dx, dy, largura):
    """Pixels opacos a até `largura` passos de um transparente na direção (dx, dy)."""
    opaco = alfa > 0
    m = np.zeros_like(opaco)
    h, w = opaco.shape
    for k in range(1, largura + 1):
        viz = np.zeros_like(opaco)
        ys = slice(max(0, -dy * k), h - max(0, dy * k))
        yd = slice(max(0, dy * k), h - max(0, -dy * k))
        xs = slice(max(0, -dx * k), w - max(0, dx * k))
        xd = slice(max(0, dx * k), w - max(0, -dx * k))
        viz[ys, xs] = opaco[yd, xd]
        m |= opaco & ~viz
    return m


def tela(base, cor, peso):
    """Mistura em «tela» (luz somada) com peso por pixel."""
    return 1 - (1 - base) * (1 - np.asarray(cor) * peso[..., None])


def faixa(alfa, dx, dy, ate):
    return borda(alfa, dx, dy, ate) & ~borda(alfa, dx, dy, 1)


def quente(rgb, alfa, x, y, yv, fim):
    rgb = rgb * np.array([0xF1, 0xC6, 0x97]) / 255
    rgb = rgb * (1 - 0.38 * np.clip((0.55 - x) / 0.55, 0, 1))[..., None]
    lum = (faixa(alfa, 1, -1, 4) | faixa(alfa, 0, -1, 4)).astype(float)
    lum *= np.clip((0.42 - y) / 0.2, 0, 1) * np.clip((x - 0.3) / 0.35, 0, 1)
    rgb = tela(rgb, [1.0, 0.85, 0.62], 0.9 * lum)
    vel = faixa(alfa, 0, 1, 4).astype(float)
    vel *= np.clip((yv - fim * 0.3) / (fim * 0.7), 0, 1)
    return tela(rgb, [1.0, 0.58, 0.22], 0.85 * vel)


def fria(rgb, alfa, x, y, yv, fim):
    rgb = rgb * np.array([0xC4, 0xD0, 0xE6]) / 255 * 0.92
    rgb = rgb * (1 - 0.30 * np.clip((x - 0.45) / 0.55, 0, 1))[..., None]  # a janela fica à esquerda
    jan = (faixa(alfa, -1, -1, 4) | faixa(alfa, 0, -1, 3) | faixa(alfa, -1, 0, 3)).astype(float)
    jan *= np.clip((0.55 - y) / 0.35, 0, 1) * np.clip((0.7 - x) / 0.4, 0, 1)
    return tela(rgb, [0.80, 0.90, 1.0], 0.75 * jan)


def tela_azul(rgb, alfa, x, y, yv, fim):
    rgb = rgb * np.array([0x8E, 0xA6, 0xD2]) / 255 * 0.72
    # o rosto e o peito clareiam de baixo para cima, perto do centro (onde está o telefone)
    centro = np.clip(1 - np.abs(x - 0.5) / 0.45, 0, 1)
    sobe = np.clip((yv / max(fim, 1) - 0.08) / 0.5, 0, 1) * np.clip((0.75 - yv / max(fim, 1)) / 0.2, 0, 1)
    rgb = tela(rgb, [0.30, 0.62, 1.0], 0.22 * centro * sobe)
    cel = (faixa(alfa, 0, 1, 4) | faixa(alfa, 1, 1, 3) | faixa(alfa, -1, 1, 3)).astype(float)
    cel *= np.clip((yv - fim * 0.15) / (fim * 0.5), 0, 1)
    return tela(rgb, [0.45, 0.85, 1.0], 0.9 * cel)


PERFIS = {"quente": quente, "fria": fria, "tela-azul": tela_azul}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("--perfil", choices=sorted(PERFIS), required=True)
    ap.add_argument("--fim-visivel", type=int, default=None)
    a = ap.parse_args()

    im = np.asarray(Image.open(a.entrada).convert("RGBA")).astype(float) / 255
    rgb, alfa = im[..., :3], im[..., 3]
    h, w = alfa.shape
    fim = a.fim_visivel or h
    y = np.linspace(0, 1, h)[:, None] * np.ones((1, w))
    x = np.ones((h, 1)) * np.linspace(0, 1, w)[None, :]
    yv = np.arange(h)[:, None] * np.ones((1, w))
    rgb = PERFIS[a.perfil](rgb, alfa, x, y, yv, fim)
    out = np.dstack([np.clip(rgb, 0, 1), alfa])
    Image.fromarray((out * 255).round().astype(np.uint8)).save(a.saida)
    print(f"{a.saida}: {w}×{h}, perfil {a.perfil}, luz de baixo até a linha {fim}")


if __name__ == "__main__":
    main()
