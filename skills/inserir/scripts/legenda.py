"""Legenda da /inserir: monta a lista de pedaços (tempo, palavras, destaque) que é gravada na imagem E escrita na
legenda-curta.srt. Os dois saem desta mesma lista, então têm o mesmo tempo.

Fonte das palavras: decupagem/palavras-corte.json (tempo de cada palavra no vídeo cortado). Sem ele, cai no
legenda.srt e divide cada bloco pelo número de letras (o jeito antigo)."""
import re

from comum import chave, ler_json, ler_srt

PONT = ".,;:!?\"“”'…()"
# a legenda nunca termina nestas palavras: elas vão para a próxima
LIGA = {"de", "da", "do", "das", "dos", "o", "a", "os", "as", "um", "uma", "pra", "para", "com", "e", "que", "em",
        "no", "na", "nos", "nas", "por", "pelo", "pela", "se", "ao", "à", "mais", "muito", "meu", "minha", "seu", "sua"}
UNIDADES = {"mil", "milhao", "milhoes", "bilhao", "bilhoes", "mi", "bi", "k", "reais", "real", "dolares", "%"}
MOEDA = {"r", "rs", "us", "usd", "€"}


def norm(w):
    return w.strip(PONT).lower()


# ---------------------------------------------------------------- caminho antigo: legenda.srt

def agrupar(ws, pmax, lmax):
    grupos, atual = [], []
    for w in ws:
        if atual and (len(atual) >= pmax or len(" ".join(atual + [w])) > lmax):
            grupos.append(atual)
            atual = []
        atual.append(w)
    if atual:
        grupos.append(atual)
    for i in range(len(grupos) - 1):          # não termina em "de", "o", "pra"...
        while len(grupos[i]) > 1 and norm(grupos[i][-1]) in LIGA and len(grupos[i + 1]) < pmax:
            grupos[i + 1].insert(0, grupos[i].pop())
    if len(grupos) > 1 and len(grupos[-1]) == 1 and len(grupos[-2]) < pmax and \
            len(" ".join(grupos[-2] + grupos[-1])) <= lmax + 4:
        ult = grupos.pop()
        grupos[-1] += ult                      # palavra sozinha no fim junta com a anterior
    elif len(grupos) > 1 and len(grupos[-1]) == 1 and len(grupos[-2]) >= 3:
        grupos[-1].insert(0, grupos[-2].pop())  # sem espaço para juntar: a anterior cede uma palavra
    return grupos


def picotar(ini, fim, texto, pmax, lmax):
    """Divide um bloco do .srt em pedaços de até pmax palavras e lmax letras, com tempo proporcional às letras.
    A vírgula é ponto de quebra: "comprar, só que enquanto" vira "comprar" + "só que enquanto"."""
    if len(texto.split()) <= pmax and len(texto) <= lmax:
        return [(ini, fim, texto.split())]    # cabe numa legenda só: fica inteiro
    oracoes, atual = [], []
    for w in texto.split():
        atual.append(w)
        if re.search(r"[,;:]$", w):
            oracoes.append(atual)
            atual = []
    if atual:
        oracoes.append(atual)
    juntas = []                                # oração de uma palavra curta ("Mas,", "E,") vai com a seguinte
    for o in oracoes:
        if juntas and len(juntas[-1]) == 1 and len(juntas[-1][0].strip(PONT)) <= 4:
            juntas[-1] += o
        else:
            juntas.append(list(o))
    grupos = [g for o in juntas for g in agrupar(o, pmax, lmax)]
    total = sum(len(" ".join(g)) + 1 for g in grupos)
    out, t = [], ini
    for g in grupos:
        d = (fim - ini) * (len(" ".join(g)) + 1) / total
        out.append((t, t + d, g))
        t += d
    return out


def de_srt(srt, estilo, destaques, correcoes):
    dest = {norm(w) for w in destaques}
    leg = []
    for ini, fim, texto in ler_srt(srt):
        for errado, certo in correcoes.items():      # palavra que o Whisper ouviu errado
            texto = re.sub(rf"(?<!\w){re.escape(errado)}(?!\w)", certo, texto)
        for a, b, g in picotar(ini, fim, texto, estilo["palavras_max"], estilo["letras_max"]):
            g = list(g)
            g[-1] = g[-1].rstrip(".,;:…")    # pontuação no fim do pedaço sai; "?" e "!" ficam
            leg.append((a, b, [[w, norm(w) in dest] for w in g if w]))
    return caixa(leg, estilo)


# ---------------------------------------------------------------- caminho novo: palavras-corte.json

def corrigir(w, correcoes):
    """Troca a palavra que o Whisper ouviu errado, mantendo a pontuação em volta ("alugas." -> "aluga-se.")."""
    m = re.match(r"^([" + re.escape(PONT) + r"]*)(.*?)([" + re.escape(PONT) + r"]*)$", w)
    ini, miolo, fim = m.groups()
    for errado, certo in correcoes.items():
        if " " not in errado and (miolo == errado or chave(miolo) == chave(errado)):
            return ini + certo + fim
    return w


def numero(w):
    return bool(re.fullmatch(r"\+?\d+(?:[.,]\d+)*", w.strip(PONT.replace("%", ""))))


def juntar(ws):
    """Fichas da legenda: "100 mil", "R$ 18 milhões" e "10, 20" viram uma ficha só."""
    fichas = []
    for w in ws:
        if fichas:
            ult = fichas[-1]
            k_ult, k = ult[-1]["w"], w["w"]
            pega = (numero(k_ult) and (chave(k) in UNIDADES or k.strip(PONT) == "%")) \
                or (chave(k_ult) in MOEDA and k_ult.strip(PONT).upper().startswith(("R$", "US$", "€")) and numero(k)) \
                or (numero(k_ult) and k_ult.endswith(",") and numero(k)) \
                or (len(ult) > 1 and chave(ult[-1]["w"]) in UNIDADES and chave(k) in UNIDADES)
            if pega:
                ult.append(w)
                continue
        fichas.append([w])
    return fichas


def de_palavras(arq, estilo, destaques, correcoes, dur):
    """Legenda a partir do tempo de cada palavra no corte. Cada pedaço fica na tela do início da 1ª palavra até
    o início do próximo pedaço (pausa curta não deixa a tela vazia); o último termina no fim do vídeo."""
    d = ler_json(arq)
    ws = [dict(w, w=corrigir(w["w"].strip(), correcoes)) for w in d.get("palavras", []) if w["w"].strip()]
    ws = [w for w in ws if w["a"] < dur - 0.01]
    dest = {chave(w) for w in destaques}
    pmax, lmax = estilo["palavras_max"], estilo["letras_max"]
    fichas = juntar(ws) if estilo.get("juntar_numeros") else [[w] for w in ws]
    # agrupa as fichas em pedaços de até pmax fichas (uma ficha conta como uma palavra), sem passar de uma frase
    grupos, atual = [], []
    for f in fichas:
        txt = " ".join(w["w"] for x in atual + [f] for w in x)
        quebra = atual and (len(atual) >= pmax or (pmax > 1 and len(txt) > lmax) or atual[-1][-1]["frase"] != f[0]["frase"]
                            or re.search(r"[,;:.?!…]$", atual[-1][-1]["w"]))
        if quebra:
            grupos.append(atual)
            atual = []
        atual.append(f)
    if atual:
        grupos.append(atual)
    if pmax > 1:                               # não termina em "de", "o", "pra"...
        for i in range(len(grupos) - 1):
            while len(grupos[i]) > 1 and norm(grupos[i][-1][-1]["w"]) in LIGA and len(grupos[i + 1]) < pmax \
                    and grupos[i][-1][-1]["frase"] == grupos[i + 1][0][0]["frase"]:
                grupos[i + 1].insert(0, grupos[i].pop())
    leg = []
    for g in grupos:
        palavras = [w for f in g for w in f]
        texto = [w["w"] for w in palavras]
        texto[-1] = texto[-1].rstrip(".,;:…")    # pontuação no fim do pedaço sai; "?" e "!" ficam
        leg.append([palavras[0]["a"], palavras[-1]["b"], [[t, chave(t) in dest] for t in texto if t]])
    for i, g in enumerate(leg):                # tempo de tela: emenda no próximo se a pausa é curta
        prox = leg[i + 1][0] if i + 1 < len(leg) else dur
        g[1] = min(max(g[1], g[0] + 0.18), prox)
        if prox - g[1] < 0.5:
            g[1] = prox
        g[1] = min(g[1], dur)
    return caixa([tuple(g) for g in leg if g[1] - g[0] > 0.01], estilo)


def caixa(leg, estilo):
    """minusculas: tudo em minúscula, menos os nomes (que podem ter mais de uma palavra: "O Animal Social")."""
    if not estilo.get("minusculas"):
        return leg
    nomes = [[chave(x) for x in n.split()] for n in estilo.get("nomes") or []]
    canon = [n.split() for n in estilo.get("nomes") or []]
    plano = [(i, j) for i, (_, _, ws) in enumerate(leg) for j in range(len(ws))]
    fixo = {}
    for k in range(len(plano)):
        for n, c in zip(nomes, canon):
            if k + len(n) <= len(plano) and all(chave(leg[plano[k + m][0]][2][plano[k + m][1]][0]) == n[m] for m in range(len(n))):
                for m in range(len(n)):
                    fixo[plano[k + m]] = c[m]
    out = []
    for i, (a, b, ws) in enumerate(leg):
        novo = []
        for j, (w, d) in enumerate(ws):
            if (i, j) in fixo:
                pre = re.match(r"^[" + re.escape(PONT) + r"]*", w).group(0)
                pos = re.search(r"[" + re.escape(PONT) + r"]*$", w).group(0)
                w = pre + fixo[(i, j)].strip(PONT) + pos
            else:
                w = w.lower()
            novo.append([w, d])
        out.append((a, b, novo))
    return out


# ---------------------------------------------------------------- altura de cada pedaço

def posicionar(leg, faixas, estilo):
    """Cada pedaço ganha a altura dele. Faixas (de, ate, y, aceito) na ordem em que foram escritas; a última que
    pega o pedaço manda. y: número (px), "alto" (legenda_y_alto) ou "some". Sem faixa, o pedaço com palavra de
    destaque sobe para destaque_y (se houver) e o resto fica em legenda_y."""
    out = []
    for a, b, ws in leg:
        dest = any(d for _, d in ws)
        y = estilo["destaque_y"] if dest and estilo.get("destaque_y") else estilo["legenda_y"]
        aceito = None
        for de, ate, pos, ac in faixas:
            if a < ate - 0.05 and b > de + 0.05:
                if pos == "some":
                    y = None
                elif pos == "alto":
                    y = estilo["legenda_y_alto"]
                elif isinstance(pos, (int, float)):
                    y = pos
                aceito = ac
        if y is not None:
            out.append((a, b, ws, y, aceito))
    return out
