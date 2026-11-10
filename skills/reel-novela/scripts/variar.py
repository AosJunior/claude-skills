# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy"]
# ///
"""/reel-novela, efeitos: variação leve e determinística no som que se repete (o mesmo cartão que toca muitas vezes).

Uso:  uv run "<skill>/scripts/variar.py" <pasta da peça> [--tipos cartao,brilho] [--semente 20261105]

Roda DEPOIS do efeitos.py, a cada vez que ele roda: o efeitos.py regrava o sequencia/som/efeitos.json sem a variação.
Serve para o cartão que toca dezenas de vezes na mesma peça (26 cartões variados assim soaram naturais).

Para cada camada dos tipos pedidos (padrão: cartao), em ordem de tempo:
  tom     base pelo tamanho do objeto (evento com "tamanho": "grande" → −2 semitons; o resto → +1), mais um sorteio de
          ±1 semitom; dois seguidos ficam a 0,4 semitom ou mais um do outro;
  volume  sorteio de ±1,5 dB;
  neutro  evento com "neutro": true (os dois lados que precisam soar iguais) fica com o tom da base e o volume do
          evento, sem sorteio.
O som é reamostrado (o tom e a duração mudam juntos), gravado em sequencia/som/sons/var/ e o efeitos.json passa a
apontar para ele, com "som_base" (o original) e "variacao" (semitons e dB). Rodar de novo dá o mesmo resultado.

No eventos/<cena>.json:  {"t": 7.02, "tipo": "cartao", "var": 2, "tamanho": "grande", "motivo": "HANÓI gigante acende"}
"""
import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.dont_write_bytecode = True   # sem __pycache__ dentro da skill
sys.path.insert(0, str(AQUI))
from comum import SR, ajuda, gravar_audio, gravar_json, ler_audio, ler_json, sair, utf8  # noqa: E402
ajuda(__doc__)   # --help sai antes de importar numpy: funciona sem o uv ter baixado nada
import numpy as np  # noqa: E402


def opcao(args, nome, padrao):
    if nome in args:
        i = args.index(nome)
        if i + 1 >= len(args):
            sair(f"Falta o valor de {nome}.")
        return args[i + 1]
    return padrao


def main():
    utf8()
    ajuda(__doc__)
    args = sys.argv[1:]
    pos = [x for i, x in enumerate(args) if not x.startswith("--") and (i == 0 or not args[i - 1].startswith("--"))]
    if not pos:
        sair(__doc__)
    som = Path(pos[0]).expanduser() / "sequencia" / "som"
    arq = som / "efeitos.json"
    if not arq.is_file():
        sair(f"Não achei {arq}. Rode antes o efeitos.py na pasta da peça.")
    tipos = {t.strip() for t in opcao(args, "--tipos", "cartao").split(",") if t.strip()}
    rng = random.Random(int(opcao(args, "--semente", "20261105")))

    efs = ler_json(arq)
    (som / "sons" / "var").mkdir(parents=True, exist_ok=True)
    ult, n = None, 0
    for e in sorted(efs, key=lambda e: (e.get("no", e["t"]), e["t"])):
        if e.get("tipo") not in tipos:
            continue
        base = e.setdefault("som_base", e["som"])
        if "variacao" in e:              # o efeitos.py não guarda; aqui só se rodou duas vezes sem o efeitos.py no meio
            e["vol"] = round(e["vol"] - e["variacao"]["db"], 2)
        origem = som / base
        if not origem.is_file():
            continue
        st0 = -2.0 if e.get("tamanho") == "grande" else 1.0
        if e.get("neutro"):
            st, db = st0, 0.0
        else:
            st = st0 + rng.uniform(-1, 1)
            while ult is not None and abs(st - ult) < 0.4:
                st = st0 + rng.uniform(-1, 1)
            db = rng.uniform(-1.5, 1.5)
            ult = st
        x = ler_audio(origem)
        f = 2 ** (st / 12)
        idx = np.arange(int(len(x) / f)) * f
        y = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(x.shape[1])], 1)
        rel = f"sons/var/{Path(base).stem}-st{st:+.2f}.wav"
        gravar_audio(som / rel, y, sr=SR, codec="pcm_s16le")
        e["som"] = rel
        e["vol"] = round(e["vol"] + db, 2)
        e["variacao"] = {"semitons": round(st, 2), "db": round(db, 2)}
        n += 1
    gravar_json(arq, efs)
    print(f"Pronto: {n} efeito(s) de {', '.join(sorted(tipos))} com variação de tom e volume em {arq}.")
    if not n:
        print("Nenhum efeito variado: confira o --tipos e se o efeitos.py já rodou.")


if __name__ == "__main__":
    main()
