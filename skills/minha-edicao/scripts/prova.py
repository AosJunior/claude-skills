# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.48"]
# ///
"""/minha-edicao, prova antes de gravar: 1 quadro-teste por bloco, o vídeo da pessoa com a receita ao lado da referência.

Uso:  uv run "<skill>/scripts/prova.py" "<prova.json>"

Grava, na pasta do prova.json, prova/<bloco>.png (referência à esquerda, vídeo dela com a receita à direita) e
prova/folha.png (todos os blocos). Cada quadro sai no tamanho 1080x1920; zoom, LUT e tela dividida são aplicados
no quadro dela; textos usam os arquivos de fonte de verdade; "lugar" desenha a caixa de uma inserção ainda sem
conteúdo, com o nome dela. Caminho que começa com marca/ é procurado subindo a partir da pasta do prova.json.

prova.json:
{
 "lut": "marca/cor/look.cube",                       opcional; aplicado em todo quadro dela
 "ancora": [0.49, 0.36],                             ponto que fica parado no zoom (fração x, y)
 "blocos": [
  {"nome": "1-gancho", "ref": ["<referência>", 2.0], "video": ["<vídeo dela>", 5.0], "zoom": 1.0,
   "dividida": {"corte": 960, "topo": ["<vídeo de cima>", 1.0], "recorte_y": 450},
   "elementos": [
    {"tipo": "texto", "texto": "lojinha", "fonte": "marca/fontes/X.otf", "tamanho": 116, "pe": 1190,
     "cor": "#FFFFFF", "sombra": 0.45},
    {"tipo": "caixa", "x": 91, "y": 908, "w": 898, "h": 104, "raio": 17, "fundo": "#FCFCFC",
     "texto": "Ter loja virou coisa de pobre?", "fonte": "marca/fontes/X.otf", "tamanho": 58, "tinta": "#111111"},
    {"tipo": "imagem", "arquivo": "<png ou jpg>", "x": 30, "y": 190, "w": 390, "rot": -6, "raio": 26},
    {"tipo": "lugar", "x": 30, "y": 190, "w": 390, "h": 693, "rotulo": "mosaico atrás dela"}
  ]}
 ]
}
"""
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

L, A = 1080, 1920


def sair(msg):
    print(msg)
    sys.exit(1)


def achar(caminho, base):
    """Resolve um caminho do prova.json: marca/... sobe até achar; o resto é relativo à pasta do json."""
    p = Path(caminho)
    if p.is_absolute():
        return p
    if p.parts and p.parts[0] == "marca":
        for pasta in [base, *base.parents]:
            if (pasta / p).exists():
                return pasta / p
    return base / p


def extrair(video, t, saida, filtro=""):
    """Um quadro em 1080x1920 (cobre e corta ao centro), com filtro extra opcional (zoom, LUT)."""
    vf = f"scale={L}:{A}:force_original_aspect_ratio=increase,crop={L}:{A}" + (f",{filtro}" if filtro else "")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video),
                        "-frames:v", "1", "-vf", vf, str(saida)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=saida.parent)
    if r.returncode or not saida.exists():
        sair(f"Não consegui tirar o quadro de {video} em {t} s: {r.stderr.strip()[-300:]}")


def filtro_dela(bloco, lut, ancora, pasta):
    """Zoom ancorado (recorte e escala de volta) e LUT. O .cube é copiado para a pasta de trabalho: o lut3d do
    ffmpeg não aceita caminho com ':' (Windows) e o ffmpeg roda com cwd nela."""
    partes = []
    z = float(bloco.get("zoom", 1.0))
    if z > 1.0:
        w, h = round(L / z / 2) * 2, round(A / z / 2) * 2
        x = min(max(0, round(ancora[0] * L - ancora[0] * w)), L - w)
        y = min(max(0, round(ancora[1] * A - ancora[1] * h)), A - h)
        partes.append(f"crop={w}:{h}:{x}:{y},scale={L}:{A}")
    if lut:
        shutil.copyfile(lut, pasta / "look.cube")
        partes.append("lut3d=file=look.cube:interp=tetrahedral")
    return ",".join(partes)


def fonte_css(arquivo, nomes):
    if arquivo not in nomes:
        nomes[arquivo] = f"f{len(nomes)}"
    return nomes[arquivo]


def elemento(e, base, nomes):
    tipo = e.get("tipo")
    if tipo == "texto":
        f = fonte_css(str(achar(e["fonte"], base)), nomes)
        som = float(e.get("sombra", 0.45))
        tam = int(e.get("tamanho", 116))
        # "pe" é a linha de base; com line-height = corpo, ela fica a ~0,8 do corpo abaixo do topo (±10 px)
        topo = int(e["pe"]) - round(0.8 * tam)
        return (f'<div style="position:absolute;left:{e.get("margem", 70)}px;right:{e.get("margem", 70)}px;'
                f'top:{topo}px;height:{tam}px;line-height:{tam}px;text-align:center;font-family:{f};'
                f'font-size:{tam}px;color:{e.get("cor", "#FFFFFF")};'
                f'text-shadow:0 2px 14px rgba(0,0,0,{som})">{html.escape(e["texto"])}</div>')
    if tipo == "caixa":
        f = fonte_css(str(achar(e["fonte"], base)), nomes) if e.get("fonte") else "sans-serif"
        return (f'<div style="position:absolute;left:{e["x"]}px;top:{e["y"]}px;width:{e["w"]}px;height:{e["h"]}px;'
                f'border-radius:{e.get("raio", 0)}px;background:{e.get("fundo", "#FCFCFC")};display:flex;'
                f'align-items:center;justify-content:center;font-family:{f};font-size:{e.get("tamanho", 58)}px;'
                f'color:{e.get("tinta", "#111111")}">{html.escape(e.get("texto", ""))}</div>')
    if tipo == "imagem":
        src = achar(e["arquivo"], base).resolve().as_uri()
        return (f'<img src="{src}" style="position:absolute;left:{e["x"]}px;top:{e["y"]}px;width:{e["w"]}px;'
                f'border-radius:{e.get("raio", 0)}px;transform:rotate({e.get("rot", 0)}deg);'
                f'box-shadow:0 8px 30px rgba(0,0,0,{e.get("sombra", 0.35)})">')
    if tipo == "lugar":
        return (f'<div style="position:absolute;left:{e["x"]}px;top:{e["y"]}px;width:{e["w"]}px;height:{e["h"]}px;'
                f'border:6px dashed #FFE600;background:rgba(255,230,0,.18);border-radius:{e.get("raio", 0)}px;'
                f'transform:rotate({e.get("rot", 0)}deg);color:#FFE600;font:bold 40px sans-serif;display:flex;'
                f'align-items:center;justify-content:center;text-align:center">{html.escape(e.get("rotulo", ""))}</div>')
    sair(f"Elemento sem tipo conhecido (texto, caixa, imagem, lugar): {e}")


def quadro_html(bloco, fundo, topo, base, nomes):
    d = bloco.get("dividida")
    if d and topo:
        c, ry = int(d.get("corte", 960)), int(d.get("recorte_y", 0))
        t = topo.resolve().as_uri()
        camada = (f'<div style="position:absolute;left:0;top:0;width:{L}px;height:{c}px;overflow:hidden">'
                  f'<img src="{t}" style="position:absolute;width:100%;height:100%;object-fit:cover;'
                  f'filter:blur(28px);transform:scale(1.15)">'
                  f'<img src="{t}" style="position:absolute;left:{(L - 720) // 2}px;width:720px;height:{c}px;'
                  f'object-fit:cover"></div>'
                  f'<div style="position:absolute;left:0;top:{c}px;width:{L}px;height:{A - c}px;overflow:hidden">'
                  f'<img src="{fundo.resolve().as_uri()}" style="position:absolute;top:{-ry}px;width:{L}px"></div>')
    else:
        camada = f'<img src="{fundo.resolve().as_uri()}" style="position:absolute;width:{L}px;height:{A}px">'
    return camada + "".join(elemento(e, base, nomes) for e in bloco.get("elementos", []))


def navegador(pw):
    try:
        return pw.chromium.launch()
    except Exception as e:
        if "Executable doesn't exist" not in str(e) and "playwright install" not in str(e):
            raise
    print("Primeira vez: baixando o navegador que desenha a prova (uns 150 MB, 1 a 3 min)...", flush=True)
    if subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"]).returncode:
        sair("Não consegui baixar o navegador. Confira a internet e rode de novo.")
    return pw.chromium.launch()


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if len(sys.argv) != 2:
        sair(__doc__)
    if not shutil.which("ffmpeg"):
        sair("Falta o ffmpeg. Mac: brew install ffmpeg · Windows: winget install Gyan.FFmpeg")
    cfg_path = Path(sys.argv[1]).resolve()
    base = cfg_path.parent
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    pasta = base / "prova"
    trabalho = pasta / ".quadros"
    trabalho.mkdir(parents=True, exist_ok=True)
    lut = achar(cfg["lut"], base) if cfg.get("lut") else None
    if lut and not lut.exists():
        sair(f"Não achei o LUT: {lut}")
    ancora = cfg.get("ancora", [0.5, 0.36])

    paginas = []
    for b in cfg["blocos"]:
        n = b["nome"]
        ref, dela = trabalho / f"{n}-ref.png", trabalho / f"{n}-dela.png"
        extrair(achar(b["ref"][0], base), float(b["ref"][1]), ref)
        extrair(achar(b["video"][0], base), float(b["video"][1]), dela, filtro_dela(b, lut, ancora, trabalho))
        topo = None
        if b.get("dividida", {}).get("topo"):
            topo = trabalho / f"{n}-topo.png"
            extrair(achar(b["dividida"]["topo"][0], base), float(b["dividida"]["topo"][1]), topo)
        nomes = {}
        corpo = quadro_html(b, dela, topo, base, nomes)
        fontes = "".join(f'@font-face{{font-family:{v};src:url("{Path(k).resolve().as_uri()}")}}'
                         for k, v in nomes.items())
        rotulo = 'position:absolute;top:-70px;font:bold 44px sans-serif;color:#fff'
        pagina = (f'<!doctype html><meta charset="utf-8"><style>{fontes}body{{margin:0;background:#222}}'
                  f'.q{{position:absolute;top:80px;width:{L}px;height:{A}px;overflow:hidden}}</style>'
                  f'<div class="q" style="left:0;overflow:visible"><div style="{rotulo}">referência</div>'
                  f'<img src="{ref.resolve().as_uri()}" style="width:{L}px;height:{A}px"></div>'
                  f'<div style="position:absolute;left:{L + 40}px;top:10px;font:bold 44px sans-serif;color:#fff">'
                  f'{html.escape(n)} · seu vídeo com a receita</div>'
                  f'<div class="q" style="left:{L + 40}px">{corpo}</div>')
        arq = trabalho / f"{n}.html"
        arq.write_text(pagina, encoding="utf-8")
        paginas.append((n, arq))

    from playwright.sync_api import sync_playwright
    saidas = []
    with sync_playwright() as pw:
        nav = navegador(pw)
        pg = nav.new_page(viewport={"width": 2 * L + 40, "height": A + 80}, device_scale_factor=0.5)
        for n, arq in paginas:
            pg.goto(arq.as_uri())
            pg.wait_for_load_state("networkidle")
            pg.evaluate("document.fonts.ready")
            out = pasta / f"{n}.png"
            pg.screenshot(path=str(out))
            saidas.append(out)
        folha = trabalho / "folha.html"
        folha.write_text('<!doctype html><body style="margin:0;background:#111">' + "".join(
            f'<img src="{s.resolve().as_uri()}" style="display:block;width:{L + 20}px">' for s in saidas), encoding="utf-8")
        pg2 = nav.new_page(viewport={"width": L + 20, "height": 600})
        pg2.goto(folha.as_uri())
        pg2.wait_for_load_state("networkidle")
        pg2.screenshot(path=str(pasta / "folha.png"), full_page=True)
        nav.close()
    print(f"Prova: {len(saidas)} blocos em {pasta} (folha.png junta todos).")


if __name__ == "__main__":
    main()
