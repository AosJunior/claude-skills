# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = [
#   "numpy>=1.26",
#   "pillow>=10.1",
#   "mlx-whisper>=0.4; sys_platform == 'darwin' and platform_machine == 'arm64'",
#   "faster-whisper>=1.1; sys_platform != 'darwin' or platform_machine != 'arm64'",
# ]
# ///
"""/criticar: mede o vídeo editado antes da entrega e grava a crítica em <pasta do vídeo>/critica/.

Uso:  uv run "<skill>/scripts/criticar.py" "<pasta do vídeo>"
         [--video <arquivo>]     outro vídeo em vez do achado em entrega/ (ou som/, insercoes/, decupagem/)
         [--sem-evento 8]        segundos sem evento visual que reprovam
         [--refazer-fala]        transcreve de novo mesmo com cache
      uv run "<skill>/scripts/criticar.py" "<pasta do vídeo>" --ampliar 01:58,90 [x y w h]
         grava critica/ampliar-<tempo>.jpg: o quadro (ou a caixa) em resolução cheia, ampliado, para ler
         letra por letra

Lê o que existir: decupagem/palavras-corte.json, insercoes/.dados/geometria.json, insercoes/insercoes.json,
a legenda-curta.srt (entrega/ ou insercoes/), som/som.json e marca/ (achada subindo as pastas).
Grava critica/relatorio.md, critica/medidas.json, critica/folha-NN.jpg (1 quadro por segundo),
critica/folha-cortes-NN.jpg (cada corte com os quadros em volta), critica/folha-referencia.jpg
(com vídeos em marca/referencias/) e critica/letras/ (cada palavra estilizada ampliada).
Nada fora de critica/ é alterado.
"""
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (IMAGEM, VIDEO, achar_marca, checar_ffmpeg, fmt_num, fmt_tempo, gravar_json,  # noqa: E402
                   ler_json, ler_srt, relativo, rodar, sair, segundos, sondar, token, utf8)

ZONA_PADRAO = [260, 1600]
SEM_EVENTO = 8.0
CONCENTRACAO_MAX = 0.70
TEXTO = {"legenda", "faixa", "html", "cartao", "titulo", "frase", "lista", "numero", "comparacao", "etapas"}


# ---------------------------------------------------------------- achar arquivos

def mais_novo(arqs):
    arqs = [a for a in arqs if a.is_file() and not a.name.startswith(".")]
    return max(arqs, key=lambda a: a.stat().st_mtime) if arqs else None


def achar_video(pasta, som):
    v = mais_novo([p for p in (pasta / "entrega").glob("*") if p.suffix.lower() in VIDEO])
    if v:
        return v
    if som:
        p = relativo(pasta / "som", som.get("saida") or "video-com-som.mp4")
        if p.is_file():
            return p
    v = mais_novo(list((pasta / "insercoes").glob("*-insercoes.mp4")))
    if v:
        return v
    for nome in ("final.mp4", "previa.mp4"):
        if (pasta / "decupagem" / nome).is_file():
            return pasta / "decupagem" / nome
    return None


def achar_voz(pasta, som, marca, video):
    """O vídeo antes da trilha (mesmo tempo do final), para medir as emendas sem a música por baixo."""
    cands = []
    if som and som.get("video"):
        cands.append(relativo(pasta / "som", som["video"], marca))
    cands.append(pasta / "decupagem" / "final.mp4")
    for c in cands:
        if c.is_file() and c.resolve() != Path(video).resolve():
            return c, True
    return Path(video), False


# ---------------------------------------------------------------- medidas sobre a geometria

def zona_de(caixa, quadro):
    W, H = quadro
    x, y, w, h = caixa
    cx, cy = x + w / 2, y + h / 2
    if cy < H / 3:
        return "alto"
    if cy > 2 * H / 3:
        return "baixo"
    return "lados" if (cx < W / 3 or cx > 2 * W / 3) else "meio"


def eh_texto(i):
    return i.get("tipo") in TEXTO or bool(i.get("texto"))


def medir_zona(itens, zona):
    """Texto fora da zona segura reprova; imagem fora dela, ou peça com "aceito" (decisão escrita no insercoes.json),
    fica em atenção."""
    fora, avisos = [], []
    for i in itens:
        c = i.get("caixa")
        if not c or i.get("tipo") == "dividida" or i.get("lugar") == "topo":
            continue
        topo, pe = c[1], c[1] + c[3]
        if topo >= zona[0] - 0.5 and pe <= zona[1] + 0.5:
            continue
        r = {"id": i.get("id"), "tipo": i.get("tipo"), "texto": i.get("texto", ""), "de": i.get("de"),
             "ate": i.get("ate"), "caixa": c, "topo": topo, "pe": pe, "destaque": bool(i.get("destaque")),
             "aceito": i.get("aceito")}
        (fora if eh_texto(i) and not i.get("aceito") else avisos).append(r)
    return fora, avisos


def medir_distribuicao(itens, quadro):
    pecas = []
    for i in itens:
        if i.get("tipo") == "dividida":
            pecas.append({"id": i.get("id"), "zona": "alto", "de": i.get("de")})
        elif i.get("tipo") != "legenda" and i.get("lugar") != "topo" and i.get("caixa"):
            pecas.append({"id": i.get("id"), "zona": zona_de(i["caixa"], quadro), "de": i.get("de")})
    hist = {z: sum(p["zona"] == z for p in pecas) for z in ("alto", "meio", "baixo", "lados")}
    return pecas, hist


def eventos_visuais(cortes_t, itens):
    ev = set(round(t, 2) for t in cortes_t)
    for i in itens:
        if i.get("tipo") == "legenda" and not i.get("destaque"):
            continue
        for k in ("de", "ate"):
            if isinstance(i.get(k), (int, float)):
                ev.add(round(float(i[k]), 2))
        for p in i.get("pessoa") or []:
            if isinstance(p.get("de"), (int, float)):
                ev.add(round(float(p["de"]), 2))
    return sorted(ev)


def medir_srt(leg, srt, dur, fps):
    """Casa cada legenda gravada (geometria) com a da SRT pela 1ª palavra e o tempo mais perto."""
    usados, pares = set(), []
    S = [dict(s, tok=[token(x) for x in s["texto"].split() if token(x)]) for s in srt]
    for g in sorted(leg, key=lambda i: i["de"]):
        tg = [token(x) for x in str(g.get("texto", "")).split() if token(x)]
        if not tg:
            continue
        melhor = None
        for j, s in enumerate(S):
            if j in usados or not s["tok"] or s["tok"][0] != tg[0] or abs(s["de"] - g["de"]) > 1.0:
                continue
            if melhor is None or abs(s["de"] - g["de"]) < abs(S[melhor]["de"] - g["de"]):
                melhor = j
        if melhor is not None:
            usados.add(melhor)
            pares.append({"texto": g["texto"], "gravada": round(g["de"], 3), "srt": round(S[melhor]["de"], 3),
                          "atraso": round(S[melhor]["de"] - g["de"], 3)})
    import numpy as np
    at = np.array([p["atraso"] for p in pares]) if pares else np.array([0.0])
    quadro = 1 / fps
    alem = [s for s in srt if s["ate"] > dur + 0.02]
    r = {"gravadas": len(leg), "srt": len(srt), "pares": len(pares),
         "atraso_mediano": round(float(np.median(at)), 3),
         "atraso_p90": round(float(np.percentile(np.abs(at), 90)), 3),
         "atraso_max": round(float(at[np.argmax(np.abs(at))]), 3),
         "acima_de_1_quadro": int((np.abs(at) > quadro + 0.005).sum()),
         "srt_sem_par": [{"de": round(s["de"], 3), "texto": s["texto"]} for j, s in enumerate(srt) if j not in usados],
         "depois_do_fim": [{"de": round(s["de"], 3), "ate": round(s["ate"], 3), "texto": s["texto"]} for s in alem],
         "piores": sorted(pares, key=lambda p: -abs(p["atraso"]))[:8]}
    frac = r["acima_de_1_quadro"] / max(1, len(pares))
    r["reprova"] = []
    if abs(r["atraso_mediano"]) > quadro:
        lado = "atrasada" if r["atraso_mediano"] > 0 else "adiantada"
        r["reprova"].append(f"a SRT está {lado} {fmt_num(abs(r['atraso_mediano']), 2)} s (mediana) em relação à "
                            "legenda gravada")
    if frac > 0.2:
        r["reprova"].append(f"{r['acima_de_1_quadro']} de {len(pares)} legendas ({round(100 * frac)} %) diferem "
                            f"mais de 1 quadro; a pior, {fmt_num(r['atraso_max'], 2)} s")
    if alem:
        r["reprova"].append(f"{len(alem)} legenda(s) da SRT terminam depois do fim do vídeo "
                            f"(a última vai até {fmt_tempo(alem[-1]['ate'])}; o vídeo acaba em {fmt_tempo(dur)})")
    if len(r["srt_sem_par"]) > 0.05 * max(1, len(srt)):
        r["reprova"].append(f"{len(r['srt_sem_par'])} legendas da SRT não aparecem gravadas no vídeo")
    return r


def volume(video):
    r = rodar(["ffmpeg", "-hide_banner", "-nostdin", "-nostats", "-i", video, "-map", "0:a:0", "-af",
               "ebur128=peak=true:framelog=quiet", "-f", "null", "-"])
    resumo = r.stderr[r.stderr.rfind("Summary:"):]

    def pega(rot):
        m = re.search(rot + r":\s*(-?[0-9.]+|-inf)", resumo)
        return float(m.group(1)) if m and m.group(1) != "-inf" else None
    return {"lufs": pega(r"\bI"), "pico_real": pega(r"True peak:\s*Peak")}


# ---------------------------------------------------------------- correções (passo c da skill)

def borda_perto(t, itens, janela):
    """Itens da geometria com `de`/`ate` (ou troca de pessoa na dividida) perto de t."""
    out = []
    for i in itens:
        if i.get("tipo") == "legenda":
            continue
        for k in ("de", "ate"):
            v = i.get(k)
            if isinstance(v, (int, float)) and abs(v - t) <= janela:
                out.append(f"{i.get('id')}.{k} = {fmt_num(v, 3)}")
        for n, p in enumerate(i.get("pessoa") or []):
            v = p.get("de")
            if n and isinstance(v, (int, float)) and abs(v - t) <= janela:
                out.append(f"{i.get('id')}.pessoa[{n}].de = {fmt_num(v, 3)}")
    return out


def emenda_perto(t, emendas, janela):
    e = min(emendas, key=lambda e: abs(e["t"] - t), default=None)
    return e if e and abs(e["t"] - t) <= janela else None


def palavra_esperada(t, esp):
    w = min(esp, key=lambda w: abs(w["a"] - t), default=None)
    return w if w and abs(w["a"] - t) < 0.5 else None


# ---------------------------------------------------------------- relatório

def linha_item(nome, res, medida, onde=""):
    return f"| {nome} | **{res}** | {medida} | {onde} |"


def main():
    utf8()
    args = [a for a in sys.argv[1:]]
    if not args or args[0].startswith("--"):
        sair(__doc__)
    t0 = time.time()
    checar_ffmpeg()
    pasta = Path(args[0]).expanduser().resolve()
    if pasta.is_file():
        sair("Passe a pasta do vídeo (a que tem decupagem/, insercoes/, som/ e entrega/), não o arquivo. "
             "Para outro vídeo, use --video.")
    if not pasta.is_dir():
        sair(f"Não achei a pasta: {pasta}")

    def opcao(nome, padrao=None):
        if nome in args:
            i = args.index(nome)
            if i + 1 < len(args):
                return args[i + 1]
        return padrao

    critica = pasta / "critica"
    dados = critica / ".dados"
    dados.mkdir(parents=True, exist_ok=True)
    marca = achar_marca(pasta)
    som_p = pasta / "som" / "som.json"
    som = ler_json(som_p) if som_p.is_file() else None
    video = Path(opcao("--video")).expanduser() if opcao("--video") else achar_video(pasta, som)
    if not video or not video.is_file():
        sair("Não achei o vídeo editado (procurei em entrega/, som/, insercoes/ e decupagem/). "
             "Passe o arquivo com --video.")
    info = sondar(video)
    fps, dur = info["fps"], info["duracao"]

    import imagem

    if "--ampliar" in args:
        i = args.index("--ampliar")
        t = segundos(args[i + 1])
        caixa = [float(x) for x in args[i + 2:i + 6]] if len(args) >= i + 6 else None
        saida = critica / f"ampliar-{fmt_tempo(t).replace(':', '-').replace(',', '-')}.jpg"
        if not imagem.ampliar(video, t, caixa, saida):
            sair("Não consegui tirar esse quadro.")
        print(f"Ampliado: {saida}")
        return

    limite = float(opcao("--sem-evento", SEM_EVENTO))
    print(f"Marca: {marca or 'nenhuma'}")
    print(f"Vídeo: {video} · {fmt_num(dur, 2)} s · {info['largura']}×{info['altura']} · "
          f"{fmt_num(fps, 2)} quadros/s", flush=True)

    # entradas
    pc_p = pasta / "decupagem" / "palavras-corte.json"
    geo_p = pasta / "insercoes" / ".dados" / "geometria.json"
    ins_p = pasta / "insercoes" / "insercoes.json"
    srt_p = next((p for p in [mais_novo(list((pasta / "entrega").glob("*.srt"))),
                              pasta / "insercoes" / "legenda-curta.srt"] if p and p.is_file()), None)
    pc = ler_json(pc_p) if pc_p.is_file() else None
    geo = ler_json(geo_p) if geo_p.is_file() else None
    ins = ler_json(ins_p) if ins_p.is_file() else None
    itens = (geo or {}).get("itens", [])
    quadro = (geo or {}).get("quadro") or [info["largura"], info["altura"]]
    zona = (geo or {}).get("zona_segura") or ((ins or {}).get("estilo") or {}).get("zona_segura") or ZONA_PADRAO
    refs = sorted(p for p in (marca / "referencias").glob("*") if p.suffix.lower() in VIDEO | IMAGEM) \
        if marca and (marca / "referencias").is_dir() else []
    faltas = []
    if not pc:
        faltas.append("decupagem/palavras-corte.json (sem ele: emendas pelos cortes da imagem, sem texto esperado)")
    if not geo:
        faltas.append("insercoes/.dados/geometria.json (sem ele: zona segura, posições e SRT × gravada ficam de fora)")
    if not srt_p:
        faltas.append("legenda-curta.srt (sem ela: SRT × gravada fica de fora)")
    if pc and not pc.get("medido"):
        faltas.append("bordas medidas no palavras-corte.json (o cortar.py grava depois do render; sem elas, a emenda "
                      "fica no tempo previsto)")
    for f in faltas:
        print(f"Aviso: falta {f}")

    M = {"video": str(video), "duracao": dur, "fps": fps, "quadro": [info["largura"], info["altura"]],
         "marca": str(marca) if marca else None, "zona_segura": zona, "faltas": faltas, "itens": []}
    itens_rel = []          # (nome, resultado, medida, onde, correcao, detalhe)

    def item(chave, nome, res, medida, onde="", correcao="", detalhe=None):
        itens_rel.append((nome, res, medida, onde, correcao))
        M["itens"].append({"item": chave, "nome": nome, "resultado": res, "medida": medida, "onde": onde,
                           "correcao": correcao, "detalhe": detalhe})

    # ------------------------------------------------ imagem
    print("Lendo o vídeo quadro a quadro (uns 10 a 30 s por minuto de vídeo)...", flush=True)
    q = imagem.ler_quadros(video, info)
    cortes, soltos = imagem.cortes_e_soltos(q, fps)
    cortes_t = [c / fps for c in cortes]
    folhas, cobertura = imagem.folhas(q, info, cortes, soltos, critica, zona)
    M["cortes"] = [round(t, 3) for t in cortes_t]
    M["cobertura"] = cobertura

    import fala
    esp, emendas = fala.esperado(pc) if pc else ([], [])

    if soltos:
        onde = ", ".join(fmt_tempo(s["t"]) for s in soltos)
        cor = []
        for s in soltos:
            b = borda_perto(s["t"], itens, 2.5 / fps)
            e = emenda_perto(s["t"], emendas, 0.2)
            alvo = []
            if b:
                alvo.append("/inserir · insercoes.json · " + "; ".join(b) + " (a borda cai a 1–2 quadros do corte: "
                            "use \"<frase do plano seguinte>:emenda\" para pôr as duas no mesmo quadro)")
            if e:
                alvo.append(f"/decupar · cortes.json · ajustes \"T{e['trecho']}.ate\" / \"T{e['trecho'] + 1}.de\" "
                            f"(emenda em {fmt_tempo(e['t'])})")
            cor.append(f"{fmt_tempo(s['t'])}: " + (" ou ".join(alvo) if alvo else "conferir na folha-cortes qual "
                                                   "camada ou trecho troca 1 quadro antes do outro"))
        item("quadros_soltos", "Quadros soltos", "reprova",
             f"{len(soltos)} pedaço(s) de {', '.join(str(s['quadros']) for s in soltos)} quadro(s) entre dois cortes",
             onde, " · ".join(cor), soltos)
    else:
        item("quadros_soltos", "Quadros soltos", "passa", f"{len(cortes)} cortes, nenhum a menos de 3 quadros do outro")

    # ------------------------------------------------ fala
    print("Transcrevendo o vídeo final com tempo por palavra (uns 10 s por minuto no Mac com chip M; "
          "1 a 2 min por minuto no Windows)...", flush=True)
    final_pal, motor_nome, do_cache = fala.transcrever(video, dados, "--refazer-fala" in args)
    gravar_json(critica / "fala-final.json", {"motor": motor_nome, "palavras": final_pal})
    emendas_aprox = False
    if not emendas:
        # sem palavras-corte: cada corte seco que não é borda de camada vira emenda provável
        emendas_aprox = True
        for t in cortes_t:
            if borda_perto(t, itens, 0.1):
                continue
            ant = [w for w in final_pal if w["b"] <= t + 0.05]
            dep = [w for w in final_pal if w["a"] >= t - 0.05]
            if ant and dep:
                emendas.append({"t": t, "b": ant[-1]["b"], "a": dep[0]["a"], "trecho": None,
                                "antes": ant[-1]["w"], "depois": dep[0]["w"], "exata": False})

    # ------------------------------------------------ emendas no som
    voz, so_voz = achar_voz(pasta, som, marca, video)
    db = fala.ler_som(voz, dados) if info["tem_audio"] else None
    db_final = fala.ler_som(video, dados) if (info["tem_audio"] and so_voz) else db
    med, limiar = fala.medir_emendas(db, db_final, emendas, so_voz)
    if emendas_aprox:        # sem a borda exata, "dentro do som" pode ser só a imagem trocando antes do som
        for m in med:
            m["avisos"] += [p for p in m["problemas"] if "dentro do som" in p or "respiro" in p]
            m["problemas"] = [p for p in m["problemas"] if not ("dentro do som" in p or "respiro" in p)]
    probl = [m for m in med if m["problemas"]]
    fonte_som = f"som de {Path(voz).name}" + ("" if so_voz else " (já com trilha: limiar mais alto)")
    tipo_em = "emendas pelos cortes da imagem (aproximado)" if emendas_aprox else "emendas do palavras-corte.json"
    if not med:
        item("emendas", "Emendas", "pulado", "sem emendas para medir" + ("" if info["tem_audio"] else " (vídeo sem som)"))
    elif probl:
        cor = []
        for m in probl[:8]:
            n = m.get("trecho")
            alvo = f"ajustes \"T{n}.ate\" / \"T{n + 1}.de\"" if n else "o trecho dessa emenda"
            dica = []
            if any("respiro" in p or "dentro do som" in p for p in m["problemas"]):
                dica.append("abrir uns 0,05 s de respiro")
            if any("longa" in p for p in m["problemas"]):
                dica.append("fechar a pausa")
            if any("volume" in p for p in m["problemas"]):
                dica.append("tomada com volume diferente: trocar a tomada ou igualar o ganho do trecho")
            cor.append(f"{fmt_tempo(m['t'])}: /decupar · cortes.json · {alvo} ({', '.join(dica)})")
        item("emendas", "Emendas", "reprova",
             f"{len(probl)} de {len(med)} com problema · {tipo_em} · {fonte_som} · silêncio < {fmt_num(limiar)} dB",
             ", ".join(f"{fmt_tempo(m['t'])} {'; '.join(m['problemas'])}" for m in probl[:8]), " · ".join(cor),
             med)
    else:
        item("emendas", "Emendas", "passa", f"{len(med)} emendas sem salto, pausa fora da faixa nem corte no som · "
                                            f"{tipo_em} · {fonte_som}", "", "", med)
    avis = [m for m in med if m["avisos"]]
    if avis:
        item("emendas_ouvir", "Emendas para ouvir", "atenção",
             f"{len(avis)} emenda(s) no meio da frase sem nenhum silêncio: confira se a palavra não perdeu o começo ou o fim",
             ", ".join(f"{fmt_tempo(m['t'])} «{m['antes']} | {m['depois']}»" for m in avis[:8]))
    fundo = [m for m in med if abs(m.get("salto_fundo", 0)) > fala.SALTO_FUNDO]
    if fundo and not som:
        item("fundo", "Ruído de fundo nas emendas", "atenção",
             f"{len(fundo)} emenda(s) em que o fundo muda mais de {fmt_num(fala.SALTO_FUNDO, 0)} dB e não há trilha "
             "para cobrir", ", ".join(f"{fmt_tempo(m['t'])} ({fmt_num(m['salto_fundo'])} dB)" for m in fundo[:6]))

    # ------------------------------------------------ gagueira (depois das emendas: uma diferença de texto só
    # reprova quando a emenda dela também falha no som)
    achados, diffs = fala.gagueira(final_pal, esp, [] if emendas_aprox else emendas)
    ruins = [m["t"] for m in med if any("dentro do som" in p or "respiro" in p for p in m["problemas"] + m["avisos"])]
    reprova_dif = [d for d in diffs if d["perto_emenda"] and d["tipo"] != "trocada"
                   and any(abs(d["t"] - t) <= fala.PERTO_EMENDA for t in ruins)]
    atencao_dif = [d for d in diffs if d not in reprova_dif]
    if achados or reprova_dif:
        onde = ", ".join(f"{fmt_tempo(a['t'])} «{a['texto']}»" for a in (achados + reprova_dif)[:8])
        cor = []
        for a in achados + reprova_dif:
            w = palavra_esperada(a["t"], esp)
            if w and w.get("frase"):
                cor.append(f"{fmt_tempo(a['t'])}: /decupar · cortes.json · o trecho que pega {w['frase']} começa "
                           f"ou termina na palavra certa (ex.: \"de\": \"{w['frase']}:{int(w.get('n', 1)) + 1}\")")
            else:
                cor.append(f"{fmt_tempo(a['t'])}: /decupar · cortes.json · tirar a repetição: o trecho começa depois "
                           "dela (âncora frase:palavra da transcricao.txt)")
        medida = f"{len(achados)} repetição(ões) no final" + (f", {len(reprova_dif)} palavra(s) perdida(s) em emenda "
                                                              "que corta dentro do som" if reprova_dif else "")
        item("gagueira", "Gagueira e repetição", "reprova", medida, onde, " · ".join(cor[:6]),
             {"achados": achados, "diferencas": diffs})
    else:
        base = "comparado com o texto esperado" if esp else "sem texto esperado (falta palavras-corte.json)"
        item("gagueira", "Gagueira e repetição", "passa", f"{len(final_pal)} palavras, nenhuma repetição; {base}",
             "", "", {"diferencas": diffs})
    if atencao_dif:
        item("texto", "Texto × esperado", "atenção",
             f"{len(atencao_dif)} diferença(s) entre o final e o texto esperado; costuma ser o Whisper, mas ouça",
             ", ".join(f"{fmt_tempo(d['t'])} «{d['final'] or '—'}»≠«{d['esperado'] or '—'}»" for d in atencao_dif[:6]),
             "", atencao_dif)

    # ------------------------------------------------ geometria
    if geo:
        fora, avisos = medir_zona(itens, zona)
        if fora:
            blocos = []
            for f in fora:
                if blocos and blocos[-1]["tipo"] == f["tipo"] == "legenda" and blocos[-1]["destaque"] == f["destaque"] \
                        and abs(blocos[-1]["topo"] - f["topo"]) < 40 and f["de"] - blocos[-1]["ate"] < 1.0:
                    blocos[-1]["ate"] = f["ate"]
                    blocos[-1]["n"] += 1
                else:
                    blocos.append(dict(f, n=1))
            cor = []
            for b in blocos[:6]:
                campo = ("estilo.destaque_y" if b["destaque"] else "estilo.legenda_y ou a faixa de `legenda`") \
                    if b["tipo"] == "legenda" else f"camada {b['id']}: `y`"
                cor.append(f"{fmt_tempo(b['de'])}: /inserir · insercoes.json · {campo} (caixa de {int(b['topo'])} a "
                           f"{int(b['pe'])} px; precisa caber em {zona[0]}–{zona[1]})")
            item("zona_segura", "Zona segura", "reprova",
                 f"{len(fora)} texto(s) fora de {zona[0]}–{zona[1]} px",
                 ", ".join(f"{fmt_tempo(b['de'])} {b['id'] if b['tipo'] != 'legenda' else '«' + b['texto'] + '»'}"
                           f"{' (+' + str(b['n'] - 1) + ')' if b['n'] > 1 else ''} topo {int(b['topo'])}/pé {int(b['pe'])}"
                           for b in blocos[:8]), " · ".join(cor), fora)
        else:
            item("zona_segura", "Zona segura", "passa", f"todo texto dentro de {zona[0]}–{zona[1]} px")
        if avisos:
            item("zona_imagens", "Peças perto da borda", "atenção",
                 f"{len(avisos)} peça(s) passam de {zona[0]}–{zona[1]} px (imagem sem texto ou com \"aceito\": só conferir)",
                 ", ".join(f"{fmt_tempo(a['de'])} {a['id']} ({int(a['topo'])}–{int(a['pe'])})"
                           + (f" aceito: {a['aceito']}" if a.get("aceito") else "") for a in avisos[:6]))
        pecas, hist = medir_distribuicao(itens, quadro)
        if len(pecas) >= 3:
            z, n = max(hist.items(), key=lambda kv: kv[1])
            frac = n / len(pecas)
            hist_txt = ", ".join(f"{k} {v}" for k, v in hist.items())
            if frac > CONCENTRACAO_MAX:
                vazias = [k for k, v in hist.items() if v == 0] or [k for k in hist if k != z]
                item("posicoes", "Variedade de posição", "reprova",
                     f"{round(100 * frac)} % das {len(pecas)} peças no {z} ({hist_txt})", "",
                     f"/inserir · insercoes.json · camadas: leve {n - int(CONCENTRACAO_MAX * len(pecas))} ou mais peças "
                     f"do {z} para {' / '.join(vazias)} (`x`, `y`, `lugar`)", {"pecas": pecas, "histograma": hist})
            else:
                item("posicoes", "Variedade de posição", "passa",
                     f"maior zona {z} com {round(100 * frac)} % das {len(pecas)} peças ({hist_txt})", "", "",
                     {"pecas": pecas, "histograma": hist})
        else:
            item("posicoes", "Variedade de posição", "pulado", f"só {len(pecas)} peça(s) de primeiro plano")
    else:
        for chave, nome in (("zona_segura", "Zona segura"), ("posicoes", "Variedade de posição")):
            item(chave, nome, "pulado", "falta insercoes/.dados/geometria.json")

    ev = eventos_visuais(cortes_t, itens)
    marcos = [0.0] + [t for t in ev if 0 < t < dur] + [dur]
    buracos = [(a, b) for a, b in zip(marcos, marcos[1:]) if b - a > limite]
    if buracos:
        item("sem_evento", "Tempo sem evento visual", "reprova",
             f"{len(buracos)} trecho(s) acima de {fmt_num(limite, 0)} s; o maior, {fmt_num(max(b - a for a, b in buracos))} s",
             ", ".join(f"{fmt_tempo(a)}–{fmt_tempo(b)}" for a, b in buracos),
             "/inserir · insercoes.json: uma camada ou destaque no meio do trecho, ou /decupar · cortes.json: "
             "outro nível de `zoom` num trecho do meio", [{"de": a, "ate": b} for a, b in buracos])
    else:
        maior = max(b - a for a, b in zip(marcos, marcos[1:]))
        item("sem_evento", "Tempo sem evento visual", "passa",
             f"maior trecho parado {fmt_num(maior)} s (limite {fmt_num(limite, 0)} s)"
             + ("" if geo else "; só cortes da imagem, sem a geometria"))

    leg = [i for i in itens if i.get("tipo") == "legenda"]
    if srt_p and leg:
        r = medir_srt(leg, ler_srt(srt_p), dur, fps)
        M["srt"] = r
        if r["reprova"]:
            item("srt", "SRT × legenda gravada", "reprova", "; ".join(r["reprova"]),
                 ", ".join(f"{fmt_tempo(p['gravada'])} «{p['texto']}» {'+' if p['atraso'] > 0 else ''}"
                           f"{fmt_num(p['atraso'], 2)} s" for p in r["piores"][:4]),
                 "/inserir · a legenda-curta.srt e a gravada saem da mesma lista (contrato 4.2): refazer a SRT pelo "
                 "inserir.py, com a última legenda terminando no fim do vídeo", r)
        else:
            item("srt", "SRT × legenda gravada", "passa",
                 f"{r['pares']} pares, atraso mediano {fmt_num(r['atraso_mediano'], 3)} s, nada depois do fim")
    elif srt_p:
        al = [s for s in ler_srt(srt_p) if s["ate"] > dur + 0.02]
        if al:
            item("srt", "SRT × legenda gravada", "reprova",
                 f"{len(al)} legenda(s) da SRT terminam depois do fim do vídeo (sem geometria para comparar o resto)",
                 fmt_tempo(al[-1]["ate"]), "/inserir · a última legenda termina no fim do vídeo")
        else:
            item("srt", "SRT × legenda gravada", "pulado", "falta a geometria com as legendas gravadas")
    else:
        item("srt", "SRT × legenda gravada", "pulado", "não achei legenda-curta.srt")

    # ------------------------------------------------ volume
    if info["tem_audio"]:
        v = volume(video)
        M["volume"] = v
        ok = v["lufs"] is not None and abs(v["lufs"] + 14) <= 1 and v["pico_real"] is not None and v["pico_real"] <= -1
        medida = f"{fmt_num(v['lufs'] or -99)} LUFS, pico real {fmt_num(v['pico_real'] or -99)} dBTP (alvo -14 ±1, pico ≤ -1)"
        item("volume", "Volume", "passa" if ok else "reprova", medida, "",
             "" if ok else "/sonorizar · som.json: mixar de novo (o sonorizar.py normaliza em -14 LUFS e limita o pico)")
    else:
        item("volume", "Volume", "reprova", "o vídeo não tem som", "", "/sonorizar")

    # ------------------------------------------------ folhas e letras
    ok_folha = cobertura["completa"]
    item("folha", "Folha de quadros", "passa" if ok_folha else "reprova",
         f"{cobertura['segundos']} quadros (1 por segundo) para {fmt_num(dur)} s · {cobertura['cortes_na_folha']} de "
         f"{cobertura['cortes']} cortes com os 5 quadros em volta", ", ".join(folhas[:3]) + ("…" if len(folhas) > 3 else ""))
    if refs:
        n = imagem.folha_referencia(video, info, refs, critica / "folha-referencia.jpg")
        M["referencias"] = [str(r) for r in refs]
        folhas.append("folha-referencia.jpg")
        print(f"Referência × resultado: {n} referência(s)")
    letras = []
    pasta_letras = critica / "letras"
    if pasta_letras.is_dir():
        for velho in pasta_letras.glob("*.jpg"):
            velho.unlink()
    vistos = set()
    for i in itens:
        if not i.get("caixa") or not (i.get("destaque") or (eh_texto(i) and i.get("tipo") != "legenda")):
            continue
        chave = token(i.get("texto") or i.get("id"))
        rotulo = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", str(i.get("texto") or i.get("id")).lower())
                        .encode("ascii", "ignore").decode()).strip("-")
        if chave in vistos or len(letras) >= 40:
            continue
        vistos.add(chave)
        pasta_letras.mkdir(exist_ok=True)
        t = float(i["de"]) + min(0.6, (float(i["ate"]) - float(i["de"])) / 2)   # depois da entrada (pop, fade)
        nome = f"{fmt_tempo(t).replace(':', '-').replace(',', '-')}-{rotulo[:28] or 'x'}.jpg"
        if imagem.ampliar(video, t, i["caixa"], pasta_letras / nome):
            letras.append({"arquivo": f"letras/{nome}", "t": round(t, 3), "texto": i.get("texto") or i.get("id"),
                           "id": i.get("id")})
    M["letras"] = letras
    M["folhas"] = folhas

    # ------------------------------------------------ gravar
    reprovados = [x for x in itens_rel if x[1] == "reprova"]
    L = [f"# Crítica: {video.name}", "",
         f"{time.strftime('%d/%m/%Y %H:%M')} · {fmt_num(dur, 2)} s · {info['largura']}×{info['altura']} · "
         f"{fmt_num(fps, 2)} quadros/s · marca: {marca or 'nenhuma'}", ""]
    if faltas:
        L += ["**Faltou:** " + "; ".join(faltas), ""]
    L += [f"**{len(reprovados)} reprovado(s)** de {sum(x[1] in ('passa', 'reprova') for x in itens_rel)} itens medidos. "
          "Gancho, trilha, legibilidade e fidelidade à referência ficam com o editor-chefe (critica.md).", "",
          "| Item | Resultado | Medida | Onde |", "|---|---|---|---|"]
    L += [linha_item(n, r, m, o) for n, r, m, o, _ in itens_rel]
    if reprovados:
        L += ["", "## Correções (skill · arquivo · campo)", ""]
        L += [f"- **{n}**: {c}" for n, r, m, o, c in reprovados if c]
    por_seg = ", ".join(f for f in folhas if re.match(r"folha-[0-9]", f))
    em_volta = ", ".join(f for f in folhas if f.startswith("folha-cortes"))
    L += ["", "## Folhas", "", f"- 1 quadro por segundo: {por_seg}", f"- quadros em volta de cada corte: {em_volta}"]
    if refs:
        L.append("- referência × resultado: folha-referencia.jpg")
    else:
        L.append("- referência × resultado: sem vídeos em marca/referencias/")
    if letras:
        L.append(f"- palavras estilizadas ampliadas: {len(letras)} em letras/")
    L += ["", f"Transcrição do final: fala-final.json ({motor_nome}{', do cache' if do_cache else ''}). "
              f"Medidas completas: medidas.json."]
    (critica / "relatorio.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    gravar_json(critica / "medidas.json", M)

    print(f"Crítica: {critica}")
    for n, r, m, o, _ in itens_rel:
        print(f"- {n}: {r.upper()} · {m}" + (f" · {o}" if o and r != "passa" else ""))
    print(f"Folhas: {len(folhas)} · letras ampliadas: {len(letras)}")
    print(f"Pronto em {fmt_num(time.time() - t0)} s. {len(reprovados)} reprovado(s).")


if __name__ == "__main__":
    main()
