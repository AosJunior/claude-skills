# Estilo: legenda limpa

> Exemplo de `marca/estilo.md` que só define a legenda. Na pasta de edição, este texto mora em
> `marca/estilo.md`; o que ele não define (cor, zoom, som, composição) fica no padrão de cada skill do kit.

Legenda que se lê sem gritar: frase curta, letra de peso médio, nada em volta do texto.

## Fontes

| Uso | Fonte | Arquivo |
|---|---|---|
| Legenda | Inter Medium; sem ela, Montserrat Medium ou Poppins Medium. Peso médio, nunca Black ou Extra Bold | `marca/fontes/Inter-Medium.ttf` |

## Legenda

Medidas no quadro de 1080×1920, y = 0 no topo; "pé" é a linha de base das letras.

| Parâmetro | Valor |
|---|---|
| Palavras por vez | 2 a 4, sempre numa linha só (até 22 letras) |
| Onde quebra | nas pausas da fala; a legenda nunca termina em "de", "da", "do", "o", "a", "pra", "com", "e", "que": essa palavra vai para a próxima |
| Letra | como se escreve: maiúscula só no começo de frase e em nome próprio |
| Tamanho | 62 px; régua: a frase de 4 palavras ocupa no máximo 2/3 da largura |
| Cor | branco `#FFFFFF`, sem palavra destacada |
| Contorno · fundo | nenhum contorno, nenhuma caixa ou pílula atrás do texto |
| Sombra | preta a 45%, desfoque leve; em cena muito clara, 60% |
| Posição | centralizada; pé em y 1400; nada abaixo de 1440 (nome, legenda do post e botões); 160 px livres de cada lado |
| Tempo | entra quando a primeira palavra é dita; fica no mínimo 0,5 s |
| Pontuação · números | sem ponto final; "?" e "!" ficam; números em algarismo ("3 ovos", "180 graus") |
| Animação | nenhuma: aparece e some com a fala |

Bloco `estilo` do `insercoes.json` (a `/inserir` grava a legenda no vídeo e gera a `legenda-curta.srt` com o
mesmo tempo):

```json
"estilo": {
  "fonte": "marca/fontes/Inter-Medium.ttf",
  "tamanho": 62, "palavras_max": 4, "letras_max": 22,
  "legenda_y": 1400, "margem": 160, "sombra": 0.45,
  "zona_segura": [260, 1440]
}
```

## No editor

Só para quem termina o vídeo no CapCut ou no Premiere, com a `legenda-curta.srt` e o vídeo sem legenda
(passos em `editores.md` da `/minha-edicao`):

- **CapCut no computador**: importe a `legenda-curta.srt`, selecione as legendas e, no painel da direita:
  fonte, branco, contorno e fundo desligados, sombra 45%. Aumente o tamanho até a frase mais longa ocupar 2/3
  da largura e arraste até o pé ficar logo acima da última quarta parte da tela.
- **CapCut no celular**: legenda automática do CapCut e os mesmos ajustes, na ordem da tabela. Legenda com mais
  de 4 palavras: divida em duas.
- **Premiere**: importe a `.srt`, arraste para a linha do tempo e ajuste em Gráficos essenciais (ou
  Propriedades): tamanho 62, branco, sombra 45%, sem contorno e sem fundo, pé em 1400. Salve como estilo de
  faixa.

## Conferir

- [ ] Nenhuma legenda com mais de 4 palavras ou em duas linhas
- [ ] Nenhuma legenda terminando em "de", "o", "pra", "com"...
- [ ] Nada escrito abaixo de 1440 px nem encostado na lateral direita
- [ ] Nenhum contorno, caixa ou texto todo em maiúsculas
- [ ] Legível na cena mais clara do vídeo

## Melhorar esta receita

Ao entregar cada vídeo, pergunte: "O que você corrigiu na mão?". Cada correção, e cada item que a
/criticar reprovou duas vezes seguidas, vira regra aqui: troque a regra antiga pela nova (uma regra
por assunto, nunca duas versões), acrescente uma linha no Histórico com a data e o que mudou, e
mostre à pessoa a linha alterada.

## Histórico

- 2026-10-16: criada com /minha-edicao como exemplo da aula; valores de partida, sem referência medida.
- 2026-10-18: passa a ser um `marca/estilo.md`; a legenda sai gravada pela /inserir, e a `.srt` fica para quem termina no editor.
