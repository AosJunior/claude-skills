# Movimento: mola, emenda e luz

Como as coisas se movem nos atos. Vídeo é keyframe: tudo é pré-definido e nada se redireciona ao vivo, então o ganho
está em simular a **mola** dentro da timeline, cuidar de cada **emenda** e dar a cada propriedade o seu tempo. A mola
está pronta em `modelos/motion/assets/mola.js` e entra no projeto com o esqueleto. A régua visual da novela
([`regua-visual.md`](regua-visual.md), «Movimento») diz o que cada plano faz; este arquivo diz como.

## Os princípios

1. **Nada espera.** Cada gesto começa na palavra que o causa; o próximo entra quando o anterior está 30–50 % feito.
2. **Mola de bounce 0 por padrão.** Bounce só com motivo: o que chega com peso, ou o caráter lúdico. Texto e número
   não quicam acima de 0,15.
3. **Velocidade contínua em toda emenda.** O fim de um movimento é o começo do próximo.
4. **Cada propriedade no seu tempo.** Posição e escala assentam primeiro; luz e desfoque terminam depois.
5. **Continuidade espacial.** O mesmo objeto atravessa os estados, e a saída volta pelo caminho da entrada.
6. **Destaque por profundidade e luz**, nunca por bump de escala: o «pulinho» no número foi reprovado como preguiçoso.
7. **Som no quadro do impacto**, curto, um por marco, com silêncio nos respiros.
8. **O movimento desaparece.** Repouso quieto e um protagonista por vez: nada flutua nem pulsa sem motivo.

## A mola

Toda mola tem dois números: a **duração perceptual** (o ritmo, não o tempo até parar) e o **bounce**, de −1 a 1.
Primeiro a duração, pelo espaço até a próxima batida; depois o bounce, pelo caráter. Na dúvida, bounce 0. A mola é o
único movimento que mantém posição e velocidade contínuas saindo do repouso ou de outro movimento; o valor dela está
em terminar devagar, sem parada abrupta.

| bounce | passa do alvo | uso |
|---|---|---|
| 0 | nunca | opacidade, cor, luz, desfoque, câmera, troca de estado, tudo que assenta |
| 0,15 | 0,6 % | chegada ágil de posição; escala pequena |
| 0,3 | 4,6 % | só o que chega com momento: o emote que cai, o carimbo, o golpe |
| 0,4 | 9,5 % | teto: não passe dele |

Presets por papel, em `MOLA(papel)`:

| Papel | duração · bounce | Quando |
|---|---|---|
| `assentar` | 0,55 · 0 | cartão, etiqueta, linha que assenta |
| `pousar` | 0,5 · 0,15 | chegada ágil: balão, etiqueta, personagem que entra |
| `impulso` | 0,5 · 0,3 | só o que chega com momento |
| `estado` | 0,6 · 0 | troca de estado e de protagonista |
| `luz` | 0,8 · 0 | luz, desfoque, brilho |
| `camera` | 0,9 · 0 | empurrão curto, aproximar, viajar |

```js
const m = MOLA("pousar");                        // preset
const c = mola({ duracao: 0.7, bounce: 0 });     // sob medida
tl.to(el, { y: 0, duration: m.d, ease: m }, a(12.48));
```

- `m.d` é a duração da tween (1,5 × a duração perceptual): o ease fecha em 1 sem salto. Com a próxima batida perto,
  encurte a `duracao` e use o `m.d` que sai dela; cortar a cauda à mão cria a parada abrupta.
- `MOLA(papel, { duracao, bounce, v0, total })` sobrescreve o que vier; papel desconhecido dá erro.
- Teste da mola: `node assets/mola.js`.

Fora da mola:

| Caso | Ease |
|---|---|
| Empurrão lento pelo plano inteiro (1,00 → 1,06) | `none` ou `power1.inOut`, num sentido só |
| Efeito ambiente que alterna entre dois estados | `sine.inOut`, ~1 s |
| Chicote que sai parado e chega parado | `power4.inOut`, 0,2–0,3 s, borrão só no eixo do movimento |
| Saída | `power3.in`, 40–50 % mais curta que a entrada, pelo caminho da entrada |
| Opacidade curta de entrada (0,12–0,25 s) | `none` |
| Rotação contínua, roleta, barra de progresso | `none` |

Na chegada principal, `power2.out`, `power3.out` e `expo.out` dão lugar ao `pousar`: esses eases começam na
velocidade máxima, e a mola parte parada e acelera.

## Emendas

### Ledger

Antes do código, no topo do `atoN.html`, uma linha por emenda: tempo, objeto que sai e que entra, eixo e sentido dos
dois lados, v0 e tipo.

```
/* LEDGER DE EMENDAS
   E1 12,40  balão sobe e some (y−)         → etiqueta pousa (y−), v0 herdado        bastão
   S1 18,10  último quadro segura até T+0,30 → o ato 3 entra por chicote (x−)        saída */
```

Pronto quando cada emenda tem objeto, eixo, sentido e v0, ou o motivo de partir do repouso.

### Velocidade herdada

O movimento novo começa com a velocidade que o anterior tinha. `v0Herdado(m1, p, d1, d2)` converte a velocidade da
mola `m1` no ponto `p` pela razão das distâncias (com sinal, fim − início de cada tween); no sentido oposto, o v0 sai
negativo. Quando não dá para medir (o anterior foi ease in-out), estime de 1 a 3 alvos/s; a entrada de um ato com
câmera usa `MOLA("camera", { v0: 2.5 })`.

### Redirecionar no meio da mola

Um alvo não pode ter dois tweens sobrepostos na mesma propriedade: o GSAP desenha em ordem e o quadro depende do
sentido do seek. A primeira tween termina no corte, e a segunda parte dali com o v0 herdado:

```js
const m1 = MOLA("camera"), d1 = 400;                 // ia de 0 a 400
const p  = (t2 - t1) / m1.d;                         // ponto de m1 em que o alvo muda
const tr = trecho(m1, p), xc = d1 * tr.fim;          // onde o objeto está no corte
const m2 = mola({ duracao: 0.6, v0: v0Herdado(m1, p, d1, 650 - xc) });
tl.fromTo(el, { x: 0 },  { x: xc,  duration: tr.d, ease: tr }, t1);
tl.fromTo(el, { x: xc }, { x: 650, duration: m2.d, ease: m2, immediateRender: false }, t2);
```

Outro caminho: um invólucro por movimento (um desliza, outro faz o zoom).

### O que cada emenda diz

| Movimento | O que diz |
|---|---|
| a câmera entra no objeto | o próximo estado está dentro deste |
| desliza de baixo para cima | temporário, por cima do que estava |
| sai na horizontal (chicote) | troca de lugar na sequência |
| corte seco | nenhuma relação: um substitui o outro |

- **Passar o bastão:** o que chega nasce com o tamanho aparente e a velocidade do que sai.
- **Objeto de um estado só:** o que sai fica visível até o que entra cobrir o lugar dele; nunca os dois a 50 % no
  meio.
- **Contêiner estável:** quando só o conteúdo muda (a conversa no telefone), o contêiner fica; o conteúdo antigo sai
  para cima e o novo entra de baixo, dentro dele.
- **Fases:** primeiro o contêiner, depois os filhos, na ordem de leitura; stagger de 40 a 80 ms entre itens, 60 a
  120 ms entre palavras.
- **Matched geometry:** meça os dois retângulos na montagem e anime `x`, `y` e `scale`; com tamanhos muito
  diferentes, `scale` com `clipPath: inset(...)`.
- Na novela, a emenda entre atos é do ato que entra ([`regua-visual.md`](regua-visual.md) e a `_regua.md` do
  episódio, «Contrato de emenda entre atos»).

## Luz e material

- As coisas entram por luz e desfoque (materializar: desfoque de 6–10 px → 0 e opacidade em tweens próprios), e o
  brilho nasce do ponto de contato. Entrada que é só fade fica barata.
- A luz do plano segue o código de luz da bíblia; o motion só reforça com um radial suave da mesma cor, na mola `luz`.
- O protagonista se destaca por estar na frente, mais nítido e mais iluminado.

## Conforto

- Nada oscila sem parar nem pisca mais de 3 vezes por segundo.
- Empurrão e chicote: no máximo um travelling longo por plano; o chicote dura até 0,3 s.
- Passagem do escuro ao claro (cartão claro depois de cena noturna) em 0,2 s ou mais, nunca num quadro só.

## Conferir o movimento

Em cada ato, depois dos snapshots da régua:

- cada movimento tem palavra-gatilho e significado; elemento sem palavra nem motivo fica parado;
- nenhum tween mistura posição com luz ou desfoque; opacidade e cor assentam com bounce 0;
- cada emenda do ledger tem v0 ou o motivo do repouso, e nenhum alvo tem dois tweens na mesma propriedade ao mesmo
  tempo;
- nenhuma entrada é só fade, nenhum destaque é bump de escala;
- snapshots em T − 0,2, T e T + 0,2 de cada fronteira, e o teste de apertar os olhos: 3 quadros a 360 px de largura e
  desfocados mostram primeiro o protagonista.
