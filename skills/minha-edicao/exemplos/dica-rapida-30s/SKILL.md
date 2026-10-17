---
name: dica-rapida-30s
description: Dica rápida de 30 s para Reels: uma dica só, gancho nos 3 primeiros segundos e pedido para salvar no fim. Use ao editar um vídeo de dica rápida ou quando a pessoa chamar /dica-rapida-30s com um vídeo.
---

# Dica rápida 30 s

Um vídeo, uma dica, 25 a 35 s: quem assiste sai sabendo fazer uma coisa.

## Como editar

1. Abra a skill `/decupar` e siga o fluxo dela (decupagem → corte → legenda) com o vídeo da pessoa, usando as regras do formato abaixo como critério de cada corte. Se ela não estiver instalada: `npx github:AosJunior/claude-skills`.
2. Antes de cortar, mostre o mapa nos 4 blocos do formato, uma linha por bloco: bloco · trecho falado · segundos. Passou de 35 s: proponha o que sai (a explicação, nunca um passo da dica).
3. Legenda: se existir uma receita de estilo de legenda em `~/.claude/skills/` (ex.: `legenda-limpa`), siga a dela; senão, a padrão da `/decupar`.
4. Texto do gancho: escreva a frase (até 6 palavras) na lista do que fazer no editor, com o lugar: entre 15% e 30% da altura (abaixo da barra de cima do Instagram), do 0 s ao fim do gancho.
5. Confira a lista abaixo e entregue.

## Regras do formato

| Bloco | Segundos | O que entra |
|---|---|---|
| Gancho | 0–3 | A primeira palavra do vídeo já é o gancho: o resultado ou o erro comum ("Você guarda o pão do jeito errado"). Sai tudo o que vem antes: "oi", respiração, "então". |
| Por que importa | 3–8 | Uma frase. |
| A dica | 8–25 | 1 a 3 passos, uma frase por passo; mostrando, se houver imagem. |
| Pedido do fim | últimos 3–5 | "Salva pra usar depois." |

- Duração: alvo 30 s, aceita de 25 a 35 s.
- Sempre sai: pausa acima de 0,4 s, erro e repetição (fica a última versão boa), despedida longa.
- O melhor gancho está no meio do vídeo: traga para o começo e avise a pessoa.

## Conferir antes de entregar

- [ ] Duração entre 25 e 35 s
- [ ] Gancho dito nos 3 primeiros segundos, com o texto na tela
- [ ] Todos os passos da dica estão no vídeo
- [ ] Pedido do fim nos últimos 5 s
- [ ] Nenhuma pausa acima de 0,4 s

## Melhorar esta receita

Ao entregar cada vídeo, pergunte: "O que você corrigiu na mão?". Cada correção vira regra
aqui: troque a regra antiga pela nova (uma regra por assunto, nunca duas versões), acrescente
uma linha no Histórico com a data e o que mudou, e mostre à pessoa a linha alterada.

## Histórico

- 2026-10-16: criada com /minha-edicao como exemplo da aula; valores de partida, sem referência medida.
