# GSAP no HyperFrames: o contrato do render

O resumo do que vale para a novela, destilado das skills oficiais do GSAP e do adaptador GSAP do HyperFrames (as
cópias estão em `gsap/` e `hyperframes/`, com fonte e licença no [`LEIA-ME.md`](LEIA-ME.md)). Quando houver
conflito, vale o HyperFrames: o vídeo é renderizado buscando um tempo por vez, então todo quadro sai só do tempo.
O movimento (mola, emenda, luz) está em [`movimento.md`](movimento.md); onde as cópias de terceiros falam de mola ou
ease, vale o `movimento.md`.

## Comando

Um só para todos, com a versão travada: `npx --yes hyperframes@0.9.6 <comando>`, na raiz do projeto motion
(`epNN/sequencia/motion/`). As cópias de `hyperframes/` são de uma versão anterior (0.8.200); o que mudou de uma para
outra, o `--help` do comando diz.

## O que usar das skills do GSAP

| Skill | Para a novela | Uso |
|---|---|---|
| `gsap-core` | sim | `to`, `from`, `fromTo`, `set`, eases, stagger, aliases de transform, `autoAlpha` |
| `gsap-timeline` | sim, é a base | uma timeline pausada por ato, posição pelo tempo da palavra |
| `gsap-plugins` | parte | CustomEase (curva própria); SplitText só se o componente pedir |
| `gsap-utils` | parte | `mapRange`, `clamp`, `interpolate`, `snap` para posições e contadores |
| `gsap-performance` | parte | transform e opacidade em vez de layout |
| `gsap-scrolltrigger`, `gsap-react`, `gsap-frameworks` | não | não há rolagem nem framework no render |

Plugins de interação (Draggable, Inertia, Observer, ScrollSmoother, `quickTo`) não servem: o render não tem mouse nem
rolagem. Todos os plugins são gratuitos e vêm no pacote `gsap`. A biblioteca não vem copiada na skill: o `montar_projeto.py` a baixa do pacote oficial, na versão 3.14.2, para `assets/gsap.min.js` do projeto.

## Contrato do render

- Cada composição tem **uma** `gsap.timeline({ paused: true })`, registrada em `window.__timelines["<id>"]` com o
  mesmo id do `data-composition-id`, só depois de pronta (na novela, no fim de `NOVELA.pronto(() => { … })`).
- Nunca `tl.play()`, `Date.now()`, `performance.now()`, `Math.random()` sem semente, rede na hora do render ou
  `repeat: -1` sem `data-duration` finito na raiz.
- A duração do vídeo vem do `data-duration` da raiz, não do tamanho da timeline. Não estique com tween vazio, e nada de
  tween de duração zero: o corte é de 0,02 s (tween de duração 0 já quebrou um render).
- Nunca anime `display`, `visibility` ou `autoAlpha` num elemento `.clip`: anime um filho (na novela, uma
  `div.nv-camada`).
- Anime transformação e opacidade: `x`, `y`, `scale`, `rotation`, `autoAlpha`; `clipPath`, filtros, cores e variáveis
  CSS também valem. Barra que cresce é `scaleX` com `transform-origin`; caixa que abre é `clipPath: inset(...)`.
  `left` e `top` dão erro no check (`gsap_non_transform_motion`); `width` e `height` passam no check e tremem no render,
  porque o navegador arredonda o pixel.
- Não centralize com `transform: translate(-50%,-50%)` num nó que o GSAP move: use flex, `inset` ou `xPercent`. Estado
  inicial vai dentro do `fromTo`, não no CSS.
- Uma propriedade, um tween por vez no mesmo alvo. Depois de um `fromTo`, os tweens seguintes dessa propriedade são
  `to`; dois `from()` na mesma propriedade pedem `immediateRender: false` no segundo. Duas timelines no mesmo `x` dão
  quadros diferentes a cada render.
- Vazamento de propósito leva marca: `data-layout-allow-overflow` (brilho, halo), `data-layout-allow-overlap` (texto
  sobre texto de propósito), `data-layout-allow-caption-zone` (a pergunta do cartão final, na faixa da legenda).
- `<audio>` sempre com `id`, senão o render sai mudo. Nada de `crossorigin` em mídia. Vídeo real (a aula) entra como
  `<video>` com `muted`: o som dele já está na narração.
- Fonte com nome precisa de `@font-face` para um arquivo da pasta. Só fontes de licença livre (a biblioteca traz a
  Montserrat, OFL). Fonte do sistema muda de máquina para máquina, e as fontes de sistema dos fabricantes não têm
  licença para vídeo público.

## Fala → tempo

- O tempo de cada palavra vem do `briefings/palavras-voz.json`, do alinhamento forçado ([`voz.md`](voz.md)).
- Cada coisa dita entra na palavra em que é dita: o tween vai no início da palavra, pelo `a()` do ato
  (`tl.add(componente.metodo(), a(12.48))`), que passa pelo `VOZ.w` e segue a narração se ela mudar.

## Conferir sem gastar

- `npx --yes hyperframes@0.9.6 check`: lint, runtime, layout e contraste num passo. Com erro de lint, os outros não
  rodam, e «0 samples» não quer dizer limpo.
- `npx --yes hyperframes@0.9.6 snapshot --at <t1>,<t2>,… --no-end`: quadros nas palavras-gatilho, nunca a sequência
  inteira. Os tempos são reais (`node briefings/tempo-real.cjs <t> …`).
- `npx --yes hyperframes@0.9.6 compare "<pasta A>" "<pasta B>" --at <t> --labels "A,B" --out <png>`: duas direções
  lado a lado num quadro, sem render (passe as pastas inteiras do projeto).
- `npx --yes hyperframes@0.9.6 measure events "<vídeo>" --map --out <pasta>`: janelas em que a tela muda, paradas
  (`holds`) e ataques do som, num JSON curto. Serve para medir um vídeo de referência e para a revisão.
- O render é do `entregar.py` (`scripts/README.md`), em rascunho para direção e uma vez em qualidade de entrega.
