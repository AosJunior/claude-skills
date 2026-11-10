# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = [
#   "numpy",
#   "certifi",
#   "librosa",
#   "mlx-whisper>=0.4; sys_platform == 'darwin' and platform_machine == 'arm64'",
#   "faster-whisper>=1.1; sys_platform != 'darwin' or platform_machine != 'arm64'",
# ]
# ///
"""/reel-novela, narração no ElevenLabs: amostras, narração numa geração só, conferência, montagem e alinhamento
forçado.

Uso:
  uv run "<skill>/scripts/narrar.py" vozes [--busca "<texto>"] [--genero masculino|feminino]
  uv run "<skill>/scripts/narrar.py" vozes --adicionar <voice_id>
  uv run "<skill>/scripts/narrar.py" amostras --texto "<trecho do gancho>" --vozes <id,id,id> --saida <pasta>
  uv run "<skill>/scripts/narrar.py" narrar <roteiro.json> --saida <brutos/narracao> [--takes N] [--bloco <cena>]
  uv run "<skill>/scripts/narrar.py" conferir <brutos/narracao>
  uv run "<skill>/scripts/narrar.py" alinhar <narracao.wav> <roteiro.json> --saida <palavras-voz.json>
  uv run "<skill>/scripts/narrar.py" validar <narracao.wav> <palavras-voz.json>

Chave: ELEVENLABS_API_KEY no ambiente, ou --chave-arquivo <arquivo com a linha ELEVENLABS_API_KEY=...>. A chave nunca
é impressa. Gastam crédito: amostras e narrar (só os takes que ainda não existem). O alinhar custa pouco. vozes,
conferir e validar não gastam.

roteiro.json (na raiz da peça):
{"voz": "<voice_id>", "modelo": "eleven_v4", "velocidade": 1.25,
 "blocos": [{"cena": "gancho", "fala": "[dramatic] texto para o ElevenLabs, números e siglas por extenso",
             "texto": "o mesmo texto como na legenda, com algarismos e siglas", "tela": "(ignorado)", "take": 2}]}
  fala        o que o ElevenLabs lê, com as marcas de emoção ([dramatic], [serious]...); números e siglas por extenso
              («quatro milhões», «í-bê-gê-é»). Sem reticências: o eleven_v3 repetiu palavra com elas.
  texto       a mesma frase como aparece na legenda («4 milhões», «IBGE»). É dele que saem as palavras do alinhamento.
  take        opcional, no bloco ou na raiz: o take que entra na montagem (sem ele, o 1º).
  velocidade  1,2 a 1,3 (padrão 1,25): o eleven_v4 não tem ajuste de velocidade; a aceleração é feita aqui (atempo).
  geracao     "inteira" (padrão): o roteiro inteiro numa geração só, a voz igual do começo ao fim, cortada nos blocos
              pelo alinhamento forçado. "blocos": uma geração por bloco (a voz varia de um bloco para outro).

vozes      lista narradores pt-BR da biblioteca do ElevenLabs (mais usados primeiro). --adicionar põe uma voz da
           biblioteca na sua conta (algumas só funcionam pela API depois disso).
amostras   um áudio por narrador com o mesmo trecho, mais a versão acelerada (--velocidade, padrão 1,25), em <pasta>.
           Reaproveita as que já existem. Opções: --modelo (eleven_v4), --estabilidade (0,5).
narrar     gera --takes N (padrão 2) com o modelo do roteiro e reaproveita os takes que já existem (mesma fala, voz,
           modelo e estabilidade): trocar o "take" e rodar de novo não gasta crédito. Na geração inteira, cada take é o
           roteiro todo, cortado nos blocos pelo alinhamento forçado (guardado ao lado do take); mudar a fala de um
           bloco gera o roteiro todo de novo. Na geração por blocos, --bloco <cena> gera só os takes desse bloco.
           Depois acelera, encurta as pausas internas acima de --pausa-max (0,35 s; no 1º bloco, o gancho,
           --pausa-gancho 0,45 s, a pausa dramática), junta os blocos com --respiro (0,35 s) e --cauda (1,6 s) no fim,
           e grava <saida>/narracao.wav, <saida>/narracao-blocos.json e <saida>/takes.json. Takes em <saida>/takes/.
           --estabilidade 0, 0,5 ou 1 (criativo, natural, robusto; padrão 0,5). O 0 faz a voz variar.
conferir   transcreve cada bloco de cada take acelerado com o Whisper, sem dar o texto como dica (a dica faz o Whisper
           completar a palavra que a voz engoliu), compara com a fala (números e siglas igualados) e mede a entonação
           (desvio do tom em semitons: mais é mais expressivo). O take que entra está marcado com *.
alinhar    alinhamento forçado (ElevenLabs /v1/forced-alignment) da narração montada com a fala dos blocos; as
           palavras saem as do "texto" de cada bloco, com início e fim em s. Grava também <saida>-bruto.json (a
           resposta inteira, com o tempo de cada letra). --resposta <bruto.json> refaz sem chamar a API. Depois valida.
validar    confere o palavras-voz.json na onda: nenhuma palavra começando dentro de uma pausa de 120 ms ou mais e
           nenhuma palavra inteira em silêncio. Sai com código 1 e lista as palavras suspeitas.
"""
import hashlib
import json
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

sys.dont_write_bytecode = True   # sem __pycache__ dentro da skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (HOP, SR, ajuda, checar_ffmpeg, chave_eleven, fmt_num, gravar_audio, gravar_json,  # noqa: E402
                   ler_audio, ler_json, sair, sem_acento, slug, utf8)

BASE = "https://api.elevenlabs.io"
PADRAO = {"modelo": "eleven_v4", "velocidade": 1.25, "takes": 2, "respiro": 0.35, "pausa_max": 0.35,
          "pausa_gancho": 0.45, "cauda": 1.6, "estabilidade": 0.5, "semelhanca": 0.75, "geracao": "inteira"}


# ---------------------------------------------------------------------------------------------------------------
# argumentos
# ---------------------------------------------------------------------------------------------------------------
def opcao(args, nome, padrao=None):
    if nome in args:
        i = args.index(nome)
        if i + 1 >= len(args):
            sair(f"Falta o valor de {nome}.")
        return args[i + 1]
    return padrao


def numero(args, nome, padrao):
    v = opcao(args, nome)
    try:
        return float(str(v).replace(",", ".")) if v is not None else padrao
    except ValueError:
        sair(f"{nome} precisa de um número (veio «{v}»).")


# ---------------------------------------------------------------------------------------------------------------
# API do ElevenLabs (só a biblioteca padrão + certifi)
# ---------------------------------------------------------------------------------------------------------------
class ErroApi(Exception):
    def __init__(self, codigo, corpo):
        super().__init__(f"HTTP {codigo}: {corpo}")
        self.codigo, self.corpo = codigo, corpo


def api(chave, metodo, caminho, corpo=None, campos=None, arquivo=None, bruto=False, timeout=600):
    import certifi
    cab = {"xi-api-key": chave}
    dados = None
    if campos is not None or arquivo is not None:
        lim = uuid.uuid4().hex
        partes = [f'--{lim}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                  for k, v in (campos or {}).items()]
        if arquivo:
            nome, p, mime = arquivo
            partes.append(f'--{lim}\r\nContent-Disposition: form-data; name="{nome}"; filename="{Path(p).name}"\r\n'
                          f"Content-Type: {mime}\r\n\r\n".encode() + Path(p).read_bytes() + b"\r\n")
        partes.append(f"--{lim}--\r\n".encode())
        dados = b"".join(partes)
        cab["Content-Type"] = f"multipart/form-data; boundary={lim}"
    elif corpo is not None:
        dados = json.dumps(corpo).encode()
        cab["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + caminho, data=dados, headers=cab, method=metodo)
    ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            b = r.read()
            return b if bruto else json.loads(b or b"{}")
    except urllib.error.HTTPError as e:
        raise ErroApi(e.code, e.read()[:800].decode("utf-8", "replace")) from None
    except urllib.error.URLError as e:
        sair(f"Sem conexão com o ElevenLabs ({e.reason}). Confira a internet e rode de novo.")


def explicar(e, voz=None):
    """Mensagem curta para o erro da API (nunca inclui a chave)."""
    c = e.corpo.lower()
    if e.codigo == 401 or "invalid_api_key" in c:
        return "A chave do ElevenLabs foi recusada (401). Confira a ELEVENLABS_API_KEY."
    if "quota" in c or "credits" in c or e.codigo == 402:
        return "Acabaram os créditos do ElevenLabs para esta geração. Nada foi perdido: os takes prontos ficam."
    if "voice_not_found" in c or (e.codigo == 404 and voz):
        return (f"A voz {voz} não está disponível na sua conta. Rode `narrar.py vozes --adicionar {voz}` "
                "(ou adicione pela Voice Library do site) e rode de novo.")
    return f"O ElevenLabs respondeu {e.codigo}: {e.corpo[:300]}"


def saldo(chave):
    try:
        s = api(chave, "GET", "/v1/user/subscription", timeout=30)
        return int(s["character_limit"]) - int(s["character_count"])
    except Exception:  # noqa: BLE001
        return None


def tts(chave, voz, modelo, texto, estabilidade, destino):
    corpo = {"text": texto, "model_id": modelo,
             "voice_settings": {"stability": estabilidade, "similarity_boost": PADRAO["semelhanca"]}}
    audio = None
    for formato in ("mp3_44100_192", "mp3_44100_128"):    # 192 kbps só a partir do plano Creator
        try:
            audio = api(chave, "POST", f"/v1/text-to-speech/{voz}?output_format={formato}", corpo=corpo, bruto=True)
            break
        except ErroApi as e:
            if formato == "mp3_44100_192" and e.codigo in (400, 403) and "format" in e.corpo.lower():
                continue
            sair(explicar(e, voz))
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".parcial")
    tmp.write_bytes(audio)
    tmp.replace(destino)


def acelerar(origem, destino, velocidade):
    """atempo no take inteiro (48 kHz mono); feito uma vez e guardado ao lado."""
    if destino.is_file() and destino.stat().st_mtime >= origem.stat().st_mtime:
        return
    filtro = "anull" if abs(velocidade - 1) < 1e-3 else f"atempo={velocidade:.4f}"
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(origem), "-af", filtro, "-ac", "1",
                        "-ar", str(SR), "-c:a", "pcm_s16le", str(destino)], capture_output=True, text=True)
    if r.returncode:
        sair(f"O ffmpeg não acelerou {origem.name}:\n{r.stderr[-600:]}")


# ---------------------------------------------------------------------------------------------------------------
# números e siglas por extenso (para igualar o texto da legenda à fala)
# ---------------------------------------------------------------------------------------------------------------
UNID = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze",
        "treze", "catorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
DEZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
CEN = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos",
       "novecentos"]
ORD = ["", "primeiro", "segundo", "terceiro", "quarto", "quinto", "sexto", "sétimo", "oitavo", "nono"]
ORD_DEZ = ["", "décimo", "vigésimo", "trigésimo", "quadragésimo", "quinquagésimo", "sexagésimo", "septuagésimo",
           "octogésimo", "nonagésimo"]
LETRAS = {"A": "á", "B": "bê", "C": "cê", "D": "dê", "E": "é", "F": "éfe", "G": "gê", "H": "agá", "I": "i", "J": "jota",
          "K": "cá", "L": "éle", "M": "ême", "N": "êne", "O": "ó", "P": "pê", "Q": "quê", "R": "érre", "S": "ésse",
          "T": "tê", "U": "u", "V": "vê", "W": "dáblio", "X": "xis", "Y": "ípsilon", "Z": "zê"}


def ate_mil(n):
    if n == 100:
        return "cem"
    c, r = divmod(n, 100)
    partes = [CEN[c]] if c else []
    if r:
        d, u = divmod(r, 10)
        partes.append(UNID[r] if r < 20 else DEZ[d] + (f" e {UNID[u]}" if u else ""))
    return " e ".join(partes)


def por_extenso(n):
    """Inteiro por extenso, com o «e» antes do último grupo quando ele é menor que 100 ou centena redonda
    (1.200.000 → um milhão e duzentos mil; 2020 → dois mil e vinte; 1999 → mil novecentos e noventa e nove)."""
    if n == 0:
        return "zero"
    grupos, resto = [], n
    for valor, um, varios in ((10 ** 9, "bilhão", "bilhões"), (10 ** 6, "milhão", "milhões"), (1000, "mil", "mil"),
                              (1, "", "")):
        q, resto = divmod(resto, valor)
        if not q:
            continue
        if valor == 1000:
            grupos.append((q, "mil" if q == 1 else f"{ate_mil(q)} mil"))
        elif valor == 1:
            grupos.append((q, ate_mil(q)))
        else:
            grupos.append((q, f"{ate_mil(q)} {um if q == 1 else varios}"))
    textos = [t for _, t in grupos]
    q = grupos[-1][0] % 1000 or grupos[-1][0]
    if len(textos) > 1 and (q < 100 or q % 100 == 0):
        return " ".join(textos[:-1]) + " e " + textos[-1]
    return " ".join(textos)


def numero_falado(s):
    """"1.234.567", "3,4", "1999" → por extenso; None se não for número."""
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        return por_extenso(int(s.replace(".", "")))
    if re.fullmatch(r"\d+", s):
        return por_extenso(int(s))
    m = re.fullmatch(r"(\d+),(\d+)", s)
    if m:
        dec = m.group(2)
        falado_dec = " ".join(UNID[int(c)] for c in dec) if dec.startswith("0") else por_extenso(int(dec))
        return f"{por_extenso(int(m.group(1)))} vírgula {falado_dec}"
    return None


def falar_token(tok):
    """Uma palavra do texto como ela é dita: números, %, ordinais, sinais e siglas por extenso."""
    nucleo = tok.strip("«»\"'“”‘’()[]{}.,;:!?…")
    if not nucleo:
        return ""
    sinal = ""
    if nucleo[0] in "+−-" and len(nucleo) > 1 and nucleo[1].isdigit():
        sinal, nucleo = ("mais " if nucleo[0] == "+" else "menos "), nucleo[1:]
    m = re.fullmatch(r"(\d+)([ºª°])", nucleo)
    if m and 0 < int(m.group(1)) < 100:
        d, u = divmod(int(m.group(1)), 10)
        o = " ".join(p for p in (ORD_DEZ[d], ORD[u]) if p)               # 13º → décimo terceiro
        return " ".join(p[:-1] + "a" for p in o.split()) if m.group(2) == "ª" else o
    if nucleo.endswith("%"):
        n = numero_falado(nucleo[:-1])
        if n:
            return f"{sinal}{n} por cento"
    n = numero_falado(nucleo)
    if n:
        return sinal + n
    if nucleo == "R$":
        return "reais"
    if re.fullmatch(r"[A-Z]{2,6}", nucleo):
        return " ".join(LETRAS[c] for c in nucleo)
    m = re.fullmatch(r"(\d+)([a-zA-Zà-ú]+)", nucleo)          # "10mil", "5x"
    if m:
        return f"{por_extenso(int(m.group(1)))} {m.group(2)}"
    return tok


def sem_marcas(fala):
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", " ", fala)).strip()


def fala_para_alinhar(fala):
    """A fala sem as marcas de emoção, com algum algarismo que tenha sobrado por extenso."""
    return " ".join(falar_token(t) if re.search(r"\d", t) else t for t in sem_marcas(fala).split())


def normalizar(texto):
    """Palavras comparáveis: minúsculas, sem acento, hífen separa (í-bê-gê-é → i be ge e)."""
    t = sem_acento(texto.lower()).replace("-", " ")
    return re.findall(r"[a-z0-9]+", t)


# ---------------------------------------------------------------------------------------------------------------
# roteiro e takes
# ---------------------------------------------------------------------------------------------------------------
def ler_roteiro(p):
    p = Path(p).expanduser()
    if not p.is_file():
        sair(f"Não achei o roteiro: {p}")
    try:
        r = ler_json(p)
    except json.JSONDecodeError as e:
        sair(f"{p.name} não é um JSON válido: {e}")
    if not r.get("voz"):
        sair(f"Falta \"voz\" (o voice_id do narrador) no {p.name}.")
    blocos = r.get("blocos") or []
    if not blocos:
        sair(f"O {p.name} não tem blocos.")
    for i, b in enumerate(blocos, 1):
        for campo in ("cena", "fala", "texto"):
            if not str(b.get(campo, "")).strip():
                sair(f"Bloco {i} do {p.name} sem \"{campo}\".")
        if "..." in b["fala"] or "…" in b["fala"]:
            print(f"Aviso: o bloco {i} ({b['cena']}) tem reticências na fala; o eleven_v3 já repetiu palavra com elas.")
    r.setdefault("modelo", PADRAO["modelo"])
    r.setdefault("geracao", PADRAO["geracao"])
    if r["geracao"] not in ("inteira", "blocos"):
        sair(f"\"geracao\" no {p.name} é \"inteira\" ou \"blocos\" (veio «{r['geracao']}»).")
    r["velocidade"] = float(r.get("velocidade", PADRAO["velocidade"]))
    if not 1.0 <= r["velocidade"] <= 1.35:
        print(f"Aviso: velocidade {r['velocidade']} fora de 1,0–1,35 (a régua é 1,2 a 1,3).")
    return r


def chave_take(r, b, estab):
    h = hashlib.sha1(f"{r['voz']}|{r['modelo']}|{estab}|{b['fala']}".encode()).hexdigest()[:6]
    return f"{slug(b['cena'])}-{h}"


def arquivos_take(saida, base, k, velocidade):
    pasta = saida / "takes"
    return pasta / f"{base}-t{k}.mp3", pasta / f"{base}-t{k}-x{velocidade:g}.wav"


def fala_inteira(r):
    """O roteiro inteiro numa fala só: um parágrafo por bloco (a quebra dá a pausa natural entre as cenas)."""
    return "\n\n".join(b["fala"].strip() for b in r["blocos"])


def chave_inteira(r, estab):
    h = hashlib.sha1(f"{r['voz']}|{r['modelo']}|{estab}|{fala_inteira(r)}".encode()).hexdigest()[:6]
    return f"inteira-{h}"


def texto_alinhar(r):
    return " ".join(fala_para_alinhar(b["fala"]) for b in r["blocos"])


def alinhamento(chave_f, wav, texto, cache):
    """Resposta do /v1/forced-alignment para `wav`, guardada em `cache` (refazer não gasta)."""
    if cache.is_file():
        return ler_json(cache)
    print(f"  alinhando {wav.name} para cortar os blocos...")
    try:
        resp = api(chave_f(), "POST", "/v1/forced-alignment", campos={"text": texto},
                   arquivo=("file", wav, "audio/wav"), timeout=900)
    except ErroApi as e:
        sair(explicar(e))
    gravar_json(cache, resp, indent=None)
    return resp


def cortar_blocos(r, wav, resp, saida, base, k, vel):
    """Corta o take inteiro nos blocos: cada corte cai no meio do silêncio entre a última palavra de um bloco e a
    primeira do seguinte. Grava um wav por bloco ao lado do take e devolve os caminhos, na ordem dos blocos."""
    import numpy as np
    tokens, dono = [], []
    for i, b in enumerate(r["blocos"]):
        ts = b["texto"].split()
        tokens += ts
        dono += [i] * len(ts)
    palavras, _ = mapear(tokens, palavras_ditas(resp))
    n = len(r["blocos"])
    ini = [min(p["ini"] for p, d in zip(palavras, dono) if d == i) for i in range(n)]
    fim = [max(p["fim"] for p, d in zip(palavras, dono) if d == i) for i in range(n)]
    x = ler_audio(wav, canais=1)[:, 0].astype(np.float64)
    cortes = [0] + [int((fim[i] + max(ini[i + 1], fim[i])) / 2 * SR) for i in range(n - 1)] + [len(x)]
    caminhos = []
    for i, b in enumerate(r["blocos"]):
        p = saida / "takes" / f"{base}-t{k}-x{vel:g}-{i + 1:02d}-{slug(b['cena'])}.wav"
        if not (p.is_file() and p.stat().st_mtime >= wav.stat().st_mtime):
            gravar_audio(p, x[cortes[i]:cortes[i + 1]], codec="pcm_s16le")
        caminhos.append(p)
    return caminhos


# ---------------------------------------------------------------------------------------------------------------
# montagem: acelera, encurta as pausas internas, junta os blocos com respiro
# ---------------------------------------------------------------------------------------------------------------
def fala_por_quadro(x, limiar=40):
    """Quadros de 10 ms com voz: acima de `limiar` dB abaixo da fala forte (percentil 95)."""
    import numpy as np
    h = int(HOP * SR)
    k = len(x) // h
    rms = 10 * np.log10(np.mean(x[:k * h].reshape(k, h) ** 2, axis=1) + 1e-20)
    return rms > np.percentile(rms, 95) - limiar


def encurtar_pausas(x, pausa_max, pre=0.05, pos=0.08, minimo=0.12):
    """O take aparado (de `pre` s antes da primeira fala a `pos` s depois da última, com o áudio de verdade e 5 ms
    de entrada e saída) e com as pausas internas mais longas que pausa_max encurtadas para pausa_max (sai o meio do
    silêncio, com 10 ms de emenda). Devolve (áudio, relato das pausas)."""
    import numpy as np
    h = int(HOP * SR)
    f = fala_por_quadro(x)
    idx = np.flatnonzero(f)
    if not len(idx):
        return x, []
    pri, ult = int(idx[0]), int(idx[-1])
    a0, b0 = max(0, pri * h - int(pre * SR)), min(len(x), (ult + 1) * h + int(pos * SR))
    pedacos, relato, i, cursor = [], [], pri, a0
    while i <= ult:
        if f[i]:
            i += 1
            continue
        j = i
        while j <= ult and not f[j]:
            j += 1
        dur = (j - i) * HOP
        if dur >= minimo and dur > pausa_max + 0.02:
            meio = int(pausa_max / 2 * SR)
            pedacos.append(x[cursor:i * h + meio])
            cursor = j * h - meio
            relato.append(f"{dur:.2f}→{pausa_max:.2f}")
        i = j
    pedacos.append(x[cursor:b0])
    e = int(0.01 * SR)
    y = pedacos[0]
    for p in pedacos[1:]:      # emenda com cruzamento de 10 ms (é silêncio, mas evita clique)
        if len(y) > e and len(p) > e:
            mist = y[-e:] * np.linspace(1, 0, e) + p[:e] * np.linspace(0, 1, e)
            y = np.concatenate([y[:-e], mist, p[e:]])
        else:
            y = np.concatenate([y, p])
    y = y.copy()
    k = min(len(y) // 2, int(0.005 * SR))
    if k:
        y[:k] *= np.linspace(0, 1, k)
        y[-k:] *= np.linspace(1, 0, k)
    return y, relato


def montar(r, saida, escolhidos, respiro, pausa_max, pausa_gancho, cauda):
    import numpy as np
    partes, blocos, t = [], [], 0.0
    for i, (b, k, wav) in enumerate(escolhidos, 1):
        x = ler_audio(wav, canais=1)[:, 0].astype(np.float64)
        y, relato = encurtar_pausas(x, pausa_gancho if i == 1 else pausa_max, pre=0.03 if i == 1 else 0.05)
        if i > 1:
            partes.append(np.zeros(int(respiro * SR)))
            t += respiro
        ini = t
        partes.append(y)
        t += len(y) / SR
        blocos.append({"bloco": i, "cena": b["cena"], "take": f"t{k}", "arquivo": Path(wav).relative_to(saida).as_posix(),
                       "ini": round(ini, 3), "fim": round(t, 3), "pausas": relato})
    partes.append(np.zeros(int(cauda * SR)))
    voz = np.concatenate(partes)
    pico = float(np.abs(voz).max())
    if pico > 0.999:
        voz *= 0.98 / pico
    gravar_audio(saida / "narracao.wav", voz, codec="pcm_s16le")
    gravar_json(saida / "narracao-blocos.json", blocos)
    return len(voz) / SR, blocos


# ---------------------------------------------------------------------------------------------------------------
# subcomandos
# ---------------------------------------------------------------------------------------------------------------
def cmd_vozes(args):
    chave = chave_eleven(opcao(args, "--chave-arquivo"))
    alvo = opcao(args, "--adicionar")
    if alvo:
        for pagina in range(10):
            q = urllib.parse.urlencode({"page_size": 100, "page": pagina, "language": "pt"})
            try:
                d = api(chave, "GET", f"/v1/shared-voices?{q}", timeout=60)
            except ErroApi as e:
                sair(explicar(e))
            achada = next((v for v in d.get("voices", []) if v.get("voice_id") == alvo), None)
            if achada:
                try:
                    api(chave, "POST", f"/v1/voices/add/{achada['public_owner_id']}/{alvo}",
                        corpo={"new_name": achada.get("name", alvo)}, timeout=60)
                except ErroApi as e:
                    sair(explicar(e, alvo))
                print(f"Pronto: «{achada.get('name')}» ({alvo}) está na sua conta.")
                return
            if not d.get("has_more"):
                break
        sair(f"Não achei {alvo} na biblioteca em português. Adicione pela Voice Library do site.")
    q = {"page_size": 30, "language": "pt", "locale": "pt-BR", "sort": "usage_character_count_1y"}
    g = opcao(args, "--genero")
    if g:
        q["gender"] = {"masculino": "male", "feminino": "female"}.get(g, g)
    if opcao(args, "--busca"):
        q["search"] = opcao(args, "--busca")
    try:
        d = api(chave, "GET", "/v1/shared-voices?" + urllib.parse.urlencode(q), timeout=60)
    except ErroApi as e:
        sair(explicar(e))
    for v in d.get("voices", []):
        uso = int(v.get("usage_character_count_1y") or 0)
        print(f"{v.get('voice_id')}  {v.get('name')}  · {v.get('gender')}, {v.get('age')}, {v.get('descriptive')}, "
              f"{v.get('use_case')} · {uso / 1e6:.0f} mi caracteres/ano"
              + (" · na sua conta" if v.get("is_added_by_user") else ""))
        if v.get("preview_url"):
            print(f"    prévia: {v['preview_url']}")


def cmd_amostras(args):
    texto, vozes, saida = opcao(args, "--texto"), opcao(args, "--vozes"), opcao(args, "--saida")
    if not (texto and vozes and saida):
        sair("Use: narrar.py amostras --texto \"<trecho>\" --vozes <id,id,id> --saida <pasta>")
    checar_ffmpeg()
    chave = chave_eleven(opcao(args, "--chave-arquivo"))
    modelo = opcao(args, "--modelo", PADRAO["modelo"])
    vel = numero(args, "--velocidade", PADRAO["velocidade"])
    estab = numero(args, "--estabilidade", PADRAO["estabilidade"])
    saida = Path(saida).expanduser()
    ids = [v.strip() for v in vozes.split(",") if v.strip()]
    print(f"{len(ids)} amostras de {len(texto)} caracteres (créditos: até {len(ids) * len(texto)}).")
    for n, voz in enumerate(ids, 1):
        try:
            nome = api(chave, "GET", f"/v1/voices/{voz}", timeout=30).get("name", voz)
        except ErroApi:
            nome = voz
        base = saida / f"{n}-{slug(nome.split(' - ')[0])}"
        mp3 = base.with_suffix(".mp3")
        if not mp3.is_file():
            tts(chave, voz, modelo, texto, estab, mp3)
        wav = base.with_name(base.name + f"-x{vel:g}.wav")
        acelerar(mp3, wav, vel)
        print(f"  {nome} ({voz}): {wav}")
    s = saldo(chave)
    if s is not None:
        print(f"Créditos restantes: {s}")


def cmd_narrar(args):
    if len(args) < 2 or args[1].startswith("-") or not opcao(args, "--saida"):
        sair("Use: narrar.py narrar <roteiro.json> --saida <brutos/narracao> [--takes N] [--bloco <cena>]")
    checar_ffmpeg()
    r = ler_roteiro(args[1])
    saida = Path(opcao(args, "--saida")).expanduser()
    n_takes = int(numero(args, "--takes", PADRAO["takes"]))
    so_bloco = opcao(args, "--bloco")
    estab = numero(args, "--estabilidade", PADRAO["estabilidade"])
    respiro = numero(args, "--respiro", PADRAO["respiro"])
    pausa_max = numero(args, "--pausa-max", PADRAO["pausa_max"])
    pausa_gancho = numero(args, "--pausa-gancho", PADRAO["pausa_gancho"])
    cauda = numero(args, "--cauda", PADRAO["cauda"])
    vel = r["velocidade"]
    blocos = r["blocos"]
    if so_bloco and not any(b["cena"] == so_bloco for b in blocos):
        sair(f"Nenhum bloco com \"cena\": \"{so_bloco}\". Cenas: {', '.join(b['cena'] for b in blocos)}")
    if r["geracao"] == "inteira":
        if so_bloco:
            sair("Na geração inteira, cada take é o roteiro todo: mudar um bloco gera o roteiro de novo. Para gerar "
                 "só um bloco, ponha \"geracao\": \"blocos\" no roteiro (a voz desse bloco pode soar diferente).")
        return narrar_inteira(args, r, saida, n_takes, estab, respiro, pausa_max, pausa_gancho, cauda)

    # o que falta gerar: até N takes (e o take escolhido) em cada bloco, ou só no bloco do --bloco
    faltam = []
    for b in blocos:
        if so_bloco and b["cena"] != so_bloco:
            continue
        base = chave_take(r, b, estab)
        for k in range(1, max(n_takes, int(b.get("take", 1))) + 1):
            mp3, _ = arquivos_take(saida, base, k, vel)
            if not mp3.is_file():
                faltam.append((b, k, mp3))
    chave = None
    if faltam:
        chave = chave_eleven(opcao(args, "--chave-arquivo"))
        total = sum(len(b["fala"]) for b, _, _ in faltam)
        print(f"Gerando {len(faltam)} {'take' if len(faltam) == 1 else 'takes'} com {r['modelo']}: {total} caracteres "
              f"no total (a `fala` de cada bloco, marcas incluídas), descontados do saldo do ElevenLabs...")
        for b, k, mp3 in faltam:
            tts(chave, r["voz"], r["modelo"], b["fala"], estab, mp3)
            (mp3.parent / f"{mp3.name.rsplit('-t', 1)[0]}.json").write_text(json.dumps(
                {"cena": b["cena"], "fala": b["fala"], "voz": r["voz"], "modelo": r["modelo"],
                 "estabilidade": estab, "data": date.today().isoformat()}, ensure_ascii=False, indent=1),
                encoding="utf-8")
            print(f"  {mp3.name}")
    else:
        print("Nenhum take novo: todos já existem (sem gasto de crédito).")

    # acelera, monta e registra
    manifesto, escolhidos = [], []
    for i, b in enumerate(blocos, 1):
        base = chave_take(r, b, estab)
        takes = []
        for mp3 in sorted((saida / "takes").glob(f"{base}-t*.mp3")):
            k = int(re.search(r"-t(\d+)\.mp3$", mp3.name).group(1))
            _, wav = arquivos_take(saida, base, k, vel)
            acelerar(mp3, wav, vel)
            takes.append({"take": f"t{k}", "arquivo": mp3.relative_to(saida).as_posix(),
                          "acelerado": wav.relative_to(saida).as_posix()})
        k = int(b.get("take", 1))
        _, wav = arquivos_take(saida, base, k, vel)
        escolhidos.append((b, k, wav))
        manifesto.append({"bloco": i, "cena": b["cena"], "fala": b["fala"], "texto": b["texto"], "escolhido": f"t{k}",
                          "takes": takes})
    gravar_json(saida / "takes.json", manifesto)
    sem_take = [f"{b['cena']} (take {k})" for b, k, wav in escolhidos if not wav.is_file()]
    if sem_take:
        print(f"Narração não montada: falta o take escolhido de {', '.join(sem_take)}. Rode o narrar sem --bloco.")
        return
    concluir(r, saida, escolhidos, respiro, pausa_max, pausa_gancho, cauda, chave)


def concluir(r, saida, escolhidos, respiro, pausa_max, pausa_gancho, cauda, chave):
    dur, info = montar(r, saida, escolhidos, respiro, pausa_max, pausa_gancho, cauda)
    print(f"Pronto: {saida / 'narracao.wav'} ({fmt_num(dur, 2)} s, {r['velocidade']:g}×, "
          f"respiro {fmt_num(respiro, 2)} s)")
    for b in info:
        print(f"  {b['bloco']}. {b['cena']}: {b['take']} · {fmt_num(b['ini'], 2)}–{fmt_num(b['fim'], 2)} s"
              + (f" · pausas {', '.join(b['pausas'])}" if b["pausas"] else ""))
    if chave:
        s = saldo(chave)
        if s is not None:
            print(f"Créditos restantes: {s}")


def narrar_inteira(args, r, saida, n_takes, estab, respiro, pausa_max, pausa_gancho, cauda):
    """Cada take é o roteiro inteiro numa geração (a voz não muda entre os blocos), acelerado e cortado nos blocos."""
    vel, blocos = r["velocidade"], r["blocos"]
    base, texto = chave_inteira(r, estab), fala_inteira(r)
    escolha = [int(b.get("take", r.get("take", 1))) for b in blocos]
    chave = None

    def chave_f():
        nonlocal chave
        chave = chave or chave_eleven(opcao(args, "--chave-arquivo"))
        return chave

    faltam = [k for k in range(1, max([n_takes] + escolha) + 1) if not arquivos_take(saida, base, k, vel)[0].is_file()]
    if faltam:
        print(f"Gerando {len(faltam)} {'take' if len(faltam) == 1 else 'takes'} do roteiro inteiro com {r['modelo']}: "
              f"{len(texto)} caracteres por take (a `fala` de todos os blocos, marcas de emoção incluídas), "
              f"{len(texto) * len(faltam)} no total, descontados do saldo do ElevenLabs...")
        for k in faltam:
            mp3, _ = arquivos_take(saida, base, k, vel)
            tts(chave_f(), r["voz"], r["modelo"], texto, estab, mp3)
            (mp3.parent / f"{base}.json").write_text(json.dumps(
                {"geracao": "inteira", "fala": texto, "voz": r["voz"], "modelo": r["modelo"], "estabilidade": estab,
                 "data": date.today().isoformat()}, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {mp3.name}")
    else:
        print("Nenhum take novo: todos já existem (sem gasto de crédito).")

    cortados = {}
    for mp3 in sorted((saida / "takes").glob(f"{base}-t*.mp3")):
        k = int(re.search(r"-t(\d+)\.mp3$", mp3.name).group(1))
        _, wav = arquivos_take(saida, base, k, vel)
        acelerar(mp3, wav, vel)
        resp = alinhamento(chave_f, wav, texto_alinhar(r), wav.with_name(wav.stem + "-alinhamento.json"))
        cortados[k] = (mp3, cortar_blocos(r, wav, resp, saida, base, k, vel))
    manifesto, escolhidos = [], []
    for i, b in enumerate(blocos):
        takes = [{"take": f"t{k}", "arquivo": mp3.relative_to(saida).as_posix(),
                  "acelerado": partes[i].relative_to(saida).as_posix()} for k, (mp3, partes) in sorted(cortados.items())]
        k = escolha[i]
        if k not in cortados:
            sair(f"O bloco {b['cena']} pede o take {k}, que não existe. Rode com --takes {k}.")
        escolhidos.append((b, k, cortados[k][1][i]))
        manifesto.append({"bloco": i + 1, "cena": b["cena"], "fala": b["fala"], "texto": b["texto"],
                          "escolhido": f"t{k}", "takes": takes})
    gravar_json(saida / "takes.json", manifesto)
    concluir(r, saida, escolhidos, respiro, pausa_max, pausa_gancho, cauda, chave)


_MODELO = {}


def transcrever(wav, prompt):
    import os
    from importlib.util import find_spec
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    if os.environ.get("WHISPER_MOTOR") != "faster-whisper" and find_spec("mlx_whisper"):
        import mlx_whisper
        res = mlx_whisper.transcribe(str(wav), path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="pt",
                                     initial_prompt=prompt)
        return " ".join(s["text"].strip() for s in res.get("segments", []))
    from faster_whisper import WhisperModel
    if "fw" not in _MODELO:
        _MODELO["fw"] = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = _MODELO["fw"].transcribe(str(wav), language="pt", initial_prompt=prompt, vad_filter=True)
    return " ".join(s.text.strip() for s in segs)


def entonacao(wav):
    import librosa
    import numpy as np
    y, sr = librosa.load(str(wav), sr=16000)
    f0, _, _ = librosa.pyin(y, fmin=60, fmax=400, sr=sr, frame_length=1024)
    f0 = f0[~np.isnan(f0)]
    return float(np.std(12 * np.log2(f0 / np.median(f0)))) if len(f0) else 0.0


def comparavel(palavras):
    """«pra» e «para» contam como a mesma palavra: sem a dica do texto, o Whisper escreve «para»."""
    return ["para" if p == "pra" else p for p in palavras]


def igualar(texto):
    """Palavras comparáveis, com números e siglas por extenso (o Whisper escreve «4 milhões» ou «IBGE»)."""
    return comparavel(normalizar(" ".join(falar_token(t) for t in sem_marcas(texto).split())))


def cmd_conferir(args):
    if len(args) < 2:
        sair("Use: narrar.py conferir <brutos/narracao>")
    pasta = Path(args[1]).expanduser()
    if not (pasta / "takes.json").is_file():
        sair(f"Não achei {pasta / 'takes.json'}. Rode o narrar antes.")
    checar_ffmpeg()
    print("Conferindo os takes com o Whisper (na primeira vez ele baixa o modelo, uns 2 GB)...")
    for b in ler_json(pasta / "takes.json"):
        print(f"{b['bloco']}. {b['cena']} — «{b['texto'][:70]}{'…' if len(b['texto']) > 70 else ''}»")
        alvo = comparavel(normalizar(fala_para_alinhar(b["fala"])))   # na fala, maiúscula é ênfase, não sigla
        for t in b["takes"]:
            wav = pasta / t["acelerado"]
            ouvido = igualar(transcrever(wav, None))   # sem dica: com ela, o Whisper completa a palavra engolida
            dif = [(op, " ".join(alvo[i1:i2]), " ".join(ouvido[j1:j2]))
                   for op, i1, i2, j1, j2 in SequenceMatcher(None, alvo, ouvido, autojunk=False).get_opcodes()
                   if op != "equal"]
            marca = "*" if t["take"] == b["escolhido"] else " "
            dur = len(ler_audio(wav, canais=1)) / SR
            difs = "texto igual" if not dif else "; ".join(
                f"{'faltou' if op == 'delete' else 'sobrou' if op == 'insert' else 'trocou'} «{a or b_}»"
                + (f" → «{b_}»" if op == "replace" else "") for op, a, b_ in dif)
            print(f"  {marca}{t['take']}  {fmt_num(dur)} s · entonação ±{fmt_num(entonacao(wav), 2)} st · {difs}")
    print("Escolha o take inteiro com texto igual em todos os blocos; ponha \"take\": N na raiz do roteiro e rode o "
          "narrar de novo (reaproveita os takes, sem crédito). Misturar takes entre blocos faz a voz variar. Nome próprio "
          "escrito como se fala na fala (outra grafia, como claude → cloud) não é erro.")


# ---------------------------------------------------------------------------------------------------------------
# alinhamento forçado e validação
# ---------------------------------------------------------------------------------------------------------------
def palavras_ditas(resp):
    """Palavras da resposta do alinhamento, separadas também no hífen, com o tempo das letras."""
    out, atual = [], None
    for c in resp.get("characters", []):
        ch = c.get("text", "")
        if re.fullmatch(r"[\w'’]", ch):
            if atual is None:
                atual = {"t": "", "ini": c["start"], "fim": c["end"]}
            atual["t"] += ch
            atual["fim"] = c["end"]
        elif atual is not None:
            out.append(atual)
            atual = None
    if atual is not None:
        out.append(atual)
    for p in out:
        p["n"] = normalizar(p["t"])[0] if normalizar(p["t"]) else ""
    return [p for p in out if p["n"]]


def mapear(tokens, ditas):
    """Cada palavra do texto → o tempo das palavras ditas que correspondem a ela (números e siglas por extenso)."""
    esperado, dono = [], []
    for i, tok in enumerate(tokens):
        ws = normalizar(falar_token(tok))
        esperado += ws
        dono += [i] * len(ws)
    faladas = [d["n"] for d in ditas]
    tempos = [[] for _ in tokens]
    for op, i1, i2, j1, j2 in SequenceMatcher(None, esperado, faladas, autojunk=False).get_opcodes():
        if op == "equal":
            for a, b in zip(range(i1, i2), range(j1, j2)):
                tempos[dono[a]].append(ditas[b])
        elif op == "replace":
            ne, nd = i2 - i1, j2 - j1
            for j in range(ne):
                for b in range(j1 + j * nd // ne, j1 + max(j * nd // ne + 1, (j + 1) * nd // ne)):
                    if b < j2:
                        tempos[dono[i1 + j]].append(ditas[b])
    saida, faltou, ultimo = [], [], 0.0
    for i, tok in enumerate(tokens):
        if tempos[i]:
            ini, fim = min(d["ini"] for d in tempos[i]), max(d["fim"] for d in tempos[i])
        else:
            prox = next((min(d["ini"] for d in tempos[j]) for j in range(i + 1, len(tokens)) if tempos[j]), ultimo)
            ini = fim = max(ultimo, min(prox, ultimo))
            faltou.append(tok)
        ini = max(ini, ultimo) if saida else ini
        saida.append({"w": tok, "ini": round(float(ini), 3), "fim": round(float(max(fim, ini)), 3)})
        ultimo = saida[-1]["fim"]
    return saida, faltou


def validar(wav, palavras, pausa_min=0.12, tolerancia=0.06, limiar=35):
    """Palavras que começam dentro de uma pausa de 120 ms ou mais (a mais de `tolerancia` s do fim dela) e palavras
    inteiras em silêncio. Pausa = quadros de 10 ms `limiar` dB abaixo da fala forte. Calibrado na produção-base: o
    tempo do Whisper teve 6 palavras suspeitas; os dois alinhamentos forçados, nenhuma."""
    import numpy as np
    x = ler_audio(wav, canais=1)[:, 0].astype(np.float64)
    f = fala_por_quadro(x, limiar)
    k = len(f)
    pausas, i = [], 0
    while i < k:
        if f[i]:
            i += 1
            continue
        j = i
        while j < k and not f[j]:
            j += 1
        if (j - i) * HOP >= pausa_min:
            pausas.append((i * HOP, j * HOP))
        i = j
    dentro, mudas = [], []
    for p in palavras:
        for a, b in pausas:
            if a + 0.02 < p["ini"] < b - tolerancia:
                dentro.append((p, a, b))
                break
        q0, q1 = int(p["ini"] / HOP), max(int(p["ini"] / HOP) + 1, int(np.ceil(p["fim"] / HOP)))
        if q0 < k and not f[q0:min(q1, k)].any() and not (dentro and dentro[-1][0] is p):
            mudas.append(p)
    return dentro, mudas


def relatar_validacao(wav, palavras):
    dentro, mudas = validar(wav, palavras)
    print(f"Validação na onda: {len(palavras)} palavras · {len(dentro)} começando dentro de pausa · "
          f"{len(mudas)} em silêncio")
    for p, a, b in dentro:
        print(f"  começa dentro da pausa {fmt_num(a, 2)}–{fmt_num(b, 2)} s: «{p['w']}» em {fmt_num(p['ini'], 2)} s")
    for p in mudas:
        print(f"  em silêncio: «{p['w']}» {fmt_num(p['ini'], 2)}–{fmt_num(p['fim'], 2)} s")
    if dentro or mudas:
        print("Confira essas palavras na onda: o tempo certo é onde a voz volta. Corrija à mão no JSON se precisar.")
    return not (dentro or mudas)


def cmd_alinhar(args):
    if len(args) < 3 or not opcao(args, "--saida"):
        sair("Use: narrar.py alinhar <narracao.wav> <roteiro.json> --saida <palavras-voz.json>")
    checar_ffmpeg()
    wav, r = Path(args[1]).expanduser(), ler_roteiro(args[2])
    if not wav.is_file():
        sair(f"Não achei a narração: {wav}")
    saida = Path(opcao(args, "--saida")).expanduser()
    bruto = saida.with_name(saida.stem + "-bruto.json")
    if opcao(args, "--resposta"):
        resp = ler_json(Path(opcao(args, "--resposta")).expanduser())
    else:
        chave = chave_eleven(opcao(args, "--chave-arquivo"))
        texto = " ".join(fala_para_alinhar(b["fala"]) for b in r["blocos"])
        print(f"Alinhando {wav.name} com {len(texto)} caracteres de fala...")
        try:
            resp = api(chave, "POST", "/v1/forced-alignment", campos={"text": texto},
                       arquivo=("file", wav, "audio/wav"), timeout=900)
        except ErroApi as e:
            sair(explicar(e))
        saida.parent.mkdir(parents=True, exist_ok=True)
        gravar_json(bruto, resp, indent=None)
    ditas = palavras_ditas(resp)
    tokens = [t for b in r["blocos"] for t in b["texto"].split()]
    palavras, faltou = mapear(tokens, ditas)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text("[\n" + ",\n".join(json.dumps(p, ensure_ascii=False) for p in palavras) + "\n]\n",
                     encoding="utf-8")
    print(f"Pronto: {saida} ({len(palavras)} palavras do texto; {len(ditas)} palavras ditas)")
    if faltou:
        print(f"Sem tempo próprio (ficaram coladas na vizinha): {', '.join(faltou[:12])}")
    if "loss" in resp:
        print(f"Confiança do alinhamento (loss médio, menor é melhor): {fmt_num(float(resp['loss']), 2)}")
    sys.exit(0 if relatar_validacao(wav, palavras) else 1)


def cmd_validar(args):
    if len(args) < 3:
        sair("Use: narrar.py validar <narracao.wav> <palavras-voz.json>")
    checar_ffmpeg()
    sys.exit(0 if relatar_validacao(Path(args[1]).expanduser(), ler_json(Path(args[2]).expanduser())) else 1)


def main():
    utf8()
    ajuda(__doc__)
    args = sys.argv[1:]
    cmds = {"vozes": cmd_vozes, "amostras": cmd_amostras, "narrar": cmd_narrar, "conferir": cmd_conferir,
            "alinhar": cmd_alinhar, "validar": cmd_validar}
    if not args or args[0] not in cmds:
        sair(__doc__)
    cmds[args[0]](args)


if __name__ == "__main__":
    main()
