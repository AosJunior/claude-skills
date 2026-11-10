# Régua comum dos atos: {{SERIE}}, ep. {{EP}} «{{TITULO_EP}}»

Anúncio vertical 1080×1920 de **{{DURACAO}} s**, pixel art 100 % motion sobre a narração de {{NARRADOR}}, com um trecho
real do vídeo de quem vende (a aula) encaixado em {{AULA}} s. [PREENCHER: personagem, o problema, o que ela tenta, o dilema final.]
Ficção declarada; modo [PREENCHER: voto real | anúncio fechado]. O projeto HyperFrames + GSAP é `sequencia/motion/`, que
é a raiz: os caminhos abaixo são relativos a ela, salvo os absolutos.

O pedido da pessoa: [PREENCHER: a frase dela, literal].

## Leia antes

1. `{{REGUA_SKILL}}`:
   a régua da novela (um foco por quadro, três planos, código de luz, barra, três vozes de texto, cartões, batida presa
   à palavra, conferência por snapshot). Vale primeiro.
2. `{{MOVIMENTO}}`: o movimento (molas, emendas com velocidade herdada, saída em `power3.in`, luz, conferência do
   movimento). A mola está em `assets/mola.js` (`MOLA(papel)`).
3. `{{CONTRATO_HF}}`: o contrato do render do HyperFrames + GSAP (timeline pausada, determinismo, o que animar).
4. `{{COMPONENTES}}/README.md`: a biblioteca `NOVELA` (assinaturas, exemplos e **pontos fracos**).
5. [PREENCHER: a direção aprovada, quadros parados da série].
6. O seu briefing, `briefings/atoN.md`.

## Comando do HyperFrames: um só para todos

```
npx --yes hyperframes@0.9.6 <comando>
```

- `npx --yes hyperframes@0.9.6 check` · `node briefings/conferir-faixa.cjs` (texto de cena abaixo de y 1430)
- `npx --yes hyperframes@0.9.6 snapshot --at <t1>,<t2>,… --no-end` (tempo real; o comando diz a pasta dos PNG)
- Tempo real a partir do tempo do código: `node briefings/tempo-real.cjs <t> …`.

Ninguém renderiza o vídeo (o `entregar.py` renderiza). Ninguém cria um segundo HTML na raiz (quebra o `check` de todos).

## Cores (tokens `--nv-*` do `assets/novela/novela.css`) · luz · sprites

[PREENCHER com a pele da série: tabela de cores por papel, código de luz (quente, fria, chapada), regras de sprite e
cenário (altura de origem, frente, empurrão, três planos). Ponto de partida: `regua-visual.md` desta skill.]

## Zonas seguras

- Cena: y 250–1430, x 72–1008. Legenda: y 1440–1580. Acima de y 230 e abaixo de y 1600 a interface do Instagram cobre;
  em x ≥ 960 entre y 1120 e 1600, os botões. Nada de texto fora da zona da cena.
- **A barra ocupa y 240–360** sempre que está na tela (tabela da barra): nada de texto nem rosto nessa faixa nesses
  intervalos.

## Três vozes de texto e um foco por quadro

- **Legenda** (a fala do narrador, camada própria), **etiqueta** (o fato) e **balão** (a fala da personagem). Nunca as
  três ao mesmo tempo: legenda + uma. Um protagonista por quadro, maior, na frente e mais nítido.

## Tempo de leitura

Segure **0,5 s + 0,3 s por palavra** antes de trocar uma etiqueta, tirar um balão ou sair de uma tela de texto. Quando a
próxima batida chega antes, a etiqueta entra mais cedo (na palavra anterior) ou troca no lugar, em vez de sair e entrar.

## Janelas dos atos

Tempo do código = tempo real enquanto o `voz.js` estiver vazio. Cada janela vai do início do primeiro bloco do ato ao
início do ato seguinte **+ 0,30 s**. Tabela GERADA pelo `montar_projeto.py` (não edite entre os marcadores):

<!-- novela:janelas -->
<!-- /novela:janelas -->

## Contrato de emenda entre atos

- **Quem faz a transição: o ato que ENTRA** (`NOVELA.chicote.entra(camada, { direcao: "esq" })`, 0,26 s, ou o corte de
  0,02 s) sobre uma camada própria (`div.nv-camada`, nunca o hospedeiro `.clip`), opaco, até 0,30 s.
- **O ato que SAI segura o último quadro** de T até o fim da janela (T + 0,30): nenhuma saída nem `chicote.sai`.
  Etiquetas e balões saem até T. Nada do ato aparece depois da janela dele.
- **A barra não é de nenhum ato**: ela atravessa as emendas parada.

[PREENCHER: tabela «fronteira · T · o que o ato que sai entrega · o que o ato que entra recebe e faz».]

## A barra de jogo (camada da sessão, `compositions/barra.html`)

Nenhum ato desenha barra, relógio ou medidor no topo. Eventos GERADOS pelo `montar_projeto.py` da lista `barra` do
`roteiro.json` (tempos do código, pela palavra que causa cada mudança):

<!-- novela:barra -->
<!-- /novela:barra -->

## Legenda (camada da sessão)

Gerada por `node briefings/legenda-novela.cjs …` com os flags que o `montar_projeto.py` imprime (palavras-chave dos
blocos e trechos fora, do `roteiro.json`). Nenhum ato mexe na legenda; se um texto seu disputa com ela, avise no resumo.

## Contrato da composição

- Tudo dentro do `<template>` do seu `compositions/atoN.html` (já criado, vazio e válido). Raiz `NOVELA.raizDe("atoN")`,
  nunca `document`. Monte dentro de `NOVELA.pronto(() => { … })` e registre `window.__timelines["atoN"] = tl` **no fim**.
- Tempo: `const a = (t) => +(VOZ.w(t) - T0).toFixed(3)` (já no esqueleto) e `tl.add(componente.metodo(), a(<palavra>))`.
- Ids e classes com o prefixo do ato. Assets novos só em `assets/atoN/`.
- Sem tween de duração zero (corte = 0,02 s), sem `Date.now`, `Math.random`, rede, `play()`. Só transform, opacidade,
  filtro, clip e variáveis CSS animam. Sem emoji no texto de tela. Perfil e app de mensagens desenhados por nós.
- Nada de afirmação nova: só os textos do seu briefing (do `roteiro.json`), na forma exata.
- Roleta só no relógio e no medidor da barra; se girar algum número, registre no seu bloco do `assets/roletas.js`.

## Como conferir

1. `npx --yes hyperframes@0.9.6 check` e `node briefings/conferir-faixa.cjs` na raiz: sem erro do seu arquivo.
2. Snapshot nas palavras-gatilho do seu briefing, mais T − 0,2 e T + 0,1 das suas fronteiras. Abra cada PNG e confira.
3. Não renderize o vídeo. Você não fala com a pessoa e não abre arquivo para ela.
