# som.json: referência

O Claude escreve o `som.json` em `<pasta do vídeo>/som/`. Fonte da verdade do formato entre as skills:
`docs/edicao-contrato.md`, seção 5. Esta página é o detalhe da `/sonorizar`.

```json
{
  "video": "../insercoes/final-insercoes.mp4",
  "saida": "video-com-som.mp4",
  "legenda": "../decupagem/legenda.srt",
  "palavras": "../decupagem/palavras-corte.json",
  "insercoes": "../insercoes/insercoes.json",
  "sons": {
    "cordas": {"arquivo": "marca/sons/trilhas/strings-in-solitude-3.wav"},
    "jazz": {"arquivo": "marca/sons/trilhas/gentlemen.wav"},
    "virada": {"arquivo": "sons/virada-swoosh.wav", "titulo": "Swooshes, Whoosh, Designed, Swoosh, Light",
               "fonte": "Epidemic Sound", "licenca": "assinatura Epidemic Sound da conta conectada · ID c52c…"},
    "kaching": {"arquivo": "marca/sons/efeitos/kaching.wav"}
  },
  "trilha": [
    {"som": "cordas", "de": 0, "abaixo_da_voz": 16, "fade_in": 0.5},
    {"som": "jazz", "de": "F36:Isso", "cruzar": 0.6, "fade_out": 2}
  ],
  "efeitos": [
    {"camada": "placa", "em": "recorte", "som": "zoom", "volume": -3, "motivo": "zoom seco na placa"},
    {"camada": "L2", "som": "kaching", "volume": -4, "motivo": "lettering R$ 18 milhões entra"},
    {"em": "F36:Isso", "som": "virada", "volume": -4, "motivo": "virada de bloco: \"Isso porque...\""},
    {"insercao": "+100 mil", "som": "clique", "volume": -3, "motivo": "cartão +100 mil entra"},
    {"legenda": "pronto, acabou", "em": "fim", "desvio": -0.1, "som": "piada", "motivo": "fecha a piada"},
    {"t": "00:02,10", "som": "clique", "motivo": "evento sem fala nem camada"}
  ],
  "entrega": {"pasta": "../entrega", "nome": "ter-loja-virou-coisa-de-pobre"}
}
```

## Caminhos

- Começa com `marca/`: vale a partir da pasta de edição (a que tem `marca/estilo.md`, achada subindo do `som.json`).
- Outros relativos: a partir da pasta do `som.json`.
- `palavras`: sem ele, o script usa `../decupagem/palavras-corte.json` se existir. O `--resumo` diz qual usou.

## Tempos

Todo tempo (`de`, `ate`, `em`, `t`) aceita segundos, `"mm:ss,cc"` ou uma âncora na fala (contrato, seção 2):
`"F36"`, `"F36:fim"`, `"F36:Isso"`, `"F36:Isso#2"`, `"F36:3"`, `"F36:emenda"`, `"F1:fim+0.25"`. As âncoras pedem
o `palavras-corte.json`. Em `ate`, `"F36"` e `"F36:Isso"` valem o **fim** da frase ou da palavra. Âncora numa
palavra que o corte tirou para o script com a palavra que sumiu. Tempo a menos de 3 quadros de uma emenda vale a
emenda, como na `/inserir`.

## sons

Cada som: `arquivo` e `licenca` (obrigatórios); `titulo`, `autor`, `fonte` (vão para os créditos). O que faltar é
completado pela linha do arquivo no `marca/sons/creditos.md`:

```
| Arquivo | Título | Autor | Fonte | ID | Licença |
|---|---|---|---|---|---|
| `trilhas/gentlemen.wav` | Gentlemen | Vendla | Epidemic Sound | 0722c45e-… | assinatura Epidemic Sound da conta conectada |
```

A coluna `Arquivo` é obrigatória (vale o nome do arquivo); as outras, as que existirem (colunas a mais, como
"Clima" ou "Uso", são ignoradas, e pode haver uma tabela para trilhas e outra para efeitos). O ID entra na licença.

## trilha

Um objeto (uma faixa no vídeo todo, o formato antigo) ou uma lista de faixas em ordem de tempo.

| Campo | Padrão | O que faz |
|---|---|---|
| `som` | | nome em `sons` |
| `de` | 0 na 1ª | onde a faixa entra no vídeo; na 2ª em diante é o ponto da **troca** |
| `ate` | até a troca ou o fim | só para acabar antes: deixa silêncio até a próxima faixa |
| `inicio` | 0 | o ponto da música que toca quando ela entra (s ou `"mm:ss,cc"`); `src` aqui é erro (é das camadas) |
| `abaixo_da_voz` | 16 | quantos LU a faixa fica abaixo da voz quando ninguém fala; durante a fala ela abaixa mais, sozinha |
| `cruzar` | 0,5 | segundos de crossfade na troca para esta faixa, centrado no `de` |
| `fade_in` | 1 | entrada do silêncio (1ª faixa, ou depois de um `ate`) |
| `fade_out` | 2 | saída para o silêncio (última faixa, ou num `ate`) |

Cada faixa é medida no pedaço que toca e fica no seu `abaixo_da_voz`: duas músicas de volumes diferentes saem no
mesmo nível. Na troca, ponha um efeito de virada no mesmo `de` (ele cobre a emenda).

## efeitos

Onde cai (um destes):

| Campo | Cai em |
|---|---|
| `camada` | `de` da camada com esse id no `insercoes.json`; com `"em": "fim"`, no `ate`; com `"em": "recorte"`, no 2º passo do `recorte` dela (o zoom seco); `"recorte#3"`, no 3º |
| `insercao` | `de` do cartão do `insercoes.json` que tem esse texto |
| `legenda` | início do trecho da fala na `legenda.srt` (com `"em": "fim"`, no fim); acento e pontuação não contam |
| `em` | a âncora (sem `camada`, `insercao` nem `legenda`) |
| `t` | o tempo |

E também: `som`, `motivo` (obrigatórios), `volume` (0 = pico em -12 dBFS; -3 a -6 em cima da fala), `desvio` (s,
adianta ou atrasa).

## entrega

`pasta` (padrão `../entrega`) e `nome` (o nome do arquivo que ela vai postar; sem extensão vira `.mp4`). Opcional:
`legenda`, o caminho da legenda curta; sem ele, o script procura `legenda-curta.srt` ao lado do `insercoes.json`,
depois ao lado do vídeo e em `../insercoes/`. Na mixagem completa, copia o vídeo, a `legenda-curta.srt`, o
`creditos.md` e o `som.json` para a pasta.

## Comandos

```
sonorizar.py som.json --resumo                         confere tudo; não grava nada
sonorizar.py som.json --trecho 30 50                   prévia do pedaço (previa-trecho.mp4)
sonorizar.py som.json --trecho 0 15 --trilha <som>     prévia com outra trilha no lugar (previa-<som>.mp4)
sonorizar.py som.json                                  vídeo inteiro, creditos.md, medida e entrega
sons.py <pasta>                                        lista sons, duração, pico e licença no creditos.md
sons.py --baixar <link> <arquivo>                      baixa um som (link do Epidemic vale minutos)
identificar.py <vídeo ou link> ...                     músicas dos Reels pelo Shazam (rode com --python 3.12)
ouvir.py <vídeo> --base <sem trilha> --de A --ate B    fala inteligível com o som por baixo (%)
```
