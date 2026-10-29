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

**Áudio em alta**: Reel de quem quer alcance pode usar o áudio em alta, que o público reconhece em 2 s. Ele só entra
se combinar com o clima e a mensagem do vídeo (passo 1): áudio em alta que não conversa com o conteúdo perde para um
que conversa. Com o link do áudio no Instagram (`instagram.com/reels/audio/<id>`) ou Reels que o usam, reconheça a
faixa com o `identificar.py` e ponha a música no **trecho que esses Reels usam**, e não no refrão achado por análise:
muitas vezes é o começo (`"inicio": 0`). Uma API do Instagram (por exemplo, a ScrapeCreators,
`/v1/instagram/audio/reels`) dá esse trecho no campo `audio_asset_start_time_in_ms`. Ela também acha o áudio em alta
do nicho: as músicas com mais plays nos Reels dos últimos 14 dias dos maiores perfis. Comece a até 0,5 s do trecho
do trend, com a batida forte na ação do vídeo.

Música comercial no arquivo pode deixar o Reel mudo. Avise e entregue também a versão só com os efeitos, sem a
trilha: o áudio entra pelo Instagram na hora de postar. Com a primeira trilha reprovada, peça referência em vez de
trocar às cegas de novo.

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
Efeito com nome comum (roleta, caça-níquel, máquina de escrever, aplauso) tem som pronto no Epidemic: use como está,
só cortado no tamanho do evento. Som montado de pedaços soa artificial e foi reprovado. Se o nome popular não
aparecer na busca ("ba dum tss", "film clicker"), busque pelo som (bateria com prato, obturador de câmera de
filme). Montar com 2 ou 3 sons da mesma fonte, cada um nos créditos, só vale quando o som pronto não existe.

**Roleta** (número que gira na tela até travar): a roda soa só no número principal do vídeo, ou no de cada bloco,
nunca em todo número; datas, números de apoio e o CTA giram mudos. A roda é curta: o último meio segundo dela, que
termina no estalo da trava, e um fim curto que some. A roda em todo número foi «demais»; só no principal, a de 2 s
ainda pediu «mais curto, enxuto, rápido e direto». Com a roda do Epidemic «Mechanical, Roller, Wheel Spin, Wheel Of Fortune Style 01»
(ID 97caed1c-c294-44b7-924a-e39906605838), o último estalo forte fica em 14,096 s. Corte uma vez:

```
ffmpeg -ss 13.546 -t 0.69 -i roda.wav -af "afade=t=in:d=0.03,afade=t=out:st=0.59:d=0.10" som/sons/roda-curta.wav
```

No `som.json`, o efeito vai na âncora em que o número trava, com `"desvio": -0.55`, para o estalo cair na trava.
Com outra roda, ache o último estalo forte de ouvido e troque o `13.546` por ele menos 0,55.

Régua:

- **Poucos**: um por evento e nunca dois a menos de 5 s. Sem receita de formato, também: em média um a cada 15 s
  ou mais e nenhum no primeiro segundo do gancho. Com receita de formato (a skill do formato gravada pela
  `/minha-edicao`, ou o `marca/estilo.md`), a receita manda. Exemplo aprovado: o zoom seco com efeito dentro do
  gancho dividido.
- **Preso ao evento, não ao relógio**: camada que entra vai com `"camada"` (o id no `insercoes.json`); zoom seco,
  com `"camada"` e `"em": "recorte"`; cartão, com `"insercao"`; virada e piada, com `"em"` numa âncora da fala
  (`"F36:Isso"`) ou `"legenda"`. Se o vídeo for cortado de novo, o efeito acompanha. `"t"` só para evento sem fala
  nem camada.
- **Swoosh só nas viradas.** Se ela pedir mais efeitos, dois swooshes continuam a 5 s ou mais um do outro, e o
  mesmo som nunca volta a menos de 2 s.
- **Mesmo som para o mesmo tipo de evento** no vídeo todo (um para virada de bloco, um para número na tela). Som
  curto e agudo que volta várias vezes (clique, plin) vai em 2 ou 3 variações dele, alternadas: repetido igual, cansa.
- **Volume** de 0 a +5: de -6 a -12, os efeitos foram achados baixos demais. O efeito-chave, como uma explosão, vai
  a +5; o efeito em cima da fala, a 0.
- Só efeito real, do Epidemic ou da pasta dela, nunca som sintetizado.

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

**Voz**: só passa-altas e compressor suave, como o script faz. Redutor de ruído (`afftdn`), EQ forte e compressor
3:1 sobem o ruído e foram reprovados. **Mudanças em lote**: junte todos os ajustes, mixe uma vez e confira os dois
pedaços do passo 6; não mixe a cada ajuste.

```
uv run "<pasta desta skill>/scripts/sonorizar.py" "<pasta do vídeo>/som/som.json"
```

Para ouvir só um pedaço antes do vídeo inteiro: `--trecho 00:30 00:50` (grava `previa-trecho.mp4`).

Pronto quando ele imprime "Pronto", o volume final fica a até 1 LU de -14 e "Trilha embaixo da fala" dá 20 ou
mais. Abaixo de 20, suba `abaixo_da_voz` em 4 em todas as faixas e rode de novo. A régua da trilha é essa medida,
e não o `ouvir.py` do passo 6: ele já deu 100 % numa mistura em que a pessoa não entendia a fala, com a trilha a
15,5 abaixo dela.

## 6. Conferir a fala

Escolha 2 pedaços de uns 20 s: o que tem efeito em cima da fala e o de trilha mais cheia. Comece e termine cada
pedaço numa pausa da fala, entre duas frases da legenda: janela que corta uma palavra dá falso negativo. Para cada
um:

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

Correções que ela pode pedir: "música mais baixa" (`abaixo_da_voz` + 4), "mais alta" (− 4, nunca abaixo de 12; a
medida do passo 5 continua em 20 ou mais),
"tira o efeito do 00:42" (apague a linha), "a música começa em outro ponto" (`inicio`), "troca a música" (volte
ao passo 2). Depois de cada uma, rode o passo 5.

## Fala baixa

Se o `ouvir.py` ou o ouvido mostrar uma frase de 8 a 10 dB abaixo do resto (a fala virada para o lado, um fim de
frase), suba só aquele trecho na voz antes de mixar, de A a B segundos, com ganho G (2 = o dobro):

```
ffmpeg -i "<vídeo>" -c:v copy -af "volume='1+(G-1)*clip((t-A)/0.06,0,1)*clip((B-t)/0.06,0,1)':eval=frame,alimiter=limit=0.89" "<vídeo>-fala.mp4"
```

Sem o limitador, a voz estoura em 0 dBFS. Depois aponte o `video` do `som.json` para a versão ajustada.

## Limites

- A trilha mais curta que o trecho dela recomeça do início; a emenda pode aparecer. No Epidemic Sound,
  `EditRecording` gera a versão no tamanho exato.
- A voz recebe só um passa-altas e um compressor suave. Ruído de fundo, eco ou vento ficam como estão.
- O vídeo precisa ter a voz no próprio arquivo; a trilha e os efeitos entram por baixo dela.
- `EditRecording` com `forceDuration` pode acelerar a música (já deu 14 % a mais). Confira o andamento ou corte a
  faixa original com fade.

## Esforço

A mixagem e os efeitos são mecânicos: esforço **low ou medium** (`effort: "low"` nos agentes). A busca do áudio em
alta e o encaixe da batida na ação pedem **high**; a pesquisa na web vai para um agente Sonnet (`model: "sonnet"`).
