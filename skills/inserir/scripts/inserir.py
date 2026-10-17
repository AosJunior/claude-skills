# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.48", "fonttools>=4.50"]
# ///
"""/inserir: desenha os cartões de inserção e a legenda em HTML, fotografa em PNG transparente e grava no vídeo.

Uso:  uv run "<skill>/scripts/inserir.py" "<pasta decupagem>" --cartoes      só os cartões: cartoes.png para conferir
      uv run "<skill>/scripts/inserir.py" "<pasta decupagem>"                vídeo com inserções e legenda + quadros/
      opções: --video V (padrão: final.mp4, senão previa.mp4 da decupagem) · --pasta P (padrão: <pai>/insercoes)
              --saida ARQ.mp4 · --sem-legenda

Lê:   <pasta decupagem>/legenda.srt e <P>/insercoes.json (o Claude escreve; formato no SKILL.md).
Grava em <P>/: cartoes.png (todos os cartões, para conferir), legenda-curta.srt (2 a 4 palavras por vez),
      quadros/*.jpg (quadros do resultado para conferir), .render/ (PNGs; refaz só o que mudou) e o vídeo final.
O vídeo de entrada só é lido. O ffmpeg do Homebrew não desenha texto: cada legenda vira um PNG transparente
desenhado pelo navegador e entra por cima do vídeo no tempo dela.
"""
import argparse
import base64
import hashlib
import json
import mimetypes
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (checar_ffmpeg, fmt_num, fmt_tempo, info_video, ler_json, ler_srt, navegador, rodar, sair,
                   srt_tempo, tempo, utf8)

MODELO = Path(__file__).resolve().parent.parent / "modelos" / "cartao.html"
PADRAO = {
    "fonte": None, "fonte_destaque": None, "tamanho": 64, "cor": "#FFFFFF", "cor_destaque": "#FFFFFF",
    "escala_destaque": 1.12, "sombra": 0.45, "maiusculas": False, "legenda_y": 1400, "margem": 110,
    "palavras_max": 4, "letras_max": 22, "legenda_y_alto": 330,
    "cartao_fundo": "#141414", "cartao_tinta": "#F5F2EC", "cartao_destaque": "#E8C27A",
}
TIPOS = {"lista", "etapas", "numero", "comparacao", "frase", "print", "imagem", "titulo", "colagem", "dividida"}
# a legenda nunca termina nestas palavras: elas vão para a próxima
LIGA = {"de", "da", "do", "das", "dos", "o", "a", "os", "as", "um", "uma", "pra", "para", "com", "e", "que", "em",
        "no", "na", "nos", "nas", "por", "pelo", "pela", "se", "ao", "à", "mais", "muito", "meu", "minha", "seu", "sua"}
PONT = ".,;:!?\"“”'…()"


def ascii_(w):
    return unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode()


def norm(w):
    return w.strip(PONT).lower()


# ---------------------------------------------------------------- legenda

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


def posicionar(leg, ins, estilo):
    """Cada legenda ganha a altura dela: sobe para o alto quando a inserção pede ("legenda": "alto"),
    some quando pede ("legenda": "some", ex.: tela dividida com faixa) e fica em legenda_y no resto."""
    out = []
    for a, b, ws in leg:
        y = estilo["legenda_y"]
        for d in ins:
            if a < d["ate"] - 0.05 and b > d["de"] + 0.05:
                pos = d.get("legenda") or ("some" if d["tipo"] == "dividida" else None)
                if pos == "some":
                    y = None
                elif pos == "alto":
                    y = estilo["legenda_y_alto"]
                elif isinstance(pos, (int, float)):
                    y = pos
        if y is not None:
            out.append((a, b, ws, y))
    return out


def montar_legendas(srt, estilo, destaques, correcoes):
    dest = {norm(w) for w in destaques}
    leg = []
    for ini, fim, texto in ler_srt(srt):
        for errado, certo in correcoes.items():      # palavra que o Whisper ouviu errado
            texto = re.sub(rf"(?<!\w){re.escape(errado)}(?!\w)", certo, texto)
        for a, b, g in picotar(ini, fim, texto, estilo["palavras_max"], estilo["letras_max"]):
            g = list(g)
            g[-1] = g[-1].rstrip(".,;:…")    # pontuação no fim do pedaço sai; "?" e "!" ficam
            leg.append((a, b, [[w, norm(w) in dest] for w in g if w]))
    return leg


# ---------------------------------------------------------------- mapa de inserções

def ler_mapa(pasta):
    p = pasta / "insercoes.json"
    if not p.exists():
        sair(f"Falta o {p}. Escreva o mapa de inserções antes (formato no SKILL.md).")
    m = ler_json(p)
    estilo = {**PADRAO, **(m.get("estilo") or {})}
    for k in ("fonte", "fonte_destaque"):
        if estilo[k]:
            f = Path(estilo[k]).expanduser()
            f = f if f.is_absolute() else (pasta / f)
            if not f.exists():
                sair(f"insercoes.json, estilo.{k}: não achei o arquivo {f}.")
            estilo[k] = str(f.resolve())
    ins = []
    for n, d in enumerate(m.get("insercoes") or [], 1):
        onde = f"insercoes.json, inserção {n}"
        if d.get("tipo") not in TIPOS:
            sair(f"{onde}: tipo {d.get('tipo')!r} não existe. Use um destes: {', '.join(sorted(TIPOS))}.")
        d = dict(d, n=n, de=tempo(d["de"], onde), ate=tempo(d["ate"], onde))
        if d["ate"] <= d["de"]:
            sair(f"{onde}: o fim vem antes do início.")
        if d["tipo"] in ("lista", "etapas"):
            itens = []
            for k, it in enumerate(d.get("itens") or []):
                it = {"texto": it} if isinstance(it, str) else dict(it)
                # item sem tempo: entram espalhados na primeira metade da inserção
                it["t"] = tempo(it["t"], onde) if "t" in it else d["de"] + k * (d["ate"] - d["de"]) * 0.5 / max(1, len(d["itens"]))
                itens.append(it)
            if not itens:
                sair(f"{onde}: lista sem itens.")
            d["itens"] = itens
        if d["tipo"] == "comparacao":
            d["t_direita"] = tempo(d.get("t_direita", (d["de"] + d["ate"]) / 2), onde)
        if d["tipo"] == "colagem":
            pecas = []
            for k, pc in enumerate(d.get("pecas") or []):
                pc = dict(pc)
                f = Path(pc.get("imagem", "")).expanduser()
                f = f if f.is_absolute() else (pasta / f)
                if not f.is_file():
                    sair(f"{onde}: não achei a imagem {f}.")
                pc["imagem_url"] = data_url(f)
                # peça sem tempo: entram espalhadas na primeira metade da inserção
                pc["t"] = tempo(pc["t"], onde) if "t" in pc else d["de"] + k * (d["ate"] - d["de"]) * 0.5 / max(1, len(d["pecas"]))
                pecas.append(pc)
            if not pecas:
                sair(f"{onde}: colagem sem peças.")
            d["pecas"] = pecas
        if d["tipo"] in ("print", "imagem", "dividida"):
            f = Path(d.get("imagem", "")).expanduser()
            f = f if f.is_absolute() else (pasta / f)
            if not f.is_file():
                sair(f"{onde}: não achei a imagem {f}.")
            d["imagem_url"] = data_url(f)
        ins.append(d)
    ins.sort(key=lambda d: d["de"])
    return estilo, m.get("destaques") or [], m.get("correcoes") or {}, ins


def estados(d):
    """[(t0, t1, estado)]: lista e etapas mostram um item a mais a cada tempo; comparação, um lado e depois os dois."""
    if d["tipo"] in ("lista", "etapas", "colagem"):
        ts = sorted(it["t"] for it in d["itens" if d["tipo"] != "colagem" else "pecas"])
        marcos = [(d["de"], max(1, sum(t <= d["de"] for t in ts)))] + [(t, k + 1) for k, t in enumerate(ts) if t > d["de"]]
    elif d["tipo"] == "comparacao":
        marcos = [(d["de"], 1), (d["t_direita"], 2)] if d["t_direita"] > d["de"] else [(d["de"], 2)]
    else:
        marcos = [(d["de"], 1)]
    marcos = [(t, e) for t, e in marcos if t < d["ate"]]
    return [(t, marcos[i + 1][0] if i + 1 < len(marcos) else d["ate"], e) for i, (t, e) in enumerate(marcos)]


def conferir(ins, estilo, dur):
    avisos = []
    for i, d in enumerate(ins):
        nome = f"Inserção {d['n']} ({fmt_tempo(d['de'])}, {d['tipo']})"
        if d["de"] < 1.0 and d["tipo"] != "dividida":
            avisos.append(f"{nome}: entra no primeiro segundo, em cima do gancho. Comece depois de 1 s.")
        if d["ate"] > dur + 0.05:
            avisos.append(f"{nome}: termina depois do fim do vídeo ({fmt_tempo(dur)}).")
        if d["ate"] - d["de"] > 6 and d.get("formato") != "painel" and d["tipo"] not in ("titulo", "colagem"):
            avisos.append(f"{nome}: fica {fmt_num(d['ate'] - d['de'])} s na tela; acima de 6 s o rosto some por tempo demais.")
        if d["ate"] - d["de"] > 10:
            avisos.append(f"{nome}: painel de {fmt_num(d['ate'] - d['de'])} s; acima de 10 s ele vira parte do cenário.")
        if i and d["de"] < ins[i - 1]["ate"]:
            sair(f"{nome} começa antes da inserção {ins[i - 1]['n']} terminar. Ajuste os tempos.")
        if i and d["de"] - ins[i - 1]["ate"] < 2.0:
            avisos.append(f"{nome}: só {fmt_num(d['de'] - ins[i - 1]['ate'])} s de rosto depois da anterior (régua: uns 2 s).")
        for it in d.get("itens", []):
            if not d["de"] <= it["t"] < d["ate"]:
                avisos.append(f"{nome}: o item «{it['texto']}» entra fora da inserção ({fmt_tempo(it['t'])}).")
    if contraste(estilo["cor"], estilo["cartao_fundo"]) < 3 and any(d.get("formato") != "painel" for d in ins):
        avisos.append("A cor da legenda quase some no fundo dos cartões de tela cheia: troque cartao_fundo ou cor.")
    return avisos


def lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ---------------------------------------------------------------- fontes

def data_url(f):
    tipo = mimetypes.guess_type(str(f))[0] or {".otf": "font/otf", ".ttf": "font/ttf", ".woff2": "font/woff2"}.get(
        Path(f).suffix.lower(), "application/octet-stream")
    return f"data:{tipo};base64,{base64.b64encode(Path(f).read_bytes()).decode()}"


def faltam_glifos(arquivo, texto):
    from fontTools.ttLib import TTFont
    fonte = TTFont(arquivo, fontNumber=0, lazy=True)
    cmap = fonte.getBestCmap() or {}
    return sorted({c for c in texto if not c.isspace() and ord(c) not in cmap})


def textos(ins, leg, estilo):
    corpo, dest = [], []
    for _, _, ws, *_ in leg:
        for w, d in ws:
            (dest if d else corpo).append(w.upper() if estilo["maiusculas"] else w)
    for d in ins:
        for k in ("titulo", "texto", "rotulo", "marca", "numero", "faixa"):
            if d.get(k):
                corpo.append(d[k])
        for it in d.get("itens", []):
            corpo.append(it["texto"])
        for lado in (d.get("esquerda"), d.get("direita")):
            if lado:
                corpo += [lado.get("texto", "")]
                dest += [lado.get("titulo", "")]
        dest += [d.get(k, "") for k in ("titulo", "numero") if d.get(k)]
        if d["tipo"] == "frase":
            dest.append(d.get("texto", ""))
    junto = " ".join(corpo + dest)
    dest += re.findall(r"\*(.+?)\*", junto)
    return junto.replace("*", ""), " ".join(dest).replace("*", "")


# ---------------------------------------------------------------- desenhar

def desenhar(pasta_render, estilo, leg, ins):
    """Fotografa cada legenda e cada estado de cartão. Nome do PNG = impressão digital do conteúdo: só refaz o que mudou."""
    from playwright.sync_api import sync_playwright
    pasta_render.mkdir(parents=True, exist_ok=True)
    fontes = {k: data_url(estilo[c]) for k, c in (("F", "fonte"), ("D", "fonte_destaque")) if estilo[c]}
    # o desenho (cartao.html) entra na impressão digital: mudou o modelo, tudo é redesenhado
    marca_estilo = hashlib.sha1(json.dumps(estilo, sort_keys=True).encode() + MODELO.read_bytes()).hexdigest()[:8]
    trabalhos = [("vazio", None)]
    trabalhos += [("leg", (ws, y)) for _, _, ws, y in leg]
    for d in ins:
        for _, _, e in estados(d):
            trabalhos.append(("cartao", (d, e)))
    nomes, a_fazer = [], []
    for tipo, x in trabalhos:
        chave = json.dumps([tipo, marca_estilo, x if tipo != "cartao" else
                            ({k: v for k, v in x[0].items() if k not in ("n",)}, x[1])], sort_keys=True, default=str)
        nome = f"{tipo}-{hashlib.sha1(chave.encode()).hexdigest()[:12]}.png"
        nomes.append(nome)
        if not (pasta_render / nome).exists():
            a_fazer.append((nome, tipo, x))
    medidas = {}
    if a_fazer:
        with sync_playwright() as pw:
            nav = navegador(pw)
            pag = nav.new_page(viewport={"width": 1080, "height": 1920})
            pag.goto(MODELO.as_uri())
            pag.wait_for_function("window.__pronto === true")
            pag.evaluate("([e, f]) => definirEstilo(e, f)", [estilo, fontes])
            for nome, tipo, x in a_fazer:
                if tipo == "leg":
                    medidas[nome] = pag.evaluate("([p, y]) => legenda(p, y)", [x[0], x[1]])
                elif tipo == "cartao":
                    medidas[nome] = pag.evaluate("([d, e]) => montar(d, e)", [x[0], x[1]])
                else:
                    pag.evaluate("() => { document.getElementById('cartao').className=''; document.getElementById('leg').style.display='none'; }")
                pag.screenshot(path=str(pasta_render / nome), omit_background=True)
                if tipo == "cartao":
                    # cartão de tela cheia sai sem transparência (RGB); a trilha precisa de todos os PNG em RGBA
                    f = pasta_render / nome
                    rodar(["ffmpeg", "-y", "-v", "error", "-i", f, "-pix_fmt", "rgba", f.with_suffix(".tmp.png")])
                    f.with_suffix(".tmp.png").replace(f)
            nav.close()
    return nomes, medidas


def folha_cartoes(pasta, pasta_render, ins, nomes_cartoes):
    """cartoes.png: todos os estados dos cartões lado a lado, pequenos, para conferir antes do vídeo."""
    from playwright.sync_api import sync_playwright
    cel = []
    for (d, e), nome in nomes_cartoes:
        rot = f"{d['n']} · {fmt_tempo(d['de'])} · {d['tipo']}" + (f" ({e})" if d["tipo"] in ("lista", "etapas", "comparacao") else "")
        cel.append(f'<figure><img src="{data_url(pasta_render / nome)}"><figcaption>{rot}</figcaption></figure>')
    html = ("<html><body style='margin:0;background:#777;font:16px sans-serif;display:flex;flex-wrap:wrap;gap:12px;padding:12px;width:1176px'>"
            "<style>figure{margin:0;width:270px}img{width:270px;height:480px;display:block;background:#3a3a3a}"
            "figcaption{color:#fff;padding:4px 0}</style>" + "".join(cel) + "</body></html>")
    with sync_playwright() as pw:
        nav = navegador(pw)
        pag = nav.new_page(viewport={"width": 1200, "height": 600})
        pag.set_content(html)
        pag.screenshot(path=str(pasta / "cartoes.png"), full_page=True)
        nav.close()


# ---------------------------------------------------------------- compor

def trilha(pasta_render, nome, eventos, dur, fps):
    """ffconcat com um PNG por evento e o PNG vazio nos intervalos (tempos no quadro mais próximo)."""
    q = lambda t: round(t * fps) / fps
    linhas, cur = ["ffconcat version 1.0"], 0.0
    for t0, t1, png in sorted(eventos):
        t0, t1 = max(q(t0), cur), q(t1)
        if t1 - t0 < 1 / fps:
            continue
        if t0 - cur >= 1 / fps:
            linhas += [f"file '{VAZIO}'", f"duration {t0 - cur:.4f}"]
        linhas += [f"file '{png}'", f"duration {t1 - t0:.4f}"]
        cur = t1
    linhas += [f"file '{VAZIO}'", f"duration {max(1.0, dur - cur + 1):.4f}", f"file '{VAZIO}'"]
    p = pasta_render / nome
    p.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return p


VAZIO = ""


def compor(video, info, faixas, saida, divididas=()):
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", video]
    filtros, atual = [], "[0:v]"
    # tela dividida: no tempo do gancho, o vídeo desce para a metade de baixo (recorte em volta do rosto)
    for j, (a, b, y) in enumerate(divididas):
        filtros.append(f"{atual}split[s{j}a][s{j}b]")
        filtros.append(f"[s{j}b]crop={info['w']}:{info['h'] // 2}:0:{y}[s{j}c]")
        filtros.append(f"[s{j}a][s{j}c]overlay=0:{info['h'] // 2}:enable='between(t,{a:.3f},{b:.3f})'[d{j}]")
        atual = f"[d{j}]"
    for k, f in enumerate(faixas, 1):
        cmd += ["-f", "concat", "-safe", "0", "-i", f]
        filtros.append(f"[{k}:v]format=rgba,scale={info['w']}:{info['h']}[c{k}]")
        filtros.append(f"{atual}[c{k}]overlay=0:0:eof_action=pass:format=auto[v{k}]")
        atual = f"[v{k}]"
    filtros.append(f"{atual}format=yuv420p[v]")
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", f"{info['fps']:.3f}",
            "-c:a", "copy" if info["audio"] == "aac" else "aac", "-movflags", "+faststart", saida]
    r = rodar(cmd)
    if r.returncode:
        sair("O ffmpeg falhou ao montar o vídeo:\n" + r.stderr[-1500:])


def quadros(saida, pasta, ins, leg, dur):
    """Quadros do resultado para conferir: cada estado de cartão e legendas com destaque, acento ou a mais longa."""
    q = pasta / "quadros"
    q.mkdir(exist_ok=True)
    for f in q.glob("*.jpg"):  # quadros da rodada anterior
        f.unlink()
    alvo = []
    for d in ins:
        for t0, t1, e in estados(d):
            alvo.append((min(t1 - 0.1, t0 + 0.4), f"insercao{d['n']:02d}-{e}"))
    leg = [x[:3] for x in leg]
    longa = max(leg, key=lambda x: len(" ".join(w for w, _ in x[2])), default=None)
    escolhidas = [x for x in leg if any(d for _, d in x[2])][:3]
    escolhidas += [x for x in leg if re.search(r"[ÃÕÇÁÉÍÓÚÂÊÔÀãõçáéíóúâêôà]", " ".join(w for w, _ in x[2]).upper())][:2]
    if longa:
        escolhidas.append(longa)
    for a, b, ws in escolhidas:
        alvo.append(((a + b) / 2, "legenda-" + re.sub(r"[^a-z0-9]+", "-", ascii_(norm(ws[0][0]))) or "x"))
    feitos = []
    for t, nome in alvo:
        f = q / f"{fmt_tempo(t).replace(':', '').replace(',', '')}-{nome}.jpg"
        rodar(["ffmpeg", "-y", "-v", "error", "-ss", f"{min(t, dur - 0.05):.3f}", "-i", saida, "-frames:v", "1",
               "-vf", "scale=540:-2", "-q:v", "3", f])
        feitos.append(f)
    # folha.jpg: todos os quadros numa imagem só, 6 por linha
    feitos = [f for f in feitos if f.exists()]
    if feitos:
        c = min(6, len(feitos))
        ent = sum((["-i", f] for f in feitos), [])
        esc = "".join(f"[{i}:v]scale=270:480[s{i}];" for i in range(len(feitos)))
        lay = "|".join(f"{(i % c) * 270}_{(i // c) * 480}" for i in range(len(feitos)))
        filtro = esc + "".join(f"[s{i}]" for i in range(len(feitos))) + (
            f"xstack=inputs={len(feitos)}:layout={lay}:fill=black" if len(feitos) > 1 else "null")
        rodar(["ffmpeg", "-y", "-v", "error", *ent, "-filter_complex", filtro, "-q:v", "3", q / "folha.jpg"])
    return feitos


# ---------------------------------------------------------------- principal

def main():
    global VAZIO
    utf8()
    ap = argparse.ArgumentParser(description="Inserções e legenda gravadas no vídeo.")
    ap.add_argument("decupagem")
    ap.add_argument("--video")
    ap.add_argument("--pasta")
    ap.add_argument("--saida")
    ap.add_argument("--cartoes", action="store_true")
    ap.add_argument("--sem-legenda", action="store_true")
    a = ap.parse_args()
    checar_ffmpeg()
    t_ini = time.time()
    dec = Path(a.decupagem).expanduser().resolve()
    pasta = Path(a.pasta).expanduser().resolve() if a.pasta else dec.parent / "insercoes"
    pasta.mkdir(parents=True, exist_ok=True)
    video = Path(a.video).expanduser().resolve() if a.video else next(
        (p for p in (dec / "final.mp4", dec / "previa.mp4") if p.exists()), None)
    if not video or not video.exists():
        sair("Não achei o vídeo cortado (final.mp4 ou previa.mp4 na decupagem). Passe --video.")
    info = info_video(video)
    estilo, destaques, correcoes, ins = ler_mapa(pasta)
    srt = dec / "legenda.srt"
    if not a.sem_legenda and not srt.exists():
        sair(f"Falta a legenda: {srt}. Rode a /decupar antes.")
    leg = [] if a.sem_legenda else montar_legendas(srt, estilo, destaques, correcoes)
    leg = posicionar(leg, ins, estilo)

    for arq, txt in zip((estilo["fonte"], estilo["fonte_destaque"]), textos(ins, leg, estilo)):
        if arq:
            falta = faltam_glifos(arq, txt)
            if falta:
                print(f"ATENÇÃO: a fonte {Path(arq).name} não tem {' '.join(falta)}: essas letras sairiam em outra fonte. "
                      "Troque a fonte ou o texto.")
    if not estilo["fonte"]:
        print("Sem arquivo de fonte no estilo: usando a fonte do sistema (Helvetica no Mac, Segoe no Windows).")
    for av in conferir(ins, estilo, info["dur"]):
        print("Aviso:", av)

    render = pasta / ".render"
    nomes, medidas = desenhar(render, estilo, leg, ins)
    VAZIO = nomes[0]
    nl = nomes[1:1 + len(leg)]
    nc = nomes[1 + len(leg):]
    pares, k = [], 0
    for d in ins:
        for t0, t1, e in estados(d):
            pares.append(((d, e), nc[k], t0, t1))
            k += 1
    for (d, e), nome, *_ in pares:
        m = medidas.get(nome)
        if m and m.get("transborda"):
            print(f"Aviso: o cartão {d['n']} ({d['tipo']}) não coube na área: encurte o texto ou tire um item.")
    folha_cartoes(pasta, render, ins, [(x[0], x[1]) for x in pares]) if pares else None
    (pasta / "legenda-curta.srt").write_text("\n".join(
        f"{i + 1}\n{srt_tempo(x[0])} --> {srt_tempo(x[1])}\n{' '.join(w for w, _ in x[2])}\n" for i, x in enumerate(leg)),
        encoding="utf-8")
    print(f"Vídeo: {fmt_tempo(info['dur'])} · {info['w']}×{info['h']} · {len(ins)} inserções · {len(leg)} legendas "
          f"(2 a {estilo['palavras_max']} palavras)")
    if a.cartoes:
        print(f"Cartões para conferir: {pasta / 'cartoes.png'}")
        return

    faixas = []
    if pares:
        faixas.append(trilha(render, "insercoes.ffconcat", [(t0, t1, n) for _, n, t0, t1 in pares], info["dur"], info["fps"]))
    if leg:
        faixas.append(trilha(render, "legenda.ffconcat", [(x[0], x[1], n) for x, n in zip(leg, nl)], info["dur"], info["fps"]))
    saida = Path(a.saida).expanduser().resolve() if a.saida else pasta / f"{video.stem}-insercoes.mp4"
    saida.parent.mkdir(parents=True, exist_ok=True)
    print(f"Montando o vídeo (no Mac com chip M, uns 20 s por minuto de vídeo)...", flush=True)
    divididas = [(d["de"], d["ate"], int(d.get("recorte_y", info["h"] // 6))) for d in ins if d["tipo"] == "dividida"]
    compor(str(video), info, [str(f) for f in faixas], str(saida), divididas)
    dur = info_video(saida)["dur"]
    ok = abs(dur - info["dur"]) < 0.2
    fs = quadros(str(saida), pasta, ins, leg, dur)
    print(f"{saida}: {fmt_tempo(dur)}" + ("" if ok else f" · ATENÇÃO: o vídeo de entrada tem {fmt_tempo(info['dur'])}"))
    print(f"Quadros para conferir ({len(fs)}): {pasta / 'quadros'} · todos juntos em {pasta / 'quadros' / 'folha.jpg'}")
    print(f"Pronto em {fmt_num(time.time() - t_ini)} s.")


if __name__ == "__main__":
    main()
