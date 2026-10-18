# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""/decupar, etapas 2 a 5: aplica o cortes.json e entrega prévia, legenda, XML e guia do CapCut.

Uso:
  uv run "<skill>/scripts/cortar.py" "<pasta decupagem>" --resumo   só confere: durações e tempos finais
  uv run "<skill>/scripts/cortar.py" "<pasta decupagem>"            legenda.srt, premiere.xml, capcut.md, previa.mp4
  uv run "<skill>/scripts/cortar.py" "<pasta decupagem>" --final    o mesmo, com final.mp4 (1080 no lado curto)
Aceita também o caminho do vídeo no lugar da pasta. Todos gravam palavras-corte.json (tempo de cada palavra, as
bordas de cada trecho e as emendas no vídeo cortado, para a /inserir, a /sonorizar e a /criticar). Depois do
render, as bordas são as medidas no vídeo (quadros contados); no --resumo, as previstas, ou as medidas do último
render se o corte não mudou.

cortes.json (o Claude escreve; a ordem dos trechos é a ordem do vídeo final). Referência completa em
referencia.md, ao lado do SKILL.md:
  {"pausa_max": 0.22, "bordas": "som", "velocidade": 1.2,
   "zoom": {"ancora": [0.5, 0.4], "niveis": [1.0, 1.12, 1.2, 1.3], "alternar_na_pausa": true},
   "trechos": [{"de": "F2", "ate": "F6", "zoom": 1.12, "nota": "abertura"},
               {"de": "F7:3", "ate": "F7:fim", "nota": "tira o 'eu eu' do começo"},
               {"de": "F30", "ate": "02:41,00", "exato": true, "nota": "fica o sorriso no fim"}],
   "ajustes": {"T2.de": 0.04}}
  de/ate: frase ("F12", "F12:fim", "F12:3", "F12:palavra#2", "F12:fim+0.2"), "mm:ss,cc" ou segundos, do bruto.
  Fica a palavra cujo meio cai dentro do trecho; pausas maiores que pausa_max saem sozinhas.
  "exato": true usa de/ate como estão (sem ajustar às palavras nem tirar pausas).
Sem velocidade e sem zoom, o vídeo sai num render só (o caminho de sempre). Com eles, sai em pedaços
guardados em .dados/pedacos-*/ pelo conteúdo: uma correção refaz só os pedaços que mudaram.
"""
import bisect
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from array import array
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from operator import mul
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (CAP_PALAVRA, Ancoras, ErroContrato, achar_pasta, assinatura_video, checar_ffmpeg,  # noqa: E402
                   encoder, fmt_dur, fmt_num, fmt_tempo, gravar_json, hwaccel, ler_json, proxy_valido, rodar, sair,
                   tamanho, utf8)
from cor import filtro_da_pasta  # noqa: E402

PAD_IN, PAD_OUT = 0.10, 0.18      # folga antes e depois da fala (valores do pipeline de edição)
RESPIRO_OUT, RESPIRO_IN = 0.12, 0.06   # silêncio que fica depois e antes da fala numa pausa interna cortada
VAZIA_MIN = 0.15                  # som sem palavra (pedaço vazio do Whisper) a partir disso sai
LEG_CARACTERES, LEG_PALAVRAS = 24, 5
# "bordas": "som" — a borda do corte sai do volume medido, não do tempo da palavra do Whisper
PASSO = 0.01                      # s; uma medida de volume a cada 10 ms
VOZ_PERCENTIL, VOZ_DB = 12, 14    # é voz o que passa 14 dB acima do ruído de fundo (percentil 12 do volume)
FOLGA_A, FOLGA_B = 0.035, 0.07    # s; antes do primeiro som e depois do último
ANCORA_ZOOM = (0.5, 0.4)          # ponto do quadro que fica parado no zoom, se o cortes.json não disser
ZOOM_MIN = 0.4                    # s; pedaço mais curto que isso não troca o zoom (seria um piscar)
VERSAO_PEDACO = 1


# ---------------------------------------------------------------- leitura do cortes.json

def palavras_da_frase(f, pal):
    """Índices das palavras com texto da frase (a palavra n da frase é a n-ésima desta lista)."""
    return [i for i in range(f["i0"], f["i1"] + 1) if str(pal[i]["w"]).strip()]


def ler_tempo(v, anc, lado, onde):
    """(segundos do bruto, índice da palavra-limite ou None), pelas âncoras do contrato (contrato.py). A âncora de
    palavra ("F3:2", "F3:loja", "F3:fim") devolve também o índice: o Whisper sobrepõe palavras coladas, e o limite
    pelo índice não deixa a vizinha entrar pelo tempo. Frase inteira, relógio, segundos e deslocamento ficam só no
    tempo (como no v1)."""
    try:
        t, w = anc.resolver(v, fim=(lado == "ate"))
    except ErroContrato as e:
        sair(f"cortes.json, {onde}: {e}")
    return t, (w["i"] if w else None)


def numero(v, onde, minimo=None, maximo=None):
    try:
        x = float(v)
    except (TypeError, ValueError):
        sair(f"cortes.json, {onde}: esperava um número e veio {v!r}.")
    if (minimo is not None and x < minimo) or (maximo is not None and x > maximo):
        sair(f"cortes.json, {onde}: {fmt_num(x, 2)} está fora do intervalo de {minimo} a {maximo}.")
    return x


def ler_cortes(pasta, frases, pal, dur):
    """Lê o cortes.json. Campo que não aparece fica como no v1 (mesmo corte, mesmo render)."""
    p = pasta / "cortes.json"
    if not p.exists():
        sair(f"Falta o {p.name} na pasta {pasta}.")
    try:
        c = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sair(f"O cortes.json tem um erro de escrita na linha {e.lineno}, coluna {e.colno}: {e.msg}.")
    trechos = c.get("trechos") if isinstance(c, dict) else None
    if not trechos:
        sair("O cortes.json precisa de uma lista \"trechos\" com pelo menos um trecho.")
    avisos = []
    anc = Ancoras.do_bruto(list(frases.values()), pal, CAP_PALAVRA)
    zc = c.get("zoom") or {}
    if not isinstance(zc, dict):
        sair("cortes.json, zoom: use {\"ancora\": [0.5, 0.4], \"niveis\": [1.0, 1.12, 1.2, 1.3], \"alternar_na_pausa\": true}.")
    ancora = zc.get("ancora", ANCORA_ZOOM)
    if not (isinstance(ancora, (list, tuple)) and len(ancora) == 2):
        sair("cortes.json, zoom.ancora: use [x, y] em fração do quadro (0 a 1), por exemplo [0.5, 0.4].")
    zoom = {"ancora": tuple(numero(a, "zoom.ancora", 0, 1) for a in ancora),
            "niveis": sorted(numero(n, "zoom.niveis", 1, 3) for n in zc.get("niveis", [])),
            "alternar": bool(zc.get("alternar_na_pausa"))}
    out = []
    for k, t in enumerate(trechos, 1):
        if not isinstance(t, dict) or "de" not in t or "ate" not in t:
            sair(f"cortes.json, trecho {k}: cada trecho precisa de \"de\" e \"ate\".")
        de, i_de = ler_tempo(t["de"], anc, "de", f"trecho {k}")
        ate, i_ate = ler_tempo(t["ate"], anc, "ate", f"trecho {k}")
        de, ate = max(0.0, de), min(dur, ate)
        if ate <= de:
            sair(f"cortes.json, trecho {k}: o fim ({fmt_tempo(ate)}) vem antes do início ({fmt_tempo(de)}).")
        z = numero(t["zoom"], f"trecho {k}, zoom", 1, 3) if t.get("zoom") is not None else None
        out.append({"k": k, "de": de, "ate": ate, "exato": bool(t.get("exato")), "nota": str(t.get("nota") or ""),
                    "zoom": z, "i_de": i_de, "i_ate": i_ate})
    ajustes = {}
    for chave, val in (c.get("ajustes") or {}).items():
        m = re.fullmatch(r"T(\d+)\.(de|ate)", str(chave))
        if not m:
            sair(f"cortes.json, ajustes: não entendi {chave!r}. Use \"T5.de\" ou \"T5.ate\" (T5 = 5º trecho).")
        if not 1 <= int(m.group(1)) <= len(out):
            avisos.append(f"ajuste {chave} ignorado: não existe o trecho {m.group(1)}.")
            continue
        ajustes.setdefault(int(m.group(1)), {})[m.group(2)] = numero(val, f"ajustes, {chave}", -1, 1)
    bordas = str(c.get("bordas", "palavra"))
    if bordas not in ("palavra", "som"):
        sair("cortes.json, bordas: use \"som\" (borda pelo volume medido) ou \"palavra\" (pelo tempo do Whisper).")
    return {"pausa": float(c.get("pausa_max", 0.35)), "trechos": out, "zoom": zoom, "ajustes": ajustes,
            "velocidade": numero(c.get("velocidade", 1.0), "velocidade", 0.5, 2.0), "bordas": bordas,
            "avisos": avisos}


# ---------------------------------------------------------------- volume (bordas pelo som)

def volume(pasta, info):
    """Volume do som do bruto em dB a cada 10 ms. Cache em .dados/volume.json (mudou o bruto, mede de novo)."""
    dados = pasta / ".dados"
    if not Path(info["arquivo"]).exists():
        sair(f"O vídeo original não está mais em {info['arquivo']}. Volte o arquivo para lá e rode de novo.")
    assinatura = {**assinatura_video(info["arquivo"]), "faixa": info["faixa_audio"], "versao": 1}
    cache = dados / "volume.json"
    if cache.exists():
        try:
            d = ler_json(cache)
            if d.get("assinatura") == assinatura:
                return d["db"]
        except Exception:
            pass
    fonte, K = info["arquivo"], info["faixa_audio"]
    px = proxy_valido(dados, info)
    if px:   # a cópia leve tem o mesmo som, sem o 4K para atravessar
        fonte, K = str(px), 0
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(fonte), "-map", f"0:a:{K}", "-vn",
                        "-ac", "1", "-ar", "16000", "-f", "s16le", "-acodec", "pcm_s16le", "-"], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        sair(f"Não consegui ler o som do vídeo para achar a borda da fala:\n{r.stderr.decode(errors='replace')[-500:]}")
    a = array("h")
    a.frombytes(r.stdout[:len(r.stdout) // 2 * 2])
    if sys.byteorder == "big":
        a.byteswap()
    n = int(16000 * PASSO)
    db = []
    for j in range(0, len(a) - n + 1, n):
        q = a[j:j + n]
        db.append(round(10 * math.log10(sum(map(mul, q, q)) / n / 32768 ** 2 + 1e-10), 1))
    gravar_json(cache, {"assinatura": assinatura, "passo": PASSO, "db": db})
    return db


def com_voz(db):
    """Para cada 10 ms: tem voz? Limiar = ruído de fundo (percentil 12) + 14 dB, medido no próprio vídeo."""
    piso = sorted(db)[int(len(db) * VOZ_PERCENTIL / 100)]
    return [d > piso + VOZ_DB for d in db]


def borda_ini(t, antes, voz):
    """Começo do som da palavra que o Whisper marcou em t, sem invadir a palavra de antes."""
    lim = max(t - 0.25, antes + 0.02)
    for i in range(max(0, int(lim / PASSO)), min(len(voz) - 3, int((t + 0.45) / PASSO))):
        if all(voz[i:i + 4]):
            return max(lim, i * PASSO - FOLGA_A)
    return t


def borda_fim(t, prox, voz):
    """Fim do som da palavra que o Whisper marcou em t: pega o "-tos" de "produtos" que ele encurtou."""
    ate = min(t + 0.30, prox - 0.03) if prox is not None else t + 0.30
    ult = None
    for i in range(max(0, int((t - 0.35) / PASSO)), min(len(voz), int(ate / PASSO))):
        if voz[i]:
            ult = i
    f = ult * PASSO + FOLGA_B if ult is not None else t
    return min(f, prox - 0.03) if prox is not None else f


# ---------------------------------------------------------------- mapa de cortes

def fim_real(w):
    return min(w["fim"], w["ini"] + CAP_PALAVRA)


def limpar(ini, fim, pal, idx, sil, pausa):
    """Tira de dentro de um pedaço de fala as pausas medidas (silencedetect) maiores que pausa, deixando um
    respiro curto, e os sons sem palavra do Whisper (pedaço vazio) de VAZIA_MIN ou mais, sem encostar na
    palavra vizinha. É o que tira os respingos e as hesitações que as bordas das palavras escondem."""
    cortes = []
    for s0, s1 in sil or []:
        if s1 - s0 > pausa and s0 < fim and s1 > ini:
            a, b = max(ini, s0 + RESPIRO_OUT), min(fim, s1 - RESPIRO_IN)
            if b - a > 0.08:
                cortes.append((a, b))
    reais = [i for i in idx if pal[i]["w"]]
    for i in idx:
        w = pal[i]
        if w["w"] or w["fim"] - w["ini"] < VAZIA_MIN:
            continue
        antes = max((fim_real(pal[j]) for j in reais if pal[j]["ini"] < w["ini"]), default=ini)
        depois = min((pal[j]["ini"] for j in reais if pal[j]["ini"] > w["ini"]), default=fim)
        a, b = max(w["ini"], antes + 0.04), min(w["fim"], depois - 0.02)
        if b - a > 0.08:
            cortes.append((a, b))
    pedacos = [[ini, fim]]
    for a, b in sorted(cortes):
        novos = []
        for x, y in pedacos:
            if b <= x or a >= y:
                novos.append([x, y])
                continue
            if a > x:
                novos.append([x, a])
            if b < y:
                novos.append([b, y])
        pedacos = novos
    return [p for p in pedacos if p[1] - p[0] > 0.05]


def vizinho(z, niveis):
    """Nível do zoom para a emenda de dentro do trecho: o de baixo; no mais baixo, o de cima."""
    abaixo = [n for n in niveis if n < z - 1e-6]
    acima = [n for n in niveis if n > z + 1e-6]
    return abaixo[-1] if abaixo else (acima[0] if acima else z)


def segmentos(c, pal, info, sil=None, voz=None):
    """Trechos -> segmentos em quadros do bruto, na ordem final: [{fi, fo, k, idx, z}].
    voz (lista de com_voz) liga as bordas pelo som; sem ela, a borda é a palavra mais uma folga fixa."""
    trechos, pausa = c["trechos"], c["pausa"]
    fps = Fraction(info["fps_num"], info["fps_den"])
    dur = info["duracao"]
    fins = [fim_real(w) for w in pal]
    reais = [i for i, w in enumerate(pal) if w["w"]]
    brutos, avisos = [], []
    for t in trechos:
        idx = [i for i, w in enumerate(pal) if t["de"] <= (w["ini"] + fins[i]) / 2 <= t["ate"]
               and (t["i_de"] is None or i >= t["i_de"]) and (t["i_ate"] is None or i <= t["i_ate"])]
        if t["exato"]:
            pedacos = [(t["de"], t["ate"], idx)]
        elif not idx:
            avisos.append(f"T{t['k']} não tem fala; ficou inteiro ({fmt_tempo(t['de'])}–{fmt_tempo(t['ate'])}).")
            pedacos = [(t["de"], t["ate"], [])]
        else:
            grupos = [[idx[0]]]
            for i in idx[1:]:
                if i != grupos[-1][-1] + 1 or pal[i]["ini"] - fins[i - 1] > pausa:
                    grupos.append([i])
                else:
                    grupos[-1].append(i)
            pedacos = []
            for g in grupos:
                a, b = pal[g[0]]["ini"], fins[g[-1]]
                if voz is None:
                    lim_a = (fins[g[0] - 1] + a) / 2 if g[0] > 0 else 0.0
                    lim_b = (b + pal[g[-1] + 1]["ini"]) / 2 if g[-1] + 1 < len(pal) else dur
                    x0, y0 = max(0.0, a - PAD_IN, lim_a), min(dur, b + PAD_OUT, lim_b)
                    pedacos += [(x, y, g) for x, y in limpar(x0, y0, pal, g, sil, pausa)]
                    continue
                gr = [i for i in g if pal[i]["w"]] or g
                antes = max((fins[j] for j in reais if j < gr[0]), default=0.0)
                prox = min((pal[j]["ini"] for j in reais if j > gr[-1]), default=None)
                x0 = max(0.0, borda_ini(pal[gr[0]]["ini"], antes, voz))
                if pedacos:   # a respiração entre dois grupos não entra nos dois: sem som repetido na emenda
                    x0 = max(x0, pedacos[-1][1])
                y0 = min(dur, borda_fim(fins[gr[-1]], prox, voz))
                partes = limpar(x0, y0, pal, g, sil, pausa)
                # pedaço sem nenhuma palavra (respiração, estalo) é um piscar de imagem: sai
                falam = [(x, y) for x, y in partes
                         if any(min(y, fins[i]) - max(x, pal[i]["ini"]) > 0.02 for i in gr if pal[i]["w"])]
                pedacos += [(x, y, g) for x, y in (falam or partes)]
        aj = c["ajustes"].get(t["k"])
        if aj and pedacos:   # deslocamento fino da borda, escrito pela /criticar
            x, y, g = pedacos[0]
            pedacos[0] = (max(0.0, x + aj.get("de", 0.0)), y, g)
            x, y, g = pedacos[-1]
            pedacos[-1] = (x, min(dur, y + aj.get("ate", 0.0)), g)
        brutos += [(x, y, t["k"], g) for x, y, g in pedacos]
    segs = []
    for ini, fim, k, idx in brutos:
        fi, fo = int(round(ini * fps)), int(round(fim * fps))
        if fo <= fi:
            continue
        p = segs[-1] if segs else None
        if p and p["k"] == k and p["fi"] <= fi <= p["fo"]:
            p["fo"] = max(p["fo"], fo)
            p["idx"] = sorted(set(p["idx"]) | set(idx))
        else:
            segs.append({"fi": fi, "fo": fo, "k": k, "idx": list(idx)})
    tl = 0
    zoom_t = {t["k"]: t["zoom"] or 1.0 for t in trechos}
    for n, s in enumerate(segs):
        s["tl_in"], s["tl_out"] = tl, tl + s["fo"] - s["fi"]
        tl = s["tl_out"]
        z, p = zoom_t[s["k"]], segs[n - 1] if n else None
        s["z"] = z
        if p and p["k"] == s["k"] and c["zoom"]["alternar"]:   # emenda dentro do trecho: troca para o vizinho
            longo = (s["fo"] - s["fi"]) / fps >= ZOOM_MIN
            s["z"] = (vizinho(z, c["zoom"]["niveis"]) if p["z"] == z else z) if longo else p["z"]
    for a in range(len(trechos)):
        for b in range(a + 1, len(trechos)):
            u, v = trechos[a], trechos[b]
            if min(u["ate"], v["ate"]) - max(u["de"], v["de"]) > 0.3:
                avisos.append(f"T{u['k']} e T{v['k']} usam o mesmo pedaço do bruto: a fala vai aparecer duas vezes.")
    return segs, avisos


def palavras_finais(segs, pal, fps):
    """Palavras que ficaram, no tempo do vídeo cortado (antes da velocidade): (texto, início, fim, índice, trecho)."""
    out = []
    for s in segs:
        a, b = s["fi"] / fps, s["fo"] / fps
        base, lo, hi = s["tl_in"] / fps - a, s["tl_in"] / fps, s["tl_out"] / fps
        for i in s["idx"]:
            w = pal[i]
            if w["w"] and a <= (w["ini"] + fim_real(w)) / 2 <= b:
                out.append((w["w"], min(max(w["ini"] + base, lo), hi), min(max(fim_real(w) + base, lo), hi), i, s["k"]))
    return out


def bordas(segs, fps, vel):
    """Bordas previstas no tempo final: [0, cada emenda, fim] em segundos (o vídeo muda de pedaço em cada emenda)."""
    return [0.0] + [float(s["tl_out"] / fps) / vel for s in segs]


def assinatura_corte(segs, fps, vel):
    return hashlib.sha1(json.dumps([[s["fi"], s["fo"], s["k"]] for s in segs] + [str(fps), vel]).encode()).hexdigest()[:16]


def remapear(t, prev, real):
    """Tempo previsto -> tempo medido no vídeo renderizado, por partes: cada pedaço entre duas emendas estica igual."""
    if not real or prev == real:
        return t
    j = max(0, min(len(prev) - 2, bisect.bisect_right(prev, t) - 1))
    a, b, x, y = prev[j], prev[j + 1], real[j], real[j + 1]
    return x + (t - a) * (y - x) / (b - a) if b > a else x


def contar(arq):
    """(quadros da imagem, amostras do som a 48 kHz) de um arquivo, contando os pacotes (sem decodificar)."""
    r = rodar(["ffprobe", "-v", "error", "-count_packets", "-show_entries",
               "stream=codec_type,nb_read_packets,duration_ts,time_base", "-of", "json", arq])
    q = am = None
    for st in json.loads(r.stdout or "{}").get("streams", []):
        if st.get("codec_type") == "video" and q is None:
            q = int(st.get("nb_read_packets") or 0)
        elif st.get("codec_type") == "audio" and am is None and st.get("duration_ts"):
            am = int(round(int(st["duration_ts"]) * Fraction(st.get("time_base") or "1/48000") * 48000))
    return q, am


def medir_render(dados, nome, segs, fps, vel, saida, pedacos=None):
    """Bordas reais do vídeo renderizado (contrato 3.2): conta os quadros e as amostras de cada pedaço (render em
    pedaços) e da saída, e grava .dados/medida-<nome>.json. Devolve (medida, aviso)."""
    prev = bordas(segs, fps, vel)
    q_out, a_out = contar(saida)
    previstos = sum(s["fo"] - s["fi"] for s in segs)
    aviso = ""
    if pedacos:
        cont = [contar(a) for a in pedacos]
        quadros = [q for q, _ in cont]
        fonte = "pedacos"
    else:
        quadros = [s["fo"] - s["fi"] for s in segs]
        fonte = "saida"
    # com velocidade, o fps da junção põe o quadro n do corte na vaga round(n / velocidade) da saída: a emenda
    # cai no quadro da saída onde a imagem troca. Se a saída tiver outro total, o resto é repartido igual.
    total = sum(quadros)
    vagas = int(round(total / vel)) or 1
    escala = (q_out / vagas) if q_out else 1.0
    real, acc = [0.0], 0
    for q in quadros:
        acc += q
        real.append(round(round(acc / vel) * escala / float(fps), 4))
    if pedacos and any(q != s["fo"] - s["fi"] for q, s in zip(quadros, segs)):
        aviso = "um pedaço saiu com quadros a mais ou a menos; as bordas no palavras-corte.json seguem o medido."
    if a_out and q_out:
        dif = a_out / 48000 - q_out / float(fps)
        if abs(dif) > 1.5 / float(fps):
            aviso += f" O som da saída tem {fmt_num(dif, 3)} s a mais que a imagem."
    m = {"assinatura": assinatura_corte(segs, fps, vel), "video": nome, "fonte": fonte, "prev": prev, "real": real,
         "quadros_saida": q_out, "quadros_previstos": int(round(previstos / vel)), "amostras_saida": a_out}
    gravar_json(dados / f"medida-{Path(nome).stem}.json", m)
    return m, aviso.strip()


def medida_salva(dados, nome, segs, fps, vel):
    p = dados / f"medida-{Path(nome).stem}.json"
    try:
        m = ler_json(p)
        return m if m.get("assinatura") == assinatura_corte(segs, fps, vel) else None
    except Exception:
        return None


def palavras_corte(pf, pal, frases, fps, velocidade, duracao, video, segs, medida=None):
    """decupagem/palavras-corte.json (contrato, seção 3.2): cada palavra e frase que ficou, as bordas de cada trecho
    e as emendas, no tempo final. Com `medida` (o vídeo já renderizado), tudo segue as bordas medidas nele."""
    prev = bordas(segs, fps, velocidade)
    real = medida["real"] if medida else None
    R = (lambda t: round(remapear(float(t), prev, real), 3)) if real else (lambda t: round(float(t), 3))
    dono = {}
    for f in frases.values():
        for n, i in enumerate(palavras_da_frase(f, pal), 1):
            dono[i] = (f["id"], n)
    palavras = []
    for w, a, b, i, k in pf:
        fid, n = dono.get(i, ("", 0))
        palavras.append({"w": w, "a": R(a), "b": R(b), "frase": fid, "n": n, "i": i, "trecho": k})
    blocos = []
    for p in palavras:
        if blocos and blocos[-1]["id"] == p["frase"] and blocos[-1]["trecho"] == p["trecho"]:
            blocos[-1]["b"] = p["b"]
            blocos[-1]["ws"].append(p["w"])
        else:
            blocos.append({"id": p["frase"], "trecho": p["trecho"], "a": p["a"], "b": p["b"], "ws": [p["w"]]})
    trechos = {}
    for j, s in enumerate(segs):
        x = trechos.setdefault(s["k"], {"n": s["k"], "a": R(prev[j])})
        x["b"] = R(prev[j + 1])
    fps_txt = int(fps) if fps.denominator == 1 else round(float(fps), 3)
    return {"versao": 2, "video": video, "duracao": R(duracao), "fps": fps_txt,
            "velocidade": velocidade, "medido": medida["fonte"] if medida else False,
            "trechos": list(trechos.values()),
            "emendas": [R(t) for t in prev[1:-1]],
            "frases": [{"id": f["id"], "a": f["a"], "b": f["b"], "texto": " ".join(f["ws"]), "trecho": f["trecho"]}
                       for f in blocos],
            "palavras": palavras}


# ---------------------------------------------------------------- legenda

def srt_tempo(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def legenda(pf):
    blocos, atual = [], []
    for w in pf:
        if atual:
            prev = atual[-1]
            txt = " ".join(x[0] for x in atual) + " " + w[0]
            if (len(txt) > LEG_CARACTERES or len(atual) >= LEG_PALAVRAS or re.search(r"[.!?…]$", prev[0])
                    or (re.search(r"[,;:]$", prev[0]) and len(atual) >= 2) or w[1] - prev[2] > 0.6):
                blocos.append(atual)
                atual = []
        atual.append(w)
    if atual:
        blocos.append(atual)
    linhas = []
    for n, b in enumerate(blocos):
        ini, fim = b[0][1], max(b[-1][2], b[0][1] + 0.4)
        if n + 1 < len(blocos):
            prox = blocos[n + 1][0][1]
            fim = prox if prox - fim < 0.25 else min(fim, prox)
        texto = re.sub(r"[.,;:…]+$", "", " ".join(x[0] for x in b)).strip()
        linhas.append(f"{n + 1}\n{srt_tempo(ini)} --> {srt_tempo(fim)}\n{texto}\n")
    return "\n".join(linhas), len(blocos)


# ---------------------------------------------------------------- XML (FCP7, Premiere e DaVinci)

def xml_premiere(info, segs):
    fps = Fraction(info["fps_num"], info["fps_den"])
    tb, ntsc = round(fps), "TRUE" if fps.denominator == 1001 else "FALSE"
    R = f"<rate><timebase>{tb}</timebase><ntsc>{ntsc}</ntsc></rate>"
    total = int(round(info["duracao"] * fps))
    video = Path(info["arquivo"])
    url = "file://localhost/" + urllib.parse.quote(video.as_posix().lstrip("/"), safe="/:")
    nome = escape(video.stem)
    W, H = info["largura"], info["altura"]
    canais = max(1, min(2, info["canais"] or 2))
    file_xml = (f'<file id="bruto"><name>{escape(video.name)}</name><pathurl>{url}</pathurl>{R}'
                f"<duration>{total}</duration><media><video><samplecharacteristics>{R}"
                f"<width>{info['largura_arq']}</width><height>{info['altura_arq']}</height>"
                f"<pixelaspectratio>square</pixelaspectratio></samplecharacteristics></video>"
                f"<audio><samplecharacteristics><depth>16</depth><samplerate>{info['taxa_audio']}</samplerate>"
                f"</samplecharacteristics><channelcount>{canais}</channelcount></audio></media></file>")
    # sem giro no clipe: o Premiere e o DaVinci já leem a rotação do arquivo (girar aqui deitava o vídeo do iPhone)
    ch0 = info["canais_antes"]

    def item(iid, s, k, extra):
        arq = file_xml if iid == "v-1" else '<file id="bruto"/>'
        return (f'<clipitem id="{iid}"><name>{nome}</name><enabled>TRUE</enabled><duration>{total}</duration>{R}'
                f"<start>{s['tl_in']}</start><end>{s['tl_out']}</end><in>{s['fi']}</in><out>{s['fo']}</out>"
                f"{arq}{extra}{links(k)}</clipitem>")

    def links(k):
        return "".join(f"<link><linkclipref>{ref}-{k}</linkclipref><mediatype>{mt}</mediatype>"
                       f"<trackindex>{ti}</trackindex><clipindex>{k}</clipindex></link>"
                       for ref, mt, ti in (("v", "video", 1), ("a1", "audio", 1), ("a2", "audio", 2)))

    v, a1, a2 = [], [], []
    for k, s in enumerate(segs, 1):
        v.append(item(f"v-{k}", s, k, "<compositemode>normal</compositemode>"))
        for lst, tag, lado in ((a1, "a1", 1), (a2, "a2", 2)):
            ti = ch0 + (lado if canais == 2 else 1)
            lst.append(item(f"{tag}-{k}", s, k, f"<sourcetrack><mediatype>audio</mediatype>"
                                               f"<trackindex>{ti}</trackindex></sourcetrack>"))

    def atrack(items, idx):
        return (f'<track premiereTrackType="Stereo" totalExplodedTrackCount="2" currentExplodedTrackIndex="{idx - 1}">'
                f"{''.join(items)}<enabled>TRUE</enabled><locked>FALSE</locked>"
                f"<outputchannelindex>{idx}</outputchannelindex></track>")

    dur = segs[-1]["tl_out"]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4">\n'
            f'<sequence id="decupar" explodedTracks="true"><name>{nome} (decupado)</name><duration>{dur}</duration>{R}'
            f"<in>-1</in><out>-1</out><timecode>{R}<string>00:00:00:00</string><frame>0</frame>"
            "<displayformat>NDF</displayformat></timecode>"
            f"<media><video><format><samplecharacteristics>{R}<width>{W}</width><height>{H}</height>"
            "<pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance>"
            f"</samplecharacteristics></format><track>{''.join(v)}<enabled>TRUE</enabled><locked>FALSE</locked>"
            "</track></video><audio><numOutputChannels>2</numOutputChannels><format><samplecharacteristics>"
            "<depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format>"
            f"{atrack(a1, 1)}{atrack(a2, 2)}</audio></media></sequence>\n</xmeml>\n")


CAPCUT = """# Levar para o CapCut (computador)

1. Abra o CapCut no computador e clique em **Criar projeto**.
2. **Importar** → escolha `{video}` → arraste para a linha do tempo.
   O vídeo já está cortado: sem pausas e sem as partes repetidas.
3. Legenda: menu **Legendas** → **Adicionar legendas** → **Importar arquivo** → escolha `legenda.srt`.
   Cada frase vira um bloco de texto que você pode editar e estilizar.
4. Se a sua versão não tiver a opção de importar: **Legendas** → **Legendas automáticas** →
   idioma Português → **Gerar**. (Em algumas versões esse recurso é pago.)
5. Exporte em 1080p.

Para publicar com mais nitidez, peça ao Claude o vídeo final ("gera o final") e use o `final.mp4`
no passo 2. A `previa.mp4` serve para conferir os cortes.
"""


# ---------------------------------------------------------------- render

def filtros_disponiveis():
    r = rodar(["ffmpeg", "-hide_banner", "-filters"])
    return set(re.findall(r"^\s*\S+\s+(\w+)\s", r.stdout, re.M))


def esperar_proxy(dados, limite=900):
    """A cópia leve sai em segundo plano depois da transcrição. Enquanto o arquivo parcial cresce, espera."""
    parcial, avisou, t0 = dados / "proxy.parcial.mov", False, time.time()
    while parcial.exists() and time.time() - parcial.stat().st_mtime < 15 and time.time() - t0 < limite:
        if not avisou:
            print("Esperando a cópia leve do vídeo terminar (ela deixa a prévia e as correções rápidas)...", flush=True)
            avisou = True
        time.sleep(1)


def recorte_vertical(pasta, info):
    """Centro do recorte 9:16 (fração da largura) para vídeo horizontal com "vertical" no cortes.json."""
    v = ler_json(pasta / "cortes.json").get("vertical")
    if not v or info["altura"] >= info["largura"]:
        return None
    if isinstance(v, dict) and "centro_x" in v:
        return min(max(float(v["centro_x"]), 0.0), 1.0)
    p = pasta / ".dados" / "enquadrar.json"
    if p.exists():
        return float(ler_json(p)["centro_x"])
    sair("O cortes.json pede \"vertical\", mas falta achar o rosto: rode antes o enquadrar.py.")


def janela(sw, sh, centro, z, ancora):
    """Recorte [w, h, x, y] na resolução da fonte: a janela 9:16 (vídeo horizontal) ou o quadro todo, apertada
    pelo zoom em volta da âncora. A âncora (fração do quadro de saída) fica no mesmo lugar com ou sem zoom."""
    if centro is not None:
        bw, bh = int(sh * 9 / 16 / 2) * 2, sh
        bx, by = max(0.0, min(sw - bw, sw * centro - bw / 2)), 0.0
    else:
        bw, bh, bx, by = sw, sh, 0.0, 0.0
    cw, ch = max(2, int(round(bw / z / 2)) * 2), max(2, int(round(bh / z / 2)) * 2)
    return cw, ch, int(round(bx + ancora[0] * (bw - cw))), int(round(by + ancora[1] * (bh - ch)))


def intermediario(final, sem_perda=True):
    """Codec dos pedaços. Final: sem perda (x264 qp 0, ou FFV1), e o vídeo só perde qualidade uma vez, no mp4.
    Prévia, ou disco sem espaço para o final sem perda: quase sem perda e uns 3x menor."""
    if "libx264" in rodar(["ffmpeg", "-hide_banner", "-encoders"]).stdout:
        q = ["-qp", "0"] if final and sem_perda else ["-crf", "8" if final else "14"]
        return ["-c:v", "libx264", "-preset", "ultrafast", *q]
    return ["-c:v", "ffv1", "-level", "3"]


def render_pedacos(pasta, info, segs, final, c, fonte, K, fonte_wh, centro, W, H, filtro_cor, tentativas, parcial):
    """Um pedaço por segmento (quadros e amostras exatos, recorte do zoom na resolução da fonte), em paralelo e
    guardados pelo conteúdo; depois junta, acelera (setpts + atempo) e grava o mp4 uma vez só."""
    fps = Fraction(info["fps_num"], info["fps_den"])
    fps_txt = f"{fps.numerator}/{fps.denominator}"
    dados = pasta / ".dados"
    pasta_p = dados / ("pedacos-final" if final else "pedacos-previa")
    pasta_p.mkdir(exist_ok=True)
    # sem perda gasta ~0,5 byte por pixel (25 MB por segundo em 1080×1920): sem espaço, cai para quase sem perda
    estimativa = 0.5 * W * H * sum(s["fo"] - s["fi"] for s in segs)
    sem_perda = shutil.disk_usage(pasta_p).free > estimativa + 1e9
    if final and not sem_perda:
        print(f"Aviso: pouco espaço no disco (os pedaços sem perda ocupariam {fmt_num(estimativa / 1e9)} GB); "
              "vou usar pedaços quase sem perda.", flush=True)
    codec = intermediario(final, sem_perda)
    try:
        sig = assinatura_video(fonte)
    except OSError:
        sig = None

    def amostras(q):   # amostra de áudio (48 kHz) onde começa o quadro q da linha do tempo
        return int(round(q * Fraction(48000) / fps))

    def fazer(s):
        """Devolve (arquivo, se foi feito agora, erro)."""
        n = s["fo"] - s["fi"]
        m = amostras(s["tl_out"]) - amostras(s["tl_in"])
        corte = janela(fonte_wh[0], fonte_wh[1], centro, s["z"], c["zoom"]["ancora"])
        geo = "" if corte == (fonte_wh[0], fonte_wh[1], 0, 0) else "crop={}:{}:{}:{},".format(*corte)
        receita = json.dumps([VERSAO_PEDACO, str(fonte), sig, K, s["fi"], n, m, fps_txt, corte, W, H, filtro_cor,
                              [t[1] for t in tentativas][:1], codec])
        arq = pasta_p / f"{hashlib.sha1(receita.encode()).hexdigest()[:16]}.mov"
        if arq.exists():
            return arq, False, ""
        ini = Fraction(s["fi"]) / fps
        ss = max(Fraction(0), ini - Fraction(1, 2))
        d = float(n / fps)
        fade = f",afade=t=in:d=0.008,afade=t=out:st={d - 0.012:.5f}:d=0.012" if d > 0.05 else ""
        af = (f"aresample=48000,atrim=start={float(ini - ss):.6f},asetpts=PTS-STARTPTS,apad,"
              f"atrim=end_sample={m}{fade}")
        tmp = arq.with_suffix(".parcial.mov")
        erro = ""
        for hw, tom in tentativas:
            # o trim pega o quadro fi; o tpad completa se a fonte acabar antes: o pedaço tem n quadros e m amostras
            vf = (f"trim=start={max(0.0, float(ini - ss - Fraction(1, 2) / fps)):.6f},setpts=PTS-STARTPTS,"
                  f"fps={fps_txt},tpad=stop_mode=clone:stop={n},trim=end_frame={n},{geo}"
                  f"scale={W}:{H}:flags=lanczos,setsar=1,{tom}{filtro_cor}format=yuv420p")
            r = rodar(["ffmpeg", "-hide_banner", "-v", "error", "-y", *hw, "-ss", f"{float(ss):.6f}",
                       "-t", f"{d + 1.2:.3f}", "-i", fonte, "-map", "0:v:0", "-map", f"0:a:{K}", "-vf", vf,
                       "-af", af, "-frames:v", str(n), *codec, "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le",
                       "-ar", "48000", "-ac", "2", tmp], cwd=dados)
            if r.returncode == 0:
                tmp.replace(arq)
                return arq, True, ""
            erro = r.stderr[-1200:]
        tmp.unlink(missing_ok=True)
        return None, False, erro

    with ThreadPoolExecutor(max(2, min(4, (os.cpu_count() or 4) // 2))) as ex:
        feitos = list(ex.map(fazer, segs))
    falhou = next((e for a, _, e in feitos if a is None), None)
    if falhou is not None:
        sair(f"O render de um pedaço falhou. Fim da mensagem do ffmpeg:\n{falhou}")
    arqs = [a for a, _, _ in feitos]
    lista = pasta_p / "lista.txt"
    lista.write_text("".join("file '{}'\n".format(a.as_posix().replace("'", "'\\''")) for a in arqs),
                     encoding="utf-8")
    v = c["velocidade"]
    vf = f"setpts=PTS/{v:g},fps={fps_txt}" if v != 1 else "null"
    af = (f"atempo={v:g}," if v != 1 else "") + \
        "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo"
    tonemap = bool(tentativas[0][1])
    cor = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"] if tonemap else []
    r = rodar(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista,
               "-map", "0:v:0", "-map", "0:a:0", "-vf", vf, "-af", af, *encoder("final" if final else "previa"),
               "-pix_fmt", "yuv420p", *cor, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", parcial])
    if r.returncode != 0:
        parcial.unlink(missing_ok=True)
        sair(f"Juntar os pedaços falhou. Fim da mensagem do ffmpeg:\n{r.stderr[-1500:]}")
    usados = set(arqs) | {lista}
    for p in pasta_p.iterdir():   # guarda só os pedaços deste corte: uma correção reaproveita, o disco não enche
        if p not in usados:
            p.unlink(missing_ok=True)
    gb = sum(a.stat().st_size for a in arqs) / 1e9
    return sum(1 for _, novo, _ in feitos if novo), len(arqs), tonemap, gb, arqs


def render(pasta, info, segs, final, c):
    fps = Fraction(info["fps_num"], info["fps_den"])
    fps_txt = f"{fps.numerator}/{fps.denominator}"
    centro = recorte_vertical(pasta, info)
    W, H = tamanho(info, final, vertical=centro is not None)
    geo = f"scale={W}:{H}:flags=bicubic"
    if centro is not None:   # janela 9:16 na altura toda, centrada no rosto e presa dentro do quadro
        geo = (f"crop=w='trunc(ih*9/16/2)*2':h=ih:x='max(0,min(iw-ow,iw*{centro:.4f}-ow/2))':y=0,"
               f"scale={W}:{H}:flags=bicubic")
    filtro_cor = filtro_da_pasta(pasta, info)
    filtro_cor = filtro_cor + "," if filtro_cor else ""
    saida = pasta / ("final.mp4" if final else "previa.mp4")
    parcial = pasta / ("final.parcial.mp4" if final else "previa.parcial.mp4")
    if saida.resolve() == Path(info["arquivo"]):
        sair("A saída cairia em cima do vídeo bruto; nada foi gravado.")
    runs = []
    for s in segs:   # blocos em ordem crescente no bruto; um gancho movido para o início abre outro bloco
        if runs and s["fi"] >= runs[-1][-1]["fo"]:
            runs[-1].append(s)
        else:
            runs.append([s])
    filtros = filtros_disponiveis()
    tom = ""
    tonemap = info["hdr"] and {"zscale", "tonemap"} <= filtros
    if tonemap:
        tom = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
               "zscale=t=bt709:m=bt709:r=tv,")
    K = info["faixa_audio"]
    fonte = info["arquivo"]
    if not final:
        esperar_proxy(pasta / ".dados")
    px = None if final else proxy_valido(pasta / ".dados", info)
    if px:
        fonte, K = str(px), 0
    # tentativas: com aceleração de vídeo, sem ela, e (vídeo HDR) sem a conversão de cor
    tentativas = [(hw, tom) for hw in ([hwaccel(), []] if hwaccel() else [[]])] + ([([], "")] if tom else [])

    if c["velocidade"] != 1 or any(s["z"] != 1 for s in segs):
        fonte_wh = tamanho(info) if px else (info["largura"], info["altura"])
        novos, total, tonemap, gb, arqs = render_pedacos(pasta, info, segs, final, c, fonte, K, fonte_wh, centro, W,
                                                         H, filtro_cor, tentativas, parcial)
        parcial.replace(saida)
        p = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", saida])
        return (saida, float(p.stdout.strip() or 0), (W, H), tonemap, bool(px), bool(filtro_cor), centro,
                (novos, total, gb, arqs))

    def montar(hw, tom):
        entradas, fc = [], []
        for r, run in enumerate(runs):
            ini, fim = float(run[0]["fi"] / fps), float(run[-1]["fo"] / fps)
            ss = round(ini - 2.0, 3) if ini > 5 else 0.0
            entradas += [*hw, *(["-ss", f"{ss:.3f}"] if ss else []), "-t", f"{fim - ss + 1:.3f}",
                         "-i", fonte]
            meio = Fraction(1, 2)
            sel = "+".join(f"between(t,{float((s['fi'] - meio) / fps) - ss:.5f},{float((s['fo'] - meio) / fps) - ss:.5f})"
                           for s in run)
            pts = f"T-{float(run[0]['fi'] / fps) - ss:.5f}" + "".join(
                f"-{float((s['fi'] - p['fo']) / fps):.5f}*gte(T,{float((s['fi'] - meio) / fps) - ss:.5f})"
                for p, s in zip(run, run[1:]))
            quadros = sum(s["fo"] - s["fi"] for s in run)
            # o trim fecha no último quadro: sem ele o fps repete a imagem até o fim da leitura (-t)
            fc.append(f"[{r}:v]select='{sel}',{geo},setsar=1,{tom}{filtro_cor}"
                      f"setpts='({pts})/TB',fps={fps_txt},trim=end_frame={quadros}[v{r}]")
            n = len(run)
            nomes = [f"r{r}a{j}" for j in range(n)]
            if n > 1:
                fc.append(f"[{r}:a:{K}]asplit={n}" + "".join(f"[{x}]" for x in nomes))
            for j, s in enumerate(run):
                a, b = float(s["fi"] / fps) - ss, float(s["fo"] / fps) - ss
                d = b - a
                fade = f",afade=t=in:d=0.008,afade=t=out:st={d - 0.012:.5f}:d=0.012" if d > 0.05 else ""
                origem = f"[{nomes[j]}]" if n > 1 else f"[{r}:a:{K}]"
                fc.append(f"{origem}atrim=start={a:.5f}:end={b:.5f},asetpts=PTS-STARTPTS{fade}[r{r}s{j}]")
            fc.append("".join(f"[r{r}s{j}]" for j in range(n)) + f"concat=n={n}:v=0:a=1[a{r}]")
        if len(runs) > 1:
            fc.append("".join(f"[v{r}][a{r}]" for r in range(len(runs))) + f"concat=n={len(runs)}:v=1:a=1[vc][ac]")
        else:
            fc.append("[v0]null[vc]")
            fc.append("[a0]anull[ac]")
        fc.append("[vc]format=yuv420p[vo]")
        fc.append("[ac]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[ao]")
        return entradas, ";\n".join(fc)

    grafo = pasta / ".dados" / "grafo.txt"
    r = None
    for hw, tom_agora in tentativas:
        tonemap = bool(tom_agora)
        cor = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"] if tonemap else []
        fim_cmd = ["-map", "[vo]", "-map", "[ao]", *encoder("final" if final else "previa"), *cor,
                   "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", parcial]
        entradas, fc = montar(hw, tom_agora)
        grafo.write_text(fc, encoding="utf-8")
        for opcao in ("-/filter_complex", "-filter_complex_script"):   # ffmpeg 7+ / ffmpeg antigo
            # pasta atual = .dados: o look com LUT usa o nome curto do .cube copiado para lá
            r = rodar(["ffmpeg", "-hide_banner", "-v", "error", "-y", *entradas, opcao, grafo, *fim_cmd],
                      cwd=pasta / ".dados")
            if "nrecognized option" not in r.stderr:
                break
        if r.returncode == 0:
            break
    if r.returncode != 0:
        parcial.unlink(missing_ok=True)
        sair(f"O render falhou. Fim da mensagem do ffmpeg:\n{r.stderr[-1500:]}")
    parcial.replace(saida)
    p = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", saida])
    return saida, float(p.stdout.strip() or 0), (W, H), tonemap, bool(px), bool(filtro_cor), centro, None


# ---------------------------------------------------------------- principal

def main():
    utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sair(__doc__)
    t0 = time.time()
    pasta = achar_pasta(args[0])
    dados = pasta / ".dados"
    info = ler_json(dados / "info.json")
    pj = ler_json(dados / "palavras.json")
    pal, sil = pj["palavras"], pj.get("silencios", [])
    frases = {f["id"]: f for f in ler_json(dados / "frases.json")}
    fps = Fraction(info["fps_num"], info["fps_den"])
    c = ler_cortes(pasta, frases, pal, info["duracao"])
    voz = com_voz(volume(pasta, info)) if c["bordas"] == "som" else None
    segs, avisos = segmentos(c, pal, info, sil, voz)
    avisos = c["avisos"] + avisos
    if not segs:
        sair("Os trechos do cortes.json não deixaram nada no vídeo.")
    vel = c["velocidade"]
    final_s = float(segs[-1]["tl_out"] / fps) / vel
    pf = [(w, a / vel, b / vel, i, k) for w, a, b, i, k in palavras_finais(segs, pal, fps)]
    final = "--final" in sys.argv
    nome = "final.mp4" if final or ("--resumo" in sys.argv and (pasta / "final.mp4").exists()) else "previa.mp4"
    pc = palavras_corte(pf, pal, frases, fps, vel, final_s, nome, segs, medida_salva(dados, nome, segs, fps, vel))
    gravar_json(pasta / "palavras-corte.json", pc)

    if "--resumo" in sys.argv:
        antes = info["duracao"]
        dentro = sum(float((max(s["fo"] for s in segs if s["k"] == t["k"]) - min(s["fi"] for s in segs if s["k"] == t["k"])
                            - sum(s["fo"] - s["fi"] for s in segs if s["k"] == t["k"])) / fps)
                     for t in c["trechos"] if any(s["k"] == t["k"] for s in segs))
        print(f"Antes: {fmt_dur(antes)} · Depois: {fmt_dur(final_s)} "
              f"(saem {fmt_dur(max(0.0, antes - final_s))}, {round(100 * max(0.0, antes - final_s) / antes)}%)"
              + (f" · velocidade {fmt_num(vel, 2).rstrip('0').rstrip(',')}×" if vel != 1 else ""))
        print(f"Emendas: {len(segs) - 1} · pausas tiradas dentro dos trechos: {fmt_num(dentro)} s · "
              f"o resto saiu com os trechos descartados" + (" · bordas pelo som" if voz else ""))
        print("Trechos na ordem do vídeo final (bruto → final):")
        for t in c["trechos"]:
            ss = [s for s in segs if s["k"] == t["k"]]
            if not ss:
                print(f"T{t['k']}: ficou vazio")
                continue
            mapa = " · ".join(f"{f['id']} {fmt_tempo(f['a'])}" for f in pc["frases"] if f["trecho"] == t["k"])
            zs = sorted({s["z"] for s in ss})
            print(f"T{t['k']}  bruto {fmt_tempo(ss[0]['fi'] / fps)}–{fmt_tempo(ss[-1]['fo'] / fps)} → "
                  f"final {fmt_tempo(ss[0]['tl_in'] / fps / vel)}–{fmt_tempo(ss[-1]['tl_out'] / fps / vel)}"
                  + (f" · zoom {'/'.join(fmt_num(z, 2) for z in zs)}" if zs != [1.0] else "")
                  + (f"  ({t['nota']})" if t["nota"] else ""))
            if mapa:
                print(f"     frases no final: {mapa}")
        for a in avisos:
            print(f"Aviso: {a}")
        print("palavras-corte.json gravado (tempo de cada palavra no vídeo cortado; "
              + (f"bordas medidas no {nome})." if pc["medido"] else "bordas previstas: o render mede as reais)."))
        return

    checar_ffmpeg()
    srt, nleg = legenda(pf)
    (pasta / "legenda.srt").write_text(srt, encoding="utf-8")
    xml = xml_premiere(info, segs)
    ET.fromstring(xml.split("\n", 2)[2])   # recusa XML malformado antes de gravar
    (pasta / "premiere.xml").write_text(xml, encoding="utf-8")
    (pasta / "capcut.md").write_text(CAPCUT.format(video="final.mp4" if final else "previa.mp4"), encoding="utf-8")
    gravar_json(dados / "segmentos.json", [{k: s[k] for k in ("fi", "fo", "tl_in", "tl_out", "k")} for s in segs])
    for a in avisos:
        print(f"Aviso: {a}")
    t1 = time.time()
    if not Path(info["arquivo"]).exists():
        sair(f"O vídeo original não está mais em {info['arquivo']}. Volte o arquivo para lá e rode de novo.")
    saida, dur, (W, H), tonemap, rapido, com_cor, centro, pedacos = render(pasta, info, segs, final, c)
    # as bordas reais (quadros contados no que foi renderizado) vão para o palavras-corte.json (contrato 3.2)
    medida, aviso_medida = medir_render(dados, saida.name, segs, fps, vel, saida, pedacos[3] if pedacos else None)
    gravar_json(pasta / "palavras-corte.json", palavras_corte(pf, pal, frases, fps, vel, final_s, saida.name, segs,
                                                              medida))
    deriva = medida["real"][-1] - final_s
    if aviso_medida or abs(deriva) > 0.5 / float(fps):
        print(f"Aviso: bordas medidas no {saida.name}: o fim cai {fmt_num(deriva, 3)} s "
              f"{'depois' if deriva > 0 else 'antes'} do previsto; o palavras-corte.json segue o medido. {aviso_medida}")
    ok = abs(dur - final_s) < 0.15
    print(f"{saida.name}: {fmt_dur(dur)} · {W}×{H} · render em {fmt_num(time.time() - t1)} s"
          + (" (da cópia leve)" if rapido else "")
          + (f" · {pedacos[1]} pedaços, {pedacos[0]} novos ({fmt_num(pedacos[2])} GB em .dados)" if pedacos else "")
          + (" · com cor" if com_cor else "")
          + (f" · recorte 9:16 em {fmt_num(100 * centro)}% da largura" if centro is not None else "")
          + ("" if ok else f" · ATENÇÃO: esperado {fmt_num(final_s, 2)} s"))
    if info["hdr"] and not tonemap:
        print("Aviso: vídeo HDR e este ffmpeg não converte as cores; a prévia pode ficar com cor diferente.")
    print(f"legenda.srt ({nleg} legendas) · premiere.xml ({len(segs)} clipes"
          + (", sem velocidade e zoom" if pedacos else "") + ") · capcut.md · palavras-corte.json")
    print(f"Pronto em {fmt_num(time.time() - t0)} s.")


if __name__ == "__main__":
    main()
