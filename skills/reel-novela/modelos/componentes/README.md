# Componentes da novela

> **De onde veio:** feita e aprovada em uso no ep. 1 da primeira série feita com esta skill. Cada série copia esta
> pasta para `<pasta da série>/componentes/` e passa `--componentes <pasta da série>/componentes` ao `montar_projeto.py`.
> **Cores:** são tokens (`--nv-*` em `novela.css`, com uma pele neutra da skill: fundo escuro, um acento quente, um
> frio, vermelho e verde de estado). Troque os valores pela pele de cada série, sem mexer no `novela.js` (ele lê os
> tokens), e meça de novo cada par texto × fundo: todo texto fica em 4,5:1 ou mais.
> **Comando:** `npx --yes hyperframes@0.9.6 check` e `npx --yes hyperframes@0.9.6 snapshot --at <t1>,<t2> --no-end` (HyperFrames 0.9.6); o `sincronizar.py` copia tudo para o projeto de `sequencia/motion/`.

Biblioteca de motion da série (HyperFrames + GSAP, 1080×1920) para os agentes de ato, feita pela régua da skill
(`referencias/regua-visual.md`). O movimento segue `referencias/movimento.md` da skill. Os exemplos abaixo usam a série
inventada do fim de `modelos/biblia.md`.

| Arquivo | O que é |
|---|---|
| `novela.js` | todos os componentes, em `window.NOVELA` |
| `novela.css` | estilo, tokens `--nv-*` (pele de exemplo + vermelho de alarme) e a Montserrat |
| `legenda.html` | a composição da legenda da novela (substitui a do esqueleto) |
| `fontes/` | Montserrat 400, 700 e 900 (OFL), tiradas da cópia embutida no HyperFrames 0.9.6 |
| `iluminar.py` | pinta a luz do lugar no sprite: `quente`, `fria`, `tela-azul` |
| `sincronizar.py` | copia tudo para um projeto de episódio (Python 3.9+, Mac e Windows) |

## Pôr num episódio

1. O `montar_projeto.py` já copia tudo para o projeto. Depois de mexer na biblioteca da série, rode
   `python3 componentes/sincronizar.py <epNN>/sequencia/motion` (copia `novela.css` e `novela.js` para `assets/novela/`,
   `legenda.html` para `compositions/` e as fontes para `assets/fontes/`; a mola vem do esqueleto). Edite sempre na
   biblioteca e sincronize de novo; a cópia do projeto é sobrescrita.
2. O `index.html` do esqueleto já carrega `assets/novela/novela.css`, `assets/novela/novela.js` e as três `@font-face`
   da Montserrat.
3. Sprite com a luz do lugar, antes de copiar para `assets/elenco/` (precisa de numpy e Pillow; com o uv:
   `uv run --with numpy --with pillow python …`):
   `python3 componentes/iluminar.py elenco/bia/poses/festa-copo.png <projeto>/assets/elenco/bia-festa-copo-quente.png --perfil quente --fim-visivel 480`
   (`--fim-visivel` = a última linha do sprite que aparece no quadro, para a luz de baixo; no busto, a cintura).

## Contrato

- Cada função monta o DOM dentro de `pai` e devolve um objeto cujos métodos **devolvem uma timeline solta**. A cena
  põe cada uma na própria timeline com `tl.add(x, a(t))`. Solta quer dizer fora do relógio global: só anda dentro da
  cena (testado). Chame os métodos na ordem do tempo: cada um continua do estado que o anterior deixou.
- Monte a cena dentro de `NOVELA.pronto(() => { … })` (espera a Montserrat, para medir texto; a medida em si usa
  `NOVELA.visivel`, que funciona também com o ato fora da janela) e registre
  `window.__timelines["<id>"]` **no fim** do callback. A raiz da composição é `NOVELA.raizDe("<id>")`: o
  `document.querySelector("#root…") || document` do esqueleto cai no `document` e quebra o `appendChild`.
- Tempo: o `a()` da cena (VOZ.w) vale para a posição do `tl.add`. Dentro do componente as durações são fixas.
- Sem tween de duração zero: «corte» é 0,02 s. Só transform, opacidade, filtro, clip e variáveis CSS animam.
- Pixel art com `image-rendering: pixelated` (sprites, avatar, emotes em SVG `crispEdges`).
- Zonas: cena em y 250–1430; legenda em y 1440–1580; a barra (y 240–360) e o telefone grande (até y 1642) são as
  exceções planejadas. Texto abaixo de 1430 só a pergunta do cartão, que já leva `data-layout-allow-caption-zone`.

## Componentes

Assinaturas (pai = elemento onde monta; x, y em px do quadro 1080×1920):

| # | Função | Devolve |
|---|---|---|
| 1 | `NOVELA.legenda(palco, grupos, {base, corpo, min, largura, max, acende, pausa, fimJanela})` | a timeline da legenda (usada por `legenda.html`) |
| 2 | `NOVELA.etiqueta(pai, {texto, cor, x, y, giro, corpo, largura})` | `entrada()`, `trocar(texto, cor)`, `saida()` |
| 3a | `NOVELA.balao(pai, {texto, x, y, lado, corpo, largura})` | `entrada()`, `saida()` |
| 3b | `NOVELA.emote(pai, {tipo, x, y, escala})` | `entrada()`, `saida()` |
| 4 | `NOVELA.barra(pai, {y, dias, rotuloDias, unidade, rotulo, valor})` | `entradaRelogio()`, `entradaMedidor()`, `saida()`, `volta()`, `medir(valor, {de, ate, semente})`, `contar(dias)` |
| 5 | `NOVELA.cena(pai, {fundo, frente, sprites, foco, luz, reforco})` | `entrada()`, `saida()`, `empurrao(dur, {ate, dx, dy, ease})`, `rosto({x, y, escala, centro, pose})`, `abrir()`, `pose(id, nome)`, `recorte(ids, {escurece, desfoque, contorno})`, `soltar()`, `entrar(id, {de})`, `sair(id)` |
| 6 | `NOVELA.chicote(sai, entra, {direcao, dur, borrao})` · `.sai(el, op)` · `.entra(el, op)` · `NOVELA.corte(sai, entra)` · `.sai(el)` · `.entra(el)` | a timeline da transição |
| 7 | `NOVELA.telefone(pai, {tamanho, miolo, hora, rotulo, chapada, conversa, perfil, post, video})` | `entrada({sobe})`, `saida({desce})` e, por miolo: `mensagem(i)`, `digitando(i, dur)` · `destacar(i)` · `teia()` |
| 8a | `NOVELA.cartaoMedidor(pai, {rotulo, valor, sprite})` | `entrada()`, `saida()` |
| 8b | `NOVELA.cartaoOpcoes(pai, {faixa, esq, dir, pergunta})` | `entrada()`, `pergunta()`, `saida()` |

### 1. Legenda

Caixa-alta Montserrat 900, branca com contorno escuro de 13 px, linha de base em y 1560, dentro de x 110–950. Palavra
por palavra como na referência: cada uma aparece seca no início dela e a linha se recentra; 1 a 3 palavras. Os grupos
continuam saindo do `briefings/legenda-grupos.cjs` do esqueleto (que agrupa de 2 a 4): a `legenda.html` divide ao
meio os de 4 (`MAX = 3` no topo dela), sem mexer no script. Cores pelo script: `--a` palavra-chave (vermelho
`--nv-alarme-vivo`), `--b` nome ou número em destaque (ouro, `--nv-ouro-vivo`), `--e` palavra do CTA (vermelho, 1,12 em). Se a última fala termina
mais de 1,5 s antes do fim da janela, a última linha sai 0,35 s depois dela (os cartões do fim ficam limpos).

```sh
node briefings/legenda-grupos.cjs --a "mãe,vitrine,nunca" --b "Bia,Lurdes" --sem 47.7-56.2,59.9-62.5,69.9-79.5
```

### 2. Etiqueta inclinada

Caixa com sombra dura deslocada; `cor`: `vermelha` (fato contra), `dourada` (número), `azul` (nome), `verde`
(estado bom), `creme` (pergunta), `escura` (faixa). `x, y` = centro; `giro` em graus (positivo desce para a direita). Entra num «pop» de
0,55 a 1 em mola curta; `trocar` dobra a face em Y e abre a nova no mesmo centro, texto e cor juntos.

```js
const et = NOVELA.etiqueta(R, { texto: "3 PEDIDOS NO MÊS", cor: "vermelha", x: 540, y: 1180, giro: 5, corpo: 72 });
tl.add(et.entrada(), a(5.4));
tl.add(et.trocar("2 SÃO DA MÃE", "dourada"), a(6.6));
tl.add(et.saida(), a(8.0));
```

### 3. Balão de fala e emotes

`x, y` = a ponta do rabo, logo acima da cabeça de quem fala. `lado`: `centro`, `esq` (quem fala está embaixo à
esquerda), `dir`. Rabo em degraus de 9 px; a escala nasce na ponta. Emote: `gota`, `!`, `?` em pixel art; `x, y` =
centro da base; cai de cima em `MOLA("pousar")`. Um emote por vez.

```js
const b = NOVELA.balao(R, { texto: "TÁ BOMBANDO!", x: 520, y: 700, lado: "centro" });
const g = NOVELA.emote(R, { tipo: "gota", x: 700, y: 640 });
tl.add(b.entrada(), a(0.3));
tl.add(g.entrada(), a(1.2));
tl.add(b.saida(), a(2.6)); tl.add(g.saida(), a(2.6));
```

### 4. Barra de jogo

Relógio x 72–372 e medidor x 400–1008 (com 72–332, «40 DIAS» vazava da caixa), y 240–360, fundo `--nv-fundo` com borda de 6 px em `--nv-moldura`. Entradas separadas
(cada caixa cai de cima em 0,3 s, como na referência). `medir` anda o trilho em `MOLA("estado")` e gira o
percentual na roleta (`referencias/roleta.md`); `contar` gira os dias. No episódio a barra é **uma camada própria**
(`compositions/barra.html`, um track acima das cenas, janela do vídeo inteiro), porque atravessa as cenas; ela sai
(`saida()`) na aula e no cartão do medidor e volta (`volta()`) no cartão das duas opções.

```js
const barra = NOVELA.barra(R, { dias: 40, rotulo: "CHANCE DE ABRIR A DOCERIA", valor: 2 });
tl.add(barra.entradaRelogio(), a(24.1));
tl.add(barra.entradaMedidor(), a(28.9));
tl.add(barra.medir(5, { semente: 41 }), a(40));
tl.add(barra.saida(), a(47.5));
```

### 5. Cena ilustrada

Três planos: fundo (desfoque e brilho por `--nv-desf` e `--nv-luz`), meio (sprites, com sombra de contato quando os pés
aparecem) e frente (opcional, imagem do tamanho do fundo com alfa só no objeto cortado embaixo). `fundo`/`frente`:
`{src, tamanho:[w,h] (padrão 1520×2688), escala, fx, fy, desfoque, luz}` (fx, fy como `background-position`).
`sprites`: `[{id, poses:{nome: src} (ou src), pose, x (centro), topo, altura, sombra, entra:{de, atraso}}]`.
`empurrao` escala os planos a 0,4 · 0,7 · 1,0 do movimento (fundo, personagem, frente). `rosto` é um corte seco para um
recorte mais fechado (a câmera salta, sem animar escala), com troca de pose opcional; o empurrão continua por baixo.
`recorte` escurece e desfoca o fundo, apaga quem não é recortado e acende o contorno branco do recortado. A luz vem
pintada no sprite (`iluminar.py`); `luz` + `reforco` (0 a 1) acendem um radial suave da mesma cor atrás.

```js
const c = NOVELA.cena(R, { fundo: { src: "assets/cenarios/festa.png", escala: 1.25, fy: 0.42, desfoque: 6, luz: 0.8 },
  sprites: [{ id: "bia", poses: { copo: "assets/elenco/bia-festa-copo-quente.png", nuca: "assets/elenco/bia-festa-nuca-quente.png" }, x: 500, topo: 700, altura: 1560 }] });
tl.add(c.empurrao(5.2, { ate: 1.06, dx: -24 }), a(0));
tl.add(c.rosto({ x: 505, y: 1090, escala: 1.6, centro: [540, 800], pose: ["bia", "nuca"] }), a(5.2));
tl.add(c.recorte("bia"), a(36.1));
```

### 6. Transições

Chicote: os dois quadros andam juntos de lado, como uma faixa, em `power3.inOut`, 0,26 s, com borrão só na horizontal
(filtro SVG `feGaussianBlur` com desvio «70 0» no meio). `direcao: "esq"` = o novo vem da direita. Corte seco: 0,02 s.
Cenas em composições diferentes chamam cada uma a sua metade no mesmo instante (a da saída no fim da janela dela,
a da entrada no começo da sua, com a janela de uma sobreposta à outra pela duração do chicote).

```js
tl.add(NOVELA.chicote(grupoFesta, grupoCozinha, { direcao: "esq" }), a(8.1));
// em composições separadas, sobre uma camada da cena (div.nv-camada), nunca sobre o hospedeiro .clip:
tl.add(NOVELA.chicote.sai(camada, { direcao: "esq" }), a(8.1));   // na cena que sai
tl.add(NOVELA.chicote.entra(camada, { direcao: "esq" }), 0);      // na cena que entra
tl.add(NOVELA.corte(grupoA, grupoB), a(42.1));
```

### 7. Telefone

Tela chapada da pele (grade de pontos) com o aparelho desenhado por nós, sem logo nem interface copiada.
`tamanho: "conversa"` (corpo x 200–880, y 390–1430, abaixo da barra) ou `"grande"` (vídeo 9:16 de 720×1280, corpo
até y 1642; a barra e a legenda saem). Miolos:

- `conversa: {contato, sub, avatar:{iniciais, cor} ou {src, tamanho, posicao}, mensagens:[{de:"eles"|"eu", texto, hora}]}`
  → `mensagem(i)`, `digitando(i, dur)` (bolha de três pontos no lugar da mensagem i e «digitando…» no topo).
- `perfil: {usuario, nome, bio, posts, seguidores, seguindo, avatar, botao, grade:[{cor, texto, views}]}` → `destacar(i)`.
- `post: {usuario, avatar, cor, texto, views, legenda, insights}` → `teia()` (a teia de aranha se desenha sobre o botão).
- `video`: a composição escreve o `<video>` no HTML dela (`class="clip"`, `muted`, `playsinline`, `data-start` e
  `data-duration` no tempo da composição, `data-track-index`) e passa o elemento; o componente só o põe na tela.
  Nunca `play()` nem seek. O som da aula vai na narração (pausa do `pausa.py`), não no `<video>`.

```js
const cel = NOVELA.telefone(R, { tamanho: "conversa", miolo: "conversa", hora: "21:12",
  conversa: { contato: "Seu Orlando · Ponto", avatar: { iniciais: "SO", cor: "#7a4a24" },
    mensagens: [{ de: "eles", texto: "Bia, o sinal do ponto vence em 40 dias.", hora: "21:12" }, { de: "eles", texto: "Fecha?" }] } });
tl.add(cel.entrada(), a(22.2)); tl.add(cel.mensagem(0), a(22.5));
tl.add(cel.digitando(1, 0.7), a(23.2)); tl.add(cel.mensagem(1), a(23.9));
```

```js
const aula = NOVELA.telefone(R, { tamanho: "grande", miolo: "video", video: R.querySelector("#aula"), rotulo: "VITRINE CHEIA" });
tl.add(aula.entrada(), 0);
```

Para trocar de miolo no mesmo aparelho (conversa → perfil → post), monte um telefone por miolo e corte entre eles:
`tl.add(c1.saida({ desce: false }), t); tl.add(c2.entrada({ sobe: false }), t);`.

### 8. Cartões

Cartão do medidor: tela cheia sem barra, rótulo em duas linhas, trilho que se desenha, nível em `MOLA("estado")`,
percentual vermelho inclinado em «pop» e a personagem pequena embaixo (`sprite: {src, altura, x (esquerda), topo}`).
`atrasoPct` (padrão 0,72 s) põe o pouso do percentual na palavra dele: entrada na palavra que abre o cartão e
`atrasoPct` = a diferença até a palavra do número .
Cartão das duas opções: geometria da régua («Cartão das duas opções») na dupla clara (`--nv-quente-claro` + `--nv-frio`, mesmo peso, texto em `--nv-tinta`).
`esq`/`dir`: `{nome, acao, custo, sprite:{src, altura}}`. Entrada medida na referência: as metades entram das bordas
para o centro em 0,3 s (o vão é claro), a faixa abre em X, nomes e «OU» pousam no fecho, as personagens caem de cima,
a da direita 0,17 s depois. `pergunta()` é separada, para cair na palavra.

```js
const card = NOVELA.cartaoOpcoes(R, { pergunta: "ENCARA OU APAGA?",
  esq: { nome: "ENCARA", acao: "ABRE OS NÚMEROS DOS POSTS ANTIGOS", custo: "A RAFA VÊ O PERFIL COMO ESTÁ", sprite: { src: "assets/elenco/bia-folha-telefone.png", altura: 480 } },
  dir: { nome: "APAGA", acao: "APAGA TUDO ANTES QUE A RAFA VEJA", custo: "NUNCA SABER O QUE ERROU", sprite: { src: "assets/elenco/bia-folha-dedo.png", altura: 480 } } });
tl.add(card.entrada(), 0);
tl.add(card.pergunta(), a(71.2));
```

## Movimento medido nas séries que medimos (quadro a quadro a 30 fps)

| O quê | Medida | No componente |
|---|---|---|
| Balão | de ~45 % a ~105 % da escala em 2 a 3 quadros (0,07–0,1 s), ancorado na ponta do rabo, e assenta | `pop` 0,45 → 1, mola de 0,24 s |
| Etiqueta | no mesmo quadro do corte para o rosto ela nasce pequena (~50 %) e fica cheia no quadro seguinte | `pop` 0,55 → 1, mola de 0,22 s |
| Corte para o rosto | corte seco (sem zoom animado), seguido do empurrão lento | `rosto()` em 0,02 s; o empurrão continua |
| Chicote | 4 a 5 quadros (0,13–0,17 s) de deslize lateral com borrão horizontal; o novo vem da direita | 0,26 s em power3.inOut, borrão «70 0» |
| Barra | cai de cima em 6 a 7 quadros (~0,22 s) logo depois do chicote; a personagem entra ~0,3 s depois | queda em mola de 0,32 s; `entra.atraso` 0,3 |
| Legenda | palavra a palavra, sem fade, a linha recentra; 1 a 3 palavras | idem, 0,05 s por palavra |
| Cartão das duas opções | metades das bordas ao centro em ~9 quadros; faixa abre em ~6; nomes e «OU» no fecho; personagens caem em ~8 quadros, a 2ª 5 quadros depois; a pergunta ~0,8 s depois | idem |

## Pontos fracos (leia antes de usar)

- **Frente derivada.** Se a série ainda não tem a frente gerada de cada cenário, use uma frente recortada
  da faixa de baixo do próprio fundo (`assets/cenarios/<lugar>-frente.png`, corte em linha reta com 10 px de
  degradê). Com empurrão forte (acima de 1,06) ou `dx` grande, a borda do balcão pode dobrar. A frente certa é uma
  geração própria com alfa (régua, «Três planos»).
- **Avatar** recortado da pose por `background-size` e `background-position`: cada pose pede um ajuste
  (`tamanho: "135%", posicao: "50% 11%"` serviu para uma folha em pé neutra).
- **Chicote** aplica um filtro SVG ao elemento que se move e ele fica ligado (em 0) até o fim da cena. O render
  não sentiu, mas evite chicote sobre elemento com vidro ou muitos filtros.
- **Roleta da barra** roda numa timeline solta: o `roleta-ticks.cjs` não a vê. Para ter o som dos tiques, registre o
  mesmo número em `assets/roletas.js` e use `ROLETA.animar` direto, ou ponha o som à mão pelo instante do `medir`.
- **Emoji** no texto do telefone cai na fonte do sistema e não foi testado no render; prefira texto sem emoji ou
  desenhe o ícone.
- **Legenda**: os grupos ainda saem do `legenda-grupos.cjs`, que mede a largura pelo Inter. A linha da novela se ajusta
  sozinha no navegador (corpo de 62 até 44 px), mas o aviso de largura do script não vale para ela.
- **Check**: a `nested_media_start_basis_ambiguous` do `<video>` dentro da composição é aviso esperado (o tempo é
  local). Com o `--caption-zone` do `conferir-faixa`, o check lia etiqueta e percentual (âncora girada de tamanho
  zero) como cobertos; eles levam `data-layout-allow-occlusion`.
- **Tempos curtos de teste** geram `line_unread` no check: no episódio o tempo vem da fala; segure 0,5 s + 0,3 s
  por palavra antes de trocar uma etiqueta ou sair de uma tela de texto.

## Medida dentro de um ato

Numa composição de ato que não começa em 0, o hospedeiro (`.clip` do `index.html`) está com `display:none` quando a
cena monta, e `offsetWidth`/`offsetHeight` dão 0. Por isso a biblioteca mede tudo por `NOVELA.visivel(el, fn)`, que põe
`display:block` nos ancestrais ocultos só durante a medida (síncrono, sem pintura no meio) e devolve o estilo como
estava: etiqueta longa encolhe, perfil e post empilham e os cartões se medem sozinhos, mesmo num ato que começa depois
de 0. Nenhum agente de cena precisa de posição fixa nem de `ajusta()` por canvas. Se medir por conta própria dentro de
uma cena (um `offsetHeight` seu), embrulhe em `NOVELA.visivel(elemento, () => …)`.
