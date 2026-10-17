# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""/decupar, etapas 2 a 5: aplica o cortes.json e entrega prévia, legenda, XML e guia do CapCut.

Uso:
  uv run "<skill>/scripts/cortar.py" "<pasta decupagem>" --resumo   só confere: durações e tempos finais
  uv run "<skill>/scripts/cortar.py" "<pasta decupagem>"            legenda.srt, premiere.xml, capcut.md, previa.mp4
  uv run "<skill>/scripts/cortar.py" "<pasta decupagem>" --final    o mesmo, com final.mp4 (1080 no lado curto)
Aceita também o caminho do vídeo no lugar da pasta.

cortes.json (o Claude escreve; a ordem dos trechos é a ordem do vídeo final):
  {"pausa_max": 0.35,
   "trechos": [{"de": "F2", "ate": "F6", "nota": "abertura"},
               {"de": "01:47,30", "ate": 112.4, "nota": "..."},
               {"de": "F30", "ate": "02:41,00", "exato": true, "nota": "fica o sorriso no fim"}]}
  de/ate: frase ("F12": início/fim dela), tempo "mm:ss,cc" ou segundos, sempre do vídeo bruto.
  Fica a palavra cujo meio cai dentro do trecho; pausas maiores que pausa_max saem sozinhas.
  "exato": true usa de/ate como estão (sem ajustar às palavras nem tirar pausas).
"""
import json
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (CAP_PALAVRA, MARCAS_DISPLAY_MATRIX, achar_pasta, checar_ffmpeg, encoder, fmt_dur,  # noqa: E402
                   fmt_num, fmt_tempo, gravar_json, hwaccel, ler_json, proxy_valido, rodar, sair, tamanho, utf8)
from cor import filtro_da_pasta  # noqa: E402

PAD_IN, PAD_OUT = 0.10, 0.18      # folga antes e depois da fala (valores do pipeline de edição)
RESPIRO_OUT, RESPIRO_IN = 0.12, 0.06   # silêncio que fica depois e antes da fala numa pausa interna cortada
VAZIA_MIN = 0.15                  # som sem palavra (pedaço vazio do Whisper) a partir disso sai
LEG_CARACTERES, LEG_PALAVRAS = 24, 5


# ---------------------------------------------------------------- leitura do cortes.json

def ler_tempo(v, frases, lado, onde):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    s = str(v).strip()
    m = re.fullmatch(r"[Ff](\d+)", s)
    if m:
        f = frases.get(f"F{int(m.group(1))}")
        if not f:
            sair(f"cortes.json, {onde}: não existe a frase {s} na transcricao.txt.")
        return f["ini"] if lado == "de" else f["fim"]
    try:
        partes = [float(p) for p in s.replace(",", ".").split(":")]
        if 1 <= len(partes) <= 3:
            return sum(p * 60 ** i for i, p in enumerate(reversed(partes)))
    except ValueError:
        pass
    sair(f"cortes.json, {onde}: não entendi o tempo {v!r}. Use \"F12\", \"01:23,45\" ou segundos (83.45).")


def ler_cortes(pasta, frases, dur):
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
    out = []
    for k, t in enumerate(trechos, 1):
        if not isinstance(t, dict) or "de" not in t or "ate" not in t:
            sair(f"cortes.json, trecho {k}: cada trecho precisa de \"de\" e \"ate\".")
        de = max(0.0, ler_tempo(t["de"], frases, "de", f"trecho {k}"))
        ate = min(dur, ler_tempo(t["ate"], frases, "ate", f"trecho {k}"))
        if ate <= de:
            sair(f"cortes.json, trecho {k}: o fim ({fmt_tempo(ate)}) vem antes do início ({fmt_tempo(de)}).")
        out.append({"k": k, "de": de, "ate": ate, "exato": bool(t.get("exato")), "nota": str(t.get("nota") or "")})
    return float(c.get("pausa_max", 0.35)), out


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


def segmentos(trechos, pal, pausa, info, sil=None):
    """Trechos -> segmentos em quadros do bruto, na ordem final: [{fi, fo, k, idx}]."""
    fps = Fraction(info["fps_num"], info["fps_den"])
    dur = info["duracao"]
    fins = [fim_real(w) for w in pal]
    brutos, avisos = [], []
    for t in trechos:
        if t["exato"]:
            idx = [i for i, w in enumerate(pal) if t["de"] <= (w["ini"] + fins[i]) / 2 <= t["ate"]]
            brutos.append((t["de"], t["ate"], t["k"], idx))
            continue
        idx = [i for i, w in enumerate(pal) if t["de"] <= (w["ini"] + fins[i]) / 2 <= t["ate"]]
        if not idx:
            avisos.append(f"T{t['k']} não tem fala; ficou inteiro ({fmt_tempo(t['de'])}–{fmt_tempo(t['ate'])}).")
            brutos.append((t["de"], t["ate"], t["k"], []))
            continue
        grupos = [[idx[0]]]
        for i in idx[1:]:
            if i != grupos[-1][-1] + 1 or pal[i]["ini"] - fins[i - 1] > pausa:
                grupos.append([i])
            else:
                grupos[-1].append(i)
        for g in grupos:
            a, b = pal[g[0]]["ini"], fins[g[-1]]
            lim_a = (fins[g[0] - 1] + a) / 2 if g[0] > 0 else 0.0
            lim_b = (b + pal[g[-1] + 1]["ini"]) / 2 if g[-1] + 1 < len(pal) else dur
            for x, y in limpar(max(0.0, a - PAD_IN, lim_a), min(dur, b + PAD_OUT, lim_b), pal, g, sil, pausa):
                brutos.append((x, y, t["k"], g))
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
    for s in segs:
        s["tl_in"], s["tl_out"] = tl, tl + s["fo"] - s["fi"]
        tl = s["tl_out"]
    for a in range(len(trechos)):
        for b in range(a + 1, len(trechos)):
            u, v = trechos[a], trechos[b]
            if min(u["ate"], v["ate"]) - max(u["de"], v["de"]) > 0.3:
                avisos.append(f"T{u['k']} e T{v['k']} usam o mesmo pedaço do bruto: a fala vai aparecer duas vezes.")
    return segs, avisos


def palavras_finais(segs, pal, fps):
    out = []
    for s in segs:
        a, b = s["fi"] / fps, s["fo"] / fps
        base, lo, hi = s["tl_in"] / fps - a, s["tl_in"] / fps, s["tl_out"] / fps
        for i in s["idx"]:
            w = pal[i]
            if w["w"] and a <= (w["ini"] + fim_real(w)) / 2 <= b:
                out.append((w["w"], min(max(w["ini"] + base, lo), hi), min(max(fim_real(w) + base, lo), hi), i))
    return out


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
    giro = 0 if info["marca"] in MARCAS_DISPLAY_MATRIX else -info["rotacao"]
    motion = ("<filter><effect><name>Basic Motion</name><effectid>basic</effectid><effectcategory>motion"
              "</effectcategory><effecttype>motion</effecttype><mediatype>video</mediatype>"
              '<parameter authoringApp="PremierePro"><parameterid>rotation</parameterid><name>Rotation</name>'
              f"<valuemin>-8640</valuemin><valuemax>8640</valuemax><value>{giro}</value></parameter>"
              "</effect></filter>") if giro else ""
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
        v.append(item(f"v-{k}", s, k, "<compositemode>normal</compositemode>" + motion))
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


def render(pasta, info, segs, final):
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
    # tentativas: com aceleração de vídeo, sem ela, e (vídeo HDR) sem a conversão de cor
    tentativas = [(hw, tom) for hw in ([hwaccel(), []] if hwaccel() else [[]])] + ([([], "")] if tom else [])
    for hw, tom_agora in tentativas:
        tonemap = bool(tom_agora)
        cor = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"] if tonemap else []
        fim_cmd = ["-map", "[vo]", "-map", "[ao]", *encoder("final" if final else "previa"), *cor,
                   "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", parcial]
        entradas, fc = montar(hw, tom_agora)
        grafo.write_text(fc, encoding="utf-8")
        for opcao in ("-/filter_complex", "-filter_complex_script"):   # ffmpeg 7+ / ffmpeg antigo
            r = rodar(["ffmpeg", "-hide_banner", "-v", "error", "-y", *entradas, opcao, grafo, *fim_cmd])
            if "nrecognized option" not in r.stderr:
                break
        if r.returncode == 0:
            break
    if r.returncode != 0:
        parcial.unlink(missing_ok=True)
        sair(f"O render falhou. Fim da mensagem do ffmpeg:\n{r.stderr[-1500:]}")
    parcial.replace(saida)
    p = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", saida])
    return saida, float(p.stdout.strip() or 0), (W, H), tonemap, bool(px), bool(filtro_cor), centro


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
    pausa, trechos = ler_cortes(pasta, frases, info["duracao"])
    segs, avisos = segmentos(trechos, pal, pausa, info, sil)
    if not segs:
        sair("Os trechos do cortes.json não deixaram nada no vídeo.")
    final_s = float(segs[-1]["tl_out"] / fps)
    pf = palavras_finais(segs, pal, fps)

    if "--resumo" in sys.argv:
        antes = info["duracao"]
        dentro = sum(float((max(s["fo"] for s in segs if s["k"] == t["k"]) - min(s["fi"] for s in segs if s["k"] == t["k"])
                            - sum(s["fo"] - s["fi"] for s in segs if s["k"] == t["k"])) / fps)
                     for t in trechos if any(s["k"] == t["k"] for s in segs))
        print(f"Antes: {fmt_dur(antes)} · Depois: {fmt_dur(final_s)} "
              f"(saem {fmt_dur(max(0.0, antes - final_s))}, {round(100 * max(0.0, antes - final_s) / antes)}%)")
        print(f"Emendas: {len(segs) - 1} · pausas tiradas dentro dos trechos: {fmt_num(dentro)} s · "
              f"o resto saiu com os trechos descartados")
        inicio_frase = {}
        for w, t, _, i in pf:
            inicio_frase.setdefault(i, t)
        print("Trechos na ordem do vídeo final (bruto → final):")
        for t in trechos:
            ss = [s for s in segs if s["k"] == t["k"]]
            if not ss:
                print(f"T{t['k']}: ficou vazio")
                continue
            fr = [f for f in frases.values() if f["i0"] in inicio_frase and any(f["i0"] in s["idx"] for s in ss)]
            mapa = " · ".join(f"{f['id']} {fmt_tempo(inicio_frase[f['i0']])}" for f in fr)
            print(f"T{t['k']}  bruto {fmt_tempo(ss[0]['fi'] / fps)}–{fmt_tempo(ss[-1]['fo'] / fps)} → "
                  f"final {fmt_tempo(ss[0]['tl_in'] / fps)}–{fmt_tempo(ss[-1]['tl_out'] / fps)}"
                  + (f"  ({t['nota']})" if t["nota"] else ""))
            if mapa:
                print(f"     frases no final: {mapa}")
        for a in avisos:
            print(f"Aviso: {a}")
        return

    checar_ffmpeg()
    srt, nleg = legenda(pf)
    (pasta / "legenda.srt").write_text(srt, encoding="utf-8")
    xml = xml_premiere(info, segs)
    ET.fromstring(xml.split("\n", 2)[2])   # recusa XML malformado antes de gravar
    (pasta / "premiere.xml").write_text(xml, encoding="utf-8")
    final = "--final" in sys.argv
    (pasta / "capcut.md").write_text(CAPCUT.format(video="final.mp4" if final else "previa.mp4"), encoding="utf-8")
    gravar_json(dados / "segmentos.json", [{k: s[k] for k in ("fi", "fo", "tl_in", "tl_out", "k")} for s in segs])
    for a in avisos:
        print(f"Aviso: {a}")
    t1 = time.time()
    if not Path(info["arquivo"]).exists():
        sair(f"O vídeo original não está mais em {info['arquivo']}. Volte o arquivo para lá e rode de novo.")
    saida, dur, (W, H), tonemap, rapido, com_cor, centro = render(pasta, info, segs, final)
    ok = abs(dur - final_s) < 0.15
    print(f"{saida.name}: {fmt_dur(dur)} · {W}×{H} · render em {fmt_num(time.time() - t1)} s"
          + (" (da cópia leve)" if rapido else "")
          + (" · com cor" if com_cor else "")
          + (f" · recorte 9:16 em {fmt_num(100 * centro)}% da largura" if centro is not None else "")
          + ("" if ok else f" · ATENÇÃO: esperado {fmt_num(final_s, 2)} s"))
    if info["hdr"] and not tonemap:
        print("Aviso: vídeo HDR e este ffmpeg não converte as cores; a prévia pode ficar com cor diferente.")
    print(f"legenda.srt ({nleg} legendas) · premiere.xml ({len(segs)} clipes) · capcut.md")
    print(f"Pronto em {fmt_num(time.time() - t0)} s.")


if __name__ == "__main__":
    main()
