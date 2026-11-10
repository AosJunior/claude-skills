#!/usr/bin/env python3
"""Encaixa o trecho real da aula (o vídeo de quem vende) na narração do episódio (passo 5 do SKILL.md), sem agente.

Uso:
  python3 encaixar_aula.py <epNN> --aula <aula.wav> --tempos <aula.json> [--respiro 0.20] [--depois <cena>]

O que faz, em ordem:
  1. acha o bloco do <epNN>/roteiro.json que tem `aula_depois` e põe o ponto da pausa 0,01 s depois do fim dele
     (em brutos/narracao/narracao-blocos.json);
  2. abre o silêncio de (duração da aula + 2 × respiro) com o pausa.py desta skill, em pedaços de até 5 s
     (o limite dele), todos no mesmo instante;
  3. mede a narração só nos trechos com fala (as palavras do alinhamento concatenadas) e leva cada pedaço da aula
     (os `pedacos` do --tempos) a esse volume integrado, com pico de no máximo −1,5 dBFS;
  4. soma o áudio da aula no silêncio e grava, em <epNN>/brutos/narracao/: narracao.wav, palavras-voz.json
     (deslocado pelo pausa.py) e aula-janela.json (janela, ganhos, picos e as palavras da aula no tempo do vídeo).

Sem `aula_depois` no roteiro (ex.: a segunda voz), passe --depois <cena>.
Pode rodar de novo: se já existirem os `*-antes-da-pausa`, ele os restaura e refaz do zero.
O --tempos é o JSON da aula (<pasta da série>/aula/<trecho>.json), com os tempos em segundos do WAV da aula:
  {"pedacos": [{"id": "A", "inicio_wav_s": 0.0, "fim_wav_s": 6.2,
                "palavras": [{"palavra": "Foto", "inicio": 0.12, "fim": 0.40}, …]}, …]}
O pedaço de id «silencio» é ignorado. Sem `pedacos`, a aula inteira é um pedaço só (com `palavras` na raiz, se houver).
Precisa de ffmpeg, ffprobe e uv (o pausa.py usa numpy).
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _novela as N  # noqa: E402

ALVO_PICO_DBFS = -1.5


def restaurar_originais(narr):
    """Volta ao estado anterior ao encaixe, se o pausa.py já guardou os originais."""
    voltou = False
    for nome in ("narracao.wav", "palavras-voz.json", "narracao-blocos.json"):
        p = narr / nome
        guarda = p.with_name(f"{p.stem}-antes-da-pausa{p.suffix}")
        if guarda.is_file():
            shutil.copy2(guarda, p)
            voltou = True
    return voltou


def bloco_da_aula(ep, depois=None):
    rot = N.ler(ep / "roteiro.json")
    if depois:
        achados = [(i, b) for i, b in enumerate(rot["blocos"]) if b.get("cena") == depois]
        if not achados:
            N.sair(f"o roteiro não tem o bloco «{depois}» (--depois).")
        return achados[0]
    achados = [(i, b) for i, b in enumerate(rot["blocos"]) if b.get("aula_depois")]
    if not achados:
        N.sair(f"nenhum bloco de {ep / 'roteiro.json'} tem `aula_depois`. Marque o bloco que chama a aula "
                "ou passe --depois <cena>.")
    if len(achados) > 1:
        N.sair("mais de um bloco com `aula_depois`: este script encaixa uma aula por episódio.")
    return achados[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ep", help="pasta do episódio (ex.: <pasta da série>/ep01)")
    ap.add_argument("--aula", required=True, help="WAV da aula (só a voz de quem vende)")
    ap.add_argument("--tempos", required=True, help="JSON da aula, com os `pedacos`")
    ap.add_argument("--respiro", type=float, default=0.20, help="silêncio de cada lado da aula, em s (padrão 0,20)")
    ap.add_argument("--depois", help="cena do bloco depois do qual a aula toca (padrão: o bloco com `aula_depois`)")
    a = ap.parse_args()

    ep = N.pasta_ep(a.ep)
    narr = ep / "brutos" / "narracao"
    aula_wav, tempos_json = Path(a.aula).expanduser(), Path(a.tempos).expanduser()
    for p in (aula_wav,):
        if not p.is_file():
            N.sair(f"não achei {p}.")
    for nome in ("narracao.wav", "palavras-voz.json", "narracao-blocos.json"):
        if not (narr / nome).is_file() and not (narr / f"{Path(nome).stem}-antes-da-pausa{Path(nome).suffix}").is_file():
            N.sair(f"falta {narr / nome}. Narre o episódio (passo 5, narrar.py) antes de encaixar a aula.")
    N.exigir("ffmpeg")
    tempos = N.ler(tempos_json)
    pausa = N.AQUI / "pausa.py"
    if not pausa.is_file():
        N.sair(f"não achei {pausa}. A pasta scripts/ da skill reel-novela está incompleta: reinstale a skill.")

    if restaurar_originais(narr):
        print("Encaixe anterior desfeito: voltei aos arquivos `-antes-da-pausa`.")
    idx, bloco_rot = bloco_da_aula(ep, a.depois)
    blocos = N.ler(narr / "narracao-blocos.json")
    palavras = N.ler(narr / "palavras-voz.json")
    cena = bloco_rot.get("cena")
    bl = next((b for b in blocos if b.get("cena") == cena), None)
    if bl is None:
        N.sair(f"o bloco «{cena}» do roteiro não está em narracao-blocos.json. Narre de novo ou confira o nome.")

    # ponto da pausa: 0,01 s depois do fim do bloco; se cair dentro de uma palavra, o meio da pausa mais próxima
    em = round(bl["fim"] + 0.01, 3)
    if any(p["ini"] < em < p["fim"] for p in palavras):
        ants = max((p["fim"] for p in palavras if p["fim"] <= bl["fim"] + 0.001), default=bl["fim"])
        deps = min((p["ini"] for p in palavras if p["ini"] >= ants + 0.001), default=ants + 0.2)
        em = round((ants + deps) / 2, 3)

    # áudio da aula, em 48 kHz mono 16 bits
    tmpd = Path(tempfile.mkdtemp(prefix="novela-aula-"))
    try:
        aula = N.ler_wav(aula_wav, tmp=tmpd / "aula-conv.wav")
        dur_aula = len(aula) / N.SR
        pecas = [p for p in tempos.get("pedacos", []) if p.get("id") != "silencio" and "inicio_wav_s" in p]
        if not pecas:
            pecas = [{"id": "A", "inicio_wav_s": 0.0, "fim_wav_s": dur_aula, "palavras": tempos.get("palavras", [])}]
        # referência: a narração só nos trechos com fala, antes de abrir a pausa
        narra = N.ler_wav(narr / "narracao.wav", tmp=tmpd / "narr-conv.wav")
        fala = N.array.array("h")
        for p in palavras:
            fala.extend(narra[int(round(p["ini"] * N.SR)):int(round(p["fim"] * N.SR))])
        ref = round(N.lufs(fala, tmpd / "fala.wav"), 1)

        total = round(dur_aula + 2 * a.respiro, 3)
        resta, n = total, 0
        while resta > 1e-6:
            s = round(min(5.0, resta), 3)
            N.uv_run(pausa, [str(ep), "--em", f"{em:.3f}", "--s", f"{s:.3f}"])
            resta = round(resta - s, 3)
            n += 1
        aula_ini = round(em + a.respiro, 3)

        nar = N.ler_wav(narr / "narracao.wav", tmp=tmpd / "narr2.wav")
        saida = N.array.array("h", nar)
        # a pausa zerou o trecho; a aula entra por soma
        pedacos, palavras_aula = {}, []
        for p in pecas:
            i0, i1 = int(round(p["inicio_wav_s"] * N.SR)), int(round(p["fim_wav_s"] * N.SR))
            seg = aula[i0:i1]
            antes = round(N.lufs(seg, tmpd / "seg.wav"), 1)
            pico_antes = N.pico_dbfs(seg)
            g = round(ref - antes, 1)
            limitado = False
            if pico_antes + g > ALVO_PICO_DBFS:
                g = round(ALVO_PICO_DBFS - pico_antes - 0.05, 1)
                limitado = True
            seg_g = N.ganho(seg, g)
            ini_s = int(round(aula_ini * N.SR)) + i0
            for k, x in enumerate(seg_g):
                v = saida[ini_s + k] + x
                saida[ini_s + k] = 32767 if v > 32767 else (-32768 if v < -32768 else v)
            pedacos[p["id"]] = {
                "ganho_db": g, "lufs_antes": antes, "lufs_depois": round(antes + g, 1),
                "pico_amostra_dbfs": round(N.pico_dbfs(seg_g), 2), "limitador": False,
                "ini": round(aula_ini + p["inicio_wav_s"], 2), "fim": round(aula_ini + p["fim_wav_s"], 2),
            }
            if limitado:
                pedacos[p["id"]]["ganho_limitado_pelo_pico"] = True
            for w in p.get("palavras", []):
                palavras_aula.append({"w": w.get("palavra", w.get("w")), "ini": round(aula_ini + w["inicio"], 2),
                                      "fim": round(aula_ini + w["fim"], 2), "pedaco": p["id"]})
        N.gravar_wav(narr / "narracao.wav", saida)
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)

    janela = {
        "silencio_ini": em, "silencio_fim": round(em + total, 2), "aula_ini": aula_ini,
        "aula_fim": round(aula_ini + dur_aula, 2), "respiro_s": a.respiro, "deslocamento_s": aula_ini,
        "referencia_lufs_fala_narracao": ref, "pedacos": pedacos, "palavras": palavras_aula,
        "nota": "Tempos da aula = tempo do wav da aula + deslocamento. Palavras da aula: Whisper, erro típico ~0,1 s. "
                "Gerado por encaixar_aula.py.",
    }
    N.gravar(narr / "aula-janela.json", janela)
    dur = N.duracao_de(narr / "narracao.wav")
    print(f"Aula encaixada depois do bloco «{cena}»: silêncio {em:.2f}–{janela['silencio_fim']:.2f} s, aula "
          f"{aula_ini:.2f}–{janela['aula_fim']:.2f} s.")
    print(f"Referência da fala do narrador: {ref} LUFS. " + " · ".join(
        f"pedaço {k}: {v['ganho_db']:+.1f} dB ({v['lufs_antes']} → {v['lufs_depois']} LUFS, pico {v['pico_amostra_dbfs']} dBFS)"
        for k, v in pedacos.items()))
    print(f"narracao.wav agora com {dur:.2f} s. Próximo passo: montar_projeto.py {a.ep}")


if __name__ == "__main__":
    main()
