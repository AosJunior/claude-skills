---
name: ana-gancho-dividido
description: Reel de opinião de cerca de 2 min com gancho em tela dividida: a prova do assunto em cima, a pessoa reagindo embaixo, headline na emenda, depois números em lettering e vídeos de outros criadores atrás dela. Use ao editar um vídeo de opinião ou análise de mercado, ou quando a pessoa chamar /ana-gancho-dividido.
---

# Gancho dividido

Uma opinião sobre um fato que todo mundo vê: o gancho mostra o fato em cima e a reação dela embaixo, e o
resto do vídeo prova com números e com o que outros criadores estão fazendo.

As fontes, a cor, a legenda, o zoom e o som vêm do `marca/estilo.md` da pasta de edição. Esta receita decide
os blocos, a composição de cada um e o que é conferido.

## Como editar

1. **`/decupar`** com o bruto. No `cortes.json`, velocidade, zoom e LUT do estilo. Antes de cortar, mostre o
   mapa nos 7 blocos abaixo: bloco · frases (`F<n>`) · segundos no vídeo final (tempo do bruto ÷ 1,2). Passou de
   140 s: proponha o que sai do bloco 5, nunca do gancho, da prova ou do pedido do fim. O trecho do gancho
   (bloco 1) é de fala contínua: no máximo um corte de respiração, porque a metade de baixo não pode pular.
2. **Mídia do gancho e das provas**: os vídeos da metade de cima (cenas que provam o assunto) e os vídeos de
   outros criadores vão para `brutos/videos/`, com origem e link em `brutos/fontes.md`. Pergunte à pessoa só
   o que ela não mandou.
3. **`/inserir`** com o `insercoes.json` da composição abaixo: a `divididas` do gancho, as camadas de cada bloco
   presas às palavras, as faixas de `legenda` e o bloco `estilo` copiado do `marca/estilo.md`. Confira a folha
   da `/inserir` contra a tabela de composição antes de seguir.
4. **`/sonorizar`**: trilha do universo do estilo, em lista com a troca na virada do bloco 4
   (`"cruzar": 0.4`). Efeitos presos às camadas: zoom seco do primeiro par do gancho, vídeos que entram, cada
   lettering de número, pedido do fim. Cada um com motivo. `entrega` para `../entrega`.
5. **`/criticar`** no vídeo com som, com esta receita como régua extra (seção "Conferir"). Reprova volta para a
   skill dona (emenda: `ajustes` do `cortes.json`; posição ou tempo: `insercoes.json`; som: `som.json`) e o kit
   roda de novo dali para frente. No máximo 2 voltas; o que ainda reprova vai para a pessoa, com a medida.
6. Entregue `entrega/` e pergunte o que ela corrigiu na mão.

## Blocos

Segundos no vídeo final do Reel de referência (134 s, fala a 1,2×).

| # | Bloco | Segundos | O que é dito | O que se vê |
|---|---|---|---|---|
| 1 | Gancho dividido | 0–13 | A pergunta da headline e o fato ("toda rua tem uma placa de aluga-se") | Tela dividida; a prova em cima, ela embaixo |
| 2 | Assunto | 13–23 | O que ela vai mostrar | Tela cheia, ela com o objeto do assunto |
| 3 | Prova | 23–55 | Os números e quem já faz | Vídeos de outros criadores atrás dela; letterings de número |
| 4 | Virada | ~55 | "Isso porque..." | Corte seco; troca de trilha |
| 5 | Explicação | 55–107 | O porquê, com um conceito ou livro | Lettering de número e de citação; mosaico atrás |
| 6 | Volta à tese | 107–130 | Antes e hoje | Lettering "antes / hoje"; as cenas do gancho voltam em cartão |
| 7 | Pedido do fim | últimos 4 | "Se quer aprender..., me segue aqui" | Destaque no verbo; ela aponta |

- Duração: alvo 2 min 10 s, aceita de 90 a 140 s.
- Sempre sai: pausa acima de 0,22 s, gagueira, repetição (fica a última versão boa), "oi" e despedida.
- Pedido do fim: a frase exata vem da pessoa (`<FRASE DO PEDIDO>`), sempre terminando em "me segue aqui".

## Composição

Quadro 1080×1920. Zona segura y 260 a 1600, margem lateral 70 px; nada importante em x acima de 960 entre y
1100 e 1700 (botões do Instagram).

| Bloco | Pessoa | Atrás dela | Na frente | Metade de cima | Legenda |
|---|---|---|---|---|---|
| 1 | metade de baixo (dividida em 960), olhos a ~56% da metade | — | headline | vídeo da prova | some até `F1:fim+0.25`, depois pé em 1190 |
| 2 | tela cheia | — | destaque | — | pé em 1290 |
| 3 | tela cheia | mosaico de 3 vídeos | letterings de número | — | pé em 1290; some no lettering de número |
| 4 | tela cheia | — | — | — | pé em 1290 |
| 5 | tela cheia | 1 mosaico | letterings de número e de citação | — | pé em 1290; some no lettering de número |
| 6 | tela cheia | 2 cartões com as cenas do gancho | lettering "antes / hoje" | — | pé em 1290 |
| 7 | tela cheia | — | destaque | — | pé em 1290 |

**Gancho (bloco 1)**

```json
"divididas": [{"id": "gancho", "de": 0, "ate": "<F DA ÚLTIMA FRASE DO GANCHO>:fim", "corte": 960,
               "pessoa": [{"de": 0, "recorte_y": 450}], "laterais": "borrado"}],
"camadas": [
  {"id": "headline", "tipo": "faixa", "texto": "<PERGUNTA DO GANCHO>", "de": 0, "ate": "F1:fim+0.25",
   "y": 908, "largura": 898, "altura": 104, "raio": 17, "fundo": "#FCFCFC", "tinta": "#111111",
   "fonte": "marca/fontes/<FONTE DA HEADLINE>", "tamanho": 58},
  {"id": "prova-1", "tipo": "video", "arquivo": "../brutos/videos/<cena-1>.mp4", "src": 0,
   "de": 0, "ate": 2.63, "lugar": "topo", "audio": null,
   "recorte": [{"t": 0, "caixa": [0, 240, 1080, 1440]}, {"t": 1.0, "caixa": [240, 520, 600, 800]}]}
]
```

- Metade de cima: pares "aberto 1,0 s + zoom seco 1,63 s". As caixas do `recorte` estão no quadro do vídeo de
  origem e têm a proporção 3:4 da janela de 720×960; a do zoom seco é menor, no detalhe que prova (a placa, o
  preço). Um par por cena, cenas diferentes em sequência até o fim do gancho.
- `recorte_y` escolhido na folha para os olhos ficarem a ~56% da metade de baixo; se ela se mexe muito, um
  segundo item em `pessoa` a partir da frase em que muda.
- O gancho fecha num destaque (a palavra que resume o fato) e num corte seco para a tela cheia.

**Letterings (blocos 3, 5, 6)**
- Entre y 300 e 780, alternando o lado (esquerda, centro, direita) de um lettering para o próximo.
- Número com complemento ("+100 mil / produtos vendidos"): entra na palavra do número, sai no fim da frase,
  `"legenda": "some"`. Citação de obra: entra no nome da obra.
- No máximo 1 lettering na tela.

**Vídeos de outros criadores (blocos 3 e 5)**
- `lugar: "atras"`, com máscara: o rosto e as mãos dela na frente.
- Mosaico de 3 no alto: cartões de 390 px de largura em x 0, 330 e 660, y 150 a 250, `rot` -6, 0 e 6, raio 26,
  sobrepostos. Cada cartão entra na palavra que o nomeia (`"F<n>:<palavra>"`), com pop.
- No máximo 1 mosaico na tela; mosaico e lettering juntos só se o lettering for de 1 palavra (destaque).

**Cartões do bloco 6**: as cenas do gancho voltam em cartão de 360 px de largura no canto de cima, atrás dela,
alternando esquerda e direita.

**Densidade**: um evento visual (corte, camada, lettering, destaque) a cada 5 s no máximo; nenhum trecho de 8 s
sem evento. Destaque a cada 8 a 15 s. Letterings: 6 a 8 no vídeo. Mosaicos: 2 a 3.

**Nunca**: nada na frente do rosto; nenhuma camada abaixo de y 1100 no bloco 1 (é onde ela está).

## Conferir antes de entregar

- [ ] Duração entre 90 e 140 s
- [ ] Headline some no fim da primeira frase; a emenda fica em 960 até o fim do gancho
- [ ] Gancho termina antes de 15 s, num destaque e num corte seco
- [ ] Metade de cima em pares "aberto + zoom seco", sem tela preta entre cenas
- [ ] Todo lettering entre y 300 e 780, lados alternados; legenda some nos de número
- [ ] Vídeos de outros criadores atrás dela, com máscara limpa no contorno do cabelo
- [ ] Nenhum trecho de 8 s sem evento visual
- [ ] Troca de trilha na virada; efeito em cada lettering de número, nenhum sem motivo
- [ ] Pedido do fim nos últimos 4 s, com a frase exata
- [ ] Todo vídeo de terceiro com origem em `brutos/fontes.md`

## Melhorar esta receita

Ao entregar cada vídeo, pergunte: "O que você corrigiu na mão?". Cada correção, e cada item que a
/criticar reprovou duas vezes seguidas, vira regra aqui: troque a regra antiga pela nova (uma regra
por assunto, nunca duas versões), acrescente uma linha no Histórico com a data e o que mudou, e
mostre à pessoa a linha alterada.

## Histórico

- 2026-10-18: criada com /minha-edicao a partir do Reel aprovado da Ana "Ter loja virou coisa de pobre?"
  (17/10/2026, 134 s), medido quadro a quadro; molde público, sem fontes nem sons.
