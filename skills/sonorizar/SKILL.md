---
name: sonorizar
description: Trilha e efeitos sonoros para vídeo falado (Reels). Lê a legenda, propõe o clima da trilha e poucos efeitos com motivo, mixa com a voz na frente e entrega o vídeo em -14 LUFS com os créditos de cada som. Use quando a pessoa mandar /sonorizar ou pedir música, trilha, efeito sonoro ou mixagem de um vídeo.
---

# /sonorizar

A pessoa traz um vídeo já cortado em que ela fala para a câmera (saída da `/decupar`, da `/inserir` ou de outra
edição) e a legenda `.srt` dele. Você lê a fala, escolhe a trilha e os efeitos, confirma uma vez e entrega o vídeo
com som.
Quem usa é leigo, no Claude Desktop, no Mac ou no Windows. Tudo em português.

A **voz manda**: a trilha combina com o sentimento do vídeo, fica bem abaixo da fala e abaixa sozinha quando a
pessoa fala. Efeito sonoro é **pontuação**: só onde algo acontece, cada um com o seu motivo.

O vídeo só é lido. Todo arquivo novo nasce em `<pasta do vídeo>/som/` (o `som.json`, os sons baixados em
`som/sons/`, o vídeo com som e o `creditos.md`). Os scripts ficam em `<pasta desta skill>/scripts/`.

## Conversa

Frases curtas, sem termo técnico: "a música abaixa quando você fala", "efeito", "volume de publicação". Antes do
que demora, diga quanto leva: mixar leva uns 5 s por minuto de vídeo; conferir a fala, uns 30 s por pedaço (na
primeira vez sem a `/decupar` no computador, 5 a 15 min para instalar o Whisper).

A única pergunta do fluxo é a confirmação do mapa de sons (passo 4). O resto você executa.

## 0. Conferir o ambiente

```
ffmpeg -version
uv --version
```

Se um faltar, diga em uma linha o que falta e ofereça instalar; instale só depois do sim. Mac:
`brew install ffmpeg uv`. Windows: `winget install Gyan.FFmpeg astral-sh.uv` e depois a pessoa fecha e abre o
Claude. Pronto quando os dois respondem com a versão.

## 1. Ler o vídeo

Pegue o caminho do vídeo e da legenda (a `/decupar` grava a `legenda.srt` na pasta `decupagem/`). Sem legenda,
rode a `/decupar` antes ou peça o `.srt` do editor dela. Leia a legenda inteira e escreva para você:

- **Clima**: o sentimento do vídeo numa frase (curioso, inspirador, sério, divertido) e a trilha que combina:
  ritmo (lento, médio, animado), instrumento, sem voz cantada.
- **Eventos**: os momentos em que algo acontece, com o tempo da legenda. Valem: **corte de bloco** (o assunto
  vira: "só que", "isso porque", "agora"), **inserção que entra** (número, lista, print, marca citada), **piada**
  (a frase de efeito e o respiro depois dela). Se a `/inserir` já rodou, leia também o `insercoes.json` dela: cada
  cartão é uma inserção que entra, no `de` dele.

Pronto quando cada efeito candidato tem um tempo e um motivo de uma linha.

## 2. Achar os sons

Pergunte de onde vêm, nesta ordem, e use o primeiro que existir:

1. **Pasta da pessoa** (trilhas e efeitos que ela já usa): `uv run "<pasta desta skill>/scripts/sons.py" "<pasta>"`
   lista trilhas e efeitos com duração. Pergunte uma vez de onde vieram e com que direito (comprou, assinatura,
   biblioteca grátis) e anote como licença.
2. **Epidemic Sound**, se o conector estiver nesta sessão: trilha com `SearchRecordings` (filtro `vocals: false`,
   faixa de bpm do clima), efeito com `SearchSoundEffects`, e baixe com `DownloadRecording` /
   `DownloadSoundEffect` (WAV). O link vale minutos: baixe na hora com
   `uv run "<pasta desta skill>/scripts/sons.py" --baixar "<link>" "<pasta do vídeo>/som/sons/<nome>.wav"`.
   Licença: "Epidemic Sound, assinatura da conta conectada", com título, autor e ID.
3. **Nenhum dos dois**: indique a Biblioteca de áudio do YouTube (grátis, no YouTube Studio) ou o Pixabay Music
   (grátis); ela baixa numa pasta e você volta ao item 1. Se for usar a música do próprio Instagram ao postar,
   pule a trilha e faça só os efeitos.

Efeito com nome popular ("ba dum tss", "film clicker") pode não existir com esse nome. Busque pelo som (bateria
com prato, obturador de câmera de filme) e, se precisar, monte com 2 ou 3 sons da mesma fonte, cada um nos créditos.

Trilha de pasta sem informação: escute 60 s do meio dela com o `ouvir.py` (passo 6, sem `--base`). Se sair frase
com sentido, tem voz cantada: troque.

Pronto quando a trilha e cada efeito têm arquivo e licença.

## 3. Mapa de sons

Grave `<pasta do vídeo>/som/som.json` (formato abaixo) e confira:

```
uv run "<pasta desta skill>/scripts/sonorizar.py" "<pasta do vídeo>/som/som.json" --resumo
```

Régua dos efeitos:

- **Poucos**: um por evento, em média um a cada 15 s ou mais, nunca dois a menos de 5 s, e nenhum no
  primeiro segundo do gancho.
- **Preso ao evento, não ao relógio**: inserção da `/inserir` vai com `"insercao"` (o texto do cartão); virada e
  piada vão com `"legenda"` (o trecho da fala; a piada com `"em": "fim"`). Se o vídeo for cortado de novo, o efeito
  acompanha. `"t"` só para evento sem fala nem inserção.
- **Mesmo som para o mesmo tipo de evento** no vídeo todo (um para virada de bloco, um para número na tela).
- Efeito que cai em cima da fala vai com `"volume": -3`.

Pronto quando o `--resumo` lista tudo sem "ATENÇÃO" e sem pedir correção.

Vídeo cortado de novo depois do mapa (nova versão da `/decupar` ou da `/inserir`): aponte `video`, `legenda` e
`insercoes` para os arquivos novos, rode o `--resumo` e confira que cada efeito caiu no evento certo.

## 4. Confirmar

Mande: o clima em uma frase, a trilha (título e autor), a tabela tempo · efeito · motivo, e uma pergunta só:
"Mixo assim? Se quiser mudar, é só dizer (por exemplo: 'tira o efeito do 00:42', 'música mais baixa')."

## 5. Mixar

```
uv run "<pasta desta skill>/scripts/sonorizar.py" "<pasta do vídeo>/som/som.json"
```

Para ouvir só um pedaço antes do vídeo inteiro: `--trecho 00:30 00:50` (grava `previa-trecho.mp4`).

Pronto quando ele imprime "Pronto", o volume final fica a até 1 LU de -14 e "Trilha embaixo da fala" dá 20 ou
mais. Abaixo de 20, suba `abaixo_da_voz` em 4 e rode de novo.

## 6. Conferir a fala

Escolha 2 pedaços de uns 20 s: o que tem efeito em cima da fala e o de trilha mais cheia. Para cada um:

```
uv run "<pasta desta skill>/scripts/ouvir.py" "<vídeo com som>" --base "<vídeo sem trilha>" --de 00:30 --ate 00:50
```

Pronto quando os dois dão 95 % ou mais. Com menos, suba `abaixo_da_voz` em 4 ou tire o efeito do pedaço, mixe e
confira de novo.

## 7. Entregar

Uma linha por arquivo:

- o vídeo com som (`saida` do `som.json`): pronto para publicar; a imagem é a mesma, sem recompressão.
- `creditos.md`: cada som, de onde veio e a licença, e o motivo de cada efeito. Guarde junto do vídeo.
- `som.json`: o mapa de sons; mudar e rodar de novo refaz a mistura em segundos.

Correções que ela pode pedir: "música mais baixa" (`abaixo_da_voz` + 4), "mais alta" (− 4, nunca abaixo de 12),
"tira o efeito do 00:42" (apague a linha), "a música começa em outro ponto" (`inicio`), "troca a música" (volte
ao passo 2). Depois de cada uma, rode o passo 5.

## som.json

```json
{
  "video": "../decupagem/previa.mp4",
  "saida": "video-com-som.mp4",
  "sons": {
    "trilha": {"arquivo": "sons/aprilmoon.wav", "titulo": "Aprilmoon", "autor": "Autohacker",
               "fonte": "Epidemic Sound", "licenca": "assinatura Epidemic Sound da conta conectada · ID a1bd…"},
    "virada": {"arquivo": "sons/film-clicker.wav", "fonte": "Epidemic Sound", "licenca": "…"}
  },
  "trilha": {"som": "trilha", "inicio": 0, "abaixo_da_voz": 16, "fade_in": 1, "fade_out": 2},
  "legenda": "../decupagem/legenda.srt",
  "insercoes": "../insercoes/insercoes.json",
  "efeitos": [
    {"legenda": "Tem marca que ninguém", "som": "virada", "volume": -3,
     "motivo": "corte de bloco: das lojas fechando para as marcas que vendem"},
    {"insercao": "+100 mil", "som": "clique", "volume": -3, "motivo": "inserção entra: painel +100 mil produtos"},
    {"legenda": "pronto, acabou", "em": "fim", "desvio": -0.1, "som": "piada", "motivo": "fecha a piada"},
    {"t": "00:02,10", "som": "clique", "motivo": "evento sem fala nem inserção"}
  ]
}
```

- Caminhos relativos à pasta do `som.json`. `t` em `"mm:ss,cc"` ou segundos, no tempo do vídeo.
- `legenda`: o efeito cai no início (ou no fim, com `"em": "fim"`) do trecho da fala; acentos e pontuação não
  contam. `insercao`: cai no `de` da inserção do `insercoes.json` que tem esse texto. `desvio` (s) ajusta.
- `abaixo_da_voz`: quantos LU a trilha fica abaixo da voz quando ninguém fala (16 é o padrão). Durante a fala ela
  abaixa mais, sozinha.
- `volume` do efeito: 0 é o padrão (pico em -12 dBFS, abaixo da voz); -3 a -6 para efeito em cima da fala.
- Todo som precisa de `licenca` e todo efeito de `motivo`; sem eles o script não mixa.

## Limites

- A trilha mais curta que o vídeo recomeça do início; a emenda pode aparecer. No Epidemic Sound,
  `EditRecording` gera a versão no tamanho exato do vídeo.
- A voz recebe só um passa-altas e um compressor suave. Ruído de fundo, eco ou vento ficam como estão.
- O vídeo precisa ter a voz no próprio arquivo; a trilha e os efeitos entram por baixo dela.
