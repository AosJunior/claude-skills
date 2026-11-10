#!/usr/bin/env python3
"""Monta o projeto motion do episódio (sequencia/motion/) do roteiro.json + brutos/narracao/, sem agente.

Uso:
  python3 montar_projeto.py <epNN> [--componentes <pasta>] [--esqueleto] [--forcar-atos]

O que faz:
  1. copia o esqueleto (modelos/motion/) para <epNN>/sequencia/motion/ (só o que falta; --esqueleto sobrescreve);
  2. copia os componentes aprovados da série (novela.css, novela.js, legenda.html, fontes) de --componentes
     (padrão: modelos/componentes/ desta skill) e, sempre, a mola vigente (modelos/motion/assets/mola.js),
     mesmo que o projeto já exista;
  3. põe a narracao.wav e o palavras-voz.json (de brutos/narracao/) no projeto;
  4. calcula a janela de cada ato (início do primeiro bloco do ato ao início do seguinte + 0,30 s) e escreve
     index.html (janelas e duração), compositions/atoN.html vazios e válidos (só os que faltam; --forcar-atos
     recria todos), assets/barra-eventos.js e o bloco da barra no assets/roletas.js, a legenda
     (assets/legenda-grupos.js, pelo briefings/legenda-novela.cjs) e a briefings/_regua.md (com os caminhos das
     réguas e referências desta skill, e as tabelas);
  5. grava briefings/montagem.json com tudo o que resolveu (janelas, eventos da barra, flags da legenda).

Campos do roteiro.json que ele lê (modelos/roteiro-episodio.md, «Campos para montar o projeto»):
  blocos[].ato · blocos[].legenda.chave (e chave_b, cta, numeros) · legenda.fora[] · barra[].
  6. no <video data-aula> do ato que mostra a aula (o vídeo real de quem vende), escreve data-start e data-duration a
     partir do aula-janela.json (tempo local ao ato). É o único tempo numérico de um ato, e é gerado.
Pode rodar de novo sempre que o roteiro ou a narração mudar: reescreve só o que é gerado e nunca o conteúdo de um
atoN.html que já existe (só o data-start e o data-duration do <video data-aula>). Num projeto da segunda voz (tem briefings/palavras-cenas.json), use o segunda_voz.py.
Precisa de node (a legenda) e, na primeira vez em cada projeto, de internet: baixa a GSAP 3.14.2 do pacote oficial
(jsDelivr) para assets/gsap.min.js. Depois: entregar.py <epNN> --rascunho.
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _montagem as M  # noqa: E402
import _novela as N  # noqa: E402

GERADOS = {"index.html", "compositions/ato-modelo.html", "briefings/_regua.md"}


def copiar_esqueleto(proj, sobrescrever):
    n = 0
    for f in sorted(N.MODELO_MOTION.rglob("*")):
        if not f.is_file() or f.name == ".DS_Store":
            continue
        rel = f.relative_to(N.MODELO_MOTION).as_posix()
        if rel in GERADOS:
            continue
        dest = proj / rel
        if dest.exists() and not sobrescrever:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        n += 1
    return n


def copiar_componentes(proj, comp):
    for nome in ("novela.css", "novela.js"):
        if not (comp / nome).is_file():
            N.sair(f"falta {comp / nome}. Passe --componentes <pasta com novela.css e novela.js> (a biblioteca aprovada da série).")
    (proj / "assets" / "novela").mkdir(parents=True, exist_ok=True)
    for nome in ("novela.css", "novela.js"):
        shutil.copy2(comp / nome, proj / "assets" / "novela" / nome)
    if (comp / "legenda.html").is_file():
        shutil.copy2(comp / "legenda.html", proj / "compositions" / "legenda.html")
    (proj / "assets" / "fontes").mkdir(parents=True, exist_ok=True)
    (proj / "compositions").mkdir(parents=True, exist_ok=True)
    for f in (comp / "fontes").glob("*") if (comp / "fontes").is_dir() else []:
        shutil.copy2(f, proj / "assets" / "fontes" / f.name)
    # a mola vigente vem do esqueleto desta skill e entra sempre, como os componentes (o esqueleto não sobrescreve)
    mola = N.MODELO_MOTION / "assets" / "mola.js"
    if not mola.is_file():
        N.sair(f"não achei {mola}. A pasta modelos/motion/ da skill reel-novela está incompleta: reinstale a skill.")
    (proj / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(mola, proj / "assets" / "mola.js")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ep", help="pasta do episódio (ex.: <pasta da série>/ep02)")
    ap.add_argument("--componentes", help=f"pasta dos componentes (padrão: {N.COMPONENTES_PADRAO})")
    ap.add_argument("--esqueleto", action="store_true", help="sobrescreve também os arquivos do esqueleto que já existem")
    ap.add_argument("--forcar-atos", action="store_true", help="recria os atoN.html (apaga o que um agente já fez neles!)")
    a = ap.parse_args()

    ep = N.pasta_ep(a.ep)
    narr = ep / "brutos" / "narracao"
    for nome in ("narracao.wav", "palavras-voz.json", "narracao-blocos.json"):
        if not (narr / nome).is_file():
            N.sair(f"falta {narr / nome}. Narre o episódio (passo 5) e, se tiver aula, rode o encaixar_aula.py antes.")
    proj = ep / "sequencia" / "motion"
    if (proj / "briefings" / "palavras-cenas.json").is_file():
        N.sair("este projeto é de uma segunda voz (tem briefings/palavras-cenas.json). Use o segunda_voz.py: o "
               "montar_projeto.py trataria a narração nova como a das cenas e desfaria a reancoragem.")
    comp = Path(a.componentes).expanduser() if a.componentes else N.COMPONENTES_PADRAO
    if not comp.is_dir():
        N.sair(f"não achei a pasta de componentes {comp}. Passe --componentes <pasta> (ex.: <série>/componentes).")
    if not N.MODELO_MOTION.is_dir():
        N.sair(f"não achei o esqueleto {N.MODELO_MOTION}.")

    rot = N.ler(ep / "roteiro.json")
    palavras, blocos = N.ler(narr / "palavras-voz.json"), N.ler(narr / "narracao-blocos.json")
    cenas_rot, cenas_voz = [b["cena"] for b in rot["blocos"]], [b["cena"] for b in blocos]
    if cenas_rot != cenas_voz:
        N.sair("os blocos do roteiro.json e da narração não batem. Roteiro: " + ", ".join(cenas_rot) +
               ". Narração: " + ", ".join(cenas_voz) + ". Narre de novo ou corrija o roteiro.")
    aula = N.ler(narr / "aula-janela.json") if (narr / "aula-janela.json").is_file() else None
    if any(b.get("aula_depois") for b in rot["blocos"]) and not aula:
        print("aviso: o roteiro tem `aula_depois`, mas não há aula-janela.json (rode o encaixar_aula.py); "
              "os trechos fora da legenda que citam a aula vão falhar.")
    dur = round(N.duracao_de(narr / "narracao.wav"), 3)

    novos = copiar_esqueleto(proj, a.esqueleto)
    copiar_componentes(proj, comp)
    if N.garantir_gsap(proj):
        print("GSAP 3.14.2 baixada do pacote oficial (jsDelivr) para assets/gsap.min.js")
    (proj / "briefings").mkdir(parents=True, exist_ok=True)
    shutil.copy2(narr / "narracao.wav", proj / "narracao.wav")
    shutil.copy2(narr / "palavras-voz.json", proj / "briefings" / "palavras-voz.json")
    shutil.copy2(narr / "narracao-blocos.json", proj / "briefings" / "blocos-cenas.json")
    if aula:   # o tempo das cenas: a segunda voz reancora a partir deles
        shutil.copy2(narr / "aula-janela.json", proj / "briefings" / "aula-janela-cenas.json")
    N.gravar(proj / "briefings" / "cenas.json", {"duracao": dur})

    A = N.ancoras_do_voz_js(proj / "assets" / "voz.js")
    mundo = N.Mundo(palavras, blocos, aula, dur)
    if a.forcar_atos:
        for f in (proj / "compositions").glob("ato[0-9]*.html"):
            f.unlink()
    resumo, criados, avisos = M.refazer(proj, ep, rot, mundo, mundo, A, dur, aula, comp=comp)

    print(f"Projeto em {proj}: esqueleto +{novos} arquivos, duração {dur:.2f} s.")
    print("Janelas dos atos (tempo real):")
    N.tabela([("ato", "blocos", "data-start", "data-duration")] +
             [(f"ato{j['n']}", ",".join(j["cenas"]), N.fmt(j["start"]), N.fmt(j["dur"])) for j in resumo["janelas"]])
    print("Barra: " + "; ".join(f"{N.fmt(e['t'], 2)} {e['faz']}" for e in resumo["barra"]["eventos"]))
    print("Legenda fora: " + "; ".join(f"{j['nome']} {N.fmt(j['ini'], 2)}–{N.fmt(j['fim'], 2)}" for j in resumo["legenda"]["fora"]))
    for l in resumo["video_aula"]:
        print("Vídeo da aula (gerado do aula-janela.json): " + l)
    print("Atos criados (vazios): " + (", ".join(criados) if criados else "nenhum (já existiam)"))
    for av in avisos:
        print("aviso da legenda: " + av)
    print("Próximo: agentes de cena nos atoN.html; depois entregar.py " + a.ep + " --rascunho")


if __name__ == "__main__":
    main()
