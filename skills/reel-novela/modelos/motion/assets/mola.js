// mola.js: a mola (duração perceptual + bounce) como ease do GSAP, para composição HyperFrames.
// Fonte única da mola da /reel-novela (montar_projeto.py a copia para cada projeto). Sem import nem rede: <script src="assets/mola.js"></script> antes do script da
// cena, ou cole o bloco (function…)(…) no <script> da composição. Determinística: segura para seek quadro a quadro.
//
//   const m = mola({ duracao: 0.5, bounce: 0.15 });      // ou MOLA("pousar"), ou MOLA("pousar", { duracao: 0.4 })
//   tl.to(el, { y: 0, duration: m.d, ease: m }, t);      // m é o ease; m.d é a duração da tween (total × duracao)
//   tl.to(el, { y: 0, duration: m.d, ease: m.ease }, t); // a forma {ease, d} também serve
//
// Parâmetros: duracao (s, perceptual; padrão 0,5) · bounce (−1 < b ≤ 1; padrão 0) · v0 (velocidade inicial em
// distâncias-alvo por segundo; padrão 0) · total (múltiplo de duracao em que a tween fecha; padrão 1,5).
// A forma posicional mola(duracao, bounce, v0, total) dá a mesma curva
// do objeto de opções (o teste --compara mede).
// Velocidade herdada numa emenda: v0 = molaVel(m1, p) × d1 / d2, ou v0Herdado(m1, p, d1, d2)
// (p = ponto de m1 em que a nova tween começa; d1, d2 = distâncias das duas tweens, com sinal, na mesma unidade).
// Redirecionar o mesmo alvo e propriedade no meio da mola: trecho(m1, p) encurta a 1ª tween até o corte (uma
// propriedade, um tween por vez), e a 2ª parte do ponto do corte com o v0 herdado.
//
// Teste:    node assets/mola.js   (de dentro do projeto motion)
// Comparar: node assets/mola.js --compara <outro mola.js>
(function (g) {
  // oscilador amortecido de massa 1 que sai de −1 (um alvo antes) com velocidade v0; f(t) → 1 (leitura nossa)
  function curva(duracao, bounce, v0) {
    var w = 2 * Math.PI / duracao, z = bounce >= 0 ? 1 - bounce : 1 / (1 + bounce), x0 = -1;
    if (Math.abs(z - 1) < 1e-6) { var B = v0 + w * x0; return function (t) { return 1 + (x0 + B * t) * Math.exp(-w * t); }; }
    if (z < 1) {
      var wd = w * Math.sqrt(1 - z * z), B2 = (v0 + z * w * x0) / wd;
      return function (t) { return 1 + Math.exp(-z * w * t) * (x0 * Math.cos(wd * t) + B2 * Math.sin(wd * t)); };
    }
    var s = Math.sqrt(z * z - 1), l1 = w * (z - s), l2 = w * (z + s), c2 = (v0 + l1 * x0) / (l1 - l2), c1 = x0 - c2;
    return function (t) { return 1 + c1 * Math.exp(-l1 * t) + c2 * Math.exp(-l2 * t); };
  }

  function mola(o, bounce, v0, total) {
    var p = o !== null && typeof o === "object" ? o : { duracao: o, bounce: bounce, v0: v0, total: total };
    var d = p.duracao || p.duration || 0.5, b = p.bounce || 0, v = p.v0 || 0, tot = p.total || 1.5;
    if (!(b > -1 && b <= 1)) throw new Error("mola: bounce fora de −1 < b ≤ 1 (" + b + ")");
    var f = curva(d, b, v), T = tot * d, fim = f(T);
    // fecha exatamente em 1, sem salto no último quadro: o resíduo f(T) − 1 se distribui linear no tempo
    var ease = function (q) { if (q <= 0) return 0; if (q >= 1) return 1; return f(q * T) + (1 - fim) * q; };
    ease.ease = ease; ease.d = T; ease.duracao = d; ease.bounce = b; ease.v0 = v; ease.total = tot;
    return ease;
  }

  // presets por papel (valores medidos e aprovados em peças anteriores)
  var MOLAS = {
    assentar: { duracao: 0.55, bounce: 0 },    // bloco, cartão, linha, rótulo que assenta
    pousar:   { duracao: 0.5,  bounce: 0.15 }, // chegada ágil (no lugar de expo.out / power3.out de entrada)
    impulso:  { duracao: 0.5,  bounce: 0.3 },  // só o que chega com momento: selo que cai, golpe
    estado:   { duracao: 0.6,  bounce: 0 },    // troca de estado e de protagonista
    luz:      { duracao: 0.8,  bounce: 0 },    // luz, desfoque, brilho, aura
    camera:   { duracao: 0.9,  bounce: 0 }     // aproximar, afastar, viajar
  };

  function MOLA(nome, opts) {
    var base = MOLAS[nome];
    if (!base) throw new Error("MOLA: papel desconhecido «" + nome + "» (há: " + Object.keys(MOLAS).join(", ") + ")");
    opts = opts || {};
    return mola({
      duracao: opts.duracao || opts.duration || base.duracao,
      bounce: opts.bounce != null ? opts.bounce : base.bounce,
      v0: opts.v0 || 0, total: opts.total
    });
  }

  // velocidade de uma ease no ponto p, em distâncias-alvo por segundo (diferença de um lado só nas bordas)
  function molaVel(m, p) {
    var h = 1e-4, a = Math.max(0, p - h), b = Math.min(1, p + h);
    if (b >= 1) { a = 1 - 2 * h; b = 1 - 1e-9; } else if (a <= 0) { a = 1e-9; b = 2 * h; }
    return (m.ease(b) - m.ease(a)) / (b - a) / m.d;
  }

  // v0 da tween nova quando o mesmo objeto segue andando: converte a velocidade para a distância nova
  // (d1, d2 com sinal: fim − início de cada tween)
  function v0Herdado(m1, p, d1, d2) { return molaVel(m1, p) * d1 / d2; }

  // redirecionar sem dois tweens na mesma propriedade: o 1º trecho de m até p, como ease próprio que fecha em 1.
  // A tween 1 vai de x0 a x0 + d1 · m(p) em t.d = p · m.d; a tween 2 parte dali com v0Herdado(m, p, d1, d2).
  function trecho(m, p) {
    if (p >= 1) return m;
    var fp = m.ease(p);
    if (!(p > 0) || fp === 0) throw new Error("trecho: p precisa ser > 0 e m(p) ≠ 0 (p = " + p + ")");
    var e = function (q) { if (q <= 0) return 0; if (q >= 1) return 1; return m.ease(q * p) / fp; };
    e.ease = e; e.d = p * m.d; e.fim = fp;   // fim: fração de d1 percorrida até o corte
    return e;
  }

  g.mola = mola; g.MOLA = MOLA; g.MOLAS = MOLAS; g.molaVel = molaVel; g.v0Herdado = v0Herdado; g.trecho = trecho;
  if (typeof module !== "undefined" && module.exports) module.exports = { mola: mola, MOLA: MOLA, MOLAS: MOLAS, molaVel: molaVel, v0Herdado: v0Herdado, trecho: trecho };

  // ---------------------------------------------------------------- teste (só roda com `node mola.js`)
  if (typeof require === "undefined" || typeof module === "undefined" || require.main !== module) return;
  var ok = 0, falhas = 0;
  function confere(cond, msg) { if (cond) { ok++; } else { falhas++; console.log("FALHOU: " + msg); } }
  function pico(m) { var mx = -Infinity; for (var i = 0; i <= 4000; i++) mx = Math.max(mx, m(i / 4000)); return mx; }
  var arg = process.argv.indexOf("--compara");
  if (arg > 0) {
    var vm = require("vm"), fs = require("fs"), arq = process.argv[arg + 1];
    var ctx = { window: {}, Math: Math }; vm.createContext(ctx); vm.runInContext(fs.readFileSync(arq, "utf8"), ctx);
    var deles = ctx.mola || ctx.window.mola;
    if (!deles) { console.log("nenhuma mola() em " + arq); process.exit(1); }
    var maxd = 0, maxT = 0, n = 0;
    [0.3, 0.5, 0.85, 1.3].forEach(function (d) { [-0.3, 0, 0.08, 0.15, 0.3].forEach(function (b) {
      [0, 1.5, 2.5].forEach(function (v) { [1.25, 1.3, 1.5, 1.6].forEach(function (tt) {
        var a = mola(d, b, v, tt), o = deles(d, b, v, tt); n++;
        maxT = Math.max(maxT, Math.abs(a.d - o.d));
        for (var i = 0; i <= 500; i++) maxd = Math.max(maxd, Math.abs(a(i / 500) - o.ease(i / 500)));
      }); }); }); });
    console.log("comparado com " + arq + ": " + n + " combinações × 501 pontos; maior diferença na curva " +
      maxd.toExponential(2) + ", na duração " + maxT.toExponential(2) + " s");
    var DM = ctx.MOLA || ctx.window.MOLA;
    if (DM) Object.keys(MOLAS).forEach(function (k) {
      var a = MOLA(k), o = DM(k), dd = Math.abs(a.d - o.d);
      for (var i = 0; i <= 500; i++) dd = Math.max(dd, Math.abs(a(i / 500) - o.ease(i / 500)));
      console.log("  preset " + k + ": diferença máxima " + dd.toExponential(2));
    });
    process.exit(maxd < 1e-12 && maxT < 1e-12 ? 0 : 1);
  }
  // 1. fecha em 1, sem salto no último quadro, e parte de 0
  [-0.3, 0, 0.15, 0.3, 0.5].forEach(function (b) { [1.1, 1.3, 1.5].forEach(function (tt) { [0, 2.5].forEach(function (v) {
    var m = mola({ duracao: 0.6, bounce: b, v0: v, total: tt });
    confere(m(0) === 0 && m(1) === 1, "extremos b=" + b + " total=" + tt);
    confere(Math.abs(m(1 - 1e-7) - 1) < 1e-5, "salto no fim b=" + b + " total=" + tt + " v0=" + v);
  }); }); });
  // 2. bounce 0 não passa de 1 partindo do repouso; com v0 acima de 2π/duracao passa (leitura nossa)
  [0.3, 0.5, 0.9, 1.3].forEach(function (d) { confere(pico(mola({ duracao: d })) <= 1 + 1e-12, "bounce 0 passou de 1, d=" + d); });
  confere(pico(mola({ duracao: 0.5, v0: 2.5 })) <= 1 + 1e-12, "bounce 0 com v0 2,5 passou de 1");
  confere(pico(mola({ duracao: 0.5, v0: 16 })) > 1, "bounce 0 com v0 16 (> 2π/0,5) devia passar de 1");
  // 3. bounce 0,3 passa do alvo (~4,6 %); 0,15 passa pouco (~0,6 %)
  var p3 = pico(mola({ duracao: 0.5, bounce: 0.3 })), p15 = pico(mola({ duracao: 0.5, bounce: 0.15 }));
  confere(p3 > 1.04 && p3 < 1.05, "bounce 0,3 devia passar ~4,6 %: " + p3);
  confere(p15 > 1.004 && p15 < 1.008, "bounce 0,15 devia passar ~0,6 %: " + p15);
  // 4. v0 muda a inclinação inicial: a velocidade em p = 0 é v0 (± 0,02: diferença finita de um lado e resíduo)
  var v0a = molaVel(mola({ duracao: 0.6 }), 0), v0b = molaVel(mola({ duracao: 0.6, v0: 3 }), 0);
  confere(Math.abs(v0a) < 0.02, "v0 0 devia partir parado: " + v0a);
  confere(Math.abs(v0b - 3) < 0.02, "v0 3 devia partir a 3 alvos/s: " + v0b);
  confere(mola({ duracao: 0.6, v0: 3 })(0.05) > mola({ duracao: 0.6 })(0.05), "v0 3 devia andar mais no começo");
  // 5. presets e forma posicional = forma em objeto
  confere(MOLA("pousar")(0.3) === mola(0.5, 0.15, 0, 1.5)(0.3), "MOLA(pousar) ≠ mola(0.5, 0.15, 0, 1.5)");
  confere(MOLA("camera", { v0: 2.5 }).v0 === 2.5, "MOLA com opts não aplicou v0");
  confere(Math.abs(v0Herdado(mola({ duracao: 0.5 }), 0.3, 400, 200) - 2 * molaVel(mola({ duracao: 0.5 }), 0.3)) < 1e-12, "v0Herdado");
  // 6. redirecionar com trecho(): posição e velocidade (px/s) iguais dos dois lados do corte
  var m1 = MOLA("camera"), pc = 0.3, d1 = 400, tr = trecho(m1, pc), xc = d1 * tr.fim, d2 = 650 - xc;
  var m2 = mola({ duracao: 0.6, v0: v0Herdado(m1, pc, d1, d2) });
  var vAntes = xc * molaVel(tr, 1), vDepois = d2 * molaVel(m2, 0), vReal = d1 * molaVel(m1, pc);
  confere(Math.abs(xc - d1 * m1(pc)) < 1e-9 && tr(1) === 1, "trecho não para no ponto do corte");
  confere(Math.abs(vAntes - vReal) / vReal < 0.01 && Math.abs(vDepois - vReal) / vReal < 0.01,
    "velocidade no corte: antes " + vAntes.toFixed(1) + ", depois " + vDepois.toFixed(1) + ", mola " + vReal.toFixed(1) + " px/s");
  console.log(ok + " conferências ok, " + falhas + " falhas");
  // tabela de comportamento (duracao = 1; escale por duracao): sobressalto, 1º cruzamento do alvo, ±5 % e ±1 %
  console.log("bounce  sobressalto  cruza o alvo  ±5 % em  ±1 % em  pico de vel. (alvos/s)");
  [-0.3, 0, 0.15, 0.3, 0.4, 0.5].forEach(function (b) {
    var f = mola({ duracao: 1, bounce: b, total: 6 }), T = 6, N = 60000, cruza = null, e5 = 0, e1 = 0, mx = 0, vmax = 0, tv = 0;
    for (var i = 0; i <= N; i++) {
      var t = i / N * T, x = f(t / T); mx = Math.max(mx, x);
      if (cruza === null && x >= 1) cruza = t;
      if (Math.abs(1 - x) > 0.05) e5 = t; if (Math.abs(1 - x) > 0.01) e1 = t;
      if (i > 0) { var vv = (x - f((i - 1) / N)) / (T / N); if (vv > vmax) { vmax = vv; tv = t; } }
    }
    console.log(String(b).padStart(6) + "  " + (Math.max(0, (mx - 1) * 100).toFixed(1) + " %").padStart(11) +
      "  " + (cruza === null || cruza > 5.9 ? "—" : cruza.toFixed(2) + " d").padStart(12) +
      "  " + (e5.toFixed(2) + " d").padStart(7) + "  " + (e1.toFixed(2) + " d").padStart(7) +
      "  " + vmax.toFixed(2) + " em " + tv.toFixed(2) + " d");
  });
  process.exit(falhas ? 1 : 0);
})(typeof globalThis !== "undefined" ? globalThis : typeof window !== "undefined" ? window : this);
