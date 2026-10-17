# /// script
# requires-python = ">=3.9"
# dependencies = ["opencv-python-headless>=4.8,<5", "numpy"]   # o OpenCV 5 tirou o detector de rostos clássico
# ///
"""/decupar, recorte vertical: acha onde está o rosto num vídeo horizontal e grava o centro do recorte 9:16.

Uso:  uv run "<skill>/scripts/enquadrar.py" "<pasta decupagem>"
Olha 12 quadros espalhados pelo vídeo (só os trechos do cortes.json, se ele já existir), procura o rosto
com o detector de rostos do OpenCV e grava:
  .dados/enquadrar.json    {"centro_x": 0.43, ...}  (fração da largura; o cortar.py lê daqui)
  enquadrar.jpg            folha com os 12 quadros, o rosto marcado e a janela 9:16 desenhada
Se a pessoa se mexe, vale a posição mediana (um quadro fora não puxa o recorte). Sem rosto achado,
o centro fica no meio e o script avisa: abra a enquadrar.jpg e escreva o centro à mão no cortes.json
("vertical": {"centro_x": 0.4}).
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import achar_pasta, fmt_num, fmt_tempo, gravar_json, ler_json, sair, utf8  # noqa: E402

N = 12
LARG = 1280  # rosto de quem está sentado longe fica pequeno: abaixo disso o detector erra


def tempos(pasta, info):
    dur = info["duracao"]
    seg = pasta / ".dados" / "segmentos.json"
    if seg.exists():
        fps = info["fps_num"] / info["fps_den"]
        partes = [(s["fi"] / fps, s["fo"] / fps) for s in ler_json(seg)]
        total = sum(b - a for a, b in partes)
        alvo, out, acc = [total * (k + 0.5) / N for k in range(N)], [], 0.0
        for a, b in partes:
            while alvo and alvo[0] <= acc + (b - a):
                out.append(a + alvo.pop(0) - acc)
            acc += b - a
        return out
    return [dur * (k + 0.5) / N for k in range(N)]


def quadro(video, t, w, h):
    H = int(round(LARG * h / w))
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video),
                        "-frames:v", "1", "-vf", f"scale={LARG}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                       capture_output=True)
    if r.returncode != 0 or len(r.stdout) != LARG * H * 3:
        return None
    return np.frombuffer(r.stdout, np.uint8).reshape(H, LARG, 3).copy()


def main():
    utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sair(__doc__)
    pasta = achar_pasta(args[0])
    info = ler_json(pasta / ".dados" / "info.json")
    w, h = info["largura"], info["altura"]
    if h >= w:
        sair("O vídeo já é vertical: não precisa de recorte.")
    px = pasta / ".dados" / "proxy.mov"
    fonte = px if px.exists() else Path(info["arquivo"])
    cascata = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    perfil = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
    achados, folhas = [], []
    for t in tempos(pasta, info):
        img = quadro(fonte, t, w, h)
        if img is None:
            continue
        cinza = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        rostos = list(cascata.detectMultiScale(cinza, 1.1, 6, minSize=(36, 36)))
        if not rostos:
            rostos = list(perfil.detectMultiScale(cinza, 1.1, 5, minSize=(36, 36)))
        if rostos:
            x, y, rw, rh = max(rostos, key=lambda r: r[2] * r[3])   # o maior rosto é quem fala
            achados.append((x + rw / 2) / img.shape[1])
            cv2.rectangle(img, (int(x), int(y)), (int(x + rw), int(y + rh)), (0, 220, 0), 3)
        folhas.append((t, img))
    if not folhas:
        sair("Não consegui ler quadros do vídeo.")
    centro = float(np.median(achados)) if achados else 0.5
    espalhado = float(np.percentile(achados, 90) - np.percentile(achados, 10)) if len(achados) >= 3 else 0.0
    janela = (h * 9 / 16) / w
    centro = min(max(centro, janela / 2), 1 - janela / 2)
    grade = []
    for t, img in folhas:
        H, W = img.shape[:2]
        a = int(round((centro - janela / 2) * W))
        b = int(round((centro + janela / 2) * W))
        sombra = img.copy()
        sombra[:, :a] = (sombra[:, :a] * 0.35).astype(np.uint8)
        sombra[:, b:] = (sombra[:, b:] * 0.35).astype(np.uint8)
        cv2.rectangle(sombra, (a, 0), (b - 1, H - 1), (255, 255, 255), 2)
        cv2.putText(sombra, fmt_tempo(t), (16, 48), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (255, 255, 255), 3)
        grade.append(cv2.resize(sombra, (480, int(round(480 * H / W)))))   # folha leve para abrir
    while len(grade) % 4:
        grade.append(np.zeros_like(grade[0]))
    linhas = [np.hstack(grade[i:i + 4]) for i in range(0, len(grade), 4)]
    cv2.imwrite(str(pasta / "enquadrar.jpg"), np.vstack(linhas), [cv2.IMWRITE_JPEG_QUALITY, 80])
    gravar_json(pasta / ".dados" / "enquadrar.json",
                {"centro_x": round(centro, 4), "rostos": len(achados), "quadros": len(folhas),
                 "espalhado": round(espalhado, 4), "janela": round(janela, 4)})
    print(f"Rosto achado em {len(achados)} de {len(folhas)} quadros · centro do recorte 9:16 em "
          f"{fmt_num(100 * centro)}% da largura (mediana)")
    if not achados:
        print("ATENÇÃO: nenhum rosto achado. Abra a enquadrar.jpg e escreva o centro à mão no cortes.json.")
    elif len(achados) < len(folhas) / 2:
        print("ATENÇÃO: rosto achado em menos da metade dos quadros. Confira a enquadrar.jpg.")
    if espalhado > janela / 2:
        print(f"A pessoa se mexe bastante (varia {fmt_num(100 * espalhado)}% da largura): ficou a posição mediana.")
    print("Folha para conferir: enquadrar.jpg (a parte clara é o que fica no vídeo vertical).")


if __name__ == "__main__":
    main()
