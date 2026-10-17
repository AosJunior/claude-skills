# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.48"]
# ///
"""/inserir: print real da página de uma marca citada no vídeo (a primeira tela do site, como a pessoa vê).

Uso:  uv run "<skill>/scripts/print.py" "https://www.capcut.com" "<pasta insercoes>/prints/capcut.png"
      --computador   tela de computador (1280×800); o padrão é a tela de celular (390×844), que enche melhor o 9:16
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import navegador, sair, utf8

ACEITAR = re.compile(r"^(aceitar|aceito|concordo|entendi|ok|accept|allow all|got it|i agree|agree)", re.I)


def main():
    utf8()
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(args) != 2:
        sair('Uso: uv run print.py "https://site" "saida.png" [--computador]')
    url, saida = args
    if not url.startswith("http"):
        url = "https://" + url
    celular = "--computador" not in sys.argv
    saida = Path(saida).expanduser().resolve()
    saida.parent.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        nav = navegador(pw)
        ctx = nav.new_context(
            viewport={"width": 390, "height": 844} if celular else {"width": 1280, "height": 800},
            device_scale_factor=3 if celular else 2, is_mobile=celular, locale="pt-BR")
        pag = ctx.new_page()
        try:
            pag.goto(url, wait_until="domcontentloaded", timeout=30000)
            pag.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass                                   # site que nunca "termina" de carregar: fotografa o que tem
        try:                                        # fecha o aviso de cookies, se houver
            pag.get_by_role("button", name=ACEITAR).first.click(timeout=1500)
        except Exception:
            pass
        pag.wait_for_timeout(1500)
        pag.screenshot(path=str(saida))
        titulo = pag.title()
        nav.close()
    print(f"Print: {saida} · {titulo}")
    print("Abra o print e confira: página certa, sem aviso de cookies na frente, sem dado pessoal.")


if __name__ == "__main__":
    main()
