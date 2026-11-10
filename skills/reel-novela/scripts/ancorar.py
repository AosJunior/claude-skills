# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""/reel-novela, régua da voz: reescreve as âncoras do assets/voz.js quando a narração muda depois das cenas.

Uso:  uv run "<skill>/scripts/ancorar.py" <palavras-cenas.json> <palavras-voz.json> <assets/voz.js> [--fixa ANTIGO=NOVO ...]

  palavras-cenas.json  a régua em que as cenas foram escritas (o tempo do código). Guarde uma cópia do
                       palavras-voz.json antes de alinhar a narração nova: é ela.
  palavras-voz.json    o alinhamento da narração nova (narrar.py alinhar).
  assets/voz.js        o arquivo com `const A = [...]`; só o conteúdo de A muda.
  --fixa 41.2=44.9     âncora medida à mão, que vale mais que o alinhador: a letra de uma sigla soletrada (tempo de
                       cada letra no palavras-voz-bruto.json), o fim do vídeo (duração antiga=duração nova). Repita.

Cada palavra das duas réguas vira o par [tempo escrito, tempo real], pelo início da palavra, e o VOZ.w interpola
entre eles; as cenas não mudam. As palavras são casadas pelo texto: uma palavra trocada no roteiro fica sem âncora e
o tempo dela sai da interpolação, sem desalinhar o resto. Âncora que andaria para trás sai, e também a âncora solta:
um trecho igual de até 2 palavras («e», «a») cujo deslocamento destoa mais de 1 s dos dois vizinhos (o script lista
cada uma e o --fixa a devolve). Quando um bloco muda de lugar no roteiro, o script lista os saltos de deslocamento:
entre as duas âncoras de um salto o VOZ.w estica, e a palavra curta da emenda pode casar com o bloco errado (ex.: o «E» da tese
casou com o «E o detalhe» do bloco que veio para antes dela; --fixa 67.88=68.48 corrigiu).
No fim, o node confere que o VOZ.w de cada tempo escrito dá o tempo novo. Depois, as janelas do index.html
(data-start de cada cena) também vão para o tempo novo: confira com o briefings/tempo-real.cjs.
"""
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

sys.dont_write_bytecode = True   # sem __pycache__ dentro da skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import ajuda, fmt_num, ler_json, sair, sem_acento, utf8  # noqa: E402

JS_CONFERE = r"""
const fs = require("fs"), vm = require("vm");
const ctx = { window: {} }; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), ctx, { filename: "voz.js" });
const V = ctx.window.VOZ || ctx.VOZ;
const pares = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
let pior = 0;
for (const [a, b] of pares) pior = Math.max(pior, Math.abs(V.w(a) - b));
console.log(JSON.stringify({ pior, ancoras: V.ancoras.length }));
"""


def chave(w):
    return re.sub(r"[^a-z0-9]", "", sem_acento(str(w).lower()))


def num(x):
    return format(round(float(x), 3), "g") if abs(x) < 1e5 else str(round(float(x), 3))


def main():
    utf8()
    ajuda(__doc__)
    a = sys.argv[1:]
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--fixa")]
    if len(pos) < 3:
        sair(__doc__)
    p_antigas, p_novas, p_voz = (Path(x).expanduser() for x in pos[:3])
    for p in (p_antigas, p_novas, p_voz):
        if not p.is_file():
            sair(f"Não achei {p}")
    antigas, novas = ler_json(p_antigas), ler_json(p_novas)
    fixas = []
    for i, x in enumerate(a):
        if x == "--fixa":
            try:
                v0, v1 = a[i + 1].replace(",", ".").split("=")
                fixas.append((float(v0), float(v1)))
            except (IndexError, ValueError):
                sair("Use --fixa TEMPO_ESCRITO=TEMPO_NOVO (ex.: --fixa 41.2=44.9).")

    ka, kn = [chave(w["w"]) for w in antigas], [chave(w["w"]) for w in novas]
    blocos, sem = [], []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, ka, kn, autojunk=False).get_opcodes():
        if op == "equal":
            blocos.append([(float(antigas[i]["ini"]), float(novas[j]["ini"]), antigas[i]["w"])
                           for i, j in zip(range(i1, i2), range(j1, j2))])
        else:
            sem += [antigas[i]["w"] for i in range(i1, i2)]
    # Bloco que mudou de lugar no roteiro deixa palavras curtas («e», «a») casadas com o lugar errado: por exemplo,
    # o «E» da tese (67,88) casou com o «E o detalhe» novo (52,76). Um trecho igual de até 2 palavras cujo deslocamento
    # destoa mais de 1 s dos trechos longos vizinhos sai; se ele era certo, o --fixa o devolve.
    def desloc(b):
        return sorted(t1 - t0 for t0, t1, _ in b)[len(b) // 2]
    longos = [k for k, b in enumerate(blocos) if len(b) >= 3]
    soltos = []
    for k, b in enumerate(blocos):
        if len(b) > 2 or not longos:
            continue
        viz = [desloc(blocos[x]) for x in (max((x for x in longos if x < k), default=None),
                                           min((x for x in longos if x > k), default=None)) if x is not None]
        if viz and all(abs(desloc(b) - v) > 1.0 for v in viz):
            soltos.append((b, viz))
    for b, _ in soltos:
        blocos.remove(b)
    pares = [(t0, t1) for b in blocos for t0, t1, _ in b]
    fixos = {round(t0, 3) for t0, _ in fixas}
    pares = [p for p in pares if round(p[0], 3) not in fixos] + fixas
    pares.sort()
    limpos, fora = [], 0
    for t0, t1 in pares:
        if limpos and (t0 <= limpos[-1][0] + 1e-6 or t1 <= limpos[-1][1] + 1e-6):
            fora += 1
            continue
        limpos.append((t0, t1))
    if not limpos:
        sair("Nenhuma palavra em comum entre as duas réguas: confira os arquivos.")

    linhas, linha = [], []
    for t0, t1 in limpos:
        linha.append(f"[{num(t0)},{num(t1)}]")
        if len(linha) == 9:
            linhas.append(",".join(linha))
            linha = []
    if linha:
        linhas.append(",".join(linha))
    corpo = "const A = [\n    " + ",\n    ".join(linhas) + "\n  ];"
    js = p_voz.read_text(encoding="utf-8")
    if not re.search(r"const A = \[[\s\S]*?\];", js):
        sair(f"Não achei `const A = [...];` em {p_voz.name}. Use o voz.js do esqueleto da skill.")
    nota = (f"// Âncoras ({date.today().isoformat()}): {p_antigas.name} → {p_novas.name}, {len(limpos)} pares"
            + (f", {len(fixas)} fixas" if fixas else "") + ".")
    js = re.sub(r"[ \t]*// Âncoras \([^\n]*\n", "", js)
    js = re.sub(r"([ \t]*)const A = \[[\s\S]*?\];", lambda m: f"{m.group(1)}{nota}\n{m.group(1)}{corpo}", js, count=1)
    p_voz.write_text(js, encoding="utf-8")

    desl = [t1 - t0 for t0, t1 in limpos]
    print(f"Pronto: {p_voz} · {len(limpos)} âncoras ({len(fixas)} fixas) · deslocamento de {fmt_num(min(desl), 2)} a "
          f"{fmt_num(max(desl), 2)} s")
    if sem:
        print(f"Palavras sem âncora (mudaram no texto): {', '.join(sem[:15])}{' …' if len(sem) > 15 else ''}")
    palavra = {round(t0, 3): w for b in blocos for t0, _, w in b}
    fixas_t = {round(t0, 3) for t0, _ in fixas}
    saltos = [(a0, a1) for a0, a1 in zip(limpos, limpos[1:]) if abs((a1[1] - a1[0]) - (a0[1] - a0[0])) > 1.0
              and not (round(a0[0], 3) in fixas_t and round(a1[0], 3) in fixas_t)]   # a pausa do pausa.py é pedida
    if saltos:
        print(f"{len(saltos)} salto(s) de deslocamento, onde um bloco mudou de lugar ou de tamanho no roteiro. Entre as "
              "duas âncoras de cada salto, o VOZ.w interpola e estica: se uma cena usa um tempo nesse intervalo (a emenda "
              "de um ato, a palavra que abre o bloco), fixe com --fixa ou reescreva o trecho em tempo real.")
        for a0, a1 in saltos:
            w0, w1 = palavra.get(round(a0[0], 3), "fixa"), palavra.get(round(a1[0], 3), "fixa")
            print(f"  «{w0}» {fmt_num(a0[0], 2)} → {fmt_num(a0[1], 2)}  |  «{w1}» {fmt_num(a1[0], 2)} → "
                  f"{fmt_num(a1[1], 2)}  (deslocamento {fmt_num(a0[1] - a0[0], 2)} → {fmt_num(a1[1] - a1[0], 2)} s)")
    for b, viz in soltos:
        ws = " ".join(w for _, _, w in b)
        print(f"Âncora solta descartada: «{ws}» {fmt_num(b[0][0], 2)} → {fmt_num(b[0][1], 2)} s (deslocamento "
              f"{fmt_num(b[0][1] - b[0][0], 2)} s; vizinhas {', '.join(fmt_num(v, 2) for v in viz)} s). Se era certa, "
              f"use --fixa {num(b[0][0])}={num(b[0][1])}.")
    if fora:
        print(f"{fora} âncoras saíram por andar para trás.")
    if shutil.which("node"):
        tmp = p_voz.with_name(".ancoras-confere.json")
        tmp.write_text(json.dumps(limpos), encoding="utf-8")
        r = subprocess.run(["node", "-e", JS_CONFERE, str(p_voz), str(tmp)], capture_output=True, text=True)
        tmp.unlink(missing_ok=True)
        if r.returncode:
            sair("O voz.js novo não rodou no node:\n" + r.stderr[-600:])
        c = json.loads(r.stdout)
        print(f"Conferência no node: VOZ.w devolve o tempo novo de cada âncora (erro máximo {c['pior']:.4f} s).")
        if c["pior"] > 0.002:
            sys.exit(1)
    print("Agora: data-start das cenas no index.html no tempo novo (briefings/tempo-real.cjs), snapshot nas palavras-"
          "gatilho e o efeitos.py de novo.")


if __name__ == "__main__":
    main()
