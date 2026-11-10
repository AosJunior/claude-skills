# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy"]
# ///
"""/reel-novela, efeitos: monta o sequencia/som/efeitos.json (a lista que o mixar.py toca) a partir da imagem.

Uso:
  uv run "<skill>/scripts/efeitos.py" <pasta da peça>                monta, aplica as regras e confere
  uv run "<skill>/scripts/efeitos.py" <pasta da peça> --sem-conferir  monta e aplica as regras, sem conferir o pico

Fontes, relidas a cada rodada:
1. Roletas: `node briefings/roleta-ticks.cjs` (em sequencia/motion/) dá o giro de cada número, em tempo real. Cada
   roleta, ou grupo de roletas que giram juntas, ganha um único som pronto de roda, alinhado pelo fim: o último
   estalo forte do som ("parada" na paleta) cai na última trava. Roda curta ("giro" na paleta): toca só os últimos
   "giro" s antes do estalo, mais a "cauda", com entrada e saída. Sem "giro", toca a roda inteira e corta o começo
   quando o giro é mais curto. Com "so_principal", soa só o grupo de uma roleta marcada "principal": true no
   eventos/<cena>.json, um por cena; as outras giram mudas. Roleta nova no assets/roletas.js entra sozinha.
2. Eventos das cenas: todo sequencia/som/eventos/<cena>.json. O "tipo" vira as camadas da paleta.

Paleta: sequencia/som/paleta.json, se existir; senão, a paleta inicial da skill (scripts/paleta.json). Ela diz de que
arquivo vem cada som (com o ID do Epidemic), o corte, o ponto que alinha e o volume padrão de cada tipo. Os cortes
são feitos aqui e guardados em sequencia/som/sons/cortes/. Som que falta: o script lista o arquivo e o ID e para.

Regras aplicadas sozinhas (cada remoção aparece no relatório):
- swoosh (camada marcada "swoosh" na paleta): nunca dois a menos de 5 s. Ficam primeiro os "fixo", depois as viradas,
  os golpes e as câmeras; o que não cabe sai. Num golpe, sai só o whoosh e o impacto fica;
- "max" na paleta (a câmera tem 3): o que passar sai, ficam os primeiros;
- o mesmo arquivo a menos de 2 s do anterior sai, e fica o primeiro (a roleta e o evento com "repetir" não contam);
- variações: evento sem "var" pega a próxima variação do tipo, então duas seguidas nunca usam o mesmo arquivo.
Conferência (sai com código 1 e diz onde): evento sem motivo, pico da soma dos efeitos acima de -1 dBFS (com e sem
trilha) e mais de 4 camadas começando na mesma janela de 150 ms. Mais de 50 efeitos à mão a cada 90 s gera aviso.

eventos/<cena>.json:
{
 "cena": "mapa",
 "roletas": {"mp-total": {"principal": true, "vol": -1}},
 "eventos": [
  {"t": 14.06, "tipo": "virada", "motivo": "a câmera mergulha no mapa (pico quando o contorno aparece)"},
  {"t": 15.42, "desloc": 0.2, "tipo": "camera", "var": 2, "motivo": "zoom no gráfico, pico no meio do movimento"},
  {"t": 16.82, "tipo": "cartao", "var": 1, "vol": 0, "motivo": "o cartão do estado entra"},
  {"t": 18.15, "tipo": "golpe", "vol": 5, "fixo": true, "motivo": "a frase-resposta pousa"},
  {"t_real": 30.5, "som": "sons/clique-seco.wav", "alinhar": "ataque", "repetir": true, "motivo": "som avulso"}
 ]
}
  t           tempo do código (o mesmo que a cena passa ao a()); vira tempo real pelo VOZ.w do assets/voz.js
  t_real      tempo real do vídeo, para o que não está preso ao código
  desloc      segundos reais somados depois da conversão (para cair no meio de um movimento)
  tipo / som  um tipo da paleta, ou um som avulso (caminho em sequencia/som/ ou nome de som da paleta)
  var         variação (1, 2, 3); sem ela, alterna sozinha
  vol         volume (pico em -12 + vol dBFS); sem ele, o padrão do tipo. De 0 a +5; em cima da fala, mais baixo
  motivo      o que acontece na imagem (obrigatório)
  fixo        nunca sai pelas regras · repetir: pode repetir o mesmo som a menos de 2 s (ex.: um clique por letra)
  so_com_trilha  só toca na versão com trilha · dur: corta o som (s), com 12 ms de saída
  tamanho, neutro  para o variar.py, que roda depois: "tamanho": "grande" soa mais grave; "neutro": true sem sorteio
  alinhar, de, ate, saida  só para som avulso: ponto que alinha (ataque, pico, fim, inicio) e corte (s)
  roletas     por nome da roleta: "principal": true (a roda soa nela; uma por cena) e "vol" (-50 ou menos: muda)
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.dont_write_bytecode = True   # sem __pycache__ dentro da skill
sys.path.insert(0, str(AQUI))
from comum import SR, ajuda, checar_ffmpeg, checar_node, gravar_audio, gravar_json, ler_audio, ler_json, rodar, \
    sair, utf8  # noqa: E402
ajuda(__doc__)   # --help sai antes de importar numpy: funciona sem o uv ter baixado nada
import numpy as np  # noqa: E402

PICO_EFEITO = -12.0   # o mixar.py põe o pico de cada efeito em -12 + vol dBFS
TETO = -1.0           # pico máximo da soma dos efeitos
SWOOSH_MIN = 5.0      # s entre dois swooshes
REPETE_MIN = 2.0      # s entre duas vezes o mesmo arquivo
POR_90S = 50          # efeitos à mão a cada 90 s, no máximo
PRIORIDADE = {"virada": 1, "golpe": 2, "camera": 3}

avisos, notas = [], []


# ---------------------------------------------------------------------------------------------------------------
# node: VOZ.w, roletas e janelas das cenas
# ---------------------------------------------------------------------------------------------------------------
JS_VOZ = r"""
const fs = require("fs"), vm = require("vm");
const ctx = { window: {} }; vm.createContext(ctx);
vm.runInContext(fs.readFileSync("assets/voz.js", "utf8"), ctx, { filename: "voz.js" });
const V = ctx.window.VOZ || ctx.VOZ;
const ts = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
console.log(JSON.stringify(ts.map((t) => +V.w(t).toFixed(3))));
"""


def tempo_real(motion, tempos):
    """Tempo do código → tempo real, pelo VOZ.w do assets/voz.js (com o mesmo arredondamento das cenas)."""
    if not tempos:
        return []
    if not (motion / "assets" / "voz.js").is_file():
        notas.append("sem assets/voz.js: tempo do código = tempo real")
        return [round(t, 3) for t in tempos]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t.json"
        p.write_text(json.dumps(tempos), encoding="utf-8")
        r = rodar(["node", "-e", JS_VOZ, p], cwd=motion)
    if r.returncode:
        sair("O assets/voz.js não rodou no node:\n" + r.stderr[-800:])
    return json.loads(r.stdout)


def ticks_das_roletas(motion):
    cjs = motion / "briefings" / "roleta-ticks.cjs"
    if not cjs.is_file():
        notas.append("sem briefings/roleta-ticks.cjs: nenhuma roleta")
        return []
    r = rodar(["node", "briefings/roleta-ticks.cjs"], cwd=motion)
    if r.returncode == 2 and r.stdout.strip():
        avisos.append("roleta-ticks.cjs pulou roleta quebrada: " + r.stderr.strip()[-400:])
    elif r.returncode:
        sair("O roleta-ticks.cjs falhou:\n" + r.stderr[-800:])
    return json.loads(r.stdout or "[]")


def janelas_das_cenas(motion):
    """[(início, nome)] das cenas do index.html (data-composition-id + data-start), sem a legenda."""
    import re
    p = motion / "index.html"
    if not p.is_file():
        return []
    out = []
    for tag in re.findall(r"<div\b[^>]*>", p.read_text(encoding="utf-8")):
        cid = re.search(r'data-composition-id="([^"]+)"', tag)
        ini = re.search(r'data-start="([0-9.]+)"', tag)
        if cid and ini and cid.group(1) not in ("main", "legenda"):
            out.append((float(ini.group(1)), cid.group(1)))
    return sorted(out)


def duracao_do_video(motion):
    """data-duration da composição principal do index.html (0 se não achar)."""
    import re
    p = motion / "index.html"
    if p.is_file():
        for tag in re.findall(r"<div\b[^>]*>", p.read_text(encoding="utf-8")):
            if 'data-composition-id="main"' in tag:
                m = re.search(r'data-duration="([0-9.]+)"', tag)
                return float(m.group(1)) if m else 0.0
    return 0.0


def cena_de(t, janelas):
    nome = janelas[0][1] if janelas else "video"
    for t0, n in janelas:
        if t >= t0 - 1e-6:
            nome = n
    return nome


# ---------------------------------------------------------------------------------------------------------------
# sons: leitura, cortes e pontos de alinhamento
# ---------------------------------------------------------------------------------------------------------------
_audio = {}


def medir_som(arq):
    """(áudio, pico, pontos): o ponto do arquivo que importa, medido no próprio som."""
    if arq not in _audio:
        x = ler_audio(arq)
        m = np.abs(x).max(1)
        j = int(0.005 * SR)
        k = max(1, len(m) // j)
        env = 20 * np.log10(np.sqrt((m[:k * j].reshape(k, j) ** 2).mean(1)) + 1e-9)
        top = env.max()
        pos = {
            "inicio": 0.0,
            "ataque": float(np.argmax(env > top - 20) * j / SR),
            "pico": float((np.argmax(env) + 0.5) * j / SR),
            "fim": float((np.where(env > top - 12)[0].max() + 1) * j / SR),
        }
        _audio[arq] = (x, float(m.max()) + 1e-9, pos)
    return _audio[arq]


def parada_auto(arq):
    """Ataque do último estalo forte (a até 8 dB do pico) de um som de roda: onde a roda para."""
    x, _, _ = medir_som(arq)
    m = np.abs(x).max(1)
    j = int(0.002 * SR)
    k = len(m) // j
    env = 20 * np.log10(m[:k * j].reshape(k, j).max(1) + 1e-9)
    fortes = np.flatnonzero(env > env.max() - 8)
    i = int(fortes[-1])
    while i > 0 and env[i - 1] > env[i] - 20 and env[i - 1] <= env[i]:
        i -= 1
    return round(i * j / SR, 3)


class Sons:
    def __init__(self, som_dir, paleta):
        self.som = som_dir
        self.sons = paleta.get("sons", {})
        self.faltando = {}

    def origem(self, chave):
        """Caminho (relativo a sequencia/som) do arquivo de um som da paleta ou avulso."""
        if chave in self.sons:
            rel = self.sons[chave]["arquivo"]
        else:
            rel = chave
        if not (self.som / rel).is_file():
            info = self.sons.get(chave, {})
            self.faltando[rel] = info
        return rel

    def arquivo(self, camada):
        """O arquivo que a camada toca: o som inteiro ou um corte dele (feito uma vez, em sons/cortes/)."""
        rel = self.origem(camada["som"])
        de, ate = camada.get("de"), camada.get("ate")
        if de is None and ate is None:
            return rel
        if not (self.som / rel).is_file():
            return rel
        ent = float(camada.get("entrada", 0.004 if de else 0.0))
        sai = float(camada.get("saida", 0.012 if ate is not None else 0.0))
        ms = lambda s: f"{int(round(s * 1000)):05d}"  # noqa: E731
        nome = (f"{Path(rel).stem}-{ms(de or 0)}-{'fim' if ate is None else ms(ate)}"
                f"-e{int(round(ent * 1000))}-s{int(round(sai * 1000))}.wav")
        destino = self.som / "sons" / "cortes" / nome
        if not destino.is_file() or destino.stat().st_mtime < (self.som / rel).stat().st_mtime:
            destino.parent.mkdir(parents=True, exist_ok=True)
            x = ler_audio(self.som / rel)
            y = x[int(round((de or 0) * SR)): None if ate is None else int(round(ate * SR))].copy()
            if ent > 0:
                k = min(len(y), int(ent * SR))
                y[:k] *= np.linspace(0, 1, k)[:, None]
            if sai > 0:
                k = min(len(y), int(sai * SR))
                y[-k:] *= np.linspace(1, 0, k)[:, None]
            gravar_audio(destino, y, codec="pcm_s24le")
        return f"sons/cortes/{nome}"


# ---------------------------------------------------------------------------------------------------------------
# eventos → camadas
# ---------------------------------------------------------------------------------------------------------------
def ler_eventos(som):
    eventos, ajustes, faltas = [], {}, []
    pasta = som / "eventos"
    for p in sorted(pasta.glob("*.json")) if pasta.is_dir() else []:
        try:
            d = ler_json(p)
        except json.JSONDecodeError as e:
            sair(f"{p.name} não é um JSON válido: {e}")
        cena = d.get("cena", p.stem)
        for nome, aj in (d.get("roletas") or {}).items():
            ajustes.setdefault(nome, {}).update(aj)
        for i, e in enumerate(d.get("eventos", [])):
            if not str(e.get("motivo", "")).strip():
                faltas.append(f"{p.name} #{i + 1} (t {e.get('t', e.get('t_real'))}) sem motivo")
            if "t" not in e and "t_real" not in e:
                sair(f"{p.name} #{i + 1}: falta t (tempo do código) ou t_real")
            if "tipo" not in e and "som" not in e:
                sair(f"{p.name} #{i + 1}: falta tipo (da paleta) ou som (avulso)")
            eventos.append(dict(e, cena=cena, arquivo_eventos=p.name, indice=i + 1))
    return eventos, ajustes, faltas


def escolher_variacoes(eventos, tipos):
    """Evento sem var pega a próxima variação do tipo (duas seguidas nunca usam o mesmo arquivo). Var escrita no
    evento é escolha de quem escreveu (ex.: a variação certa para o motivo) e fica como está."""
    ultimo = {}
    for e in sorted(eventos, key=lambda e: e["no"]):
        if "tipo" not in e:
            continue
        tipo = e["tipo"]
        if tipo not in tipos:
            sair(f"{e['arquivo_eventos']} #{e['indice']}: tipo «{tipo}» não está na paleta ({', '.join(tipos)})")
        n = len(tipos[tipo]["var"])
        if e.get("var") is not None:
            v = int(e["var"])
            if not 1 <= v <= n:
                sair(f"{e['arquivo_eventos']} #{e['indice']}: «{tipo}» tem {n} variação(ões); pediram {v}")
        else:
            v = (ultimo.get(tipo, 0) % n) + 1
        e["var_usada"] = v
        ultimo[tipo] = v


def expandir(e, tipos, sons):
    """Um evento → as camadas dele, cada uma alinhada pelo ponto que importa e com o volume final."""
    if "tipo" in e:
        spec = tipos[e["tipo"]]
        camadas = spec["var"][e["var_usada"] - 1]
        vol = float(e.get("vol", spec.get("vol", 0)))
        tipo = e["tipo"]
    else:
        camadas = [{k: e[k] for k in ("som", "de", "ate", "entrada", "saida") if k in e}
                   | {"alinhar": e.get("alinhar", "ataque")}]
        vol = float(e.get("vol", 0))
        tipo = "som"
    out = []
    for c in camadas:
        rel = sons.arquivo(c)
        if not (sons.som / rel).is_file():
            continue
        _, _, pos = medir_som(sons.som / rel)
        alinhar = c.get("alinhar", "ataque")
        if alinhar not in pos:
            sair(f"alinhar «{alinhar}» não existe (use ataque, pico, fim ou inicio)")
        t = e["no"] + float(c.get("desloc", 0)) - pos[alinhar]
        if t < 0:
            if t < -0.03:
                avisos.append(f"{e['cena']} {tipo} em {e['no']:.3f} s: {rel} precisaria começar em {t:.3f} s; foi para 0")
            t = 0.0
        camada = {"t": round(t, 4), "som": rel, "vol": round(vol + float(c.get("rel", 0)), 2),
                  "motivo": e.get("motivo", ""), "cena": e["cena"], "tipo": tipo, "no": round(e["no"], 3)}
        for k in ("so_com_trilha", "dur", "tamanho", "neutro"):   # tamanho e neutro: para o variar.py
            if e.get(k):
                camada[k] = e[k]
        camada["_swoosh"] = bool(c.get("swoosh"))
        camada["_fixo"] = bool(e.get("fixo"))
        camada["_repetir"] = bool(e.get("repetir"))
        camada["_evento"] = id(e)
        out.append(camada)
    return out


def roletas(ticks, ajustes, cfg, sons, janelas):
    """Um som de roda por giro (ou grupo de giros juntos), parado na última trava. Com "giro" na paleta, a roda é
    curta: só os últimos "giro" s antes do estalo, mais a "cauda". Com "so_principal", soa só o grupo que tem uma
    roleta marcada "principal", um por cena; o resto gira mudo. Volume -50 ou menos também deixa mudo."""
    por = {}
    for e in ticks:
        por.setdefault(e["roleta"], []).append(float(e["t"]))
    giros = sorted((min(l), max(l), n) for n, l in por.items())
    grupos = []
    for t0, t1, n in giros:
        if grupos and t0 <= grupos[-1]["fim"] + float(cfg.get("junto", 0.05)):
            grupos[-1]["nomes"].append(n)
            grupos[-1]["fim"] = max(grupos[-1]["fim"], t1)
        else:
            grupos.append({"nomes": [n], "ini": t0, "fim": t1})
    rel = sons.origem(cfg["som"])
    if not (sons.som / rel).is_file():
        return []
    parada = cfg.get("parada", "auto")
    if parada == "auto":
        parada = parada_auto(sons.som / rel)
        notas.append(f"roleta: último estalo forte medido em {parada:.3f} s do arquivo")
    parada = float(parada)
    x, _, _ = medir_som(sons.som / rel)
    cortes = sons.som / "sons" / "cortes-roleta"
    if cortes.exists():
        shutil.rmtree(cortes)
    out, soou, sem_principal = [], set(), {}
    for g in grupos:
        nomes, t0, fim = g["nomes"], g["ini"], g["fim"]
        cena = cena_de(t0, janelas)
        vol = next((ajustes[n]["vol"] for n in nomes if "vol" in ajustes.get(n, {})), cfg.get("vol", -2))
        if float(vol) <= -50:
            notas.append(f"roleta {' + '.join(nomes)}: muda (vol {vol})")
            continue
        if cfg.get("so_principal"):
            if not any(ajustes.get(n, {}).get("principal") for n in nomes):
                sem_principal.setdefault(cena, []).extend(nomes)
                continue
            if cena in soou:
                avisos.append(f"cena {cena}: mais de uma roleta principal; {' + '.join(nomes)} ficou muda")
                continue
            soou.add(cena)
        if cfg.get("giro"):  # roda curta: os últimos "giro" s antes do estalo, mais a cauda, com entrada e saída
            giro = min(float(cfg["giro"]), max(0.25, fim - t0))
            cauda = float(cfg.get("cauda", 0.14))
            y = x[int(round((parada - giro) * SR)):int(round((parada + cauda) * SR))].copy()
            k = min(len(y), int(float(cfg.get("entrada", 0.03)) * SR))
            y[:k] *= np.linspace(0, 1, k)[:, None]
            k = min(len(y), int(float(cfg.get("saida", 0.10)) * SR))
            y[len(y) - k:] *= np.linspace(1, 0, k)[:, None]
            nome = f"roda-curta-{int(round(giro * 1000)):04d}.wav"
            cortes.mkdir(parents=True, exist_ok=True)
            if not (cortes / nome).is_file():
                gravar_audio(cortes / nome, y, codec="pcm_s24le")
            out.append({"t": round(max(fim - giro, 0.0), 4), "som": f"sons/cortes-roleta/{nome}", "vol": vol,
                        "motivo": f"roleta {' + '.join(nomes)}: {giro:.2f} s de roda e a trava ({fim:.3f} s)",
                        "cena": cena, "tipo": "roleta", "no": round(fim, 3),
                        "_swoosh": False, "_fixo": True, "_repetir": True, "_evento": f"roleta:{'+'.join(nomes)}"})
            continue
        ts = fim - parada   # onde o som começaria para parar na última trava
        som, t = rel, ts
        if ts < t0:         # giro mais curto que o som: corta o começo, com entrada curta
            ini = t0 - ts
            nome = f"roda-{int(round(ini * 1000)):05d}.wav"
            cortes.mkdir(parents=True, exist_ok=True)
            y = x[int(round(ini * SR)):].copy()
            k = min(len(y), int(float(cfg.get("entrada", 0.04)) * SR))
            y[:k] *= np.linspace(0, 1, k)[:, None]
            gravar_audio(cortes / nome, y, codec="pcm_s24le")
            som, t = f"sons/cortes-roleta/{nome}", t0
        out.append({"t": round(max(t, 0.0), 4), "som": som, "vol": vol,
                    "motivo": f"roleta {' + '.join(nomes)}: a roda gira e para na última trava ({fim:.3f} s)",
                    "cena": cena, "tipo": "roleta", "no": round(fim, 3),
                    "_swoosh": False, "_fixo": True, "_repetir": True, "_evento": f"roleta:{'+'.join(nomes)}"})
    for cena, nomes in sem_principal.items():
        (notas if cena in soou else avisos).append(
            f"cena {cena}: {', '.join(nomes)} giram mudas" + ("" if cena in soou else
            "; nenhuma é principal (marque a do número principal com \"principal\": true)"))
    return out


# ---------------------------------------------------------------------------------------------------------------
# regras de quantidade
# ---------------------------------------------------------------------------------------------------------------
def aplicar_regras(camadas, tipos):
    fora = set()
    # swooshes a 5 s ou mais um do outro: fixos primeiro, depois viradas, golpes e câmeras
    sw = [c for c in camadas if c["_swoosh"]]
    ordem = sorted(sw, key=lambda c: (0 if c["_fixo"] else PRIORIDADE.get(c["tipo"], 4), c["no"]))
    aceitos = []
    for c in ordem:
        perto = [a for a in aceitos if abs(a["no"] - c["no"]) < SWOOSH_MIN]
        if perto and not c["_fixo"]:
            fora.add(id(c))
            notas.append(f"saiu swoosh do {c['tipo']} em {c['no']:.2f} s ({c['cena']}): a {abs(perto[0]['no'] - c['no']):.1f} s "
                         f"do {perto[0]['tipo']} de {perto[0]['no']:.2f} s")
        else:
            if perto:
                avisos.append(f"swoosh fixo em {c['no']:.2f} s a menos de {SWOOSH_MIN:.0f} s de outro ({perto[0]['no']:.2f} s)")
            aceitos.append(c)
    # máximo por tipo (a câmera tem 3): ficam os primeiros
    for tipo, spec in tipos.items():
        if "max" not in spec:
            continue
        evs = sorted({c["_evento"]: c for c in camadas if c["tipo"] == tipo and id(c) not in fora}.values(),
                     key=lambda c: c["no"])
        for c in [c for c in evs if not c["_fixo"]][int(spec["max"]):]:
            for d in camadas:
                if d["_evento"] == c["_evento"]:
                    fora.add(id(d))
            notas.append(f"saiu {tipo} em {c['no']:.2f} s ({c['cena']}): passa do máximo de {spec['max']}")
    # o mesmo arquivo a menos de 2 s do anterior sai
    ultimo = {}
    for c in sorted(camadas, key=lambda c: (c["no"], c["t"])):
        if id(c) in fora:
            continue
        s = c["som"]
        if s in ultimo and c["no"] - ultimo[s] < REPETE_MIN and not (c["_repetir"] or c["_fixo"]):
            fora.add(id(c))
            notas.append(f"saiu {c['tipo']} em {c['no']:.2f} s ({c['cena']}): {Path(s).name} repetia a "
                         f"{c['no'] - ultimo[s]:.1f} s")
            continue
        ultimo[s] = c["no"]
    return [c for c in camadas if id(c) not in fora]


# ---------------------------------------------------------------------------------------------------------------
# conferência: soma a camada de efeitos como o mixar.py e mede o pico
# ---------------------------------------------------------------------------------------------------------------
def somar(efs, som, sem_trilha):
    fim = max(float(e["t"]) + len(medir_som(som / e["som"])[0]) / SR for e in efs) + 0.1
    cam = np.zeros((int(fim * SR) + 1, 2), dtype=np.float32)
    for e in efs:
        if sem_trilha and e.get("so_com_trilha"):
            continue
        x, pico, _ = medir_som(som / e["som"])
        if e.get("dur"):
            x = x[: int(float(e["dur"]) * SR)].copy()
            k = min(len(x), int(0.012 * SR))
            x[-k:] *= np.linspace(1, 0, k)[:, None]
        p0 = int(round(float(e["t"]) * SR))
        cam[p0:p0 + len(x)] += x * (10 ** ((PICO_EFEITO + float(e["vol"])) / 20) / pico)
    return cam


def conferir(efs, som):
    ok = True
    for sem in (False, True):
        cam = somar(efs, som, sem)
        m = np.abs(cam).max(1)
        pk = 20 * np.log10(m.max() + 1e-12)
        j = int(0.1 * SR)
        k = len(m) // j
        jan = 20 * np.log10(m[:k * j].reshape(k, j).max(1) + 1e-12)
        altos = [(i * 0.1, v) for i, v in enumerate(jan) if v > TETO]
        rotulo = "sem trilha" if sem else "com trilha"
        print(f"Pico da soma dos efeitos ({rotulo}): {pk:.1f} dBFS (teto {TETO:.0f})"
              + ("" if not altos else " · acima do teto em " + ", ".join(f"{t:.1f} s ({v:.1f})" for t, v in altos[:8])))
        ok &= not altos
    soltas = sorted(efs, key=lambda e: e["t"])
    for i, e in enumerate(soltas):
        juntas = [f for f in soltas[i:] if f["t"] - e["t"] < 0.15]
        if len(juntas) > 4:
            print(f"  amontoado: {len(juntas)} camadas começam entre {e['t']:.2f} e {e['t'] + 0.15:.2f} s")
            ok = False
    return ok


# ---------------------------------------------------------------------------------------------------------------
def main():
    utf8()
    ajuda(__doc__)
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        sair(__doc__)
    checar_ffmpeg()
    checar_node()
    peca = Path(args[0]).expanduser().resolve()
    som, motion = peca / "sequencia" / "som", peca / "sequencia" / "motion"
    if not som.is_dir():
        sair(f"Não achei {som}. Passe a pasta da peça (a que tem sequencia/som/ e sequencia/motion/).")
    pp = som / "paleta.json"
    paleta = ler_json(pp if pp.is_file() else AQUI / "paleta.json")
    print(f"Paleta: {'sequencia/som/paleta.json' if pp.is_file() else 'a inicial da skill (scripts/paleta.json)'}")
    tipos = paleta["tipos"]
    sons = Sons(som, paleta)
    janelas = janelas_das_cenas(motion)

    eventos, ajustes, faltas = ler_eventos(som)
    codigo = [float(e["t"]) for e in eventos if "t_real" not in e]
    reais = iter(tempo_real(motion, codigo))
    for e in eventos:
        t = float(e["t_real"]) if "t_real" in e else next(reais)
        e["no"] = t + float(e.get("desloc", 0))
    escolher_variacoes(eventos, tipos)
    camadas = []
    for e in sorted(eventos, key=lambda e: e["no"]):
        camadas += expandir(e, tipos, sons)
    ticks = ticks_das_roletas(motion)
    if ticks and paleta.get("roleta"):
        camadas += roletas(ticks, ajustes, paleta["roleta"], sons, janelas)

    if sons.faltando:
        print("Faltam estes sons em sequencia/som/ (baixe do Epidemic pelo ID, com o sons.py --baixar):")
        for rel, info in sorted(sons.faltando.items()):
            print(f"  {rel}  ·  «{info.get('titulo', '?')}»  ·  ID {info.get('id', '?')}")
        sys.exit(1)

    antes = len({c["_evento"] for c in camadas})
    camadas = aplicar_regras(camadas, tipos)
    efs = sorted(camadas, key=lambda c: (c["t"], c["som"]))
    mao = {c["_evento"] for c in efs if c["tipo"] != "roleta"}
    limpos = [{k: v for k, v in c.items() if not k.startswith("_")} for c in efs]
    gravar_json(som / "efeitos.json", limpos)

    conta = {}
    for c in efs:
        conta.setdefault(c["cena"], {}).setdefault(c["tipo"], set()).add(c["_evento"])
    dur = duracao_do_video(motion) or (max(c["no"] for c in efs) if efs else 0)
    ficaram = len({c["_evento"] for c in efs})
    print(f"efeitos.json: {len(efs)} camadas · {ficaram} efeitos ({len(mao)} à mão) · {antes - ficaram} saíram pelas regras")
    for cena, ts in conta.items():
        print(f"  {cena}: " + " · ".join(f"{t} {len(n)}" for t, n in sorted(ts.items())))
    for n in notas:
        print("  " + n)
    for a in avisos:
        print("  aviso: " + a)
    if dur >= 30 and len(mao) / dur * 90 > POR_90S:   # régua do vídeo inteiro; o gancho sozinho é mais denso
        print(f"  aviso: {len(mao)} efeitos à mão em {dur:.0f} s passam de {POR_90S} a cada 90 s: corte os de menos motivo")
    ok = True
    for f in faltas:
        print("  SEM MOTIVO: " + f)
        ok = False
    if efs and "--sem-conferir" not in args:
        ok &= conferir(limpos, som)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
