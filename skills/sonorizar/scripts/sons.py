# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""/sonorizar: lista os sons de uma pasta (trilhas e efeitos) com duração e volume, ou baixa um som por link.

Uso:  uv run "<skill>/scripts/sons.py" "<pasta>"
      uv run "<skill>/scripts/sons.py" --baixar "<link>" "<arquivo.wav>"   (igual no Mac e no Windows)

Procura .wav, .mp3, .m4a, .aif, .flac e .ogg em todas as subpastas. Até 6 s conta como efeito; de 30 s em diante,
como trilha. Com um creditos.md na pasta (o de marca/sons/), marca cada som que tem ou não tem licença anotada.
Sem ele, mostra os arquivos de licença ou créditos (txt, md, pdf, tsv) que achar, para conferir.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import AUDIO, checar_ffmpeg, fmt_num, fmt_tempo, ler_creditos, medir, sair, sondar, utf8  # noqa: E402


def baixar(url, destino):
    import urllib.request
    destino = Path(destino).expanduser()
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, destino)
    except Exception as e:  # noqa: BLE001
        sair(f"Não consegui baixar ({e}). O link do Epidemic Sound vale poucos minutos: peça um novo e baixe na hora.")
    print(f"Baixado: {destino} · {fmt_tempo(sondar(destino)['duracao'])}")


def main():
    utf8()
    checar_ffmpeg()
    if len(sys.argv) < 2:
        sair(__doc__)
    if sys.argv[1] == "--baixar":
        if len(sys.argv) < 4:
            sair(__doc__)
        return baixar(sys.argv[2], sys.argv[3])
    pasta = Path(sys.argv[1]).expanduser()
    if not pasta.is_dir():
        sair(f"Não achei a pasta {pasta}.")
    arqs = sorted(p for p in pasta.rglob("*") if p.suffix.lower() in AUDIO and not p.name.startswith("."))
    if not arqs:
        sair(f"Nenhum som em {pasta}.")
    cred_md = next((p for p in (pasta / "creditos.md", pasta / "sons" / "creditos.md") if p.is_file()), None)
    cred = ler_creditos(cred_md) if cred_md else {}
    grupos = {"trilha": [], "efeito": [], "outro": []}
    for p in arqs[:300]:
        d = sondar(p)["duracao"]
        tipo = "efeito" if d <= 6 else "trilha" if d >= 30 else "outro"
        m = medir(p)
        c = cred.get(p.name.lower())
        nota = "" if not cred_md else f"  · {c.get('titulo') or 'com crédito'}" if c and c.get("licenca") else "  · SEM licença no creditos.md"
        grupos[tipo].append(f"  {fmt_tempo(d)}  pico {fmt_num(m['pico']):>6} dBFS  {p.relative_to(pasta)}{nota}")
    for tipo, titulo in (("trilha", "Trilhas (30 s ou mais)"), ("efeito", "Efeitos (até 6 s)"),
                         ("outro", "Outros (entre 6 e 30 s)")):
        if grupos[tipo]:
            print(f"{titulo}: {len(grupos[tipo])}")
            print("\n".join(grupos[tipo]))
    if len(arqs) > 300:
        print(f"(mostrando 300 de {len(arqs)})")
    if cred_md:
        print(f"Créditos: {cred_md}")
        return
    lic = sorted(p for p in pasta.rglob("*") if p.suffix.lower() in {".txt", ".md", ".pdf", ".tsv", ".json"}
                 and any(k in p.name.lower() for k in ("licen", "credit", "fonte", "readme", "inventario")))
    print("Licenças ou créditos na pasta: " + (", ".join(str(p.relative_to(pasta)) for p in lic) if lic else "nenhum"))


if __name__ == "__main__":
    main()
