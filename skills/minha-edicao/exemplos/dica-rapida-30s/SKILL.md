---
name: dica-rapida-30s
description: Dica rápida de 30 s para Reels: uma dica só, gancho nos 3 primeiros segundos e pedido para salvar no fim. Use ao editar um vídeo de dica rápida ou quando a pessoa chamar /dica-rapida-30s com um vídeo.
---

# Dica rápida 30 s

Um vídeo, uma dica, 25 a 35 s: quem assiste sai sabendo fazer uma coisa.

A legenda, a cor, o zoom e o som vêm do `marca/estilo.md` da pasta de edição; sem ele, ficam os padrões de
cada skill do kit. Se alguma skill não estiver instalada: `npx github:AosJunior/claude-skills edicao`.

## Como editar

1. **`/decupar`** com o vídeo da pessoa, usando os blocos abaixo como critério de cada corte. Antes de cortar,
   mostre o mapa nos 4 blocos, uma linha por bloco: bloco · frases (`F<n>`) · segundos. Passou de 35 s:
   proponha o que sai (a explicação, nunca um passo da dica).
2. **`/inserir`** com o `insercoes.json` da composição abaixo: o texto do gancho e um número grande ou uma lista
   por passo, se a fala pedir. A legenda sai gravada no estilo da pasta.
3. **`/sonorizar`**: trilha baixa do estilo e no máximo 2 efeitos (o texto do gancho entra, o pedido do fim).
4. **`/criticar`** no vídeo com som. Reprova volta para a skill dona e o kit roda de novo dali para frente; no
   máximo 2 voltas.
5. Entregue `entrega/` e pergunte o que ela corrigiu na mão.

## Blocos

| Bloco | Segundos | O que entra |
|---|---|---|
| Gancho | 0–3 | A primeira palavra do vídeo já é o gancho: o resultado ou o erro comum ("Você guarda o pão do jeito errado"). Sai tudo o que vem antes: "oi", respiração, "então". |
| Por que importa | 3–8 | Uma frase. |
| A dica | 8–25 | 1 a 3 passos, uma frase por passo; mostrando, se houver imagem. |
| Pedido do fim | últimos 3–5 | "Salva pra usar depois." |

- Duração: alvo 30 s, aceita de 25 a 35 s.
- Sempre sai: pausa acima de 0,4 s, erro e repetição (fica a última versão boa), despedida longa.
- O melhor gancho está no meio do vídeo: traga para o começo e avise a pessoa.

## Composição

| Bloco | Camada | Onde | Âncora |
|---|---|---|---|
| Gancho | texto do gancho, até 6 palavras, `tipo: "faixa"` | y entre 300 e 560, centralizado | de 0 até `F1:fim` |
| A dica | número do passo ("1", "2", "3") em lettering | y entre 300 e 780, acima da cabeça | entra na primeira palavra do passo, sai no fim da frase |
| Pedido do fim | nenhuma: só a legenda | — | — |

- Zona segura y 260 a 1600; nada encostado na lateral direita entre y 1100 e 1700.
- Um evento visual a cada 4 s no máximo (corte, zoom do estilo ou camada).

## Conferir antes de entregar

- [ ] Duração entre 25 e 35 s
- [ ] Gancho dito nos 3 primeiros segundos, com o texto na tela até o fim da primeira frase
- [ ] Todos os passos da dica estão no vídeo, cada um com o número
- [ ] Pedido do fim nos últimos 5 s
- [ ] Nenhuma pausa acima de 0,4 s

## Melhorar esta receita

Ao entregar cada vídeo, pergunte: "O que você corrigiu na mão?". Cada correção, e cada item que a
/criticar reprovou duas vezes seguidas, vira regra aqui: troque a regra antiga pela nova (uma regra
por assunto, nunca duas versões), acrescente uma linha no Histórico com a data e o que mudou, e
mostre à pessoa a linha alterada.

## Histórico

- 2026-10-16: criada com /minha-edicao como exemplo da aula; valores de partida, sem referência medida.
- 2026-10-18: passa a encadear /decupar, /inserir, /sonorizar e /criticar; texto do gancho gravado pela /inserir.
