# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""/minha-edicao: traz para marca/estilo.md uma receita de estilo gravada na versão de 17/10 (a aula).

Naquela versão, a /minha-edicao gravava o estilo como uma skill em ~/.claude/skills/<nome>/SKILL.md. Hoje o estilo
mora em <pasta de edição>/marca/estilo.md, que a /decupar, a /inserir, a /sonorizar e a /criticar leem.

Uso:
  uv run "<skill>/scripts/importar_estilo.py" --listar [--skills-dir <pasta>]
  uv run "<skill>/scripts/importar_estilo.py" <nome da receita> --pasta "<pasta de edição>"
        [--skills-dir <pasta>] [--fontes-de <pasta>]... [--simular]

--listar     mostra as receitas de estilo no formato antigo (e as de formato, que não precisam de importação).
--pasta      a pasta de edição; o arquivo sai em <pasta>/marca/estilo.md e as fontes achadas em marca/fontes/.
--fontes-de  pasta onde procurar os arquivos de fonte que a receita cita (pode repetir). Procura também na pasta
             da própria receita e nas pastas de fontes do sistema.
--simular    escreve o estilo.md na tela, sem gravar nada.
--skills-dir pasta das skills (padrão: ~/.claude/skills).

Não apaga nem altera a receita antiga e não sobrescreve um marca/estilo.md que já exista. No fim, diz o que trouxe
e o que falta perguntar (arquivos de fonte, universo da trilha, o que nunca pode...).
"""
import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

DO_KIT = {"decupar", "inserir", "sonorizar", "criticar", "minha-edicao", "reel-novela", "docs-init", "primeiro-valor"}
FONTE = re.compile(r"[\w][\w .\-]*\.(?:otf|ttf)", re.I)

MELHORAR = """## Melhorar esta receita

Ao entregar cada vídeo, pergunte: "O que você corrigiu na mão?". Cada correção, e cada item que a
/criticar reprovou duas vezes seguidas, vira regra aqui: troque a regra antiga pela nova (uma regra
por assunto, nunca duas versões), acrescente uma linha no Histórico com a data e o que mudou, e
mostre à pessoa a linha alterada."""

# título da seção antiga (minúsculo, sem acento) -> seção do estilo novo
MAPA = {
    "fontes": "fontes", "fonte": "fontes",
    "parametros": "legenda", "legenda": "legenda",
    "cortes e ritmo": "corte", "corte e zoom": "corte", "corte": "corte", "cortes": "corte", "ritmo": "corte",
    "cor": "cor",
    "som": "som",
    "como aplicar": "aplicar", "conferir": "conferir", "melhorar esta receita": None, "historico": "historico",
}
ORDEM_COMPOSICAO = ("cartoes", "letterings", "transicoes", "composicao", "cartao")


def sem_acento(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn").lower().strip()


# ---------------------------------------------------------------- ler a receita antiga

def ler_receita(arq):
    """Devolve dict: nome, description, h1, intro, secoes [(titulo, corpo)]."""
    texto = Path(arq).read_text(encoding="utf-8").replace("\r\n", "\n")
    fm = {}
    m = re.match(r"---\n(.*?)\n---\n", texto, re.S)
    if m:
        for linha in m.group(1).split("\n"):
            k, _, v = linha.partition(":")
            fm[k.strip()] = v.strip()
        texto = texto[m.end():]
    secoes, atual, dentro = [], None, False
    h1, intro = "", []
    for linha in texto.split("\n"):
        if linha.startswith("```"):
            dentro = not dentro
        if not dentro and linha.startswith("# ") and not h1:
            h1 = linha[2:].strip()
        elif not dentro and linha.startswith("## "):
            atual = [linha[3:].strip(), []]
            secoes.append(atual)
        elif atual is not None:
            atual[1].append(linha)
        elif h1:
            intro.append(linha)
    return {"nome": fm.get("name", ""), "description": fm.get("description", ""), "h1": h1,
            "intro": "\n".join(intro).strip(), "secoes": [(t, "\n".join(c).strip()) for t, c in secoes]}


def tipo_da_receita(r):
    t = {sem_acento(s) for s, _ in r["secoes"]}
    if t & {"regras do formato", "como editar", "blocos"}:
        return "formato"
    if "melhorar esta receita" in t and t & {"parametros", "legenda", "fontes"}:
        return "estilo"
    return None


def candidatas(skills_dir):
    achadas = []
    base = Path(skills_dir)
    if not base.is_dir():
        return achadas
    for pasta in sorted(base.iterdir()):
        arq = pasta / "SKILL.md"
        if pasta.name in DO_KIT or not arq.is_file():
            continue
        try:
            r = ler_receita(arq)
        except (OSError, UnicodeDecodeError):
            continue
        tipo = tipo_da_receita(r)
        if tipo:
            achadas.append((pasta.name, tipo, arq, r))
    return achadas


# ---------------------------------------------------------------- tabelas e fontes

def tabela(corpo):
    """Linhas de dados da primeira tabela do texto: lista de listas de células."""
    linhas = []
    for l in corpo.split("\n"):
        if l.strip().startswith("|"):
            cel = [c.strip() for c in l.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cel):
                continue
            linhas.append(cel)
    return linhas[1:] if linhas else []      # tira o cabeçalho


def procurar_fonte(arquivo, pastas):
    nome = Path(arquivo).name.lower()
    for p in pastas:
        p = Path(p)
        if p.is_file() and p.name.lower() == nome:
            return p
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and f.name.lower() == nome:
                    return f
    return None


def pastas_de_fonte(extras, pasta_receita):
    casa = Path.home()
    return [*map(Path, extras), pasta_receita, casa / "Library" / "Fonts", Path("/Library/Fonts"),
            casa / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts", Path("C:/Windows/Fonts")]


def numero(s):
    return int(s) if s else None


def estilo_pelos_numeros(linhas):
    """Sem bloco `estilo` na receita antiga, tira da tabela o que dá para ler com segurança."""
    por = {sem_acento(l[0]): l[1] for l in linhas if len(l) >= 2}
    achou = {}
    def val(*chaves):
        for k, v in por.items():
            if any(c in k for c in chaves):
                return v
        return ""
    m = re.search(r"(\d+)\s*px", val("tamanho"))
    if m:
        achou["tamanho"] = int(m.group(1))
    m = re.match(r"\s*(?:(\d+)\s*(?:a|-)\s*)?(\d+)\b", val("palavras por vez"))
    if m:
        achou["palavras_max"] = int(m.group(2))
    m = re.search(r"at[eé]\s*(\d+)\s*letras", val("palavras por vez"), re.I)
    if m:
        achou["letras_max"] = int(m.group(1))
    m = re.search(r"\by\s*=?\s*(\d{3,4})", val("posicao"))
    if m:
        achou["legenda_y"] = int(m.group(1))
    m = re.search(r"abaixo de (\d{3,4})", val("posicao"))
    if m:
        achou["zona_segura"] = [260, int(m.group(1))]
    m = re.search(r"(\d+)\s*px livres", val("posicao"))
    if m:
        achou["margem"] = int(m.group(1))
    m = re.search(r"(\d+)\s*%", val("sombra"))
    if m:
        achou["sombra"] = int(m.group(1)) / 100
    m = re.search(r"#[0-9A-Fa-f]{6}", val("cor"))
    if m:
        achou["cor"] = m.group(0).upper()
    if re.search(r"nunca tudo mai[uú]sculo|sem tudo mai[uú]sculo|como se escreve", val("letra"), re.I):
        pass          # letra normal é o padrão do kit; não escreve nada
    return achou


# ---------------------------------------------------------------- montar o estilo novo

def importar(r, arq_receita, extras_fonte, hoje):
    """Devolve (texto do estilo.md, fontes a copiar {nome: caminho}, trouxe [...], falta [...])."""
    nome = r["nome"] or Path(arq_receita).parent.name
    trouxe, falta, copiar, sem_arquivo = [], [], {}, set()
    pastas = pastas_de_fonte(extras_fonte, Path(arq_receita).parent)
    corpos = {}
    extras = []      # seções que não têm par: ficam como estão
    for titulo, corpo in r["secoes"]:
        base = sem_acento(re.sub(r"\s*\(.*?\)\s*$", "", titulo))      # «Fontes (os arquivos ficam...)» vale «fontes»
        chave = MAPA.get(base, "?")
        if chave == "?":
            chave = "composicao" if base.split(" ")[0] in ORDEM_COMPOSICAO else "?"
        if chave == "?":
            extras.append((titulo, corpo))
        elif chave is not None:
            corpos.setdefault(chave, []).append((titulo, corpo))

    def resolver_fonte(arquivo):
        """Nome do arquivo -> caminho 'marca/fontes/<arquivo>' se achou (e marca para copiar), senão None."""
        base = Path(str(arquivo).replace("\\", "/")).name
        if base in copiar:
            return f"marca/fontes/{base}"
        achada = procurar_fonte(base, [Path(str(arquivo)).parent] + pastas) if Path(str(arquivo)).is_absolute() \
            else procurar_fonte(base, pastas)
        if achada:
            copiar[base] = achada
            return f"marca/fontes/{base}"
        if base not in sem_arquivo:
            sem_arquivo.add(base)
            falta.append(f"arquivo da fonte {base} (não achei no computador: peça para a pessoa arrastar o arquivo)")
        return None

    # --- Fontes
    linhas_fonte = []
    if "fontes" in corpos:
        for c in tabela(corpos["fontes"][0][1]):
            if len(c) >= 3:
                arq = FONTE.search(c[2])
                novo = resolver_fonte(arq.group(0)) if arq else None
                linhas_fonte.append((c[0], c[1], f"`{novo}`" if novo else "— (sem arquivo: usa a do sistema)"))
    legenda_linhas = tabela(corpos["legenda"][0][1]) if "legenda" in corpos else []
    if not linhas_fonte:
        for c in legenda_linhas:
            if len(c) >= 2 and sem_acento(c[0]).startswith("fonte"):
                arq = FONTE.search(c[1])
                novo = resolver_fonte(arq.group(0)) if arq else None
                if not arq:
                    falta.append("arquivo da fonte da legenda (a receita cita só o nome, " + c[1].split(";")[0] +
                                 "; peça o arquivo .otf ou .ttf)")
                linhas_fonte.append(("Legenda", c[1], f"`{novo}`" if novo else "— (sem arquivo: usa a do sistema)"))
    if linhas_fonte and "fontes" not in corpos:      # a linha «Fonte» da tabela da legenda foi para Fontes
        legenda_linhas = [c for c in legenda_linhas if not (len(c) >= 2 and sem_acento(c[0]).startswith("fonte"))]

    saida = [f"# {r['h1'] or 'Estilo'}", "",
             f"> Importado em {hoje} da receita `{nome}` (formato de 17/10, em `~/.claude/skills/{nome}`). A receita antiga não foi "
             "alterada. Na pasta de edição, este texto\n> mora em `marca/estilo.md`, sem cabeçalho de skill: as 4 skills "
             "do kit o leem quando o vídeo está dentro da pasta.", ""]
    if r["intro"]:
        saida += [r["intro"], ""]
    if linhas_fonte:
        saida += ["## Fontes", "", "| Uso | Fonte | Arquivo |", "|---|---|---|"]
        saida += [f"| {a} | {b} | {c} |" for a, b, c in linhas_fonte] + [""]
        trouxe.append("fontes (" + str(len(linhas_fonte)) + " linha(s); " + str(len(copiar)) + " arquivo(s) copiado(s) "
                      "para marca/fontes/)")

    # --- Legenda + bloco estilo
    bloco_estilo = None
    for titulo, corpo in corpos.get("aplicar", []):
        for m in re.finditer(r"```json\n(.*?)\n```", corpo, re.S):
            try:
                dado = json.loads(m.group(1).replace("<pasta das fontes>", "FONTES"))
            except ValueError:
                try:
                    dado = json.loads("{" + m.group(1).strip().strip(",") + "}")
                except ValueError:
                    continue
            if isinstance(dado, dict) and "estilo" in dado and isinstance(dado["estilo"], dict):
                bloco_estilo = dict(dado["estilo"])
            elif isinstance(dado, dict) and "tamanho" in dado:
                bloco_estilo = dict(dado)
    derivado = False
    if bloco_estilo is None and legenda_linhas:
        bloco_estilo, derivado = estilo_pelos_numeros(legenda_linhas), True
    if bloco_estilo:
        for k in ("fonte", "fonte_destaque"):
            if k in bloco_estilo:
                novo = resolver_fonte(bloco_estilo[k])
                if novo:
                    bloco_estilo[k] = novo
                else:
                    del bloco_estilo[k]
        if linhas_fonte and "fonte" not in bloco_estilo:
            principal = FONTE.search(linhas_fonte[0][2])
            if principal:
                bloco_estilo = {"fonte": principal.group(0).strip("`"), **bloco_estilo}
    if legenda_linhas or bloco_estilo:
        saida += ["## Legenda", "", "Medidas no quadro de 1080×1920, y = 0 no topo; \"pé\" é a linha de base das letras.", ""]
        if legenda_linhas:
            saida += ["| Parâmetro | Valor |", "|---|---|"] + [f"| {c[0]} | {c[1]} |" for c in legenda_linhas if len(c) >= 2] + [""]
        elif "legenda" in corpos:
            saida += [corpos["legenda"][0][1], ""]
        if bloco_estilo:
            saida += ["Bloco `estilo` do `insercoes.json` (a `/inserir` grava a legenda no vídeo e gera a "
                      "`legenda-curta.srt` com o mesmo tempo):", "", "```json", '"estilo": ' +
                      re.sub(r"\[\s*(\d+),\s*(\d+)\s*\]", r"[\1, \2]",
                             json.dumps(bloco_estilo, ensure_ascii=False, indent=2)), "```", ""]
            trouxe.append("legenda: tabela de parâmetros e o bloco `estilo` do insercoes.json" +
                          (" (montado pelos números da tabela: confira)" if derivado else ""))
        else:
            trouxe.append("legenda: tabela de parâmetros")

    def copia(chave, titulo_novo, trouxe_txt):
        if chave in corpos:
            saida.extend([f"## {titulo_novo}", "", "\n\n".join(c for _, c in corpos[chave]), ""])
            trouxe.append(trouxe_txt)
            return True
        return False

    tem_corte = copia("corte", "Corte e zoom", "corte e zoom")
    tem_cor = copia("cor", "Cor", "cor (o texto da receita antiga)")
    if tem_cor and not re.search(r"\.cube|lut", corpos["cor"][0][1], re.I):
        falta.append("LUT da cor (opcional): um bruto e o mesmo vídeo exportado do editor dela copiam a cor exata; "
                     "sem isso vale o texto da receita")
    elif not tem_cor:
        falta.append("cor (opcional): sem LUT vale o look por números da /decupar; para copiar a cor do editor dela, "
                     "um bruto e o mesmo vídeo exportado")
    comp = [(t, c) for t, c in corpos.get("composicao", [])]
    if comp:
        saida += ["## Composição", ""]
        for t, c in comp:
            saida += [f"### {t}", "", c, ""]
        trouxe.append("composição: " + ", ".join(t for t, _ in comp))
    tem_som = copia("som", "Som", "som (o texto da receita antiga)")
    if not tem_som:
        falta.append("universo da trilha: as 3 faixas que definem o som dela (a /sonorizar usa como régua)")
    elif not re.search(r"trilha|m[uú]sica|faixa", corpos["som"][0][1], re.I):
        falta.append("universo da trilha: a receita antiga fala só de efeitos; faltam as 3 faixas que definem o som dela")

    # --- No editor: o que sobra de "Como aplicar" (o Claude e a /inserir agora são o kit)
    editor = []
    for _, corpo in corpos.get("aplicar", []):
        blocos, atual, dentro = [], [], False
        for linha in corpo.split("\n"):
            if linha.startswith("```"):
                dentro = not dentro
            if not linha.strip() and not dentro:
                if atual:
                    blocos.append("\n".join(atual))
                    atual = []
            else:
                atual.append(linha)
        if atual:
            blocos.append("\n".join(atual))
        for b in blocos:
            if b.startswith("**Na /inserir") or b.startswith("**O Claude**") or b.startswith("```json"):
                continue
            editor.append(b)
    if editor:
        saida += ["## No editor", "", "Só para quem termina o vídeo no CapCut ou no Premiere, com a `legenda-curta.srt` "
                  "e o vídeo sem legenda (passos em `editores.md` da `/minha-edicao`):", "", *[x + "\n" for x in editor]]
        trouxe.append("passos do editor (CapCut/Premiere)")

    for t, c in extras:
        saida += [f"## {t}", "", c, ""]
        trouxe.append(f"seção «{t}» (sem par no formato novo, copiada como está)")

    falta.append("o que a edição nunca faz (ex.: cobrir o rosto, legenda em maiúsculas): a receita antiga não tinha "
                 "esta parte")

    if "conferir" in corpos:
        saida += ["## Conferir", "", corpos["conferir"][0][1], ""]
        trouxe.append("lista Conferir")
    saida += [MELHORAR, "", "## Histórico", ""]
    historico = corpos["historico"][0][1] if "historico" in corpos else ""
    saida += [historico, ] if historico else []
    saida += [f"- {hoje}: importada para `marca/estilo.md` com a /minha-edicao, a partir da receita `{nome}` da versão "
              "de 17/10. Valores da receita antiga, sem medida nova."]
    return "\n".join(saida).rstrip() + "\n", copiar, trouxe, falta


# ---------------------------------------------------------------- linha de comando

def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Importa uma receita de estilo da versão de 17/10 para marca/estilo.md")
    ap.add_argument("receita", nargs="?", help="nome da pasta da receita em ~/.claude/skills")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--pasta", help="pasta de edição (onde fica marca/)")
    ap.add_argument("--skills-dir", default=str(Path.home() / ".claude" / "skills"))
    ap.add_argument("--fontes-de", action="append", default=[])
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()

    achadas = candidatas(a.skills_dir)
    if a.listar:
        if not achadas:
            print("Nenhuma receita de estilo ou de formato no formato de 17/10 em", a.skills_dir)
            return 0
        for nome, tipo, arq, r in achadas:
            print(f"{nome}\t{tipo}\t{arq}\t{r['description'][:100]}")
        print("\n'estilo' pode ser importada para marca/estilo.md; 'formato' continua valendo como está.")
        return 0
    if not a.receita or not a.pasta:
        ap.error("diga o nome da receita e --pasta (ou use --listar)")
    por_nome = {n: (t, arq, r) for n, t, arq, r in achadas}
    if a.receita not in por_nome:
        print(f"Não achei a receita de estilo «{a.receita}» em {a.skills_dir}. Receitas lá: "
              + (", ".join(f"{n} ({t})" for n, (t, _, _) in por_nome.items()) or "nenhuma"))
        return 1
    tipo, arq, r = por_nome[a.receita]
    if tipo != "estilo":
        print(f"«{a.receita}» é uma receita de formato: ela continua valendo como skill e não vai para o marca/estilo.md.")
        return 1
    marca = Path(a.pasta).expanduser().resolve() / "marca"
    destino = marca / "estilo.md"
    if destino.exists() and not a.simular:
        print(f"{destino} já existe: não sobrescrevo. Use o caminho «Ajustar» da /minha-edicao.")
        return 1
    hoje = datetime.date.today().isoformat()
    texto, copiar, trouxe, falta = importar(r, arq, a.fontes_de, hoje)
    if a.simular:
        print(texto)
    else:
        (marca / "fontes").mkdir(parents=True, exist_ok=True)
        for nome_arq, origem in copiar.items():
            shutil.copy2(origem, marca / "fontes" / nome_arq)
        destino.write_text(texto, encoding="utf-8")
        print(f"Gravei {destino}")
    print("\nTrouxe da receita antiga:")
    for t in trouxe:
        print("  -", t)
    print("\nFalta perguntar:")
    for f in falta:
        print("  -", f)
    print("\nA receita antiga continua em", arq.parent, "(não apaguei nada).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
