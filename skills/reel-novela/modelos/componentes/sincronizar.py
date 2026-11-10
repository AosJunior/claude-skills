#!/usr/bin/env python3
"""Copia os componentes da série para um projeto motion de episódio (o HyperFrames não lê fora do projeto).

Uso:  python3 <pasta dos componentes>/sincronizar.py <projeto>
Ex.:  python3 componentes/sincronizar.py ep02/sequencia/motion

  novela.css, novela.js  → <projeto>/assets/novela/
  legenda.html           → <projeto>/compositions/legenda.html   (troca a legenda do esqueleto)
  fontes/*.woff2         → <projeto>/assets/fontes/               (Montserrat 400, 700, 900)
  fontes/OFL-montserrat.txt → <projeto>/assets/fontes/            (licença das fontes)

A mola (assets/mola.js) não passa por aqui: ela vem do esqueleto (modelos/motion/) com o montar_projeto.py.
Edite sempre na pasta dos componentes e sincronize: a cópia no projeto é sobrescrita.
Python 3.9 ou mais novo, só biblioteca padrão; igual no Mac e no Windows.
"""
import shutil
import sys
from pathlib import Path


def sair(msg):
    print("erro: " + msg, file=sys.stderr)
    sys.exit(1)


def copiar(origem, destino):
    if not origem.is_file():
        sair(f"falta {origem}. A pasta dos componentes está incompleta: reinstale a skill reel-novela.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)


def main():
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(__doc__)
        return
    if len(args) != 1:
        sair("uso: python3 sincronizar.py <pasta do projeto motion>")
    aqui = Path(__file__).resolve().parent
    proj = Path(args[0]).expanduser().resolve()
    if not (proj / "index.html").is_file():
        sair(f"{proj} não parece um projeto motion (falta index.html).")
    for nome in ("novela.css", "novela.js"):
        copiar(aqui / nome, proj / "assets" / "novela" / nome)
    copiar(aqui / "legenda.html", proj / "compositions" / "legenda.html")
    fontes = sorted((aqui / "fontes").glob("*.woff2"))
    if not fontes:
        sair(f"não achei as fontes .woff2 em {aqui / 'fontes'}.")
    for f in fontes:
        copiar(f, proj / "assets" / "fontes" / f.name)
    copiar(aqui / "fontes" / "OFL-montserrat.txt", proj / "assets" / "fontes" / "OFL-montserrat.txt")
    print(f"sincronizado: {proj} (assets/novela/, compositions/legenda.html, assets/fontes/)")


if __name__ == "__main__":
    main()
