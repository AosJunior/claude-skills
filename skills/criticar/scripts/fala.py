"""/criticar: a fala. Transcreve o vídeo final com tempo por palavra, caça gagueira e repetição, compara com o
texto esperado (decupagem/palavras-corte.json) e mede cada emenda no som."""
import difflib
import os
import re
import wave
from pathlib import Path

import numpy as np

from comum import gravar_json, ler_json, rodar, sair, token

IDIOMA = "pt"
MODELO_MLX = "mlx-community/whisper-large-v3-turbo"   # o mesmo da /decupar: o modelo baixado é reaproveitado
MODELO_FW = "large-v3-turbo"
VERSAO = 1
PERTO_EMENDA = 0.35          # s; diferença de texto a menos disso de uma emenda é defeito do corte
PAUSA_LONGA = 0.25           # s, no meio da frase
PAUSA_LONGA_PONTO = 0.45     # s, depois de pontuação
PAUSA_CURTA = 0.04           # s
SALTO_VOZ = 6.0              # dB entre a voz antes e depois da emenda
SALTO_FUNDO = 10.0           # dB no ruído de fundo (só aviso, e só sem trilha)


# ---------------------------------------------------------------- transcrição (mesmo motor da /decupar)

def motor():
    """Qual Whisper está instalado, sem importar (importar o mlx/torch leva segundos)."""
    from importlib.util import find_spec
    if os.environ.get("DECUPAR_MOTOR") != "faster-whisper" and find_spec("mlx_whisper"):
        return "mlx-whisper"
    if find_spec("faster_whisper"):
        return "faster-whisper"
    sair("Não achei o Whisper. Rode este script com `uv run` (ele instala sozinho).")


def _whisper(wav, qual):
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    palavras = []
    if qual == "mlx-whisper":
        import mlx_whisper
        r = mlx_whisper.transcribe(str(wav), path_or_hf_repo=MODELO_MLX, language=IDIOMA,
                                   word_timestamps=True, hallucination_silence_threshold=2.0,
                                   condition_on_previous_text=False)
        for s in r.get("segments", []):
            for w in s.get("words", []):
                palavras.append((w["word"], w["start"], w["end"], w.get("probability", 1.0)))
    else:
        from faster_whisper import WhisperModel
        with wave.open(str(wav), "rb") as f:
            audio = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        m = WhisperModel(MODELO_FW, device="cpu", compute_type="int8")
        segs, _ = m.transcribe(audio, language=IDIOMA, word_timestamps=True, vad_filter=True,
                               hallucination_silence_threshold=2.0, condition_on_previous_text=False)
        for s in segs:
            for w in s.words or []:
                palavras.append((w.word, w.start, w.end, w.probability))
    return [{"w": t.strip(), "a": round(float(a), 3), "b": round(max(float(a), float(b)), 3), "p": round(float(p), 3)}
            for t, a, b, p in palavras if t.strip()]


def transcrever(video, dados, refazer=False):
    """Palavras do vídeo final com tempo. Cache em critica/.dados/fala.json (mesmo arquivo = não refaz)."""
    st = Path(video).stat()
    qual = motor()
    assin = {"arquivo": str(Path(video).resolve()), "tamanho": st.st_size, "mtime": int(st.st_mtime), "versao": VERSAO}
    cache = Path(dados) / "fala.json"
    if cache.exists() and not refazer:
        try:
            d = ler_json(cache)
            if d.get("assinatura") == assin:
                return d["palavras"], qual, True
        except Exception:
            pass
    wav = Path(dados) / "fala16k.wav"
    r = rodar(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", video, "-map", "0:a:0", "-vn", "-ac", "1",
               "-ar", "16000", "-c:a", "pcm_s16le", wav])
    if r.returncode != 0:
        sair(f"Não consegui tirar o som do vídeo:\n{r.stderr[-600:]}")
    try:
        pal = _whisper(wav, qual)
    finally:
        wav.unlink(missing_ok=True)
    gravar_json(cache, {"assinatura": assin, "motor": qual, "palavras": pal})
    return pal, qual, False


# ---------------------------------------------------------------- texto esperado e emendas

def esperado(pc):
    """Palavras e emendas do palavras-corte.json (contrato 3.2). A emenda fica entre a última palavra de um
    trecho e a primeira do seguinte; com "trechos" [{n, a, b}] no arquivo, vale a borda exata."""
    pal = sorted([w for w in pc.get("palavras", []) if str(w.get("w", "")).strip()], key=lambda w: w["a"])
    exatas = {int(t["n"]): t for t in pc.get("trechos", []) if "n" in t and "b" in t}
    emendas = []
    for x, y in zip(pal, pal[1:]):
        if x.get("trecho") is not None and y.get("trecho") is not None and x["trecho"] != y["trecho"]:
            t = exatas[x["trecho"]]["b"] if x["trecho"] in exatas else (x["b"] + y["a"]) / 2
            emendas.append({"t": round(float(t), 3), "b": x["b"], "a": y["a"], "trecho": x["trecho"],
                            "antes": x["w"], "depois": y["w"], "exata": x["trecho"] in exatas})
    return pal, emendas


def quase(a, b):
    """Mesma palavra, ou 4+ letras com uma letra de diferença (o Whisper varia entre duas passadas)."""
    if a == b:
        return True
    if len(a) < 4 or len(b) < 4 or abs(len(a) - len(b)) > 1:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.8


# o Whisper escreve a mesma fala ora coloquial, ora por extenso: não é diferença de corte
COLOQUIAL = {"pra": ["para"], "pras": ["para", "as"], "pro": ["para", "o"], "pros": ["para", "os"],
             "tava": ["estava"], "tavam": ["estavam"], "ta": ["esta"], "to": ["estou"], "ce": ["voce"],
             "num": ["em", "um"], "numa": ["em", "uma"], "dum": ["de", "um"], "duma": ["de", "uma"]}


def _tokens(pal):
    out = []
    for w in pal:
        t = token(w["w"])
        for x in COLOQUIAL.get(t, [t] if t else []):
            out.append((x, w))
    return out


def _com_acento(w):
    return re.sub(r"[^\w]", "", str(w).lower())


def _juntar(tks):
    vistos, out = set(), []
    for _, w in tks:
        if id(w) not in vistos:
            vistos.add(id(w))
            out.append(w["w"])
    return " ".join(out)


def gagueira(final, esp, emendas):
    """Repetição e sílaba sobrando no final; com o texto esperado, também palavra que sumiu, sobrou ou trocou.
    A comparação de repetição guarda o acento ("E é" não é gagueira)."""
    F = [dict(w, t=_com_acento(w["w"])) for w in final if _com_acento(w["w"])]
    achados = []
    perto = (lambda t: min((abs(t - e["t"]) for e in emendas), default=99) <= PERTO_EMENDA)
    for i in range(len(F) - 1):
        a, b = F[i], F[i + 1]
        if a["t"] == b["t"] and b["a"] - a["b"] < 0.6:
            achados.append({"tipo": "palavra repetida", "t": a["a"], "texto": f"{a['w']} {b['w']}"})
        elif (len(a["t"]) >= 2 and len(b["t"]) >= len(a["t"]) + 2 and b["t"].startswith(a["t"])
              and b["a"] - a["b"] < 0.35 and a.get("p", 1) < 0.6):
            achados.append({"tipo": "sílaba sobrando", "t": a["a"], "texto": f"{a['w']} {b['w']}"})
        for j in range(i + 2, min(i + 5, len(F) - 1)):
            if [x["t"] for x in F[i:i + 2]] == [x["t"] for x in F[j:j + 2]] and F[j]["a"] - F[i]["a"] < 3.0:
                achados.append({"tipo": "trecho repetido", "t": a["a"],
                                "texto": " ".join(w["w"] for w in F[i:j + 2])})
    for x in achados:
        x["perto_emenda"] = perto(x["t"])
    diffs = []
    if esp:
        TF, TE = _tokens(final), _tokens(esp)
        tf, te = [x[0] for x in TF], [x[0] for x in TE]
        sm = difflib.SequenceMatcher(None, tf, te, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            if op == "replace" and i2 - i1 == j2 - j1 and all(quase(tf[i], te[j]) for i, j in
                                                             zip(range(i1, i2), range(j1, j2))):
                continue
            t = TF[i1][1]["a"] if i1 < len(TF) else (TE[j1][1]["a"] if j1 < len(TE) else 0)
            tipo = {"insert": "sobra no final", "delete": "sumiu do final", "replace": "trocada"}[op]
            fin, es = _juntar(TF[i1:i2]), _juntar(TE[j1:j2])
            diffs.append({"tipo": tipo, "t": round(float(t), 3), "final": fin, "esperado": es,
                          "texto": f"{fin or '—'}» no lugar de «{es or '—'}", "perto_emenda": perto(float(t))})
    return achados, diffs


# ---------------------------------------------------------------- som das emendas

def ler_som(video, dados):
    """Som mono 48 kHz em níveis de 10 ms (dB)."""
    wav = Path(dados) / "voz48k.wav"
    r = rodar(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", video, "-map", "0:a:0", "-vn", "-ac", "1",
               "-ar", "48000", "-c:a", "pcm_s16le", wav])
    if r.returncode != 0:
        return None
    try:
        with wave.open(str(wav), "rb") as f:
            x = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
    finally:
        wav.unlink(missing_ok=True)
    hop = 480
    fr = x[:len(x) // hop * hop].reshape(-1, hop)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)


def medir_emendas(db, db_final, emendas, so_voz):
    """Para cada emenda: a pausa que ficou, se cortou dentro do som e o salto da voz.
    Limiar de silêncio = ruído de fundo (10º percentil) + 12 dB (+ 8 dB quando o som já tem trilha).
    Depois de pontuação a fala respira: pausa até 0,45 s passa, e emenda sem respiro reprova. No meio da frase,
    fala colada é normal (pausa tirada) e a pausa passa até 0,25 s. O salto da voz é medido no som final."""
    if db is None or not emendas:
        return [], None
    thr = float(np.percentile(db, 10)) + (12 if so_voz else 8)
    dbf = db_final if db_final is not None else db
    thr_f = float(np.percentile(dbf, 10)) + 8
    H = 0.01
    n = len(db)
    out = []
    for e in emendas:
        pont = bool(re.search(r"[.,;:!?…]$", str(e.get("antes", "")).strip()))
        lo, hi = min(e["b"], e["t"]) - 0.06, max(e["a"], e["t"]) + 0.06
        i0, i1 = max(0, int(lo / H)), min(n, int(hi / H) + 1)
        quietos = [k for k in range(i0, i1) if db[k] < thr]
        r = {"t": e["t"], "trecho": e.get("trecho"), "antes": e.get("antes", ""), "depois": e.get("depois", ""),
             "pontuacao": pont, "problemas": [], "avisos": []}
        if not quietos:
            r["pausa"] = 0.0
            (r["problemas"] if pont else r["avisos"]).append("corta dentro do som")
        else:
            melhor = 0
            k = i0
            while k < i1:
                if db[k] < thr:
                    a = k
                    while a > 0 and db[a - 1] < thr:
                        a -= 1
                    b = k
                    while b < n and db[b] < thr:
                        b += 1
                    melhor = max(melhor, b - a)
                    k = b
                else:
                    k += 1
            r["pausa"] = round(melhor * H, 2)
            longa = PAUSA_LONGA_PONTO if pont else PAUSA_LONGA
            if r["pausa"] > longa:
                r["problemas"].append(f"pausa longa ({r['pausa']:.2f} s)".replace(".", ","))
            elif r["pausa"] < PAUSA_CURTA and pont:
                r["problemas"].append(f"sem respiro depois de «{r['antes']}» ({r['pausa']:.2f} s)".replace(".", ","))
        nf = len(dbf)
        antes = dbf[max(0, int((e["b"] - 0.6) / H)):max(1, min(nf, int(e["b"] / H)))]
        depois = dbf[min(nf - 1, int(e["a"] / H)):min(nf, int((e["a"] + 0.6) / H))]
        va, vd = antes[antes >= thr_f], depois[depois >= thr_f]
        if len(va) >= 8 and len(vd) >= 8:
            r["salto_voz"] = round(float(np.median(vd) - np.median(va)), 1)
            if abs(r["salto_voz"]) > SALTO_VOZ:
                r["problemas"].append(f"volume da voz pula {abs(r['salto_voz']):.1f} dB".replace(".", ","))
        av = db[max(0, int((e["b"] - 0.6) / H)):max(1, int(e["b"] / H))]
        dv = db[min(n - 1, int(e["a"] / H)):min(n, int((e["a"] + 0.6) / H))]
        if len(av) >= 10 and len(dv) >= 10:
            r["salto_fundo"] = round(float(np.percentile(dv, 15) - np.percentile(av, 15)), 1)
        out.append(r)
    return out, round(thr, 1)
