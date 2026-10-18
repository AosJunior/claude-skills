---
name: minha-edicao
description: Receita de edição da pessoa, escrita a partir dos Reels dela. Mede a referência e grava o estilo em marca/estilo.md (legenda, zoom, cor por LUT, letterings, tela dividida, trilha) ou uma skill de formato de Reel (blocos, gancho, composição das camadas) que encadeia /decupar, /inserir, /sonorizar e /criticar. Use quando a pessoa quiser criar ou ajustar o jeito dela de editar, ou pedir que os vídeos fiquem sempre de um jeito.
---

# /minha-edicao

Uma receita para cada formato de conteúdo e um estilo por marca: quem escreve a receita uma vez para de editar
do zero. Esta skill mede os Reels que a pessoa já aprovou, pergunta só o que é decisão dela, mostra a receita
aplicada no vídeo dela e grava. Dois tipos:

- **Estilo**: como o vídeo parece e soa (fontes, legenda e destaque, zoom e ritmo, cor por LUT, letterings,
  tela dividida, camadas, trilha e efeitos). Vai para `<pasta de edição>/marca/estilo.md`, a fonte única que
  as 4 skills do kit leem.
- **Formato**: o que um tipo de vídeo precisa ter (duração, gancho, blocos com segundos, pedido do fim) e a
  **composição** de cada bloco (camadas, posições em px, âncoras na fala, densidade). É uma skill que encadeia
  `/decupar` → `/inserir` → `/sonorizar` → `/criticar`.

Quem usa é criador de conteúdo leigo, no Claude Code Desktop, Mac ou Windows. Os scripts ficam em
`<pasta desta skill>/scripts/`.

## Como conversar

- Fale como quem faz Reels. Termo técnico só com a tradução ao lado, na primeira vez: "pedido do fim (CTA)",
  "LUT (o filtro de cor dela, copiado)". Quando o conteúdo dela também é receita (cozinha), chame a skill de
  "receita de edição".
- **Fatos** são trabalho seu: medir, olhar, ler. **Decisões** são da pessoa. O que a medida responde vira
  afirmação para confirmar ("seu Reel aprovado troca de plano a cada 2,4 s, com zoom de 1,12, 1,2 e 1,3"),
  nunca pergunta.
- Em cada rodada, pergunte toda a fronteira: tudo o que já dá para decidir sem chutar, no máximo 5 perguntas,
  numeradas, cada uma com a sua recomendação. A pessoa pode responder "ok" ou só os números que quer mudar.
- No máximo 3 rodadas. Uma pergunta que a mensagem da pessoa já respondeu sai da rodada.

```
**1. <título curto>**: <pergunta, com as opções>
**Recomendo:** <a opção e o porquê, em 1 linha>
```

## Passos

### 1. Rodada 1: o tipo e o material

Antes de perguntar, em silêncio: `ffmpeg -version`, `uv --version`, o sistema (Mac ou Windows) e a **pasta de
edição**: suba a partir da pasta aberta até achar `marca/estilo.md`. Achou: leia o estilo (pedido de estilo
vira o caminho "Ajustar"; o formato novo usa esse estilo). Não achou: a pasta aberta vira a pasta de edição,
com o layout do contrato do kit (`marca/` e `videos/`), e isso entra na confirmação da rodada 3.

Pergunte:

1. **Estilo ou formato**: "Quer gravar o seu **estilo** (o jeito de todo vídeo seu: legenda, zoom, cor, letterings,
   trilha) ou um **formato** (um tipo de vídeo que você repete: react com tela dividida, dica rápida, antes e
   depois)?" Sem `marca/estilo.md`, recomende o estilo primeiro: o formato usa as fontes, a cor e o som dele.
2. **Reels de referência**: "Mande 1 a 3 Reels que são o jeito que você quer (link ou arquivo)." Recomende
   mandar: você mede e ela responde menos.
3. **Vídeo seu aprovado**: "Tem um vídeo seu que saiu do jeito certo? Arraste aqui." Ele vale mais que a
   referência quando os dois discordam.
4. **Cor** (só estilo): "Para copiar a sua cor, preciso de um vídeo bruto seu e do mesmo vídeo exportado do seu
   editor com o filtro que você usa." Recomende mandar: o LUT copia a cor exata (no Reel da Ana, a diferença
   ficou em 1,43 contra 5,46 do ajuste feito no olho).
5. **Onde o vídeo termina**: o kit entrega pronto (legenda gravada, cor, trilha, volume de publicação) ou ela
   termina no CapCut ou no Premiere. Recomende o kit; quem termina no editor recebe os passos de
   [editores.md](editores.md).

Sem referência e sem vídeo, ofereça partir de um exemplo pronto: `exemplos/estilo-ana/` (estilo completo),
`exemplos/legenda-limpa/` (só legenda), `exemplos/ana-gancho-dividido/` (formato com composição) ou
`exemplos/dica-rapida-30s/` (formato enxuto). Ela só muda o que for diferente.

Feito quando o tipo está decidido, a pasta de edição está definida e cada material foi recebido ou dispensado.

### 2. Medir o material

Siga [medir.md](medir.md): ele começa conferindo qual Reel é qual pela folha e monta a **ficha** de cada vídeo.
Mostre à pessoa o que você viu em até 8 linhas ("No seu Reel aprovado: 134 s, fala a 1,2×, troca de plano a
cada 2,4 s com zoom de 1,12, 1,2 e 1,3; legenda de 1 palavra no peito; gancho em tela dividida até 13 s...").
Se a referência e o vídeo dela discordam num ponto, vale o vídeo dela; a discordância só vira pergunta quando
ela pediu explicitamente o jeito da referência.

Feito quando cada linha da ficha tem um valor ou "não deu para ver".

### 3. Rodada 2: as decisões dela

Pergunte só o que a medida não responde. Pergunta que a ficha responde sai. Em cada pergunta, a recomendação
traz a proposta completa, com números, para ela só corrigir.

**Estilo**
1. **Origem padrão do gancho**: o que vai na metade de cima da tela dividida (vídeo de outro criador, cena
   filmada que prova o assunto, o produto) ou se o gancho é em tela cheia.
2. **Universo da trilha**: 3 faixas que definem o som dela (proponha as que o Shazam achou nos Reels dela).
   As 3 viram a régua da `/sonorizar`: trilha nova só entra se couber nesse universo.
3. **O que nunca pode**: o que a edição não faz nunca (ex.: cobrir o rosto, som de piada, legenda em
   maiúsculas).
4. Cada "não deu para ver" da ficha.

**Formato**
1. **Duração**: alvo e máximo (proponha a do vídeo aprovado).
2. **Blocos**: a sequência medida, com segundos, para ela confirmar ou mudar a ordem.
3. **Pedido do fim (CTA)**: seguir, salvar, compartilhar ou comentar, e a frase exata.
4. **Origem do gancho**, se o estilo não fixou.

Feito quando toda regra que a receita vai guardar tem um valor concreto: número, cor, nome de fonte, segundos.

### 4. Prova antes de gravar

Com um vídeo dela em mãos, monte 1 quadro-teste por bloco (gancho, corpo com lettering, corpo com camada
atrás dela, pedido do fim), com o vídeo dela e a receita aplicada, ao lado da referência no mesmo momento:
escreva `marca/referencias/prova.json` (formato no topo do script) e rode

```
uv run "<pasta desta skill>/scripts/prova.py" "marca/referencias/prova.json"
```

Mostre `marca/referencias/prova/folha.png`. O que ela apontar volta como ajuste da regra e a prova é refeita
uma vez. Sem nenhum vídeo dela, diga que a prova fica para o primeiro vídeo e siga.

Feito quando ela aprovou a prova (ou a prova foi dispensada por falta de vídeo).

### 5. Rodada 3: confirmar

Mostre a receita em lista curta: onde vai ser gravada (o arquivo e a pasta de edição), quando entra (em
palavras simples: "toda skill do kit lê esse estilo quando o vídeo está dentro desta pasta"; "ela entra quando
você pedir para editar um react"), as regras com os valores e os arquivos que vão para `marca/` (fontes, LUT,
referências). Pergunte o que ainda estiver em aberto e "Posso gravar?".

Feito quando a pessoa disse sim.

### 6. Escrever a receita

Siga [receita.md](receita.md) (lugar, seções de cada tipo, composição, bloco de melhoria):

- **Estilo**: `<pasta de edição>/marca/estilo.md`, e os arquivos que ele cita em `marca/fontes/`, `marca/cor/`,
  `marca/referencias/` e `marca/letterings/`. Copie as fontes e o LUT para lá; o original dela não sai do lugar.
- **Formato**: `<pasta de edição>/.claude/skills/<nome>/SKILL.md`; sem pasta de edição,
  `~/.claude/skills/<nome>/SKILL.md`.

Feito quando o arquivo existe, todo caminho com `marca/` que ele cita existe, todo valor decidido nas rodadas
está nele e nenhuma decisão ficou para preencher depois (marcador do que muda a cada vídeo, como
`<TEXTO DA HEADLINE>`, fica). No formato, o `name` é igual ao nome da pasta. Leia o arquivo uma vez para
conferir.

### 7. Mostrar e ensinar

Resuma em 5 linhas:
1. O que foi gravado e onde.
2. Quando entra sozinho.
3. As 3 regras que mais mudam o vídeo.
4. Como usar: estilo, "abra o Claude Code na pasta de edição, ponha o vídeo em `videos/<data>-<assunto>/` e
   peça `/decupar`"; formato, "digite `/<nome>` e arraste o vídeo".
5. Como melhorar: "Depois de cada vídeo, me diga o que você corrigiu na mão, e eu atualizo a receita."

Se o `/<nome>` não aparecer, peça para rodar `/reload-skills` ou abrir uma conversa nova na pasta de edição.
Ofereça, em uma linha, criar a outra metade (o formato para quem fez o estilo, e o contrário).

## Ajustar uma receita que já existe

Quando a pessoa pede para mudar uma receita dela: leia o `marca/estilo.md` ou o `SKILL.md` do formato, mostre a
regra atual, pergunte só o que muda (uma rodada), faça a prova do bloco afetado quando a mudança é visual e
aplique o bloco "Melhorar esta receita" da própria receita: a regra nova substitui a antiga e o histórico ganha
uma linha.
