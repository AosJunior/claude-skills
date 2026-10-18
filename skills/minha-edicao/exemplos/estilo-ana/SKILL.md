# Estilo da Ana

> Exemplo de `marca/estilo.md`. Na pasta de edição, este texto mora em `marca/estilo.md`, sem cabeçalho de
> skill: as 4 skills do kit o leem quando o vídeo está dentro da pasta. As fontes, o LUT e os sons citados
> ficam em `marca/` na máquina dela; este repositório não leva nenhum deles.

Uma palavra por vez no peito, a palavra que importa em serifa itálica acima da cabeça, zoom seco em níveis
fixos, cor quente copiada do CapCut dela e cordas e jazz por baixo: parece revista, não tutorial.

## Fontes

| Uso | Fonte | Arquivo |
|---|---|---|
| Legenda, headline, números dos letterings | Neue Montreal **Bold** | `marca/fontes/NeueMontreal-Bold.otf` |
| Destaque e complemento dos letterings | Apple Garamond **Italic** | `marca/fontes/AppleGaramond-Italic.ttf` |

As duas têm acentuação completa ("ã", "ç" e "é" saem na mesma fonte da palavra).

## Legenda

Medidas no quadro de 1080×1920, y = 0 no topo; "pé" é a linha de base das letras.

| Parâmetro | Valor |
|---|---|
| Palavras por vez | 1. Número sai junto com o que o acompanha ("100 mil", "R$ 18 milhões", "10, 20") |
| Letra | minúscula; nome próprio com maiúscula (lista `nomes`, por vídeo) |
| Fonte · tamanho · cor | Neue Montreal Bold, 116 px, branco `#FFFFFF` |
| Sombra | preta a 45%, difusa; sem contorno, sem caixa |
| Posição | centralizada, pé em y 1290 (no peito, abaixo do queixo); na tela dividida, pé em y 1190 |
| Destaque | a palavra que carrega a frase ("doido?", "comuns", "propaganda", "experimentar", "aluga-se") troca para Apple Garamond Italic, 1,75× (203 px), e sobe para pé em y 760, acima da cabeça. Uma a cada 8 a 15 s |
| Troca | seca, no tempo da palavra, sem animação |
| Some | enquanto a headline do gancho está na tela e durante lettering de número |

Bloco `estilo` do `insercoes.json`:

```json
"estilo": {
  "fonte": "marca/fontes/NeueMontreal-Bold.otf",
  "fonte_destaque": "marca/fontes/AppleGaramond-Italic.ttf",
  "tamanho": 116, "palavras_max": 1, "letras_max": 30,
  "minusculas": true, "juntar_numeros": true, "nomes": ["<NOMES PRÓPRIOS DO VÍDEO>"],
  "legenda_y": 1290, "margem": 70, "sombra": 0.45,
  "escala_destaque": 1.75, "destaque_y": 760,
  "zona_segura": [260, 1600]
}
```

## Corte e zoom

| Parâmetro | Valor |
|---|---|
| Velocidade da fala | 1,2× (vídeo e voz juntos) |
| Pausa máxima | 0,22 s |
| Zoom | só os níveis 1,0 · 1,12 · 1,2 · 1,3, parados durante o plano (sem rampa), âncora perto dos olhos |
| Padrão | vai e volta: um plano entra num nível, o seguinte volta para 1,0; 1,3 fica para ênfase ou piada |
| Plano | cerca de 2,6 s; cada frase nova ganha enquadramento novo |

Pedaço do `cortes.json`:

```json
"pausa_max": 0.22,
"velocidade": 1.2,
"zoom": {"ancora": [0.49, 0.36], "niveis": [1.0, 1.12, 1.2, 1.3], "alternar_na_pausa": true},
"cor": {"corrigir": false, "look": {"lut": "marca/cor/ana-capcut.cube"}}
```

## Cor

LUT `marca/cor/ana-capcut.cube`, ajustado com o `lut_capcut.py` da `/decupar` a partir de um bruto dela e da
exportação do mesmo vídeo no CapCut com o filtro dela. Diferença média (ΔE00) num trecho fora do ajuste: 1,43.
O look feito no olho, com contraste, sombra e filtros por número, ficou em 5,46 e foi abandonado. Um look só:
nada de filtro por cima do LUT.

## Composição

**Tela dividida (gancho)**
- Emenda em y 960. Embaixo, ela, num take contínuo, com os olhos a cerca de 56% da metade de baixo.
- Em cima, o vídeo do gancho em 720×960 no centro, com as laterais preenchidas pelo mesmo vídeo ampliado e
  borrado. Ritmo em pares: aberto por 1,0 s, depois zoom seco no detalhe (a placa, o preço) por 1,63 s.
- Headline: caixa `#FCFCFC` de 898×104 px em x 91, y 908 (monta em cima da emenda), raio 17, sem borda e sem
  sombra; texto em Neue Montreal Bold 58 px, `#111111`, numa linha. Fica do início até o fim da primeira frase
  mais 0,25 s; depois a legenda volta, com pé em 1190, até o fim da dividida.
- A dividida termina num destaque e num corte seco para ela em tela cheia.

**Letterings**
- Entre y 300 e 780, acima da cabeça. Número em Neue Montreal Bold grande, com o complemento embaixo em Apple
  Garamond Italic ("+100 mil / produtos vendidos", "R$ 18 / milhões"); citação de obra com uma linha pequena
  em caixa alta e o título em itálico ("O LIVRO / O Animal Social").
- Modelos em `marca/letterings/`. Entram com pop de 0,14 s; a legenda some enquanto um lettering de número
  está na tela.

**Vídeos de outros criadores**
- Atrás dela, com máscara (`lugar: "atras"`): o rosto e as mãos ficam na frente.
- Cartões de cerca de 390 px de largura, raio 26, inclinados até 6°, sombra a 35%. Em mosaico de 2 a 3 no
  alto da tela ou espalhados em volta da cabeça.
- Entram com pop de 0,18 s na palavra que os nomeia e saem em 0,12 s.

## Som

- **Universo da trilha**: cordas calmas e jazz instrumental, do Epidemic Sound, identificados com o Shazam
  nos Reels dela. Referências: "Strings in Solitude 3" e "Gentlemen". Fica de fora: pop, eletrônica, trilha de
  suspense.
- **Troca de trilha**: na virada de bloco ("Isso porque..."), das cordas para o jazz, com crossfade de 0,4 s
  e um swoosh.
- **Volume**: trilha 16 dB abaixo da voz; entrega em -14 LUFS.
- **Efeitos**, cada um com motivo: pop (vídeos de outros criadores entram), kaching (lettering de dinheiro),
  clique (lettering de número), página virando (livro citado), swoosh (virada de bloco), whoosh curto (zoom seco
  do gancho), ding (pedido do fim).

## Nunca

- Cobrir o rosto: lettering acima da cabeça, vídeos atrás dela.
- Legenda em maiúsculas ou com mais de uma palavra (fora os números).
- Cartão chapado colorido atrás de texto.
- Filtro do editor por cima do LUT.
- Som de piada ("ba dum tss", risada).

## Conferir

- [ ] Legenda em Neue Montreal Bold 116 px, 1 palavra, minúscula, pé em 1290 (1190 na dividida)
- [ ] Destaque em Apple Garamond Italic 1,75×, pé em 760, legível (o "h" itálico não pode ser lido como "b")
- [ ] Zoom só em 1,0 · 1,12 · 1,2 · 1,3, sem rampa
- [ ] Emenda da dividida em 960 e headline de 898×104 em y 908
- [ ] Nenhum lettering fora de y 300 a 780; nenhum vídeo na frente do rosto
- [ ] Pele igual à do CapCut dela (LUT aplicado uma vez só)
- [ ] Trilha no universo de cordas e jazz; nenhum efeito sem motivo

## Melhorar esta receita

Ao entregar cada vídeo, pergunte: "O que você corrigiu na mão?". Cada correção, e cada item que a
/criticar reprovou duas vezes seguidas, vira regra aqui: troque a regra antiga pela nova (uma regra
por assunto, nunca duas versões), acrescente uma linha no Histórico com a data e o que mudou, e
mostre à pessoa a linha alterada.

## Histórico

- 2026-10-17: criada como exemplo da aula, a partir do que a Ana usa no CapCut.
- 2026-10-18: reescrita com as medidas do Reel aprovado "Ter loja virou coisa de pobre?" (134 s): legenda
  Bold 116 px de 1 palavra (era Regular 64 de 2 a 4), pé em 1290 (era 1400), destaque Italic 1,75× subindo para
  760 (era regular 12% maior na mesma linha), vídeos de outros criadores atrás dela (eram cartões verdes),
  LUT do CapCut com ΔE 1,43 (eram filtros 3 + 24), cordas e jazz e efeitos com motivo (saiu o "ba dum tss").
