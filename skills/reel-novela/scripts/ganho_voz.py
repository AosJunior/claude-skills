# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy"]
# ///
"""/reel-novela, conferência da voz: o ganho da voz na entrega varia quanto? Alvo: 0,3 dB ou menos.

Uso:  uv run "<skill>/scripts/ganho_voz.py" <entrega.mp4> --voz <narracao.wav> [--inicio S]

Refaz a voz tratada da mixagem (a mesma cadeia do mixar.py) a partir da narração e, em janelas de 4 s com fala,
mede o ganho da voz na entrega pela projeção do áudio entregue sobre ela (música e efeitos não se correlacionam com a
voz e quase não pesam). Relata a variação (máximo − mínimo) em dB. Acima de 0,3 dB, algo no master está mexendo no
volume da voz (limitador agindo demais ou loudnorm dinâmico): confira antes de entregar.
Serve para a entrega com trilha e para a sem trilha. --inicio: onde a entrega começa na narração (prévia de trecho).
Sai com código 1 se a variação passar de 0,3 dB.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True   # sem __pycache__ dentro da skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import SR, ajuda, checar_ffmpeg, fmt_num, sair, segundos, utf8, voz_da_entrega  # noqa: E402
ajuda(__doc__)   # --help sai antes de importar numpy: funciona sem o uv ter baixado nada
import numpy as np  # noqa: E402

JANELA = 4.0
ALVO = 0.3


def main():
    utf8()
    ajuda(__doc__)
    checar_ffmpeg()
    a = sys.argv[1:]
    if not a or a[0].startswith("-") or "--voz" not in a:
        sair(__doc__)
    entrega = Path(a[0]).expanduser()
    voz = Path(a[a.index("--voz") + 1]).expanduser()
    inicio = segundos(a[a.index("--inicio") + 1]) if "--inicio" in a else 0.0
    for p in (entrega, voz):
        if not p.is_file():
            sair(f"Não achei {p}")
    y, v, lag = voz_da_entrega(entrega, voz, inicio)
    y = y.mean(1)
    J = int(JANELA * SR)
    ref = np.sqrt(np.mean(v ** 2))
    gs = []
    for i in range(0, len(v) - J + 1, J):
        vv, yy = v[i:i + J], y[i:i + J]
        if np.sqrt(np.mean(vv ** 2)) < ref * 0.3:   # janela quase sem fala
            continue
        gs.append((inicio + i / SR, 20 * np.log10(max(np.dot(yy, vv) / np.dot(vv, vv), 1e-9))))
    if len(gs) < 2:
        sair("Menos de duas janelas de 4 s com fala: use um trecho mais longo.")
    g = np.array([x[1] for x in gs])
    var = g.max() - g.min()
    print(f"{entrega.name}: atraso {lag} amostras · {len(g)} janelas de 4 s · ganho médio {fmt_num(g.mean(), 2)} dB · "
          f"variação {fmt_num(var, 2)} dB (de {fmt_num(g.min(), 2)} em {gs[int(np.argmin(g))][0]:.0f} s a "
          f"{fmt_num(g.max(), 2)} em {gs[int(np.argmax(g))][0]:.0f} s)")
    print("   " + " ".join(f"{t:.0f}:{d:+.2f}" for t, d in gs))
    print(f"Alvo: variação de {fmt_num(ALVO)} dB ou menos → {'ok' if var <= ALVO else 'ACIMA: o master está mexendo na voz'}")
    sys.exit(0 if var <= ALVO else 1)


if __name__ == "__main__":
    main()
