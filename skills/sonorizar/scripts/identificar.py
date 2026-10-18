# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["shazamio>=0.6"]
# ///
"""/sonorizar: descobre que música toca nos Reels da pessoa (Shazam), para achar o universo da trilha dela.

Uso:  uv run --python 3.12 "<skill>/scripts/identificar.py" "<reel1.mp4>" "<reel2.mp4>" ["<link do Reel>" ...]

Aceita vídeo ou áudio do computador e links (baixa com o yt-dlp, se ele estiver instalado). Escuta pedaços de 10 s
a cada 8 s e imprime, por vídeo, cada música reconhecida com o trecho do vídeo em que ela toca e o selo (quando o
Shazam sabe). Uma música achada num pedaço só pode ser engano: confira de ouvido. O que o Shazam não reconhece
fica como "não reconhecido"; nada é inventado.
O Python 3.13 quebra o shazamio: rode com `--python 3.12` (o uv baixa sozinho).
"""
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import checar_ffmpeg, ff, fmt_tempo, rodar, sair, sondar, utf8  # noqa: E402

JANELA, PASSO = 10.0, 8.0


def baixar(link, pasta):
    if not shutil.which("yt-dlp"):
        sair(f"Para ler links preciso do yt-dlp (Mac: brew install yt-dlp · Windows: winget install yt-dlp). "
             f"Ou baixe o Reel e me passe o arquivo. Link: {link}")
    r = rodar(["yt-dlp", "-q", "--no-playlist", "-f", "bestaudio/best", "-o", str(Path(pasta) / "%(id)s.%(ext)s"), link])
    arqs = sorted(Path(pasta).glob("*"))
    if r.returncode != 0 or not arqs:
        print(f"Não consegui baixar {link} (o Instagram às vezes pede login). Baixe o Reel e me passe o arquivo.")
        return None
    return arqs[0]


def trechos(achados):
    """Junta pedaços seguidos da mesma música: [(início, fim, pedaços)]."""
    out = []
    for t in sorted(achados):
        if out and t - out[-1][1] <= PASSO + 0.01:
            out[-1] = (out[-1][0], t + JANELA, out[-1][2] + 1)
        else:
            out.append((t, t + JANELA, 1))
    return out


def selo(track):
    for sec in track.get("sections") or []:
        for m in sec.get("metadata") or []:
            if str(m.get("title", "")).lower() in ("label", "selo", "gravadora"):
                return m.get("text")
    return None


async def identificar(arq, tmp, shazam):
    dur = sondar(arq)["duracao"]
    musicas, vazios, erros = {}, [], 0
    t = 0.0
    while t < max(dur - 3, 0.01):
        wav = Path(tmp) / "pedaco.wav"
        ff(["-ss", f"{t:.2f}", "-t", f"{JANELA}", "-i", str(arq), "-vn", "-ac", "1", "-ar", "44100", str(wav)])
        try:
            r = await shazam.recognize(str(wav))
        except Exception:  # noqa: BLE001 (rede ou limite do Shazam: conta como não reconhecido e avisa)
            r, erros = {}, erros + 1
        tr = r.get("track") if isinstance(r, dict) else None
        if tr:
            k = (tr.get("title") or "?", tr.get("subtitle") or "?")
            m = musicas.setdefault(k, {"tempos": [], "selo": selo(tr), "link": tr.get("url")})
            m["tempos"].append(t)
        else:
            vazios.append(t)
        t += PASSO
        await asyncio.sleep(0.4)
    return dur, musicas, vazios, erros


async def main_async(entradas):
    import warnings
    warnings.filterwarnings("ignore", category=SyntaxWarning)  # avisos antigos do pydub, sem efeito no resultado
    from shazamio import Shazam
    shazam = Shazam()
    with tempfile.TemporaryDirectory() as tmp:
        for i, e in enumerate(entradas, 1):
            if e.startswith(("http://", "https://")):
                pasta = Path(tmp) / f"baixado{i}"
                pasta.mkdir()
                arq = baixar(e, pasta)
                if arq is None:
                    continue
            else:
                arq = Path(e).expanduser()
                if not arq.is_file():
                    print(f"\nNão achei o arquivo {arq}.")
                    continue
            dur, musicas, vazios, erros = await identificar(arq, tmp, shazam)
            print(f"\n{Path(e).name if not e.startswith('http') else e} · {fmt_tempo(dur)}")
            if not musicas:
                print("  O Shazam não reconheceu nenhuma música neste vídeo.")
            for (titulo, artista), m in sorted(musicas.items(), key=lambda x: x[1]["tempos"][0]):
                tt = ", ".join(f"{fmt_tempo(a)} a {fmt_tempo(min(b, dur))}" for a, b, _ in trechos(m["tempos"]))
                n = len(m["tempos"])
                extra = f" · selo {m['selo']}" if m["selo"] else ""
                aviso = " · achada num pedaço só: confira de ouvido" if n == 1 else ""
                print(f"  {titulo} · {artista}{extra}\n    toca em {tt} ({n} pedaço{'s' if n > 1 else ''}){aviso}")
            if vazios and musicas:
                print(f"  Não reconhecido: {len(vazios)} de {len(vazios) + sum(len(m['tempos']) for m in musicas.values())}"
                      " pedaços (fala por cima, música feita para o vídeo ou fora do Shazam).")
            if erros:
                print(f"  ATENÇÃO: {erros} pedaços não foram ao Shazam (rede ou limite). Rode de novo daqui a pouco.")


def main():
    utf8()
    checar_ffmpeg()
    if sys.version_info >= (3, 13):
        sair("O shazamio não roda no Python 3.13 ou mais novo. Rode assim: uv run --python 3.12 "
             f"\"{Path(__file__).resolve()}\" <vídeos>")
    entradas = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not entradas:
        sair(__doc__)
    asyncio.run(main_async(entradas))


if __name__ == "__main__":
    main()
