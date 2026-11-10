// Roleta de dígitos com flicker (rolo de caça-níquel) para todo número do vídeo. Guia: referencias/roleta.md da
// skill /reel-novela. Peça compartilhada por todas as cenas: não edite; os números ficam em assets/roletas.js.
//
// Cada dígito é um rolo que troca de dígito em passos discretos. No começo as trocas são muito rápidas, com flicker de
// brilho e opacidade a cada troca e um deslize curto em y. O rolo perde força como roleta: os intervalos crescem até a
// trava, que cai exatamente no pouso do dígito. A trava é um estalo (assentamento curto em y + flash de luz), nunca
// escala. Enquanto gira, o número inteiro pisca como placar ou neon acendendo; ele estabiliza quando o último dígito
// trava, com um pulso de luz.
//
// Determinismo: nada de Math.random. A agenda das trocas sai de uma física simples, calculada uma vez a partir da
// configuração. Um único tween "motor" por giro chama desenhar(t) no onUpdate, e desenhar é função pura do tempo: o
// quadro sai igual em qualquer ordem de seek. Só escrevemos transform, opacity, filter e o texto do dígito.
//
// Tempo: os instantes da configuração (início, pousos) estão no tempo do código (briefings/palavras-voz.json) e
// passam pelo conversor da cena, o a() (VOZ.w − T0). A física do giro corre em segundos reais entre esses instantes,
// então a narração não deforma a desaceleração. ROLETA.tiques(cfg, w) usa a mesma conta: sem w, tempo do código; com
// VOZ.w, tempo real, idêntico ao que a tela mostra.
(function (raiz) {
  "use strict";

  const PADRAO = {
    vMax: 22, // trocas por segundo com o rolo cheio (a 30 fps, uma troca a cada 1,4 quadro)
    vFim: 6.5, // trocas por segundo no instante da trava (o último intervalo fica perto de 0,13 s)
    freio: 1.0, // s de desaceleração antes de cada trava (encolhe sozinho quando o giro é mais curto)
    arranque: 0, // s para ganhar velocidade a partir do repouso; 0 = o número já nasce girando
    emOrdem: 5, // as últimas trocas seguem a ordem do rolo até o alvo (… 7, 8, 9, 0 → trava no 1)
    acender: 0, // s de neon acendendo no começo do giro; 0 = sem
    deslize: 0.2, // deslize de cada troca, em em (fração do corpo do número)
    solto: 0.76, // opacidade do dígito solto com o rolo lento (cai 0,12 no giro cheio); travado = 1
    piscaTroca: 1, // força do flicker de cada troca (0 desliga)
    piscaPlacar: 1, // força do flicker do número inteiro durante o giro (0 desliga)
    pulso: true, // pulso de luz no número inteiro quando o último dígito trava
  };
  const FPS = 30; // o flicker do placar sorteia um valor por quadro
  const ASSENTA = 0.45; // s até o dígito travado ficar limpo (estalo + flash)
  const PULSO = 0.75; // s do pulso da última trava
  const LUZ = 0.085; // s da queda do flash da trava (e meio período do estalo em y)
  const AMORTECE = 21.6; // amortecimento do estalo: passa do lugar uns 16% do deslize e volta
  const MASCARA = "linear-gradient(to bottom, transparent 0, #000 9%, #000 91%, transparent 100%)";

  // ---------- sorteio determinístico ----------
  function mulberry32(a) {
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  // sorteio sem estado: o mesmo (semente, n) dá sempre o mesmo número em [0, 1), em qualquer ordem
  function sorteio(semente, n) {
    let x = (semente ^ Math.imul(n + 1, 0x9e3779b1)) >>> 0;
    x = Math.imul(x ^ (x >>> 16), 0x85ebca6b);
    x = Math.imul(x ^ (x >>> 13), 0xc2b2ae35);
    return ((x ^ (x >>> 16)) >>> 0) / 4294967296;
  }
  function sementeDe(cfg) {
    if (Number.isFinite(cfg.semente)) return cfg.semente >>> 0;
    const s = String(cfg.valor) + "|" + cfg.inicio;
    let h = 0x811c9dc5;
    for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 0x01000193);
    return h >>> 0;
  }

  // ---------- configuração ----------
  const ehDigito = (c) => c >= "0" && c <= "9";
  const digitosDe = (valor) => [...String(valor)].filter(ehDigito).map(Number);
  const mascaraDe = (valor) => String(valor).replace(/[0-9]/g, "#");

  function ordemDe(ordem, n) {
    if (Array.isArray(ordem)) {
      const ok = ordem.length === n && [...ordem].sort((x, y) => x - y).every((v, i) => v === i);
      if (!ok) throw new Error("ROLETA: ordem tem de listar cada dígito uma vez (0 = o da esquerda)");
      return ordem.slice();
    }
    const esq = [...Array(n).keys()];
    if (ordem === "dir-esq") return esq.reverse();
    if (ordem == null || ordem === "esq-dir") return esq;
    throw new Error(`ROLETA: ordem «${ordem}» desconhecida (use "esq-dir", "dir-esq" ou uma lista de índices)`);
  }
  // Instantes de trava já convertidos, na ordem de trava. Lista: cada pouso passa pelo conversor (fica preso à sua
  // palavra). {de, ate}: só as pontas passam pelo conversor e as travas se espaçam por igual no tempo de destino, para
  // a cascata manter o ritmo mesmo quando a narração estica ou encolhe as palavras do meio.
  function pousosDe(pousos, n, conv) {
    if (Array.isArray(pousos)) {
      if (pousos.length !== n) throw new Error(`ROLETA: são ${n} dígitos e ${pousos.length} pousos`);
      return pousos.map(conv);
    }
    if (pousos && Number.isFinite(pousos.de)) {
      const de = conv(pousos.de), ate = conv(Number.isFinite(pousos.ate) ? pousos.ate : pousos.de);
      return [...Array(n)].map((_, i) => (n === 1 ? ate : de + ((ate - de) * i) / (n - 1)));
    }
    throw new Error("ROLETA: pousos é uma lista (um por dígito, na ordem de trava) ou {de, ate}");
  }

  // ---------- agenda: instantes das trocas de cada dígito ----------
  // Roleta perdendo força: a velocidade (trocas/s) cai em linha reta de vMax a vFim no freio que antecede a trava, e
  // a trava acontece exatamente no pouso. A conta anda para trás a partir da trava: cada troca é um inteiro da
  // distância que ainda falta rodar. Com arranque, a velocidade sai do zero no início do giro.
  function trocas(t0, tTrava, p) {
    const giro = tTrava - t0;
    if (!(giro > 1e-6)) return [tTrava];
    const freio = Math.min(p.freio, Math.max(0.15, giro - p.arranque));
    const acel = (p.vMax - p.vFim) / freio;
    const vel = (falta) => {
      let v = Math.min(p.vMax, p.vFim + acel * falta);
      const desde = giro - falta;
      if (p.arranque > 0 && desde < p.arranque) {
        const g = desde / p.arranque;
        v *= 1 - (1 - g) * (1 - g);
      }
      return v;
    };
    const dt = 0.0005;
    const faltas = [];
    let falta = 0, dist = 0, v0 = vel(0), k = 1;
    while (falta < giro) {
      const falta1 = Math.min(giro, falta + dt), v1 = vel(falta1);
      const dist1 = dist + (v0 + v1) * 0.5 * (falta1 - falta);
      while (dist1 >= k) {
        faltas.push(falta + ((falta1 - falta) * (k - dist)) / (dist1 - dist));
        k++;
      }
      falta = falta1;
      dist = dist1;
      v0 = v1;
    }
    const ts = faltas.reverse().map((x) => tTrava - x);
    ts.push(tTrava);
    return ts;
  }

  // w: conversor de tempo dos instantes da configuração (tempo do código → destino). Sem w, fica no tempo do código.
  function agenda(cfg, w) {
    const conv = typeof w === "function" ? w : (t) => t;
    const p = Object.assign({}, PADRAO, cfg);
    const alvos = digitosDe(cfg.valor), n = alvos.length;
    if (!n) throw new Error(`ROLETA: «${cfg.valor}» não tem dígitos`);
    const ordem = ordemDe(cfg.ordem, n), pousos = pousosDe(cfg.pousos, n, conv);
    const t0 = conv(cfg.inicio);
    const travaDe = new Array(n);
    ordem.forEach((d, i) => (travaDe[d] = pousos[i]));
    const digitos = alvos.map((alvo, i) => ({ i, alvo, trava: travaDe[i], T: trocas(t0, travaDe[i], p) }));
    let ultima = -Infinity, ultimoDigito = ordem[0];
    for (const d of ordem) if (travaDe[d] >= ultima) { ultima = travaDe[d]; ultimoDigito = d; }
    return { p, n, t0, ordem, digitos, ultima, ultimoDigito, semente: sementeDe(cfg), cor: cfg.cor };
  }

  // ---------- tiques para o som ----------
  // Um "tique" por troca que não trava, uma "trava" por dígito e, no mesmo instante da última trava, a "ultima".
  // digito = posição do dígito no número (0 = o da esquerda), sem contar pontos e vírgulas.
  function tiques(cfg, w) {
    const g = agenda(cfg, w);
    const ms = (x) => Math.round(x * 1000) / 1000;
    const ev = [];
    for (const d of g.digitos) {
      for (let s = 0; s < d.T.length - 1; s++) ev.push({ t: ms(d.T[s]), tipo: "tique", digito: d.i });
      ev.push({ t: ms(d.trava), tipo: "trava", digito: d.i });
    }
    ev.push({ t: ms(g.ultima), tipo: "ultima", digito: g.ultimoDigito });
    const peso = { tique: 0, trava: 1, ultima: 2 };
    ev.sort((x, y) => x.t - y.t || peso[x.tipo] - peso[y.tipo] || x.digito - y.digito);
    return ev;
  }

  // ---------- o que cada rolo mostra ----------
  // A última troca é o alvo; as emOrdem finais seguem a ordem do rolo; antes disso, saltos sorteados (o rolo cheio
  // anda mais de uma casa por troca). A primeira troca sempre muda o dígito que estava na tela.
  function sequencia(d, p, semente, de) {
    const M = d.T.length, D = new Array(M);
    const rnd = mulberry32((semente + Math.imul(d.i + 1, 0x2545f491)) | 0);
    D[M - 1] = d.alvo;
    const L = Math.min(p.emOrdem, M);
    for (let s = M - 2; s >= M - L; s--) D[s] = (D[s + 1] + 9) % 10;
    for (let s = M - L - 1; s >= 0; s--) {
      let x = Math.floor(rnd() * 9);
      if (x >= D[s + 1]) x++;
      D[s] = x;
    }
    if (de != null && M > 1 && D[0] === de) {
      for (let j = 1; j < 10; j++) if ((de + j) % 10 !== D[1]) { D[0] = (de + j) % 10; break; }
    }
    // índice -1: a troca virtual de antes do início, para o número que já nasce girando
    return { D, flash: D.map(() => rnd()), apagao: D.map(() => rnd()), flash0: rnd(), apagao0: rnd() };
  }

  // ---------- montagem (DOM gerado uma vez) ----------
  function criar(cls, estilos, txt) {
    const e = document.createElement("span");
    e.className = cls;
    for (const k in estilos) e.style.setProperty(k, estilos[k]);
    if (txt != null) e.textContent = txt;
    return e;
  }
  // Monta as casas no elemento (formato de cfg.valor). O elemento define fonte, tamanho e cor do número.
  function montar(el, cfg) {
    if (el.__roleta) return el.__roleta;
    const num = criar("rl-num", {
      position: "relative", display: "inline-flex", "align-items": "flex-start", "white-space": "nowrap",
      "font-variant-numeric": "tabular-nums",
    });
    const cels = [], seps = [];
    for (const c of String(cfg.valor)) {
      if (!ehDigito(c)) { // o ponto acende quando os dígitos dos dois lados travam
        const sep = criar("rl-sep", { display: "inline-block" }, c);
        sep.setAttribute("data-c", c); // a cena estreita só o ponto: .rl-sep[data-c="."]
        seps.push({ el: sep, esq: cels.length - 1, dir: cels.length });
        num.appendChild(sep);
        continue;
      }
      const cel = criar("rl-cel", { position: "relative", display: "inline-block" });
      cel.setAttribute("data-layout-allow-overlap", "");
      // a janela do rolo: corta em cima e embaixo com borda suave; dos lados sobra espaço para o desenho do dígito
      const janela = criar("rl-janela", {
        position: "absolute", top: "0", bottom: "0", left: "-0.25em", right: "-0.25em",
        "-webkit-mask-image": MASCARA, "mask-image": MASCARA, "pointer-events": "none",
      });
      janela.setAttribute("data-layout-allow-overflow", "");
      // rastro de luz: cópia desfocada do dígito que entra, somada como luz, no caminho do deslize
      const rastro = criar("rl-rastro", { position: "absolute", top: "0", left: "0.25em", opacity: "0", "mix-blend-mode": "plus-lighter" });
      const dig = criar("rl-dig", { position: "absolute", top: "0", left: "0.25em" }, c);
      rastro.setAttribute("aria-hidden", "true");
      rastro.setAttribute("data-layout-ignore", ""); // cópia de luz, nunca lida: fora das auditorias do check
      janela.append(dig, rastro); // o rastro vem por cima: é luz somada ao dígito
      cel.append(criar("rl-medida", { visibility: "hidden" }, "0"), janela); // "0" dá a largura tabular da casa
      num.appendChild(cel);
      cels.push({ cel, dig, rastro });
    }
    for (const s of seps) if (s.dir >= cels.length) s.dir = -1; // pontuação no fim do número: só o vizinho da esquerda
    el.textContent = "";
    el.appendChild(num);
    el.__roleta = { el, num, cels, seps, mascara: mascaraDe(cfg.valor), giros: [] };
    return el.__roleta;
  }

  // ---------- desenho de um quadro (função pura do tempo) ----------
  const fmt = (x) => (Math.abs(x) < 5e-5 ? "0" : x.toFixed(4));
  function por(el, prop, val) {
    const c = el.__c || (el.__c = {});
    if (c[prop] !== val) { el.style.setProperty(prop, val); c[prop] = val; }
  }
  function texto(el, s) {
    if (el.__t !== s) { el.textContent = s; el.__t = s; }
  }
  function rgba(cor, a) {
    a = Math.max(0, Math.min(1, a));
    const m = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(String(cor || "").trim());
    if (!m) return `color-mix(in srgb, currentColor ${Math.round(a * 100)}%, transparent)`;
    const h = m[1].length === 3 ? m[1].replace(/./g, "$&$&") : m[1];
    const n = parseInt(h, 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a.toFixed(3)})`;
  }
  function ultimoAte(T, t) {
    if (t < T[0]) return -1;
    let lo = 0, hi = T.length - 1;
    while (lo < hi) {
      const m = (lo + hi + 1) >> 1;
      if (T[m] <= t) lo = m; else hi = m - 1;
    }
    return lo;
  }

  // flicker do número inteiro: um sorteio por quadro; a força cai com os dígitos que já travaram
  function placar(g, t, sig) {
    const p = g.p;
    if (!(p.piscaPlacar > 0)) return { op: 1, br: 1 };
    let soltos = 0;
    for (const d of g.digitos) if (d.trava > t) soltos++;
    const q = Math.floor(sig * FPS + 1e-6);
    const r1 = sorteio(g.semente, 2 * q), r2 = sorteio(g.semente, 2 * q + 1);
    const entra = p.arranque > 0 ? Math.min(1, sig / Math.max(0.08, p.arranque)) : 1;
    const forca = 0.3 * p.piscaPlacar * Math.pow(soltos / g.n, 0.8) * entra;
    let op = 1 - forca * r1, br = 1 + forca * (r2 - 0.35);
    if (p.acender > 0 && sig < p.acender) { // neon acendendo: sobe de 70% e falha antes de firmar
      const resto = 1 - sig / p.acender;
      op *= 1 - 0.3 * resto;
      if (q > 0 && r2 < 0.55 * resto) { op = 0.3 + 0.35 * r1; br = 0.85; }
    }
    return { op, br };
  }
  const pulso = (tau) => (tau < 0 || tau >= PULSO ? 0 : tau < 0.045 ? tau / 0.045 : Math.exp(-(tau - 0.045) / 0.17));

  function limpar(c) {
    por(c.dig, "transform", "none");
    por(c.dig, "opacity", "1");
    por(c.dig, "filter", "none");
    por(c.dig, "color", "");
    por(c.cel, "filter", "none");
    por(c.rastro, "opacity", "0");
    por(c.rastro, "color", "");
    texto(c.rastro, "");
  }
  // rastro de luz: o mesmo dígito, desfocado e somado como luz, um pouco acima (de onde ele veio), apagando quando o
  // deslize termina. y = posição do dígito (em); resto = quanto do deslize falta (1 → 0)
  function rastro(c, digito, y, resto, forca) {
    if (resto < 0.02 || forca <= 0) { por(c.rastro, "opacity", "0"); texto(c.rastro, ""); return; }
    texto(c.rastro, String(digito));
    por(c.rastro, "color", "");
    por(c.rastro, "transform", `translateY(${fmt(y - 0.15 * resto)}em)`);
    por(c.rastro, "opacity", fmt(Math.min(1, 0.6 * forca * resto)));
    por(c.rastro, "filter", "blur(0.035em) brightness(1.6)");
  }
  // miolo branco da trava: cópia branca somada como luz sobre o dígito, que nasce desfocada e firma enquanto apaga
  function miolo(c, digito, y, tau, fl) {
    if (fl < 0.01) { por(c.rastro, "opacity", "0"); texto(c.rastro, ""); return; }
    const tr = Math.exp(-tau / 0.05);
    texto(c.rastro, String(digito));
    por(c.rastro, "color", "#fff");
    por(c.rastro, "transform", `translateY(${fmt(y - 0.035 * tr)}em)`);
    por(c.rastro, "opacity", fmt(0.9 * fl));
    por(c.rastro, "filter", `blur(${fmt(0.008 + 0.03 * tr)}em)`);
  }

  // girando: o dígito troca seco no instante ini e entra deslizando de cima, com flash ou apagão sorteado
  // (prox = próxima troca)
  function girando(c, g, t, ini, prox, digito, flash, apagao) {
    const p = g.p, S = p.deslize;
    const I = prox - ini, dt = t - ini;
    const dur = Math.min(0.75 * I, 0.08);
    const x = Math.min(1, dt / dur), e = 1 - (1 - x) * (1 - x) * (1 - x);
    const q = Math.min(1, 1 / I / p.vMax); // velocidade relativa do rolo
    const fP = p.piscaTroca;
    const base = p.solto - 0.12 * q; // solto, o dígito fica bem abaixo do travado: só se lê de vez quando trava
    const op = base * (apagao < 0.24 * fP ? 0.35 + 0.65 * e : 1 - 0.2 * fP * (1 - e));
    const br = 1 + 0.95 * fP * flash * (1 - e) * (1 - e);
    const y = -S * (1 - e);
    texto(c.dig, String(digito));
    por(c.dig, "transform", `translateY(${fmt(y)}em)`);
    por(c.dig, "opacity", fmt(op));
    por(c.dig, "filter", `brightness(${fmt(br)}) blur(${fmt(0.005 + 0.009 * q * q)}em)`);
    por(c.dig, "color", "");
    por(c.cel, "filter", "none");
    rastro(c, digito, y, 1 - e, op * (0.55 + 0.45 * q));
  }

  function desenharDigito(c, d, g, t) {
    const p = g.p, S = p.deslize, T = d.T, M = T.length, D = d.seq.D;
    const k = ultimoAte(T, t);
    if (k < 0) { // antes da primeira troca
      if (!(p.arranque > 0) && M > 1 && t >= g.t0) { // o rolo já girava: nunca mostra o dígito parado e limpo
        girando(c, g, t, T[0] - (T[1] - T[0]), T[0], d.de, d.seq.flash0, d.seq.apagao0);
      } else { texto(c.dig, String(d.de)); limpar(c); } // em repouso: o que estava na tela
      return;
    }

    if (k === M - 1) { // travado: estalo em y + flash de luz, depois limpo
      const tau = t - T[k];
      texto(c.dig, String(D[k]));
      if (tau >= ASSENTA) { limpar(c); return; }
      const fl = Math.exp(-tau / LUZ);
      const y = -S * Math.exp(-AMORTECE * tau) * Math.cos((Math.PI * tau) / LUZ);
      por(c.dig, "transform", `translateY(${fmt(y)}em)`);
      por(c.dig, "opacity", "1");
      por(c.dig, "filter", "none");
      por(c.dig, "color", g.cor || ""); // trava já na cor do número; depois do assentamento herda a cor do elemento
      por(c.cel, "filter", fl < 0.003 ? "none"
        : `brightness(${fmt(1 + 0.35 * fl)}) drop-shadow(0 0 ${fmt(0.02 + 0.12 * fl)}em ${rgba(g.cor, 0.95 * fl)})`);
      miolo(c, D[k], y, tau, fl);
      return;
    }

    girando(c, g, t, T[k], T[k + 1], D[k], d.seq.flash[k], d.seq.apagao[k]); // troca k
  }

  // pontuação: apaga junto com o giro e acende quando o último dos dois vizinhos trava
  function desenharSep(s, g, t, sig) {
    const solto = 0.55;
    const tLuz = Math.max(s.esq >= 0 ? g.digitos[s.esq].trava : -Infinity, s.dir >= 0 ? g.digitos[s.dir].trava : -Infinity);
    let op = 1;
    if (sig >= 0 && t < tLuz) {
      const apaga = g.p.arranque > 0 ? Math.min(1, sig / Math.max(0.08, g.p.arranque)) : 1;
      op = 1 - (1 - solto) * apaga;
    } else if (sig >= 0) op = solto + (1 - solto) * Math.min(1, (t - tLuz) / 0.12);
    por(s.el, "opacity", fmt(op));
  }

  function desenhar(h, g, t) {
    const sig = t - g.t0;
    let op = 1, br = 1, P = 0;
    if (sig < 0) op = g.primeiro ? 0 : 1; // primeiro giro: o número só acende quando começa a girar
    else if (t < g.ultima) ({ op, br } = placar(g, t, sig));
    else if (g.p.pulso) P = pulso(t - g.ultima);
    por(h.num, "opacity", fmt(op));
    const luz = br * (1 + 0.15 * P);
    por(h.num, "filter", Math.abs(luz - 1) < 1e-4 && P < 0.004 ? "none"
      : `brightness(${fmt(luz)})` + (P >= 0.004 ? ` drop-shadow(0 0 ${fmt(0.04 + 0.16 * P)}em ${rgba(g.cor, 0.85 * P)})` : ""));
    g.digitos.forEach((d, i) => desenharDigito(h.cels[i], d, g, t));
    for (const s of h.seps) desenharSep(s, g, t, sig);
  }

  // ---------- animação: um tween motor por giro ----------
  // a: conversor da cena (tempo do código → tempo local da timeline). Um segundo giro no mesmo elemento parte do valor
  // do giro anterior (mesmo formato de número).
  function animar(tl, el, cfg, a) {
    if (!tl || typeof tl.to !== "function") throw new Error("ROLETA.animar: passe a timeline da cena");
    const h = el.__roleta || montar(el, cfg);
    if (mascaraDe(cfg.valor) !== h.mascara) {
      throw new Error(`ROLETA: «${cfg.valor}» tem outro formato que o número já montado; use outro elemento`);
    }
    const g = agenda(cfg, a);
    const anterior = h.giros[h.giros.length - 1];
    const de = anterior ? digitosDe(anterior.cfg.valor) : null;
    g.primeiro = !anterior;
    for (const d of g.digitos) {
      d.seq = sequencia(d, g.p, g.semente, de ? de[d.i] : null);
      d.de = de ? de[d.i] : (d.seq.D[0] + 5) % 10;
    }
    const ini = g.primeiro ? 0 : Math.max(0, g.t0); // o primeiro motor cobre também o antes do giro (número apagado)
    const fim = Math.max(g.ultima + (g.p.pulso ? PULSO : ASSENTA), ini + 0.001);
    if (anterior && anterior.fim > ini) { // dois motores nunca se sobrepõem no mesmo elemento
      anterior.tween.duration(Math.max(0.001, ini - anterior.ini));
      anterior.fim = ini;
    }
    const motor = { p: 0 };
    const tween = tl.to(motor, {
      p: 1, duration: fim - ini, ease: "none",
      onUpdate: function () { desenhar(h, g, ini + this.time()); },
    }, ini);
    if (g.primeiro) desenhar(h, g, ini);
    h.giros.push({ cfg, g, ini, fim, tween });
    return { inicio: g.t0, travas: g.digitos.map((d) => d.trava), ultima: g.ultima, fim };
  }

  raiz.ROLETA = { montar, animar, tiques, agenda, PADRAO };
})(typeof window !== "undefined" ? window : globalThis);
