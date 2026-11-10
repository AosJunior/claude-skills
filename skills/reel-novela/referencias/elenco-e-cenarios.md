# Elenco e cenários

Como nascem as personagens e os lugares de uma série: aprovados uma vez, no portão 1, e reaproveitados em todos os
episódios. Só o que um roteiro pede e ainda não existe é gerado depois (passo 6 do `SKILL.md`). A identidade se segura
pelo figurino, pela cor-assinatura e pela silhueta, que o gerador repete bem; rosto e adorno de cabeça derivam entre
gerações. O conserto é um por vez: com dois de uma vez, não se sabe qual resolveu.

O estilo: pixel art de 16 bits, personagem de cabeça grande, luz pintada com brilho, névoa de luz e reflexo. Não é
pixel chapado.

## Trava de gasto

Toda geração paga segue esta trava, em qualquer gerador:

1. A sessão mostra à pessoa o lote (o que gerar, quantas tentativas, o preço de cada uma) e pede o sim com um teto em
   créditos ou em US$. O sim de um lote não vale para o próximo.
2. O preço vem da própria ferramenta antes de gerar (no Higgsfield, `get_cost: true`); depois, o extrato confirma e o
   total entra no `geracoes.md` da pasta.
3. Até 2 tentativas por asset. Se a segunda falhar, simplifique o pedido (menos objetos, pose mais simples).
4. Mudar roupa, objeto ou expressão de um asset aprovado é edição dele, nunca geração do zero.

`geracoes.md` de cada pasta, uma linha por geração: data, ferramenta e modelo, prompt exato, referências com o papel de
cada uma, configuração, custo e veredito.

## Gerador

A primeira calibração aprovou o `gpt_image_2_6` pelo conector do Higgsfield: veja a tabela abaixo e parta dela. Para
trocar de gerador ou calibrar um novo, com o sim e o teto da pessoa:

1. Escolha dois candidatos: os modelos de imagem do Higgsfield e outro gerador que a pessoa já use.
2. O mesmo molde de prompt da protagonista (abaixo), uma geração em cada.
3. Na que vencer, mais duas poses com a primeira como referência, e um cenário.
4. Compare: estilo igual ao da referência (luz pintada, cabeça grande), a mesma pessoa nas três poses, fundo fácil de
   recortar, custo por imagem.

Registre aqui, depois do piloto:

| Série | Gerador e modelo | Para quê | Configuração que funcionou | Custo por imagem | O que falhou |
|---|---|---|---|---|---|
| 1ª | Higgsfield, `gpt_image_2_6` | Folha de personagem (a protagonista), 6 poses em grade 3×2 | `quality: medium`, `resolution: 1k`, `aspect_ratio: 3:2`, `background: transparent`; prompt em inglês com «ONE single character repeated in six full-body poses», a cor da roupa em hex e as poses numeradas | 0,5 crédito | Nada na 1ª geração: mesmo rosto, cabelo e roupa nas seis poses, alfa limpo. Saiu em 1024×688, cada pose com ~250 px; ampliada a ~975 px no quadro, fica mole. Para o final, gerar em `2k` ou uma pose por imagem |
| 1ª | Higgsfield, `gpt_image_2_6` | Cenário 9:16 em três planos (jantar) | `quality: medium`, `resolution: 1k`, `aspect_ratio: 9:16`; prompt com «THREE DEPTH PLANES», a frente «cropped by the frame», o meio vazio «where a character will be placed later», «No text» | 0,5 crédito | Saiu em 752×1344 e mais pintado que pixelado. O meio veio vazio demais (um piso grande): peça o meio com menos área. A frente não vem separada: recortar |
| 1ª | Higgsfield, `gpt_image_2_6` | A mesma personagem em outra roupa (a protagonista de festa), 2 poses | A folha aprovada em `medias` com o papel `image_references` (o `job_id` da geração); prompt abrindo com «Same character as in the reference image (same face, same hair…)» e a roupa nova com a cor-assinatura; `3:2`, `medium`, `1k`, `transparent` | 0,5 crédito | Nada: rosto, cabelo, brincos e estilo iguais aos da folha. Com 2 poses por imagem, cada uma sai com ~560 px de altura, o dobro da folha de 6: prefira 2 ou 3 poses por geração |
| 1ª | Higgsfield, `gpt_image_2_6` | Elenco: coadjuvantes novos e poses novas, 3 por imagem; cenários em 2k | Personagem nova: a folha da protagonista em `image_references` com «Use the reference ONLY for the art style: this is a DIFFERENT character» (estilo igual, rosto outro). Três poses por imagem dão ~650 px de altura cada. Cenário: `9:16`, `medium`, `2k` (1520×2688, 1 crédito), com «MIDDLE GROUND, compact (NOT a large empty floor)» e a frente «filling only the bottom 18–22%» | 0,5 (personagem) · 1 (cenário 2k) | Em 1 de 5 folhas o fundo transparente falhou (fundo claro meio opaco, a de roupa branca): recorte pelo fundo claro ligado à borda (veja «Recorte»). No cenário de grupo, o coro saiu com a roupa e o coque da protagonista: diga a roupa do coro e «none has <marca da protagonista>» |

Preço conferido com `get_cost` na calibração (não gera nada): `low` 1k = 0,25; `medium` 1k = 0,5; `high` 2k = 2,75
créditos por imagem; confira de novo antes de cada lote, porque o preço muda.

Falta medir: um segundo personagem ao lado dela no mesmo quadro, e a frente do cenário gerada à parte.

## Folha de personagem

Pasta `elenco/<personagem>/`, uma por personagem da bíblia.

| Item | O que é | Pronto quando |
|---|---|---|
| Ficha | função na história, as dicotomias («o que ela é × o que o perfil mostra»), fatos fixos e relações, cor-assinatura (hex), 3 a 5 marcas fixas (roupa, acessório, cabelo), uma marca visível de costas | escrita em `elenco/<personagem>/ficha.md` (lição N2) |
| Folha | frente, três quartos, costas e busto, no mesmo fundo liso | a pessoa aprova no portão 1 |
| Poses | PNG com alfa, recortadas: em pé neutra (corpo inteiro, para o cartão das duas opções), busto neutro, constrangida, feliz, frustrada, olhando o telefone com a luz fria no rosto | cada pose passou na conferência de identidade |
| Expressões | busto em 4 a 6 emoções, no mesmo enquadramento, para o corte para o rosto | idem |

- A cor-assinatura segura a identidade mesmo pequena na tela (medida: cinco personagens, cinco cores, de preto e
  jeans a azul claro, lilás, verde com boné e vermelho). Duas personagens nunca dividem a mesma cor.
- Adorno de cabeça simples ou nenhum: é o que mais deriva entre gerações.
- Coadjuvante deriva mais que protagonista: ganha folha própria se aparece em mais de um episódio.
- Quem só aparece em mensagem (o dono do prazo, no exemplo da bíblia) tem só a foto de perfil e o nome.
- Quem vende não tem folha: é real e aparece só em vídeo, na tela do telefone.
- Os emotes (gota de suor, «!», «?», coração partido) são um jogo só por série, desenhados uma vez e usados por todas as
  personagens.

## Cenário em camadas

Pasta `cenarios/<lugar>/`, um por lugar da bíblia, com as três camadas da profundidade
([`regua-visual.md`](regua-visual.md), «Três planos de profundidade»):

| Arquivo | O que é |
|---|---|
| `fundo.png` | o lugar sem ninguém, com a luz do código da bíblia e os três objetos que caracterizam; 15% maior que o quadro nos dois sentidos, para o empurrão |
| `frente.png` | o objeto cortado na borda de baixo, PNG com alfa |
| `quadro-aprovado.png` | fundo, personagem e frente montados em 1080×1920: a referência de luz e de escala para os episódios |

Gere o fundo já sem personagem; a personagem entra recortada por cima. Assim a mesma pose serve em vários lugares e a
luz do lugar se ajusta no motion. Se o gerador não separar a frente, recorte-a do fundo e preencha o buraco por edição.

## Moldes de prompt

Quem escreve é um agente Opus, em high, a partir da bíblia. Os moldes ficam fixos na série: muda só o que está entre
`<>`. O texto exato de cada prompt aprovado vai para o `geracoes.md`.

**Personagem:**

```
Pixel art de 16 bits, estilo de jogo de aventura, personagem de cabeça grande e corpo pequeno, luz pintada com brilho
suave e reflexo, contorno escuro de 1 pixel. <nome>, <idade aparente>, <corpo e cabelo>. Roupa: <marcas fixas, cada
uma com a cor>. Cor-assinatura <cor> dominante. Pose: <pose>, <expressão>. Corpo inteiro, de frente, centrado, fundo
liso <cor neutra que não aparece na roupa>, sem sombra no chão, sem texto, sem moldura, sem outros personagens.
```

**Cenário:**

```
Pixel art de 16 bits, cenário de jogo de aventura em vertical 9:16, luz pintada com névoa e reflexo. <lugar>. Primeiro
plano: <objeto> cortado pela borda de baixo. Plano do meio: espaço livre no centro, sem ninguém. Fundo: <o que se vê>,
iluminado por <luz do código>. Objetos que caracterizam: <três objetos>. Sem pessoas, sem texto legível, sem moldura.
```

Uma referência por papel, dita no prompt quando a ferramenta aceita imagem: a folha aprovada para a identidade, o
`quadro-aprovado` do lugar para a luz, um quadro da referência só para o estilo.

## Recorte

Cada pose e cada frente sai com alfa: peça fundo transparente ao gerador e, quando ele falhar, use a remoção de fundo
do Higgsfield ou um recorte local pela cor do fundo ligada à borda (um script curto com Pillow). Prova do recorte: a pose sobre um fundo escuro e sobre um claro, a 2×, sem halo nem
borda da cor do fundo original.

## Conferência de identidade

Toda imagem nova de personagem vai lado a lado com a folha aprovada, numa folha só, antes de entrar em cena:

- [ ] a cor-assinatura é a mesma;
- [ ] todas as marcas fixas estão lá, inclusive a de costas quando aparece;
- [ ] a silhueta e a proporção da cabeça batem;
- [ ] cabelo e adorno iguais;
- [ ] mesma idade aparente;
- [ ] nada a mais na mão ou no corpo (telefone, objeto) que a pose não pediu.

Reprovada num item, conserte por edição, um item por vez. O veredito vai para o `geracoes.md`.
