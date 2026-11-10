"""Biblioteca comum dos scripts da novela (só biblioteca padrão; Python 3.9 ou mais novo).

Não é um comando: é importada por encaixar_aula.py, montar_projeto.py, segunda_voz.py e entregar.py.
Reúne o que os quatro repetem: achar a pasta do episódio, ler e gravar JSON, resolver uma referência do roteiro
(«bloco + palavra») em segundos, a régua VOZ.w do assets/voz.js, e a leitura, a medida e a gravação de WAV.
Tudo se acha pela posição deste arquivo (a pasta scripts/ da skill); nenhuma outra skill é necessária.
"""
from __future__ import annotations

import array
import json
import math
import re
import shutil
import subprocess
import sys
import unicodedata
import wave
from pathlib import Path

AQUI = Path(__file__).resolve().parent               # <skill>/scripts
SKILL = AQUI.parent                                    # a pasta desta skill
MODELO_MOTION = SKILL / "modelos" / "motion"
COMPONENTES_PADRAO = SKILL / "modelos" / "componentes"
REGUA_SKILL = SKILL / "referencias" / "regua-visual.md"
MOVIMENTO = SKILL / "referencias" / "movimento.md"
CONTRATO_HF = SKILL / "referencias" / "gsap-hyperframes.md"
SR = 48000
SOBREPOSICAO = 0.30          # janela do ato = início do ato seguinte + 0,30 s
HYPERFRAMES = "hyperframes@0.9.6"
GSAP_URL = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"


def garantir_gsap(proj):
    """Baixa a GSAP para assets/gsap.min.js se o projeto ainda não a tem. A biblioteca não vem copiada na skill:
    ela é da GreenSock (gsap.com/standard-license) e chega do pacote oficial, na versão travada em GSAP_URL."""
    dest = Path(proj) / "assets" / "gsap.min.js"
    if dest.is_file() and dest.stat().st_size > 10000:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        import urllib.request
        with urllib.request.urlopen(GSAP_URL, timeout=30) as r:
            dados = r.read()
    except Exception:  # sem certificado no Python do sistema: o Node 22, que a skill já exige, baixa
        dados = b""
        node = shutil.which("node")
        if node:
            js = ("fetch(process.argv[1]).then(r=>{if(!r.ok)throw 0;return r.arrayBuffer()})"
                  ".then(b=>require('fs').writeFileSync(process.argv[2],Buffer.from(b))).catch(()=>process.exit(1))")
            if subprocess.run([node, "-e", js, GSAP_URL, str(dest)]).returncode == 0 and dest.is_file():
                dados = dest.read_bytes()
    if len(dados) < 10000 or b"GSAP" not in dados[:400]:
        if dest.is_file():
            dest.unlink()
        sair(f"não consegui baixar a GSAP. Com internet, rode de novo; ou salve {GSAP_URL} em {dest}.")
    dest.write_bytes(dados)
    return True


def sair(msg, codigo=1):
    print("erro: " + msg, file=sys.stderr)
    sys.exit(codigo)


def ler(p):
    p = Path(p)
    if not p.is_file():
        sair(f"não achei {p}. Confira o caminho e se o passo anterior já rodou.")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sair(f"{p} não é um JSON válido ({e}). Abra o arquivo e corrija a vírgula ou a aspa indicada.")


def gravar(p, dados, indent=1):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(dados, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def pasta_ep(arg):
    """Aceita o caminho do episódio (<pasta da série>/ep01, ou só ep01 de dentro da série) e confere o roteiro.json."""
    p = Path(arg).expanduser().resolve()
    if not p.is_dir():
        sair(f"«{arg}» não é uma pasta. Passe a pasta do episódio, ex.: <pasta da série>/ep01 "
             "(ou só ep01, de dentro da pasta da série).")
    if not (p / "roteiro.json").is_file():
        sair(f"{p} não tem roteiro.json. O argumento é a pasta do episódio, não a da série.")
    return p


def norm(w):
    t = unicodedata.normalize("NFD", str(w).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", t)


NUMEROS = {n: str(i) for i, n in enumerate(
    "zero um dois tres quatro cinco seis sete oito nove dez onze doze treze catorze quinze dezesseis dezessete dezoito "
    "dezenove vinte".split())}
NUMEROS.update({"trinta": "30", "quarenta": "40", "cinquenta": "50", "sessenta": "60", "setenta": "70",
                "oitenta": "80", "noventa": "90", "cem": "100", "duas": "2"})


# ---------------------------------------------------------------- blocos e palavras
def blocos_de(ep):
    return ler(Path(ep) / "brutos" / "narracao" / "narracao-blocos.json")


def palavras_por_bloco(palavras, blocos):
    """Índice do bloco de cada palavra: o último bloco que começa até 0,05 s depois do início da palavra."""
    out = []
    for p in palavras:
        k = 0
        for i, b in enumerate(blocos):
            if b["ini"] - 0.05 <= p["ini"]:
                k = i
        out.append(k)
    return out


class Mundo:
    """O que uma referência do roteiro precisa para virar segundos: palavras, blocos, aula e duração."""

    def __init__(self, palavras, blocos, aula=None, duracao=None):
        self.palavras, self.blocos, self.aula, self.duracao = palavras, blocos, aula, duracao
        self.por_bloco = palavras_por_bloco(palavras, blocos)

    def bloco(self, cena):
        for i, b in enumerate(self.blocos):
            if b["cena"] == cena:
                return i, b
        nomes = ", ".join(b["cena"] for b in self.blocos)
        sair(f"o bloco «{cena}» não existe na narração. Blocos: {nomes}.")

    def palavra(self, cena, frase, n=1):
        i, _ = self.bloco(cena)
        idx = [k for k, p in enumerate(self.palavras) if self.por_bloco[k] == i and norm(p["w"])]
        toks = [norm(t) for t in str(frase).split() if norm(t)]
        if not toks:
            sair(f"palavra vazia na referência do bloco «{cena}».")
        for tentativa in (toks, [NUMEROS.get(t, t) for t in toks]):
            achados = []
            for j in range(len(idx) - len(tentativa) + 1):
                if all(norm(self.palavras[idx[j + m]]["w"]) == tentativa[m] for m in range(len(tentativa))):
                    achados.append(idx[j])
            if len(achados) >= n:
                return self.palavras[achados[n - 1]], self.palavras[achados[n - 1] + len(tentativa) - 1]
        ditas = " ".join(self.palavras[k]["w"] for k in idx)
        sair(f"não achei «{frase}» (ocorrência {n}) no bloco «{cena}». O bloco tem: {ditas}")

    def tempo(self, ref):
        """Referência → segundos. Formas:
        {"bloco": c}                      início do bloco (com "ponto": "fim", o fim dele)
        {"bloco": c, "palavra": "x y", "n": 1, "ponto": "ini"|"fim", "desloc": 0}   início (ou fim) da palavra/frase
        {"aula": "silencio_ini"|"aula_ini"|"aula_fim"|"silencio_fim"}               janela da aula
        {"video": "fim"}                  duração da narração
        """
        if not isinstance(ref, dict):
            sair(f"referência inválida: {ref!r}. Use {{\"bloco\": \"...\", \"palavra\": \"...\"}}.")
        if "aula" in ref:
            if not self.aula or ref["aula"] not in self.aula:
                sair(f"a referência {ref} pede a janela da aula, mas ela não existe (rode o encaixar_aula.py antes).")
            return float(self.aula[ref["aula"]]) + float(ref.get("desloc", 0))
        if "video" in ref:
            return float(self.duracao) + float(ref.get("desloc", 0))
        if "bloco" not in ref:
            sair(f"referência sem «bloco», «aula» nem «video»: {ref}")
        ponto = ref.get("ponto", "ini")
        if "palavra" in ref:
            p0, p1 = self.palavra(ref["bloco"], ref["palavra"], int(ref.get("n", 1)))
            t = p0["ini"] if ponto == "ini" else p1["fim"]
        else:
            _, b = self.bloco(ref["bloco"])
            t = b["ini"] if ponto == "ini" else b["fim"]
        return round(float(t) + float(ref.get("desloc", 0)), 3)


# ---------------------------------------------------------------- VOZ.w
def ancoras_do_voz_js(voz_js):
    txt = Path(voz_js).read_text(encoding="utf-8")
    m = re.search(r"const A = \[([\s\S]*?)\];", txt)
    if not m:
        sair(f"não achei `const A = [...]` em {voz_js}. Use o assets/voz.js do esqueleto (modelos/motion).")
    return [(float(a), float(b)) for a, b in re.findall(r"\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]", m.group(1))]


def voz_w(A, t):
    """Mesma conta do assets/voz.js."""
    P = ([(0.0, 0.0)] + A) if A and A[0][0] > 0 else list(A)
    if len(P) < 2 or t <= P[0][0]:
        return t
    n = len(P) - 1
    if t >= P[n][0]:
        return t - P[n][0] + P[n][1]
    i, j = 0, n
    while j - i > 1:
        m = (i + j) >> 1
        if P[m][0] <= t:
            i = m
        else:
            j = m
    return P[i][1] + (t - P[i][0]) * (P[j][1] - P[i][1]) / (P[j][0] - P[i][0])


# ---------------------------------------------------------------- áudio
def rodar(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    return r


def exigir(cmd, onde=""):
    if not shutil.which(cmd):
        sair(f"«{cmd}» não está instalado ou não está no PATH{onde}.")


def duracao_de(arq):
    exigir("ffprobe")
    r = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", arq])
    try:
        return float(r.stdout.strip())
    except ValueError:
        sair(f"o ffprobe não leu {arq}: {r.stderr.strip()[:200]}")


def ler_wav(arq, tmp=None):
    """WAV → (array('h') mono 48 kHz). Converte pelo ffmpeg se o arquivo não for PCM 16 bits mono 48 kHz."""
    arq = Path(arq)
    try:
        with wave.open(str(arq), "rb") as w:
            ok = w.getsampwidth() == 2 and w.getnchannels() == 1 and w.getframerate() == SR
    except (wave.Error, EOFError):
        ok = False
    if not ok:
        exigir("ffmpeg")
        tmp = Path(tmp or arq.with_suffix(".conv.wav"))
        r = rodar(["ffmpeg", "-v", "error", "-y", "-i", arq, "-ac", "1", "-ar", SR, "-c:a", "pcm_s16le", tmp])
        if r.returncode:
            sair(f"o ffmpeg não converteu {arq}: {r.stderr.strip()[:200]}")
        arq = tmp
    with wave.open(str(arq), "rb") as w:
        a = array.array("h")
        a.frombytes(w.readframes(w.getnframes()))
    if sys.byteorder == "big":
        a.byteswap()
    return a


def gravar_wav(arq, a):
    b = array.array("h", a)
    if sys.byteorder == "big":
        b.byteswap()
    with wave.open(str(arq), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b.tobytes())


def pico_dbfs(a):
    m = max((abs(x) for x in a), default=0)
    return -120.0 if m == 0 else 20 * math.log10(m / 32768.0)


def lufs(a, tmp):
    """Loudness integrado (LUFS) do array, pelo ebur128 do ffmpeg."""
    exigir("ffmpeg")
    gravar_wav(tmp, a)
    r = rodar(["ffmpeg", "-nostats", "-hide_banner", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"])
    achados = re.findall(r"^\s*I:\s*(-?[\d.]+) LUFS", r.stderr, re.M)
    if not achados:
        sair("o ffmpeg não devolveu o loudness (ebur128): " + r.stderr[-200:])
    return float(achados[-1])


def ganho(a, db):
    k = 10 ** (db / 20.0)
    return array.array("h", (max(-32768, min(32767, int(round(x * k)))) for x in a))


def uv_run(script, args):
    """Roda um script desta skill (que tem dependências próprias) pelo uv; sem uv, com o python3."""
    exe = ["uv", "run", "--quiet", str(script)] if shutil.which("uv") else [sys.executable, str(script)]
    r = rodar(exe + [str(a) for a in args])
    if r.returncode:
        sair(f"{Path(script).name} falhou:\n{(r.stdout + r.stderr).strip()[-700:]}")
    return r.stdout


def copiar_arvore(origem, destino, ignorar=()):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    shutil.copytree(origem, destino, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(*ignorar) if ignorar else None)


def fmt(x, c=3):
    return f"{x:.{c}f}".rstrip("0").rstrip(".")


def tabela(linhas, titulo=""):
    """Imprime «esperado × obtido × diferença» alinhado."""
    if titulo:
        print(titulo)
    larg = [max(len(str(l[i])) for l in linhas) for i in range(len(linhas[0]))]
    for l in linhas:
        print("  " + "  ".join(str(c).ljust(larg[i]) for i, c in enumerate(l)))
