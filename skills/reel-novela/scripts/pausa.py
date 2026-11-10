# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy"]
# ///
"""/reel-novela, segurar a tela: põe uma pausa na narração aprovada sem narrar de novo (nem gastar crédito).

Uso:  uv run "<skill>/scripts/pausa.py" <pasta da peça> --em 5.85 --s 1.0

Em brutos/narracao/, insere <s> segundos de silêncio no instante <em> da narracao.wav e soma <s> a todo tempo depois
dele no palavras-voz.json e no narracao-blocos.json. O <em> precisa cair numa pausa da fala: entre o fim de uma
palavra e o começo da seguinte. Antes de mudar, guarda os três arquivos com o sufixo -antes-da-pausa (só na primeira
pausa; numa segunda, os de antes da primeira continuam guardados). No fim, imprime os próximos passos, com os dois
--fixa do ancorar.py que congelam a tela durante o silêncio.
"""
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.dont_write_bytecode = True   # sem __pycache__ dentro da skill
sys.path.insert(0, str(AQUI))
from comum import ajuda, checar_ffmpeg, gravar_audio, gravar_json, ler_audio, ler_json, sair, sondar, utf8  # noqa: E402
ajuda(__doc__)   # --help sai antes de importar numpy: funciona sem o uv ter baixado nada
import numpy as np  # noqa: E402


def valor(args, nome):
    if nome not in args or args.index(nome) + 1 >= len(args):
        sair(f"Falta {nome}. Uso: pausa.py <pasta da peça> --em <s> --s <s>")
    try:
        return float(args[args.index(nome) + 1].replace(",", "."))
    except ValueError:
        sair(f"{nome} precisa de um número em segundos")


def main():
    utf8()
    args = sys.argv[1:]
    ajuda(__doc__)
    checar_ffmpeg()
    if not args or args[0].startswith("--"):
        sair("Passe a pasta da peça. Uso: pausa.py <pasta da peça> --em <s> --s <s>")
    narr = Path(args[0]) / "brutos" / "narracao"
    em, s = valor(args, "--em"), valor(args, "--s")
    if not 0 < s <= 5:
        sair("--s vai de 0 a 5 s")
    wav, pal, blo = narr / "narracao.wav", narr / "palavras-voz.json", narr / "narracao-blocos.json"
    for p in (wav, pal, blo):
        if not p.is_file():
            sair(f"Não achei {p}")

    palavras, blocos = ler_json(pal), ler_json(blo)
    dentro = [p["w"] for p in palavras if p["ini"] < em < p["fim"]]
    if dentro:
        sair(f"{em} s cai dentro da palavra «{dentro[0]}». Escolha um instante na pausa entre duas palavras.")
    antes = max((p for p in palavras if p["fim"] <= em), key=lambda p: p["fim"], default=None)
    depois = min((p for p in palavras if p["ini"] >= em), key=lambda p: p["ini"], default=None)

    for p in (wav, pal, blo):
        guarda = p.with_name(f"{p.stem}-antes-da-pausa{p.suffix}")
        if not guarda.exists():
            shutil.copy2(p, guarda)

    info = sondar(wav)
    canais = max(1, info["canais"])
    x = ler_audio(wav, canais=canais)
    i = int(round(em * 48000))
    y = np.concatenate([x[:i], np.zeros((int(round(s * 48000)), canais), np.float32), x[i:]])
    gravar_audio(wav, y, codec="pcm_s16le")

    mais = lambda t: round(t + s, 3) if t >= em else t   # noqa: E731
    for p in palavras:
        p["ini"], p["fim"] = mais(p["ini"]), mais(p["fim"])
    for b in blocos:
        b["ini"], b["fim"] = mais(b["ini"]), mais(b["fim"])
    gravar_json(pal, palavras)
    gravar_json(blo, blocos)

    print(f"Pausa de {s:.2f} s em {em:.2f} s"
          + (f", entre «{antes['w']}» ({antes['fim']:.2f}) e «{depois['w']}» (agora em {depois['ini']:.2f})"
             if antes and depois else ""))
    print(f"narracao.wav: {info['duracao']:.2f} s → {sondar(wav)['duracao']:.2f} s. Os originais ficaram com o sufixo"
          " -antes-da-pausa.")
    print("Próximos passos (referencias/voz.md, «Narração mudou depois das cenas» e «Segurar a tela»):")
    print("  1. Na primeira mudança, palavras-voz.json do projeto → briefings/palavras-cenas.json (o tempo das cenas).")
    print("  2. Copie a narracao.wav e o palavras-voz.json novos para o projeto, como na montagem do projeto.")
    print("  3. Escolha T, o tempo do código em que a tela para: a cena já assentou e a saída dela ainda não começou.")
    print(f"     ancorar.py ... --fixa T=T --fixa T+0.01=T+{s + 0.01:.2f}   (por exemplo, T = {em:.2f}:"
          f" --fixa {em:.2f}={em:.2f} --fixa {em + 0.01:.2f}={em + 0.01 + s:.2f})")
    print(f"  4. A cena que segura ganha {s:.2f} s no data-duration; as seguintes, {s:.2f} s no data-start.")


if __name__ == "__main__":
    main()
