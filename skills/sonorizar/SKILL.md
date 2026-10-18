---
name: sonorizar
description: Trilha e efeitos sonoros para vídeo falado (Reels). Lê a fala, acha a trilha no universo da pessoa (os sons dela, as músicas dos Reels dela, o Epidemic Sound), põe poucos efeitos presos aos eventos, mixa com a voz na frente e entrega o vídeo em -14 LUFS com os créditos. Use quando a pessoa mandar /sonorizar ou pedir música, trilha, efeito sonoro ou mixagem de um vídeo.
---

# /sonorizar

A pessoa traz um vídeo já cortado em que ela fala para a câmera (saída da `/decupar`, da `/inserir` ou de outra
edição). Você lê a fala, acha a trilha com ela, põe os efeitos, confirma e entrega o vídeo com som.
Quem usa é leigo, no Claude Desktop, no Mac ou no Windows. Tudo em português.

A **voz manda**: a trilha combina com o sentimento do vídeo, fica bem abaixo da fala e abaixa sozinha quando a
pessoa fala. Efeito sonoro é **pontuação**: só onde algo acontece, cada um com o seu motivo.

O vídeo só é lido. Todo arquivo novo nasce em `<pasta do vídeo>/som/` (o `som.json`, os sons baixados em
`som/sons/`, o vídeo com som e o `creditos.md`), e a entrega vai para `<pasta do vídeo>/entrega/`. Os scripts
ficam em `<pasta desta skill>/scripts/`; o formato completo do `som.json` está em [referencia.md](referencia.md).

**Pasta de edição**: suba da pasta do vídeo até achar `marca/estilo.md` (o `sonorizar.py` imprime
`Marca: <caminho>`). Leia o `estilo.md` antes de começar: ele diz o jeito de usar cada som e, às vezes, o universo
da trilha. Os sons dela moram em `marca/sons/`, com as licenças em `marca/sons/creditos.md`.

## Conversa

Frases curtas, sem termo técnico: "a música abaixa quando você fala", "efeito", "volume de publicação". Antes do
que demora, diga quanto leva: mixar leva de 15 s a 1 min por minuto de vídeo; conferir a fala, uns 30 s por pedaço
(na primeira vez sem a `/decupar` no computador, 5 a 15 min para instalar o Whisper); reconhecer as músicas dos
Reels, uns 40 s por Reel.

Ela decide duas coisas: **a trilha** (passo 2) e **o mapa de sons** (passo 4). O resto você executa.

## 0. Conferir o ambiente

```
ffmpeg -version
uv --version
```

Se um faltar, diga em uma linha o que falta e ofereça instalar; instale só depois do sim. Mac:
`brew install ffmpeg uv`. Windows: `winget install Gyan.FFmpeg astral-sh.uv` e depois a pessoa fecha e abre o
Claude. Pronto quando os dois respondem com a versão.

## 1. Ler o vídeo

Junte o que existe na pasta do vídeo: o vídeo (de `insercoes/` se a `/inserir` rodou, senão de `decupagem/`), a
`decupagem/legenda.srt`, o `decupagem/palavras-corte.json` e o `insercoes/insercoes.json`. Sem legenda, rode a
`/decupar` antes ou peça o `.srt` do editor dela. Leia a fala inteira e escreva para você:

- **Clima**: o sentimento do vídeo numa frase (curioso, inspirador, sério, divertido) e, se ele vira no meio, onde
  vira (a "virada": "isso porque", "só que", "então").
- **Eventos**: os momentos em que algo acontece. Valem: **virada de bloco**, **camada que entra** (cada
  `camadas[]` do `insercoes.json`: lettering, vídeo atrás da pessoa, print), **zoom seco** (o 2º passo do
  `recorte` de uma camada), **cartão** (`insercoes[]`), **piada** (a frase de efeito e o respiro depois dela).

Pronto quando cada efeito candidato tem um evento e um motivo de uma linha.

## 2. Achar a trilha no universo dela

A trilha certa é a que **ela já usaria**. Os itens 1 a 3 dão o universo, nesta ordem (pare no primeiro que
der); as candidatas saem de `marca/sons/` e, faltando, do item 4 ou 5.

1. **`marca/sons/`**: `uv run "<pasta desta skill>/scripts/sons.py" "<marca>/marca/sons"` lista trilhas e
   efeitos com duração e diz quais têm licença no `creditos.md`. Som com licença lá: use sem perguntar de novo.
   Som sem licença: pergunte uma vez de onde veio e com que direito (comprou, assinatura, biblioteca grátis) e
   anote no `marca/sons/creditos.md` (formato em referencia.md).
2. **`marca/estilo.md`**: se ele descreve o universo da trilha (gênero, instrumentos, faixas que ela usa), siga.
3. **Os Reels dela**: sem universo anotado, peça 2 ou 3 Reels dela de que ela gosta (arquivo ou link) e rode
   `uv run --python 3.12 "<pasta desta skill>/scripts/identificar.py" "<reel1>" "<reel2>"`. Ele diz o título, o
   artista, o selo e o trecho em que cada música toca. Música achada num pedaço só pode ser engano: confira. O que
   ele não reconhece, diga que não reconheceu; descreva o universo só com o que foi reconhecido ou ouvido. Com o sim
   dela, anote o universo no `marca/estilo.md` (seção de som) para a próxima vez.
4. **Epidemic Sound**, se o conector estiver nesta sessão. Ele não tem programa de linha de comando: o caminho são
   as ferramentas do conector. Parta de uma faixa que ela já usa:
   - faixa do Epidemic (selo "Epidemic Sound" no `identificar.py`): `SearchRecordings` com `term` "título artista"
     dá o `id`; `SearchSimilarToRecording` com esse `id` traz as parecidas;
   - faixa de fora (selo de gravadora): `SearchExternalReferences` com "título artista" dá o id do Spotify;
     `SearchRecordings` com `query.externalID` traz as parecidas do catálogo;
   - sem faixa de partida: `SearchRecordings` com o clima em `term`, `filter.vocals: false` e a faixa de bpm.
5. **Nenhum dos dois**: indique a Biblioteca de áudio do YouTube (grátis, no YouTube Studio) ou o Pixabay Music
   (grátis); ela baixa numa pasta e você volta ao item 1. Se for usar a música do próprio Instagram ao postar,
   pule a trilha e faça só os efeitos.

**Três candidatas, ela escolhe.** Separe 3 trilhas do universo dela, sem voz cantada. Para cada uma, ponha o
arquivo em `sons` do `som.json` (do Epidemic, a prévia `lqmp3Url` da busca basta:
`uv run "<pasta desta skill>/scripts/sons.py" --baixar "<link>" "<pasta do vídeo>/som/sons/candidata-1.mp3"`) e
grave uma prévia de 15 s no vídeo dela:

```
uv run "<pasta desta skill>/scripts/sonorizar.py" "<pasta do vídeo>/som/som.json" --trecho 0 15 --trilha candidata-1
```

Mande as 3 prévias (`som/previa-candidata-N.mp4`), cada uma com título, artista e o porquê numa linha, e pergunte
qual fica. Vídeo com virada forte pode trocar de trilha nela (ex.: cordas na tensão, jazz depois da virada):
ofereça isso como uma das opções. Depois da escolha, baixe o arquivo inteiro: `DownloadRecording` (`fileType`
WAV, `stemType` FULL) e `sons.py --baixar`; o link vale minutos, baixe na hora.

**Licença do Epidemic Sound**: "Epidemic Sound, assinatura da conta conectada", com título, autor e ID. A
assinatura cobre os canais cadastrados nela: confirme que o perfil onde o vídeo vai ser publicado está liberado
na conta conectada.

Pronto quando a trilha tem arquivo e licença e foi escolhida por ela.

## 3. Achar os efeitos

Mesma ordem de fonte: `marca/sons/` primeiro, depois `SearchSoundEffects` + `DownloadSoundEffect` no Epidemic.
Efeito com nome popular ("ba dum tss", "film clicker") pode não existir com esse nome: busque pelo som (bateria
com prato, obturador de câmera de filme) e, se precisar, monte com 2 ou 3 sons da mesma fonte, cada um nos
créditos.

Régua:

- **Poucos**: um por evento e nunca dois a menos de 5 s. Sem receita de formato, também: em média um a cada 15 s
  ou mais e nenhum no primeiro segundo do gancho. Com receita de formato (a skill do formato gravada pela
  `/minha-edicao`, ou o `marca/estilo.md`), a receita manda. Exemplo aprovado: o zoom seco com efeito dentro do
  gancho dividido.
- **Preso ao evento, não ao relógio**: camada que entra vai com `"camada"` (o id no `insercoes.json`); zoom seco,
  com `"camada"` e `"em": "recorte"`; cartão, com `"insercao"`; virada e piada, com `"em"` numa âncora da fala
  (`"F36:Isso"`) ou `"legenda"`. Se o vídeo for cortado de novo, o efeito acompanha. `"t"` só para evento sem fala
  nem camada.
- **Mesmo som para o mesmo tipo de evento** no vídeo todo (um para virada de bloco, um para número na tela).
- Efeito que cai em cima da fala vai com `"volume": -3`.

Pronto quando cada efeito tem arquivo, licença, evento e motivo.

## 4. Mapa de sons

Grave `<pasta do vídeo>/som/som.json` ([referencia.md](referencia.md)), com a `entrega` (pasta `../entrega` e o
nome do arquivo final que ela vai postar), e confira:

```
uv run "<pasta desta skill>/scripts/sonorizar.py" "<pasta do vídeo>/som/som.json" --resumo
```

Pronto quando o `--resumo` lista tudo sem "ATENÇÃO" e sem pedir correção.

Mande: o clima em uma frase, a trilha (título e autor; com troca, onde troca), a tabela tempo · efeito · motivo, e
uma pergunta só: "Mixo assim? Se quiser mudar, é só dizer (por exemplo: 'tira o efeito do 00:42', 'música mais
baixa')."

## 5. Mixar

```
uv run "<pasta desta skill>/scripts/sonorizar.py" "<pasta do vídeo>/som/som.json"
```

Para ouvir só um pedaço antes do vídeo inteiro: `--trecho 00:30 00:50` (grava `previa-trecho.mp4`).

Pronto quando ele imprime "Pronto", o volume final fica a até 1 LU de -14 e "Trilha embaixo da fala" dá 20 ou
mais. Abaixo de 20, suba `abaixo_da_voz` em 4 em todas as faixas e rode de novo.

## 6. Conferir a fala

Escolha 2 pedaços de uns 20 s: o que tem efeito em cima da fala e o de trilha mais cheia. Para cada um:

```
uv run "<pasta desta skill>/scripts/ouvir.py" "<vídeo com som>" --base "<vídeo sem trilha>" --de 00:30 --ate 00:50
```

Pronto quando os dois dão 95 % ou mais. Com menos, leia as duas transcrições: palavra cortada na borda do pedaço
ou erro do Whisper só no "sem trilha" não contam. Se a trilha cobriu de fato, suba `abaixo_da_voz` em 4 ou tire o
efeito do pedaço, mixe e confira de novo.

## 7. Entregar

O passo 5 já copiou para `entrega/`: o vídeo final com o nome escolhido, a `legenda-curta.srt` da `/inserir`
(se existir), o `creditos.md` e o `som.json`. Diga em uma linha cada um:

- o vídeo: pronto para publicar; a imagem é a mesma, sem recompressão;
- `legenda-curta.srt`: a legenda para colar no post, se ela quiser;
- `creditos.md`: cada som, de onde veio e a licença, e o motivo de cada efeito. Guarde junto do vídeo;
- `som.json`: o mapa de sons; mudar e rodar de novo refaz a mistura.

Se a `/criticar` estiver instalada, chame-a com a pasta do vídeo e mostre o relatório antes de dizer que está pronto.

Correções que ela pode pedir: "música mais baixa" (`abaixo_da_voz` + 4), "mais alta" (− 4, nunca abaixo de 12),
"tira o efeito do 00:42" (apague a linha), "a música começa em outro ponto" (`inicio`), "troca a música" (volte
ao passo 2). Depois de cada uma, rode o passo 5.

## Limites

- A trilha mais curta que o trecho dela recomeça do início; a emenda pode aparecer. No Epidemic Sound,
  `EditRecording` gera a versão no tamanho exato.
- A voz recebe só um passa-altas e um compressor suave. Ruído de fundo, eco ou vento ficam como estão.
- O vídeo precisa ter a voz no próprio arquivo; a trilha e os efeitos entram por baixo dela.
