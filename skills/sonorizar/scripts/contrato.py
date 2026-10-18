"""Contrato do kit de edição (docs/edicao-contrato.md): achar a marca, caminhos dos JSONs e âncoras na fala.

Este arquivo é o MESMO nas skills /decupar, /inserir, /sonorizar e /criticar: elas são instaladas uma a uma e não
importam código umas das outras. Mudou aqui, copie para as quatro; o tests/test_contrato.py do repositório confere
que os quatro arquivos são iguais e dão o mesmo resultado. Só biblioteca padrão, Python 3.9 ou mais novo.
"""
import json
import os
import re
import unicodedata
from pathlib import Path

VERSAO = 2
EMENDA_QUADROS = 3          # uma borda a menos de 3 quadros de uma emenda encosta nela (contrato, seção 2)
EMENDA_MAX = 1.0            # s; "F15:emenda" só vale se a F15 começa até 1 s depois do corte da imagem


class ErroContrato(ValueError):
    """Âncora, tempo ou caminho que não dá para resolver. A mensagem já diz o que fazer."""


# ---------------------------------------------------------------- marca e caminhos (seção 1)

def achar_marca(pasta):
    """Sobe a partir de `pasta` até achar marca/estilo.md (ou chegar à raiz do disco). Devolve a pasta marca/ ou None.
    Não segue atalhos (symlinks): vale a pasta como a pessoa a vê."""
    p = Path(os.path.abspath(os.path.expanduser(str(pasta))))
    for d in (p, *p.parents):
        if (d / "marca" / "estilo.md").is_file():
            return d / "marca"
    return None


def texto_marca(marca):
    return f"Marca: {marca}" if marca else "Marca: nenhuma"


def caminho(c, base, marca):
    """Caminho escrito num JSON. "marca/..." vale contra a pasta de edição (a que contém marca/); outro relativo,
    contra `base` (a pasta do próprio JSON). Sem marca achada, "marca/..." é erro."""
    s = str(c).replace("\\", "/")
    if s.startswith("marca/"):
        if not marca:
            raise ErroContrato(f"o caminho {c} começa com marca/, mas não achei a pasta marca (com estilo.md) na "
                               "pasta do vídeo nem acima dela")
        return Path(os.path.normpath(Path(marca).parent / s))
    p = Path(os.path.expanduser(s))
    return Path(os.path.normpath(p if p.is_absolute() else Path(base) / p))


# ---------------------------------------------------------------- tempos e âncoras (seção 2)

ANCORA = re.compile(r"[Ff](\d+)(?::(.*?))?([+-]\d+(?:[.,]\d+)?)?")
RELOGIO = re.compile(r"(?:(\d+):)?(?:(\d+):)?(\d+(?:[.,]\d+)?)")
FORMAS = ('segundos (83.45), "01:23,45" ou uma âncora na fala ("F12", "F12:fim", "F12:palavra", "F12:palavra#2", '
          '"F12:3", "F12:emenda", "F12:fim+0.2")')


def chave(w):
    """Palavra sem acento, caixa e pontuação ("Aluga-se," -> "alugase"): é assim que as âncoras comparam."""
    s = unicodedata.normalize("NFKD", str(w)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def segundos(v):
    """42.9, "42,9", "00:42,90" ou "1:02:03.5" -> segundos. Âncora na fala não passa por aqui."""
    if isinstance(v, bool):
        raise ErroContrato(f"não entendi o tempo {v!r}. Use {FORMAS}.")
    if isinstance(v, (int, float)):
        return float(v)
    m = RELOGIO.fullmatch(str(v).strip())
    if not m:
        raise ErroContrato(f"não entendi o tempo «{v}». Use {FORMAS}.")
    a, b, s = m.groups()
    h, mi = (int(a), int(b)) if b is not None else (0, int(a or 0))
    return h * 3600 + mi * 60 + float(s.replace(",", "."))


def eh_ancora(v):
    return isinstance(v, str) and ANCORA.fullmatch(v.strip()) is not None


class Ancoras:
    """Resolve os tempos da seção 2 do contrato contra uma lista de frases e palavras.

    - `Ancoras.de_corte(palavras-corte.json)`: tempo do vídeo cortado (/inserir, /sonorizar, /criticar);
    - `Ancoras.do_bruto(frases, palavras)`: tempo do bruto (/decupar, no cortes.json).
    `resolver(v, fim)` devolve (segundos, palavra): a palavra (dict) quando a âncora aponta uma palavra ou a borda
    de uma frase sem deslocamento, senão None. `fim=True` é o lado `ate`: "F15" e "F15:palavra" valem o fim.
    `tempo(v, fim)` devolve só os segundos, encostados na emenda (no vídeo cortado; o bruto não tem emendas)."""

    def __init__(self, frases=None, palavras=None, original=None, sem_fala=None):
        self.frases = dict(frases or {})               # id -> {"a", "b", "texto"}
        self.palavras = {}                             # id -> [palavra, ...] em ordem de n
        for w in palavras or []:
            self.palavras.setdefault(w["frase"], []).append(w)
        for ws in self.palavras.values():
            ws.sort(key=lambda w: (w.get("n") or 0, w["a"]))
        self.original = dict(original or {})          # id -> texto da frase no bruto (para dizer o que sumiu)
        self.sem_fala = sem_fala                       # motivo de não aceitar âncora (falta o palavras-corte.json)
        self.arquivo = None
        self.trechos, self.emendas, self.fps, self.duracao = [], [], None, None

    # -------------------------------------------------- construir

    @classmethod
    def de_corte(cls, arquivo, transcricao=None):
        """Lê o decupagem/palavras-corte.json (seção 3.2). Sem o arquivo, só segundos e relógio valem.
        `transcricao`: a transcricao.txt do bruto (padrão: ao lado do JSON), para dizer qual palavra o corte tirou."""
        p = Path(arquivo) if arquivo else None
        if p is None or not p.is_file():
            return cls(sem_fala="a âncora na fala pede o decupagem/palavras-corte.json, que a /decupar grava "
                                "(rode a /decupar de novo ou use segundos)")
        d = json.loads(p.read_text(encoding="utf-8"))
        pal = [w for w in d.get("palavras", []) if str(w.get("w", "")).strip() and w.get("frase")]
        frases = {}
        for f in d.get("frases", []):
            x = frases.setdefault(f["id"], {"a": f["a"], "b": f["b"], "texto": []})
            x["a"], x["b"] = min(x["a"], f["a"]), max(x["b"], f["b"])
            x["texto"].append(f.get("texto", ""))
        for w in pal:                                   # frase sem linha em "frases": sai das palavras
            x = frases.setdefault(w["frase"], {"a": w["a"], "b": w["b"], "texto": []})
            x["a"], x["b"] = min(x["a"], w["a"]), max(x["b"], w["b"])
        for x in frases.values():
            x["texto"] = " ".join(t for t in x["texto"] if t)
        t = Path(transcricao) if transcricao else p.parent / "transcricao.txt"
        original = {}
        if t.is_file():
            for linha in t.read_text(encoding="utf-8").splitlines():
                m = re.match(r"\s*(F\d+)\s+\[[^\]]*\]\s+(.*)$", linha)
                if m:
                    original[m.group(1)] = m.group(2).strip()
        a = cls(frases, pal, original)
        a.arquivo = p
        a.duracao, a.fps = d.get("duracao"), d.get("fps")
        a.trechos = list(d.get("trechos") or [])
        a.emendas = sorted(float(x) for x in d.get("emendas") or [tr["b"] for tr in a.trechos[:-1]])
        return a

    @classmethod
    def do_bruto(cls, frases, palavras, limite_palavra=None):
        """`frases`: a lista de .dados/frases.json ({id, ini, fim, i0, i1, texto}); `palavras`: a lista de
        .dados/palavras.json ({w, ini, fim}). `limite_palavra` (s) corta a palavra que o Whisper esticou."""
        fs, pal = {}, []
        for f in frases:
            fs[f["id"]] = {"a": f["ini"], "b": f["fim"], "texto": f.get("texto", "")}
            n = 0
            for i in range(f["i0"], f["i1"] + 1):
                w = palavras[i]
                if not str(w.get("w", "")).strip():
                    continue
                n += 1
                b = w["fim"] if limite_palavra is None else min(w["fim"], w["ini"] + limite_palavra)
                pal.append({"w": w["w"], "a": w["ini"], "b": b, "frase": f["id"], "n": n, "i": i})
        return cls(fs, pal, {k: v["texto"] for k, v in fs.items()})

    # -------------------------------------------------- resolver

    def tempo(self, v, fim=False):
        """Segundos, já encostados na emenda quando caem a menos de 3 quadros dela (ver `encostar`)."""
        return self.encostar(self.resolver(v, fim)[0])[0]

    def resolver(self, v, fim=False):
        if v is None:
            raise ErroContrato("falta o tempo")
        if not eh_ancora(v):
            return segundos(v), None
        s = v.strip()
        m = ANCORA.fullmatch(s)
        fid, alvo = f"F{int(m.group(1))}", (m.group(2) or "").strip()
        desl = float(m.group(3).replace(",", ".")) if m.group(3) else 0.0
        if self.sem_fala:
            raise ErroContrato(f"«{s}»: {self.sem_fala}")
        f, ws = self.frases.get(fid), self.palavras.get(fid, [])
        if f is None or not ws:
            if fid in self.original:
                raise ErroContrato(f"«{s}»: a frase {fid} («{self.original[fid][:60]}») saiu no corte. "
                                   "Escolha outra âncora.")
            raise ErroContrato(f"«{s}»: a frase {fid} não existe na transcrição.")
        if not alvo:
            t, w = (f["b"] if fim else f["a"]), None
        elif chave(alvo) == "inicio":
            t, w = f["a"], ws[0]
        elif chave(alvo) == "fim":
            t, w = f["b"], ws[-1]
        elif chave(alvo) == "emenda":
            t, w = self._emenda(fid, ws, s), None
        else:
            w = self._palavra(fid, alvo, s, ws)
            t = w["b"] if fim else w["a"]
        return (t + desl, None) if m.group(3) else (t, w)

    def _palavra(self, fid, alvo, s, ws):
        """A palavra pedida: "3" é a 3ª da frase (contando de 1); "loja" ou "loja#2", a 1ª (ou 2ª) "loja".
        Número falado se escreve com #: "10#1" é a palavra "10"; "10" sozinho é a 10ª palavra."""
        orig = self.original.get(fid, "")
        if alvo.isdigit():
            n = int(alvo)
            w = next((w for w in ws if w.get("n") == n), None)
            if w is None:
                tokens = orig.split()
                if 0 < n <= len(tokens) and len(tokens) > len(ws):
                    raise ErroContrato(f"«{s}»: a palavra {n} da {fid} («{tokens[n - 1]}») saiu no corte. "
                                       "Escolha outra âncora.")
                raise ErroContrato(f"«{s}»: a {fid} não tem palavra {n} (ficou «{' '.join(w['w'] for w in ws)}»). "
                                   "Para um número falado, escreva o número com #1 (\"F81:10#1\").")
            return w
        nome, _, k = alvo.partition("#")
        k = int(k) if k.strip().isdigit() else 1
        achou = [w for w in ws if chave(w["w"]) == chave(nome)]
        if len(achou) < k:
            vez = "" if k == 1 else f" (a {k}ª vez)"
            if sum(1 for x in orig.split() if chave(x) == chave(nome)) >= k:
                raise ErroContrato(f"«{s}»: «{nome}»{vez} da {fid} saiu no corte. Escolha outra âncora.")
            raise ErroContrato(f"«{s}»: não achei «{nome}»{vez} na {fid}. O que ela tem: «{' '.join(w['w'] for w in ws)}».")
        return achou[k - 1]

    # -------------------------------------------------- emendas

    def _emenda(self, fid, ws, s):
        """"F15:emenda": o corte da imagem logo antes da 1ª palavra que ficou da F15 (o começo do plano dela)."""
        if self.duracao is None:
            raise ErroContrato(f"«{s}»: a emenda só existe no vídeo cortado (a /decupar não usa \"emenda\")")
        x = ws[0]["a"]
        e = max([0.0] + [t for t in self.emendas if t <= x + 1e-6])
        if x - e > EMENDA_MAX:
            raise ErroContrato(f"«{s}»: a {fid} não começa logo depois de uma emenda (a de antes fica "
                               f"{x - e:.2f} s antes da 1ª palavra). Use outra frase ou segundos.")
        return e

    def encostar(self, t, quadros=EMENDA_QUADROS):
        """Borda que cai a menos de `quadros` quadros de uma emenda (corte da imagem no vídeo cortado) vai para a
        emenda: sem isso sobra um pedaço de 1 ou 2 quadros (quadro solto). Devolve (tempo, encostou)."""
        if not self.emendas or not self.fps or t is None:
            return t, False
        e = min(self.emendas, key=lambda x: abs(x - t))
        if 1e-6 < abs(e - t) < quadros / float(self.fps):
            return e, True
        return t, False
