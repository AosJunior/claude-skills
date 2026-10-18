# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""/sonorizar: mixa trilha e efeitos por baixo da voz de um vídeo, a partir do som.json.

Uso:
  uv run "<skill>/scripts/sonorizar.py" "<som.json>" --resumo        confere arquivos, tempos e licenças; não grava nada
  uv run "<skill>/scripts/sonorizar.py" "<som.json>" --trecho 30 50  prévia só desse pedaço (previa-trecho.mp4, rápida)
  uv run "<skill>/scripts/sonorizar.py" "<som.json>" --trecho 0 15 --trilha <som>
                                                                      prévia com outra trilha (previa-<som>.mp4)
  uv run "<skill>/scripts/sonorizar.py" "<som.json>"                 vídeo inteiro, creditos.md, medida e entrega

O formato do som.json está em referencia.md, ao lado do SKILL.md.

A voz é o áudio do próprio vídeo (passa-altas leve e compressor suave). Cada faixa da trilha fica `abaixo_da_voz`
LU abaixo da voz e ainda abaixa sozinha quando há fala (sidechaincompress); na troca, as duas se cruzam. Cada
efeito toca com pico em -12 dBFS + `volume`. A mistura final vai a -14 LUFS (loudnorm em duas passadas) e a
imagem é copiada sem recomprimir.
"""
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (SR, Ancoras, achar_marca, checar_ffmpeg, ff, fmt_num, fmt_tempo, ler_creditos,  # noqa: E402
                   ler_json, medir, rodar, sair, segundos, sondar, utf8)

VOZ_LUFS = -16.0          # a voz é levada a este nível antes da mistura (referência da trilha e dos efeitos)
ALVO_LUFS = -14.0         # mistura final (Reels, TikTok, YouTube)
ALVO_TP = -1.5            # pico verdadeiro máximo
PICO_EFEITO = -12.0       # dBFS do pico de cada efeito com "volume": 0
CRUZAR = 0.5              # troca de faixa sem "cruzar": meio segundo de crossfade
DUCK = "sidechaincompress=threshold=0.04:ratio=3:attack=15:release=500:knee=4"


# ---------------------------------------------------------------- leitura do som.json

def carregar(som_json, trilha_outra=None):
    p = Path(som_json).expanduser().resolve()
    if p.is_dir():
        p = p / "som.json"
    if not p.exists():
        sair(f"Não achei o som.json em {p}.")
    cfg = ler_json(p)
    base = p.parent
    marca = achar_marca(base)
    print(f"Marca: {marca if marca else 'nenhuma'}")

    def caminho(x):
        x = str(x)
        if marca and (x.startswith("marca/") or x.startswith("marca\\")):
            return (marca / x).resolve()
        q = Path(x).expanduser()
        return q if q.is_absolute() else (base / q).resolve()

    erros = []
    video = caminho(cfg.get("video", ""))
    if not video.is_file():
        sair(f"Corrija o som.json:\n- vídeo não encontrado: {video}")
    info = sondar(video)
    if not info["tem_audio"]:
        sair("Esse vídeo não tem som. A /sonorizar precisa da voz no próprio vídeo.")
    dur = info["duracao"]

    # âncoras na fala: palavras-corte.json da /decupar (explícito ou no lugar de sempre)
    pj = caminho(cfg["palavras"]) if cfg.get("palavras") else (base / "../decupagem/palavras-corte.json").resolve()
    if cfg.get("palavras") and not pj.is_file():
        erros.append(f"palavras-corte.json não encontrado: {pj}")
    anc = Ancoras(pj if pj.is_file() else None)

    def T(v, borda="inicio", onde=""):
        try:
            return anc.tempo(v, borda)
        except ValueError as e:
            erros.append(f"{onde}: {e}")
            return None

    # sons e licenças (o que faltar sai de marca/sons/creditos.md)
    cred = creditos_marca(marca)
    sons = {}
    for nome, s in (cfg.get("sons") or {}).items():
        arq = caminho(s.get("arquivo", ""))
        if not arq.is_file():
            erros.append(f"som '{nome}': arquivo não encontrado ({arq})")
        extra = cred.get(arq.name.lower(), {})
        s = {**{k: v for k, v in extra.items() if v}, **{k: v for k, v in s.items() if v not in (None, "")}}
        if not str(s.get("licenca", "")).strip():
            erros.append(f"som '{nome}': falta a licença (de onde veio e com que direito de uso)")
        sons[nome] = {**s, "arquivo": arq}

    # legenda e insercoes.json (para "legenda", "insercao" e "camada")
    fala = None
    if cfg.get("legenda"):
        srt = caminho(cfg["legenda"])
        if srt.is_file():
            fala = palavras_srt(srt)
        else:
            erros.append(f"legenda não encontrada: {srt}")
    ij, insercoes, camadas = None, None, None
    if cfg.get("insercoes"):
        ij = caminho(cfg["insercoes"])
        if ij.is_file():
            d = ler_json(ij)
            insercoes, camadas = d.get("insercoes") or [], d.get("camadas") or []
        else:
            erros.append(f"insercoes.json não encontrado: {ij}")

    # trilha: objeto (uma faixa no vídeo todo) ou lista de faixas com troca
    tr = cfg.get("trilha")
    if trilha_outra:
        if trilha_outra not in sons:
            sair(f"--trilha: o som '{trilha_outra}' não está em \"sons\" do som.json.")
        modelo = (tr[0] if isinstance(tr, list) and tr else tr) or {}
        tr = {"som": trilha_outra, "abaixo_da_voz": modelo.get("abaixo_da_voz", 16)}
    faixas = faixas_da_trilha(tr, sons, dur, T, erros)

    efeitos = []
    for i, e in enumerate(cfg.get("efeitos") or [], 1):
        onde = f"efeito {i}"
        if e.get("som") not in sons:
            erros.append(f"{onde}: o som '{e.get('som')}' não está em \"sons\"")
            continue
        if not str(e.get("motivo", "")).strip():
            erros.append(f"{onde} ({e.get('som')}): falta o motivo (o que acontece na tela ou na fala)")
        t, aviso, ancora = efeito_tempo(e, onde, T, fala, insercoes, camadas, erros)
        if t is None:
            continue
        t += float(e.get("desvio", 0))
        efeitos.append({**e, "t": max(0.0, t), "volume": float(e.get("volume", 0)), "aviso": aviso, "ancora": ancora})

    ent = cfg.get("entrega")
    entrega = None
    if ent:
        pasta = caminho(ent.get("pasta") or "../entrega")
        nome = str(ent.get("nome") or "").strip() or Path(cfg.get("saida") or "video-com-som.mp4").stem
        if not Path(nome).suffix:
            nome += ".mp4"
        if ent.get("legenda"):
            curta = caminho(ent["legenda"])
        else:
            lugares = [ij.parent / "legenda-curta.srt"] if ij else []
            lugares += [video.parent / "legenda-curta.srt", (base / "../insercoes/legenda-curta.srt").resolve()]
            curta = next((x for x in lugares if x.is_file()), None)
        entrega = {"pasta": pasta, "nome": nome, "legenda": curta if curta and curta.is_file() else None}

    if erros:
        sair("Corrija o som.json:\n- " + "\n- ".join(erros))
    saida = caminho(cfg.get("saida") or "video-com-som.mp4")
    return {"pasta": base, "json": p, "video": video, "dur": dur, "saida": saida, "sons": sons, "faixas": faixas,
            "efeitos": efeitos, "entrega": entrega, "palavras": anc.arquivo}


def creditos_marca(marca):
    """marca/sons/creditos.md da pasta de edição -> {nome do arquivo: {titulo, autor, fonte, licenca}}."""
    return ler_creditos(marca / "marca" / "sons" / "creditos.md") if marca else {}


def faixas_da_trilha(tr, sons, dur, T, erros):
    """Lista de faixas com o intervalo que soa [a, b], as rampas e o ponto da música de onde parte."""
    if not tr:
        return []
    lista = [tr] if isinstance(tr, dict) else list(tr)
    brutas = []
    for i, f in enumerate(lista, 1):
        onde = f"trilha, faixa {i}"
        if f.get("som") not in sons:
            erros.append(f"{onde}: o som '{f.get('som')}' não está em \"sons\"")
            return []
        dv = f.get("de", 0 if i == 1 else None)
        de = T(dv, "inicio", onde) if dv is not None else None
        ate = T(f["ate"], "fim", onde) if f.get("ate") is not None else None
        if dv is not None and de is None:
            return []
        if de is None and brutas and brutas[-1]["ate"] is not None:
            de = brutas[-1]["ate"]
        if de is None:
            erros.append(f"{onde}: falta \"de\" (onde esta faixa entra)")
            return []
        brutas.append({**f, "de": max(0.0, de), "ate": ate, "n": i})
    for x, y in zip(brutas, brutas[1:]):
        if y["de"] <= x["de"]:
            erros.append(f"trilha: a faixa {y['n']} entra antes da faixa {x['n']} (ponha em ordem de tempo)")
            return []
    faixas = []
    for i, f in enumerate(brutas):
        prox = brutas[i + 1] if i + 1 < len(brutas) else None
        fim = min(f["ate"], dur) if f["ate"] is not None else dur
        cola = False
        if prox is not None:
            # a troca é no "de" da próxima; um "ate" que acaba antes dela deixa um silêncio entre as duas
            if f["ate"] is None or f["ate"] >= prox["de"] - 0.05:
                fim, cola = prox["de"], True
        if fim - f["de"] < 0.5:
            erros.append(f"trilha, faixa {f['n']}: dura menos de meio segundo ({fmt_tempo(f['de'])} a {fmt_tempo(fim)})")
            return []
        faixas.append({"som": f["som"], "n": f["n"], "de": f["de"], "fim": fim, "cola": cola,
                       "inicio": segundos(f.get("inicio", 0)), "abaixo": float(f.get("abaixo_da_voz", 16)),
                       "fade_in": float(f.get("fade_in", 1)), "fade_out": float(f.get("fade_out", 2)),
                       "cruzar": float(f.get("cruzar", CRUZAR))})
    for i, f in enumerate(faixas):
        ant = faixas[i - 1] if i and faixas[i - 1]["cola"] else None
        c_in = f["cruzar"] if ant else 0.0
        c_out = faixas[i + 1]["cruzar"] if f["cola"] else 0.0
        f["a"] = max(0.0, f["de"] - c_in / 2)
        f["b"] = min(dur, f["fim"] + c_out / 2)
        if ant:
            f["rampa_in"] = (f["a"], f["a"] + c_in, True) if c_in > 0 else None
        else:
            f["rampa_in"] = (f["de"], f["de"] + f["fade_in"], False) if f["fade_in"] > 0 else None
        if f["cola"]:
            f["rampa_out"] = (f["b"] - c_out, f["b"], True) if c_out > 0 else None
        else:
            f["rampa_out"] = (f["fim"] - f["fade_out"], f["fim"], False) if f["fade_out"] > 0 else None
    return faixas


def efeito_tempo(e, onde, T, fala, insercoes, camadas, erros):
    """Tempo de um efeito preso a camada, insercao, legenda, âncora (em) ou t. Devolve (t, aviso, rótulo)."""
    em = e.get("em", "inicio")
    if e.get("camada"):
        if camadas is None:
            erros.append(f"{onde}: usa \"camada\", mas o som.json não diz qual é o insercoes.json")
            return None, "", ""
        cam = next((c for c in camadas if str(c.get("id")) == str(e["camada"])), None)
        if cam is None:
            ids = ", ".join(str(c.get("id")) for c in camadas if c.get("id")) or "nenhuma camada com id"
            erros.append(f"{onde}: não achei a camada «{e['camada']}» no insercoes.json (tem: {ids})")
            return None, "", ""
        rot = f"[camada {e['camada']}" + ("" if em == "inicio" else f" · {em}") + "]"
        if em == "fim":
            return T(cam.get("ate"), "fim", onde), "", rot
        t0 = T(cam.get("de", 0), "inicio", onde)
        if str(em).startswith("recorte"):
            k = int(str(em).partition("#")[2] or 2)
            rec = cam.get("recorte") if isinstance(cam.get("recorte"), list) else []
            if t0 is None or len(rec) < k:
                erros.append(f"{onde}: a camada «{e['camada']}» não tem o {k}º passo de \"recorte\"")
                return None, "", ""
            return t0 + float(rec[k - 1].get("t", 0)), "", rot
        return t0, "", rot
    if e.get("insercao"):
        alvo = " ".join(norm(str(e["insercao"])))
        achou = [x for x in (insercoes or [])
                 if alvo and f" {alvo} " in " " + " ".join(norm(json.dumps(x, ensure_ascii=False))) + " "]
        if not achou:
            erros.append(f"{onde}: não achei a inserção «{e['insercao']}» no insercoes.json")
            return None, "", ""
        aviso = f"«{e['insercao']}» bate com {len(achou)} inserções; usei a primeira" if len(achou) > 1 else ""
        return T(achou[0]["de"], "inicio", onde), aviso, f"[inserção «{e['insercao']}»]"
    if e.get("legenda"):
        if fala is None:
            erros.append(f"{onde}: usa \"legenda\", mas o som.json não diz qual é a legenda.srt")
            return None, "", ""
        t, aviso = ancorar(fala, e["legenda"], em)
        if t is None:
            erros.append(f"{onde}: não achei «{e['legenda']}» na legenda")
        return t, aviso, f"«{e['legenda']}»"
    if e.get("em") not in (None, "inicio", "fim"):
        return T(e["em"], "inicio", onde), "", f"[{e['em']}]"
    if e.get("t") is not None:
        return T(e["t"], "inicio", onde), "", ""
    erros.append(f"{onde}: diga onde ele cai (\"camada\", \"insercao\", \"legenda\", \"em\" ou \"t\")")
    return None, "", ""


def norm(txt):
    t = unicodedata.normalize("NFKD", txt.lower()).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z0-9]+", t)


def palavras_srt(srt):
    """Palavras da legenda com tempo: cada linha reparte o seu tempo entre as palavras, pelo tamanho delas."""
    txt = Path(srt).read_text(encoding="utf-8-sig").replace("\r", "")
    out = []
    for bloco in re.split(r"\n\s*\n", txt.strip()):
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", bloco)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        ws = norm(" ".join(bloco[m.end():].split("\n")))
        tot = sum(len(w) + 1 for w in ws) or 1
        acc = 0
        for w in ws:
            ini = a + (b - a) * acc / tot
            acc += len(w) + 1
            out.append((w, ini, a + (b - a) * acc / tot))
    return out


def ancorar(fala, trecho, em="inicio"):
    """Tempo do início (ou do fim) da primeira vez que `trecho` aparece na legenda; avisa se aparece mais vezes."""
    alvo = norm(trecho)
    if not alvo:
        return None, ""
    achados = [i for i in range(len(fala) - len(alvo) + 1)
               if [w for w, _, _ in fala[i:i + len(alvo)]] == alvo]
    if not achados:
        return None, ""
    i = achados[0]
    t = fala[i + len(alvo) - 1][2] if em == "fim" else fala[i][1]
    return t, (f"«{trecho}» aparece {len(achados)} vezes; usei a primeira" if len(achados) > 1 else "")


# ---------------------------------------------------------------- mistura

def envelope(f, s0):
    """Expressão do volume (0 a 1) da faixa no tempo local t, que começa em s0 no vídeo: rampas de entrada e saída.
    Fade simples é linear; na troca entre faixas a rampa é de potência igual (seno), para o meio não afundar."""
    partes = []
    for lado in ("rampa_in", "rampa_out"):
        if not f[lado]:
            continue
        a, b, cruza = f[lado]
        x = (f"(t+{s0:.4f}-{a:.4f})" if lado == "rampa_in" else f"({b:.4f}-t-{s0:.4f})") + f"/{max(b - a, 0.001):.4f}"
        x = f"clip({x},0,1)"
        partes.append(f"sin({x}*PI/2)" if cruza else x)
    return "*".join(partes) or "1"


def montar(c, ini, dur):
    """Entradas e filter_complex da mistura da janela [ini, ini+dur] do vídeo. Rótulos: [voz] [trilha] [efeitos] [mix]."""
    ent = ["-ss", f"{ini:.3f}", "-t", f"{dur:.3f}", "-i", str(c["video"])]
    g = [f"[0:a:0]aresample={SR},aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,highpass=f=70,"
         f"acompressor=threshold=-22dB:ratio=2.5:attack=8:release=200:makeup=2,volume={c['ganho_voz']:.2f}dB,"
         f"aformat=sample_rates=48000:channel_layouts=stereo,apad,atrim=0:{dur:.3f},asplit=3[voz][vozkey][vozout]"]
    partes = ["[voz]"]
    k = 1
    if c["faixas"]:
        rot = []
        for f in c["faixas"]:
            s0, s1 = max(f["a"], ini), min(f["b"], ini + dur)
            if s1 - s0 < 0.01:
                continue
            seek = (f["inicio"] + (s0 - f["a"])) % f["dur_arquivo"]
            n = s1 - s0
            ent += ["-stream_loop", "-1", "-ss", f"{seek:.3f}", "-t", f"{n:.3f}", "-i", str(c["sons"][f["som"]]["arquivo"])]
            g.append(f"[{k}:a:0]aresample={SR},aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                     f"atrim=0:{n:.3f},asetpts=N/SR/TB,volume={f['ganho']:.2f}dB,asetnsamples=n=480,"
                     f"volume=volume='{envelope(f, s0)}':eval=frame,adelay={int(round((s0 - ini) * 1000))}:all=1[f{k}]")
            rot.append(f"[f{k}]")
            k += 1
        if rot:
            g.append("".join(rot) + (f"amix=inputs={len(rot)}:normalize=0:duration=longest," if len(rot) > 1 else "")
                     + f"apad,atrim=0:{dur:.3f}[tcru]")
        else:
            g.append(f"anullsrc=r={SR}:cl=stereo,atrim=0:{dur:.3f}[tcru]")
        g.append(f"[tcru][vozkey]{DUCK}[trilha]")
        partes.append("[trilha]")
    else:
        g.append("[vozkey]anullsink")
    evs = [e for e in c["efeitos"] if ini - 0.05 <= e["t"] < ini + dur]
    rot = []
    for e in evs:
        s = c["sons"][e["som"]]
        ent += ["-i", str(s["arquivo"])]
        ms = int(round(max(0.0, e["t"] - ini) * 1000))
        ganho = PICO_EFEITO + e["volume"] - c["picos"][e["som"]]
        g.append(f"[{k}:a:0]aresample={SR},aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume={ganho:.2f}dB,"
                 f"adelay={ms}:all=1[e{k}]")
        rot.append(f"[e{k}]")
        k += 1
    if rot:
        g.append("".join(rot) + f"amix=inputs={len(rot)}:normalize=0:duration=longest,apad,atrim=0:{dur:.3f}[efeitos]")
    else:
        g.append(f"anullsrc=r={SR}:cl=stereo,atrim=0:{dur:.3f}[efeitos]")
    partes.append("[efeitos]")
    g.append("".join(partes) + f"amix=inputs={len(partes)}:normalize=0:duration=first,"
             f"alimiter=limit=0.89:level=disabled,atrim=0:{dur:.3f}[mix]")
    return ent, ";".join(g), evs


def preparar(c):
    """Ganhos fixos: voz a VOZ_LUFS, cada faixa `abaixo_da_voz` LU abaixo (medida no pedaço que toca), pico de cada efeito."""
    v = medir(entradas=["-i", str(c["video"])],
              filtro=f"[0:a:0]aresample={SR},aformat=channel_layouts=mono,highpass=f=70,"
                     "acompressor=threshold=-22dB:ratio=2.5:attack=8:release=200:makeup=2[m]")
    if v["lufs"] < -70:
        sair("O vídeo está sem voz (ou mudo). Confira se é o arquivo certo.")
    c["ganho_voz"] = VOZ_LUFS - v["lufs"]
    for f in c["faixas"]:
        arq = c["sons"][f["som"]]["arquivo"]
        f["dur_arquivo"] = sondar(arq)["duracao"]
        t0 = f["inicio"] % f["dur_arquivo"]
        m = medir(entradas=["-stream_loop", "-1", "-ss", f"{t0:.3f}", "-t", f"{min(f['b'] - f['a'], 600):.3f}",
                            "-i", str(arq)], filtro="[0:a:0]anull[m]")
        f["ganho"] = (VOZ_LUFS - f["abaixo"]) - m["lufs"]
    c["picos"] = {}
    for nome in {e["som"] for e in c["efeitos"]}:
        c["picos"][nome] = medir(c["sons"][nome]["arquivo"])["pico"]


def resumo(c):
    dur = c["dur"]
    print(f"Vídeo: {c['video'].name} · {fmt_tempo(dur)}")
    print(f"Âncoras na fala: {c['palavras'] if c['palavras'] else 'sem palavras-corte.json (só segundos e legenda)'}")
    if not c["faixas"]:
        print("Trilha: nenhuma")
    for f in c["faixas"]:
        s = c["sons"][f["som"]]
        d = sondar(s["arquivo"])["duracao"]
        volta = " · ATENÇÃO: a música acaba antes e recomeça do início; confira a emenda" \
            if d - f["inicio"] < f["b"] - f["a"] else ""
        troca = f" · troca cruzando {fmt_num(f['cruzar'], 2)} s" if f["n"] > 1 and f["a"] < f["de"] else ""
        print(f"Trilha {f['n']}: {fmt_tempo(f['de'])} a {fmt_tempo(f['fim'])}  {s.get('titulo') or s['arquivo'].name}"
              f" (desde {fmt_tempo(f['inicio'])} da música), {fmt_num(f['abaixo'], 0)} LU abaixo da voz{troca}{volta}")
    print(f"Efeitos: {len(c['efeitos'])}")
    ant = None
    for e in sorted(c["efeitos"], key=lambda x: x["t"]):
        aviso = "  ATENÇÃO: depois do fim do vídeo" if e["t"] >= dur else ""
        if ant is not None and e["t"] - ant < 5:
            aviso += "  ATENÇÃO: menos de 5 s depois do anterior"
        if e.get("aviso"):
            aviso += "  ATENÇÃO: " + e["aviso"]
        ancora = f"{e['ancora']} " if e.get("ancora") else ""
        print(f"  {fmt_tempo(e['t'])}  {e['som']:<14} {ancora}{e['motivo']}{aviso}")
        ant = e["t"]
    sem_uso = set(c["sons"]) - {e["som"] for e in c["efeitos"]} - {f["som"] for f in c["faixas"]}
    if sem_uso:
        print("Sons listados sem uso (saem dos créditos): " + ", ".join(sorted(sem_uso)))
    if c["entrega"]:
        en = c["entrega"]
        print(f"Entrega: {en['pasta'] / en['nome']} + "
              + ("legenda-curta.srt" if en["legenda"] else "sem legenda-curta.srt (a /inserir não gravou uma)")
              + " + creditos.md + som.json")


def momentaneo(arq):
    """Loudness momentâneo (janela de 400 ms) a cada 100 ms."""
    r = rodar(["ffmpeg", "-hide_banner", "-nostdin", "-nostats", "-v", "verbose", "-i", arq,
               "-af", "ebur128=framelog=verbose", "-f", "null", "-"])
    return [float(x) for x in re.findall(r"M:\s*(-?[0-9.]+)", r.stderr)]


def sob_a_fala(voz, trilha):
    """Mediana de (voz - trilha) nos momentos com fala, e da trilha nas pausas, em LU."""
    v, t = momentaneo(voz), momentaneo(trilha)
    n = min(len(v), len(t))
    fala = sorted(v[i] - t[i] for i in range(n) if v[i] > VOZ_LUFS - 8)
    pausas = sorted(VOZ_LUFS - t[i] for i in range(n) if v[i] < VOZ_LUFS - 25 and t[i] > -70)
    med = lambda xs: xs[len(xs) // 2] if xs else None  # noqa: E731
    return med(fala), med(pausas)


def creditos(c, destino):
    usados = list(dict.fromkeys([f["som"] for f in c["faixas"]] + sorted({e["som"] for e in c["efeitos"]})))
    linhas = [f"# Créditos do som: {c['saida'].name}", "",
              "| Som | Arquivo | Título e autor | Fonte | Licença |", "|---|---|---|---|---|"]
    for n in usados:
        s = c["sons"][n]
        tit = " · ".join(x for x in (s.get("titulo"), s.get("autor")) if x)
        linhas.append(f"| {n} | `{s['arquivo'].name}` | {tit or '—'} | {s.get('fonte', '—')} | {s['licenca']} |")
    if c["faixas"]:
        linhas += ["", "## Trilha", "", "| De | Até | Som | Desde (na música) |", "|---|---|---|---|"]
        linhas += [f"| {fmt_tempo(f['de'])} | {fmt_tempo(f['fim'])} | {f['som']} | {fmt_tempo(f['inicio'])} |"
                   for f in c["faixas"]]
    linhas += ["", "## Efeitos e motivo", "", "| Tempo | Efeito | Motivo |", "|---|---|---|"]
    linhas += [f"| {fmt_tempo(e['t'])} | {e['som']} | {e['motivo']} |" for e in sorted(c["efeitos"], key=lambda x: x["t"])]
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def entregar(c, creditos_md):
    en = c["entrega"]
    en["pasta"].mkdir(parents=True, exist_ok=True)
    copias = [(c["saida"], en["nome"]), (creditos_md, "creditos.md"), (c["json"], "som.json")]
    if en["legenda"]:
        copias.insert(1, (en["legenda"], "legenda-curta.srt"))
    print(f"\nEntrega: {en['pasta']}")
    for origem, nome in copias:
        shutil.copyfile(origem, en["pasta"] / nome)
        print(f"  {nome}")
    if not en["legenda"]:
        print("  (sem legenda-curta.srt: a /inserir não gravou uma)")


def main():
    utf8()
    checar_ffmpeg()
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        sair(__doc__)
    outra = a[a.index("--trilha") + 1] if "--trilha" in a and a.index("--trilha") + 1 < len(a) else None
    c = carregar(a[0], outra)
    dur = c["dur"]
    resumo(c)
    if "--resumo" in a:
        return
    ini, fim = 0.0, dur
    trecho = "--trecho" in a
    if trecho:
        i = a.index("--trecho")
        try:
            ini, fim = segundos(a[i + 1]), min(dur, segundos(a[i + 2]))
        except (IndexError, ValueError):
            sair("Use: --trecho <início> <fim>, por exemplo --trecho 00:30 00:50")
    elif outra:
        sair("--trilha serve só para prévia: use junto com --trecho <início> <fim>.")
    janela = fim - ini
    preparar(c)
    dados = c["pasta"] / ".dados"
    dados.mkdir(exist_ok=True)

    ent, grafo, evs = montar(c, ini, janela)
    # 1a passada: mede a mistura; 2a: grava com o loudnorm linear (acerta o LUFS sem "bombear" a trilha)
    r = rodar(["ffmpeg", "-hide_banner", "-nostdin", *ent, "-filter_complex",
               grafo + f";[mix]loudnorm=I={ALVO_LUFS}:TP={ALVO_TP}:LRA=11:print_format=json[o];[vozout]anullsink",
               "-map", "[o]", "-f", "null", "-"])
    try:
        j = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    except ValueError:
        sair("O ffmpeg não conseguiu medir a mistura:\n" + r.stderr.strip()[-1500:])
    ln = (f"loudnorm=I={ALVO_LUFS}:TP={ALVO_TP}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    mix = dados / ("mix-trecho.wav" if trecho else "mix.wav")
    # a voz e a trilha já abaixada saem também em separado: é a medida de "trilha abaixo da voz"
    tem_trilha = bool(c["faixas"])
    grafo2 = grafo + f";[mix]{ln},aresample={SR},atrim=0:{janela:.3f}[o]"
    if tem_trilha:
        grafo2 = grafo2.replace(f"{DUCK}[trilha]", f"{DUCK},asplit=2[trilha][trilhaout]")
    mapas = ["-map", "[o]", "-c:a", "pcm_s16le", str(mix), "-map", "[vozout]", "-c:a", "pcm_s16le",
             str(dados / "stem-voz.wav")]
    if tem_trilha:
        mapas += ["-map", "[trilhaout]", "-c:a", "pcm_s16le", str(dados / "stem-trilha.wav")]
    ff([*ent, "-filter_complex", grafo2, *mapas])

    if trecho:
        saida = c["pasta"] / (f"previa-{outra}.mp4" if outra else "previa-trecho.mp4")
        venc = ["-c:v", "h264_videotoolbox", "-b:v", "4M"] if sys.platform == "darwin" else \
            ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"]
        ff(["-ss", f"{ini:.3f}", "-t", f"{janela:.3f}", "-i", str(c["video"]), "-i", str(mix), "-map", "0:v:0",
            "-map", "1:a:0", "-vf", "scale=-2:'min(1280,ih)'", *venc, "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(saida)])
    else:
        saida = c["saida"]
        saida.parent.mkdir(parents=True, exist_ok=True)
        ff(["-i", str(c["video"]), "-i", str(mix), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "256k", "-ar", str(SR), "-t", f"{dur:.3f}", "-movflags", "+faststart", str(saida)])
        creditos(c, saida.parent / "creditos.md")

    m = medir(saida)
    print(f"\nPronto: {saida}")
    print(f"Volume final: {fmt_num(m['lufs'])} LUFS (alvo {fmt_num(ALVO_LUFS)}) · pico {fmt_num(m['true_peak'])} dBTP")
    if tem_trilha:
        sob, pausa = sob_a_fala(dados / "stem-voz.wav", dados / "stem-trilha.wav")
        if sob is not None:
            print(f"Trilha embaixo da fala: {fmt_num(sob)} LU abaixo da voz (confortável: de 20 a 30)")
        if pausa is not None:
            print(f"Trilha nas pausas: {fmt_num(pausa)} LU abaixo do nível da voz")
    if abs(m["lufs"] - ALVO_LUFS) > 1:
        print("ATENÇÃO: o volume final ficou mais de 1 LU longe do alvo. Rode de novo uma vez; se repetir, avise.")
    if evs:
        print(f"Efeitos neste pedaço: {len(evs)}")
    if not trecho:
        print(f"Créditos: {saida.parent / 'creditos.md'}")
        if c["entrega"]:
            entregar(c, saida.parent / "creditos.md")


if __name__ == "__main__":
    main()
