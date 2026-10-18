# Contrato do kit de edição (v2)

As skills `/decupar`, `/inserir`, `/sonorizar` e `/criticar` são instaladas uma a uma e não importam
código umas das outras. Elas se falam por **arquivos**: a pasta do vídeo e os JSONs abaixo. Este
documento é a fonte da verdade desses arquivos. Uma mudança de formato muda aqui primeiro.

Origem: o Reel da Ana "Ter loja virou coisa de pobre?" (17/10/2026) saiu de scripts feitos na hora,
fora do kit. O v2 traz para o kit o que aqueles scripts sabiam fazer, sem nada da Ana dentro do código.

## 1. Pastas

```
<pasta de edição>/                 qualquer nome; é onde mora a marca
  marca/
    estilo.md                      receita de estilo (fontes, legenda, cor, som, composição)
    fontes/  cor/<nome>.cube  sons/{trilhas,efeitos}/ + sons/creditos.md  referencias/  letterings/
  videos/<AAAA-MM-DD-assunto>/
    bruto.<ext>                    só leitura (pode ser symlink)
    brutos/{imagens,videos}/ + brutos/fontes.md   mídia de terceiros com origem anotada
    decupagem/   insercoes/   som/   critica/   entrega/
```

**Achar a marca** (`achar_marca(pasta)`, copiado no `comum.py` de cada skill): sobe a partir da
pasta do vídeo até achar `marca/estilo.md` ou até a raiz do disco. O script imprime
`Marca: <caminho>` ou `Marca: nenhuma`. Em todo JSON, um caminho que começa com `marca/` é resolvido
contra essa pasta. Os outros caminhos relativos valem a partir da pasta do próprio JSON.

## 2. Âncoras de tempo (iguais em todos os JSONs)

Um tempo pode ser:

| Forma | Exemplo | Significa |
|---|---|---|
| segundos | `42.9` | tempo do vídeo cortado |
| relógio | `"00:42,90"` | idem |
| frase | `"F15"` | início da frase F15 (em `ate`: fim dela) |
| frase:borda | `"F15:inicio"`, `"F15:fim"` | início ou fim da frase |
| frase:palavra | `"F15:repente"`, `"F15:repente#2"` | início da 1ª (ou 2ª) ocorrência da palavra na frase; a comparação ignora acento, caixa e pontuação |
| frase:índice | `"F15:3"` | início da 3ª palavra da frase (contando de 1) |
| deslocamento | `"F1:fim+0.25"`, `"F20:mais-0.1"` | qualquer âncora mais ou menos segundos |

- `F<n>` é o id da frase na `decupagem/transcricao.txt` do **bruto**. Ele não muda quando o corte
  muda. Por isso o JSON escrito com âncoras sobrevive a um novo corte.
- Em `ate` (fim de inserção ou camada), `"F15:repente"` significa o **fim** da palavra.
- Quem resolve é o `palavras-corte.json` (seção 3). Se a âncora cair numa palavra que o corte tirou,
  o script para e diz qual palavra sumiu. Não pode cair no lugar mais perto em silêncio.

## 3. `/decupar` → `decupagem/`

### 3.1 `cortes.json` (o Claude escreve)

```json
{
  "pausa_max": 0.22,
  "velocidade": 1.2,
  "zoom": {"ancora": [0.49, 0.36], "niveis": [1.0, 1.12, 1.2, 1.3], "alternar_na_pausa": true},
  "cor": {"corrigir": false, "look": {"lut": "marca/cor/look.cube"}},
  "trechos": [
    {"de": "F1", "ate": "F1", "zoom": 1.0, "nota": "pergunta do gancho"},
    {"de": "F3:2", "ate": "F3:fim", "zoom": 1.25, "nota": "tira o 'até' gaguejado"},
    {"de": 70.47, "ate": 73.68, "exato": true, "zoom": 1.12}
  ],
  "ajustes": {"T5.de": 0.04, "T5.ate": -0.03}
}
```

- Os tempos de `trechos` são do **bruto**. `F3:2` é a palavra 2 da frase 3 (no `de` vale o início
  dela, no `ate` o fim). Para o `/decupar`, as âncoras da seção 2 valem com o tempo do bruto.
- `velocidade` (padrão 1.0): acelera vídeo e voz juntos (`setpts` + `atempo`). Tudo o que sai em
  tempo final já vem dividido por ela.
- `zoom.ancora`: o ponto do quadro de **saída** que fica parado no zoom, em fração (x, y). Fica perto
  dos olhos. O recorte do zoom sai da resolução **nativa** do bruto, antes de reduzir.
- `trechos[].zoom`: o nível daquele trecho. Com `alternar_na_pausa`, cada emenda **dentro** de um
  trecho (pausa interna tirada) troca para o nível vizinho em `niveis`, para a emenda não pular.
- `cor.look.lut`: um `.cube`, aplicado depois do recorte e da escala com `lut3d=interp=tetrahedral`.
  Continua valendo o look por números de hoje (`contraste`, `calor`…). Os dois juntos não: com
  `lut`, o resto do look é ignorado e o script avisa.
- `ajustes`: deslocamento fino (s) da borda de um trecho, escrito pela `/criticar`. `T5` é o 5º
  trecho da lista (contando de 1).

### 3.2 Saídas novas

`decupagem/palavras-corte.json`, gravado em todo `cortar.py` (também no `--resumo`):

```json
{
  "versao": 1, "video": "final.mp4", "duracao": 134.4, "fps": 30, "velocidade": 1.2,
  "frases": [{"id": "F1", "a": 0.0, "b": 2.13, "texto": "Vocês acham que..."}],
  "palavras": [{"w": "Vocês", "a": 0.0, "b": 0.31, "frase": "F1", "n": 1, "i": 37, "trecho": 1}]
}
```

- `a` e `b` estão no tempo do vídeo cortado, já com a velocidade. `n` é a posição da palavra na
  frase (contando de 1), `i` é o índice em `.dados/palavras.json` e `trecho` conta de 1.
- `frases` só lista as frases que ficaram no corte, com o pedaço que ficou.
- Uma frase cortada no meio aparece com as palavras que restaram e o `a`/`b` delas.

O `legenda.srt` continua igual, para quem usa outro editor.

### 3.3 LUT a partir do CapCut

`decupar/scripts/lut_capcut.py "<bruto>" "<exportação do editor>" "<saída.cube>"` casa os dois
vídeos (áudio para achar o tempo, imagem para o quadro exato), ajusta um LUT 33³ e imprime o ΔE00
médio num trecho que ficou fora do ajuste. Quem chama é a `/minha-edicao`, uma vez por pessoa, e a
saída vai para `marca/cor/`.

## 4. `/inserir` → `insercoes/`

### 4.1 `insercoes.json` (o Claude escreve)

```json
{
  "estilo": {
    "fonte": "marca/fontes/NeueMontreal-Bold.otf",
    "fonte_destaque": "marca/fontes/AppleGaramond-Italic.ttf",
    "tamanho": 116, "palavras_max": 1, "letras_max": 30,
    "minusculas": true, "juntar_numeros": true, "nomes": ["Gokoco", "TikTok"],
    "legenda_y": 1290, "margem": 70, "sombra": 0.45,
    "escala_destaque": 1.75, "destaque_y": 760,
    "zona_segura": [260, 1600]
  },
  "destaques": ["pobre", "milhões"],
  "correcoes": {"Gococo": "Gokoco"},
  "legenda": [
    {"de": 0, "ate": "F1:fim+0.25", "y": "some"},
    {"de": "F1:fim+0.25", "ate": "F7:aluga-se", "y": 1190}
  ],
  "divididas": [
    {"id": "gancho", "de": 0, "ate": "F7:aluga-se", "corte": 960,
     "pessoa": [{"de": 0, "recorte_y": 150, "escala": 0.72}, {"de": "F3", "recorte_y": 450}],
     "laterais": "borrado"}
  ],
  "camadas": [
    {"id": "placa", "tipo": "video", "arquivo": "../brutos/videos/aluga-se.mp4", "src": 22.0,
     "de": 0, "ate": 2.63, "lugar": "topo", "audio": null,
     "recorte": [{"t": 0, "caixa": [21, 347, 699, 932]}, {"t": 1.0, "caixa": [105, 347, 495, 660]}]},
    {"id": "headline", "tipo": "faixa", "texto": "Ter loja virou coisa de pobre?",
     "de": 0, "ate": "F1:fim+0.25", "y": 908, "largura": 898, "altura": 104, "raio": 17,
     "fundo": "#FCFCFC", "tinta": "#111111", "fonte": "marca/fontes/NeueMontreal-Bold.otf", "tamanho": 58},
    {"id": "gokoco-1", "tipo": "video", "arquivo": "../brutos/videos/gokoco-luma.mp4", "src": 114,
     "de": "F15:repente", "ate": "F17:fim", "x": 30, "y": 190, "w": 390, "rot": -6, "raio": 26,
     "sombra": 0.35, "lugar": "atras", "entra": {"efeito": "pop", "dur": 0.18}, "sai": 0.12},
    {"id": "L2", "tipo": "html", "modelo": "marca/letterings/numero.html",
     "campos": {"numero": "R$ 18", "unidade": "milhões", "texto": "por mês"},
     "de": "F29:faturou", "ate": "F29:fim", "lugar": "frente",
     "entra": {"efeito": "pop", "dur": 0.14}, "legenda": "some"}
  ],
  "insercoes": []
}
```

- Os tempos estão no tempo do vídeo cortado e aceitam as âncoras da seção 2.
- **`legenda`** (lista de faixas) muda a altura da legenda ou a esconde num intervalo. É o único jeito
  de mexer na legenda. Nada de inserção vazia. Uma camada ou inserção com `"legenda"` cria a faixa dela.
- **`destaque_y`**: a palavra de destaque sobe para esta linha de base (px), maior
  (`escala_destaque`), na `fonte_destaque`. Sem `destaque_y`, ela fica na linha da legenda.
- **`palavras_max: 1` com `juntar_numeros`**: "100 mil", "R$ 18 milhões" e "10, 20" saem juntos.
- **`minusculas`**: tudo em minúscula, menos o que está em `nomes` e a primeira palavra de frase com nome próprio.
- **`divididas`**: tela dividida em `corte` (px). A pessoa vai para a metade de baixo; cada item de
  `pessoa` vale a partir do seu `de` (`recorte_y` é a linha do quadro de onde sai a janela; `escala`
  menor que 1 deixa laterais borradas). A metade de cima recebe as camadas `lugar: "topo"`.
- **`camadas`** (`tipo`: `video`, `imagem`, `faixa`, `html`):
  - `lugar`: `topo` é a metade de cima da dividida, em 720 px de largura, com laterais do mesmo
    vídeo ampliado e borrado; `atras` fica atrás da pessoa e precisa de máscara; `frente` fica por
    cima de tudo, menos da legenda.
  - `recorte`: uma caixa fixa `[x, y, w, h]`, ou uma lista com `t` (relativo ao início da camada)
    para o "aberto e depois o zoom seco".
  - `src` é o segundo do arquivo de origem; `audio` é o ganho em dB, ou `null` para mudo.
  - `entra` e `sai`: `{"efeito": "pop", "dur": 0.18}` (escala 0,82 para 1 com alfa) ou só o número
    (alfa).
  - `html` usa um modelo com `{{campo}}` e vira PNG transparente pelo navegador.
- `insercoes` (os cartões de hoje) continua valendo, com o mesmo formato. As âncoras passam a ser aceitas.

### 4.2 Saídas

- `<vídeo>-insercoes.mp4`, `legenda-curta.srt` (**o mesmo tempo da legenda gravada**: os dois
  saem da mesma lista) e `quadros/folha.jpg`.
- `insercoes/.dados/geometria.json`: tudo o que foi desenhado, no tempo final, para a `/criticar` medir.

```json
{"duracao": 134.4, "quadro": [1080, 1920], "itens": [
  {"id": "leg-0042", "tipo": "legenda", "texto": "pobre", "destaque": true, "de": 1.9, "ate": 2.3, "caixa": [312, 640, 455, 150]},
  {"id": "gokoco-1", "tipo": "video", "lugar": "atras", "de": 23.8, "ate": 31.48, "caixa": [30, 190, 390, 693]},
  {"id": "gancho", "tipo": "dividida", "de": 0, "ate": 13.17, "corte": 960}
]}
```

- Máscara: `inserir/scripts/mascara.py --motor auto|vision|rvm`. Gera só os trechos com camada
  `atras`, em `insercoes/.dados/mascaras/`, como vídeo cinza sem perda e faixa completa (ffv1).
- Composição: `inserir/scripts/compor.py`, chamado pelo `inserir.py`. Quando não há dividida nem
  camada, o caminho de hoje continua igual (rápido).

## 5. `/sonorizar` → `som/`

```json
{
  "video": "../insercoes/video-insercoes.mp4",
  "legenda": "../decupagem/legenda.srt",
  "palavras": "../decupagem/palavras-corte.json",
  "insercoes": "../insercoes/insercoes.json",
  "sons": {"cordas": {"arquivo": "marca/sons/trilhas/strings-in-solitude-3.flac", "licenca": "..."}},
  "trilha": [{"som": "cordas", "de": 0, "ate": "F20:Isso"}, {"som": "gentlemen", "de": "F20:Isso", "cruzar": 0.4}],
  "efeitos": [
    {"camada": "L2", "som": "kaching", "volume": -4, "motivo": "lettering R$ 18 milhões entra"},
    {"em": "F20:Isso", "som": "virada", "motivo": "virada de bloco"}
  ],
  "entrega": {"pasta": "../entrega", "nome": "ter-loja-virou-coisa-de-pobre"}
}
```

- `trilha` pode ser um objeto (como hoje) ou uma lista de faixas com troca (`cruzar` = segundos de
  crossfade).
- Um efeito se prende a `camada` (id em `insercoes.json`), `insercao` (como hoje), `legenda` (como
  hoje), `em` (âncora da seção 2) ou `t`.
- `entrega` copia o vídeo final, a `legenda-curta.srt` e o `creditos.md` para a pasta de entrega.

## 6. `/criticar` → `critica/`

Ela lê o vídeo final, o `palavras-corte.json`, o `geometria.json`, o `som.json`, o `marca/estilo.md`
e `marca/referencias/`. Grava:

- `critica/relatorio.md`: cada item com **passa** ou **reprova**, medida e onde (tempo).
- `critica/folha.jpg`: o resultado ao lado da referência no mesmo bloco.

O que é medido pelo script:
- emendas (salto de volume, pausa curta ou longa demais, palavra cortada);
- gagueira e repetição (transcreve o final e compara com o texto esperado);
- quadros soltos (corte com menos de 3 quadros);
- zona segura (caixas fora de `zona_segura`);
- distribuição de posições (as inserções não podem estar todas na mesma região);
- tempo sem evento visual acima de 8 s;
- legenda gravada contra `legenda-curta.srt`;
- volume (-14 LUFS ±1, pico ≤ -1 dBTP).

O olho crítico fica a cargo de um subagente "editor-chefe" (régua em `criticar/critica.md`). Ele
compara a folha com a referência e julga o gancho, a trilha e a legibilidade. Por exemplo, o "h" do
Garamond itálico lido como "b".
