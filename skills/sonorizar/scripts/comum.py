"""Funções comuns da /sonorizar. Só biblioteca padrão; roda igual no Mac e no Windows."""
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

AUDIO = {".wav", ".mp3", ".m4a", ".aac", ".aif", ".aiff", ".flac", ".ogg", ".opus"}
VIDEO = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}
SR = 48000


def utf8():
    """Saída em UTF-8 até no console do Windows (senão "→" e acentos derrubam o script)."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def rodar(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def ff(args):
    r = rodar(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y", *args])
    if r.returncode != 0:
        sair("O ffmpeg parou com erro:\n" + r.stderr.strip()[-1500:])
    return r


def sair(msg, codigo=1):
    print(msg)
    sys.exit(codigo)


def checar_ffmpeg():
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sair("Falta o ffmpeg neste computador. Mac: brew install ffmpeg · Windows: winget install Gyan.FFmpeg "
             "(no Windows, feche e abra o Claude depois de instalar).")


def ler_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def segundos(v):
    """83.4, "83.4", "01:23,40" ou "1:23.4" -> segundos."""
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(",", ".")
    if ":" in t:
        m, s = t.rsplit(":", 1)
        h = 0
        if ":" in m:
            h, m = m.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    return float(t)


def fmt_tempo(s):
    cs = int(round(max(0.0, float(s)) * 100))
    return f"{cs // 6000:02d}:{cs // 100 % 60:02d},{cs % 100:02d}"


def fmt_num(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


def sondar(arq):
    """Duração e faixas de um arquivo de áudio ou vídeo."""
    r = rodar(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", arq])
    if r.returncode != 0:
        sair(f"Não consegui abrir o arquivo (pode estar incompleto ou ainda baixando): {arq}")
    d = json.loads(r.stdout or "{}")
    ss = d.get("streams", [])
    a = next((s for s in ss if s.get("codec_type") == "audio"), None)
    v = next((s for s in ss if s.get("codec_type") == "video"
              and not (s.get("disposition") or {}).get("attached_pic")), None)
    return {
        "duracao": float((d.get("format") or {}).get("duration") or 0),
        "tem_audio": a is not None,
        "tem_video": v is not None,
        "canais": int((a or {}).get("channels") or 0),
        "largura": int((v or {}).get("width") or 0),
        "altura": int((v or {}).get("height") or 0),
    }


def medir(arq=None, filtro=None, entradas=None):
    """Loudness integrado (LUFS), pico verdadeiro (dBTP) e pico de amostra (dBFS) com o ebur128.

    `entradas` + `filtro` medem a saída de um filter_complex (rótulo final [m]) sem gravar arquivo."""
    if entradas is None:
        entradas = ["-i", str(arq)]
        filtro = "[0:a:0]anull[m]"
    r = rodar(["ffmpeg", "-hide_banner", "-nostdin", "-nostats", *entradas, "-filter_complex",
               f"{filtro};[m]ebur128=peak=true+sample:framelog=quiet[o]", "-map", "[o]", "-f", "null", "-"])
    resumo = r.stderr[r.stderr.rfind("Summary:"):]

    def pega(rotulo):
        m = re.search(rotulo + r":\s*(-?[0-9.]+|-inf)", resumo)
        return float(m.group(1)) if m and m.group(1) != "-inf" else -99.0
    return {"lufs": pega(r"\bI"), "true_peak": pega(r"True peak:\s*Peak"), "pico": pega(r"Sample peak:\s*Peak")}


def achar_marca(pasta):
    """Pasta de edição: sobe a partir de `pasta` até achar marca/estilo.md (contrato, seção 1). None se não achar."""
    p = Path(pasta).expanduser().resolve()
    for q in [p, *p.parents]:
        if (q / "marca" / "estilo.md").is_file():
            return q
    return None


def chave(txt):
    """Palavra comparável: sem acento, sem caixa, sem pontuação ("Aluga-se," -> "alugase")."""
    t = unicodedata.normalize("NFKD", str(txt).lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", t)


ANCORA = re.compile(r"^(F\d+)(?::(.+?))?(?:([+-]\d+(?:[.,]\d+)?))?$")


class Ancoras:
    """Resolve tempos do contrato (seção 2): 42.9, "00:42,90", "F15", "F15:fim", "F15:repente#2", "F15:3",
    "F1:fim+0.25". As âncoras F<n> pedem o palavras-corte.json da /decupar."""

    def __init__(self, palavras_json=None):
        self.arquivo = palavras_json
        self.frases, self.palavras = {}, {}
        if palavras_json:
            d = ler_json(palavras_json)
            self.frases = {f["id"]: f for f in d.get("frases", [])}
            for w in d.get("palavras", []):
                self.palavras.setdefault(w["frase"], []).append(w)
            for ws in self.palavras.values():
                ws.sort(key=lambda w: w.get("n", 0))

    def tempo(self, v, borda="inicio"):
        """Segundos no vídeo cortado. `borda` = "fim" para `ate`: "F15" e "F15:palavra" valem o fim."""
        if isinstance(v, (int, float)):
            return float(v)
        txt = str(v).strip()
        m = ANCORA.match(txt)
        if not m:
            try:
                return segundos(txt)
            except ValueError:
                raise ValueError(f"não entendi o tempo «{txt}» (use segundos, \"mm:ss,cc\" ou uma âncora como \"F15:palavra\")")
        fid, alvo, desloc = m.group(1), (m.group(2) or "").strip(), m.group(3)
        desloc = float(desloc.replace(",", ".")) if desloc else 0.0
        if not self.arquivo:
            raise ValueError(f"«{txt}» é uma âncora na fala e pede o palavras-corte.json da /decupar "
                             "(\"palavras\" no som.json)")
        ws = self.palavras.get(fid)
        if fid not in self.frases and not ws:
            raise ValueError(f"«{txt}»: a frase {fid} não está no corte (o corte tirou ela inteira)")
        fr = self.frases.get(fid) or {"a": ws[0]["a"], "b": ws[-1]["b"]}
        if not alvo:
            t = fr["b"] if borda == "fim" else fr["a"]
        elif alvo in ("inicio", "fim"):
            t = fr["b"] if alvo == "fim" else fr["a"]
        else:
            w = self._palavra(fid, alvo, txt)
            t = w["b"] if borda == "fim" else w["a"]
        return t + desloc

    def _palavra(self, fid, alvo, txt):
        ws = self.palavras.get(fid) or []
        if alvo.isdigit():
            n = int(alvo)
            w = next((w for w in ws if w.get("n") == n), None)
            if w is None:
                raise ValueError(f"«{txt}»: a palavra {n} da frase {fid} sumiu no corte ou não existe")
            return w
        nome, _, k = alvo.partition("#")
        k = int(k) if k.isdigit() else 1
        achadas = [w for w in ws if chave(w["w"]) == chave(nome)]
        if len(achadas) < k:
            raise ValueError(f"«{txt}»: a palavra «{nome}» ({k}ª vez) não está no que ficou da frase {fid}; "
                             "ou o corte tirou ela, ou ela está escrita diferente na transcrição")
        return achadas[k - 1]


def ler_creditos(arq):
    """Tabela de créditos em Markdown -> {nome do arquivo: {titulo, autor, fonte, licenca}}.

    Lê a tabela que tem a coluna "Arquivo" (e as que existirem entre Título, Autor, Fonte, ID e Licença)."""
    arq = Path(arq)
    if not arq.is_file():
        return {}
    nomes = {"arquivo": "arquivo", "titulo": "titulo", "autor": "autor", "artista": "autor", "fonte": "fonte",
             "licenca": "licenca", "id": "id"}
    out, cab = {}, None
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if not linha.strip().startswith("|"):
            cab = None
            continue
        cel = [c.strip() for c in linha.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cel if c):
            continue
        if cab is None:
            cab = [nomes.get(chave(c)) for c in cel]
            continue
        d = {k: c.strip("`").strip() for k, c in zip(cab, cel) if k}
        if d.get("arquivo"):
            if d.get("id") and d.get("licenca") and d["id"] not in d["licenca"]:
                d["licenca"] += f" · ID {d['id']}"
            out[Path(d.pop("arquivo")).name.lower()] = d
    return out
