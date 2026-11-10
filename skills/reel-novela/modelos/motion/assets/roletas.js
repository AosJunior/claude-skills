// Registro dos números que giram na roleta (motor em assets/roleta.js; guia em referencias/roleta.md da skill).
// Tempos no tempo do código (briefings/palavras-voz.json), como no resto das cenas: a cena converte com o a().
//   valor   número final, com a pontuação (o formato vem daqui)
//   inicio  começo do giro
//   pousos  instante de trava de cada dígito, na ordem de trava. {de, ate}: a primeira e a última trava ficam presas
//           às palavras e as do meio se espaçam por igual no tempo real (use em cascata). Lista: um instante por
//           dígito, cada um preso à sua palavra.
//   ordem   "esq-dir", "dir-esq" ou lista de índices dos dígitos (0 = o da esquerda)
//   cor     cor do número na trava, em hex: o dígito trava nela (halo e pulso) e depois herda a cor do elemento
//   semente número fixo do sorteio; números lado a lado levam sementes diferentes
// Opcionais (padrão em ROLETA.PADRAO): arranque (s até ganhar velocidade a partir do repouso; só para número que já
// estava parado na tela), acender (s de neon acendendo no começo), solto, freio, vMax, vFim, emOrdem, deslize,
// piscaTroca, piscaPlacar, pulso.
//
// Arquivo compartilhado: cada cena escreve só no bloco dela, com Edit (nunca reescrevendo o arquivo inteiro), e com o
// nome prefixado pela cena. O briefings/roleta-ticks.cjs exporta o som de tudo o que está aqui: registre só o que a
// cena anima.
window.ROLETAS = window.ROLETAS || {};

// ---------- barra (br-) · GERADO pelo montar_projeto.py a partir dos eventos `relogio_muda` da lista `barra` do roteiro ----------
// Gêmeos, só para o som: o relógio vira pelo NOVELA.barra().contar() numa timeline solta que o roleta-ticks.cjs não vê.
// Mesma configuração e mesma semente do contar() da barra.html: os tiques saem iguais. Tempos no tempo do código.
// <novela:barra>
// </novela:barra>

// ---------- ato1 (a1-) ----------
// Etiquetas com número são texto fixo (régua da novela): só registre aqui o que a cena girar com ROLETA.animar.

// ---------- ato2 (a2-) ----------

// ---------- ato3 (a3-) ----------

// ---------- ato4 (a4-) ----------

// ---------- ato5 (a5-) ----------

// ---------- ato6 (a6-) ----------

