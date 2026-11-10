# Régua visual da novela (1080×1920)

O padrão de cena da novela: cena ilustrada em pixel art e tela chapada. O movimento (molas, emendas, luz) está em
[`movimento.md`](movimento.md); o contrato do render (o que animar, determinismo), em
[`gsap-hyperframes.md`](gsap-hyperframes.md).

**Medida** é o que saiu de quadros 1080×1920 das séries que medimos (ep. 1 em 1,5; 4,5; 14,5; 50,5; 58,5; 66,5 e
71,5 s; ep. 2 em 1,5; 17,5 e 86 s), extraídos com `ffmpeg -ss <t> -i <vídeo> -frames:v 1 <saída>.png` e medidos por
cor de pixel. **Proposta** é desta skill, a confirmar no piloto. As cores do episódio vêm da pele da oferta, escrita
na bíblia e posta nos tokens `--nv-*` do `componentes/novela.css` da série. Abaixo, cor é papel (fundo escuro, acento
quente, vermelho de alarme), com o token da pele neutra da skill entre parênteses; troque os valores, não os papéis.
Todo texto fica em 4,5:1 ou mais contra o próprio fundo: ao trocar a pele, meça cada par de novo.

## Um foco por quadro

- Um protagonista por quadro: a personagem do momento, maior, na frente e mais nítida. Quem testemunha fica menor e
  de lado (medida: a testemunha entra no canto direito, de corpo inteiro, menor que o protagonista em busto).
- No máximo duas vozes de texto ao mesmo tempo: a legenda e mais uma (etiqueta ou balão). Medida: em 1,5 s há balão e
  legenda; em 4,5 s, etiqueta e legenda; nunca as três.
- Texto sobre a cena tem fundo próprio (caixa da etiqueta, balão) ou contorno escuro (legenda). Meça o contraste do
  texto contra o próprio fundo: 4,5:1 ou mais (proposta: o mínimo de contraste para leitura).
- Teste de apertar os olhos: o quadro a 360 px de largura, desfocado, mostra primeiro o protagonista, depois o texto.

## Três planos de profundidade

Toda cena ilustrada tem três planos (medida):

| Plano | O que é | Regra |
|---|---|---|
| Frente | objeto cortado na borda de baixo (banco, painel do carro, roupa no chão, a maca) | camada própria com alfa, um pouco desfocada (proposta: 2 a 4 px) |
| Meio | a personagem recortada | a mais nítida do quadro |
| Fundo | o lugar iluminado (altar, janela, cidade) | levemente desfocado (proposta: 1 a 2 px) e mais escuro que a personagem |

No empurrão, os planos andam em velocidades diferentes: fundo devagar, personagem no meio, frente mais rápido
(proposta: 0,4 · 0,7 · 1,0 do deslocamento da frente). O fundo é gerado com sobra de pelo menos 15% na largura e na
altura, para o empurrão não mostrar borda (proposta).

O cenário caracteriza sem fala: três objetos que dizem quem a personagem é (medida: flâmula de time, calendário de
2019, cadeira gamer). Os objetos de cada lugar estão na bíblia.

## Código de luz

| Luz | Quando | Exemplo medido |
|---|---|---|
| Quente, dourada | onde há gente de verdade, onde se mente ou se acolhe | festa, jantar |
| Fria, azul | tela, solidão, madrugada | quarto à noite; o telefone no rosto |
| Cor do antagonista | o lugar e a presença dele | roxa para a concorrente, no exemplo da bíblia |

Uma luz fria num quadro quente é sempre a do telefone (medida: numa festa de luz quente, a única luz fria é a do telefone
no rosto da personagem). A luz é pintada no cenário e na pose; o motion só reforça com um radial suave da mesma cor (proposta).

## Camada de jogo: a barra do topo

**Medida (ep. 1, 50,5 e 71,5 s; ep. 2, 1,5 s):** duas caixas na mesma linha, y 150–269 (120 px de altura).

| Peça | Medida |
|---|---|
| Caixa do relógio | x 50–319 (270 px), rótulo «FALTAM» com 16 px de altura de maiúscula em y 174–189, número «30 DIAS» com 36 px de altura de maiúscula em y 214–250 |
| Vão entre as caixas | 28 px |
| Caixa do medidor | x 347–1033 (687 px), rótulo do medidor em y 174–189; trilho x 390–900, y 214–250, escuro (`--nv-trilho`); indicador de acento a partir de x 376 (`--nv-quente`); percentual em x 932–995 |
| Acabamento | fundo escuro (`--nv-fundo`), borda de 6 px num dourado discreto (`--nv-moldura`) |

Entrada: no ep. 1, a barra entra no retrato por provas (27 s); do ep. 2 em diante, está lá desde o quadro 0. Ela some
nos cartões cheios (medidor em 52–54 s no ep. 1; tela do app em 16–22 s no ep. 2).

**Proposta para a novela:** mesmas proporções, dentro das zonas seguras: y 240–360, caixa do relógio x 72–332, vão de
28 px, caixa do medidor x 360–1008. A medida da referência começa em y 150, dentro da faixa que a interface do
Instagram cobre; no piloto, confira no telefone se a barra fica legível nas duas posições. O número do relógio e o do
medidor giram na roleta quando mudam ([`roleta.md`](roleta.md)), com os pousos presos às palavras.

**Emotes** sobre a cabeça: gota de suor, «!», «?», coração partido. Um por vez, entrando de cima com `MOLA("pousar")`,
sem pulso parado (proposta).

## Três vozes de texto

Sempre nos mesmos lugares. A família tipográfica é a da pele da oferta, em peso 800 a 900, maiúsculas (a referência
usa uma sem serifa de traço grosso; a biblioteca da skill traz a Montserrat, de licença livre). Nunca SF Pro nem fonte
do sistema: a SF não tem licença para uso público, e a do sistema muda de máquina para máquina.

| Voz | Medida | Proposta na novela |
|---|---|---|
| **Legenda** (a fala do narrador) | branca com contorno escuro, palavra-chave em vermelho; 1 a 3 palavras; altura de maiúscula 43–44 px (y 1519–1563), linha de base em y ≈ 1562, centrada em x 540 | linha de base em y 1560, ~60 px, dentro de x 110–950; contorno escuro de 4 px ou mais; palavra-chave pelo `--a` do `legenda-grupos.cjs`, com a cor do lado A trocada pelo vermelho da pele no `compositions/legenda.html` (a calibrar no piloto). O script agrupa de 2 a 4 palavras; a `legenda.html` da biblioteca já divide ao meio os grupos de 4 |
| **Etiqueta** (o fato que desmente ou dá nome) | caixa vermelha (`--nv-alarme`) com sombra escura deslocada, texto branco em maiúsculas, inclinada ~6° (sobe 81 px em 760 px); em 4,5 s, x 96–971, y 1054–1227, sobre o queixo dele; azul para nome («NOME · FUNÇÃO», x 300–799, y 360–465) e dourada para número | mesma forma; vermelha para o fato contra, azul para nome (`--nv-frio`), dourada para número (`--nv-dourado`), verde para estado bom (`--nv-ok`); dentro da zona das cenas |
| **Balão** (a fala da personagem) | branco, borda escura, ponta para a cabeça, texto escuro em maiúsculas; em 1,5 s, y 329–410, ao lado da cabeça | mesma forma; até 5 palavras; perto da cabeça de quem fala, sem cobrir o rosto |

**Devolução do voto** (medida, ep. 2, 1,5 s): faixa escura inclinada «VOCÊS ESCOLHERAM:» em x 201–899, y 480–639, e
logo abaixo a palavra vencedora numa caixa vermelha em x 204–861, y 605–757, com 92 px de altura de maiúscula; acima da
cabeça da personagem. No anúncio fechado, o mesmo componente leva o que ela fez («ELA GRAVOU»), nunca «vocês».

## Cena ilustrada e tela chapada

As duas se revezam. A tela chapada descansa o olho, carrega a informação e é barata de produzir. Medida: no ep. 1, uns
40% dos segundos são tela chapada (contagem nas folhas de 1 quadro por segundo).

- **Fundo chapado:** escuro com grade de pontos (`--nv-fundo`; na tela do telefone, `--nv-fundo-2`) ou uma cor clara.
  Na série, as cores da pele da oferta.
- **Telefone** (medida, ep. 2, 17,5 s): corpo x 110–970, y 165–1690, grafite; tela x 142–937, y 262–1641 (796 × 1380);
  rótulo inclinado dourado com o nome da oferta acima do telefone, em y ≈ 50–170. O telefone da conversa é menor: tela x
  250–830, y 499–1562.
- **A aula no telefone** (proposta): o trecho real do vídeo de quem vende em 9:16, 776 × 1380, centrado na tela do
  telefone grande; a barra do topo e a legenda saem; a lei entra numa etiqueta no momento em que quem vende a diz; o
  rótulo acima do telefone traz o nome da aula ou da oferta. Quem vende nunca é desenhado.
- **Cartão de frase** (medida, ep. 1, 39–43 s): duas etiquetas empilhadas no centro («AMANHÃ» dourada, «VOCÊ DECIDE»
  vermelha) e a personagem pequena embaixo.
- **Cartão do medidor** (medida, ep. 1, 52–54 s): rótulo de duas linhas, trilho vazio e o percentual vermelho
  inclinado, no terço de cima, sem barra do topo.

## Movimento

Medido nas folhas: imagem parada com empurrão lento; corte para o rosto na emoção; chicote borrado na troca de lugar;
recorte da personagem com contorno branco sobre o fundo escurecido na piada física (ep. 1, 44–51 s).

- Empurrão: escala de 1,00 a 1,06 ao longo do plano, em ease linear ou `power1.inOut` (proposta).
- Chicote: deslocamento lateral com borrão de movimento de 0,2 a 0,3 s, na troca de lugar (proposta).
- Recorte na piada: fundo escurece a ~50% e ganha 6 px de desfoque; a personagem ganha contorno branco de 4 a 6 px
  (proposta).
- Sprite de pixel art escalado leva `image-rendering: pixelated`, para o pixel não borrar (proposta).
- Entradas de etiqueta, balão e emote em `MOLA`; saídas em `power3.in`, 40–50 % mais curtas que a entrada
  ([`movimento.md`](movimento.md)). Sem bump de escala no número.

## Cartão das duas opções

**Medida (ep. 1, 71,5 s; o ep. 2, em 86 s, repete a geometria):**

| Peça | Medida |
|---|---|
| Faixa do topo | clara (`--nv-claro`), y 0–437, com a barra de jogo dentro (y 150–269) |
| «COMENTE UMA PALAVRA» | caixa preta com sombra deslocada, x 171–900, y 314–398; texto branco com 33 px de altura de maiúscula |
| Divisão | de y 440 até o fim; esquerda x 0–539 e direita x 540–1079, uma cor fria e uma quente de mesmo peso |
| Nome da opção | branco com contorno escuro, 63 px de altura de maiúscula, y 561–624 |
| Custo | branco, maiúsculas, 21 px de altura de maiúscula, y 669–689 |
| Personagem de cada lado | corpo inteiro, ~580 px de altura (y 791–1373) |
| «OU» | círculo branco de 120 px com borda escura, centro em (540, 960) |
| Pergunta | etiqueta inclinada creme-dourada, x 144–929, y 1471–1639 (no ep. 2, x 88–991, y 1440–1699) |
| Tempo | parado 5 s no fim |

**Proposta para a novela:** a mesma geometria, com as duas cores da pele (`--nv-quente-claro` e `--nv-frio`, texto
em `--nv-tinta`) e a pose de cada escolha. A pergunta sobe
para y 1420–1580, fora da faixa coberta pelo Instagram, e o custo fica com 28 px de corpo ou mais. As duas cores têm o
mesmo peso: nenhuma opção parece a certa.

## Zonas seguras

Conteúdo das cenas em y 250–1430 e x 72–1008; legenda em y 1440–1580; acima de y 230 e
abaixo de y 1600, a interface do Instagram cobre; em x ≥ 960 entre y 1120 e 1600, os botões. Aqui, a barra do topo
e o telefone da aula são as duas exceções planejadas (y 240 e corpo do telefone até ~1690); o que ficar sob a interface
não pode ser texto. O `conferir-faixa.cjs` acusa texto de cena abaixo de y 1430. A única liberação é a pergunta do
cartão das duas opções: na janela do cartão a legenda sai (`--sem`), e a pergunta leva `data-layout-allow-caption-zone`
para ocupar a faixa dela.

## Batida presa à palavra

- Cada mudança na tela começa no **início** da palavra que a causa, com o tempo do `briefings/palavras-voz.json`
  (alinhamento forçado, [`voz.md`](voz.md)) passado pelo `a()` do ato. O tempo do Whisper não entra no código: ele erra
  até 0,6 s. Batida presa ao fim de palavra escorrega onde a palavra estica.
- **Leitura:** 0,5 s + 0,3 s por palavra antes de um texto sair ou mudar. O cartão final fica parado e legível.
- **Ease por papel:** chegada, câmera, luz e troca de estado em `MOLA`; saída em `power3.in`. O mesmo fade em tudo é o
  que denuncia vídeo genérico.
- Cada ato recebe a tela como o anterior deixou e entrega pronta para o próximo; o briefing diz o que recebe e entrega.

## Conferência por snapshot

Depois de cada mudança, na raiz do projeto motion:

1. `npx --yes hyperframes@0.9.6 check`, sem erro do seu arquivo. O `first_frame_empty` pode acusar à toa com algo
   legível no quadro 0; o `line_unread` nos dígitos da roleta é falso positivo.
2. `node briefings/conferir-faixa.cjs`, sem erro: acusa texto de cena abaixo de y 1430. Texto escondido sob máscara
   também conta: ele nasce de um recorte, em vez de esperar sob a máscara na faixa da legenda.
3. Snapshot no tempo real: `node briefings/tempo-real.cjs <tempos>` e
   `npx --yes hyperframes@0.9.6 snapshot --at <t1>,<t2>,… --no-end`, um quadro em cada palavra-gatilho, mais um na
   entrada e um na saída do ato. Abra cada PNG; o comando diz a pasta.

Em cada quadro:

- texto com texto e texto com barras: nada se cruza nem encosta (balão e etiqueta, etiqueta e barra, cena e legenda);
- zona: tudo dentro das zonas seguras, nada cortado na borda;
- restos: nada do ato anterior, nada do ato depois da janela dele;

- três planos na cena ilustrada, com a personagem mais nítida que o fundo;
- a luz do quadro bate com o código do lugar na bíblia;
- uma voz de texto além da legenda, no lugar dela;
- a personagem bate com a folha (`elenco-e-cenarios.md`, «Conferência de identidade»);
- a barra do topo legível, com o dia e o medidor iguais aos do roteiro.
