#!/usr/bin/env python3
"""Faz a versão do episódio com outra narração por reancoragem, sem refazer as cenas (nem agente).

Uso:
  python3 segunda_voz.py <epNN> <epNN-da-outra-voz> --preparar --voz <voice_id>     1º: cria a pasta da outra voz
  python3 segunda_voz.py <epNN> <epNN-da-outra-voz>                                 3º: reancora e refaz o projeto

  <epNN>                 o episódio pronto (tem sequencia/motion/ com as cenas)
  <epNN-da-outra-voz>    pasta da narração nova (ex.: ep01-b, ao lado do ep01)

Ordem completa (a pasta da outra voz precisa de um roteiro.json antes de narrar, e o --preparar o cria):
  1. --preparar --voz <voice_id>: cria <epNN-da-outra-voz>/brutos/narracao/ e grava ali uma CÓPIA do roteiro.json do
     <epNN> com o campo `voz` trocado (e sem o `take` escolhido, que era da voz antiga). Fala, texto, ato, legenda e
     barra ficam iguais: são as mesmas cenas. Não sobrescreve um roteiro.json que já exista.
  2. narre e alinhe nessa pasta (narrar.py narrar, conferir, alinhar) e rode o encaixar_aula.py nela (o `aula_depois`
     vem na cópia do roteiro; o --depois só serve a quem não o copiou).
  3. este script, sem o --preparar. Precisa de narracao.wav, palavras-voz.json, narracao-blocos.json e
     aula-janela.json em <epNN-da-outra-voz>/brutos/narracao/.

O que faz:
  1. copia o projeto de <epNN>/sequencia/motion/ para o da outra voz, sem renders/, node_modules/ nem .hyperframes/;
  2. guarda o alinhamento antigo como briefings/palavras-cenas.json (o tempo em que as cenas foram escritas);
  3. põe a narração nova no projeto (narracao.wav e briefings/palavras-voz.json);
  4. roda o ancorar.py desta skill com âncoras fixas no começo e no fim do silêncio da aula, de cada pedaço dela e
     do fim do vídeo (a aula não está no alinhamento: sem elas o VOZ.w esticaria as cenas em volta);
  5. refaz as janelas do index.html, a legenda (trechos fora e palavras-chave do roteiro, no tempo novo) e os eventos
     da barra. Os atoN.html não mudam: eles seguem a narração nova pelo assets/voz.js. A única exceção é o
     data-start/data-duration do <video data-aula> (o vídeo real da aula), que sai de novo do aula-janela.json da
     voz nova.
Pode rodar de novo: se o projeto da outra voz já existe (tem palavras-cenas.json), só reancora e refaz.
Depois: entregar.py <epNN-da-outra-voz> --rascunho. Precisa de uv e node.
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _montagem as M  # noqa: E402
import _novela as N  # noqa: E402

IGNORAR = ("renders", "node_modules", ".hyperframes", ".DS_Store")


def primeiro_que_existe(*caminhos):
    for c in caminhos:
        if Path(c).is_file():
            return Path(c)
    return None


def preparar(src, dst, voz):
    """Cria <dst>/brutos/narracao/ e a cópia do roteiro.json do episódio com a voz trocada."""
    if not voz:
        N.sair("passe --voz <voice_id> da outra voz (narrar.py vozes lista as do ElevenLabs).")
    rot_src = N.ler(src / "roteiro.json")
    alvo = dst / "roteiro.json"
    if alvo.is_file():
        atual = N.ler(alvo).get("voz")
        if atual != voz:
            N.sair(f"{alvo} já existe com outra voz ({atual}). Apague-o ou use o mesmo --voz.")
        print(f"{alvo} já existe com essa voz: nada a fazer.")
    else:
        rot = dict(rot_src)
        rot["voz"] = voz
        rot.pop("take", None)
        rot["blocos"] = [{k: v for k, v in b.items() if k != "take"} for b in rot_src["blocos"]]
        N.gravar(alvo, rot, indent=2)
        print(f"Criado {alvo}: cópia do roteiro de {src.name} com `voz` = {voz}.")
    (dst / "brutos" / "narracao").mkdir(parents=True, exist_ok=True)
    print("Próximo, nesta ordem:")
    print(f'  uv run narrar.py narrar "{alvo}" --saida "{dst / "brutos" / "narracao"}" --takes 1   (gasta crédito: confira a conta)')
    print(f'  narrar.py conferir "{dst / "brutos" / "narracao"}"  ·  narrar.py alinhar … --saida palavras-voz.json')
    print(f'  encaixar_aula.py "{dst}" --aula <aula>.wav --tempos <aula>.json')
    print(f'  segunda_voz.py "{src}" "{dst}"')


def fixas_da_aula(aula_cod, aula_novo, dur_cod, dur_novo):
    """Pares (tempo das cenas, tempo novo) nas pontas do silêncio, de cada pedaço da aula e do fim do vídeo."""
    pares = [(aula_cod["silencio_ini"], aula_novo["silencio_ini"]), (aula_cod["aula_ini"], aula_novo["aula_ini"])]
    for k, p in aula_cod["pedacos"].items():
        if k not in aula_novo["pedacos"]:
            N.sair(f"o pedaço «{k}» da aula existe nas cenas mas não na narração nova: encaixe a mesma aula nas duas.")
        pares += [(p["ini"], aula_novo["pedacos"][k]["ini"]), (p["fim"], aula_novo["pedacos"][k]["fim"])]
    pares += [(aula_cod["aula_fim"], aula_novo["aula_fim"]), (aula_cod["silencio_fim"], aula_novo["silencio_fim"]),
              (dur_cod, dur_novo)]
    out = []
    for c, n in sorted(set((round(c, 3), round(n, 3)) for c, n in pares)):
        out.append((c, n))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ep", help="episódio pronto (a origem das cenas)")
    ap.add_argument("outra", help="episódio da outra voz (tem a narração nova em brutos/narracao/)")
    ap.add_argument("--preparar", action="store_true",
                    help="só cria a pasta da outra voz, com a cópia do roteiro.json (precisa do --voz)")
    ap.add_argument("--voz", help="voice_id da outra voz (com o --preparar)")
    a = ap.parse_args()

    src, dst = N.pasta_ep(a.ep), Path(a.outra).expanduser().resolve()
    if src == dst:
        N.sair("a origem e a outra voz são a mesma pasta.")
    if a.preparar:
        preparar(src, dst, a.voz)
        return
    if not (dst / "roteiro.json").is_file():
        N.sair(f"«{a.outra}» não tem roteiro.json. Rode antes: segunda_voz.py {a.ep} {a.outra} --preparar --voz <voice_id>, "
               "narre, alinhe e encaixe a aula nessa pasta.")
    ps, pd = src / "sequencia" / "motion", dst / "sequencia" / "motion"
    narr = dst / "brutos" / "narracao"
    for nome in ("narracao.wav", "palavras-voz.json", "narracao-blocos.json", "aula-janela.json"):
        if not (narr / nome).is_file():
            N.sair(f"falta {narr / nome}. Narre a voz nova (passo 5) e rode encaixar_aula.py em {dst.name} antes.")
    ancorar = N.AQUI / "ancorar.py"
    if not ancorar.is_file():
        N.sair(f"não achei {ancorar}. A pasta scripts/ da skill reel-novela está incompleta: reinstale a skill.")

    refaz = (pd / "briefings" / "palavras-cenas.json").is_file()
    if refaz:
        print(f"{pd} já é uma segunda voz: só reancoro e refaço.")
    else:
        if not (ps / "index.html").is_file():
            N.sair(f"{ps} não é um projeto motion (falta index.html). Rode o montar_projeto.py em {src.name} antes.")
        if pd.exists():
            N.sair(f"{pd} já existe e não é uma segunda voz (sem briefings/palavras-cenas.json). Apague-o ou escolha "
                   "outra pasta: o script não sobrescreve um projeto.")
        N.copiar_arvore(ps, pd, IGNORAR)
        cenas = primeiro_que_existe(ps / "briefings" / "palavras-cenas.json", ps / "briefings" / "palavras-voz.json")
        shutil.copy2(cenas, pd / "briefings" / "palavras-cenas.json")
        # o tempo das cenas também vale para os blocos e a janela da aula: guarda para as próximas reancoragens
        b = primeiro_que_existe(ps / "briefings" / "blocos-cenas.json", src / "brutos" / "narracao" / "narracao-blocos.json")
        al = primeiro_que_existe(ps / "briefings" / "aula-janela-cenas.json", src / "brutos" / "narracao" / "aula-janela.json")
        if not b or not al:
            N.sair("faltam os blocos e a janela da aula da narração original (brutos/narracao/narracao-blocos.json e "
                   f"aula-janela.json em {src.name}).")
        shutil.copy2(b, pd / "briefings" / "blocos-cenas.json")
        shutil.copy2(al, pd / "briefings" / "aula-janela-cenas.json")
        N.gravar(pd / "briefings" / "cenas.json", {"duracao": round(N.duracao_de(ps / "narracao.wav"), 3)})
        print(f"Projeto copiado para {pd} (sem renders).")

    shutil.copy2(narr / "narracao.wav", pd / "narracao.wav")
    shutil.copy2(narr / "palavras-voz.json", pd / "briefings" / "palavras-voz.json")
    palavras_cod = N.ler(pd / "briefings" / "palavras-cenas.json")
    blocos_cod = N.ler(pd / "briefings" / "blocos-cenas.json")
    aula_cod = N.ler(pd / "briefings" / "aula-janela-cenas.json")
    palavras, blocos, aula = (N.ler(narr / n) for n in ("palavras-voz.json", "narracao-blocos.json", "aula-janela.json"))
    dur = round(N.duracao_de(narr / "narracao.wav"), 3)
    dur_cod = N.ler(pd / "briefings" / "cenas.json")["duracao"]

    fixas = fixas_da_aula(aula_cod, aula, dur_cod, dur)
    args = [pd / "briefings" / "palavras-cenas.json", pd / "briefings" / "palavras-voz.json", pd / "assets" / "voz.js"]
    for c, n in fixas:
        args += ["--fixa", f"{c}={n}"]
    saida = N.uv_run(ancorar, args)
    print("ancorar.py: " + " | ".join(l for l in saida.splitlines() if l.startswith(("Pronto", "Conferência")) or "salto" in l))

    rot_dst = N.ler(dst / "roteiro.json")
    rot = rot_dst if all("ato" in b for b in rot_dst["blocos"]) else N.ler(src / "roteiro.json")
    if rot is not rot_dst:
        print("aviso: o roteiro.json da outra voz não tem os campos de montagem (`ato`…); usei o de " + src.name + ".")
    cod = N.Mundo(palavras_cod, blocos_cod, aula_cod, dur_cod)
    real = N.Mundo(palavras, blocos, aula, dur)
    A = N.ancoras_do_voz_js(pd / "assets" / "voz.js")
    resumo, criados, avisos = M.refazer(pd, dst, rot, real, cod, A, dur, aula)

    print(f"Âncoras fixas ({len(fixas)}): " + ", ".join(f"{c}→{n}" for c, n in fixas))
    for l in resumo["video_aula"]:
        print("Vídeo da aula (gerado do aula-janela.json): " + l)
    print("Janelas dos atos (tempo real da voz nova):")
    N.tabela([("ato", "data-start", "data-duration")] +
             [(f"ato{j['n']}", N.fmt(j["start"]), N.fmt(j["dur"])) for j in resumo["janelas"]])
    print("Legenda fora: " + "; ".join(f"{j['nome']} {N.fmt(j['ini'], 2)}–{N.fmt(j['fim'], 2)}" for j in resumo["legenda"]["fora"]))
    for av in avisos:
        print("aviso da legenda: " + av)
    print(f"Pronto: {pd}. Depois: entregar.py {a.outra} --rascunho (e confira os snapshots das palavras que mudaram).")


if __name__ == "__main__":
    main()
