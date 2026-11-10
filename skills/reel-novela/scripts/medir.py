# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy"]
# ///
"""/reel-novela, conferência da trilha: mede a música contra a voz na própria entrega, em LU abaixo da voz.

Uso:  uv run "<skill>/scripts/medir.py" <entrega com trilha.mp4> --voz <narracao.wav>
          [--sem <sem trilha.mp4>] [--mix <mix.json>] [--inicio S] [--palavras <palavras-voz.json>]

Como mede: a entrega com trilha e a sem trilha têm a mesma voz e os mesmos efeitos; a diferença entre elas, com o
ganho de cada uma acertado em janelas de 20 ms, é a música. A referência da voz é a do nivelador do mixar.py: a
narração inteira (média de energia do loudness momentâneo nas falas), no ganho desta entrega. Fala e respiros saem
das palavras do palavras-voz.json (o de --palavras ou o que estiver ao lado da narração, ou em briefings/ ao lado
dela), como no mixar.py; sem ele, da energia da própria narração. Loudness momentâneo: 400 ms, ponderação K.
- sob a fala: a média e o trecho mais alto (o percentil de 95 %; um pico isolado sai à parte, quase sempre efeito);
- respiros de 0,5 s ou mais e o fim: a música no meio de cada um.
Régua (a música em LU abaixo da voz): sob a fala, média de -21,5 a -19,5 (o alvo é -20); respiros de 0,8 s ou mais,
de -6,5 a -9,5. Os de 0,5 s leem uns -10, porque a música só abre 0,2 s. O respiro com mergulho fica lá embaixo de
propósito: com as revelações do mix.json, ele sai marcado e fora da régua, pela mesma regra do mixar.py (revelação
dentro do respiro, com a medida no mergulho, ou logo depois dele, que não deixa a música subir).
Com "trilha.fora" no mix.json (a música sai, ex.: a aula da novela), essas janelas saem das contas de fala e o respiro
que as contém sai marcado «fora» e não conta na régua.

--sem      a entrega sem trilha. Sem ele, o script procura o par pelo nome: "-com-trilha" → "-sem-trilha", ou
           "<nome>-sem-trilha" (o par do --trecho do mixar.py).
--mix      o mix.json da peça, de onde saem as revelações. Sem ele, o script procura sequencia/som/mix.json subindo a
           partir da pasta da entrega.
--inicio   onde a entrega começa na narração, em s (prévia de um --trecho que não começa no 0).
Sai com código 1 se a média sob a fala ou algum respiro longo sem mergulho ficar fora da régua.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True   # sem __pycache__ dentro da skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (HOP, SR, ajuda, arquivo_palavras, checar_ffmpeg, fechar_buracos, fmt_num, ler_json,  # noqa: E402
                   media_energia, momentaneo, sair, segmentos_de_fala, segundos, utf8, voz_da_entrega, voz_tratada)
ajuda(__doc__)   # --help sai antes de importar numpy: funciona sem o uv ter baixado nada
import numpy as np  # noqa: E402

JANELA = 0.02    # s: janela do ganho entre as duas entregas


def achar_mix(entrega, a):
    """O mix.json de --mix, ou o sequencia/som/mix.json mais próximo subindo a partir da entrega."""
    if "--mix" in a:
        p = Path(a[a.index("--mix") + 1]).expanduser()
        if not p.is_file():
            sair(f"Não achei {p}")
        return p
    for d in [entrega.resolve().parent, *entrega.resolve().parents]:
        p = d / "sequencia" / "som" / "mix.json"
        if p.is_file():
            return p
    return None


def com_mergulho(p0, p1, c, revelacoes, folga):
    """O respiro (p0, p1), medido em c, tem mergulho? A mesma regra da curva do mixar.py: revelação dentro do respiro
    com a janela de 400 ms da medida pegando os 0,35 s do mergulho, ou revelação logo depois, que não deixa a música
    subir."""
    t0, t1 = p0 + folga, p1 - folga
    for r in revelacoes:
        if t0 < r < t1:
            if r - 0.35 - 0.2 <= c <= r + 0.2:
                return True
        elif t1 > r - 0.6 and t0 < r:
            return True
    return False


def par_sem_trilha(com):
    nome = com.name
    candidatos = []
    if "com-trilha" in nome:
        candidatos.append(com.with_name(nome.replace("com-trilha", "sem-trilha")))
    candidatos.append(com.with_name(com.stem + "-sem-trilha" + com.suffix))
    for c in candidatos:
        if c.is_file():
            return c
    sair(f"Não achei a entrega sem trilha de {nome} (tentei {', '.join(c.name for c in candidatos)}). "
         "Gere com o mixar.py --sem-trilha (com o mesmo --trecho) ou passe --sem <arquivo>.")


def musica(y1, y2):
    """Com trilha menos sem trilha, com a razão de ganho das duas por janela (o limitador do master age diferente)."""
    from scipy.ndimage import uniform_filter1d
    n = min(len(y1), len(y2))
    y1, y2 = y1[:n], y2[:n]
    R0 = float(np.sum(y1 * y2) / max(np.sum(y2 * y2), 1e-30))
    J, h = int(JANELA * SR), int(HOP * SR)
    num = uniform_filter1d((y1 * y2).sum(1), J)[::h]
    den = uniform_filter1d((y2 * y2).sum(1), J)[::h]
    ok = den > np.percentile(den, 99) * 1e-5            # onde a sem trilha tem som (voz ou efeito)
    r = np.where(ok, num / np.maximum(den, 1e-30), R0)
    r = np.clip(r, R0 * 10 ** (-3 / 20), R0 * 10 ** (3 / 20))
    rs = np.interp(np.arange(n) / h, np.arange(len(r)), r)
    return y1 - rs[:, None] * y2


def main():
    utf8()
    ajuda(__doc__)
    checar_ffmpeg()
    a = sys.argv[1:]
    if not a or a[0].startswith("-") or "--voz" not in a:
        sair(__doc__)
    com = Path(a[0]).expanduser()
    voz = Path(a[a.index("--voz") + 1]).expanduser()
    sem = Path(a[a.index("--sem") + 1]).expanduser() if "--sem" in a else par_sem_trilha(com)
    inicio = segundos(a[a.index("--inicio") + 1]) if "--inicio" in a else 0.0
    for p in (com, voz, sem):
        if not p.is_file():
            sair(f"Não achei {p}")
    mixp = achar_mix(com, a)
    trilha = (ler_json(mixp).get("trilha") or {}) if mixp else {}
    revelacoes = [float(r) for r in trilha.get("revelacoes", [])]
    folga = float(trilha.get("folga", 0.15))
    janelas_fora = [(float(a), float(b)) for a, b in trilha.get("fora", [])]

    vt = voz_tratada(voz).astype(np.float64)[:, 0]
    y1, v, _ = voz_da_entrega(com, vt, inicio)
    y2, _, _ = voz_da_entrega(sem, vt, inicio)
    n = min(len(y1), len(y2), len(v))
    m = musica(y1[:n], y2[:n])
    G = float(np.dot(y1[:n].mean(1), v[:n]) / np.dot(v[:n], v[:n]))   # ganho do master sobre a voz tratada
    # referência da voz: a narração inteira (a mesma do nivelador), no ganho desta entrega
    lv = momentaneo(np.repeat((G * vt)[:, None], 2, axis=1))
    V = media_energia(lv[lv > -30 + 20 * np.log10(G)])
    lm = momentaneo(m)
    k = len(lm)
    t = inicio + np.arange(k) * HOP
    fim_t = t[-1]
    palavras = arquivo_palavras(voz, a)
    if palavras:
        w = sorted(ler_json(palavras), key=lambda p: p["ini"])
        fala = np.zeros(k, bool)
        for p in w:
            fala |= (t >= p["ini"]) & (t <= p["fim"])
        fala = fechar_buracos(fala, 0.1)
        for f0, f1 in janelas_fora:
            fala &= ~((t >= f0) & (t <= f1))
        # respiros como no mixar.py: entre palavras, 0,495 s ou mais, e depois da última
        pausas = [(x["fim"], y["ini"]) for x, y in zip(w, w[1:]) if y["ini"] - x["fim"] >= 0.495]
        pausas.append((w[-1]["fim"], fim_t))
        print(f"fala e respiros: pelas palavras de {palavras.name}")
    else:
        fala = segmentos_de_fala(v[:n])
        fala = np.pad(fala, (0, max(0, k - len(fala))))[:k]
        for f0, f1 in janelas_fora:
            fala &= ~((t >= f0) & (t <= f1))
        pausas, i = [], 0
        while i < k:                       # trechos sem fala, depois da primeira palavra
            if fala[i]:
                i += 1
                continue
            j = i
            while j < k and not fala[j]:
                j += 1
            if i > 0 and ((j - i) * HOP >= 0.495 or j == k):
                pausas.append((t[i], t[j] if j < k else fim_t))
            i = j
        print("fala e respiros: pela energia da narração (sem palavras-voz.json ao lado dela)")

    # sob a fala: janelas centradas dentro da fala, a 50 ms das bordas
    from scipy.ndimage import binary_erosion
    dentro = binary_erosion(fala, np.ones(11, bool))
    if dentro.sum() < 50:
        sair("Quase não há fala neste pedaço; escolha um trecho com narração.")
    abaixo = V - lm[:k][dentro]
    media = V - media_energia(lm[:k][dentro])
    alto = float(np.percentile(abaixo, 5))
    i_pico = int(np.argmin(abaixo))
    print(f"{com.name} (menos {sem.name}): a música em LU abaixo da voz")
    print(f"voz nas falas: {fmt_num(V)} LUFS (momentâneo)")
    print(f"sob a fala: média {fmt_num(-media)} · trecho mais alto {fmt_num(-alto)} (95 % das janelas ficam abaixo)")
    if abaixo[i_pico] < alto - 2:
        print(f"   pico isolado: {fmt_num(-abaixo[i_pico])} em {fmt_num(t[dentro][i_pico], 2)} s (quase sempre um efeito)")

    # respiros: a música no meio de cada um (no fim, 0,75 s depois da última palavra)
    resp = []
    for p0, p1 in pausas:
        if p0 < t[0] or p0 >= fim_t - 0.2:
            continue
        c = (p0 + p1) / 2 if p1 < fim_t else min(fim_t, p0 + 0.75)
        i = int(np.clip(round((c - t[0]) / HOP), 0, k - 1))
        tira = any(p0 < f1 and p1 > f0 for f0, f1 in janelas_fora)   # a pausa contém uma janela «fora»
        resp.append((p0, min(p1, fim_t), min(p1, fim_t) - p0, V - lm[i], com_mergulho(p0, p1, c, revelacoes, folga), tira))
    ok = -21.5 <= -media <= -19.5
    print(f"revelações: {len(revelacoes)}, do {mixp.name if mixp else '(sem mix.json: nenhuma)'}")
    if janelas_fora:
        print(f"janelas fora (a música sai): {len(janelas_fora)}")
    contam = [r for r in resp if not r[5]]
    if resp:
        if contam:
            print(f"respiros de 0,5 s ou mais ({len(contam)}): de {fmt_num(-max(r[3] for r in contam))} a "
                  f"{fmt_num(-min(r[3] for r in contam))}")
        for t0, t1, dur, d, merg, tira in resp:
            print(f"   {fmt_num(t0, 2):>6}–{fmt_num(t1, 2):<6} ({fmt_num(dur, 2)} s): {fmt_num(-d)}"
                  + ("  «fora»: a música sai aqui, não conta" if tira else "")
                  + ("  mergulho da revelação: não conta" if merg else ""))
        fora = [r for r in contam if r[2] >= 0.8 and not r[4] and not 6.5 <= r[3] <= 9.5]
        if fora:
            print("respiros longos fora de -6,5 a -9,5: " + ", ".join(f"{fmt_num(r[0], 2)} s ({fmt_num(-r[3])})"
                                                                    for r in fora))
        ok &= not fora
    veredito = "dentro da régua" if ok else ("ALTA" if -media > -19.5 else "BAIXA" if -media < -21.5 else
                                             "respiros fora da régua")
    print(f"Régua: sob a fala -20 (média de -21,5 a -19,5), respiros longos de -7 a -9 → {veredito}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
