"""Funções comuns da /inserir. Roda igual no Mac e no Windows."""
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path


def utf8():
    """Saída em UTF-8 até no console do Windows (senão acento e "→" derrubam o script)."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def sair(msg, codigo=1):
    print(msg)
    sys.exit(codigo)


def rodar(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def checar_ffmpeg():
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sair("Falta o ffmpeg neste computador. Mac: brew install ffmpeg · Windows: winget install Gyan.FFmpeg "
             "(no Windows, feche e abra o Claude depois de instalar).")


def ler_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sair(f"{Path(p).name} tem um erro de escrita na linha {e.lineno}, coluna {e.colno}: {e.msg}.")


def fmt_tempo(s):
    """83.456 -> "01:23,46" (minuto:segundo,centésimos)."""
    cs = int(round(max(0.0, float(s)) * 100))
    return f"{cs // 6000:02d}:{cs // 100 % 60:02d},{cs % 100:02d}"


def fmt_num(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


def tempo(v, onde=""):
    """Aceita segundos (12.5), "mm:ss,cc" ou "mm:ss.cc"."""
    if isinstance(v, (int, float)):
        return float(v)
    m = re.fullmatch(r"\s*(?:(\d+):)?(\d+)(?:[.,](\d+))?\s*", str(v))
    if not m:
        sair(f"{onde}: não entendi o tempo {v!r}. Use \"01:23,45\" ou segundos (83.45).")
    mi, se, fr = m.groups()
    return int(mi or 0) * 60 + int(se) + (float("0." + fr) if fr else 0.0)


def achar_marca(pasta):
    """Sobe a partir da pasta do vídeo até achar marca/estilo.md (ou chegar na raiz do disco).
    Devolve a pasta marca/ ou None. Contrato do kit de edição, seção 1."""
    p = Path(pasta).expanduser().absolute()
    for d in (p, *p.parents):
        if (d / "marca" / "estilo.md").is_file():
            return d / "marca"
    return None


def caminho(s, base, marca, onde=""):
    """Caminho de um JSON: "marca/..." vale contra a pasta de edição (a que tem marca/); o resto, contra a
    pasta do próprio JSON. Não segue atalhos (symlinks): a origem em brutos/ é conferida pelo caminho escrito."""
    s = str(s)
    if s.replace("\\", "/").startswith("marca/"):
        if not marca:
            sair(f"{onde}: o caminho {s} começa com marca/, mas não achei a pasta marca (com estilo.md) "
                 "na pasta do vídeo nem acima dela.")
        return Path(os.path.normpath(marca.parent / s))
    p = Path(s).expanduser()
    return Path(os.path.normpath(p if p.is_absolute() else Path(base) / p))


# ---------------------------------------------------------------- âncoras de tempo (contrato, seção 2)

ANCORA = re.compile(r"^\s*(F\d+)(?::(.+?))?(?:([+-])(\d+(?:[.,]\d+)?))?\s*$")


def chave(w):
    """Palavra para comparar: sem acento, sem caixa e sem pontuação ("Aluga-se," -> "alugase")."""
    w = unicodedata.normalize("NFKD", str(w)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", w)


class Ancoras:
    """Resolve "F15", "F15:fim", "F15:repente#2", "F15:3", "F1:fim+0.25" pelo decupagem/palavras-corte.json.
    Sem esse arquivo, só aceita segundos e relógio."""

    def __init__(self, pasta_decupagem, correcoes=None):
        self.ok = False
        self.frases, self.palavras, self.original = {}, {}, {}
        p = Path(pasta_decupagem) / "palavras-corte.json"
        if p.exists():
            d = ler_json(p)
            self.frases = {f["id"]: f for f in d.get("frases", [])}
            for w in d.get("palavras", []):
                self.palavras.setdefault(w["frase"], []).append(w)
            self.duracao = d.get("duracao")
            self.ok = True
        corr = {chave(k): v for k, v in (correcoes or {}).items()}
        self.corr = corr
        t = Path(pasta_decupagem) / "transcricao.txt"
        if t.exists():   # o texto da frase no bruto: diz se a palavra existia e o corte tirou
            for linha in t.read_text(encoding="utf-8").splitlines():
                m = re.match(r"\s*(F\d+)\s+\[[^\]]*\]\s+(.*)$", linha)
                if m:
                    self.original[m.group(1)] = m.group(2)

    def _bate(self, w, alvo):
        k = chave(w)
        return k == alvo or chave(self.corr.get(k, "")) == alvo

    def tempo(self, v, onde="", fim=False):
        if v is None:
            sair(f"{onde}: falta o tempo.")
        if isinstance(v, (int, float)) or not re.match(r"\s*F\d", str(v)):
            return tempo(v, onde)
        m = ANCORA.match(str(v))
        if not m:
            sair(f"{onde}: não entendi a âncora {v!r}. Exemplos: \"F15\", \"F15:fim\", \"F15:repente\", \"F15:3\", "
                 "\"F1:fim+0.25\".")
        fid, parte, sinal, desl = m.groups()
        if not self.ok:
            sair(f"{onde}: a âncora {v!r} precisa do decupagem/palavras-corte.json, que a /decupar grava. "
                 "Rode a /decupar de novo ou use segundos.")
        desl = (-1 if sinal == "-" else 1) * float(desl.replace(",", ".")) if desl else 0.0
        if fid not in self.frases:
            if fid in self.original:
                sair(f"{onde}: a frase {fid} («{self.original[fid][:60]}») saiu no corte. Escolha outra âncora.")
            sair(f"{onde}: a frase {fid} não existe na transcrição.")
        f, ws = self.frases[fid], self.palavras.get(fid, [])
        if not parte:
            return (f["b"] if fim else f["a"]) + desl
        parte = parte.strip()
        if parte.lower() in ("inicio", "início"):
            return f["a"] + desl
        if parte.lower() == "fim":
            return f["b"] + desl
        if parte.isdigit():
            n = int(parte)
            w = next((w for w in ws if w.get("n") == n), None)
            if not w:
                orig = (self.original.get(fid) or "").split()
                nome = f" («{orig[n - 1]}»)" if 0 < n <= len(orig) else ""
                sair(f"{onde}: a palavra {n} da {fid}{nome} saiu no corte. Escolha outra âncora.")
            return (w["b"] if fim else w["a"]) + desl
        palavra, _, k = parte.partition("#")
        k = int(k) if k.isdigit() else 1
        alvo = chave(palavra)
        achou = [w for w in ws if self._bate(w["w"], alvo)]
        if len(achou) < k:
            orig = self.original.get(fid, "")
            n_orig = sum(1 for w in orig.split() if self._bate(w, alvo))
            if n_orig >= k:
                sair(f"{onde}: «{palavra}» da {fid} saiu no corte. Escolha outra âncora.")
            sair(f"{onde}: não achei «{palavra}»{'' if k == 1 else f' (vez {k})'} na {fid}. "
                 f"O que ficou dela no corte: «{' '.join(w['w'] for w in ws)}».")
        w = achou[k - 1]
        return (w["b"] if fim else w["a"]) + desl


def ler_srt(p):
    """[(ini, fim, texto)] de um .srt."""
    blocos = []
    txt = Path(p).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    for b in re.split(r"\n\s*\n", txt.strip()):
        linhas = b.strip().split("\n")
        for i, l in enumerate(linhas):
            m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", l)
            if m:
                g = [int(x) for x in m.groups()]
                ini = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
                fim = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
                texto = " ".join(linhas[i + 1:]).strip()
                if texto:
                    blocos.append((ini, fim, texto))
                break
    return blocos


def srt_tempo(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def info_video(p):
    r = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
               "-of", "json", p])
    if r.returncode:
        sair(f"Não consegui abrir o vídeo {p}.")
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    n, _, q = v["r_frame_rate"].partition("/")
    return {"dur": float(d["format"]["duration"]), "w": v["width"], "h": v["height"],
            "fps": float(n) / float(q or 1), "audio": a["codec_name"] if a else None}


def contar_quadros(p):
    """Número exato de quadros (conta os pacotes, sem decodificar)."""
    r = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
               "stream=nb_read_packets", "-of", "csv=p=0", p])
    try:
        return int(r.stdout.strip().split(",")[0])
    except ValueError:
        return None


def navegador(pw):
    """Abre o Chromium do Playwright; na primeira vez da máquina, baixa o navegador sozinho."""
    try:
        return pw.chromium.launch()
    except Exception as e:
        if "Executable doesn't exist" not in str(e) and "playwright install" not in str(e):
            raise
    print("Primeira vez: baixando o navegador que desenha os cartões (uns 150 MB, 1 a 3 min)...", flush=True)
    r = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    if r.returncode:
        sair("Não consegui baixar o navegador. Confira a internet e rode de novo.")
    return pw.chromium.launch()
