#!/usr/bin/env python3
"""Confere, renderiza, mede e faz a folha de contato do episódio, sem agente (passos 7 e 10 do SKILL.md).

Uso:
  python3 entregar.py <epNN> [--rascunho] [--sem-render] [--video <mp4>] [--sem-check]

  (sem flag)     check + conferir-faixa + render de ENTREGA (1080×1920, -q delivery, 4 workers) + medidas + folha
  --rascunho     o render é de rascunho (-q draft): para direção e revisão. Só a entrega final é em qualidade de entrega
  --sem-render   não renderiza: mede e faz a folha do render que já existe (o mais novo de renders/, ou o --video)
  --sem-check    pula o check e o conferir-faixa
  --video <mp4>  com --sem-render, qual vídeo medir

Passos, parando no primeiro que falhar:
  1. `npx hyperframes@<versão do package.json> check` e `node briefings/conferir-faixa.cjs` (texto de cena abaixo de y 1430);
  2. render em sequencia/motion/renders/<série>-<epNN>-rascunho.mp4 ou -1080.mp4;
  3. medidas: largura 1080, altura 1920 e duração igual à da narracao.wav (±0,10 s);
  4. folha de contato de 1 quadro por segundo (briefings/folha.py) em renders/folha/<epNN>-NN.jpg, 8×3 quadros por folha.
Sai com 0 se tudo passou e com 1 se algo falhou (o motivo vai na linha «FALHOU»). Precisa de node, npx, ffprobe e Pillow
(ou uv, que o traz).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _novela as N  # noqa: E402

TOLERANCIA_S = 0.10


def versao_hyperframes(proj):
    pkg = N.ler(proj / "package.json")
    m = re.search(r"hyperframes@[\w.-]+", (pkg.get("scripts") or {}).get("check", ""))
    return m.group(0) if m else N.HYPERFRAMES


def rodar_vivo(cmd, cwd):
    cmd = [str(c) for c in cmd]
    cmd[0] = shutil.which(cmd[0]) or cmd[0]   # no Windows, npx é npx.cmd: o caminho completo o acha
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr)


def medir(mp4):
    r = N.rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                 "-show_entries", "format=duration", "-of", "json", mp4])
    try:
        d = json.loads(r.stdout)
        return int(d["streams"][0]["width"]), int(d["streams"][0]["height"]), float(d["format"]["duration"])
    except (ValueError, KeyError, IndexError):
        N.sair(f"o ffprobe não leu {mp4}: {r.stderr.strip()[:200]}")


def folha(proj, mp4, prefixo):
    script = proj / "briefings" / "folha.py"
    if not script.is_file():
        N.sair(f"falta {script}. Rode o montar_projeto.py --esqueleto para recuperar o esqueleto.")
    tem_pil = subprocess.run([sys.executable, "-c", "import PIL"], capture_output=True).returncode == 0
    if tem_pil:
        cmd = [sys.executable, script]
    elif shutil.which("uv"):
        cmd = ["uv", "run", "--quiet", "--with", "pillow", "python", script]
    else:
        N.sair("a folha precisa do Pillow (pip install pillow) ou do uv.")
    prefixo.parent.mkdir(parents=True, exist_ok=True)
    for velho in prefixo.parent.glob(prefixo.name + "-*.jpg"):
        velho.unlink()
    rc, out = rodar_vivo(cmd + ["--video", mp4, "--saida", prefixo], proj)
    if rc:
        N.sair("a folha não saiu:\n" + out[-500:])
    return [l for l in out.splitlines() if l.endswith(".jpg")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ep", help="pasta do episódio (ex.: <pasta da série>/ep01)")
    ap.add_argument("--rascunho", action="store_true")
    ap.add_argument("--sem-render", action="store_true")
    ap.add_argument("--sem-check", action="store_true")
    ap.add_argument("--video")
    a = ap.parse_args()

    ep = N.pasta_ep(a.ep)
    proj = ep / "sequencia" / "motion"
    if not (proj / "index.html").is_file():
        N.sair(f"{proj} não é um projeto motion. Rode o montar_projeto.py {a.ep} antes.")
    for exe in ("node", "npx", "ffprobe"):
        N.exigir(exe)
    ver = versao_hyperframes(proj)
    falhas = []

    if not a.sem_check:
        rc, out = rodar_vivo(["npx", "--yes", ver, "check"], proj)
        avisos = [l.strip() for l in out.splitlines() if "⚠" in l or "✗" in l or "error" in l.lower() and "0 error" not in l.lower()]
        print(f"check ({ver}): {'passou' if rc == 0 else 'FALHOU'}" + ("".join("\n    " + l[:150] for l in avisos[:8]) if avisos else ""))
        if rc:
            falhas.append("check do HyperFrames")
            print(out[-1200:])
        rc2, out2 = rodar_vivo(["node", "briefings/conferir-faixa.cjs"], proj)
        print(f"conferir-faixa (texto abaixo de y 1430): {'passou' if rc2 == 0 else 'FALHOU'}")
        if rc2:
            falhas.append("conferir-faixa")
            print(out2[-800:])
        if falhas:
            print("FALHOU: " + ", ".join(falhas) + ". Corrija e rode de novo; nada foi renderizado.")
            sys.exit(1)

    renders = proj / "renders"
    slug = ep.parent.name
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)
    if a.sem_render:
        if a.video:
            mp4 = Path(a.video).expanduser().resolve()
        else:
            mp4s = sorted(renders.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
            if not mp4s:
                N.sair(f"não há render em {renders}. Tire o --sem-render.")
            mp4 = mp4s[-1]
        if not mp4.is_file():
            N.sair(f"não achei {mp4}.")
        print(f"render: usando o que já existe, {mp4.name}")
    else:
        renders.mkdir(exist_ok=True)
        if a.rascunho:
            mp4 = renders / f"{slug}-{ep.name}-rascunho.mp4"
            extra = ["-q", "draft"]
        else:
            mp4 = renders / f"{slug}-{ep.name}-1080.mp4"
            extra = ["-q", "delivery", "-w", "4"]
        print(f"render {'de rascunho' if a.rascunho else 'de ENTREGA'} → {mp4.name} (alguns minutos)")
        rc, out = rodar_vivo(["npx", "--yes", ver, "render", "-o", mp4] + extra, proj)
        if rc or not mp4.is_file():
            print(out[-1200:])
            print("FALHOU: render. Veja a saída acima.")
            sys.exit(1)

    w, h, dur = medir(mp4)
    dur_voz = N.duracao_de(proj / "narracao.wav")
    ok_res = (w, h) == (1080, 1920)
    ok_dur = abs(dur - dur_voz) <= TOLERANCIA_S
    N.tabela([("medida", "esperado", "obtido", "ok"),
              ("largura × altura", "1080 × 1920", f"{w} × {h}", "sim" if ok_res else "NÃO"),
              ("duração (s)", f"{dur_voz:.3f} (narracao.wav)", f"{dur:.3f}", "sim" if ok_dur else f"NÃO (±{TOLERANCIA_S})")])
    if not ok_res:
        falhas.append(f"resolução {w}×{h}")
    if not ok_dur:
        falhas.append(f"duração {dur:.3f} s contra {dur_voz:.3f} s da narração")

    jpgs = folha(proj, mp4, renders / "folha" / ep.name)
    print(f"folha de contato: {len(jpgs)} folha(s) em {renders / 'folha'} (1 quadro por segundo, 8×3 por folha)")
    if falhas:
        print("FALHOU: " + "; ".join(falhas))
        sys.exit(1)
    print("Tudo certo." + (" Rascunho: confira a folha e, só depois da passada de direção, rode sem --rascunho."
                           if a.rascunho else " Siga para o som (passos 8 e 9)."))


if __name__ == "__main__":
    main()
