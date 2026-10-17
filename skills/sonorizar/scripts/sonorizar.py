# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""/sonorizar: mixa trilha e efeitos por baixo da voz de um vídeo, a partir do som.json.

Uso:
  uv run "<skill>/scripts/sonorizar.py" "<som.json>" --resumo        confere arquivos, tempos e licenças; não grava nada
  uv run "<skill>/scripts/sonorizar.py" "<som.json>" --trecho 30 50  prévia só desse pedaço (previa-trecho.mp4, rápida)
  uv run "<skill>/scripts/sonorizar.py" "<som.json>"                 vídeo inteiro, creditos.md e a medida do som

som.json (o Claude escreve; caminhos relativos à pasta do som.json; tempos em segundos ou "mm:ss,cc"):
  {"video": "../decupagem/previa.mp4", "saida": "video-com-som.mp4",
   "sons": {"trilha": {"arquivo": "trilha.wav", "titulo": "...", "autor": "...", "fonte": "Epidemic Sound",
                       "licenca": "assinatura Epidemic Sound da conta X"},
            "clique": {"arquivo": "sfx/clique.wav", "fonte": "arquivo da pessoa", "licenca": "..."}},
   "trilha": {"som": "trilha", "inicio": 0, "abaixo_da_voz": 16, "fade_in": 1, "fade_out": 2},
   "legenda": "../decupagem/legenda.srt",
   "efeitos": [{"legenda": "mais de 100 mil", "som": "clique", "volume": -3, "motivo": "o número entra na tela"},
               {"legenda": "pronto, acabou", "em": "fim", "som": "piada", "motivo": "fecha a piada"},
               {"t": "00:12,40", "som": "clique", "motivo": "o print entra num momento sem fala"}]}
  Efeito com "legenda" cai no início (ou no "fim") desse trecho da fala, achado na legenda.srt; se o vídeo for
  cortado de novo, basta a legenda nova e o efeito acompanha a fala. "desvio" (s) adianta ou atrasa.
  Com "insercoes": "<insercoes.json da /inserir>", o efeito {"insercao": "+100 mil", ...} cai no "de" da inserção
  que tem esse texto (número, título, marca...).

A voz é o áudio do próprio vídeo (passa-altas leve e compressor suave). A trilha fica `abaixo_da_voz` LU abaixo
da voz e ainda abaixa sozinha quando há fala (sidechaincompress). Cada efeito toca com pico em -12 dBFS + `volume`.
A mistura final vai a -14 LUFS (loudnorm em duas passadas) e a imagem é copiada sem recomprimir.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (SR, checar_ffmpeg, ff, fmt_num, fmt_tempo, ler_json, medir, rodar, sair, segundos,  # noqa: E402
                   sondar, utf8)

VOZ_LUFS = -16.0          # a voz é levada a este nível antes da mistura (referência da trilha e dos efeitos)
ALVO_LUFS = -14.0         # mistura final (Reels, TikTok, YouTube)
ALVO_TP = -1.5            # pico verdadeiro máximo
PICO_EFEITO = -12.0       # dBFS do pico de cada efeito com "volume": 0
DUCK = "sidechaincompress=threshold=0.04:ratio=3:attack=15:release=500:knee=4"


def carregar(som_json):
    p = Path(som_json).expanduser().resolve()
    if p.is_dir():
        p = p / "som.json"
    if not p.exists():
        sair(f"Não achei o som.json em {p}.")
    cfg = ler_json(p)
    base = p.parent

    def caminho(x):
        q = Path(str(x)).expanduser()
        return q if q.is_absolute() else (base / q).resolve()

    erros = []
    video = caminho(cfg.get("video", ""))
    if not video.is_file():
        erros.append(f"vídeo não encontrado: {video}")
    sons = {}
    for nome, s in (cfg.get("sons") or {}).items():
        arq = caminho(s.get("arquivo", ""))
        if not arq.is_file():
            erros.append(f"som '{nome}': arquivo não encontrado ({arq})")
        if not str(s.get("licenca", "")).strip():
            erros.append(f"som '{nome}': falta a licença (de onde veio e com que direito de uso)")
        sons[nome] = {**s, "arquivo": arq}
    tr = cfg.get("trilha")
    if tr and tr.get("som") not in sons:
        erros.append(f"trilha: o som '{tr.get('som')}' não está em \"sons\"")
    fala = None
    if cfg.get("legenda"):
        srt = caminho(cfg["legenda"])
        if srt.is_file():
            fala = palavras_srt(srt)
        else:
            erros.append(f"legenda não encontrada: {srt}")
    insercoes = None
    if cfg.get("insercoes"):
        ij = caminho(cfg["insercoes"])
        if ij.is_file():
            insercoes = ler_json(ij).get("insercoes") or []
        else:
            erros.append(f"insercoes.json não encontrado: {ij}")
    efeitos = []
    for i, e in enumerate(cfg.get("efeitos") or [], 1):
        if e.get("som") not in sons:
            erros.append(f"efeito {i}: o som '{e.get('som')}' não está em \"sons\"")
            continue
        if not str(e.get("motivo", "")).strip():
            erros.append(f"efeito {i} ({e.get('som')}): falta o motivo (o que acontece na tela ou na fala)")
        if e.get("insercao"):
            alvo = " ".join(norm(str(e["insercao"])))
            achou = [x for x in (insercoes or [])
                     if alvo and f" {alvo} " in " " + " ".join(norm(json.dumps(x, ensure_ascii=False))) + " "]
            if not achou:
                erros.append(f"efeito {i}: não achei a inserção «{e['insercao']}» no insercoes.json")
                continue
            t = segundos(achou[0]["de"]) + float(e.get("desvio", 0))
            aviso = f"«{e['insercao']}» bate com {len(achou)} inserções; usei a primeira" if len(achou) > 1 else ""
        elif e.get("legenda"):
            if fala is None:
                erros.append(f"efeito {i}: usa \"legenda\", mas o som.json não diz qual é a legenda.srt")
                continue
            t, aviso = ancorar(fala, e["legenda"], e.get("em", "inicio"))
            if t is None:
                erros.append(f"efeito {i}: não achei «{e['legenda']}» na legenda")
                continue
            t += float(e.get("desvio", 0))
        else:
            t, aviso = segundos(e["t"]), ""
        efeitos.append({**e, "t": max(0.0, t), "volume": float(e.get("volume", 0)), "aviso": aviso})
    if erros:
        sair("Corrija o som.json:\n- " + "\n- ".join(erros))
    saida = caminho(cfg.get("saida") or "video-com-som.mp4")
    return {"pasta": base, "video": video, "saida": saida, "sons": sons, "trilha": tr, "efeitos": efeitos}


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


def montar(c, ini, dur):
    """Entradas e filter_complex da mistura da janela [ini, ini+dur] do vídeo. Rótulos: [voz] [trilha] [efeitos] [mix]."""
    ent = ["-ss", f"{ini:.3f}", "-t", f"{dur:.3f}", "-i", str(c["video"])]
    g = [f"[0:a:0]aresample={SR},aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,highpass=f=70,"
         f"acompressor=threshold=-22dB:ratio=2.5:attack=8:release=200:makeup=2,volume={c['ganho_voz']:.2f}dB,"
         f"aformat=sample_rates=48000:channel_layouts=stereo,apad,atrim=0:{dur:.3f},asplit=3[voz][vozkey][vozout]"]
    partes = ["[voz]"]
    k = 1
    tr = c["trilha"]
    if tr:
        s = c["sons"][tr["som"]]
        t0 = (segundos(tr.get("inicio", 0)) + ini) % c["dur_trilha"]
        ent += ["-stream_loop", "-1", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", str(s["arquivo"])]
        fi, fo = float(tr.get("fade_in", 1)), float(tr.get("fade_out", 2))
        fades = ""
        if ini <= 0.01 and fi > 0:
            fades += f",afade=t=in:st=0:d={fi}"
        if c["ate_o_fim"] and fo > 0:
            fades += f",afade=t=out:st={max(0.0, dur - fo):.3f}:d={fo}"
        g.append(f"[{k}:a:0]aresample={SR},aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,atrim=0:{dur:.3f},"
                 f"asetpts=N/SR/TB,volume={c['ganho_trilha']:.2f}dB{fades}[tcru]")
        g.append(f"[tcru][vozkey]{DUCK}[trilha]")
        partes.append("[trilha]")
        k += 1
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


def preparar(c, dur_video):
    """Ganhos fixos: voz a VOZ_LUFS, trilha `abaixo_da_voz` LU abaixo, pico de cada efeito."""
    v = medir(entradas=["-i", str(c["video"])],
              filtro=f"[0:a:0]aresample={SR},aformat=channel_layouts=mono,highpass=f=70,"
                     "acompressor=threshold=-22dB:ratio=2.5:attack=8:release=200:makeup=2[m]")
    if v["lufs"] < -70:
        sair("O vídeo está sem voz (ou mudo). Confira se é o arquivo certo.")
    c["ganho_voz"] = VOZ_LUFS - v["lufs"]
    tr = c["trilha"]
    if tr:
        s = c["sons"][tr["som"]]
        c["dur_trilha"] = sondar(s["arquivo"])["duracao"]
        t0 = segundos(tr.get("inicio", 0)) % c["dur_trilha"]
        m = medir(entradas=["-stream_loop", "-1", "-ss", f"{t0:.3f}", "-t", f"{min(dur_video, 600):.3f}",
                            "-i", str(s["arquivo"])], filtro="[0:a:0]anull[m]")
        abaixo = float(tr.get("abaixo_da_voz", 16))
        c["ganho_trilha"] = (VOZ_LUFS - abaixo) - m["lufs"]
    c["picos"] = {}
    for nome in {e["som"] for e in c["efeitos"]}:
        c["picos"][nome] = medir(c["sons"][nome]["arquivo"])["pico"]


def resumo(c, dur):
    print(f"Vídeo: {c['video'].name} · {fmt_tempo(dur)}")
    tr = c["trilha"]
    if tr:
        s = c["sons"][tr["som"]]
        d = sondar(s["arquivo"])["duracao"]
        t0 = segundos(tr.get("inicio", 0))
        volta = " (a trilha é mais curta: ela recomeça do início; confira a emenda)" if d - t0 < dur else ""
        print(f"Trilha: {s.get('titulo') or s['arquivo'].name} · {fmt_tempo(d)}, a partir de {fmt_tempo(t0)}, "
              f"{fmt_num(float(tr.get('abaixo_da_voz', 16)), 0)} LU abaixo da voz{volta}")
    else:
        print("Trilha: nenhuma")
    print(f"Efeitos: {len(c['efeitos'])}")
    ant = None
    for e in sorted(c["efeitos"], key=lambda x: x["t"]):
        aviso = "  ATENÇÃO: depois do fim do vídeo" if e["t"] >= dur else ""
        if ant is not None and e["t"] - ant < 5:
            aviso += "  ATENÇÃO: menos de 5 s depois do anterior"
        if e.get("aviso"):
            aviso += "  ATENÇÃO: " + e["aviso"]
        ancora = f"[inserção «{e['insercao']}»] " if e.get("insercao") else f"«{e['legenda']}» " if e.get("legenda") else ""
        print(f"  {fmt_tempo(e['t'])}  {e['som']:<14} {ancora}{e['motivo']}{aviso}")
        ant = e["t"]
    sem_uso = set(c["sons"]) - {e["som"] for e in c["efeitos"]} - ({tr["som"]} if tr else set())
    if sem_uso:
        print("Sons listados sem uso (saem dos créditos): " + ", ".join(sorted(sem_uso)))


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
    usados = ([c["trilha"]["som"]] if c["trilha"] else []) + sorted({e["som"] for e in c["efeitos"]})
    linhas = [f"# Créditos do som: {c['saida'].name}", "",
              "| Som | Arquivo | Título e autor | Fonte | Licença |", "|---|---|---|---|---|"]
    for n in usados:
        s = c["sons"][n]
        tit = " · ".join(x for x in (s.get("titulo"), s.get("autor")) if x)
        linhas.append(f"| {n} | `{s['arquivo'].name}` | {tit or '—'} | {s.get('fonte', '—')} | {s['licenca']} |")
    linhas += ["", "## Efeitos e motivo", "", "| Tempo | Efeito | Motivo |", "|---|---|---|"]
    linhas += [f"| {fmt_tempo(e['t'])} | {e['som']} | {e['motivo']} |" for e in sorted(c["efeitos"], key=lambda x: x["t"])]
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main():
    utf8()
    checar_ffmpeg()
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sair(__doc__)
    c = carregar(sys.argv[1])
    info = sondar(c["video"])
    if not info["tem_audio"]:
        sair("Esse vídeo não tem som. A /sonorizar precisa da voz no próprio vídeo.")
    dur = info["duracao"]
    resumo(c, dur)
    if "--resumo" in sys.argv:
        return
    ini, fim = 0.0, dur
    trecho = "--trecho" in sys.argv
    if trecho:
        i = sys.argv.index("--trecho")
        try:
            ini, fim = segundos(sys.argv[i + 1]), min(dur, segundos(sys.argv[i + 2]))
        except (IndexError, ValueError):
            sair("Use: --trecho <início> <fim>, por exemplo --trecho 00:30 00:50")
    janela = fim - ini
    c["ate_o_fim"] = fim >= dur - 0.05
    preparar(c, dur)
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
    tem_trilha = bool(c["trilha"])
    grafo2 = grafo + f";[mix]{ln},aresample={SR},atrim=0:{janela:.3f}[o]"
    if tem_trilha:
        grafo2 = grafo2.replace(f"{DUCK}[trilha]", f"{DUCK},asplit=2[trilha][trilhaout]")
    mapas = ["-map", "[o]", "-c:a", "pcm_s16le", str(mix), "-map", "[vozout]", "-c:a", "pcm_s16le",
             str(dados / "stem-voz.wav")]
    if tem_trilha:
        mapas += ["-map", "[trilhaout]", "-c:a", "pcm_s16le", str(dados / "stem-trilha.wav")]
    ff([*ent, "-filter_complex", grafo2, *mapas])

    if trecho:
        saida = c["pasta"] / "previa-trecho.mp4"
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


if __name__ == "__main__":
    main()
