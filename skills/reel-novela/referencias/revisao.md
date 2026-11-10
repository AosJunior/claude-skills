# Revisão de olhos novos

Passo 9. Você não fez nenhuma parte deste episódio. Olhe e meça a entrega como quem vai postar, siga os itens abaixo e
devolva uma lista. Você não corrige nada: quem corrige é o dono de cada arquivo. Esta revisão já achou o que os
autores não viram (o volume que mudava ao longo do vídeo, o estalo da roleta que não se ouvia, textos se cruzando, a
testemunha confundida com a protagonista). Seja duro: a pessoa vai ser.

## O que ler

- `<pasta da série>/biblia.md`: modo de veiculação, elenco, código de luz, o que a série não afirma.
- `<pasta da série>/fatos-verificados.md`: a régua de todo número, nome e da lei.
- `<ep>/roteiro.json`: o que a voz diz (`texto`), os planos, os textos e a barra.
- `<ep>/sequencia/motion/briefings/palavras-voz.json`: quando cada palavra é dita; é a sua régua de tempo.
- `<ep>/sequencia/motion/briefings/_regua.md` e `<pasta desta skill>/referencias/regua-visual.md`.
- `<pasta desta skill>/referencias/grade-de-batidas.md`: a grade, os mecanismos e o modo.
- A entrega (`<ep>/sequencia/exports/<slug>-epNN.mp4`), o `sequencia/som/efeitos.json` e o `sequencia/som/mix.json`.

## Como olhar

Grave quadros e medidas numa pasta de trabalho fora do episódio.

- **Telas paradas, primeiro:**
  `npx --yes hyperframes@0.9.6 measure events "<entrega>" --map --out "<pasta>/eventos" > "<pasta>/eventos.json"` e
  `python3 -c "import json;print([h for h in json.load(open('<pasta>/eventos.json'))['holds'] if h['seconds']>=2])"`.
  Cada parada ganha um quadro exato: respiro pedido pelo roteiro, a aula ou o cartão final (OK), ou tela morta (MENOR;
  BLOQUEANTE na abertura).
- **Folhas do vídeo inteiro**, um quadro por segundo, 20 por folha:
  `ffmpeg -i "<entrega>" -vf "fps=1,scale=270:-2,tile=4x5" "<pasta>/folha-%02d.jpg"`.
- **Quadro exato:** `ffmpeg -ss <t> -i "<entrega>" -frames:v 1 "<pasta>/q-<t>.png"`, nas palavras-gatilho, nas
  mudanças da barra, no primeiro e no último quadro. Abra o quadro inteiro sempre que a miniatura deixar dúvida.
- **Volume de um trecho:** `ffmpeg -ss <ini> -t <duração> -i "<entrega>" -af ebur128=peak=true -f null -` (as linhas
  `I:` e `Peak:` do fim).

## Gravidade

- **BLOQUEANTE**: o vídeo não pode sair assim.
- **MENOR**: pode sair, mas fica melhor corrigido.
- **OK**: conferido e certo. Diga como: quantos quadros, que medida.

## Os itens, nesta ordem

### 1. Fatos, números e a lei

- Cada número da tela e da voz (a barra, as etiquetas, o preço, o prazo da oferta) bate com o roteiro e com o
  `fatos-verificados.md`; o relógio e o medidor andam como a lista `barra` do roteiro manda.
- A lei da etiqueta é a frase literal de quem vende no trecho da aula.
- Durante um giro, nenhum número errado nítido e parado.

BLOQUEANTE: número, nome ou lei diferente do fato.

### 2. Limites da série

- Ficção declarada; o resultado da personagem é número de jogo e nunca aparece como efeito garantido da oferta.
- Fala, tela e legenda descrevem a personagem em terceira pessoa e não afirmam atributo de quem assiste.
- Quem vende aparece só no vídeo real, nunca desenhado.
- As regras do modo de veiculação (`SKILL.md`, «Modos de veiculação»): no anúncio fechado, nenhuma frase dá ao
  público a decisão.

BLOQUEANTE: qualquer quebra.

### 3. A grade

- As batidas da grade do episódio existem, na faixa de posição delas, e os mecanismos da grade estão lá.
- A abertura se entende sem som; o pedido de comentário aparece dentro da história e no fim.

MENOR: batida fora da faixa; BLOQUEANTE: batida que falta.

### 4. Régua da novela

Em cada quadro conferido:

- um foco por quadro; quando a fala diz o nome ou uma qualidade de um personagem, é ele quem está no quadro;
- três planos na cena ilustrada, a personagem mais nítida que o fundo;
- a luz bate com o código do lugar na bíblia;
- a personagem bate com a folha (`elenco-e-cenarios.md`, «Conferência de identidade»);
- no máximo duas vozes de texto (legenda e mais uma), cada uma no seu lugar;
- a barra legível, com o dia e o medidor certos.

BLOQUEANTE: identidade trocada, personagem confundida, três vozes de texto juntas. MENOR: o resto.

### 5. Texto com texto e texto com barras

- Nenhum texto sobre outro, nem encostando ou cruzando etiqueta, balão, barra, telefone ou a legenda.
- Nada cortado na borda; conteúdo dentro das zonas da `_regua.md`; nada de leitura sob a interface do Instagram
  (acima de y 230, abaixo de y 1600 e, de y 1120 a 1600, à direita de x 960), salvo as exceções planejadas da régua.
- Nenhum texto de leitura abaixo de 28 px de corpo; nada que sobra de um ato no seguinte; nenhuma tela vazia no meio
  de uma frase.

BLOQUEANTE: texto que não se lê inteiro. MENOR: encosta sem cobrir.

### 6. Legenda

- Acende cada palavra quando ela é dita: confira 6 palavras espalhadas, duas no último terço, em `t − 0,1`, `t` e
  `t + 0,1`.
- Diz exatamente o `texto` do roteiro; fica fora da janela da aula e dos trechos de `legenda.fora`.

BLOQUEANTE: palavra errada, ou 0,2 s ou mais fora da voz. MENOR: de 0,1 a 0,2 s.

### 7. A aula

- O trecho toca inteiro, começando e acabando em pausa, sem música nem efeito por cima.
- A voz de quem vende fica no volume da narração (o `encaixar_aula.py` iguala): o `ouvir.py` na janela dá 95 % ou mais.
- A etiqueta da lei entra quando quem vende a diz.

BLOQUEANTE: trecho cortado, coberto ou ininteligível.

### 8. Começo e fim

- Quadro 0: algo já se lê e algo se move, sem quadro preto. A voz começa logo.
- A última palavra sai inteira, o som final se completa e o cartão das duas opções fica parado 5 s.
- A duração do arquivo é a da `sequencia/motion/narracao.wav`, a até 0,10 s.

BLOQUEANTE: palavra cortada, quadro 0 vazio, fim cortado.

### 9. Roleta e som

- Cada roleta trava na palavra dela (a `ultima` a até 0,1 s do início da palavra); o estalo final da roda, quando o
  número é o principal, se ouve e cai a até 1 quadro da trava.
- Nas medidas de [`som.md`](som.md): −14 LUFS a até 0,5 LU, pico de −1,5 dBTP ou menos, ganho da voz de 0,3 dB ou
  menos (`ganho_voz.py`), e, com trilha, o `medir.py` sob a fala e nos respiros. Nenhum efeito cobrindo uma palavra.
- Na entrega só com efeitos, nenhum pedaço de música; nos respiros sem efeito, silêncio abaixo de −50 LUFS.

BLOQUEANTE: medida fora da faixa, estalo que não se ouve, música na versão sem trilha. MENOR: ganho da voz até 0,05 dB
acima da régua quando quem pega a voz é o limitador do master (diga o número).

### Fora da lista

O que pesar e não couber nos itens (hierarquia plana, transição sem causa, movimento abaixo do piloto aprovado) entra
como MENOR, ou BLOQUEANTE se quebra a `_regua.md`. Para o movimento, use [`movimento.md`](movimento.md), «Conferir o
movimento».

## Resposta

1. A lista numerada, BLOQUEANTE primeiro. Cada item: tempo (s), ato, o que está errado (uma frase), por que importa
   (uma frase), a correção sugerida e o dono provável (ato, roteiro, voz, efeitos, trilha, mixagem, elenco).
2. Os itens, cada um com OK, MENOR ou BLOQUEANTE e a evidência em uma linha.
3. Uma linha de veredito: «pode entregar» ou «N bloqueantes».
