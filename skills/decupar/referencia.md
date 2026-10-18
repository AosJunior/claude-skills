# cortes.json: referência completa

O formato é o do contrato do kit (`docs/edicao-contrato.md`, seção 3.1). Um campo que não aparece fica
como no primeiro formato: o mesmo corte e o mesmo render.

```json
{
  "pausa_max": 0.22,
  "bordas": "som",
  "velocidade": 1.2,
  "zoom": {"ancora": [0.5, 0.36], "niveis": [1.0, 1.12, 1.2, 1.3], "alternar_na_pausa": true},
  "cor": {"corrigir": false, "look": {"lut": "marca/cor/look.cube"}},
  "trechos": [
    {"de": "F1", "ate": "F1", "zoom": 1.0, "nota": "pergunta do gancho"},
    {"de": "F3:2", "ate": "F3:fim", "zoom": 1.2, "nota": "tira o 'até' gaguejado"},
    {"de": "03:05,00", "ate": "03:08,10", "exato": true, "zoom": 1.12, "nota": "fica o sorriso"}
  ],
  "ajustes": {"T2.de": 0.04, "T2.ate": -0.03}
}
```

## Trechos

- A ordem da lista é a ordem do vídeo final. `T5` é o 5º trecho da lista (contando de 1).
- Fica a palavra cujo meio cai dentro do trecho. As pausas maiores que `pausa_max` saem sozinhas
  (entre palavras e as medidas no som, deixando um respiro curto), e também os sons sem palavra de
  0,15 s ou mais dentro da frase.
- `"exato": true` usa `de` e `ate` como estão, sem ajustar às palavras nem tirar pausas. Serve para
  gesto, sorriso ou respiro que precisa ficar.
- `"zoom"` (opcional): o nível do trecho, de 1.0 (sem zoom) a 3.0. Veja "Zoom".
- `"nota"`: o porquê, para a `decupagem.md` e o `--resumo`.

## Tempos de `de` e `ate` (sempre do vídeo bruto)

| Forma | Exemplo | No `de` | No `ate` |
|---|---|---|---|
| frase | `"F12"` | início da frase | fim da frase |
| frase:borda | `"F12:inicio"`, `"F12:fim"` | essa borda | essa borda |
| frase:índice | `"F12:3"` | início da 3ª palavra | fim da 3ª palavra |
| frase:palavra | `"F12:loja"`, `"F12:loja#2"` | início da 1ª (2ª) "loja" | fim dela |
| deslocamento | `"F12:fim+0.2"`, `"F12:loja-0.1"` | a âncora mais ou menos segundos | idem |
| relógio | `"01:47,30"` | o tempo da transcrição | idem |
| segundos | `107.3` | idem | idem |

- `F<n>` é o número da frase na `transcricao.txt`. As palavras contam de 1 dentro da frase (só as com
  texto), e a comparação ignora acento, caixa e pontuação ("Vocês," = "voces"). Número falado vai com
  `#`: a palavra "10" é `"F81:10#1"` (`"F81:10"` é a 10ª palavra).
- Âncora de palavra (posição, texto, `inicio`, `fim`) sem deslocamento também limita o trecho pela
  posição da palavra, para a vizinha colada não entrar. Com deslocamento, vale só o tempo.
- Âncora que não existe para o script e diz qual: frase que não existe, palavra que não está na
  frase, índice maior que a frase. As regras são as do contrato (seção 2), no `scripts/contrato.py`,
  igual nas 4 skills; `"F12:emenda"` só existe no vídeo cortado.

## Bordas

- `"bordas": "som"`: a borda de cada pedaço de fala sai do volume medido no próprio vídeo (é voz o que
  passa 14 dB acima do ruído de fundo), com folga de 0,035 s antes e 0,07 s depois, sem encostar na
  palavra vizinha. Pega o fim da palavra que o Whisper encurta antes de uma pausa ("produ-tos").
- Sem `bordas` (ou `"palavra"`): a borda é o tempo da palavra do Whisper mais uma folga fixa
  (0,10 s antes e 0,18 s depois).
- `ajustes`: deslocamento fino em segundos da borda de um trecho (`"T5.de": 0.04` começa 40 ms
  depois; `"T5.ate": -0.03` termina 30 ms antes), de -1 a 1. Quem escreve é a `/criticar`, a partir
  do que ela mediu no final.

## Velocidade

`"velocidade": 1.2` acelera vídeo e voz juntos (a voz não fica fina). Vai de 0.5 a 2.0. A legenda,
o `--resumo` e o `palavras-corte.json` já saem no tempo acelerado. O `premiere.xml` sai em 1×.

## Zoom

- `zoom.ancora`: o ponto do quadro de saída que fica parado no zoom, em fração `[x, y]` (0 a 1).
  Ponha perto dos olhos; sem ela, `[0.5, 0.4]`.
- `zoom.niveis`: os níveis que a pessoa usa, por exemplo `[1.0, 1.12, 1.2, 1.3]`.
- `zoom.alternar_na_pausa: true`: cada emenda **dentro** de um trecho (pausa tirada) troca para o
  nível vizinho (o de baixo; no mais baixo, o de cima) e volta na emenda seguinte. A emenda vira um
  corte de câmera, e o pulo de imagem some. Pedaço com menos de 0,4 s não troca (seria um piscar).
- O recorte sai da resolução original do bruto (4K vira 1080 sem perder nitidez até 2×).

## Vertical (só vídeo horizontal)

`"vertical": true` usa o centro achado pelo `enquadrar.py`; `{"centro_x": 0.42}` fixa à mão (fração
da largura, 0 = borda esquerda). O zoom aperta dentro dessa janela 9:16.

## Cor

Veja o passo 2b do SKILL.md. Com `"look": {"lut": ...}` o `.cube` é aplicado depois do recorte e da
escala, com interpolação tetraédrica; `contraste`, `sombra`, `calor` e `saturacao` ficam de fora, e
o script avisa. Um caminho que começa com `marca/` vale a partir da pasta de edição (a que tem
`marca/estilo.md`); outro caminho relativo vale a partir da pasta da decupagem.

## Render

- Sem velocidade e sem zoom, o vídeo sai num render só.
- Com velocidade ou zoom, sai em pedaços: cada um com o número exato de quadros e de amostras de som
  (assim a boca não sai da fala no fim do vídeo), sem perda de qualidade, feitos em paralelo e
  guardados em `.dados/pedacos-previa/` e `.dados/pedacos-final/` pelo conteúdo. Uma correção refaz
  só os pedaços que mudaram. As pastas guardam só os pedaços do último corte e podem ser apagadas.

## palavras-corte.json

Gravado em toda rodada do `cortar.py` (também no `--resumo`), no formato do contrato (seção 3.2): cada
palavra e cada frase que ficou, as bordas de cada trecho (`trechos`) e as trocas de pedaço (`emendas`),
no tempo do vídeo cortado e acelerado. É o que a `/inserir`, a `/sonorizar` e a `/criticar` leem para
achar "F15:repente" no vídeo final.

Depois do render, as bordas são **medidas** no que saiu (quadros contados em cada pedaço e na saída) e
todo tempo do arquivo segue a medida (`"medido": "pedacos"` ou `"saida"`; a medida fica em
`.dados/medida-<vídeo>.json`). O `--resumo` grava as bordas previstas (`"medido": false`), ou reaproveita
a medida do último render quando o corte é o mesmo.
