# Scripts da novela

Passos mecânicos do episódio: um comando cada, sem agente, sem pergunta. Todos se acham pela posição do próprio
arquivo (a pasta `scripts/` desta skill) e nada procura outra skill. `<ep>` é a pasta do episódio
(`<pasta da série>/ep02`). `--help` em todos, sem instalar nada. Os comandos usam `python3`; **no Windows, troque por
`python`** (o resto é igual).

- Os que têm o cabeçalho `# /// script` com dependências rodam com `uv run "<pasta desta skill>/scripts/<script>"`: o
  uv instala numpy, scipy, librosa e o Whisper sozinho na primeira vez, num ambiente isolado.
- Os outros rodam com `python3` (3.9 ou mais novo, só biblioteca padrão) e chamam `ffmpeg`, `node` e, por baixo, o
  `pausa.py` e o `ancorar.py` pelo uv.
- No Windows, os mesmos comandos, com todo caminho entre aspas. O Whisper usa o mlx-whisper em Mac com chip M e o faster-whisper no resto; `WHISPER_MOTOR=faster-whisper` força o
  segundo.

## Da novela (python3)

| Script | O que faz | Comando |
|---|---|---|
| `encaixar_aula.py` | abre a pausa no fim do bloco com `aula_depois`, iguala o volume da voz de quem vende ao da narração, soma a aula e grava `aula-janela.json` | `python3 encaixar_aula.py <ep> --aula aula/<trecho>.wav --tempos aula/<trecho>.json` |
| `montar_projeto.py` | monta `sequencia/motion/`: esqueleto, componentes, mola, a GSAP 3.14.2 (baixada do pacote oficial: precisa de internet), narração, janelas dos atos, atos vazios, barra, legenda, o tempo do `<video data-aula>` e a `_regua.md` | `python3 montar_projeto.py <ep> --componentes <pasta da série>/componentes` |
| `segunda_voz.py` | a mesma animação com outro narrador: cria a pasta da outra voz com a cópia do roteiro (`--preparar --voz <voice_id>`), e depois cópia do projeto, ancoragem, janelas, legenda e o tempo do vídeo da aula | `python3 segunda_voz.py <ep> <ep-da-outra-voz>` |
| `entregar.py` | check, render, medidas (1080×1920, duração da narração) e folha de contato | `python3 entregar.py <ep> --rascunho` (ou sem flag, para a entrega) |

`_novela.py` e `_montagem.py` são a biblioteca dos quatro. O esqueleto que o `montar_projeto.py` copia está em
`../modelos/motion/`; a biblioteca de componentes, em `../modelos/componentes/` (ou `--componentes <pasta>`, a cópia
com a pele da série).

## Voz e som (uv run)

| Script | O que faz | Detalhe |
|---|---|---|
| `narrar.py` | narradores, amostras, takes do roteiro inteiro, conferência pelo Whisper, montagem e alinhamento forçado | `../referencias/voz.md` |
| `pausa.py` | põe um silêncio na narração aprovada e soma a duração aos tempos depois dele | `voz.md`, «Segurar a tela» |
| `ancorar.py` | reescreve as âncoras do `assets/voz.js` quando a narração muda depois das cenas | `voz.md`, «Narração mudou depois das cenas» |
| `montar_trilha.py` | corta a música no compasso, pela `planta.json` (`--grade` lista os compassos) | `../referencias/som.md`, «Editar no compasso» |
| `sons.py` | lista os sons de uma pasta ou baixa um som por link | `som.md`, «Sons prontos» |
| `efeitos.py` | monta o `efeitos.json` dos eventos dos atos e das roletas, com as regras de quantidade | `som.md`, «Quantidade»; a paleta em `paleta.json` |
| `variar.py` | dá tom e volume levemente diferentes ao som que se repete | `som.md`, «Quantidade» |
| `mixar.py` | a mix: voz na frente, trilha nivelada (com `trilha.fora` na janela da aula), efeitos, −14 LUFS | `som.md`, «Mixagem» |
| `medir.py` · `ganho_voz.py` · `ouvir.py` | trilha contra a voz · variação do ganho da voz · inteligibilidade da fala | `som.md`, «Medidas» |
| `custo_sessao.py` | custo de uma sessão do Claude Code por área e por agente (roda com `python3`) | `../referencias/orquestracao.md`, «Custo por área» |

`comum.py` é a biblioteca dos scripts de voz e som.

## Ordem num episódio novo

1. Roteiro aprovado (portão 2) com os campos de `../modelos/roteiro-episodio.md`, «Campos para montar o projeto»:
   `ato`, `legenda.chave`, `legenda.fora`, `barra`.
2. Narração (`narrar.py narrar`, `conferir`, `alinhar`) em `<ep>/brutos/narracao/`.
3. `encaixar_aula.py` (se o episódio tem aula). Ele deixa `aula-janela.json`; ouça o encaixe uma vez.
4. `montar_projeto.py <ep>`: projeto pronto, atos vazios, com o HyperFrames travado em 0.9.26 pelo `npx` dos comandos.
   Agentes de ato preenchem só os `atoN.html` (passo 7).
5. `entregar.py <ep> --rascunho` a cada passada de direção; o de entrega, uma vez por versão.
6. Som: `montar_trilha.py`, `efeitos.py`, `variar.py`, `mixar.py` e as medidas.
7. Segunda voz: `segunda_voz.py <ep> <ep>-<voz> --preparar --voz <voice_id>` (cria a pasta e a cópia do `roteiro.json`
   com a voz trocada), narre e alinhe em `<ep>-<voz>/brutos/narracao/`, `encaixar_aula.py <ep>-<voz> …` (o `aula_depois`
   vem na cópia; o `--depois <cena>` só a quem não a tem), `segunda_voz.py <ep> <ep>-<voz>`,
   `entregar.py <ep>-<voz> --rascunho`.

Rodar `montar_projeto.py` de novo (roteiro ou narração mudou) reescreve só o gerado e nunca o conteúdo de um `atoN.html`
existente; a única coisa que ele troca num ato é o `data-start`/`data-duration` do `<video data-aula>`, que vem do
`aula-janela.json`.

## Confiança

- `encaixar_aula.py`, `montar_projeto.py` e `segunda_voz.py`: provados contra um episódio feito à mão, nas duas vozes
  (duração, janelas, ganhos, barra, roletas, `voz.js` e legenda idênticos).
- `entregar.py`: provado num episódio mínimo de 12,7 s, no HyperFrames 0.9.26: o check (0 erros, os dois avisos
  esperados de `componentes/README.md`), o render de rascunho e o de entrega (1080×1920, 12,733 s, igual ao da
  0.9.6) e a folha de contato. A saída do HyperFrames aparece linha a linha enquanto ele roda.
- Os scripts de voz e som vêm de produções anteriores de vídeo narrado por IA, onde passaram nas medidas de `som.md`.
  O `trilha.fora` do `mixar.py` é novo: a curva foi testada e a mix inteira com aula passou num episódio mínimo de 12,7 s
  (`medir.py` dentro da régua, com o respiro final medido pela média do patamar).
