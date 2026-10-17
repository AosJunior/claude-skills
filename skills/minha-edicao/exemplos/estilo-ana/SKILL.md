---
name: estilo-ana
description: Estilo de edição da Ana para Reels: legenda em Neue Montreal Regular com Apple Garamond nas palavras de destaque, cor quente e suave (Gastronômico + Verão Italiano), cartões verde-escuro e efeitos sonoros de clique. Use ao legendar, colorir, sonorizar ou pôr inserções num vídeo da Ana, inclusive dentro da /inserir.
---

# Estilo da Ana

Legenda fina e calma, uma palavra por frase em serifa para dar o tom, cor quente sem saturar e som de
clique só quando algo acontece na tela.

## Fontes (os arquivos ficam no computador da Ana)

Este repositório não leva arquivo de fonte: as fontes são licenciadas e ficam só na máquina da pessoa.
Antes de usar, confira o caminho dos arquivos; se não estiverem lá, pergunte onde estão.

| Uso | Fonte | Arquivo |
|---|---|---|
| Legenda e texto dos cartões | Neue Montreal **Regular** (nunca a Medium) | `NeueMontreal-Regular.otf` |
| Palavras de destaque, títulos e números | Apple Garamond (regular) | `AppleGaramond.ttf` |

Na máquina do Junior: `producao/2026-10-17-aula-edicao-video-ia/video-ana/brutos/fontes/`. As duas têm
acentuação completa (o "Ã" do "NÃO" sai na mesma fonte).

## Legenda

Medidas no quadro do Reel, 1080 × 1920 px.

| Parâmetro | Valor |
|---|---|
| Tamanho | 64 px (o "tamanho 20" do CapCut); régua: 4 palavras ocupam no máximo 3/4 da largura |
| Cor | branco `#FFFFFF`, destaque também branco: o destaque é a troca para Apple Garamond, 12% maior |
| Destaque | 1 palavra a cada 5 a 8 s, a que carrega a frase ("pobre", "milhões", "conteúdo") |
| Letra | normal, como se escreve; nunca tudo maiúsculo |
| Sombra | preta a 60%, macia (a cena tem mão, pele e produto branco atrás da legenda); sem contorno e sem caixa |
| Palavras por vez | 2 a 4, numa linha só |
| Posição | centralizada, pé das letras em y = 1400 px, abaixo do queixo e acima dos botões do Instagram |
| Animação | nenhuma: aparece e some com a fala |

## Cartões de inserção

Fundo verde-escuro `#22372B` (o verde da parede do escritório dela), texto creme `#F3EDE2`, destaque
dourado `#E2C48E` em Apple Garamond. Nos planos abertos (ela sentada à mesa, cabeça abaixo de 680 px)
o cartão vai em **painel** no alto da tela, sobre a parede, e o produto que ela mostra continua à
vista; tela cheia só para o print de site. Corte seco; a legenda continua por baixo.

## Cor

- No CapCut: Contraste −4 · Sombra −2 · filtros "Gastronômico" (3) + "Verão Italiano" (24).
- Fora do CapCut (ffmpeg, Premiere, DaVinci): contraste um pouco menor, sombras um pouco mais escuras,
  tom quente suave. Pele natural, nada de saturar. A mesma cor em todas as tomadas.

## Som

Efeitos sonoros: film clicker, click e "Ba dum tss", só quando algo acontece na tela (entra um cartão,
uma piada fecha). Pouco.

## Como aplicar

**Na /inserir**: o bloco `estilo` do `insercoes.json` fica assim (troque a pasta pela da máquina):

```json
"estilo": {
  "fonte": "<pasta das fontes>/NeueMontreal-Regular.otf",
  "fonte_destaque": "<pasta das fontes>/AppleGaramond.ttf",
  "tamanho": 64, "cor": "#FFFFFF", "cor_destaque": "#FFFFFF", "escala_destaque": 1.12,
  "sombra": 0.6, "legenda_y": 1400,
  "cartao_fundo": "#22372B", "cartao_tinta": "#F3EDE2", "cartao_destaque": "#E2C48E"
}
```

**No CapCut do computador**: importe a `legenda-curta.srt`, fonte Neue Montreal Regular, tamanho 20,
branco, sombra leve, sem contorno. Nas palavras de destaque, selecione a palavra e troque para Apple
Garamond.

## Conferir

- [ ] Legenda em Neue Montreal Regular (não Medium), destaque em Apple Garamond
- [ ] O "Ã", o "Ç" e o "É" na mesma fonte da palavra
- [ ] Nenhuma legenda em cima da boca ou do queixo, nem abaixo de 1440 px
- [ ] Pele natural depois do filtro

## Melhorar esta receita

Ao entregar cada vídeo, pergunte: "O que você corrigiu na mão?". Cada correção vira regra aqui: troque a
regra antiga pela nova, acrescente uma linha no Histórico com a data e o que mudou, e mostre à pessoa a
linha alterada.

## Histórico

- 2026-10-17: criada como exemplo da aula, a partir do que a Ana usa no CapCut; tamanho conferido no
  vídeo de 17/10 (64 px).
