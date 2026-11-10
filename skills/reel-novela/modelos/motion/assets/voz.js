// Régua de tempo da voz: VOZ.w(t) leva um tempo do código (o escrito nas cenas) para o tempo real da narração do vídeo.
//
// As cenas escrevem os tempos do briefings/palavras-voz.json da narração em que foram escritas (o início de cada
// palavra, do alinhamento forçado). Enquanto essa narração for a do vídeo, A fica vazia e VOZ.w é a identidade.
// Se a narração mudar depois das cenas prontas, o ancorar.py desta skill (chamado pelo segunda_voz.py) reescreve A
// com um par por palavra, [tempo do código, tempo real da narração nova], e VOZ.w interpola entre eles. As cenas não
// mudam; mudam as janelas do index.html (montar_projeto.py/segunda_voz.py) e a legenda se gera de novo.
//
// Quem usa: o a() de cada cena, a barra, o assets/roleta.js (pelo a()) e os briefings/*.cjs (som e snapshot). A legenda
// não usa: ela vive no tempo real.
(function (raiz) {
  // [tempo do código, tempo real da voz], em ordem; vazia = identidade
  const A = [];
  // o vídeo começa em 0 nas duas réguas
  const P = A.length && A[0][0] > 0 ? [[0, 0]].concat(A) : A;
  function w(t) {
    if (P.length < 2 || t <= P[0][0]) return t;
    const n = P.length - 1;
    if (t >= P[n][0]) return t - P[n][0] + P[n][1];
    let i = 0, j = n;
    while (j - i > 1) { const m = (i + j) >> 1; if (P[m][0] <= t) i = m; else j = m; }
    return P[i][1] + ((t - P[i][0]) * (P[j][1] - P[i][1])) / (P[j][0] - P[i][0]);
  }
  raiz.VOZ = { w, ancoras: A };
})(typeof window !== "undefined" ? window : globalThis);
