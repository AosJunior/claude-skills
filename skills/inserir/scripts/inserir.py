# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.48", "fonttools>=4.50", "numpy>=1.26", "opencv-python-headless>=4.9"]
# ///
"""/inserir: desenha a legenda, os cartões e as peças em HTML, fotografa em PNG transparente e grava tudo no vídeo,
num render só.

Uso:  uv run "<skill>/scripts/inserir.py" "<pasta decupagem>" --cartoes      só o que é desenhado: cartoes.png
      uv run "<skill>/scripts/inserir.py" "<pasta decupagem>"                vídeo final + quadros/
      opções: --video V (padrão: final.mp4, senão previa.mp4 da decupagem) · --pasta P (padrão: <pai>/insercoes)
              --saida ARQ.mp4 · --sem-legenda · --mascara auto|vision|rvm · --trabalhadores N

Lê:   <pasta decupagem>/palavras-corte.json (senão legenda.srt) e <P>/insercoes.json (formato em referencia.md).
Grava em <P>/: cartoes.png, legenda-curta.srt (a mesma lista da legenda gravada), quadros/folha.jpg, .render/ (PNGs;
      refaz só o que mudou), .dados/geometria.json (tudo o que foi desenhado, para a /criticar), .dados/mascaras/
      e o vídeo final. Sem `divididas` nem `camadas`, monta com o ffmpeg (rápido); com elas, com o compor.py.
Sai com código 2 quando há ATENÇÃO (zona segura, letra que a fonte não tem): nesse caso não grava o vídeo.
"""
import argparse
import base64
import hashlib
import html as html_mod
import json
import math
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import legenda as L
from comum import (Ancoras, achar_marca, caminho, checar_ffmpeg, contar_quadros, fmt_num, fmt_tempo, info_video,
                   ler_json, navegador, rodar, sair, srt_tempo, tempo, utf8)

AQUI = Path(__file__).resolve().parent
MODELO = AQUI.parent / "modelos" / "cartao.html"
PADRAO = {
    "fonte": None, "fonte_destaque": None, "tamanho": 64, "cor": "#FFFFFF", "cor_destaque": "#FFFFFF",
    "escala_destaque": 1.12, "sombra": 0.45, "maiusculas": False, "legenda_y": 1400, "margem": 110,
    "palavras_max": 4, "letras_max": 22, "legenda_y_alto": 330,
    "cartao_fundo": "#141414", "cartao_tinta": "#F5F2EC", "cartao_destaque": "#E8C27A",
    "minusculas": False, "juntar_numeros": False, "nomes": [], "destaque_y": None, "zona_segura": [260, 1600],
}
# réguas padrão: valem quando a receita de formato ou o marca/estilo.md não dizem outra coisa (estilo.reguas)
REGUAS = {"primeiro_segundo": 1.0, "min": 1.5, "max": 6.0, "max_painel": 10.0, "respiro": 2.0}
TIPOS = {"lista", "etapas", "numero", "comparacao", "frase", "print", "imagem", "titulo", "colagem", "dividida"}
TIPOS_CAMADA = {"video", "imagem", "faixa", "html"}
LUGARES = {"topo", "atras", "frente"}


def ascii_(w):
    return unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode()


def norm(w):
    return L.norm(w)


# ---------------------------------------------------------------- mapa de inserções

class Mapa:
    """O insercoes.json lido: tempos já em segundos (âncoras resolvidas) e caminhos já resolvidos."""


def ler_mapa(pasta, dec, marca, pasta_video):
    p = pasta / "insercoes.json"
    if not p.exists():
        sair(f"Falta o {p}. Escreva o mapa de inserções antes (formato em referencia.md).")
    m = ler_json(p)
    M = Mapa()
    M.correcoes = m.get("correcoes") or {}
    M.destaques = m.get("destaques") or []
    anc = Ancoras(dec)
    M.ancoras = anc
    T = lambda v, onde, fim=False: anc.tempo(v, onde, fim)
    arq = lambda s, onde: caminho(s, pasta, marca, onde)

    estilo = {**PADRAO, **(m.get("estilo") or {})}
    for k in ("fonte", "fonte_destaque"):
        if estilo[k]:
            f = arq(estilo[k], f"insercoes.json, estilo.{k}")
            if not f.exists():
                sair(f"insercoes.json, estilo.{k}: não achei o arquivo {f}.")
            estilo[k] = str(f.resolve())
    estilo["reguas"] = {**REGUAS, **(estilo.get("reguas") or {})}
    M.estilo = estilo

    # faixas da legenda: a lista "legenda" e depois quem pede "legenda" (camada ou inserção); a última que pega manda
    faixas = []
    for n, f in enumerate(m.get("legenda") or [], 1):
        onde = f"insercoes.json, legenda {n}"
        faixas.append((T(f.get("de", 0), onde), T(f.get("ate"), onde, True), f.get("y"), f.get("aceito")))

    ins = []
    for n, d in enumerate(m.get("insercoes") or [], 1):
        onde = f"insercoes.json, inserção {n}"
        if d.get("tipo") not in TIPOS:
            sair(f"{onde}: tipo {d.get('tipo')!r} não existe. Use um destes: {', '.join(sorted(TIPOS))}.")
        d = dict(d, n=n, de=T(d["de"], onde), ate=T(d["ate"], onde, True))
        if d["ate"] <= d["de"]:
            sair(f"{onde}: o fim vem antes do início.")
        if d["tipo"] in ("lista", "etapas"):
            itens = []
            for k, it in enumerate(d.get("itens") or []):
                it = {"texto": it} if isinstance(it, str) else dict(it)
                # item sem tempo: entram espalhados na primeira metade da inserção
                it["t"] = T(it["t"], onde) if "t" in it else d["de"] + k * (d["ate"] - d["de"]) * 0.5 / max(1, len(d["itens"]))
                itens.append(it)
            if not itens:
                sair(f"{onde}: lista sem itens.")
            d["itens"] = itens
        if d["tipo"] == "comparacao":
            d["t_direita"] = T(d.get("t_direita", (d["de"] + d["ate"]) / 2), onde)
        if d["tipo"] == "colagem":
            pecas = []
            for k, pc in enumerate(d.get("pecas") or []):
                pc = dict(pc)
                f = arq(pc.get("imagem", ""), onde)
                if not f.is_file():
                    sair(f"{onde}: não achei a imagem {f}.")
                pc["imagem_url"] = data_url(f)
                # peça sem tempo: entram espalhadas na primeira metade da inserção
                pc["t"] = T(pc["t"], onde) if "t" in pc else d["de"] + k * (d["ate"] - d["de"]) * 0.5 / max(1, len(d["pecas"]))
                pecas.append(pc)
            if not pecas:
                sair(f"{onde}: colagem sem peças.")
            d["pecas"] = pecas
        if d["tipo"] in ("print", "imagem", "dividida"):
            f = arq(d.get("imagem", ""), onde)
            if not f.is_file():
                sair(f"{onde}: não achei a imagem {f}.")
            d["imagem_url"] = data_url(f)
        ins.append(d)
    ins.sort(key=lambda d: d["de"])
    for d in ins:
        pos = d.get("legenda") or ("some" if d["tipo"] == "dividida" else None)
        if pos is not None:
            faixas.append((d["de"], d["ate"], pos, d.get("aceito")))
    M.ins = ins

    # telas divididas
    divs = []
    for n, d in enumerate(m.get("divididas") or [], 1):
        onde = f"insercoes.json, dividida {n}"
        d = dict(d, id=d.get("id") or f"dividida-{n}", de=T(d.get("de", 0), onde), ate=T(d.get("ate"), onde, True))
        d["corte"] = int(d.get("corte", 960))
        pessoa = d.get("pessoa") or [{"de": d["de"], "recorte_y": d.get("recorte_y", 0)}]
        d["pessoa"] = [dict(pp, de=T(pp.get("de", d["de"]), onde), recorte_y=int(pp.get("recorte_y", 0)),
                            escala=float(pp.get("escala", 1.0))) for pp in pessoa]
        d.setdefault("laterais", "borrado")
        if d["ate"] <= d["de"]:
            sair(f"{onde}: o fim vem antes do início.")
        divs.append(d)
    M.divididas = divs

    # camadas
    fontes_md = pasta_video / "brutos" / "fontes.md"
    origens = fontes_md.read_text(encoding="utf-8") if fontes_md.exists() else ""
    cams, ids = [], set()
    for n, c in enumerate(m.get("camadas") or [], 1):
        c = dict(c)
        onde = f"insercoes.json, camada {n}" + (f" ({c['id']})" if c.get("id") else "")
        if c.get("tipo") not in TIPOS_CAMADA:
            sair(f"{onde}: tipo {c.get('tipo')!r} não existe. Use um destes: {', '.join(sorted(TIPOS_CAMADA))}.")
        c["id"] = c.get("id") or f"{c['tipo']}-{n}"
        if c["id"] in ids:
            sair(f"{onde}: o id {c['id']!r} se repete; cada camada precisa de um id dela.")
        ids.add(c["id"])
        c["n"] = n
        c["lugar"] = c.get("lugar") or "frente"
        if c["lugar"] not in LUGARES:
            sair(f"{onde}: lugar {c['lugar']!r} não existe. Use topo, atras ou frente.")
        c["de"], c["ate"] = T(c.get("de", 0), onde), T(c.get("ate"), onde, True)
        if c["ate"] <= c["de"]:
            sair(f"{onde}: o fim vem antes do início.")
        for k in ("entra", "sai"):
            v = c.get(k)
            c[k] = {"efeito": "alfa", "dur": float(v)} if isinstance(v, (int, float)) else (
                {"efeito": v.get("efeito", "pop"), "dur": float(v.get("dur", 0.18))} if isinstance(v, dict) else None)
        if c["tipo"] in ("video", "imagem"):
            f = arq(c.get("arquivo", ""), onde)
            if not f.is_file():
                sair(f"{onde}: não achei o arquivo {f}.")
            try:
                f.relative_to(Path(os.path.normpath(pasta_video / "brutos")))
                de_brutos = True
            except ValueError:
                de_brutos = False
            if de_brutos and not re.search(rf"(?<![\w.-]){re.escape(f.name)}(?![\w-])", origens):
                sair(f"{onde}: {f.name} veio de brutos/, mas não tem a origem anotada em brutos/fontes.md. "
                     f"Escreva uma linha com «{f.name}», o endereço de onde veio e a licença.")
            c["arquivo"] = str(f)
        if c["tipo"] == "html":
            f = arq(c.get("modelo", ""), onde)
            if not f.is_file():
                sair(f"{onde}: não achei o modelo {f}.")
            c["modelo"] = str(f)
        if c["tipo"] == "faixa":
            if c.get("fonte"):
                f = arq(c["fonte"], onde)
                if not f.is_file():
                    sair(f"{onde}: não achei a fonte {f}.")
                c["fonte"] = str(f)
        if c["tipo"] == "video":
            preparar_video(c, divs, T, onde)
        elif c["tipo"] == "imagem":
            import cv2
            img = cv2.imread(c["arquivo"], cv2.IMREAD_UNCHANGED)
            if img is None:
                sair(f"{onde}: não consegui abrir a imagem {c['arquivo']}.")
            ih, iw = img.shape[:2]
            c["w"] = int(c.get("w") or iw)
            c["h"] = int(c.get("h") or round(ih * c["w"] / iw))
            c.setdefault("x", 0)
            c.setdefault("y", 0)
        if "legenda" in c:
            faixas.append((c["de"], c["ate"], c["legenda"], c.get("aceito")))
        cams.append(c)
    M.camadas = cams
    M.faixas = faixas
    return M


def dims(arq):
    r = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,duration",
               "-show_entries", "format=duration", "-of", "json", arq])
    d = json.loads(r.stdout)
    s = d["streams"][0]
    return s["width"], s["height"], float(d.get("format", {}).get("duration") or 0)


def preparar_video(c, divs, T, onde):
    """Camada de vídeo: tamanho na tela e os trechos (recorte fixo ou com mudança no tempo, o "aberto e depois o zoom")."""
    sw, sh, sdur = dims(c["arquivo"])
    rec = c.get("recorte")
    if rec and isinstance(rec[0], (int, float)):
        rec = [{"t": 0, "caixa": rec}]
    rec = sorted([dict(r, t=float(r.get("t", 0))) for r in rec], key=lambda r: r["t"]) if rec else [{"t": 0, "caixa": None}]
    for r in rec:
        cx = r.get("caixa")
        if cx and (cx[0] < 0 or cx[1] < 0 or cx[0] + cx[2] > sw or cx[1] + cx[3] > sh):
            sair(f"{onde}: o recorte {cx} sai do vídeo de origem ({sw}×{sh}).")
    caixa0 = rec[0].get("caixa")
    asp = (caixa0[3] / caixa0[2]) if caixa0 else sh / sw
    if c["lugar"] == "topo":
        div = next((d for d in divs if d["de"] <= c["de"] + 0.01 < d["ate"]), None)
        c.setdefault("w", 720)
        c.setdefault("h", div["corte"] if div else 960)
    else:
        if not c.get("w"):
            sair(f"{onde}: falta a largura (w) da camada na tela.")
        c.setdefault("h", int(round(c["w"] * asp)))
        c.setdefault("x", 0)
        c.setdefault("y", 0)
    c["w"], c["h"] = int(c["w"]), int(c["h"])
    src0 = float(c.get("src", 0))
    trechos = []
    for k, r in enumerate(rec):
        de = c["de"] + r["t"]
        ate = c["de"] + rec[k + 1]["t"] if k + 1 < len(rec) else c["ate"]
        if ate <= de:
            continue
        src = float(r["src"]) if "src" in r else src0 + r["t"]
        dur = r.get("dur", c.get("dur") if k == 0 else None)
        if src >= sdur:
            sair(f"{onde}: o src {fmt_num(src, 2)} s passa do fim do vídeo de origem ({fmt_num(sdur, 2)} s).")
        trechos.append({"de": de, "ate": ate, "arquivo": c["arquivo"], "src": src, "caixa": r.get("caixa"),
                        "dur": float(dur) if dur else None})
    c["trechos"] = trechos


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


# ---------------------------------------------------------------- réguas e zona segura

def conferir(M, dur):
    """Avisos das réguas (padrão ou da receita) para o que cobre o rosto: cartões e camadas da frente.
    Camada atrás da pessoa ou no topo da dividida não cobre o rosto e não entra aqui."""
    R = M.estilo["reguas"]
    avisos = []
    ins = M.ins
    for i in range(1, len(ins)):
        if ins[i]["de"] < ins[i - 1]["ate"]:
            sair(f"Inserção {ins[i]['n']} ({fmt_tempo(ins[i]['de'])}) começa antes da inserção {ins[i - 1]['n']} terminar. "
                 "Ajuste os tempos.")
    em_dividida = lambda t: any(d["de"] - 0.05 <= t < d["ate"] for d in M.divididas) or \
        any(d["tipo"] == "dividida" and d["de"] - 0.05 <= t < d["ate"] for d in ins)
    cobre = []
    for d in ins:
        nome = f"Inserção {d['n']} ({fmt_tempo(d['de'])}, {d['tipo']})"
        maxd = None if d["tipo"] in ("titulo", "colagem") else (R["max_painel"] if d.get("formato") == "painel" else R["max"])
        cobre.append((d, nome, d["tipo"] == "dividida", maxd))
        for it in d.get("itens", []):
            if not d["de"] <= it["t"] < d["ate"]:
                avisos.append((d, f"{nome}: o item «{it['texto']}» entra fora da inserção ({fmt_tempo(it['t'])})."))
    for c in M.camadas:
        if c["lugar"] == "frente":
            cobre.append((c, f"Camada {c['id']} ({fmt_tempo(c['de'])}, {c['tipo']})", False, R["max"]))
        if c["lugar"] == "topo" and not any(d["de"] - 0.05 <= c["de"] and c["ate"] <= d["ate"] + 0.05 for d in M.divididas):
            avisos.append((c, f"Camada {c['id']}: está no topo, mas fora de uma tela dividida; fora dela não aparece."))
    cobre.sort(key=lambda x: x[0]["de"])
    ant = None
    for d, nome, isenta, maxd in cobre:
        dd = d["ate"] - d["de"]
        if R.get("primeiro_segundo") and d["de"] < R["primeiro_segundo"] and not isenta and not em_dividida(d["de"]):
            avisos.append((d, f"{nome}: entra no primeiro segundo, em cima do gancho (régua: depois de "
                              f"{fmt_num(R['primeiro_segundo'])} s)."))
        if d["ate"] > dur + 0.05:
            avisos.append((d, f"{nome}: termina depois do fim do vídeo ({fmt_tempo(dur)})."))
        if R.get("min") and dd < R["min"] and not isenta:
            avisos.append((d, f"{nome}: fica só {fmt_num(dd)} s na tela (régua: de {fmt_num(R['min'])} s para cima)."))
        if maxd and R.get("max") and dd > maxd:
            avisos.append((d, f"{nome}: fica {fmt_num(dd)} s na tela; acima de {fmt_num(maxd)} s o rosto some por tempo demais."))
        if ant is not None and R.get("respiro") and 0 <= d["de"] - ant["ate"] < R["respiro"]:
            avisos.append((d, f"{nome}: só {fmt_num(d['de'] - ant['ate'])} s de rosto depois da anterior "
                              f"(régua: {fmt_num(R['respiro'])} s)."))
        ant = d if ant is None or d["ate"] > ant["ate"] else ant
    e = M.estilo
    if contraste(e["cor"], e["cartao_fundo"]) < 3 and any(d.get("formato") != "painel" and d["tipo"] not in
                                                          ("titulo", "colagem", "dividida", "imagem") for d in ins):
        avisos.append(({}, "A cor da legenda quase some no fundo dos cartões de tela cheia: troque cartao_fundo ou cor."))
    return [txt for d, txt in avisos if not d.get("aceito")]


def fora_da_zona(caixa, zona):
    return caixa and (caixa[1] < zona[0] - 0.5 or caixa[1] + caixa[3] > zona[1] + 0.5)


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

def html_preenchido(c, pasta_render):
    """O modelo html da camada com cada {{campo}} trocado pelo texto (escapado) e a base apontando para a pasta do modelo."""
    modelo = Path(c["modelo"])
    txt = modelo.read_text(encoding="utf-8")
    campos = c.get("campos") or {}
    faltam = sorted(set(re.findall(r"\{\{\s*(\w+)\s*\}\}", txt)) - set(campos))
    if faltam:
        sair(f"Camada {c['id']}: o modelo {modelo.name} pede {', '.join(faltam)} em «campos».")
    txt = re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: html_mod.escape(str(campos[m.group(1)])), txt)
    base = f'<base href="{modelo.parent.as_uri()}/">'
    txt = re.sub(r"(<head[^>]*>)", r"\1" + base, txt, count=1, flags=re.I) if re.search(r"<head", txt, re.I) else base + txt
    return txt


def desenhar(pasta_render, estilo, leg, ins, cams):
    """Fotografa cada legenda, cada estado de cartão e cada faixa ou html. Nome do PNG = impressão digital do
    conteúdo: só refaz o que mudou. As medidas (caixa de cada desenho) ficam em medidas.json."""
    pasta_render.mkdir(parents=True, exist_ok=True)
    fontes = {k: data_url(estilo[c]) for k, c in (("F", "fonte"), ("D", "fonte_destaque")) if estilo[c]}
    # o desenho (cartao.html) entra na impressão digital: mudou o modelo, tudo é redesenhado
    so_estilo = {k: v for k, v in estilo.items() if k != "reguas"}
    marca_estilo = hashlib.sha1(json.dumps(so_estilo, sort_keys=True).encode() + MODELO.read_bytes()).hexdigest()[:8]
    trabalhos = [("vazio", None)]
    trabalhos += [("leg", (ws, y)) for _, _, ws, y, *_ in leg]
    for d in ins:
        for _, _, e in estados(d):
            trabalhos.append(("cartao", (d, e)))
    for c in cams:
        if c["tipo"] in ("faixa", "html"):
            trabalhos.append((c["tipo"], c))
    nomes, a_fazer = [], []
    for tipo, x in trabalhos:
        if tipo == "cartao":
            x_chave = ({k: v for k, v in x[0].items() if k not in ("n",)}, x[1])
        elif tipo == "faixa":
            fonte = Path(x["fonte"]).read_bytes() if x.get("fonte") else b""
            x_chave = [{k: x.get(k) for k in ("texto", "x", "y", "largura", "altura", "raio", "fundo", "tinta", "tamanho")},
                       hashlib.sha1(fonte).hexdigest()]
        elif tipo == "html":
            x_chave = html_preenchido(x, pasta_render)
        else:
            x_chave = x
        chave = json.dumps([tipo, marca_estilo, x_chave], sort_keys=True, default=str)
        nome = f"{tipo}-{hashlib.sha1(chave.encode()).hexdigest()[:12]}.png"
        nomes.append(nome)
        if not (pasta_render / nome).exists():
            a_fazer.append((nome, tipo, x))
    arq_medidas = pasta_render / "medidas.json"
    medidas = ler_json(arq_medidas) if arq_medidas.exists() else {}
    if a_fazer:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            nav = navegador(pw)
            pag = nav.new_page(viewport={"width": 1080, "height": 1920})
            pag.goto(MODELO.as_uri())
            pag.wait_for_function("window.__pronto === true")
            pag.evaluate("([e, f]) => definirEstilo(e, f)", [so_estilo, fontes])
            pag2 = None
            for nome, tipo, x in a_fazer:
                alvo = pag
                if tipo == "leg":
                    medidas[nome] = pag.evaluate("([p, y]) => legenda(p, y)", [x[0], x[1]])
                elif tipo == "cartao":
                    medidas[nome] = pag.evaluate("([d, e]) => montar(d, e)", [x[0], x[1]])
                elif tipo == "faixa":
                    d = {k: x.get(k) for k in ("texto", "x", "y", "largura", "altura", "raio", "fundo", "tinta", "tamanho")}
                    medidas[nome] = pag.evaluate("([d, f]) => faixa(d, f)", [d, data_url(x["fonte"]) if x.get("fonte") else None])
                elif tipo == "html":
                    pag2 = pag2 or nav.new_page(viewport={"width": 1080, "height": 1920})
                    f = pasta_render / (nome[:-4] + ".html")
                    f.write_text(html_preenchido(x, pasta_render), encoding="utf-8")
                    pag2.goto(f.as_uri())
                    pag2.evaluate("document.fonts.ready")
                    if re.search(r"data-pronto|dataset\.pronto", f.read_text(encoding="utf-8")):
                        # o modelo diz quando terminou de se arrumar (encolher linha larga, esconder campo vazio)
                        pag2.wait_for_selector("body[data-pronto]", state="attached", timeout=15000)
                    else:
                        pag2.wait_for_timeout(100)
                    alvo = pag2
                else:
                    pag.evaluate("() => { document.getElementById('cartao').className=''; "
                                 "document.getElementById('leg').style.display='none'; "
                                 "document.getElementById('faixa').style.display='none'; }")
                alvo.screenshot(path=str(pasta_render / nome), omit_background=True)
                if tipo == "cartao":
                    # cartão de tela cheia sai sem transparência (RGB); a trilha precisa de todos os PNG em RGBA
                    f = pasta_render / nome
                    rodar(["ffmpeg", "-y", "-v", "error", "-i", f, "-pix_fmt", "rgba", f.with_suffix(".tmp.png")])
                    f.with_suffix(".tmp.png").replace(f)
                if tipo == "html":
                    medidas[nome] = {"caixa": caixa_alfa(pasta_render / nome)}
            nav.close()
        arq_medidas.write_text(json.dumps(medidas), encoding="utf-8")
    return nomes, medidas


def caixa_alfa(png):
    """[x, y, w, h] da parte desenhada (alfa > 0) de um PNG."""
    import cv2
    import numpy as np
    a = cv2.imread(str(png), cv2.IMREAD_UNCHANGED)
    if a is None or a.ndim < 3 or a.shape[2] < 4:
        return None
    ys, xs = np.nonzero(a[..., 3] > 8)
    if not len(xs):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]


def folha_cartoes(pasta, pasta_render, celulas):
    """cartoes.png: todos os desenhos (estados dos cartões, faixas, letterings) lado a lado, pequenos, para conferir."""
    from playwright.sync_api import sync_playwright
    cel = [f'<figure><img src="{data_url(pasta_render / nome)}"><figcaption>{html_mod.escape(rot)}</figcaption></figure>'
           for rot, nome in celulas]
    html = ("<html><body style='margin:0;background:#777;font:16px sans-serif;display:flex;flex-wrap:wrap;gap:12px;padding:12px;width:1176px'>"
            "<style>figure{margin:0;width:270px}img{width:270px;height:480px;display:block;background:#3a3a3a}"
            "figcaption{color:#fff;padding:4px 0}</style>" + "".join(cel) + "</body></html>")
    with sync_playwright() as pw:
        nav = navegador(pw)
        pag = nav.new_page(viewport={"width": 1200, "height": 600})
        pag.set_content(html)
        pag.screenshot(path=str(pasta / "cartoes.png"), full_page=True)
        nav.close()


# ---------------------------------------------------------------- compor: caminho rápido (só ffmpeg)

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


def compor_ffmpeg(video, info, faixas, saida, divididas=()):
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


# ---------------------------------------------------------------- compor: motor (dividida e camadas)

def mascaras(video, pasta, M, fps, n_quadros, motor):
    """Trechos de quadros com camada atrás da pessoa (fora da dividida), com folga; gera as máscaras que faltam."""
    tr = []
    for c in M.camadas:
        if c["lugar"] != "atras":
            continue
        q0, q1 = max(0, int(round(c["de"] * fps)) - 3), min(n_quadros, int(round(c["ate"] * fps)) + 3)
        tr.append([q0, q1])
    tr.sort()
    juntos = []
    for q0, q1 in tr:
        if juntos and q0 <= juntos[-1][1] + int(fps):
            juntos[-1][1] = max(juntos[-1][1], q1)
        else:
            juntos.append([q0, q1])
    if not juntos:
        return []
    print(f"Máscara da pessoa em {len(juntos)} trecho(s) ({fmt_num(sum(b - a for a, b in juntos) / fps)} s de vídeo); "
          "no Mac com chip M, uns 8 quadros por segundo; depois fica guardada.", flush=True)
    uv = shutil.which("uv")
    cmd = ([uv, "run", "-q"] if uv else [sys.executable]) + [
        str(AQUI / "mascara.py"), str(video), str(pasta / ".dados" / "mascaras"),
        "--trechos", ",".join(f"{a}:{b}" for a, b in juntos), "--motor", motor, "--fps", FPS_TXT]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    linhas = r.stdout.strip().splitlines()
    for l in linhas[:-1]:
        print(l)
    if r.returncode or not linhas:
        sair("Não consegui gerar a máscara da pessoa." + ("\n" + "\n".join(linhas[-5:]) if linhas else ""))
    d = json.loads(linhas[-1])
    return d["mascaras"]


FPS_TXT = "30/1"


def codificador():
    """Mac: o codificador do chip (h264_videotoolbox, 16 Mb/s); Windows e Linux: libx264 veryfast, crf 17."""
    if sys.platform == "darwin" and "h264_videotoolbox" in rodar(["ffmpeg", "-hide_banner", "-encoders"]).stdout:
        return {"codificador": "videotoolbox", "taxa": "16M"}
    return {"codificador": "libx264", "preset": "veryfast", "crf": 17}


def plano_compor(M, video, info, n_quadros, saida, pasta, render, pares, leg, nl, nomes_cam, masc, trab):
    camadas, sons = [], []
    for c in M.camadas:
        base = {k: c.get(k) for k in ("id", "lugar", "de", "ate", "x", "y", "w", "h", "rot", "raio", "sombra", "entra", "sai")}
        if c["tipo"] == "video":
            camadas.append(dict(base, tipo="video", trechos=c["trechos"]))
            if c.get("audio") is not None:
                for s in c["trechos"]:
                    sons.append({"arquivo": s["arquivo"], "src": s["src"], "de": s["de"], "ate": s["ate"],
                                 "ganho": float(c["audio"])})
        elif c["tipo"] == "imagem":
            camadas.append(dict(base, tipo="imagem", arquivo=c["arquivo"]))
        else:   # faixa e html: o PNG de tela cheia recortado na parte desenhada
            camadas.append(dict(base, tipo="imagem", arquivo=str(render / nomes_cam[c["id"]]), cheia=True,
                                x=0, y=0, w=None, h=None, raio=0))
    divs = [{"id": d["id"], "de": d["de"], "ate": d["ate"], "corte": d["corte"], "laterais": d["laterais"],
             "pessoa": d["pessoa"]} for d in M.divididas]
    for d in M.ins:   # o gancho em tela dividida do formato antigo vira uma dividida do motor
        if d["tipo"] == "dividida":
            divs.append({"id": f"insercao-{d['n']}", "de": d["de"], "ate": d["ate"], "corte": 960, "laterais": "preto",
                         "pessoa": [{"de": d["de"], "recorte_y": int(d.get("recorte_y", 320)), "escala": 1.0}]})
    return {
        "video": str(video), "saida": str(saida), "dados": str(pasta / ".dados"), "fps": info["fps"], "fps_txt": FPS_TXT,
        "quadros": n_quadros, "trabalhadores": trab, "audio_codec": info["audio"], **codificador(),
        "divididas": divs, "camadas": camadas,
        "cartoes": [{"png": str(render / nome), "de": t0, "ate": t1} for _, nome, t0, t1 in pares],
        "legendas": [{"png": str(render / n), "de": x[0], "ate": x[1]} for x, n in zip(leg, nl)],
        "mascaras": masc, "audio": sons,
    }


# ---------------------------------------------------------------- conferência

def quadros(saida, pasta, ins, leg, dur, cams=(), divs=()):
    """Quadros do resultado para conferir: cada estado de cartão, cada camada, a dividida e legendas com destaque,
    acento ou a mais longa."""
    q = pasta / "quadros"
    q.mkdir(exist_ok=True)
    for f in q.glob("*.jpg"):  # quadros da rodada anterior
        f.unlink()
    alvo = []
    for d in ins:
        for t0, t1, e in estados(d):
            alvo.append((min(t1 - 0.1, t0 + 0.4), f"insercao{d['n']:02d}-{e}"))
    for d in divs:
        alvo.append((d["de"] + min(0.5, (d["ate"] - d["de"]) / 2), f"dividida-{d['id']}"))
    grupos = []                                        # mosaico que entra aos poucos: um quadro pelo grupo
    for c in sorted((c for c in cams if c["lugar"] != "topo"), key=lambda c: c["de"]):
        if grupos and c["de"] < grupos[-1][1] and c["lugar"] == grupos[-1][2]["lugar"]:
            grupos[-1][1] = max(grupos[-1][1], c["ate"])
            grupos[-1][3] = c["de"]
        else:
            grupos.append([c["de"], c["ate"], c, c["de"]])
    for de, ate, c, ultimo in grupos:
        alvo.append((min(ate - 0.15, max(de + 0.4, ultimo + 0.4)), f"camada-{c['id']}"))
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


def geometria(M, leg, nl, pares, medidas, nomes_cam, dur):
    from compor import caixa_girada
    itens = []
    for k, (x, n) in enumerate(zip(leg, nl), 1):
        a, b, ws, y, aceito = x
        cx = (medidas.get(n) or {}).get("caixa")
        itens.append({"id": f"leg-{k:04d}", "tipo": "legenda", "texto": " ".join(w for w, _ in ws),
                      "destaque": any(d for _, d in ws), "de": round(a, 3), "ate": round(b, 3), "caixa": cx,
                      **({"aceito": aceito} if aceito else {})})
    for (d, e), nome, t0, t1 in pares:
        itens.append({"id": f"insercao-{d['n']}" + (f"-{e}" if len(estados(d)) > 1 else ""), "tipo": d["tipo"],
                      "lugar": "cartao", "de": round(t0, 3), "ate": round(t1, 3),
                      "caixa": (medidas.get(nome) or {}).get("caixa"), **({"aceito": d["aceito"]} if d.get("aceito") else {})})
    for c in M.camadas:
        if c["tipo"] in ("faixa", "html"):
            cx = (medidas.get(nomes_cam[c["id"]]) or {}).get("caixa")
        elif c["lugar"] == "topo":
            corte = next((d["corte"] for d in M.divididas if d["de"] <= c["de"] + 0.01 < d["ate"]), 960)
            cx = [0, 0, 1080, corte]
        elif c["tipo"] == "video" or c.get("w"):
            b = caixa_girada(c["x"], c["y"], c["w"], c["h"], c.get("rot") or 0)
            cx = [round(b[0]), round(b[1]), round(b[2] - b[0]), round(b[3] - b[1])]
        else:
            cx = None
        texto = c.get("texto") if c["tipo"] == "faixa" else (
            " ".join(str(v) for v in (c.get("campos") or {}).values() if str(v).strip()) if c["tipo"] == "html" else None)
        itens.append({"id": c["id"], "tipo": c["tipo"], "lugar": c["lugar"], "de": round(c["de"], 3),
                      "ate": round(c["ate"], 3), "caixa": cx, **({"texto": texto} if texto else {}),
                      **({"aceito": c["aceito"]} if c.get("aceito") else {})})
    for d in M.divididas:
        itens.append({"id": d["id"], "tipo": "dividida", "de": round(d["de"], 3), "ate": round(d["ate"], 3),
                      "corte": d["corte"], "laterais": d["laterais"],
                      "pessoa": [{"de": round(pp["de"], 3), "recorte_y": pp["recorte_y"], "escala": pp["escala"]}
                                 for pp in d["pessoa"]]})
    for d in M.ins:   # o gancho em tela dividida do formato antigo (inserção "dividida") também é uma dividida
        if d["tipo"] == "dividida":
            itens.append({"id": f"insercao-{d['n']}-dividida", "tipo": "dividida", "de": round(d["de"], 3),
                          "ate": round(d["ate"], 3), "corte": 960, "laterais": "preto",
                          "pessoa": [{"de": round(d["de"], 3), "recorte_y": int(d.get("recorte_y", 320)), "escala": 1.0}]})
    return {"duracao": round(dur, 3), "quadro": [1080, 1920], "zona_segura": M.estilo["zona_segura"], "itens": itens}


def zona(M, geo, leg):
    """ATENÇÃO para texto ou peça da frente fora da zona segura (padrão: y de 260 a 1600)."""
    z = M.estilo["zona_segura"]
    lugar = {c["id"]: c["lugar"] for c in M.camadas}
    out, leg_fora = [], {}
    for it, x in zip([i for i in geo["itens"] if i["tipo"] == "legenda"], leg):
        if fora_da_zona(it["caixa"], z) and not x[4]:
            leg_fora.setdefault(x[3], []).append(it)
    for y, its in leg_fora.items():
        out.append(f"a legenda em y {y} sai da zona segura ({z[0]}–{z[1]}) em {len(its)} pedaço(s), "
                   f"a partir de {fmt_tempo(its[0]['de'])} («{its[0]['texto']}»). Mude legenda_y, destaque_y ou a faixa.")
    for it in geo["itens"]:
        if it["tipo"] in ("legenda", "dividida") or not it.get("caixa"):
            continue
        if lugar.get(it["id"]) in ("atras", "topo") or it.get("aceito"):
            continue
        if fora_da_zona(it["caixa"], z):
            cx = it["caixa"]
            out.append(f"{it['id']} ({fmt_tempo(it['de'])}) vai de y {cx[1]} a {cx[1] + cx[3]}, fora da zona segura "
                       f"({z[0]}–{z[1]}): os botões e o nome do perfil cobrem. Mude a posição ou escreva "
                       "\"aceito\": \"<motivo>\" nele.")
    return out


# ---------------------------------------------------------------- principal

def main():
    global VAZIO, FPS_TXT
    utf8()
    ap = argparse.ArgumentParser(description="Inserções e legenda gravadas no vídeo.")
    ap.add_argument("decupagem")
    ap.add_argument("--video")
    ap.add_argument("--pasta")
    ap.add_argument("--saida")
    ap.add_argument("--cartoes", action="store_true")
    ap.add_argument("--sem-legenda", action="store_true")
    ap.add_argument("--mascara", default="auto", choices=["auto", "vision", "rvm"])
    ap.add_argument("--trabalhadores", type=int)
    a = ap.parse_args()
    checar_ffmpeg()
    t_ini = time.time()
    dec = Path(a.decupagem).expanduser().resolve()
    pasta_video = Path(os.path.normpath(Path(a.decupagem).expanduser().absolute())).parent
    pasta = Path(a.pasta).expanduser().resolve() if a.pasta else dec.parent / "insercoes"
    pasta.mkdir(parents=True, exist_ok=True)
    video = Path(a.video).expanduser().resolve() if a.video else next(
        (p for p in (dec / "final.mp4", dec / "previa.mp4") if p.exists()), None)
    if not video or not video.exists():
        sair("Não achei o vídeo cortado (final.mp4 ou previa.mp4 na decupagem). Passe --video.")
    info = info_video(video)
    r = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", video])
    FPS_TXT = r.stdout.strip().split(",")[0] or "30/1"
    marca = achar_marca(pasta_video)
    print(f"Marca: {marca if marca else 'nenhuma'}")
    M = ler_mapa(pasta, dec, marca, pasta_video)
    estilo = M.estilo
    motor = bool(M.divididas or M.camadas)

    pal = dec / "palavras-corte.json"
    srt = dec / "legenda.srt"
    if a.sem_legenda:
        leg = []
    elif pal.exists():
        leg = L.de_palavras(pal, estilo, M.destaques, M.correcoes, info["dur"])
    elif srt.exists():
        leg = L.de_srt(srt, estilo, M.destaques, M.correcoes)
    else:
        sair(f"Falta a legenda: {pal.name} ou {srt.name} na decupagem. Rode a /decupar antes.")
    leg = L.posicionar(leg, M.faixas, estilo)

    atencao = []
    for arq, txt in zip((estilo["fonte"], estilo["fonte_destaque"]), textos(M.ins, leg, estilo)):
        if arq:
            falta = faltam_glifos(arq, txt)
            if falta:
                atencao.append(f"a fonte {Path(arq).name} não tem {' '.join(falta)}: essas letras sairiam em outra "
                               "fonte. Troque a fonte ou o texto.")
    if not estilo["fonte"]:
        print("Sem arquivo de fonte no estilo: usando a fonte do sistema (Helvetica no Mac, Segoe no Windows).")
    for av in conferir(M, info["dur"]):
        print("Aviso:", av)
    enc = M.ancoras.encostadas
    if enc:
        print(f"{len(enc)} borda(s) a menos de 3 quadros de uma emenda foram para a emenda (contrato, seção 2): "
              + ", ".join(f"{onde.replace('insercoes.json, ', '')} {fmt_tempo(t)}→{fmt_tempo(t2)}" for onde, t, t2 in enc[:6])
              + (" …" if len(enc) > 6 else ""))

    render = pasta / ".render"
    nomes, medidas = desenhar(render, estilo, leg, M.ins, M.camadas)
    VAZIO = nomes[0]
    nl = nomes[1:1 + len(leg)]
    k = 1 + len(leg)
    pares = []
    for d in M.ins:
        for t0, t1, e in estados(d):
            pares.append(((d, e), nomes[k], t0, t1))
            k += 1
    nomes_cam = {c["id"]: nomes[k + j] for j, c in enumerate([c for c in M.camadas if c["tipo"] in ("faixa", "html")])}
    for (d, e), nome, *_ in pares:
        m = medidas.get(nome)
        if m and m.get("transborda"):
            print(f"Aviso: o cartão {d['n']} ({d['tipo']}) não coube na área: encurte o texto ou tire um item.")
    celulas = [(f"{d['n']} · {fmt_tempo(d['de'])} · {d['tipo']}" + (f" ({e})" if d["tipo"] in ("lista", "etapas", "comparacao") else ""), n)
               for (d, e), n, *_ in pares]
    celulas += [(f"{c['id']} · {fmt_tempo(c['de'])} · {c['tipo']}", nomes_cam[c["id"]]) for c in M.camadas if c["id"] in nomes_cam]
    if celulas:
        folha_cartoes(pasta, render, celulas)
    (pasta / "legenda-curta.srt").write_text("\n".join(
        f"{i + 1}\n{srt_tempo(x[0])} --> {srt_tempo(x[1])}\n{' '.join(w for w, _ in x[2])}\n" for i, x in enumerate(leg)),
        encoding="utf-8")
    geo = geometria(M, leg, nl, pares, medidas, nomes_cam, info["dur"])
    (pasta / ".dados").mkdir(exist_ok=True)
    (pasta / ".dados" / "geometria.json").write_text(json.dumps(geo, ensure_ascii=False, indent=1), encoding="utf-8")
    atencao += zona(M, geo, leg)
    faixa_pal = f"1 a {estilo['palavras_max']}" if estilo["palavras_max"] > 1 else "1"
    print(f"Vídeo: {fmt_tempo(info['dur'])} · {info['w']}×{info['h']} · {len(M.ins)} inserções · {len(M.camadas)} camadas · "
          f"{len(M.divididas)} divididas · {len(leg)} legendas ({faixa_pal} palavra{'s' if estilo['palavras_max'] > 1 else ''}"
          f", de {'palavras-corte.json' if pal.exists() and not a.sem_legenda else 'legenda.srt'})")
    for x in atencao:
        print("ATENÇÃO:", x)
    if a.cartoes:
        if celulas:
            print(f"Cartões e peças para conferir: {pasta / 'cartoes.png'}")
        sys.exit(2 if atencao else 0)
    if atencao:
        print("O vídeo não foi gravado: corrija o que está em ATENÇÃO no insercoes.json e rode de novo.")
        sys.exit(2)

    saida = Path(a.saida).expanduser().resolve() if a.saida else pasta / f"{video.stem}-insercoes.mp4"
    saida.parent.mkdir(parents=True, exist_ok=True)
    t_render = time.time()
    if not motor:
        faixas = []
        if pares:
            faixas.append(trilha(render, "insercoes.ffconcat", [(t0, t1, n) for _, n, t0, t1 in pares], info["dur"], info["fps"]))
        if leg:
            faixas.append(trilha(render, "legenda.ffconcat", [(x[0], x[1], n) for x, n in zip(leg, nl)], info["dur"], info["fps"]))
        print(f"Montando o vídeo (no Mac com chip M, uns 20 s por minuto de vídeo)...", flush=True)
        divididas = [(d["de"], d["ate"], int(d.get("recorte_y", info["h"] // 6))) for d in M.ins if d["tipo"] == "dividida"]
        compor_ffmpeg(str(video), info, [str(f) for f in faixas], str(saida), divididas)
    else:
        import compor
        n_q = contar_quadros(video) or int(round(info["dur"] * info["fps"]))
        masc = mascaras(video, pasta, M, info["fps"], n_q, a.mascara)
        t_render = time.time()
        print(f"Montando o vídeo com camadas (no Mac com chip M, mais ou menos o tempo do vídeo)...", flush=True)
        P = plano_compor(M, video, info, n_q, saida, pasta, render, pares, leg, nl, nomes_cam, masc, a.trabalhadores)
        compor.compor(P)
    t_render = time.time() - t_render
    dur = info_video(saida)["dur"]
    ok = abs(dur - info["dur"]) < 0.2
    fs = quadros(str(saida), pasta, M.ins, leg, dur, M.camadas, M.divididas)
    print(f"{saida}: {fmt_tempo(dur)}" + ("" if ok else f" · ATENÇÃO: o vídeo de entrada tem {fmt_tempo(info['dur'])}"))
    print(f"Quadros para conferir ({len(fs)}): {pasta / 'quadros'} · todos juntos em {pasta / 'quadros' / 'folha.jpg'}")
    print(f"Pronto em {fmt_num(time.time() - t_ini)} s (montagem: {fmt_num(t_render)} s, "
          f"{fmt_num(info['dur'] / max(t_render, 1e-6), 2)}× o tempo real).")


if __name__ == "__main__":
    main()
