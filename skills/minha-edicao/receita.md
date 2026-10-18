# Como escrever a receita

A receita é seguida por outro Claude no próximo vídeo, sem esta conversa. Tudo o que foi decidido nas rodadas
precisa estar escrito nela, com valor concreto: px no quadro 1080×1920, cor em hex, tempo em segundos ou em
âncora da fala. Os formatos dos JSONs citados aqui são os do contrato do kit (`docs/edicao-contrato.md` no
repositório `AosJunior/claude-skills`); a receita diz **quais valores** vão neles, nunca um formato novo.

## Onde cada receita mora

| Tipo | Arquivo | Quem lê |
|---|---|---|
| Estilo | `<pasta de edição>/marca/estilo.md`, um por pasta de edição: é a fonte única do jeito dela | `/decupar`, `/inserir`, `/sonorizar` e `/criticar`, que acham a pasta subindo a partir do vídeo |
| Formato | `<pasta de edição>/.claude/skills/<nome>/SKILL.md`; sem pasta de edição, `~/.claude/skills/<nome>/SKILL.md` (no Windows, `%USERPROFILE%\.claude\skills\`) | o Claude, quando ela edita um vídeo daquele formato |

- A receita de formato na pasta de edição entra quando o Claude Code está aberto nessa pasta. Na pasta do usuário, entra em qualquer pasta.
- Ao gravar o estilo, ponha junto o que ele cita: fontes em `marca/fontes/`, LUT em `marca/cor/`, Reels de referência em `marca/referencias/`, modelos de lettering em `marca/letterings/`. O estilo cita esses arquivos por caminho começando com `marca/`.
- Pasta ou arquivo com esse nome já existe: pare e pergunte. Se for a receita dela, é o caminho "Ajustar" da SKILL.md; se não, proponha outro nome.

## Receita de formato

Nome: minúsculas, sem acento, palavras ligadas por hífen, até 3 palavras, dizendo o que é (`receita-45s`, `react-rapido`, `gancho-dividido`).

Frontmatter:

```
---
name: <nome igual ao da pasta>
description: <o que é. Quando usar.>
---
```

A `description` é o que faz a receita entrar sozinha. Duas frases: (1) o formato com as palavras que a pessoa usa e o essencial dele; (2) "Use ao editar um vídeo de <assunto> ou quando a pessoa chamar /<nome>".

Moldes: [exemplos/ana-gancho-dividido/SKILL.md](exemplos/ana-gancho-dividido/SKILL.md) (com composição) e [exemplos/dica-rapida-30s/SKILL.md](exemplos/dica-rapida-30s/SKILL.md) (enxuto). Seções, nesta ordem:

1. Uma linha: o formato e o que quem assiste ganha.
2. `## Como editar` (abaixo).
3. `## Blocos`: tabela bloco · segundos (no vídeo final) · o que é dito · o que se vê. Mais duração alvo e faixa, pedido do fim com a frase exata e o que sempre sai.
4. `## Composição` (abaixo).
5. `## Conferir antes de entregar`: uma linha marcável por regra que dá para errar.
6. `## Melhorar esta receita` (bloco fixo) e `## Histórico`.

### Como editar

As 4 skills do kit, em ordem, cada uma com o que o formato decide nela. Escreva os passos com os valores do formato, não com remissão genérica:

1. **`/decupar`**: abrir a skill e seguir o fluxo dela com o bruto. O `cortes.json` usa a velocidade, o zoom e a cor do `marca/estilo.md`. Antes de cortar, mostrar o mapa nos blocos do formato: bloco · frases (`F<n>`) · segundos no vídeo final (o tempo do bruto dividido pela velocidade). Passou da duração máxima: proponha o que sai, nunca o gancho nem o pedido do fim.
2. **`/inserir`**: escrever o `insercoes.json` a partir da `## Composição`: a `divididas` do gancho, as `camadas` de cada bloco presas a palavras da fala, as faixas de `legenda` e o bloco `estilo` copiado do `marca/estilo.md`. Mídia de terceiros vai para `brutos/` com a origem em `brutos/fontes.md`.
3. **`/sonorizar`**: a trilha do universo do estilo, com a troca na virada de bloco que a composição marca, e os efeitos presos às camadas (`"camada": "<id>"`), cada um com motivo. A `entrega` copia vídeo, `legenda-curta.srt` e créditos para `entrega/`.
4. **`/criticar`**: rodar no vídeo com som. Cada item que reprova volta para a skill dona dele (emenda e gagueira: `ajustes` no `cortes.json`; posição e tempo de camada: `insercoes.json`; volume e trilha: `som.json`) e o kit roda de novo dali para frente. No máximo 2 voltas; o que ainda reprova vai para a pessoa, com a medida.
5. Entregar a pasta `entrega/` e perguntar o que ela corrigiu na mão (bloco de melhoria).

Se ela termina o vídeo num editor (CapCut, Premiere), acrescente o passo do editor com [editores.md](editores.md).

### Composição

Quem lê a composição é a `/inserir`: tudo vira `divididas`, `camadas` e `legenda`. Escreva:

- **Quadro e margens**: zona segura em y (o padrão é 260 a 1600: acima de 260 fica a barra do Instagram, abaixo de 1600 o nome, a legenda do post e os botões) e margem lateral (70 px). Botões do Instagram ocupam também a lateral direita de y 1100 a 1700: nada importante em x acima de 960 nessa faixa.
- **Camadas por bloco**: tabela bloco · pessoa (tela cheia, ou metade de baixo da dividida com `recorte_y`) · `atras` · `frente` · `topo` · legenda (y ou "some"). Cada camada com caixa em px (`x`, `y`, `w`; `h` quando importa), `rot`, `raio` e de onde vem a mídia (vídeo de outro criador, print, foto, lettering).
- **Âncoras na fala**: toda camada entra e sai numa âncora do contrato (`"F15:repente"`, `"F17:fim"`, `"F1:fim+0.25"`), nunca em segundo solto. Regra para escolher: entra na palavra que nomeia o que aparece; sai no fim da frase ou na entrada da próxima camada.
- **Densidade**: um evento visual (corte, camada, lettering, troca de legenda de lugar) a cada quantos segundos, o máximo sem evento (a `/criticar` reprova acima de 8 s) e quantas camadas ao mesmo tempo (no máximo 1 lettering e 1 camada de vídeo).
- **Posição por tipo de inserção**: tabela tipo · zona em y · lugar · o que acontece com a legenda. Ex.: lettering entre y 300 e 780, acima da cabeça; vídeo de outro criador `atras`, com máscara, ao lado da cabeça; print no peito com a legenda subindo.
- **Variação**: as posições se alternam (esquerda, direita, alto); a `/criticar` reprova inserções todas na mesma região.
- **Nunca**: o que a pessoa proibiu (ex.: cobrir o rosto), repetido aqui como regra de composição.

## Receita de estilo (`marca/estilo.md`)

Sem frontmatter: não é skill, é a marca. Moldes: [exemplos/estilo-ana/SKILL.md](exemplos/estilo-ana/SKILL.md) (completo) e [exemplos/legenda-limpa/SKILL.md](exemplos/legenda-limpa/SKILL.md) (só legenda). Seções, nesta ordem; a que ela não definiu fica de fora e vale o padrão do kit:

1. `# Estilo de <nome>` e uma linha: o jeito e a sensação que ele passa.
2. `## Fontes`: tabela uso · fonte (nome e peso) · arquivo em `marca/fontes/`.
3. `## Legenda`: tabela parâmetro · valor, e o bloco `estilo` do `insercoes.json` pronto para copiar. Inclui palavras por vez, minúsculas, nomes próprios, juntar números, tamanho, pé (`legenda_y`) e as alturas alternativas (na dividida, com inserção no peito), sombra e o **destaque**: fonte, escala e linha para onde ele sobe (`destaque_y`), e quando uma palavra vira destaque.
4. `## Corte e zoom`: velocidade, pausa máxima, níveis de zoom, âncora do zoom, duração típica do plano e quando o nível troca. Com o pedaço do `cortes.json` pronto para copiar.
5. `## Cor`: `"look": {"lut": "marca/cor/<nome>.cube"}`, de onde o LUT veio (bruto e exportação do editor dela) e o ΔE medido. Sem LUT, o look por números da `/decupar`.
6. `## Composição`: o vocabulário visual que vale em todo formato: tela dividida (emenda, metade de cima, headline), letterings (modelos em `marca/letterings/`, fontes, tamanhos, zona), camadas de vídeo (largura, raio, rotação, sombra, como entram), o que acontece com a legenda em cada caso. O formato decide **quando** e **onde**; o estilo decide **como parece**.
7. `## Som`: o universo da trilha (as 3 faixas que ela escolheu, com nome, autor e fonte; gênero; o que fica de fora), troca de trilha (em que momento, crossfade), efeitos permitidos e o motivo de cada um, volume (trilha abaixo da voz, -14 LUFS na entrega).
8. `## Nunca`: as proibições dela, uma por linha.
9. `## Conferir`: uma linha marcável por parâmetro que dá para errar. É a régua da `/criticar` para o estilo.
10. `## Melhorar esta receita` (bloco fixo) e `## Histórico`.

Palavra vaga vira número com régua visual ("grande" vira "116 px: a palavra mais longa ocupa até 2/3 da largura"). Se ela termina num editor, acrescente `## No editor` com os passos de [editores.md](editores.md).

## Bloco fixo de melhoria

Copie igual em toda receita:

```
## Melhorar esta receita

Ao entregar cada vídeo, pergunte: "O que você corrigiu na mão?". Cada correção, e cada item que a
/criticar reprovou duas vezes seguidas, vira regra aqui: troque a regra antiga pela nova (uma regra
por assunto, nunca duas versões), acrescente uma linha no Histórico com a data e o que mudou, e
mostre à pessoa a linha alterada.
```

## Histórico

Primeira linha: `- AAAA-MM-DD: criada com /minha-edicao.` e de onde vieram os valores (Reel de referência pelo link ou nome, "vídeo dela aprovado", "escolha na entrevista", "LUT do CapCut dela, ΔE 1,43"). Datas sempre completas.
