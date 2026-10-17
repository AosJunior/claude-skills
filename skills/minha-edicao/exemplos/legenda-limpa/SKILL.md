---
name: legenda-limpa
description: Legenda limpa e delicada para Reels: letra normal (sem tudo maiúsculo), 2 a 4 palavras por vez, sem contorno grosso nem fundo, no terço de baixo acima dos botões do Instagram. Use ao legendar qualquer vídeo da pessoa, inclusive dentro de uma receita de formato.
---

# Legenda limpa

Legenda que se lê sem gritar: frase curta, letra fina, nada em volta do texto.

## Parâmetros

Medidas no quadro do Reel, 1080 × 1920 px.

| Parâmetro | Valor |
|---|---|
| Fonte | Inter Medium; sem ela, Montserrat Medium ou Poppins Medium. Peso médio, nunca Black ou Extra Bold |
| Tamanho | 62 px; régua: a frase de 4 palavras ocupa no máximo 2/3 da largura |
| Letra | como se escreve normalmente: maiúscula só no começo de frase e em nome próprio |
| Cor | branco `#FFFFFF`, sem palavra destacada |
| Contorno · fundo | nenhum contorno, nenhuma caixa ou pílula atrás do texto |
| Sombra | preta a 45%, deslocada 2 px, desfoque leve; em cena muito clara, preta a 60% |
| Palavras por vez | 2 a 4, sempre numa linha só (até 22 letras) |
| Onde quebra | nas pausas da fala; a legenda nunca termina em "de", "da", "do", "o", "a", "pra", "com", "e", "que": essa palavra vai para a próxima |
| Posição | centralizada; a base do texto em y = 1400 px (logo acima da última quarta parte da tela); nada abaixo de 1440 px, onde ficam o nome, a legenda do post e os botões; 160 px livres de cada lado |
| Tempo | entra quando a primeira palavra é dita; fica no mínimo 0,5 s; intervalo menor que 0,3 s entre duas legendas é emendado |
| Pontuação · números | sem ponto final; "?" e "!" ficam; números em algarismo ("3 ovos", "180 graus") |
| Animação | nenhuma: aparece e some com a fala |

## Como aplicar

**O Claude**: monta o `.srt` (UTF-8) nessas regras a partir da legenda da `/decupar`. Se ela der o tempo de cada palavra, use; senão, divida o tempo de cada legenda pelo número de letras de cada pedaço. Entregue o `.srt` junto do vídeo cortado.

**No CapCut do computador**: importe o `.srt` (aba Texto ou Legendas, "legendas locais" ou "importar legendas"). Selecione as legendas e, no painel da direita: fonte, cor branca, contorno desligado, fundo desligado, sombra com opacidade 45%. Tamanho: aumente até a frase mais longa ocupar 2/3 da largura. Arraste para cima até a base do texto ficar logo acima da última quarta parte da tela.

**No CapCut do celular**: legenda automática do CapCut e os mesmos ajustes, na ordem da tabela. Legenda com mais de 4 palavras: divida em duas.

**No Premiere**: Arquivo › Importar o `.srt` e arraste para a linha do tempo. No painel Gráficos essenciais (ou Propriedades): fonte, tamanho 62, branco, sombra 45%, sem contorno e sem fundo, posição com a base em 1400 px. Salve como estilo de faixa para usar nos próximos vídeos.

## Conferir

- [ ] Nenhuma legenda com mais de 4 palavras ou em duas linhas
- [ ] Nenhuma legenda terminando em "de", "o", "pra", "com"...
- [ ] Nada escrito abaixo de 1440 px nem encostado na lateral direita
- [ ] Nenhum contorno, caixa ou texto todo em maiúsculas
- [ ] Legível na cena mais clara do vídeo

## Melhorar esta receita

Ao entregar cada vídeo, pergunte: "O que você corrigiu na mão?". Cada correção vira regra
aqui: troque a regra antiga pela nova (uma regra por assunto, nunca duas versões), acrescente
uma linha no Histórico com a data e o que mudou, e mostre à pessoa a linha alterada.

## Histórico

- 2026-10-16: criada com /minha-edicao como exemplo da aula; valores de partida, sem referência medida.
