# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["numpy", "librosa", "pylibrb"]
# ///
"""/reel-novela, trilha: edita a música no compasso para a estrutura do vídeo e grava a trilha editada.

Uso:
  uv run "<skill>/scripts/montar_trilha.py" <planta.json> --grade   lista os compassos da música (para planejar)
  uv run "<skill>/scripts/montar_trilha.py" <planta.json>           monta a trilha editada

Os compassos saem do beat tracking (librosa): um a cada "tempos_por_compasso" batidas, cada um ajustado ao ataque mais
forte em ±60 ms. Cada trecho da planta começa num instante do vídeo e toca a música a partir de um compasso (ou de um
segundo exato da fonte) até o próximo trecho. As emendas:
- "compasso": a anterior acaba no tempo de compasso e a nova entra com cruzamento de 40 ms, que termina no ataque;
- "mergulho": a anterior é cortada dentro do mergulho da trilha (antes de uma revelação, ver "revelacoes" no mix.json)
  e a nova entra no ataque, que é o golpe da revelação;
- "cauda": cruzamento longo (0,3 s), para encurtar um trecho sem ritmo (cauda de um estrondo);
- "livre": corte seco, só para o primeiro trecho.
Trecho com "ate_compasso" é esticado (Rubber Band R3, offline) para caber exatamente no espaço do vídeo; mantenha o
fator perto de 1 (a produção-base usou 0,97 e 0,98).

planta.json (caminhos relativos à pasta dele; o padrão é sequencia/som/trilha/planta.json):
{
 "fonte": "../sons/musica.wav",
 "saida": "trilha-editada.wav",
 "duracao": 60.0,
 "bpm": 99, "tempos_por_compasso": 4, "primeiro_compasso": 2.57,
 "trechos": [
  {"video": 0, "fonte": 0.03, "entra": "livre", "nota": "o golpe do começo, intacto"},
  {"video": 6.49, "compasso": 2, "nota": "o tema entra no respiro"},
  {"video": 18.2, "compasso": 12, "compassos": 8, "entra": "mergulho", "nota": "golpe na revelação"},
  {"compasso": 20, "nota": "começa onde o anterior acaba (8 compassos depois de 18,2)"},
  {"video": 41.6, "compasso": 24, "ate_compasso": 31, "entra": "mergulho", "nota": "esticado para caber"},
  {"video": 58.6, "fonte": 2.57, "entra": "mergulho", "nota": "o golpe do começo de novo, no fim"}
 ]
}
  video            instante do vídeo em que o trecho começa (sem ele: onde o anterior acaba, se o anterior tem
                   "compassos")
  compasso / fonte o compasso da música (índice do --grade) ou o segundo exato da fonte que cai no "video"
  compassos        quantos compassos o trecho dura (para o seguinte vir sem "video")
  ate_compasso     estica o trecho para que esse compasso caia no começo do trecho seguinte
  fator            esticamento explícito (duração no vídeo ÷ duração na fonte), no lugar do ate_compasso
  entra            compasso (padrão), mergulho, cauda ou livre
  bpm, primeiro_compasso  chute do andamento e um tempo forte conhecido da fonte (acerta a fase da grade)
Grava a "saida" (48 kHz, 24 bits) e <saida>-emendas.json (os compassos da fonte e cada trecho resolvido).
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True   # sem __pycache__ dentro da skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import SR, ajuda, checar_ffmpeg, fmt_num, gravar_audio, gravar_json, ler_audio, ler_json, sair, \
    utf8  # noqa: E402
ajuda(__doc__)   # --help sai antes de importar numpy: funciona sem o uv ter baixado nada
import numpy as np  # noqa: E402

PRE = {"compasso": 0.04, "mergulho": 0.03, "livre": 0.0, "cauda": 0.15}   # quanto a nova entra antes do instante
POS = {"compasso": 0.02, "mergulho": 0.06, "livre": 0.0, "cauda": 0.15, "fim": 0.0}   # quanto a anterior passa dele


def compassos(x, bpm, por_compasso, primeiro):
    import librosa
    y = librosa.resample(x.mean(1), orig_sr=SR, target_sr=22050)
    oenv = librosa.onset.onset_strength(y=y, sr=22050, hop_length=256)
    _, bf = librosa.beat.beat_track(onset_envelope=oenv, sr=22050, hop_length=256, start_bpm=bpm)
    bt = librosa.frames_to_time(bf, sr=22050, hop_length=256)
    if not len(bt):
        sair("O beat tracking não achou batidas nesta música. Use trechos com \"fonte\" em segundos.")
    fase = 0 if primeiro is None else int(np.argmin(np.abs(bt - primeiro))) % por_compasso
    D = bt[fase::por_compasso]
    of = librosa.onset.onset_strength(y=y, sr=22050, hop_length=64)
    tf = librosa.frames_to_time(np.arange(len(of)), sr=22050, hop_length=64)
    out = []
    for d in D:   # ajuste fino ao ataque mais forte em ±60 ms
        m = (tf > d - 0.06) & (tf < d + 0.06)
        out.append(float(tf[m][np.argmax(of[m])]) if m.any() else float(d))
    andamento = 60 / np.median(np.diff(bt)) if len(bt) > 1 else 0
    return np.array(out), andamento


def esticar(x, fator):
    if abs(fator - 1) < 1e-4:
        return x
    import pylibrb
    st = pylibrb.RubberBandStretcher(SR, 2, pylibrb.Option.PROCESS_OFFLINE | pylibrb.Option.ENGINE_FINER,
                                     initial_time_ratio=fator)
    a = np.ascontiguousarray(x.T, dtype=np.float32)
    BL = 262144
    st.set_max_process_size(BL)
    for i in range(0, a.shape[1], BL):
        st.study(a[:, i:i + BL], final=i + BL >= a.shape[1])
    partes = []
    for i in range(0, a.shape[1], BL):
        st.process(a[:, i:i + BL], final=i + BL >= a.shape[1])
        partes.append(st.retrieve_available())
    while not st.is_done() or st.available() > 0:
        r = st.retrieve_available()
        if r.shape[1] == 0 and st.is_done():
            break
        partes.append(r)
    return np.ascontiguousarray(np.concatenate(partes, axis=1).T)


def resolver(planta, D, dur):
    """Cada trecho com início no vídeo, início na fonte, fator e emendas."""
    tr = planta.get("trechos") or []
    if not tr:
        sair("A planta não tem trechos. Rode com --grade para ver os compassos e escreva os trechos.")

    def bar(k, onde):
        if not 0 <= int(k) < len(D):
            sair(f"{onde}: o compasso {k} não existe (a música tem {len(D)}, de 0 a {len(D) - 1}).")
        return float(D[int(k)])
    res = []
    for i, t in enumerate(tr):
        onde = f"trecho {i + 1}"
        if "fonte" in t:
            f0 = float(t["fonte"])
        elif "compasso" in t:
            f0 = bar(t["compasso"], onde)
        else:
            sair(f"{onde}: falta \"compasso\" ou \"fonte\".")
        if "video" in t:
            v0 = float(t["video"])
        elif res and "compassos" in tr[i - 1] and "compasso" in tr[i - 1]:
            a = res[-1]
            v0 = a["v0"] + (bar(int(tr[i - 1]["compasso"]) + int(tr[i - 1]["compassos"]), onde) - a["f0"]) / a["fator"]
        else:
            sair(f"{onde}: falta \"video\" (ou \"compassos\" no trecho anterior).")
        if res and v0 <= res[-1]["v0"]:
            sair(f"{onde}: o vídeo dele ({v0}) precisa vir depois do trecho anterior ({res[-1]['v0']}).")
        entra = t.get("entra", "compasso" if i else "livre")
        if entra not in PRE:
            sair(f"{onde}: entra «{entra}» não existe (use compasso, mergulho, cauda ou livre).")
        res.append({"v0": v0, "f0": f0, "entra": entra, "fator": float(t.get("fator", 1.0)), "t": t})
    for i, r in enumerate(res):
        r["v1"] = res[i + 1]["v0"] if i + 1 < len(res) else dur
        r["sai"] = res[i + 1]["entra"] if i + 1 < len(res) else "fim"
        if "ate_compasso" in r["t"]:
            r["fator"] = (r["v1"] - r["v0"]) / (bar(r["t"]["ate_compasso"], f"trecho {i + 1}") - r["f0"])
        if not 0.8 <= r["fator"] <= 1.25:
            sair(f"trecho {i + 1}: esticar {r['fator']:.3f}× deforma a música. Escolha outros compassos.")
    return res


def main():
    utf8()
    ajuda(__doc__)
    checar_ffmpeg()
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        sair(__doc__)
    pp = Path(a[0]).expanduser().resolve()
    if not pp.is_file():
        sair(f"Não achei a planta: {pp}")
    planta = ler_json(pp)
    cam = lambda x: (Path(x).expanduser() if Path(x).expanduser().is_absolute() else pp.parent / x)  # noqa: E731
    fonte = cam(planta.get("fonte", ""))
    if not fonte.is_file():
        sair(f"Não achei a música: {fonte}")
    x = ler_audio(fonte)
    por = int(planta.get("tempos_por_compasso", 4))
    D, bpm = compassos(x, float(planta.get("bpm", 120)), por, planta.get("primeiro_compasso"))
    if "--grade" in a:
        print(f"{fonte.name}: {fmt_num(len(x) / SR, 2)} s · ~{fmt_num(bpm)} BPM · compasso de "
              f"{fmt_num(float(np.median(np.diff(D))), 2)} s ({por} tempos) · {len(D)} compassos")
        for k in range(0, len(D), 6):
            print("  " + "   ".join(f"{j:2d}: {fmt_num(D[j], 2):>6} s" for j in range(k, min(k + 6, len(D)))))
        print("Ouça os trechos candidatos e escreva os trechos da planta com esses índices.")
        return
    dur = float(planta.get("duracao", 0))
    if dur <= 0:
        sair("Falta \"duracao\" (a duração do vídeo, em s) na planta.")
    res = resolver(planta, D, dur)
    n = int(round(dur * SR))
    pista = np.zeros((n, 2), np.float32)
    s = lambda t: int(round(t * SR))  # noqa: E731
    emendas = []
    for r in res:
        v0, v1, f0, fator = r["v0"], r["v1"], r["f0"], r["fator"]
        pre, pos = PRE[r["entra"]], POS[r["sai"]]
        ini, fim = f0 - pre / fator, f0 + (v1 - v0 + pos) / fator
        seg = x[max(0, s(ini)):s(fim) + SR // 2]
        if ini < 0:
            seg = np.pad(seg, ((s(-ini), 0), (0, 0)))
        seg = esticar(seg, fator)
        L = s(v1 - v0 + pre + pos)
        seg = np.pad(seg, ((0, max(0, L - len(seg))), (0, 0)))[:L].copy()
        ki, ko = s(pre), s(pos)
        if ki:   # entrada e saída em rampa de potência constante
            seg[:ki] *= np.sin(np.linspace(0, np.pi / 2, ki))[:, None]
        if ko:
            seg[-ko:] *= np.cos(np.linspace(0, np.pi / 2, ko))[:, None]
        p0 = s(v0 - pre)
        p1 = min(n, p0 + len(seg))
        if p0 < 0:
            seg, p0 = seg[-p0:], 0
        pista[p0:p1] += seg[: p1 - p0]
        emendas.append({"trecho": r["t"].get("nota", ""), "video": [round(v0, 3), round(v1, 3)],
                        "fonte": [round(f0, 3), round(f0 + (v1 - v0) / fator, 3)], "fator": round(fator, 4),
                        "entra": r["entra"], "sai": r["sai"]})
    saida = cam(planta.get("saida", "trilha-editada.wav"))
    saida.parent.mkdir(parents=True, exist_ok=True)
    gravar_audio(saida, pista, codec="pcm_s24le")
    gravar_json(saida.with_name(saida.stem + "-emendas.json"),
                {"compassos_fonte": [round(float(d), 3) for d in D], "trechos": emendas})
    for e in emendas:
        print(f"{fmt_num(e['video'][0], 2):>6}–{fmt_num(e['video'][1], 2):<6} fonte {fmt_num(e['fonte'][0], 2):>6}–"
              f"{fmt_num(e['fonte'][1], 2):<6} ×{e['fator']:.4f}  {e['entra']:>8} → {e['sai']:<8} {e['trecho']}")
    print(f"Pronto: {saida} ({fmt_num(dur, 2)} s)")


if __name__ == "__main__":
    main()
