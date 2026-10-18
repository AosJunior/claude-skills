# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["numpy>=1.26", "opencv-python-headless>=4.9"]
# ///
"""/minha-edicao, medidas automáticas de um Reel: cortes, zoom entre cortes, linhas fixas, texto por zona e folhas.

Uso:  uv run "<skill>/scripts/medir.py" "<vídeo>" "<pasta de saída>" [--de 0 --ate 13] [--zona 0 960]
                                                                    [--cena 0.12] [--fps-folha 1]

Tudo é medido no quadro de 1080x1920: um vídeo de outro tamanho é escalado antes. Grava na pasta de saída:
  medidas.json   todos os números
  folha_NN.jpg   folhas de contato com o tempo e réguas de y a cada 240 px
e imprime o resumo para a ficha. As medidas são aproximadas: o que importa confere-se na folha.
"""
import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

L, A = 1080, 1920                      # quadro de medida
FAIXA = 120                            # altura de cada faixa do histograma de texto (px)


def utf8():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def sair(msg):
    print(msg)
    sys.exit(1)


def sondar(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(video)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sair(f"Não consegui ler o vídeo: {video}")
    d = json.loads(r.stdout)
    s = d["streams"][0]
    n, q = s["r_frame_rate"].split("/")
    return {"largura": int(s["width"]), "altura": int(s["height"]),
            "fps": round(int(n) / max(1, int(q)), 3), "duracao": round(float(d["format"]["duration"]), 2)}


def quadros(video, de, ate, fps, w=L, h=A):
    """Gera (t, quadro BGR w x h) de 'de' a 'ate', 'fps' quadros por segundo, num passe só do ffmpeg."""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{de:.3f}", "-t", f"{ate - de:.3f}",
           "-i", str(video), "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    tam, i = w * h * 3, 0
    while True:
        buf = p.stdout.read(tam)
        if len(buf) < tam:
            break
        yield de + i / fps, np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        i += 1
    p.wait()


def quadro_em(video, t):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(video),
                        "-frames:v", "1", "-vf", f"scale={L}:{A}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                       capture_output=True)
    if len(r.stdout) < L * A * 3:
        return None
    return np.frombuffer(r.stdout[:L * A * 3], np.uint8).reshape(A, L, 3)


def achar_cortes(video, de, ate, limiar):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{de:.3f}", "-t", f"{ate - de:.3f}", "-i", str(video),
                        "-vf", f"scale=270:480,select='gt(scene,{limiar})',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    ts = [de + float(m) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]
    limpos = []
    for t in ts:                        # dois "cortes" a menos de 0,2 s são o mesmo
        if not limpos or t - limpos[-1] > 0.2:
            limpos.append(round(t, 2))
    return limpos


def escala_entre(a, b, zona=(0, A)):
    """Zoom de b em relação a a (1,12 = b está 12 % mais perto), casando pontos do fundo. None = outra cena."""
    y0, y1 = zona
    ga, gb = (cv2.cvtColor(cv2.resize(x[y0:y1], (540, (y1 - y0) // 2)), cv2.COLOR_BGR2GRAY) for x in (a, b))
    orb = cv2.ORB_create(3000)
    ka, da = orb.detectAndCompute(ga, None)
    kb, db = orb.detectAndCompute(gb, None)
    if da is None or db is None or len(ka) < 30 or len(kb) < 30:
        return None, 0
    pares = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    if len(pares) < 30:
        return None, 0
    pa = np.float32([ka[m.queryIdx].pt for m in pares])
    pb = np.float32([kb[m.trainIdx].pt for m in pares])
    M, ok = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=3.0)
    if M is None or ok is None or int(ok.sum()) < 25:
        return None, 0 if ok is None else int(ok.sum())
    return float(math.hypot(M[0, 0], M[1, 0])), int(ok.sum())


def saltos_de_zoom(video, cortes, fps, zona):
    """Em cada corte: quanto a imagem aproxima ou afasta. Nível = o maior entre salto e 1/salto (o vai e volta)."""
    meio, saltos = 1.5 / fps, []
    for t in cortes:
        a, b = quadro_em(video, t - meio), quadro_em(video, t + meio)
        s, pontos = (None, 0) if a is None or b is None else escala_entre(a, b, zona)
        if s is not None and not 0.45 < s < 2.2:
            s = None
        saltos.append({"t": t, "salto": None if s is None else round(s, 3), "pontos": pontos,
                       "nivel": None if s is None else round(max(s, 1 / s), 2)})
    return saltos


def agrupar(valores, tol=0.03):
    grupos = []
    for v in sorted(valores):
        if grupos and v - grupos[-1][-1] <= tol:
            grupos[-1].append(v)
        else:
            grupos.append([v])
    return [{"nivel": round(float(np.median(g)), 2), "cortes": len(g)} for g in grupos]


def corrida_max(linha):
    """Maior trecho contínuo de True (tolera buracos de até 6 px)."""
    xs = np.where(linha)[0]
    if not len(xs):
        return 0, 0, 0
    quebras = np.where(np.diff(xs) > 6)[0]
    inicios = np.r_[xs[0], xs[quebras + 1]]
    fins = np.r_[xs[quebras], xs[-1]]
    k = int(np.argmax(fins - inicios))
    return int(fins[k] - inicios[k]), int(inicios[k]), int(fins[k])


def linhas_e_texto(video, de, ate, fps):
    """Linhas horizontais que não mudam (emenda da tela dividida, borda de caixa) e texto branco por faixa de y."""
    n, borda, borda_x, texto = 0, np.zeros(A), [[] for _ in range(A)], np.zeros(A // FAIXA)
    for _, q in quadros(video, de, ate, fps):
        n += 1
        g = cv2.cvtColor(q, cv2.COLOR_BGR2GRAY).astype(np.int16)
        dy = np.abs(np.diff(g, axis=0))                     # dy[y]: salto entre as linhas y e y+1 (a borda é a y+1)
        forte = dy > 24
        cobre = forte.mean(axis=1)                          # fração da largura com salto forte
        for y in np.where(cobre > 0.06)[0]:                 # linha de verdade = um traço longo, não letras
            comp, x0, x1 = corrida_max(forte[y])
            if comp >= 80:
                borda[y + 1] += 1
                borda_x[y + 1].append((x0, x1))
        branco = (q.min(axis=2) > 225) & (np.abs(np.diff(g, axis=1, prepend=0)) > 60)
        texto += branco.sum(axis=1)[: (A // FAIXA) * FAIXA].reshape(-1, FAIXA).sum(axis=1)
    if not n:
        sair("Nenhum quadro lido nesse trecho.")
    linhas = []
    for y in np.where(borda / n >= 0.6)[0]:
        if linhas and y - linhas[-1]["y"] <= 2:
            continue
        xs = np.median(np.array(borda_x[y]), axis=0).astype(int)
        linhas.append({"y": int(y), "constante": round(float(borda[y] / n), 2), "x": [int(xs[0]), int(xs[1])]})
    total = texto.sum() or 1
    faixas = [{"y": [i * FAIXA, (i + 1) * FAIXA], "parte": round(float(v / total), 3)} for i, v in enumerate(texto)]
    return linhas, faixas


def ritmo(cortes, de, ate):
    janelas, t = [], de
    while t < ate - 0.5:
        janelas.append({"de": round(t, 1), "cortes": sum(t <= c < t + 10 for c in cortes)})
        t += 10
    bordas = [de] + cortes + [ate]
    maior = max((b - a, a) for a, b in zip(bordas, bordas[1:]))
    return janelas, {"segundos": round(maior[0], 2), "a_partir_de": round(maior[1], 2)}


def folhas(video, saida, de, ate, fps, colunas=6, linhas=4, w=180):
    h = w * 16 // 9
    lote, nomes, k = [], [], 0

    def gravar():
        nonlocal k, lote
        k += 1
        tela = np.full((linhas * (h + 4), colunas * (w + 4), 3), 40, np.uint8)
        for i, (t, q) in enumerate(lote):
            x, y = (i % colunas) * (w + 4), (i // colunas) * (h + 4)
            tela[y:y + h, x:x + w] = q
            for gy in range(240, A, 240):               # régua: uma linha a cada 240 px do quadro de 1920
                yy = y + gy * h // A
                cv2.line(tela, (x, yy), (x + 10, yy), (0, 230, 255), 1)
                if gy % 480 == 0:
                    cv2.putText(tela, str(gy), (x + 12, yy + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 230, 255), 1)
            cv2.rectangle(tela, (x, y), (x + 62, y + 16), (0, 0, 0), -1)
            cv2.putText(tela, f"{t:.1f}s", (x + 3, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 230, 255), 1)
        nome = saida / f"folha_{k:02d}.jpg"
        cv2.imwrite(str(nome), tela, [cv2.IMWRITE_JPEG_QUALITY, 88])
        nomes.append(nome.name)
        lote = []

    for t, q in quadros(video, de, ate, fps, w, h):
        lote.append((t, q))
        if len(lote) == colunas * linhas:
            gravar()
    if lote:
        gravar()
    return nomes


def main():
    utf8()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("saida")
    ap.add_argument("--de", type=float, default=0.0)
    ap.add_argument("--ate", type=float)
    ap.add_argument("--cena", type=float, default=0.12, help="limiar de troca de plano (0.12 pega o corte seco)")
    ap.add_argument("--zona", type=int, nargs=2, default=[0, A], metavar=("Y0", "Y1"),
                    help="mede o zoom só nessa faixa de y (ex.: 0 960 = metade de cima da tela dividida)")
    ap.add_argument("--fps-folha", type=float, default=1.0)
    ap.add_argument("--fps-linhas", type=float, default=2.0)
    a = ap.parse_args()
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sair("Falta o ffmpeg. Mac: brew install ffmpeg · Windows: winget install Gyan.FFmpeg")
    video, saida = Path(a.video), Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    info = sondar(video)
    de, ate = a.de, min(a.ate or info["duracao"], info["duracao"])

    print(f"Vídeo: {video.name} · {info['largura']}x{info['altura']} · {info['fps']} fps · {info['duracao']} s"
          f" · medindo de {de:.1f} a {ate:.1f} s (no quadro 1080x1920)")
    cortes = achar_cortes(video, de, ate, a.cena)
    saltos = saltos_de_zoom(video, cortes, info["fps"] or 30, tuple(a.zona))
    niveis = agrupar([z["nivel"] for z in saltos if z["nivel"] is not None])
    bordas = [de] + cortes + [ate]
    duracoes = [b - a for a, b in zip(bordas, bordas[1:])]
    janelas, vazio = ritmo(cortes, de, ate)
    linhas, faixas = linhas_e_texto(video, de, ate, a.fps_linhas)
    nomes = folhas(video, saida, de, ate, a.fps_folha)

    medidas = {"video": video.name, **info, "de": de, "ate": ate, "cortes": cortes, "saltos": saltos,
               "niveis_zoom": niveis, "plano_mediano": round(float(np.median(duracoes)), 2),
               "ritmo_10s": janelas, "maior_trecho_sem_corte": vazio, "linhas_fixas": linhas,
               "texto_por_faixa": faixas, "folhas": nomes}
    (saida / "medidas.json").write_text(json.dumps(medidas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"Cortes: {len(cortes)} · plano mediano {medidas['plano_mediano']} s · maior trecho sem corte "
          f"{vazio['segundos']} s (a partir de {vazio['a_partir_de']} s)")
    print("Zoom nos cortes (1,00 = mesmo enquadramento): "
          + ", ".join(f"{n['nivel']:.2f} ×{n['cortes']}" for n in niveis))
    print(f"Cortes para outra imagem (fundo não casa): {sum(z['nivel'] is None for z in saltos)}")
    print("Cortes a cada 10 s: " + " ".join(str(j["cortes"]) for j in janelas))
    print("Linhas fixas (y · quanto do trecho · x de-até): "
          + ("; ".join(f"{l['y']} · {l['constante']:.0%} · {l['x'][0]}-{l['x'][1]}" for l in linhas) or "nenhuma"))
    top = sorted(faixas, key=lambda f: -f["parte"])[:4]
    print("Texto branco por faixa de y (maiores): "
          + "; ".join(f"{f['y'][0]}-{f['y'][1]}: {f['parte']:.0%}" for f in top))
    print(f"Folhas: {', '.join(nomes)} em {saida}")


if __name__ == "__main__":
    main()
