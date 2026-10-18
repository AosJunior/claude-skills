# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26", "onnxruntime>=1.17"]
# ///
"""/inserir: máscara da pessoa para as camadas que ficam atrás dela (lugar "atras").

Uso:  uv run "<skill>/scripts/mascara.py" "<vídeo cortado>" "<pasta saída>" --trechos 714:948,2019:2200
          [--motor auto|vision|rvm] [--fps 30/1]
      --trechos: quadros q0:q1 (q1 fora) de cada trecho; quem calcula é o inserir.py.

Grava <pasta saída>/m-<q0>-<q1>-<motor>.mkv: vídeo cinza sem perda (ffv1), faixa completa (0 = fundo, 255 = pessoa),
com exatamente q1-q0 quadros, alinhados aos quadros do vídeo cortado. Trecho que já existe não é refeito.

Motores:
  vision  Apple Vision (Mac com macOS 12+; pessoa e objeto na mão no macOS 14+). Compila mascara_vision.swift na
          primeira vez, para ~/.cache/claude-skills/inserir/. Precisa das Command Line Tools (swiftc).
  rvm     RobustVideoMatting (mobilenetv3, ONNX) no onnxruntime: Windows, Linux, Mac Intel. O modelo (15 MB) é
          baixado na primeira vez do GitHub do autor para ~/.cache/claude-skills/inserir/. Licença GPL-3.0: o kit
          não empacota o modelo, só baixa e usa.
  auto    vision no Mac com chip Apple e macOS 14+; senão rvm.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import checar_ffmpeg, sair, utf8

AQUI = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "claude-skills" / "inserir"
RVM_URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"
RVM_SHA = "88d4531297118f595bf2fd60f6f566aec2e559393802d1f436c380f0cbbd2828"


def mac_versao():
    if sys.platform != "darwin":
        return None
    try:
        return tuple(int(x) for x in platform.mac_ver()[0].split(".")[:2])
    except ValueError:
        return None


def escolher(motor):
    """Motor que vai rodar e, se mudou, o porquê (uma linha)."""
    v = mac_versao()
    if motor == "auto":
        if v and v >= (14, 0) and platform.machine() == "arm64":
            motor = "vision"
        else:
            return "rvm", None
    if motor == "vision":
        if not v:
            return "rvm", "o Apple Vision só existe no Mac; vou de RobustVideoMatting."
        if v < (12, 0):
            return "rvm", "o Apple Vision pede macOS 12 ou mais novo; vou de RobustVideoMatting."
        if not shutil.which("swiftc"):
            return "rvm", ("faltam as Command Line Tools da Apple (instale com: xcode-select --install); "
                           "por agora vou de RobustVideoMatting.")
    return motor, None


def compilar_vision():
    """Compila o filtro Swift uma vez (por versão do código) para a pasta de cache do usuário."""
    src = AQUI / "mascara_vision.swift"
    h = hashlib.sha1(src.read_bytes()).hexdigest()[:10]
    exe = CACHE / f"mascara_vision-{h}"
    if exe.exists():
        return exe
    CACHE.mkdir(parents=True, exist_ok=True)
    print("Primeira vez: preparando o Apple Vision (uns 30 s)...", flush=True)
    r = subprocess.run(["swiftc", "-O", "-o", str(exe), str(src)], capture_output=True, text=True)
    if r.returncode:
        return None
    return exe


def baixar_rvm():
    m = CACHE / "rvm_mobilenetv3_fp32.onnx"
    if m.exists() and hashlib.sha256(m.read_bytes()).hexdigest() == RVM_SHA:
        return m
    CACHE.mkdir(parents=True, exist_ok=True)
    print("Primeira vez: baixando o modelo de recorte da pessoa (15 MB)...", flush=True)
    tmp = m.with_suffix(".parcial")
    try:
        urllib.request.urlretrieve(RVM_URL, tmp)
    except Exception as e:
        sair(f"Não consegui baixar o modelo ({e}). Confira a internet e rode de novo.")
    if hashlib.sha256(tmp.read_bytes()).hexdigest() != RVM_SHA:
        tmp.unlink(missing_ok=True)
        sair("O modelo baixado veio diferente do esperado. Rode de novo; se repetir, avise.")
    tmp.replace(m)
    return m


def decodificar(video, q0, n, fps_txt, fmt):
    """ffmpeg lendo exatamente os quadros q0..q0+n-1 do vídeo (o mesmo jeito que o compor.py lê)."""
    fps = eval_fps(fps_txt)
    cmd = ["ffmpeg", "-v", "error", "-nostdin"]
    if q0:
        cmd += ["-ss", f"{(q0 - 0.25) / fps:.4f}"]
    cmd += ["-i", str(video), "-frames:v", str(n), "-an", "-vf", f"fps={fps_txt}",
            "-f", "rawvideo", "-pix_fmt", fmt, "-"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 7)


def codificar(saida, w, h, fps_txt):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "rawvideo", "-pix_fmt", "gray",
                             "-s", f"{w}x{h}", "-r", fps_txt, "-i", "-", "-c:v", "ffv1", "-level", "3",
                             "-pix_fmt", "gray", "-color_range", "pc", str(saida)], stdin=subprocess.PIPE)


def eval_fps(t):
    n, _, q = str(t).partition("/")
    return float(n) / float(q or 1)


def tamanho(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "json", str(video)], capture_output=True, text=True)
    s = json.loads(r.stdout)["streams"][0]
    return s["width"], s["height"]


def trecho_vision(exe, video, q0, q1, saida, fps_txt):
    w, h = tamanho(video)
    dec = decodificar(video, q0, q1 - q0, fps_txt, "bgra")
    filtro = subprocess.Popen([str(exe), str(w), str(h)], stdin=dec.stdout, stdout=subprocess.PIPE, bufsize=10 ** 7)
    dec.stdout.close()
    enc = codificar(saida, w, h, fps_txt)
    feitos, n = 0, w * h
    while True:
        b = filtro.stdout.read(n)
        if len(b) < n:
            break
        enc.stdin.write(b)
        feitos += 1
    enc.stdin.close()
    enc.wait()
    filtro.wait()
    dec.wait()
    if filtro.returncode:
        raise RuntimeError(f"o filtro do Vision parou (código {filtro.returncode})")
    return feitos


def trecho_rvm(sess, video, q0, q1, saida, fps_txt):
    import numpy as np
    w, h = tamanho(video)
    dec = decodificar(video, q0, q1 - q0, fps_txt, "rgb24")
    enc = codificar(saida, w, h, fps_txt)
    rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4
    # downsample: o modelo trabalha com o lado maior perto de 512 px (o recomendado pelo autor para vídeo vertical HD)
    ds = np.array([min(1.0, 512 / max(w, h))], np.float32)
    feitos, n = 0, w * h * 3
    while True:
        b = dec.stdout.read(n)
        if len(b) < n:
            break
        x = np.frombuffer(b, np.uint8).reshape(h, w, 3).transpose(2, 0, 1)[None].astype(np.float32) / 255
        _, pha, *rec = sess.run(None, {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                       "downsample_ratio": ds})
        enc.stdin.write((np.clip(pha[0, 0], 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        feitos += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    return feitos


def gerar(video, pasta, trechos, motor="auto", fps_txt="30/1"):
    """Gera as máscaras que faltam. Devolve {(q0, q1): arquivo} e o motor usado."""
    checar_ffmpeg()
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    motor, porque = escolher(motor)
    exe = sess = None
    if motor == "vision":
        exe = compilar_vision()
        if not exe:
            motor, porque = "rvm", "não consegui preparar o Apple Vision (falha ao compilar); vou de RobustVideoMatting."
    if porque:
        print("Máscara:", porque, flush=True)
    feitos = {}
    for q0, q1 in trechos:
        arq = pasta / f"m-{q0:06d}-{q1:06d}-{motor}.mkv"
        ok = pasta / (arq.name + ".ok")
        if arq.exists() and ok.exists():
            feitos[(q0, q1)] = arq
            continue
        t0 = time.time()
        if motor == "vision":
            n = trecho_vision(exe, video, q0, q1, arq, fps_txt)
        else:
            if sess is None:
                import onnxruntime as ort
                sess = ort.InferenceSession(str(baixar_rvm()), providers=["CPUExecutionProvider"])
            n = trecho_rvm(sess, video, q0, q1, arq, fps_txt)
        if n != q1 - q0:
            sair(f"A máscara do trecho {q0}–{q1} saiu com {n} quadros (esperava {q1 - q0}).")
        ok.write_text(json.dumps({"video": str(video), "motor": motor, "quadros": n}), encoding="utf-8")
        dt = time.time() - t0
        print(f"Máscara {q0}–{q1}: {n} quadros em {dt:.1f} s ({n / max(dt, 1e-6):.1f} quadros/s, {motor})", flush=True)
        feitos[(q0, q1)] = arq
    return feitos, motor


def main():
    utf8()
    ap = argparse.ArgumentParser(description="Máscara da pessoa para as camadas atrás dela.")
    ap.add_argument("video")
    ap.add_argument("pasta")
    ap.add_argument("--trechos", required=True)
    ap.add_argument("--motor", default="auto", choices=["auto", "vision", "rvm"])
    ap.add_argument("--fps", default="30/1")
    a = ap.parse_args()
    trechos = [tuple(int(x) for x in t.split(":")) for t in a.trechos.split(",") if t]
    feitos, motor = gerar(Path(a.video).expanduser(), Path(a.pasta).expanduser(), trechos, a.motor, a.fps)
    print(json.dumps({"motor": motor, "mascaras": [{"q0": q0, "q1": q1, "arquivo": str(f)}
                                                    for (q0, q1), f in feitos.items()]}))


if __name__ == "__main__":
    main()
