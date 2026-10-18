# Contrato do kit de edição (v2)

As skills `/decupar`, `/inserir`, `/sonorizar`, `/criticar` e `/minha-edicao` são instaladas uma a uma e não
importam código umas das outras. Elas se falam por **arquivos**: a pasta do vídeo, a pasta `marca/` e os JSONs
abaixo. Este documento é a fonte da verdade desses arquivos; o detalhe de cada JSON que só uma skill lê fica no
`referencia.md` dela.

## 0. Quem decide

- Cada arquivo tem **um dono**: a skill que o grava (`palavras-corte.json` → `/decupar`, `geometria.json` →
  `/inserir`, `critica/` → `/criticar`, `marca/estilo.md` e `marca/referencias/` → `/minha-edicao`). O JSON que
  o Claude escreve é do script que o lê (`cortes.json` → `/decupar`, `insercoes.json` → `/inserir`,
  `som.json` → `/sonorizar`).
- Conflito entre skills: vale o que está aqui. Um campo novo ou uma mudança de formato entra **aqui primeiro**;
  quem lê pede o campo ao dono, e o dono grava.
- Âncoras, `achar_marca` e caminhos vivem em `scripts/contrato.py`, **o mesmo arquivo** nas skills `/decupar`,
  `/inserir`, `/sonorizar` e `/criticar`. Mudou um, copie para as quatro e rode `uv run tests/test_contrato.py`
  (confere que os quatro são iguais e dão o mesmo resultado pela porta de cada skill).

## 1. Pastas

```
<pasta de edição>/                       qualquer nome; é onde mora a marca
  marca/
    estilo.md                            receita de estilo (a /minha-edicao escreve; as outras leem)
    fontes/   cor/<nome>.cube   letterings/<modelo>.html
    sons/trilhas/  sons/efeitos/  sons/creditos.md
    referencias/<nome>.<mp4|mov|jpg|png>  vídeos e prints de referência, direto na pasta
    referencias/medidas/<nome>/  referencias/ficha.md  referencias/prova.json  referencias/prova/
  videos/<AAAA-MM-DD-assunto>/           a pasta do vídeo
    bruto.<ext>                          só leitura (pode ser atalho)
    brutos/{imagens,videos}/  brutos/fontes.md   mídia de terceiros; fontes.md tem nome, origem e licença
    decupagem/  insercoes/  som/  critica/  entrega/
```

- **`achar_marca(pasta)`** sobe a partir da pasta dada até achar `marca/estilo.md`, sem seguir atalhos
  (symlinks), e devolve a pasta `marca/` (ou nada). O script que a procura imprime `Marca: <caminho>` ou
  `Marca: nenhuma`.
  Exceção: o `prova.py` da `/minha-edicao` roda antes de existir `estilo.md` e procura o arquivo pedido subindo.
- **Caminho num JSON**: começa com `marca/` → contra a pasta que contém `marca/`; sem marca achada, é erro.
  Outro relativo → contra a pasta do próprio JSON.
- `marca/referencias/`: só vídeo e imagem de referência ficam soltos na pasta (a `/criticar` usa todos);
  medidas, ficha e prova vão nas subpastas e arquivos acima.

## 2. Tempos e âncoras na fala

Todo tempo de `cortes.json`, `insercoes.json` e `som.json` pode ser:

| Forma | Exemplo | Em `de` | Em `ate` |
|---|---|---|---|
| segundos | `42.9`, `"42,9"` | o tempo | o tempo |
| relógio | `"00:42,90"`, `"1:02:03.5"` | o tempo | o tempo |
| frase | `"F15"` | início da frase | fim da frase |
| borda da frase | `"F15:inicio"`, `"F15:fim"` | essa borda | essa borda |
| palavra pela posição | `"F15:3"` | início da 3ª palavra | fim dela |
| palavra pelo texto | `"F15:repente"`, `"F15:repente#2"` | início da 1ª (2ª) "repente" | fim dela |
| emenda | `"F15:emenda"` | o corte da imagem logo antes da F15 | idem |
| deslocamento | `"F1:fim+0.25"`, `"F20:mais-0,1"` | a âncora ± segundos | idem |

- `F<n>` é o id da frase na `decupagem/transcricao.txt` do **bruto**: não muda com um novo corte. No
  `cortes.json` a âncora vale no tempo do bruto; nos outros JSONs, no tempo do vídeo cortado, resolvida pelo
  `decupagem/palavras-corte.json`.
- A posição conta só as palavras com texto, de 1. Número sozinho é posição: a palavra falada "10" se escreve
  `"F81:10#1"`. `inicio`, `fim` e `emenda` são bordas; a palavra falada "fim" se escreve `"F3:fim#1"`.
- A palavra compara sem acento, caixa e pontuação ("Vocês," = "voces"), e é a palavra **da transcrição**:
  `correcoes` da `/inserir` muda só o texto da legenda, não a âncora.
- Frase que o corte partiu vale inteira: `"F3"` começa na 1ª palavra que ficou e termina na última.
- Âncora numa palavra ou frase que o corte tirou é **erro**, com a palavra que sumiu. Nunca cai no lugar mais
  perto em silêncio.
- `"F15:emenda"` só existe no vídeo cortado, e só se a F15 começa até 1 s depois de um corte. É o jeito de uma
  camada acabar junto com o plano: `"ate": "<1ª frase do plano seguinte>:emenda"`.
- **Encostar**: no vídeo cortado, todo tempo que cai a menos de 3 quadros de uma emenda vale a emenda (sem
  quadro solto). Vale na `/inserir` e na `/sonorizar` (é o `tempo` do `contrato.py`); a `/inserir` diz quais
  encostou.
- No `cortes.json`, âncora de palavra (posição, texto, `inicio`, `fim`) sem deslocamento também limita o
  trecho pela posição da palavra (o Whisper sobrepõe palavras coladas); com deslocamento, vale só o tempo.

## 3. `/decupar` → `decupagem/`

### 3.1 `cortes.json` (o Claude escreve; detalhe em `decupar/referencia.md`)

```json
{
  "pausa_max": 0.22, "bordas": "som", "velocidade": 1.2,
  "zoom": {"ancora": [0.49, 0.36], "niveis": [1.0, 1.12, 1.2, 1.3], "alternar_na_pausa": true},
  "cor": {"corrigir": false, "look": {"lut": "marca/cor/look.cube"}},
  "trechos": [
    {"de": "F1", "ate": "F1:fim", "zoom": 1.0, "nota": "pergunta do gancho"},
    {"de": "F3:2", "ate": "F3:fim", "zoom": 1.25, "nota": "tira o 'até' gaguejado"},
    {"de": 185.095, "ate": 188.47, "exato": true, "zoom": 1.12}
  ],
  "ajustes": {"T5.de": 0.04, "T5.ate": -0.03}
}
```

| Campo | Padrão | Faixa | Regra |
|---|---|---|---|
| `bordas` | `"palavra"` | `"som"`, `"palavra"` | `som`: a borda de cada fala sai do volume medido; `palavra`: tempo do Whisper + folga fixa |
| `velocidade` | 1.0 | 0,5 a 2 | vídeo e voz juntos; todo tempo de saída já vem dividido por ela |
| `trechos[].zoom` | 1.0 | 1 a 3 | nível do trecho |
| `zoom.alternar_na_pausa` | false | | emenda **dentro** do trecho troca para o nível vizinho: o de baixo; no mais baixo, o de cima. Pedaço com menos de 0,4 s não troca |
| `zoom.ancora` | [0.5, 0.4] | 0 a 1 | ponto do quadro de saída que fica parado no zoom; o recorte sai da resolução nativa |
| `ajustes` | | -1 a 1 s | desloca a borda do trecho `T<n>` (n conta de 1 na lista). Quem acha o valor é a `/criticar` |
| `cor.look.lut` | | | `.cube` aplicado depois do recorte e da escala; com ele, o look por números é ignorado (o script avisa) |

### 3.2 `palavras-corte.json` (a `/decupar` grava em todo `cortar.py`, também no `--resumo`)

```json
{
  "versao": 2, "video": "final.mp4", "duracao": 134.3, "fps": 30, "velocidade": 1.2, "medido": "pedacos",
  "trechos": [{"n": 1, "a": 0.0, "b": 2.1}, {"n": 2, "a": 2.1, "b": 3.267}],
  "emendas": [2.1, 3.267],
  "frases": [{"id": "F1", "a": 0.12, "b": 2.05, "texto": "Vocês acham que...", "trecho": 1}],
  "palavras": [{"w": "Vocês", "a": 0.12, "b": 0.41, "frase": "F1", "n": 1, "i": 37, "trecho": 1}]
}
```

- Tudo no tempo do vídeo cortado, já com a velocidade. `n` é a posição da palavra na frase (seção 2), `i` o
  índice em `.dados/palavras.json`, `trecho` o `T<n>` do `cortes.json`.
- `frases` tem uma linha por pedaço de frase que ficou (frase partida em dois trechos aparece duas vezes).
- `trechos`: as bordas de cada trecho; `emendas`: toda troca de pedaço no vídeo (entre trechos e nas pausas
  tiradas dentro deles).
- `medido`: depois do render, `"pedacos"` (quadros contados em cada pedaço e na saída) ou `"saida"` (render
  único: quadros da saída), e **todo** tempo do arquivo segue as bordas medidas. No `--resumo`, `false` (bordas
  previstas), a não ser que o último render seja do mesmo corte. `video` diz em qual arquivo foi medido.

O `legenda.srt` continua igual, para quem usa outro editor.

### 3.3 LUT do editor da pessoa (quem chama é a `/minha-edicao`)

```
uv run "<decupar>/scripts/lut_capcut.py" "<bruto>" "<exportação do editor>" "marca/cor/<nome>.cube" [--comparar "<outro.cube>"]
```

Grava o `.cube` e `<nome>-comparacao.jpg` (bruto | com o LUT | exportação). A última linha é JSON:
`{"de00_com_lut", "de00_sem_lut", "quadros", "resultado", "comparacao"}`. `resultado`: `"aceita"` (ΔE00 até 2),
`"atenção"` (de 2 a 3: a pessoa olha a comparação e decide) ou `"refaz"` (acima de 3, ou pior que sem LUT).

## 4. `/inserir` → `insercoes/`

### 4.1 `insercoes.json` (o Claude escreve; detalhe em `inserir/referencia.md`)

O que as outras skills leem dele:

- `camadas[]`: `id` (único), `tipo` (`video`, `imagem`, `faixa`, `html`), `lugar` (`topo`, `atras`,
  `frente`), `de`, `ate` e, no vídeo, `src` (segundo do arquivo de origem) e `recorte` (caixa fixa, ou lista
  de passos `{"t", "caixa", "src"?, "dur"?}` com `t` relativo ao início da camada). A `/sonorizar` prende
  efeito a `id`, à borda (`de`, `ate`) e ao passo do `recorte`.
- `insercoes[]` (cartões): `tipo`, `de`, `ate` e o texto. A `/sonorizar` acha o cartão pelo texto.
- `estilo.zona_segura` ([260, 1600]) e `estilo.reguas`.
- `aceito: "<motivo>"` em camada, inserção ou faixa de `legenda`: a decisão escrita de deixar a peça fora da
  zona segura ou da régua. A `/inserir` não avisa e a `/criticar` não reprova (fica em atenção).
- Arquivo de `brutos/` só entra com uma linha em `brutos/fontes.md` com o nome dele, a origem e a licença.

### 4.2 Modelo de lettering (camada `"tipo": "html"`)

`marca/letterings/<nome>.html`: página de 1080×1920 com fundo transparente. Todo `{{campo}}` do modelo precisa
estar em `campos` (campo opcional vai com `""`; o modelo esconde o vazio). Fontes e imagens valem relativas à
pasta do modelo (`../fontes/`). Se o modelo se arruma por script, ele marca `document.body.dataset.pronto` no
fim, e a `/inserir` espera por `body[data-pronto]` antes de fotografar; sem isso, espera as fontes.

### 4.3 Saídas

- `<vídeo>-insercoes.mp4` (`final-insercoes.mp4` a partir do `final.mp4`), `legenda-curta.srt` (a mesma lista
  da legenda gravada), `cartoes.png`, `quadros/folha.jpg`.
- `.dados/mascaras/m-<q0>-<q1>-<motor>.mkv`: máscara da pessoa (ffv1 cinza, faixa completa) só nos trechos com
  camada `atras`.
- `.dados/geometria.json`: tudo o que foi desenhado, no tempo final, com caixa `[x, y, w, h]` no quadro 1080×1920:

```json
{"duracao": 134.4, "quadro": [1080, 1920], "zona_segura": [260, 1600], "itens": [
  {"id": "leg-0042", "tipo": "legenda", "texto": "pobre", "destaque": true, "de": 1.9, "ate": 2.3, "caixa": [312, 640, 455, 150]},
  {"id": "insercao-3", "tipo": "numero", "lugar": "cartao", "de": 42.9, "ate": 45.0, "caixa": [90, 300, 900, 600]},
  {"id": "headline", "tipo": "faixa", "lugar": "frente", "texto": "Ter loja virou coisa de pobre?", "de": 0, "ate": 2.3, "caixa": [91, 908, 898, 104]},
  {"id": "L2", "tipo": "html", "lugar": "frente", "texto": "R$ 18 milhões", "de": 45.9, "ate": 48.5, "caixa": [183, 335, 810, 413]},
  {"id": "mosaico1-1", "tipo": "video", "lugar": "atras", "de": 23.8, "ate": 31.47, "caixa": [30, 190, 390, 693], "aceito": "..."},
  {"id": "gancho", "tipo": "dividida", "de": 0, "ate": 13.14, "corte": 960, "laterais": "borrado",
   "pessoa": [{"de": 0, "recorte_y": 150, "escala": 0.72}, {"de": 2.11, "recorte_y": 450, "escala": 1.0}]}
]}
```

`aceito` aparece em qualquer item que o tenha no `insercoes.json` (na legenda, pela faixa). `recorte_y` é medido
no quadro já na `escala`.

## 5. `/sonorizar` → `som/`

### 5.1 `som.json` (o Claude escreve; detalhe em `sonorizar/referencia.md`)

```json
{
  "video": "../insercoes/final-insercoes.mp4",
  "palavras": "../decupagem/palavras-corte.json",
  "insercoes": "../insercoes/insercoes.json",
  "legenda": "../decupagem/legenda.srt",
  "sons": {"cordas": {"arquivo": "marca/sons/trilhas/strings-in-solitude-3.flac"}},
  "trilha": [
    {"som": "cordas", "de": 0, "abaixo_da_voz": 16, "fade_in": 0.5},
    {"som": "jazz", "de": "F36:inicio-0.5", "cruzar": 1.2, "fade_out": 2}
  ],
  "efeitos": [
    {"camada": "placa-5-zoom", "em": "recorte", "som": "zoom", "volume": -3, "motivo": "zoom seco na placa"},
    {"em": "F36:inicio-0.2", "som": "virada", "volume": -4, "motivo": "virada de bloco"}
  ],
  "entrega": {"pasta": "../entrega", "nome": "ter-loja-virou-coisa-de-pobre"}
}
```

- `video` é o vídeo **antes** da trilha (a saída da `/inserir`, ou o final da `/decupar`); a `/criticar` mede
  as emendas nele. `saida` (padrão `video-com-som.mp4`, na pasta `som/`) é o vídeo com som.
- `trilha`: um objeto (uma faixa no vídeo todo) ou uma lista em ordem de tempo. A troca acontece no `de` da
  faixa seguinte. Campos por faixa: `som`, `de`, `inicio` (ponto da música de onde ela parte; `src` é das
  camadas e aqui é erro), `abaixo_da_voz` (16), `fade_in` (1), `fade_out` (2), `cruzar` (0,5 s de crossfade,
  centrado no `de`). `ate` serve só para acabar antes e deixar silêncio.
- Efeito preso a `camada`: `em` é `"inicio"` (padrão), `"fim"`, `"recorte"` (2º passo do recorte) ou
  `"recorte#k"`. Sem camada: `insercao` (texto do cartão), `legenda` (trecho da `legenda.srt`), `em` (âncora)
  ou `t`.
- `entrega` copia o vídeo final, a legenda curta, o `creditos.md` e o `som.json`. A legenda curta é a
  `legenda-curta.srt` ao lado do `insercoes.json`; `entrega.legenda` aponta outra.

### 5.2 `marca/sons/creditos.md`

Tabela Markdown com a coluna `Arquivo` (obrigatória; vale o nome do arquivo) e, se houver, `Título`, `Autor`,
`Fonte`, `ID` e `Licença`; outras colunas são ignoradas. Pode haver mais de uma tabela. O que o `som.json` não
diz de um som sai da linha dele; o `ID` entra na licença. Som sem licença em nenhum dos dois é erro.

```
| Arquivo | Título | Autor | Fonte | ID | Licença |
|---|---|---|---|---|---|
| `trilhas/gentlemen.flac` | Gentlemen | Vendla | Epidemic Sound | 0722c45e-… | assinatura Epidemic Sound |
```

### 5.3 Trilha dos Reels da pessoa (quem chama é a `/minha-edicao`)

```
uv run --python 3.12 "<sonorizar>/scripts/identificar.py" "<reel ou link>" ...
```

Shazam em pedaços de 10 s a cada 8 s; imprime, por vídeo, cada música com o trecho em que toca e o selo.

## 6. `/criticar` → `critica/`

Lê o vídeo final (o mais novo em `entrega/`, senão a `saida` do `som.json`, o da `/inserir` ou o da
`/decupar`), o `palavras-corte.json` (texto esperado e as emendas pelas bordas de `trechos`), o
`geometria.json` (zona segura dele, `aceito`, `pessoa` das divididas, `texto` de faixa e html, `destaque`), o
`video` do `som.json`, a `legenda-curta.srt`, `marca/estilo.md` e `marca/referencias/`. Nada fora de `critica/`
muda. Grava:

- `relatorio.md` e `medidas.json`: cada item com **passa**, **reprova**, **atenção** (ouvir ou olhar; não
  bloqueia) ou **pulado** (faltou entrada), a medida, onde e a correção (skill · arquivo · campo);
- `folha-NN.jpg` (1 quadro por segundo), `folha-cortes-NN.jpg` (2 quadros antes e 2 depois de cada corte),
  `folha-referencia.jpg`, `letras/` (palavras estilizadas ampliadas) e `fala-final.json` (transcrição do final);
- `editor-chefe.md`: o veredito do subagente, pela régua `criticar/critica.md`.

As correções voltam para o arquivo do dono (seção 0): quem aplica é o Claude, não o script.

## 7. `/minha-edicao` → `marca/` e o formato

Grava `marca/estilo.md`, copia para `marca/` o que ele cita (fontes, LUT, sons, letterings, referências) e
escreve a receita de formato em `<pasta de edição>/.claude/skills/<nome>/SKILL.md`. Usa o `lut_capcut.py`
(3.3) e o `identificar.py` (5.3) pelo caminho da skill irmã. Exemplos de estilo moram em
`minha-edicao/exemplos/<nome>/estilo.md` (sem frontmatter); exemplos de formato, em `.../<nome>/SKILL.md`.
