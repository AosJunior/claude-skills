# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = [
#   "mlx-whisper>=0.4; sys_platform == 'darwin' and platform_machine == 'arm64'",
#   "faster-whisper>=1.1; sys_platform != 'darwin' or platform_machine != 'arm64'",
# ]
# ///
"""/decupar, etapa 1: transcreve o vídeo com tempo por palavra e prepara a decupagem.

Uso:  uv run "<skill>/scripts/transcrever.py" "<vídeo>"
      uv run "<skill>/scripts/transcrever.py" "<vídeo>" --ouvir 00:23,5 00:27,5
         escuta de novo só esse pedaço (para "voz sem texto" e "tempos quebrados") e só mostra o que ouviu
      uv run "<skill>/scripts/transcrever.py" "<vídeo>" --ouvir 01:28,2 01:31,0 --trocar
         troca as palavras desse pedaço pelas ouvidas de novo e refaz a transcricao.txt (renumera as frases)

Grava em <pasta do vídeo>/decupagem/:
  transcricao.txt          frases numeradas (F1, F2...) com [início – fim] do bruto
  .dados/whisper.json      saída do Whisper + silêncios (cache: o mesmo vídeo não é transcrito de novo)
  .dados/palavras.json     palavras com tempo, já ajustadas aos silêncios (o cortar.py lê daqui)
  .dados/frases.json       frases com tempo (o cortar.py entende "F12" no cortes.json)
  .dados/info.json         duração, tamanho, taxa, rotação, faixa de áudio
  .dados/pistas.txt        possíveis retakes, frases que recomeçam, voz sem texto (só sugestões)
  .dados/proxy.mov         cópia leve (vídeo acima de Full HD), feita em segundo plano: prévia e correções rápidas
O vídeo bruto só é lido. Whisper large-v3-turbo em português: mlx-whisper no Mac Apple Silicon,
faster-whisper (CPU) no Windows e no Mac Intel. DECUPAR_MOTOR=faster-whisper força o segundo.
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (CAP_PALAVRA, VIDEO, achar_marca, assinatura_video, checar_ffmpeg, encoder, fmt_dur,  # noqa: E402
                   fmt_num, fmt_tempo, gravar_json, hwaccel, ler_json, orientacao, pasta_decupagem, proxy_valido,
                   rodar, sair, sondar, tamanho, texto_marca, utf8)

VERSAO = 1
IDIOMA = "pt"
MODELO_MLX = "mlx-community/whisper-large-v3-turbo"
MODELO_FW = "large-v3-turbo"
GAP_FRASE = 0.7        # s; pausa que fecha frase
PAUSA_CORTE = 0.35     # s; pausa que o corte tira sozinho
JANELA = 60            # s; retake só é procurado entre frases a até 60 s


def motor():
    """Qual Whisper está instalado, sem importar (importar o mlx/torch leva segundos)."""
    from importlib.util import find_spec
    if os.environ.get("DECUPAR_MOTOR") != "faster-whisper" and find_spec("mlx_whisper"):
        return "mlx-whisper"
    if find_spec("faster_whisper"):
        return "faster-whisper"
    sair("Não achei o Whisper. Rode este script com `uv run` (ele instala sozinho).")


def transcrever(wav, qual):
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    palavras = []
    if qual == "mlx-whisper":
        import mlx_whisper
        r = mlx_whisper.transcribe(str(wav), path_or_hf_repo=MODELO_MLX, language=IDIOMA,
                                   word_timestamps=True, hallucination_silence_threshold=2.0)
        for s in r.get("segments", []):
            for w in s.get("words", []):
                palavras.append((w["word"], w["start"], w["end"]))
    else:
        import wave
        import numpy as np
        from faster_whisper import WhisperModel
        # o áudio vai como números, não como arquivo: a leitura de arquivo do faster-whisper depende do PyAV,
        # e versões novas do PyAV quebram essa leitura (TypeError metadata_errors, out/2026)
        with wave.open(str(wav), "rb") as f:
            audio = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        # CPU de propósito: no Windows com placa NVIDIA sem as bibliotecas CUDA, "auto" quebra no meio
        m = WhisperModel(MODELO_FW, device="cpu", compute_type="int8")
        segs, _ = m.transcribe(audio, language=IDIOMA, word_timestamps=True, vad_filter=True,
                               hallucination_silence_threshold=2.0)
        for s in segs:
            for w in s.words or []:
                palavras.append((w.word, w.start, w.end))
    out = []
    for txt, a, b in palavras:
        txt = txt.strip()
        if txt:
            out.append({"w": txt, "ini": round(float(a), 3), "fim": round(max(float(a), float(b)), 3)})
    return out


def silencios(wav):
    r = rodar(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af", "silencedetect=noise=-38dB:d=0.3",
               "-f", "null", "-"])
    ini = [float(x) for x in re.findall(r"silence_start:\s*(-?[0-9.]+)", r.stderr)]
    fim = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", r.stderr)]
    return [[round(max(0.0, a), 3), round(b, 3)] for a, b in zip(ini, fim)]


def fim_real(w):
    return min(w["fim"], w["ini"] + CAP_PALAVRA)


def ajustar(pal, sil, margem=0.08, perto=0.25):
    """Leva o começo e o fim de cada palavra para a borda do som medido (silencedetect).

    O Whisper erra a borda da palavra em pausa: estica por cima do silêncio ou começa tarde, e o
    corte depende dessas bordas. Palavra por cima de um silêncio inteiro vira dois pedaços (o
    pedaço menor fica sem texto, "sombra"): o silêncio do meio sai e nenhum lado da fala se perde."""
    juntos = []
    for a, b in sorted(sil):
        if juntos and a - juntos[-1][1] < 0.1:
            juntos[-1][1] = max(juntos[-1][1], b)
        else:
            juntos.append([a, b])
    juntos = [x for x in juntos if x[1] - x[0] >= 0.3]
    out = []
    for w in pal:
        pedacos = [[w["ini"], w["fim"]]]
        for s0, s1 in juntos:
            novos = []
            for a, b in pedacos:
                if a < s0 and b > s1:
                    novos += [[a, s0 + margem], [s1 - margem, b]]
                else:
                    novos.append([a, b])
            pedacos = novos
        for pc in pedacos:
            a, b = pc
            for s0, s1 in juntos:
                if s0 <= a < s1 - margem and b > s1:
                    a = s1 - margem              # começou dentro do silêncio
                if s0 + margem < b <= s1 and a < s0:
                    b = s0 + margem              # terminou dentro do silêncio
                if s1 <= a < s1 + perto:
                    a = s1                       # o som volta antes do que o Whisper marcou
                if s0 - perto < b <= s0 and a < s0:
                    b = s0                       # o som vai até o silêncio
            pc[0], pc[1] = a, max(a, b)
        maior = max(range(len(pedacos)), key=lambda k: pedacos[k][1] - pedacos[k][0])
        for k, (a, b) in enumerate(pedacos):
            out.append({"w": w["w"] if k == maior else "", "ini": round(a, 3), "fim": round(b, 3)})
    return sorted(out, key=lambda x: x["ini"])


# ---------------------------------------------------------------- frases e pistas

ACENTOS = str.maketrans("áàâãéêíóôõúüç", "aaaaeeiooouuc")


def token(w):
    return re.sub(r"[^a-z0-9]", "", w.lower().translate(ACENTOS))


def quase(a, b):
    """Mesma palavra, ou 4+ letras com uma letra de diferença."""
    if a == b:
        return True
    if len(a) < 4 or len(b) < 4 or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    lo, cu = (a, b) if len(a) > len(b) else (b, a)
    i = j = 0
    pulou = False
    while i < len(lo) and j < len(cu):
        if lo[i] == cu[j]:
            i += 1
            j += 1
        elif pulou:
            return False
        else:
            pulou, i = True, i + 1
    return True


def lcs(u, v):
    prev = [0] * (len(v) + 1)
    for a in u:
        cur = [0] * (len(v) + 1)
        for j, b in enumerate(v, 1):
            cur[j] = prev[j - 1] + 1 if quase(a, b) else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1]


def montar_frases(pal):
    """Frase = até ponto final, pausa longa, ou vírgula depois de 8 palavras (linhas curtas para cortar)."""
    frs, f, ultima = [], None, ""
    for i, w in enumerate(pal):
        if f and w["w"] and (w["ini"] - fim_real(pal[i - 1]) > GAP_FRASE or re.search(r"[.!?…]$", ultima)
                             or (re.search(r"[,;:]$", ultima) and i - f["i0"] >= 8)):
            frs.append(f)
            f = None
        ultima = w["w"] or ultima
        if not f:
            f = {"i0": i, "i1": i}
        f["i1"] = i
    if f:
        frs.append(f)
    out = []
    for k, f in enumerate(frs, 1):
        ws = pal[f["i0"]:f["i1"] + 1]
        out.append({"id": f"F{k}", "ini": ws[0]["ini"], "fim": round(fim_real(ws[-1]), 3),
                    "i0": f["i0"], "i1": f["i1"], "texto": " ".join(w["w"] for w in ws if w["w"]),
                    "tok": [t for t in (token(w["w"]) for w in ws) if t]})
    return out


def recomeco(tok):
    """Posição em que a frase recomeça a si mesma ("eu vou, eu vou te mostrar")."""
    n = len(tok)
    for w in range(2, min(n - 1, 7)):        # recomeço de verdade acontece nas primeiras palavras
        x = 3 if w >= 3 else 2
        if w + x <= n and (x == 3 or n - w >= 4) and all(quase(tok[w + z], tok[z]) for z in range(x)):
            return w
    return -1


def curto(t, n=60):
    return t if len(t) <= n else t[:n - 1] + "…"


def pistas(pal, frs, sil, dur):
    linhas = []
    for a in range(len(frs)):
        for b in range(a + 1, len(frs)):
            u, v = frs[a], frs[b]
            if v["ini"] - u["fim"] > JANELA:
                break
            nu, nv = len(u["tok"]), len(v["tok"])
            if min(nu, nv) == 0:
                continue
            c = lcs(u["tok"], v["tok"])
            tipo = None
            if min(nu, nv) >= 3 and c / max(nu, nv) >= 0.55:
                tipo = f"repetição {round(100 * c / max(nu, nv))}%"
            elif min(nu, nv) >= 3 and nu != nv and c / min(nu, nv) >= 0.8:
                tipo = "recomeço"
            elif nu <= 2 and nv >= 4 and v["ini"] - u["fim"] <= 1.5 and all(
                    quase(u["tok"][k], v["tok"][k]) for k in range(nu)):
                tipo = "arranque"
            if tipo:
                linhas.append(f"- possível retake ({tipo}): {u['id']} [{fmt_tempo(u['ini'])}] «{curto(u['texto'])}»"
                              f" ≈ {v['id']} [{fmt_tempo(v['ini'])}] «{curto(v['texto'])}»")
    for f in frs:
        k = recomeco(f["tok"])
        if k > 0:
            linhas.append(f"- {f['id']} [{fmt_tempo(f['ini'])}] recomeça no meio: «{curto(f['texto'], 90)}»")
    # voz sem texto (o Whisper pode ter pulado) e texto sem voz (pode ter inventado)
    falas, t = [], 0.0
    for a, b in sil + [[dur, dur]]:
        if a - t >= 0.6:
            falas.append((t, a))
        t = max(t, b)
    cobre = sorted((w["ini"] - 0.15, fim_real(w) + 0.15) for w in pal)
    for a, b in falas:
        t = a
        for x, y in cobre + [(b, b)]:
            if y <= t or x >= b + 1:
                continue
            if min(x, b) - t >= 0.8:
                linhas.append(f"- voz sem texto em {fmt_tempo(t)}–{fmt_tempo(min(x, b))}: o Whisper pode ter "
                              "pulado uma fala (ouça antes de cortar)")
            t = max(t, y)
    for f in frs:
        ws = pal[f["i0"]:f["i1"] + 1]
        if len(ws) >= 3 and sum(w["fim"] - w["ini"] < 0.02 for w in ws) >= len(ws) / 2:
            linhas.append(f"- {f['id']} [{fmt_tempo(f['ini'])}] veio com tempos quebrados do Whisper: confira "
                          f"ouvindo «{curto(f['texto'])}»")
    for f in frs:
        ws = pal[f["i0"]:f["i1"] + 1]
        tot = sum(fim_real(w) - w["ini"] for w in ws) or 1e-9
        mudo = sum(max(0.0, min(b, fim_real(w)) - max(a, w["ini"])) for w in ws for a, b in sil)
        if mudo / tot >= 0.8:
            linhas.append(f"- {f['id']} [{fmt_tempo(f['ini'])}] cai em silêncio: o Whisper pode ter inventado "
                          f"«{curto(f['texto'])}»")
    return linhas


def texto_transcricao(info, frs, pal):
    L = [f"Transcrição de \"{info['nome']}\" · {fmt_dur(info['duracao'])} · /decupar",
         "Cada linha é uma frase: F<n> [início – fim] em minuto:segundo,centésimos do vídeo bruto.",
         f"Pausas de mais de {fmt_num(PAUSA_CORTE, 2)} s entre frases aparecem como \"· pausa\".", ""]
    if pal and pal[0]["ini"] >= PAUSA_CORTE:
        L.append(f"        · {fmt_num(pal[0]['ini'], 2)} s antes da primeira fala")
    for k, f in enumerate(frs):
        L.append(f"{f['id']:<5}[{fmt_tempo(f['ini'])} – {fmt_tempo(f['fim'])}]  {f['texto']}")
        if k + 1 < len(frs):
            gap = frs[k + 1]["ini"] - f["fim"]
            if gap >= PAUSA_CORTE:
                L.append(f"        · pausa {fmt_num(gap, 2)} s")
    if frs and info["duracao"] - frs[-1]["fim"] >= PAUSA_CORTE:
        L.append(f"        · {fmt_num(info['duracao'] - frs[-1]['fim'], 2)} s depois da última fala")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- principal

def precisa_proxy(info, dados):
    parcial = dados / "proxy.parcial.mov"
    trabalhando = parcial.exists() and time.time() - parcial.stat().st_mtime < 15
    return min(info["largura"], info["altura"]) > 1080 and not trabalhando and not proxy_valido(dados, info)


def fazer_proxy(video, info, dados):
    """Cópia leve no tamanho da prévia (roda em segundo plano depois do Whisper). Se falhar, a prévia usa
    o original. Enquanto trabalha, proxy.parcial.mov cresce; o cortar.py espera por ele."""
    W, H = tamanho(info)
    parcial = dados / "proxy.parcial.mov"
    for hw in ([hwaccel(), []] if hwaccel() else [[]]):
        r = rodar(["ffmpeg", "-hide_banner", "-v", "error", "-y", *hw, "-i", video, "-map", "0:v:0",
                   "-map", f"0:a:{info['faixa_audio']}", "-vf", f"scale={W}:{H}", "-fps_mode", "passthrough",
                   *encoder("proxy"), "-g", "15", "-c:a", "pcm_s16le", parcial])
        if r.returncode == 0:
            parcial.replace(dados / "proxy.mov")
            gravar_json(dados / "proxy.json", {**assinatura_video(info["arquivo"]), "largura": W, "altura": H})
            return
    parcial.unlink(missing_ok=True)


def disparar_proxy(video):
    """Solta o fazer_proxy num processo à parte, sem segurar o terminal."""
    extra = {"start_new_session": True}
    if sys.platform.startswith("win"):
        extra = {"creationflags": 0x00000008 | 0x00000200}   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen([sys.executable, str(Path(__file__).resolve()), str(video), "--fazer-proxy"],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     close_fds=True, **extra)


def segundos(txt):
    try:
        return sum(float(p) * 60 ** i for i, p in enumerate(reversed(txt.replace(",", ".").split(":"))))
    except ValueError:
        sair(f"Não entendi o tempo {txt!r}. Use 01:23,45 ou segundos.")


def aplicar_correcoes(brutas, correcoes):
    pal = list(brutas)
    for c in correcoes:
        pal = [w for w in pal if not c["ini"] <= (w["ini"] + w["fim"]) / 2 <= c["fim"]] + c["palavras"]
    return sorted(pal, key=lambda w: w["ini"])


def ouvir(video, info, ini, fim, trocar):
    """Transcreve de novo só um pedaço: o Whisper costuma pular fala repetida (justamente o retake)."""
    pasta = pasta_decupagem(video) / ".dados"
    pasta.mkdir(parents=True, exist_ok=True)
    wav = pasta / "pedaco16k.wav"
    a = max(0.0, ini - 0.3)
    r = rodar(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{fim - a + 0.3:.3f}",
               "-i", video, "-map", f"0:a:{info['faixa_audio']}", "-vn", "-ac", "1", "-ar", "16000", wav])
    if r.returncode != 0:
        sair(f"Não consegui extrair esse pedaço do som:\n{r.stderr[-500:]}")
    try:
        pal = transcrever(wav, motor())
    finally:
        wav.unlink(missing_ok=True)
    if not pal:
        print(f"{fmt_tempo(ini)}–{fmt_tempo(fim)}: sem fala reconhecível (respiração, ruído ou fala muito baixa).")
        return
    print(f"{fmt_tempo(ini)}–{fmt_tempo(fim)}, ouvido de novo:")
    print(" ".join(f"[{fmt_tempo(w['ini'] + a)}] {w['w']}" for w in pal))
    if trocar:
        cache = pasta / "whisper.json"
        if not cache.exists():
            sair("Rode a transcrição completa antes de trocar um pedaço.")
        d = ler_json(cache)
        novas = [{"w": w["w"], "ini": round(w["ini"] + a, 3), "fim": round(w["fim"] + a, 3)} for w in pal
                 if ini <= (w["ini"] + w["fim"]) / 2 + a <= fim]
        d["correcoes"] = [c for c in d.get("correcoes", []) if c["fim"] <= ini or c["ini"] >= fim]
        d["correcoes"].append({"ini": round(ini, 3), "fim": round(fim, 3), "palavras": novas})
        gravar_json(cache, d)
        print(f"Troquei {len(novas)} palavras nesse pedaço. Transcrição refeita:")


def main():
    utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sair(__doc__)
    t0 = time.time()
    video = Path(args[0]).expanduser()
    if video.is_dir():
        vs = sorted(p.name for p in video.iterdir() if p.suffix.lower() in VIDEO and not p.name.startswith("."))
        sair("Essa é uma pasta. Escolha um vídeo de cada vez:\n" + "\n".join(f"- {n}" for n in vs), 2)
    if not video.is_file():
        sair(f"Não achei o arquivo: {video}")
    checar_ffmpeg()
    info = sondar(video)
    if info["faixa_audio"] is None:
        sair("Esse vídeo não tem som que dê para transcrever.")
    if "--fazer-proxy" in sys.argv:
        dados = pasta_decupagem(video) / ".dados"
        dados.mkdir(parents=True, exist_ok=True)
        fazer_proxy(video, info, dados)
        return
    if "--ouvir" in sys.argv:
        i = sys.argv.index("--ouvir")
        if len(sys.argv) < i + 3:
            sair("Use: --ouvir <início> <fim>, por exemplo --ouvir 00:23,5 00:27,5")
        trocar = "--trocar" in sys.argv
        ouvir(video, info, segundos(sys.argv[i + 1]), segundos(sys.argv[i + 2]), trocar)
        if not trocar:
            return
    pasta = pasta_decupagem(video)
    dados = pasta / ".dados"
    dados.mkdir(parents=True, exist_ok=True)
    st = video.stat()
    qual = motor()
    assinatura = {"arquivo": info["arquivo"], "tamanho": st.st_size, "mtime": int(st.st_mtime),
                  "motor": qual, "versao": VERSAO}
    cache = dados / "whisper.json"
    gravar_json(dados / "info.json", info)
    usou_cache = False
    if cache.exists():
        try:
            d = ler_json(cache)
            sig = d.get("assinatura", {})
            usou_cache = {k: sig.get(k) for k in ("arquivo", "tamanho", "mtime", "versao")} == \
                {k: assinatura[k] for k in ("arquivo", "tamanho", "mtime", "versao")}
        except Exception:
            usou_cache = False
    t_whisper = 0.0
    correcoes = []
    if usou_cache:
        brutas, sil, correcoes = d["palavras"], d["silencios"], d.get("correcoes", [])
    else:
        wav = dados / "audio16k.wav"
        r = rodar(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", video, "-map", f"0:a:{info['faixa_audio']}",
                   "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav])
        if r.returncode != 0:
            sair(f"Não consegui extrair o som do vídeo:\n{r.stderr[-800:]}")
        try:
            sil = silencios(wav)
            print(f"Transcrevendo com {qual} (na primeira vez ele baixa o modelo, cerca de 1,6 GB)...", flush=True)
            t1 = time.time()
            brutas = transcrever(wav, qual)
            t_whisper = time.time() - t1
        finally:
            wav.unlink(missing_ok=True)
        gravar_json(cache, {"assinatura": assinatura, "palavras": brutas, "silencios": sil})
    pal = ajustar(aplicar_correcoes(brutas, correcoes), sil)
    gravar_json(dados / "palavras.json", {"palavras": pal, "silencios": sil})
    if not pal:
        sair("O Whisper não achou fala nesse vídeo.")
    frs = montar_frases(pal)
    antigas = dados / "frases.json"
    if antigas.exists() and (pasta / "cortes.json").exists():
        velhas = [(f["id"], f["texto"]) for f in ler_json(antigas)]
        if velhas != [(f["id"], f["texto"]) for f in frs]:
            print("ATENÇÃO: as frases mudaram de número. Revise o cortes.json, que usa os números antigos.")
    gravar_json(dados / "frases.json", [{k: f[k] for k in ("id", "ini", "fim", "i0", "i1", "texto")} for f in frs])
    (pasta / "transcricao.txt").write_text(texto_transcricao(info, frs, pal), encoding="utf-8")
    pis = pistas(pal, frs, sil, info["duracao"])
    (dados / "pistas.txt").write_text("\n".join(pis) + "\n", encoding="utf-8")
    gaps = [b["ini"] - fim_real(a) for a, b in zip(pal, pal[1:])]
    longas = [g for g in gaps if g > PAUSA_CORTE]
    fps = info["fps_num"] / info["fps_den"]
    print(f"Pasta: {pasta}")
    print(texto_marca(achar_marca(pasta.parent)))
    print(f"Vídeo: {fmt_dur(info['duracao'])} · {info['largura']}×{info['altura']} {orientacao(info)} · "
          f"{fmt_num(fps, 2).rstrip('0').rstrip(',')} quadros/s" + (" · HDR" if info["hdr"] else ""))
    print(f"Transcrição: {sum(1 for w in pal if w['w'])} palavras em {len(frs)} frases → transcricao.txt"
          + (" (do cache)" if usou_cache else f" · Whisper levou {fmt_num(t_whisper)} s"))
    print(f"Pausas acima de {fmt_num(PAUSA_CORTE, 2)} s: {len(longas)} (somam {fmt_num(sum(longas))} s); "
          "o corte tira sozinho.")
    print("Pistas (sugestões para conferir na transcrição):")
    print("\n".join(pis) if pis else "- nenhuma repetição óbvia")
    if precisa_proxy(info, dados):
        disparar_proxy(video)
        print("Em segundo plano: uma cópia leve do vídeo para a prévia sair rápido (o corte espera por ela).")
    print(f"Pronto em {fmt_num(time.time() - t0)} s.")


if __name__ == "__main__":
    main()
