# insercoes.json: referência completa

O `insercoes.json` mora em `<pasta do vídeo>/insercoes/`. Caminho que começa com `marca/` vale contra a pasta
de edição (a que tem `marca/estilo.md`); os outros caminhos relativos valem a partir de `insercoes/`. O vídeo
tem 1080×1920 e toda posição (`x`, `y`, `w`, `h`) é em px nesse quadro.

```json
{
  "estilo": {...},
  "destaques": ["pobre", "milhões"],
  "correcoes": {"Gococo": "Gokoco", "alugas": "aluga-se"},
  "legenda": [...],
  "divididas": [...],
  "camadas": [...],
  "insercoes": [...]
}
```

## Âncoras

Todo tempo (`de`, `ate`, `t`, `t_direita`, `pessoa[].de`) aceita:

| Forma | Exemplo | Significa |
|---|---|---|
| segundos | `42.9` | tempo do vídeo cortado |
| relógio | `"00:42,90"` | idem |
| frase | `"F15"` | início da frase F15 (em `ate`: fim dela) |
| frase:borda | `"F15:inicio"`, `"F15:fim"` | início ou fim da frase |
| frase:palavra | `"F15:repente"`, `"F15:repente#2"` | início da 1ª (ou 2ª) vez da palavra na frase; em `ate`, o fim dela. Ignora acento, caixa e pontuação; vale a palavra da `transcricao.txt` (`correcoes` muda só a legenda) |
| frase:índice | `"F15:3"` | 3ª palavra da frase (contando de 1). Para a palavra "10", escreva `"F81:10#1"` |
| emenda | `"F15:emenda"` | o corte da imagem logo antes da F15: a camada que acaba junto com o plano usa `"ate": "<1ª frase do plano seguinte>:emenda"` |
| deslocamento | `"F1:fim+0.25"`, `"F20:mais-0.1"` | qualquer âncora mais ou menos segundos |

`F<n>` é o id da frase na `decupagem/transcricao.txt` do bruto: não muda com um novo corte. Quem resolve é o
`decupagem/palavras-corte.json`, pelas regras do contrato (seção 2). Âncora que cai numa palavra ou frase que o
corte tirou faz o script parar e dizer qual sumiu. Todo tempo que cai a menos de 3 quadros de uma emenda vai
para a emenda (sem quadro solto); o script diz quais encostou.

## estilo

Só o que difere do padrão.

| Chave | Padrão | O que é |
|---|---|---|
| `fonte`, `fonte_destaque` | fonte do sistema | arquivo `.otf`/`.ttf` (pode ser `marca/fontes/...`) |
| `tamanho` | 64 | tamanho da legenda (px) |
| `palavras_max`, `letras_max` | 4, 22 | pedaço da legenda: até N palavras e N letras. `1` = uma palavra por vez |
| `juntar_numeros` | false | "100 mil", "R$ 18 milhões" e "10, 20" saem juntos, como uma palavra |
| `minusculas` | false | tudo em minúscula, menos os `nomes` |
| `nomes` | [] | nomes que mantêm a caixa; aceita mais de uma palavra: `"TikTok Shop"`, `"O Animal Social"` |
| `maiusculas` | false | tudo em maiúscula |
| `cor`, `cor_destaque` | #FFFFFF | cor da legenda e da palavra de destaque |
| `escala_destaque` | 1.12 | tamanho da palavra de destaque em relação ao resto |
| `destaque_y` | — | o pedaço com destaque sobe para esta linha de base (px); sem ele, fica em `legenda_y` |
| `legenda_y` | 1400 | linha de base (o pé das letras) da legenda |
| `legenda_y_alto` | 330 | altura de `"alto"` nas faixas da legenda |
| `margem` | 110 | margem lateral da legenda; palavra longa encolhe para caber |
| `sombra` | 0.45 | sombra da legenda, de 0 a 1 |
| `zona_segura` | [260, 1600] | faixa de `y` onde texto e peça da frente ficam; fora dela é ATENÇÃO |
| `reguas` | ver abaixo | réguas de tempo para o que cobre o rosto |
| `cartao_fundo`, `cartao_tinta`, `cartao_destaque` | #141414, #F5F2EC, #E8C27A | cores dos cartões |

`reguas` (o que a receita de formato ou o `marca/estilo.md` disser vale mais; `null` desliga uma régua):
`{"primeiro_segundo": 1.0, "min": 1.5, "max": 6.0, "max_painel": 10.0, "respiro": 2.0}`. Elas valem para
cartões e camadas da frente. Camada `atras` e `topo` ficam fora.

`destaques`: as palavras de destaque (na `fonte_destaque`, maiores). `correcoes`: palavra que o Whisper
ouviu errado → a certa.

## legenda

Lista de faixas que mudam a legenda num intervalo. É o único jeito de mexer nela.

```json
"legenda": [
  {"de": 0, "ate": "F1:fim+0.25", "y": "some"},
  {"de": "F1:fim+0.25", "ate": "F7:fim", "y": 1190},
  {"de": "F40", "ate": "F41", "y": "alto"}
]
```

`y`: número (linha de base, px), `"alto"` ou `"some"`. A última faixa que pega o pedaço manda; camada ou
inserção com `"legenda": <y>` cria a faixa dela. Faixa com `"aceito": "<motivo>"` silencia a zona segura
dos pedaços dela.

A legenda sai do `decupagem/palavras-corte.json` (tempo de cada palavra; cada pedaço fica na tela até o
próximo, e o último termina no fim do vídeo). A troca de um pedaço para o seguinte que cai a menos de 3 quadros de uma emenda vai para a emenda (a
palavra de antes do corte não sobra sobre o plano novo), se os dois pedaços ficarem com 1 quadro ou mais. Sem ele, sai do `legenda.srt`, dividido pelo número de letras.
A `legenda-curta.srt` é escrita da mesma lista que é gravada na imagem.

## divididas

Tela dividida: a pessoa desce para baixo do `corte`, a metade de cima recebe as camadas `lugar: "topo"`.

```json
{"id": "gancho", "de": 0, "ate": "F7:fim", "corte": 960, "laterais": "borrado",
 "pessoa": [{"de": 0, "recorte_y": 150, "escala": 0.72}, {"de": "F3", "recorte_y": 450}]}
```

- `pessoa`: cada item vale a partir do seu `de`. `recorte_y` é a linha de cima da janela que desce,
  medida no quadro já na `escala`. `escala` menor que 1 deixa a pessoa menor, com laterais do mesmo quadro
  ampliado e borrado (`laterais`: `"borrado"` ou `"preto"`).
- Sem camada `topo` no trecho, a metade de cima fica preta.

## camadas

Peças soltas: vídeo, imagem, faixa (headline) e html (lettering). Todas têm `id`, `tipo`, `de`, `ate` e:

| Chave | O que é |
|---|---|
| `lugar` | `"frente"` (padrão: por cima de tudo, menos da legenda), `"atras"` (atrás da pessoa; gera a máscara) ou `"topo"` (metade de cima da dividida: 720 px de largura, com laterais do mesmo vídeo borradas) |
| `x`, `y`, `w`, `h` | posição e tamanho na tela; `h` sai da proporção quando falta |
| `rot`, `raio`, `sombra` | giro em graus, canto arredondado (px) e sombra (0 a 1) |
| `entra`, `sai` | `{"efeito": "pop", "dur": 0.18}` (escala 0,82→1 com alfa) ou só o número (alfa) |
| `legenda` | cria uma faixa da legenda no tempo da camada (`"some"`, `"alto"` ou um número) |
| `aceito` | motivo; silencia zona segura e réguas desta camada |

Por tipo:

- `video`: `arquivo`, `src` (segundo do arquivo de origem), `audio` (ganho em dB; `null` ou ausente = mudo)
  e `recorte`: caixa fixa `[x, y, w, h]` do arquivo de origem, ou lista `[{"t": 0, "caixa": [...]},
  {"t": 1.0, "caixa": [...]}]` com `t` relativo ao início da camada (o "aberto e depois o zoom seco"). Cada
  item pode trazer `src` (recomeça a origem ali) e `dur` (segundos de origem; depois segura o último
  quadro). `dur` também vale na camada.
- `imagem`: `arquivo` (PNG com transparência ou JPG).
- `faixa`: `texto`, `y` (alto da caixa), `x` (padrão: centrada), `largura` (898), `altura` (104), `raio`
  (17), `fundo` (#FCFCFC), `tinta` (#111111), `fonte`, `tamanho` (58; encolhe até caber).
- `html`: `modelo` (um `.html` de 1080×1920 com fundo transparente, por exemplo `marca/letterings/numero.html`)
  e `campos` (`{{campo}}` no modelo vira o texto, escapado). Todo campo do modelo vai em `campos`; o opcional,
  com `""`. Fontes e imagens do modelo valem relativas à pasta dele. Modelo que se arruma por script marca
  `document.body.dataset.pronto` no fim, e a foto espera por isso (contrato, seção 4.2).

Arquivo de `brutos/` precisa de uma linha em `brutos/fontes.md` com o nome dele.

## insercoes (cartões)

```json
"insercoes": [
  {"tipo": "lista", "de": "F12", "ate": "F14:fim", "titulo": "Três *erros*",
   "itens": [{"texto": "Preço sem conta", "t": "F12:preço"}, {"texto": "Vitrine apagada", "t": "F13"}]},
  {"tipo": "numero", "de": 42.9, "ate": 45.0, "numero": "+100 mil", "texto": "produtos vendidos"},
  {"tipo": "comparacao", "de": 80.5, "ate": 86.4, "t_direita": 84.5,
   "esquerda": {"titulo": "A marca diz", "texto": "você desconfia"},
   "direita": {"titulo": "Gente como você", "texto": "você confia"}},
  {"tipo": "etapas", "de": 20, "ate": 25, "titulo": "Como fazer", "itens": ["Grave", "Corte", "Poste"]},
  {"tipo": "print", "de": 35.2, "ate": 38.6, "imagem": "prints/marca.png", "marca": "Marca", "endereco": "marca.com.br"},
  {"tipo": "frase", "de": 75.3, "ate": 77.6, "texto": "Conformidade *social*"},
  {"tipo": "imagem", "de": 90, "ate": 92, "imagem": "geradas/cena.png"},
  {"tipo": "dividida", "de": 0, "ate": 3.1, "imagem": "../brutos/imagens/gancho.jpg",
   "faixa": "Lojinha de rua virou coisa de pobre?", "recorte_y": 280},
  {"tipo": "titulo", "de": 5.9, "ate": 9.2, "texto": "R$ 18 milhões", "tamanho": 150, "y": 300},
  {"tipo": "colagem", "de": 26.9, "ate": 33.1, "pecas": [
    {"imagem": "../brutos/imagens/produto-1.png", "estilo": "recorte", "x": 650, "y": 300, "largura": 380, "rot": 8, "t": 26.95},
    {"imagem": "../brutos/imagens/produto-2.png", "x": 90, "y": 320, "largura": 290, "rot": -8, "t": 29.9}]},
  {"tipo": "colagem", "de": 33.2, "ate": 36.9, "legenda": "alto", "pecas": [
    {"imagem": "prints/noticia.png", "estilo": "noticia", "x": 250, "y": 1130, "largura": 580, "rot": -3}]}
]
```

- `*palavra*` em texto de cartão sai na fonte e na cor de destaque.
- `"formato": "painel"` põe o cartão numa caixa no alto (a partir de y 260), com o vídeo em volta; sem ele,
  o cartão ocupa a tela toda e a legenda continua por cima. Painel só quando o rosto fica abaixo da caixa.
- Item de lista ou etapa sem `"t"` entra sozinho, espalhado na primeira metade da inserção.
- `titulo`: `texto`, `tamanho` (92) e `y` (alto da frase, 260). Conceito e número grande, sem caixa.
- `colagem`: `pecas`, cada uma com `imagem`, `estilo` (`"recorte"`: PNG sem fundo com sombra; `"foto"`:
  canto arredondado; `"noticia"`: print em papel branco), `x`, `y`, `largura`, `rot`, `t` e `rotulo`
  (opcional). `texto` (opcional) põe uma frase no alto, em `y_texto` (260).
- `dividida` (cartão): `imagem` na metade de cima, `faixa` (texto na faixa branca) e `recorte_y`. A legenda
  some nesse trecho. Para vídeo em cima ou pessoa menor, use `divididas` + camada `topo`.
- `"legenda"`: `"alto"`, `"some"` ou um número muda a legenda só naquele trecho.
- `"nota"` guarda a frase da fala que justifica o cartão; o script ignora. `"aceito"` silencia os avisos dele.

## Saídas

- `<vídeo>-insercoes.mp4`, `legenda-curta.srt`, `cartoes.png`, `quadros/folha.jpg`.
- `.dados/geometria.json`: tudo o que foi desenhado, no tempo final, para a `/criticar` medir (formato no
  contrato, seção 4.3): legendas com `destaque`, cartões com `lugar: "cartao"`, camadas com a caixa
  `[x, y, w, h]` e o `texto` de faixa e html, divididas com `corte`, `laterais` e `pessoa`, `aceito` onde houver
  e a `zona_segura`.
- `.dados/mascaras/m-<q0>-<q1>-<motor>.mkv`: máscara da pessoa (ffv1 cinza, faixa completa) só nos trechos com
  camada `atras`.
  Motor: `--mascara auto` (padrão: Apple Vision no Mac com chip M e macOS 14+, senão RobustVideoMatting),
  `vision` ou `rvm`. O RobustVideoMatting (Peter Lin, licença GPL-3.0) é baixado na primeira vez do GitHub
  do autor para `~/.cache/claude-skills/inserir/`; o kit não o empacota.
- Código de saída 2: há ATENÇÃO e o vídeo não foi gravado.

## prompts.md

```markdown
# Prompts de imagem e vídeo: <nome do vídeo>

## 00:16 · placas de "aluga-se" (fala: «um monte de placa de aluga-se»)
- Ferramenta sugerida: Nano Banana (imagem) ou Higgsfield (vídeo de 3 s)
- Prompt: <cena, enquadramento vertical 9:16, luz, estilo, o que NÃO pode aparecer>
- Entra como: camada atrás da pessoa, 2 s
```
