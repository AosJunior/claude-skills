---
name: minha-edicao
description: Receita de edição da pessoa, escrita como skill nova. Entrevista e cria uma skill para um formato de Reel (dica rápida, react, bastidor, antes e depois) ou para um estilo de edição (legenda, cortes, ritmo, letterings, cor, som, transições). Use quando a pessoa quiser criar ou ajustar uma skill do jeito dela de editar, ou pedir que os vídeos fiquem sempre de um jeito.
---

# /minha-edicao

Uma skill para cada formato de conteúdo e uma para cada estilo de edição: quem escreve a **receita** uma vez para de editar do zero. Esta skill entrevista a pessoa e escreve essa receita como skill nova. Dois tipos:

- **Receita de formato**: o que o vídeo precisa ter (duração, gancho, estrutura, pedido do fim). Encadeia a `/decupar` (decupagem → corte → legenda) e acrescenta as regras do formato.
- **Receita de estilo**: como o vídeo parece e soa (fonte, tamanho, cor, posição, palavras por vez, ritmo de corte, som) e como aplicar no CapCut ou no Premiere.

Quem usa é criador de conteúdo leigo, no Claude Code Desktop, Mac ou Windows.

## Como conversar

- Fale como quem faz Reels. Termo técnico só com a tradução ao lado, na primeira vez: "pedido do fim (CTA)", "música que abaixa quando você fala". Quando o conteúdo dela também é receita (cozinha, confeitaria), chame a skill de "receita de edição".
- **Fatos** são trabalho seu: medir, olhar, ler. **Decisões** são da pessoa. O que a referência já mostra vira afirmação para confirmar ("seu Reel de referência tem 31 s, a receita mira 30 s"), nunca pergunta.
- Em cada rodada, pergunte toda a fronteira: tudo o que já dá para decidir sem chutar, no máximo 5 perguntas, todas numeradas e cada uma com a sua recomendação. A pessoa pode responder "ok" ou só os números que quer mudar.
- No máximo 3 rodadas. Uma pergunta que a mensagem da pessoa já respondeu sai da rodada.

```
**1. <título curto>**: <pergunta, com as opções>
**Recomendo:** <a opção e o porquê, em 1 linha>
```

## Passos

### 1. Rodada 1: o tipo e o material

Antes de perguntar, confira em silêncio se o ffmpeg está instalado (`ffmpeg -version`) e qual é o sistema (Mac ou Windows). Depois pergunte:

1. **Formato ou estilo**: "Quer uma receita de **formato** (um tipo de vídeo que você repete: dica rápida, react, bastidor, antes e depois, receita) ou de **estilo** (o jeito de editar: legenda, cortes e ritmo, letterings (frases grandes na tela), cor, som, transições)? Se for estilo, de qual parte?" Recomende formato para quem repete o mesmo tipo de vídeo toda semana; estilo para quem perde mais tempo deixando o vídeo com a sua cara.
2. **Reel de referência**: "Tem um Reel que é o jeito que você quer? Mande o link ou arraste o arquivo aqui." Recomende mandar: você mede e a pessoa responde menos.
3. **Vídeo seu já editado**: "Tem um vídeo seu já editado do jeito que você gosta? Arraste aqui." Recomende mandar, pelo mesmo motivo.
4. **Onde você monta o vídeo**: CapCut no celular, CapCut no computador, Premiere ou outro editor. Se ela disser só "CapCut", pergunte celular ou computador. Recomende o computador, onde ela já está com o Claude: a legenda que o Claude faz entra direto no CapCut do computador e no Premiere; no CapCut do celular ela refaz a legenda à mão.

Sem referência e sem vídeo, ofereça partir de um exemplo pronto desta skill (`exemplos/dica-rapida-30s/` para formato, `exemplos/legenda-limpa/` para estilo; `exemplos/estilo-ana/` mostra um estilo completo, com legenda, cartões, cor e som): ela só muda o que for diferente.

Feito quando o tipo (e, no estilo, as partes) está decidido, o editor está definido e cada material foi recebido ou dispensado.

### 2. Medir o material (só se veio referência ou vídeo)

Siga [medir.md](medir.md): ele monta a **ficha** de cada vídeo. Mostre à pessoa o que você viu em até 6 linhas ("No Reel de referência: 31 s, troca de plano a cada 2,1 s, legenda de 3 palavras no terço de baixo, sem caixa de fundo..."). Se a referência e o vídeo dela discordam num ponto, esse ponto vira pergunta da rodada 2, com as duas medidas lado a lado.

Feito quando cada item da ficha tem um valor ou "não deu para ver". Só os "não deu para ver" e as discordâncias seguem como pergunta.

### 3. Rodada 2: as regras

Pergunte só o que a ficha não respondeu. Em cada pergunta, a recomendação já traz a proposta completa, com números, para a pessoa só corrigir ("Proponho: fonte Inter Medium, branca, sombra leve, 2 a 4 palavras por vez. Muda alguma coisa?").

**Formato**
1. **Duração**: alvo e máximo.
2. **Gancho**: o que acontece nos 3 primeiros segundos (frase falada, texto na tela, o resultado pronto primeiro).
3. **Estrutura**: os blocos do vídeo, em ordem, com os segundos de cada um.
4. **Pedido do fim (CTA)**: seguir, salvar, compartilhar ou comentar uma palavra, e a frase exata.
5. **Legenda**: o visual da legenda mora numa receita de estilo, separada da de formato. Liste as receitas de estilo que encontrar em `~/.claude/skills/`. Sem nenhuma, e com a legenda dela medida, recomende criar junto a receita de estilo dessa legenda: as duas entram na confirmação da rodada 3 e são gravadas no passo 5. Sem medida, a legenda padrão da `/decupar` por enquanto.

**Estilo**, por parte escolhida (junte numa pergunta só os itens de uma parte):
- **Legenda**: fonte, tamanho (quanto da largura a frase ocupa), cor e destaque, posição, palavras por vez, letra maiúscula ou normal, contorno, fundo ou sombra.
- **Cortes e ritmo**: pausa máxima que fica, erros e repetições, zoom no rosto (quando), troca de plano a cada quantos segundos.
- **Letterings**: quando entram (frase de efeito, número, palavra-chave), quantos por vídeo, fonte e posição.
- **Cor**: mais quente, mais fria, mais contraste, ou o filtro do editor e a intensidade.
- **Som**: música (tipo e volume embaixo da voz), efeitos sonoros (em quais momentos), limpeza da voz.
- **Transições**: corte seco, zoom ou deslizar, e onde.

Feito quando toda regra que a receita vai guardar tem um valor concreto: número, cor, nome de fonte, segundos.

### 4. Rodada 3: confirmar

Mostre a receita em lista curta: nome proposto (regra em [receita.md](receita.md)), onde vai ser gravada, quando ela entra sozinha (em palavras simples: "ela entra quando você pedir para editar uma receita de 45 s") e as regras com os valores. Pergunte o que ainda estiver em aberto e "Posso gravar?".

Feito quando a pessoa disse sim.

### 5. Escrever a receita

Siga [receita.md](receita.md) (nome, description, seções de cada tipo, bloco de melhoria). Grave em `~/.claude/skills/<nome>/SKILL.md`. Se a pessoa usa CapCut ou Premiere, a parte "como aplicar" vem de [editores.md](editores.md).

Feito quando o arquivo existe, o `name` é igual ao nome da pasta, todo valor decidido nas rodadas está nele e nenhuma decisão ficou para preencher depois (marcador do que muda a cada vídeo, como `<NOME DA RECEITA>`, fica). Leia o arquivo uma vez para conferir.

### 6. Mostrar e ensinar

Resuma em 5 linhas:
1. Nome da receita e onde ela está.
2. Quando ela entra sozinha.
3. As 3 regras que mais mudam o vídeo.
4. Como usar: "digite `/<nome>` e arraste o vídeo, ou diga 'edita esse vídeo como <nome>'".
5. Como melhorar: "Depois de cada vídeo, me diga o que você corrigiu na mão, e eu atualizo a receita."

Se o `/<nome>` não aparecer quando ela digitar, peça para rodar `/reload-skills` ou abrir uma conversa nova. Ofereça, em uma linha, criar a outra metade do par (a de estilo para quem fez formato, e o contrário).

## Ajustar uma receita que já existe

Quando a pessoa pede para mudar uma receita dela: leia o `SKILL.md`, mostre a regra atual, pergunte só o que muda (uma rodada) e aplique o bloco "Melhorar esta receita" da própria receita: a regra nova substitui a antiga e o histórico ganha uma linha.
