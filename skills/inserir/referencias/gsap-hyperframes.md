# GSAP no HyperFrames: o que vale para Reel

Destilado das 8 skills oficiais `greensock/gsap-skills` (versão de 21/04/2026, iguais às instaladas) e do adaptador
GSAP do HyperFrames (`hyperframes-animation/adapters/gsap*.md`). Quando houver conflito, vale o HyperFrames: o vídeo
é renderizado buscando um tempo por vez, então todo quadro tem que sair só do tempo.

## O que usar das skills do GSAP

| Skill | Para Reel | Uso |
|---|---|---|
| `gsap-core` | sim | `to`, `from`, `fromTo`, `set`, eases, stagger, aliases de transform, `autoAlpha` |
| `gsap-timeline` | sim, é a base | uma timeline pausada, posição por tempo da palavra, labels por cena |
| `gsap-plugins` | parte | SplitText (legenda e títulos por palavra), DrawSVG e MorphSVG (diagramas), CustomEase (mola própria) |
| `gsap-utils` | parte | `mapRange`, `clamp`, `interpolate`, `snap`, `distribute` para posições e contadores |
| `gsap-performance` | parte | transform e opacidade em vez de layout; stagger em vez de tweens soltos |
| `gsap-scrolltrigger`, `gsap-react`, `gsap-frameworks` | não | não há rolagem nem framework no render |

Plugins que dependem de interação (Draggable, Inertia, Observer, ScrollSmoother, `quickTo`) não servem: o render não
tem mouse nem rolagem. Todos os plugins são gratuitos e vêm no pacote `gsap`; nunca peça token ou Club GSAP.

## Contrato do render (não negociável)

- Cada composição tem **uma** `gsap.timeline({ paused: true })`, registrada em `window.__timelines["<id>"]` com o
  mesmo id do `data-composition-id`, só depois de pronta (pode montar dentro de `document.fonts.ready`).
- Nunca `tl.play()`, `Date.now()`, `performance.now()`, `Math.random()` sem semente, rede na hora do render ou
  `repeat: -1` sem `data-duration` finito na raiz.
- A duração do vídeo vem do `data-duration` da raiz, não do tamanho da timeline. Não estique com tween vazio.
- Nunca anime `display`, `visibility` ou `autoAlpha` num elemento `.clip`: anime um filho.
- Não centralize com `transform: translate(-50%,-50%)` num nó que o GSAP move: use flex/`inset` ou `xPercent`.
  Estado inicial vai dentro do `fromTo`, não no CSS.
- Dois `from()` na mesma propriedade do mesmo elemento: `immediateRender: false` no segundo.
- Uma propriedade, uma timeline: duas timelines mexendo no mesmo `x` ao mesmo tempo dão quadros diferentes a cada
  render.
- `<audio>` sempre com `id`, senão o render sai mudo. Nada de `crossorigin` em mídia.
- Fonte com nome precisa de `@font-face` para um arquivo da pasta. Para o kit, só fontes livres: Inter, Source Serif,
  EB Garamond, JetBrains Mono e as que vêm no HyperFrames. SF Pro e New York são da Apple e não vão no kit.

## Fala → tempo

- As palavras com tempo saem da `/decupar` (`.dados/palavras.json`, já no tempo do corte) ou de
  `npx hyperframes transcribe <arquivo> --json --language pt --model small`. **Sem `--language pt` o padrão
  `small.en` traduz a fala para o inglês.**
- Cada coisa dita entra na palavra em que é dita: posicione o tween no `start` da palavra
  (`tl.from(el, {...}, palavra("Senado").start)`). Uma função `palavra(texto, n)` que acha a n-ésima ocorrência
  substitui o antigo `M.acha`.
- Labels por cena (`tl.addLabel("plenario", t)`) deixam o roteiro legível e a revisão por trecho barata.

## Movimento com cara de produto (substitui as molas próprias)

- Mola pela razão de amortecimento: 1,0 não quica; **0,7–0,85 é o premium (padrão)**; 0,4–0,6 brincalhão. Posição e
  tamanho podem quicar; opacidade e cor nunca. Mais perto disso no GSAP: `back.out(1.4)` e `elastic.out(1, 0.5)`.
  Para a mola exata, um `CustomEase` gerado de uma mola fechada em `t` (determinística).
- Ease por papel: chegada com cauda longa (`expo.out`, `power4.out`); câmera e cor `power2.inOut`; saída acelerando
  (`power3.in`). O mesmo `power2.out` em tudo é o padrão que denuncia vídeo gerado.
- Movimento rápido de 0,3–0,6 s; saída 40–50 % mais curta que a entrada; o próximo elemento entra quando o anterior
  está 30–50 % feito. Stagger: letras 1 quadro, palavras 60–120 ms, itens de lista 40–80 ms.
- Título que pousou fica parado; o movimento passa para o próximo elemento. Nada de flutuar, pulsar ou respirar.
- Leitura: segura 0,5 s + 0,3 s por palavra; a última linha do vídeo, 2 s ou mais.
- 3 a 5 tipos de transição por vídeo, cada uma causada por algo na tela (zoom por um botão, objeto vira o mundo,
  morph, cor que inunda, chicote). No máximo um terço das emendas em corte seco.
- Contador: `tl.to(el, { innerText: 115000, snap: { innerText: 1 } }, t)`.
- Legenda e título por palavra: SplitText (`type: "words"`), com blur 6 px → 0 e opacidade 0 → 1 em 0,13 s.

## Conferir sem gastar

- `npx hyperframes check`: lint, runtime, layout e contraste num passo. Com erro de lint, os outros não rodam e
  "0 samples" não quer dizer limpo.
- `npx hyperframes snapshot --at <t1>,<t2>,<t3>`: 3 quadros-chave por cena, nunca a sequência inteira.
- `npx hyperframes keyframes` mostra onde cada tween começa e acaba sem renderizar.
- `npx hyperframes preview --background` abre o Studio para a pessoa ver e mexer.
- `npx hyperframes render` só depois do sim, uma vez.
