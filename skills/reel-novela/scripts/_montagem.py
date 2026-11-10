"""Montagem do projeto motion do episódio: tudo o que sai do roteiro.json + narração, sem agente.

Importada por montar_projeto.py e segunda_voz.py. A função central é `refazer`, que reescreve só os arquivos GERADOS
do projeto (index.html, barra-eventos.js, o bloco da barra no roletas.js, legenda-grupos.js, as tabelas da _regua.md
e briefings/montagem.json) e cria os compositions/atoN.html que faltam. Nunca toca num atoN.html que já existe.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import _novela as N  # noqa: E402


# ---------------------------------------------------------------- roteiro
def atos_do_roteiro(rot):
    """[{n, blocos: [índice…], cenas: […]}], conferindo o campo `ato` de cada bloco."""
    atos, ultimo = [], 0
    for i, b in enumerate(rot["blocos"]):
        n = b.get("ato")
        if not isinstance(n, int):
            N.sair(f"o bloco {i + 1} («{b.get('cena')}») do roteiro.json não tem `ato` (número inteiro). Veja "
                   "modelos/roteiro-episodio.md, «Campos para montar o projeto».")
        if n < ultimo or (ultimo and n > ultimo + 1):
            N.sair(f"`ato` do bloco «{b.get('cena')}» é {n}: os atos crescem de 1 em 1 e não voltam (anterior: {ultimo}).")
        if n != ultimo:
            atos.append({"n": n, "blocos": [], "cenas": []})
            ultimo = n
        atos[-1]["blocos"].append(i)
        atos[-1]["cenas"].append(b["cena"])
    if atos[0]["n"] != 1:
        N.sair("o primeiro bloco precisa ter `ato`: 1.")
    return atos


def flags_legenda(rot):
    f = {"a": [], "b": [], "e": [], "n": []}
    for b in rot["blocos"]:
        l = b.get("legenda") or {}
        for k, nome in (("chave", "a"), ("chave_b", "b"), ("cta", "e"), ("numeros", "n")):
            for x in l.get(k, []):
                if x not in f[nome]:
                    f[nome].append(x)
    return f


def janelas_fora(rot, mundo):
    """Os `legenda.fora` do roteiro → [(nome, ini, fim)] no tempo real."""
    out = []
    for j in (rot.get("legenda") or {}).get("fora", []):
        ini, fim = mundo.tempo(j["de"]), mundo.tempo(j["ate"])
        if fim <= ini:
            N.sair(f"a janela fora «{j.get('nome', '?')}» termina ({fim}) antes de começar ({ini}).")
        out.append((j.get("nome", "?"), round(ini, 3), round(fim, 3)))
    return out


def eventos_barra(rot, mundo_cod):
    """A lista `barra` do roteiro → (config, eventos) no tempo do código."""
    cfg, evs = {}, []
    for e in rot.get("barra") or []:
        if not isinstance(e, dict) or "em" not in e or "faz" not in e:
            N.sair(f"evento de barra inválido: {e!r}. Use {{\"em\": {{\"bloco\": …, \"palavra\": …}}, \"faz\": …}}.")
        t = mundo_cod.tempo(e["em"])
        faz = e["faz"]
        if faz not in ("relogio", "relogio_muda", "medidor", "sai", "corte", "volta"):
            N.sair(f"`faz: {faz}` não existe. Use relogio, relogio_muda, medidor, sai, corte ou volta.")
        ev = {"t": t, "faz": faz, "palavra": e["em"].get("palavra", e["em"].get("bloco", ""))}
        if faz in ("relogio", "relogio_muda"):
            if "dias" not in e:
                N.sair(f"o evento {faz} em «{e['em'].get('palavra')}» precisa de `dias`.")
            ev["dias"] = e["dias"]
            if faz == "relogio" and "dias" not in cfg:
                cfg["dias"] = e["dias"]
        if faz == "relogio_muda" and "giro" in e:
            ev["giro"] = e["giro"]
        if faz == "medidor":
            cfg.setdefault("rotulo", e.get("rotulo", ""))
            cfg.setdefault("valor", e.get("valor", 0))
        evs.append(ev)
    evs.sort(key=lambda x: x["t"])
    return cfg, evs


# ---------------------------------------------------------------- arquivos gerados
def js_barra(cfg, evs):
    linhas = ["// GERADO por montar_projeto.py / segunda_voz.py a partir da lista `barra` do roteiro.json. Tempos no tempo do",
              "// código (VOZ.w os leva ao tempo real). Edição à mão se perde."]
    c = ", ".join(f"{k}: {N.json.dumps(v, ensure_ascii=False)}" for k, v in cfg.items())
    ev = ",\n".join("    " + N.json.dumps(e, ensure_ascii=False) for e in evs)
    linhas.append("window.BARRA = { " + (c + ", " if c else "") + "eventos: [\n" + ev + "\n  ] };")
    return "\n".join(linhas) + "\n"


def roletas_barra(evs):
    out = []
    n = 0
    for e in evs:
        if e["faz"] != "relogio_muda":
            continue
        n += 1
        nome = "br-dias" if n == 1 else f"br-dias-{n}"
        g = e.get("giro", [0.45, 0.70])
        out.append(f'  "{nome}": {{\n    valor: "{e["dias"]}",\n    inicio: {N.fmt(e["t"])},\n'
                   f'    pousos: {{ de: {N.fmt(e["t"] + g[0])}, ate: {N.fmt(e["t"] + g[1])} }},\n'
                   f'    ordem: "dir-esq",\n    cor: "#f3f1ec",\n    arranque: 0.06,\n    semente: {e["dias"] * 100 + 1},\n  }},')
    if not out:
        return ""
    return "Object.assign(window.ROLETAS, {\n" + "\n".join(out) + "\n});\n"


def trocar_bloco(texto, marca, novo, comentario="//"):
    ini, fim = f"{comentario} <{marca}>", f"{comentario} </{marca}>"
    m = re.search(re.escape(ini) + r"[\s\S]*?" + re.escape(fim), texto)
    if not m:
        return texto, False
    return texto[:m.start()] + ini + "\n" + novo + fim + texto[m.end():], True


def trocar_md(texto, marca, novo):
    ini, fim = f"<!-- {marca} -->", f"<!-- /{marca} -->"
    m = re.search(re.escape(ini) + r"[\s\S]*?" + re.escape(fim), texto)
    if not m:
        return texto
    return texto[:m.start()] + ini + "\n" + novo + "\n" + fim + texto[m.end():]


def montar_index(modelo, titulo, dur, janelas, n):
    clips = []
    for j in janelas:
        k = j["n"]
        clips.append(
            f'      <!-- ato{k}: {", ".join(j["cenas"])} · {N.fmt(j["codigo_ini"], 2).replace(".", ",")} (código) → '
            f'fim da fala {N.fmt(j["fala_fim"], 2).replace(".", ",")} (+0,30) -->\n'
            f'      <div id="cena-ato{k}" class="clip" data-composition-id="ato{k}" data-composition-src="compositions/ato{k}.html"\n'
            f'           data-start="{N.fmt(j["start"])}" data-duration="{N.fmt(j["dur"])}" data-track-index="{k}" '
            f'data-width="1080" data-height="1920"></div>')
    t = modelo.replace("{{ATOS}}", "\n".join(clips)).replace("{{DURACAO}}", N.fmt(dur)).replace("{{TITULO}}", titulo)
    return (t.replace("{{TRACK_BARRA}}", str(n + 1)).replace("{{TRACK_LEGENDA}}", str(n + 3))
            .replace("{{TRACK_MARCA}}", str(n + 4)))


def calcular_janelas(atos, blocos_cod, blocos_real, A, dur):
    """Janela de cada ato no tempo real: VOZ.w do início do ato; fim = início do seguinte + 0,30 s."""
    js = []
    for k, a in enumerate(atos):
        i0 = a["blocos"][0]
        codigo_ini = blocos_cod[i0]["ini"]
        start = round(N.voz_w(A, codigo_ini), 3)
        js.append({"n": a["n"], "cenas": a["cenas"], "codigo_ini": codigo_ini, "start": start, "fala_fim": 0.0})
    for k, j in enumerate(js):
        if k + 1 < len(js):
            j["fala_fim"] = js[k + 1]["start"]
            j["dur"] = round(js[k + 1]["start"] + N.SOBREPOSICAO - j["start"], 3)
        else:
            j["fala_fim"] = dur
            j["dur"] = round(dur - j["start"], 3)
    return js


def tabela_janelas(js, dur):
    L = ["| Ato | Arquivo | Prefixo | Blocos | `data-start` | Fim da fala (T) | `data-duration` | Track |",
         "|---|---|---|---|---|---|---|---|"]
    for j in js:
        L.append(f"| ato{j['n']} | `compositions/ato{j['n']}.html` | `a{j['n']}-` | {', '.join(j['cenas'])} | "
                 f"{N.fmt(j['start'], 2)} | {N.fmt(j['fala_fim'], 2)}{' (fim)' if j is js[-1] else ''} | {N.fmt(j['dur'], 2)} | {j['n']} |")
    n = len(js)
    L.append(f"| barra | `compositions/barra.html` | `br-` | — | 0 | — | {N.fmt(dur, 2)} | {n + 1} |")
    L.append(f"| legenda | `compositions/legenda.html` | `lg-` | — | 0 | — | {N.fmt(dur, 2)} | {n + 3} |")
    return "\n".join(L)


def tabela_barra(rot, cfg, evs):
    desc = {"relogio": "o relógio cai de cima", "relogio_muda": "o relógio gira para {dias}", "medidor": "o medidor cai de cima",
            "sai": "a barra sobe e sai", "corte": "a barra some em corte", "volta": "a barra volta"}
    L = ["| Tempo (código) | Palavra | Barra |", "|---|---|---|"]
    for ev in evs:
        L.append(f"| {N.fmt(ev['t'], 2)} | «{ev['palavra']}» | {desc[ev['faz']].format(dias=ev.get('dias', ''))} |")
    return "\n".join(L)


def preencher_regua(proj, rot, dur, js, cfg, evs, aula, comp=None):
    """Cria a briefings/_regua.md do modelo (se falta), preenche os {{…}} que restarem e reescreve as tabelas geradas."""
    p = proj / "briefings" / "_regua.md"
    modelo = N.MODELO_MOTION / "briefings" / "_regua.md"
    if not p.is_file():
        if not modelo.is_file():
            return
        p.write_text(modelo.read_text(encoding="utf-8"), encoding="utf-8")
    t = p.read_text(encoding="utf-8")
    ep = rot.get("episodio", "")
    for k, v in {"{{SERIE}}": Path(proj).resolve().parents[2].name, "{{EP}}": str(ep),
                 "{{TITULO_EP}}": rot.get("titulo", rot["blocos"][0]["cena"]), "{{DURACAO}}": N.fmt(dur, 2).replace(".", ","),
                 "{{NARRADOR}}": str(rot.get("voz", "")),
                 "{{AULA}}": (f"{N.fmt(aula['aula_ini'], 2)}–{N.fmt(aula['aula_fim'], 2)}".replace(".", ",") if aula else "—"),
                 "{{REGUA_SKILL}}": N.REGUA_SKILL.as_posix(),
                 "{{MOVIMENTO}}": N.MOVIMENTO.as_posix(),
                 "{{CONTRATO_HF}}": N.CONTRATO_HF.as_posix(),
                 "{{COMPONENTES}}": Path(comp or N.COMPONENTES_PADRAO).resolve().as_posix()}.items():
        t = t.replace(k, v)
    t = trocar_md(t, "novela:janelas", tabela_janelas(js, dur))
    t = trocar_md(t, "novela:barra", tabela_barra(rot, cfg, evs))
    p.write_text(t, encoding="utf-8")


def criar_atos(proj, js, forcar=False):
    modelo = (N.MODELO_MOTION / "compositions" / "ato-modelo.html").read_text(encoding="utf-8")
    novos = []
    for j in js:
        f = proj / "compositions" / f"ato{j['n']}.html"
        if f.exists() and not forcar:
            continue
        janela = f"{N.fmt(j['start'], 2).replace('.', ',')} → {N.fmt(j['start'] + j['dur'], 2).replace('.', ',')} s"
        f.write_text(modelo.replace("{{ATO}}", str(j["n"])).replace("{{BLOCOS}}", ", ".join(j["cenas"]))
                     .replace("{{JANELA}}", janela).replace("{{INICIO}}", N.fmt(j["codigo_ini"])), encoding="utf-8")
        (proj / "assets" / f"ato{j['n']}").mkdir(parents=True, exist_ok=True)
        novos.append(f.name)
    return novos


def gerar_legenda(proj, flags, janelas):
    if not shutil.which("node"):
        N.sair("o node não está instalado: ele gera a legenda (briefings/legenda-novela.cjs).")
    cmd = ["node", "briefings/legenda-novela.cjs"]
    for k in ("a", "b", "e", "n"):
        if flags[k]:
            cmd += [f"--{k}", ",".join(flags[k])]
    if janelas:
        cmd += ["--sem", ",".join(f"{N.fmt(i)}-{N.fmt(f)}" for _, i, f in janelas)]
    r = subprocess.run(cmd, cwd=proj, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        N.sair("a legenda não gerou:\n" + (r.stdout + r.stderr)[-600:])
    avisos = [l for l in r.stdout.splitlines() if "aviso" in l.lower() or "sozinha" in l or "passa de" in l]
    return cmd, avisos


def refazer(proj, ep, rot, real, cod, A, dur, aula, log=print, comp=None):
    """Reescreve os arquivos gerados do projeto. real/cod = Mundo no tempo real e no tempo do código.
    comp = a pasta dos componentes usada (só para o caminho na _regua.md)."""
    atos = atos_do_roteiro(rot)
    js = calcular_janelas(atos, cod.blocos, real.blocos, A, dur)
    modelo = (N.MODELO_MOTION / "index.html").read_text(encoding="utf-8")
    titulo = rot.get("titulo") or f"{proj.parents[2].name} · ep{rot.get('episodio', '')}"
    (proj / "index.html").write_text(montar_index(modelo, titulo, dur, js, len(atos)), encoding="utf-8")
    cfg, evs = eventos_barra(rot, cod)
    (proj / "assets" / "barra-eventos.js").write_text(js_barra(cfg, evs), encoding="utf-8")
    rj = proj / "assets" / "roletas.js"
    if rj.is_file():
        t, ok = trocar_bloco(rj.read_text(encoding="utf-8"), "novela:barra", roletas_barra(evs))
        if not ok:
            log("aviso: assets/roletas.js sem os marcadores <novela:barra>; o som dos tiques do relógio não foi registrado.")
        rj.write_text(t, encoding="utf-8")
    novos = criar_atos(proj, js)
    flags = flags_legenda(rot)
    fora = janelas_fora(rot, real)
    cmd, avisos = gerar_legenda(proj, flags, fora)
    preencher_regua(proj, rot, dur, js, cfg, evs, aula, comp)
    resumo = {"duracao": dur, "janelas": js, "barra": {"config": cfg, "eventos": evs},
              "legenda": {"flags": flags, "fora": [{"nome": n, "ini": i, "fim": f} for n, i, f in fora], "comando": " ".join(cmd)}}
    N.gravar(proj / "briefings" / "montagem.json", resumo)
    return resumo, novos, avisos
