#!/usr/bin/env python3
"""Custo de uma sessão do Claude Code, por área e por agente, em US$ equivalentes de API.

Soma o `usage` de cada chamada (sessão principal e subagentes), sem repetir a mesma mensagem, e aplica a tabela
de preços abaixo. É o custo que a sessão teria na API; numa assinatura, serve para comparar fases, áreas e peças.

Cada agente lançado pela sessão principal é uma área: a linha dele mostra o próprio custo e, na coluna «área», a
soma dele com os agentes que ele lançou (que aparecem recuados logo abaixo). «ctx» é o contexto médio por chamada,
em milhares de tokens: é ele, vezes o número de chamadas, que faz o custo. «!» marca agente com mais de 60 chamadas.

Uso:
    python3 custo_sessao.py <id-da-sessão> [--projeto <pasta de ~/.claude/projects>]

Sem --projeto, usa a pasta do diretório atual. O id da sessão é o nome do .jsonl em ~/.claude/projects/<projeto>/.
"""
import collections
import glob
import json
import os
import re
import sys

# US$ por milhão de tokens. Fonte: tabela da skill claude-api (cache de 03/11/2026). Confira antes de confiar:
# escrita de cache = 1,25x a entrada (5 min) e 2x (1 h); a leitura de cache do Haiku foi suposta em 0,1x.
PRECOS = {
    "claude-fable-5-2": {"in": 8.0, "out": 40.0, "cr": 0.20},
    "claude-opus-5-5": {"in": 4.0, "out": 20.0, "cr": 0.20},
    "claude-sonnet-5-5": {"in": 2.0, "out": 10.0, "cr": 0.10},
    "claude-haiku-5-5": {"in": 0.10, "out": 0.50, "cr": 0.01},
}
CHAMADAS_DEMAIS = 60


def somar(caminho):
    """Devolve (começo do primeiro pedido, {modelo: contadores}) de um .jsonl de sessão ou de agente."""
    vistos, inicio = {}, None
    for linha in open(caminho, encoding="utf-8"):
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if inicio is None and d.get("type") == "user":
            c = d.get("message", {}).get("content")
            if isinstance(c, list):
                c = " ".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
            inicio = (c or "")[:60].replace("\n", " ")
        if d.get("type") != "assistant":
            continue
        m = d.get("message", {})
        u = m.get("usage") or {}
        if u:
            vistos[m.get("id") or d.get("uuid")] = (m.get("model"), u)
    total = collections.defaultdict(collections.Counter)
    for modelo, u in vistos.values():
        c = total[modelo]
        cc = u.get("cache_creation") or {}
        c["req"] += 1
        c["in"] += u.get("input_tokens") or 0
        c["out"] += u.get("output_tokens") or 0
        c["cr"] += u.get("cache_read_input_tokens") or 0
        c["w5"] += cc.get("ephemeral_5m_input_tokens") or (0 if cc else u.get("cache_creation_input_tokens") or 0)
        c["w1"] += cc.get("ephemeral_1h_input_tokens") or 0
    return inicio, total


def dolares(modelo, c):
    p = PRECOS.get(modelo)
    if not p:
        return None
    return (c["in"] * p["in"] + c["w5"] * p["in"] * 1.25 + c["w1"] * p["in"] * 2 + c["cr"] * p["cr"]
            + c["out"] * p["out"]) / 1e6


def custo(total):
    return sum(dolares(m, c) or 0 for m, c in total.items())


def carregar(base):
    """Lê cada subagente da sessão com o pai, a descrição e o esforço que o lançamento gravou no .meta.json."""
    agentes = {}
    for p in sorted(glob.glob(base + "/subagents/agent-*.jsonl")):
        ident = os.path.basename(p)[len("agent-"):-len(".jsonl")]
        try:
            meta = json.load(open(p[:-len(".jsonl")] + ".meta.json", encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
        inicio, total = somar(p)
        agentes[ident] = {"pai": meta.get("parentAgentId"), "nome": meta.get("description") or inicio or ident,
                          "esforco": meta.get("effort") or "", "total": total, "filhos": []}
    for ident, a in agentes.items():
        if a["pai"] in agentes:
            agentes[a["pai"]]["filhos"].append(ident)
        else:
            a["pai"] = None
    return agentes


def da_area(agentes, ident):
    a = agentes[ident]
    return custo(a["total"]) + sum(da_area(agentes, f) for f in a["filhos"])


def linha(nome, esforco, total, area=None):
    for modelo, c in total.items():
        v = dolares(modelo, c)
        ctx = (c["in"] + c["cr"] + c["w5"] + c["w1"]) / max(c["req"], 1) / 1000
        marca = "!" if c["req"] > CHAMADAS_DEMAIS else " "
        valor = f"{v:7.2f}" if v is not None else "   s/p "
        curto = str(modelo).replace("claude-", "")[:11]
        print(f"{nome[:38]:38} {curto:11} {esforco[:6]:6} {c['req']:4d}{marca} {ctx:6.0f} {c['out'] / 1000:7.0f} {valor}"
              + (f" {area:7.2f}" if area is not None else ""))
        area = None


def mostrar(agentes, ident, recuo=0):
    a = agentes[ident]
    linha("  " * recuo + ("└ " if recuo else "") + a["nome"], a["esforco"], a["total"],
          da_area(agentes, ident) if recuo == 0 else None)
    for f in a["filhos"]:
        mostrar(agentes, f, recuo + 1)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) > 1 else 1)
    sessao = sys.argv[1]
    if "--projeto" in sys.argv:
        projeto = sys.argv[sys.argv.index("--projeto") + 1]
    else:
        projeto = re.sub(r"[^A-Za-z0-9]", "-", os.getcwd())   # como o Claude Code nomeia a pasta (Mac e Windows)
    base = os.path.expanduser(f"~/.claude/projects/{projeto}/{sessao}")
    if not os.path.exists(base + ".jsonl"):
        sys.exit(f"Sessão não encontrada: {base}.jsonl")
    _, principal = somar(base + ".jsonl")
    agentes = carregar(base)
    print(f"{'quem':38} {'modelo':11} {'esf.':6} {'ch.':>4}  {'ctx':>6} {'saída':>7} {'US$':>7} {'área':>7}")
    linha("SESSÃO PRINCIPAL", "", principal)
    for ident, a in agentes.items():
        if a["pai"] is None:
            mostrar(agentes, ident)
    da_principal = custo(principal)
    geral = da_principal + sum(custo(a["total"]) for a in agentes.values())
    print(f"\nTOTAL: US$ {geral:.2f} (equivalente de API, preços de 03/11/2026). "
          f"Sessão principal: {100 * da_principal / max(geral, 0.01):.0f} % do total.")
    print("ctx e saída em milhares de tokens; «área» soma o agente com os que ele lançou.")


if __name__ == "__main__":
    main()
