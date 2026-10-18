# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Teste do contrato do kit de edição (docs/edicao-contrato.md): as 4 skills resolvem tempo e marca igual.

Uso:  uv run tests/test_contrato.py        (ou python3 tests/test_contrato.py)

Confere que o scripts/contrato.py é o mesmo arquivo em /decupar, /inserir, /sonorizar e /criticar e, num processo
separado por skill (cada uma importa o próprio comum.py), que as âncoras dão o mesmo resultado num
palavras-corte.json de exemplo, que palavra cortada é erro, que a borda perto da emenda encosta nela e que
achar_marca e os caminhos marca/ são iguais. Sai com código 1 na primeira diferença.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SKILLS = ["decupar", "inserir", "sonorizar", "criticar"]

# palavras-corte.json de exemplo: F2 saiu inteira; o "até" de F3 saiu; F3 ficou partida em dois trechos;
# F81 tem número falado ("10,"). fps 30; emendas em 2,0 s e 4,0 s.
EXEMPLO = {
    "versao": 2, "video": "final.mp4", "duracao": 7.5, "fps": 30, "velocidade": 1.0, "medido": "pedacos",
    "trechos": [{"n": 1, "a": 0.0, "b": 2.0}, {"n": 2, "a": 2.0, "b": 4.0}, {"n": 3, "a": 4.0, "b": 7.5}],
    "emendas": [2.0, 4.0],
    "frases": [
        {"id": "F1", "a": 0.1, "b": 1.9, "texto": "Vocês acham que ter lojinha", "trecho": 1},
        {"id": "F3", "a": 2.1, "b": 2.9, "texto": "pouco tempo atrás", "trecho": 2},
        {"id": "F3", "a": 3.0, "b": 3.95, "texto": "você ter você", "trecho": 2},
        {"id": "F81", "a": 4.1, "b": 7.2, "texto": "Agora, quando você vê 10, 20 pessoas", "trecho": 3},
    ],
    "palavras": [
        {"w": "Vocês", "a": 0.1, "b": 0.4, "frase": "F1", "n": 1, "i": 0, "trecho": 1},
        {"w": "acham", "a": 0.4, "b": 0.8, "frase": "F1", "n": 2, "i": 1, "trecho": 1},
        {"w": "que", "a": 0.8, "b": 1.0, "frase": "F1", "n": 3, "i": 2, "trecho": 1},
        {"w": "ter", "a": 1.0, "b": 1.3, "frase": "F1", "n": 4, "i": 3, "trecho": 1},
        {"w": "lojinha", "a": 1.3, "b": 1.9, "frase": "F1", "n": 5, "i": 4, "trecho": 1},
        {"w": "pouco", "a": 2.1, "b": 2.4, "frase": "F3", "n": 2, "i": 12, "trecho": 2},
        {"w": "tempo", "a": 2.4, "b": 2.7, "frase": "F3", "n": 3, "i": 13, "trecho": 2},
        {"w": "atrás,", "a": 2.7, "b": 2.9, "frase": "F3", "n": 4, "i": 14, "trecho": 2},
        {"w": "você", "a": 3.0, "b": 3.3, "frase": "F3", "n": 5, "i": 15, "trecho": 2},
        {"w": "ter", "a": 3.3, "b": 3.6, "frase": "F3", "n": 6, "i": 16, "trecho": 2},
        {"w": "Você", "a": 3.6, "b": 3.95, "frase": "F3", "n": 7, "i": 17, "trecho": 2},
        {"w": "Agora,", "a": 4.1, "b": 4.5, "frase": "F81", "n": 1, "i": 40, "trecho": 3},
        {"w": "quando", "a": 4.5, "b": 4.8, "frase": "F81", "n": 2, "i": 41, "trecho": 3},
        {"w": "você", "a": 4.8, "b": 5.0, "frase": "F81", "n": 3, "i": 42, "trecho": 3},
        {"w": "vê", "a": 5.0, "b": 5.2, "frase": "F81", "n": 4, "i": 43, "trecho": 3},
        {"w": "10,", "a": 5.2, "b": 5.6, "frase": "F81", "n": 5, "i": 44, "trecho": 3},
        {"w": "20", "a": 5.7, "b": 6.0, "frase": "F81", "n": 6, "i": 45, "trecho": 3},
        {"w": "pessoas", "a": 6.0, "b": 7.2, "frase": "F81", "n": 7, "i": 46, "trecho": 3},
    ],
}
TRANSCRICAO = """Transcrição de "bruto.MOV" · 1 min · /decupar
F1   [00:03,59 – 00:06,60]  Vocês acham que ter lojinha
F2   [00:08,00 – 00:09,00]  Porque assim,
F3   [00:21,40 – 00:27,91]  até pouco tempo atrás, você ter você
F81  [06:40,00 – 06:45,00]  Agora, quando você vê 10, 20 pessoas
"""

# (âncora, lado ate?, resultado esperado: segundos ou "ERRO"). 3,95 s fica a 1,5 quadro da emenda de 4,0 s: encosta.
CASOS = [
    ("F3", False, 2.1), ("F3", True, 4.0), ("F3:fim", False, 4.0), ("F3:inicio", True, 2.1),
    ("F3:2", False, 2.1), ("F3:2", True, 2.4), ("F3:voce#2", False, 3.6), ("F3:Você#2", True, 4.0),
    ("F81:10#1", False, 5.2), ("F81:10#1", True, 5.6), ("F81:5", False, 5.2), ("F81:6", False, 5.7),
    ("F1:fim+0.25", False, 2.15), ("F1:fim+0,25", True, 2.15), ("F1+0.1", False, 0.2), ("F3:tempo-0.1", False, 2.3),
    ("f1:acham", False, 0.4), (" F1:lojinha ", True, 1.9),
    ("00:01,50", False, 1.5), ("1:02:03.5", False, 3723.5), (2.5, False, 2.5), ("4", False, 4.0),
    ("F3:emenda", True, 2.0), ("F81:emenda", False, 4.0), ("F1:emenda", False, 0.0), ("F3:emenda+0.5", False, 2.5),
    ("F3:até", False, "ERRO"), ("F3:1", False, "ERRO"), ("F2", False, "ERRO"), ("F9", False, "ERRO"),
    ("F81:10", False, "ERRO"), ("F3:loja", False, "ERRO"), ("depois", False, "ERRO"), (True, False, "ERRO"),
]
ENCOSTAR = [(1.95, 2.0), (2.05, 2.0), (2.0, 2.0), (1.85, 1.85), (3.95, 4.0)]   # 3 quadros a 30 fps = 0,1 s

SONDA = r'''
import json, os, sys
from pathlib import Path
pasta, exemplo, tree = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, pasta)
import comum                                  # o comum.py da skill, que importa o contrato.py dela
import contrato
casos = json.loads(sys.stdin.read())
out = {"contrato": os.path.realpath(contrato.__file__), "ancoras": [], "encostar": []}
a = contrato.Ancoras.de_corte(exemplo)
for v, fim in casos["ancoras"]:
    try:
        out["ancoras"].append(round(a.tempo(v, fim), 4))
    except contrato.ErroContrato as e:
        out["ancoras"].append("ERRO " + str(e))
out["encostar"] = [round(a.encostar(t)[0], 4) for t in casos["encostar"]]
# a mesma conta pela porta de cada skill (o embrulho do comum.py, que dá a mensagem de erro do jeito dela)
skill = Path(pasta).parent.name
porta = []
for v, fim in casos["ancoras"]:
    try:
        if skill == "inserir":
            import io, contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                t = comum.Ancoras(Path(exemplo).parent).tempo(v, "teste", fim)
        elif skill == "sonorizar":
            t = comum.Ancoras(exemplo).tempo(v, "fim" if fim else "inicio")
        else:
            t = comum.Ancoras.de_corte(exemplo).tempo(v, fim)
        porta.append(round(t, 4))
    except (SystemExit, ValueError):
        porta.append("ERRO")
out["porta"] = porta
if skill == "decupar":                         # no bruto (cortes.json): o cortar.py usa o mesmo contrato
    import cortar
    frases = [{"id": "F1", "ini": 3.59, "fim": 6.6, "i0": 0, "i1": 3, "texto": "Vocês acham isso"},
              {"id": "F3", "ini": 21.4, "fim": 27.91, "i0": 4, "i1": 7, "texto": "até até pouco"}]
    pal = [{"w": "Vocês", "ini": 3.59, "fim": 4.0}, {"w": "", "ini": 4.0, "fim": 4.2},
           {"w": "acham", "ini": 4.2, "fim": 4.6}, {"w": "isso", "ini": 4.6, "fim": 6.6},
           {"w": "até", "ini": 21.4, "fim": 21.6}, {"w": "até", "ini": 21.7, "fim": 23.9},
           {"w": "pouco", "ini": 24.0, "fim": 24.3}, {"w": "", "ini": 24.3, "fim": 27.91}]
    b = contrato.Ancoras.do_bruto(frases, pal, comum.CAP_PALAVRA)
    out["bruto"] = [list(cortar.ler_tempo(v, b, lado, "t")) for v, lado in
                    [("F1", "de"), ("F1", "ate"), ("F1:2", "de"), ("F1:isso", "ate"), ("F3:ate#2", "ate"),
                     ("F3:fim", "ate"), ("F3:3+0.1", "de"), ("01:00,00", "de")]]
m = comum.achar_marca(Path(tree) / "edicao" / "videos" / "v" / "som")
out["marca"] = str(m)
out["marca_atalho"] = str(comum.achar_marca(Path(tree) / "atalho"))
out["caminho"] = str(contrato.caminho("marca/cor/look.cube", Path(tree) / "edicao" / "videos" / "v" / "som", m))
out["relativo"] = str(contrato.caminho("../insercoes/x.mp4", Path(tree) / "edicao" / "videos" / "v" / "som", m))
try:
    contrato.caminho("marca/cor/look.cube", tree, None)
    out["sem_marca"] = "sem erro"
except contrato.ErroContrato:
    out["sem_marca"] = "ERRO"
print(json.dumps(out, ensure_ascii=False))
'''


def falha(msg):
    print("FALHOU:", msg)
    sys.exit(1)


def main():
    arqs = {s: RAIZ / "skills" / s / "scripts" / "contrato.py" for s in SKILLS}
    hashes = {s: hashlib.sha1(p.read_bytes()).hexdigest()[:12] for s, p in arqs.items() if p.is_file()}
    if len(hashes) != len(SKILLS):
        falha(f"falta o contrato.py em {sorted(set(SKILLS) - set(hashes))}")
    if len(set(hashes.values())) != 1:
        falha("os contrato.py não são iguais: " + ", ".join(f"{s} {h}" for s, h in hashes.items())
              + f". Copie o de skills/decupar/scripts/ para as outras.")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "decupagem").mkdir()
        exemplo = tmp / "decupagem" / "palavras-corte.json"
        exemplo.write_text(json.dumps(EXEMPLO, ensure_ascii=False), encoding="utf-8")
        (tmp / "decupagem" / "transcricao.txt").write_text(TRANSCRICAO, encoding="utf-8")
        (tmp / "edicao" / "marca").mkdir(parents=True)
        (tmp / "edicao" / "marca" / "estilo.md").write_text("# estilo\n", encoding="utf-8")
        (tmp / "edicao" / "videos" / "v" / "som").mkdir(parents=True)
        (tmp / "atalho").symlink_to(tmp / "edicao" / "videos" / "v")
        entrada = json.dumps({"ancoras": [[v, fim] for v, fim, _ in CASOS], "encostar": [t for t, _ in ENCOSTAR]})
        res = {}
        for s in SKILLS:
            r = subprocess.run([sys.executable, "-I", "-c", SONDA, str(arqs[s].parent), str(exemplo), str(tmp)],
                               input=entrada, capture_output=True, text=True, encoding="utf-8")
            if r.returncode:
                falha(f"/{s}: o comum.py não importou:\n{r.stderr[-1500:]}")
            res[s] = json.loads(r.stdout)
            if Path(res[s]["contrato"]) != arqs[s].resolve():
                falha(f"/{s}: o comum.py carregou outro contrato.py ({res[s]['contrato']})")
        base = res[SKILLS[0]]
        for s in SKILLS[1:]:
            for k in ("ancoras", "porta", "encostar", "marca", "marca_atalho", "caminho", "relativo", "sem_marca"):
                if res[s][k] != base[k]:
                    falha(f"/{s} difere de /{SKILLS[0]} em {k}:\n  {res[s][k]}\n  {base[k]}")
        for (v, fim, esperado), got in zip(CASOS, base["ancoras"]):
            ok = str(got).startswith("ERRO") if esperado == "ERRO" else (got == round(esperado, 4))
            if not ok:
                falha(f"{v!r} ({'ate' if fim else 'de'}): esperava {esperado}, deu {got}")
        for (v, fim, esperado), got in zip(CASOS, base["porta"]):
            if got != ("ERRO" if esperado == "ERRO" else round(esperado, 4)):
                falha(f"porta das skills, {v!r}: esperava {esperado}, deu {got}")
        # bruto: (segundos, índice da palavra-limite); o "ate" da palavra é o fim limitado a 1 s (CAP_PALAVRA)
        bruto = [[3.59, None], [6.6, None], [4.2, 2], [5.6, 3], [22.7, 5], [27.91, 6], [24.1, None], [60.0, None]]
        if res["decupar"]["bruto"] != bruto:
            falha(f"cortar.py no bruto: {res['decupar']['bruto']} (esperava {bruto})")
        if "saiu no corte" not in base["ancoras"][CASOS.index(("F3:até", False, "ERRO"))]:
            falha("palavra cortada precisa dizer que saiu no corte: " + base["ancoras"][CASOS.index(("F3:até", False, "ERRO"))])
        for (t, esperado), got in zip(ENCOSTAR, base["encostar"]):
            if got != esperado:
                falha(f"encostar({t}): esperava {esperado}, deu {got}")
        if base["marca"] != str(tmp / "edicao" / "marca") or base["marca_atalho"] != "None":
            falha(f"achar_marca: {base['marca']} · pelo atalho: {base['marca_atalho']}")
        if base["caminho"] != str(tmp / "edicao" / "marca" / "cor" / "look.cube") or base["sem_marca"] != "ERRO":
            falha(f"caminho marca/: {base['caminho']} · sem marca: {base['sem_marca']}")
        if base["relativo"] != str(tmp / "edicao" / "videos" / "v" / "insercoes" / "x.mp4"):
            falha(f"caminho relativo: {base['relativo']}")
    print(f"ok: contrato.py igual nas 4 skills ({hashes['decupar']}); {len(CASOS)} tempos, {len(ENCOSTAR)} bordas, "
          "achar_marca e caminhos dão o mesmo resultado em /" + ", /".join(SKILLS))


if __name__ == "__main__":
    main()
