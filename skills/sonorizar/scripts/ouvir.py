# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = [
#   "mlx-whisper>=0.4; sys_platform == 'darwin' and platform_machine == 'arm64'",
#   "faster-whisper>=1.1; sys_platform != 'darwin' or platform_machine != 'arm64'",
# ]
# ///
"""/sonorizar, conferência: escuta um pedaço do vídeo já com som e diz se a fala continua inteligível.

Uso:  uv run "<skill>/scripts/ouvir.py" "<vídeo com som>" --base "<vídeo sem trilha>" --de 00:30 --ate 00:50

Transcreve o mesmo pedaço nos dois vídeos (com Whisper, no computador) e compara: quantas palavras ditas sem
trilha continuam sendo ouvidas com a trilha por baixo. 95 % ou mais: a fala está limpa.
Usa o mesmo Whisper da /decupar (na primeira vez sem ela, instala e baixa o modelo, cerca de 2 GB).
"""
import os
import re
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import checar_ffmpeg, ff, fmt_num, fmt_tempo, sair, segundos, utf8  # noqa: E402

MODELO_MLX = "mlx-community/whisper-large-v3-turbo"
MODELO_FW = "large-v3-turbo"


def motor():
    from importlib.util import find_spec
    if os.environ.get("DECUPAR_MOTOR") != "faster-whisper" and find_spec("mlx_whisper"):
        return "mlx-whisper"
    if find_spec("faster_whisper"):
        return "faster-whisper"
    sair("Não achei o Whisper. Rode este script com `uv run` (ele instala sozinho).")


def transcrever(wav, qual):
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    if qual == "mlx-whisper":
        import mlx_whisper
        r = mlx_whisper.transcribe(str(wav), path_or_hf_repo=MODELO_MLX, language="pt")
        return " ".join(s["text"].strip() for s in r.get("segments", []))
    import wave
    import numpy as np
    from faster_whisper import WhisperModel
    with wave.open(str(wav), "rb") as f:
        audio = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    m = WhisperModel(MODELO_FW, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, language="pt", vad_filter=True)
    return " ".join(s.text.strip() for s in segs)


FALADO = {"pra": "para", "pro": "para", "ta": "esta", "tava": "estava", "to": "estou", "ce": "voce", "cê": "voce"}


def palavras(txt):
    """Palavras sem acento, com o falado igualado ao escrito ("pra" = "para"): o Whisper alterna entre os dois."""
    t = unicodedata.normalize("NFKD", txt.lower()).encode("ascii", "ignore").decode()
    return [FALADO.get(w, w) for w in re.findall(r"[a-z0-9]+", t)]


def juntar(ws, outras):
    """Junta duas palavras seguidas quando a outra transcrição tem a palavra emendada ("tik tok" = "tiktok")."""
    out, i = [], 0
    while i < len(ws):
        if i + 1 < len(ws) and ws[i] + ws[i + 1] in outras:
            out.append(ws[i] + ws[i + 1])
            i += 2
        else:
            out.append(ws[i])
            i += 1
    return out


def escutar(video, de, ate, pasta, qual):
    wav = Path(pasta) / f"{Path(video).stem}.wav"
    ff(["-ss", f"{de:.3f}", "-t", f"{ate - de:.3f}", "-i", str(video), "-map", "0:a:0", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(wav)])
    return transcrever(wav, qual)


def main():
    utf8()
    checar_ffmpeg()
    a = sys.argv[1:]
    if not a or a[0].startswith("-") or "--de" not in a or "--ate" not in a:
        sair(__doc__)
    video = Path(a[0]).expanduser()
    de, ate = segundos(a[a.index("--de") + 1]), segundos(a[a.index("--ate") + 1])
    base = Path(a[a.index("--base") + 1]).expanduser() if "--base" in a else None
    qual = motor()
    with tempfile.TemporaryDirectory() as tmp:
        com = escutar(video, de, ate, tmp, qual)
        print(f"Com som ({fmt_tempo(de)} a {fmt_tempo(ate)}): {com}")
        if not base:
            return
        wav_dir = Path(tmp) / "base"
        wav_dir.mkdir()
        sem = escutar(base, de, ate, wav_dir, qual)
    print(f"Sem trilha:                 {sem}")
    ps, pc = palavras(sem), palavras(com)
    ref, ouv = Counter(juntar(ps, set(pc))), Counter(juntar(pc, set(ps)))
    total = sum(ref.values())
    if not total:
        sair("Nesse pedaço não tem fala. Escolha um trecho em que a pessoa fala.")
    achadas = sum(min(n, ouv[w]) for w, n in ref.items())
    pct = 100 * achadas / total
    faltam = [w for w, n in ref.items() if ouv[w] < n]
    print(f"\nFala inteligível: {fmt_num(pct, 0)} % das palavras continuam sendo ouvidas com o som por baixo.")
    if faltam:
        print("Sumiram: " + ", ".join(faltam[:15]))
    if pct < 95:
        print("ATENÇÃO: a trilha ou um efeito está cobrindo a fala. Abaixe a trilha (\"abaixo_da_voz\" maior) "
              "ou tire o efeito desse pedaço.")


if __name__ == "__main__":
    main()
