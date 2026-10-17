# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""/decupar, cor saudável (opcional): corrige primeiro, depois aplica UM look leve.

Uso:  uv run "<skill>/scripts/cor.py" "<pasta decupagem>"
Lê o "cor" do cortes.json, mede o vídeo e grava:
  .dados/cor.json         a medida (exposição e branco) e o filtro do ffmpeg que o cortar.py usa
  cor-antes-depois.jpg    2 quadros do vídeo cortado, antes (em cima) e depois (embaixo), para conferir a pele
Rode antes do cortar.py; ele usa a mesma conta (se faltar o cor.json, ele mede sozinho).

"cor" no cortes.json:
  {"corrigir": true,
   "look": {"nome": "Ana: Gastronômico + Verão Italiano", "contraste": -4, "sombra": -2, "calor": 0.5}}
  corrigir   exposição (só se o vídeo estiver escuro ou claro demais) e branco (tira o tom puxado da luz)
  look       UM só, vindo da skill de estilo da pessoa. contraste e sombra na escala do CapCut (-50 a 50),
             calor de 0 a 1 (tom quente suave), saturacao de -10 a 5 (opcional; 0 = não mexe)
Travas: nada de lista de looks (dois filtros por cima), saturação no máximo +5%, ajustes limitados.
"""
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import achar_pasta, fmt_num, gravar_json, ler_json, rodar, sair, utf8  # noqa: E402

AMOSTRAS = 8
MW = 96   # quadros minúsculos bastam para medir


def limitar(x, a, b):
    return max(a, min(b, x))


def ler_cor(pasta):
    p = pasta / "cortes.json"
    c = ler_json(p) if p.exists() else {}
    cor = c.get("cor")
    if not cor:
        return None
    if isinstance(cor.get("look"), list):
        sair("cortes.json, cor: é um look só. Dois filtros por cima deixam a pele laranja; escolha um.")
    return cor


def fonte(pasta, info):
    px = pasta / ".dados" / "proxy.mov"
    return str(px) if px.exists() else info["arquivo"]


def quadro_bytes(video, t, w, h, filtro=""):
    H = max(2, int(round(MW * h / w / 2)) * 2)
    vf = (filtro + "," if filtro else "") + f"scale={MW}:{H}"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                        "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    return r.stdout if r.returncode == 0 else b""


def estatisticas(px):
    """Luma média, média dos pixels quase neutros (para o branco) e croma médio (quanto de cor tem)."""
    n = len(px) // 3
    sy = ss = 0.0
    neutros = [0.0, 0.0, 0.0, 0]
    for i in range(n):
        r, g, b = px[3 * i] / 255, px[3 * i + 1] / 255, px[3 * i + 2] / 255
        y = 0.2126 * r + 0.7152 * g + 0.0722 * b
        mx, mn = max(r, g, b), min(r, g, b)
        sat = (mx - mn) / mx if mx > 0 else 0
        sy += y
        ss += mx - mn   # croma: não infla nas sombras como a saturação HSV
        if 0.25 < y < 0.92 and sat < 0.18:
            neutros[0] += r
            neutros[1] += g
            neutros[2] += b
            neutros[3] += 1
    return sy / max(1, n), neutros, ss / max(1, n)


def medir(pasta, info):
    video = fonte(pasta, info)
    w, h = info["largura"], info["altura"]
    dur = info["duracao"]
    ys, sats, acc = [], [], [0.0, 0.0, 0.0, 0]
    for k in range(AMOSTRAS):
        px = quadro_bytes(video, dur * (k + 0.5) / AMOSTRAS, w, h)
        if not px:
            continue
        y, ne, s = estatisticas(px)
        ys.append(y)
        sats.append(s)
        for j in range(4):
            acc[j] += ne[j]
    if not ys:
        sair("Não consegui ler quadros do vídeo para medir a cor.")
    y = sum(ys) / len(ys)
    ganhos = [1.0, 1.0, 1.0]
    if acc[3] > 50:
        media = [acc[j] / acc[3] for j in range(3)]
        cinza = sum(media) / 3
        # um terço do caminho até o neutro e no máximo 2,5%: tira o tom puxado sem matar a luz do ambiente
        ganhos = [round(limitar(1 + 0.35 * (cinza / m - 1), 0.975, 1.025), 4) for m in media]
    gama = 1.0
    if not 0.25 <= y <= 0.65:   # luz baixa de propósito (ambiente intimista) não é erro: só corrige o extremo
        alvo = 0.45
        g = math.log(y) / math.log(alvo) if 0 < y < 1 else 1.0
        gama = round(limitar(1 + 0.5 * (g - 1), 0.92, 1.1), 3)
    return {"luma": round(y, 4), "saturacao": round(sum(sats) / len(sats), 4), "ganhos_rgb": ganhos,
            "gama": gama, "pixels_neutros": acc[3]}


def filtro(cor, medida):
    """Filtro do ffmpeg: correção (gama e branco) e depois o look. Volta "" se não há nada a fazer."""
    if not cor:
        return ""
    partes = []
    if cor.get("corrigir", True) and medida:
        g = medida.get("gama", 1.0)
        if abs(g - 1) > 0.005:
            partes.append(f"eq=gamma={g:.3f}")
        r, gg, b = medida.get("ganhos_rgb", [1, 1, 1])
        if max(abs(r - 1), abs(gg - 1), abs(b - 1)) > 0.004:
            partes.append(f"colorchannelmixer=rr={r:.4f}:gg={gg:.4f}:bb={b:.4f}")
    look = cor.get("look")
    if look:
        c = limitar(float(look.get("contraste", 0)), -20, 20)
        s = limitar(float(look.get("sombra", 0)), -20, 20)
        k = limitar(float(look.get("calor", 0)), 0, 1)
        sat = limitar(float(look.get("saturacao", 0)), -10, 5)
        if c or sat:
            partes.append(f"eq=contrast={1 + c / 100:.3f}:saturation={1 + sat / 100:.3f}")
        if s:
            partes.append(f"curves=all='0/0 0.12/{0.12 + 0.005 * s:.4f} 0.3/{0.3 + 0.0035 * s:.4f} 0.6/0.6 1/1'")
        if k:
            partes.append(f"colorbalance=rs={0.02 * k:.4f}:bs={-0.03 * k:.4f}:rm={0.04 * k:.4f}:"
                          f"gm={0.006 * k:.4f}:bm={-0.045 * k:.4f}:rh={0.02 * k:.4f}:bh={-0.03 * k:.4f}:pl=1")
    return ",".join(partes)


def filtro_da_pasta(pasta, info):
    """O que o cortar.py chama: lê o cortes.json, usa a medida gravada ou mede agora."""
    cor = ler_cor(pasta)
    if not cor:
        return ""
    p = pasta / ".dados" / "cor.json"
    medida = ler_json(p).get("medida") if p.exists() else None
    if medida is None and cor.get("corrigir", True):
        medida = medir(pasta, info)
    return filtro(cor, medida)


def tempos_do_corte(pasta, info, n=2):
    seg = pasta / ".dados" / "segmentos.json"
    fps = info["fps_num"] / info["fps_den"]
    ss = ler_json(seg) if seg.exists() else None
    if not ss and (pasta / "cortes.json").exists():
        from cortar import ler_cortes, segmentos   # quadros do vídeo cortado, mesmo antes do primeiro render
        pal = ler_json(pasta / ".dados" / "palavras.json")["palavras"]
        frases = {f["id"]: f for f in ler_json(pasta / ".dados" / "frases.json")}
        pausa, trechos = ler_cortes(pasta, frases, info["duracao"])
        ss = segmentos(trechos, pal, pausa, info)[0]
    if ss:
        escolhidos = [ss[len(ss) // 4], ss[(3 * len(ss)) // 4]][:n]
        return [(s["fi"] + s["fo"]) / 2 / fps for s in escolhidos]
    return [info["duracao"] * 0.3, info["duracao"] * 0.7][:n]


def main():
    utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sair(__doc__)
    pasta = achar_pasta(args[0])
    info = ler_json(pasta / ".dados" / "info.json")
    cor = ler_cor(pasta)
    if not cor:
        sair("O cortes.json não tem \"cor\": o vídeo sai com a cor original.")
    medida = medir(pasta, info) if cor.get("corrigir", True) else None
    f = filtro(cor, medida)
    gravar_json(pasta / ".dados" / "cor.json", {"medida": medida, "filtro": f})
    video = fonte(pasta, info)
    w, h = info["largura"], info["altura"]
    alt = 720
    larg = max(2, int(round(alt * w / h / 2)) * 2)
    ts = tempos_do_corte(pasta, info)
    entradas, fc = [], []
    for j, t in enumerate(ts):
        entradas += ["-ss", f"{t:.2f}", "-i", video]
        fc.append(f"[{j}:v]scale={larg}:{alt},setsar=1,split[a{j}][b{j}]")
        fc.append(f"[b{j}]{f or 'null'}[d{j}]")
    fc.append("".join(f"[a{j}]" for j in range(len(ts))) + f"hstack={len(ts)}[antes]")
    fc.append("".join(f"[d{j}]" for j in range(len(ts))) + f"hstack={len(ts)}[depois]")
    fc.append("[antes][depois]vstack=2[o]")
    saida = pasta / "cor-antes-depois.jpg"
    r = rodar(["ffmpeg", "-hide_banner", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(fc),
               "-map", "[o]", "-frames:v", "1", "-q:v", "3", saida])
    if r.returncode != 0:
        sair(f"Não consegui montar a folha antes × depois:\n{r.stderr[-800:]}")
    # trava de saturação: compara antes e depois nos mesmos quadros
    s0 = s1 = 0.0
    for t in ts:
        s0 += estatisticas(quadro_bytes(video, t, w, h))[2]
        s1 += estatisticas(quadro_bytes(video, t, w, h, f) if f else quadro_bytes(video, t, w, h))[2]
    sub = (s1 / max(s0, 1e-6) - 1) * 100
    if medida:
        print(f"Medida: luz média {fmt_num(100 * medida['luma'])}% · branco R×{fmt_num(medida['ganhos_rgb'][0], 3)} "
              f"G×{fmt_num(medida['ganhos_rgb'][1], 3)} B×{fmt_num(medida['ganhos_rgb'][2], 3)} · "
              f"gama {fmt_num(medida['gama'], 3)}")
    print(f"Look: {(cor.get('look') or {}).get('nome', 'nenhum')} · saturação {'+' if sub >= 0 else ''}{fmt_num(sub)}%")
    if sub > 10:
        print("ATENÇÃO: a saturação subiu mais de 10%. Baixe o calor ou ponha \"saturacao\": -3 no look.")
    elif sub < -15:
        print("ATENÇÃO: a cor ficou lavada (saturação caiu mais de 15%). Confira a folha; tente \"corrigir\": false.")
    print(f"Filtro: {f or '(nenhum)'}")
    print(f"Folha para conferir a pele: {saida.name} (em cima antes, embaixo depois).")


if __name__ == "__main__":
    main()
