# Como escrever a receita

A receita é uma skill pequena que outro Claude vai seguir no próximo vídeo, sem esta conversa. Tudo o que foi decidido nas rodadas precisa estar escrito nela, com valor concreto.

## Nome e lugar

- Nome curto: minúsculas, sem acento, palavras ligadas por hífen, até 3 palavras, dizendo o que é (`receita-45s`, `legenda-limpa`, `react-rapido`).
- Arquivo: `~/.claude/skills/<nome>/SKILL.md` (no Windows, `~` é a pasta do usuário, `C:\Users\<nome>`). Se quem chamou esta skill indicou outra pasta, grave lá.
- Pasta com esse nome já existe: pare e pergunte. Se for receita dela, é o caminho "Ajustar"; se não, proponha outro nome.

## Frontmatter

```
---
name: <nome igual ao da pasta>
description: <o que é. Quando usar.>
---
```

A `description` é o que faz a receita entrar sozinha. Duas frases:
1. O que a receita é, com as palavras que a pessoa usa ("Receita de 45 s da confeitaria: ...", "Legenda limpa: ...") e o essencial dela.
2. Quando entra, um gatilho por caso: formato → "Use ao editar um vídeo de <assunto> ou quando a pessoa chamar /<nome>"; estilo → "Use ao <legendar, cortar, colorir...> qualquer vídeo da pessoa, inclusive dentro de uma receita de formato".

Se a pessoa já tem outra receita de estilo para a mesma parte (duas legendas, por exemplo), a description diz quando cada uma vale ("para os vídeos de receita") e a pessoa confirma isso na rodada 3.

## Receita de formato

Molde: [exemplos/dica-rapida-30s/SKILL.md](exemplos/dica-rapida-30s/SKILL.md). Seções, nesta ordem:

1. Uma linha: o formato e o que quem assiste ganha.
2. `## Como editar`: (1) abrir a skill `/decupar` e seguir o fluxo dela (decupagem → corte → legenda), usando as regras do formato como critério de cada corte; (2) antes de cortar, mostrar o mapa nos blocos do formato; (3) legenda pela receita de estilo escolhida, com o caminho do arquivo dela, ou a padrão da `/decupar`; (4) a entrega para o editor da pessoa; (5) conferir.
3. `## Regras do formato`: tabela com duração (alvo e faixa), gancho (o que, em quais segundos, texto na tela), cada bloco em ordem com segundos, pedido do fim (frase exata), o que sempre sai.
4. `## Conferir antes de entregar`: uma linha marcável por regra.
5. `## Melhorar esta receita` (bloco fixo abaixo) e `## Histórico`.

## Receita de estilo

Molde: [exemplos/legenda-limpa/SKILL.md](exemplos/legenda-limpa/SKILL.md). Seções, nesta ordem:

1. Uma linha: o jeito e a sensação que ele passa.
2. `## Parâmetros`: tabela parâmetro · valor. Números em px no quadro 1080×1920, cores em hex, tempos em segundos, fonte pelo nome com uma alternativa. Palavra vaga vira número com uma régua visual ("médio" vira "62 px: a frase de 4 palavras ocupa até 2/3 da largura").
3. `## Como aplicar`: primeiro o que o Claude faz (legenda `.srt` quebrada pela receita, corte, lista para o editor); depois só o editor que a pessoa usa, com os passos de [editores.md](editores.md).
4. `## Conferir`: uma linha marcável por parâmetro que dá para errar.
5. `## Melhorar esta receita` (bloco fixo abaixo) e `## Histórico`.

## Bloco fixo de melhoria

Copie igual em toda receita:

```
## Melhorar esta receita

Ao entregar cada vídeo, pergunte: "O que você corrigiu na mão?". Cada correção vira regra
aqui: troque a regra antiga pela nova (uma regra por assunto, nunca duas versões), acrescente
uma linha no Histórico com a data e o que mudou, e mostre à pessoa a linha alterada.
```

## Histórico

Primeira linha: `- AAAA-MM-DD: criada com /minha-edicao.` e de onde vieram os valores (link ou nome do arquivo da referência, "vídeo dela", "escolha na entrevista"). Datas sempre completas.
