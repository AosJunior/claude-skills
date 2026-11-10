// novela.js · biblioteca de componentes de motion da novela (HyperFrames + GSAP, 1080×1920).
// Fonte: <pasta da série>/componentes/. O projeto usa a cópia em assets/novela/ (montar_projeto.py ou sincronizar.py).
// Manual com exemplos: componentes/README.md. Estilo: novela.css (prefixo nv-).
//
// Contrato (vale para todo componente):
// - Cada função monta o DOM dentro de `pai` e devolve um objeto com métodos que DEVOLVEM UMA TIMELINE SOLTA:
//   entrada(), saida() e os do componente (trocar, medir, rosto…). A cena põe cada uma na própria timeline com
//   tl.add(x, a(t)). Timeline solta não anda sozinha: só toca dentro da cena. Chame os métodos na ordem do tempo
//   (cada um continua do estado deixado pelo anterior).
// - Monte tudo dentro de NOVELA.pronto(() => { … }): a Montserrat precisa estar carregada para medir o texto.
//   Medidas (offsetWidth/offsetHeight) passam por NOVELA.visivel: num ato que não começa em 0 o hospedeiro está com
//   display:none na montagem; visivel() o põe display:block só durante a medida.
//   Registre window.__timelines[id] no fim do callback (contrato do HyperFrames para montagem assíncrona).
// - Determinístico: sem Math.random, sem relógio, sem setTimeout, sem animação CSS, nenhum tween de duração zero
//   (o «corte» é um tween de 0,02 s). Só transform, opacidade, filtro, clip e variáveis CSS são animados.
// - Movimento pela mola (assets/mola.js): entrada em MOLA, saída em power3.in mais curta, sem bump de escala
//   em texto parado. As entradas «pop» de etiqueta, balão e «OU» saem de 0,55 de escala (0,07 a 0,1 s até o
//   tamanho cheio, medido em quadro); depois de pousado, nada pulsa.
(function (raiz) {
  "use strict";
  const doc = raiz.document;
  const SVG = "http://www.w3.org/2000/svg";
  let conta = 0;
  const novoId = (p) => `nv-${p}-${++conta}`;
  const CORTE = 0.02; // um quadro a 30 fps: troca seca sem tween de duração zero
  // cor de um token --nv-* do novela.css (a pele da série); o padrão vale se o CSS ainda não carregou
  const cor = (nome, padrao) => (raiz.getComputedStyle(doc.documentElement).getPropertyValue(nome) || "").trim() || padrao;

  // ---------- utilidades ----------
  function solta() {
    // fora do relógio global: só anda quando a cena a põe na timeline dela (testado: órfã não anda)
    const t = gsap.timeline();
    gsap.globalTimeline.remove(t);
    return t;
  }
  function criar(tag, cls, pai, txt) {
    const e = doc.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = txt;
    if (pai) pai.appendChild(e);
    return e;
  }
  function svg(tag, attrs, pai) {
    const e = doc.createElementNS(SVG, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (pai) pai.appendChild(e);
    return e;
  }
  function pos(e, x, y) { e.style.left = x + "px"; e.style.top = y + "px"; return e; }
  const M = (papel, o) => raiz.MOLA(papel, o);
  // Mede com o pai visível. Numa composição de ato que não começa em 0, o hospedeiro (.clip do index.html) está com
  // display:none na hora da montagem e offsetWidth/offsetHeight dão 0. Aqui os ancestrais ocultos ficam
  // display:block só durante o fn (síncrono, sem pintura no meio) e voltam ao que eram. Aninhado, não faz nada.
  function visivel(el, fn) {
    const alt = [];
    for (let e = el; e && e.nodeType === 1 && e !== doc.documentElement; e = e.parentElement) {
      if (raiz.getComputedStyle(e).display === "none") {
        alt.push([e, e.style.getPropertyValue("display"), e.style.getPropertyPriority("display")]);
        e.style.setProperty("display", "block", "important");
      }
    }
    try { return fn(); }
    finally { for (let i = alt.length - 1; i >= 0; i--) { const [e, v, p] = alt[i]; if (v) e.style.setProperty("display", v, p); else e.style.removeProperty("display"); } }
  }
  // reduz o corpo até a largura de layout (sem rotação) caber em max
  function caber(e, max, min) {
    return visivel(e, () => {
      let fs = parseFloat(raiz.getComputedStyle(e).fontSize);
      while (e.offsetWidth > max && fs > (min || 20)) { fs -= 1; e.style.fontSize = fs + "px"; }
      return fs;
    });
  }
  // a raiz da composição: o elemento com o data-composition-id dela que não é o hospedeiro (o do index.html, que
  // tem data-composition-src). Não use document como reserva: appendChild no document quebra a montagem.
  function raizDe(id) {
    // sem seletor montado (o lint do HyperFrames recusa variável em querySelector): filtra pelo atributo
    const todos = [...doc.querySelectorAll("[data-composition-id]")].filter((e) => e.getAttribute("data-composition-id") === id);
    const r = todos.find((e) => !e.hasAttribute("data-composition-src")) || todos[todos.length - 1];
    if (!r) throw new Error(`NOVELA.raizDe: nenhuma composição «${id}» no documento`);
    return r;
  }
  function pronto(fn) {
    const fontes = ["400", "700", "900"].map((p) => doc.fonts.load(`${p} 60px Montserrat`, "ÁÉÇÃÕ09%"));
    return Promise.all(fontes).then(() => doc.fonts.ready).then(fn).catch((e) => { console.error("NOVELA:", e); throw e; });
  }
  // entrada «pop» medida na referência: escala 0,55 → 1 em mola curta, opacidade em 0,06 s; ancorada no transform-origin
  function pop(t, e, at, o) {
    o = o || {};
    const m = M("pousar", { duracao: o.duracao || 0.22 });
    const ir = o.ir !== false;
    t.fromTo(e, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.06, ease: "power1.out", immediateRender: ir }, at);
    t.fromTo(e, { scale: o.de || 0.55 }, { scale: 1, duration: m.d, ease: m, immediateRender: ir }, at);
  }
  function despop(t, e, at) {
    t.to(e, { scale: 0.8, duration: 0.14, ease: "power3.in" }, at);
    t.to(e, { autoAlpha: 0, duration: 0.1, ease: "power3.in" }, at + 0.04);
  }
  // sobe/desce de um deslocamento até o lugar, em mola (entrada de sprite, telefone, emote, barra)
  function chega(t, e, at, o) {
    o = o || {};
    const m = M(o.papel || "pousar", { duracao: o.duracao || 0.4 });
    const ir = o.ir !== false;
    const de = {}, para = { duration: m.d, ease: m, immediateRender: ir };
    de[o.eixo || "y"] = o.dist == null ? 140 : o.dist; para[o.eixo || "y"] = 0;
    t.fromTo(e, { autoAlpha: 0 }, { autoAlpha: 1, duration: o.fade || 0.1, ease: "power1.out", immediateRender: ir }, at);
    t.fromTo(e, de, para, at);
  }
  function vai(t, e, at, o) {
    o = o || {};
    const para = { duration: o.duracao || 0.22, ease: "power3.in" };
    para[o.eixo || "y"] = o.dist == null ? 120 : o.dist;
    t.to(e, para, at);
    t.to(e, { autoAlpha: 0, duration: (o.duracao || 0.22) * 0.7, ease: "power3.in" }, at + (o.duracao || 0.22) * 0.3);
  }

  // ======================================================================================================
  // 1. LEGENDA · NOVELA.legenda(palco, grupos, opts) → timeline pausada (é a da composição legenda.html)
  //    Palavra por palavra, como na referência: cada palavra aparece seca no início dela e a linha se recentra;
  //    1 a `max` palavras por linha (os grupos maiores do legenda-grupos.cjs se dividem ao meio aqui).
  // ======================================================================================================
  function legenda(palco, grupos, o) {
    // fimJanela: fim da janela da legenda (o data-duration do hospedeiro). Se a última fala termina mais de 1,5 s
    // antes dele, a última linha sai 0,35 s depois do fim dela (na novela os cartões do fim ficam sem legenda).
    o = Object.assign({ base: 1560, corpo: 62, min: 44, largura: 840, max: 3, acende: 0.03, pausa: 0.6, fimJanela: Infinity }, o || {});
    const G = [];
    (grupos || []).forEach((g) => {
      const n = g.p.length;
      if (n <= o.max) { G.push(g); return; }
      const tam = Math.ceil(n / Math.ceil(n / o.max));
      for (let i = 0; i < n; i += tam) G.push({ p: g.p.slice(i, i + tam), nx: i + tam >= n ? g.nx : undefined });
    });
    const tl = gsap.timeline({ paused: true });
    const linhas = visivel(palco, () => G.map((g) => {
      const l = criar("div", "nv-lg-linha", palco);
      const txt = criar("div", "nv-lg-txt", l);
      txt.style.fontSize = o.corpo + "px";
      const spans = g.p.map(([w, , , c], k) => {
        const s = criar("span", "nv-lg-p" + (c ? " " + c : ""), txt, w);
        if (k < g.p.length - 1) txt.appendChild(doc.createTextNode(" "));
        return s;
      });
      const fs = caber(txt, o.largura, o.min);
      // linha de base: Montserrat (ascendente 0,968, descendente 0,251) com line-height 1 → base a 0,8585 do corpo
      l.style.top = (o.base - 0.8585 * fs).toFixed(1) + "px";
      const larg = spans.map((s) => s.offsetLeft + s.offsetWidth - spans[0].offsetLeft);
      return { txt, spans, x: larg.map((w) => +(540 - w / 2).toFixed(1)) };
    }));
    const SAI = G.map((g, k) => {
      const prox = G[k + 1], ult = g.p[g.p.length - 1];
      if (!prox) return o.fimJanela - ult[2] > 1.5 ? ult[2] + 0.35 : null;
      const sai = prox.p[0][1] - ult[2] > o.pausa ? ult[2] + 0.35 : prox.p[0][1] - o.acende - 0.07;
      const fala = g.nx !== undefined ? g.nx : prox.p[0][1];
      return Math.max(Math.min(sai, fala - o.acende - 0.07), ult[1] - o.acende + 0.06);
    });
    G.forEach((g, k) => {
      const { txt, spans, x } = linhas[k];
      const entra = k === 0 ? g.p[0][1] - o.acende : Math.max(SAI[k - 1] + 0.065, g.p[0][1] - o.acende);
      let ant = null;
      g.p.forEach(([, ini], j) => {
        const t = +Math.max(ini - o.acende, entra).toFixed(3);
        tl.fromTo(spans[j], { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.05, ease: "power1.out" }, t);
        tl.fromTo(spans[j], { y: 6 }, { y: 0, duration: 0.12, ease: "power3.out" }, t);
        const dx = ant === null ? 0.03 : Math.max(0.02, Math.min(0.05, t - ant - 0.005));
        if (j === 0) tl.fromTo(txt, { x: x[0] }, { x: x[0], duration: 0.03, ease: "none" }, t);
        else tl.to(txt, { x: x[j], duration: dx, ease: "power2.out" }, t);
        ant = t;
      });
      if (SAI[k] !== null) {
        tl.fromTo(txt, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.06, ease: "power3.in", immediateRender: false }, +SAI[k].toFixed(3));
      }
    });
    return tl;
  }

  // ======================================================================================================
  // 2. ETIQUETA INCLINADA · NOVELA.etiqueta(pai, {texto, cor, x, y, giro, corpo, largura})
  //    cor: "vermelha" (o fato contra), "dourada" (número), "azul" (nome), "creme" (pergunta), "escura" (faixa).
  //    x, y = centro. giro em graus (positivo desce para a direita). Métodos: entrada(), trocar(texto, cor), saida().
  // ======================================================================================================
  function etiqueta(pai, o) {
    o = Object.assign({ texto: "", cor: "vermelha", x: 540, y: 1100, giro: 5, corpo: 58, largura: 900 }, o || {});
    const anc = pos(criar("div", "nv-ancora", pai), o.x, o.y);
    anc.style.transform = `rotate(${o.giro}deg)`; // parado: o GSAP nunca mexe na âncora
    if (o.atributos) for (const k in o.atributos) anc.setAttribute(k, o.atributos[k]);
    function face(texto, cor) {
      const w = pos(criar("div", "nv-ancora", anc), 0, 0); // cada face no mesmo centro
      const f = criar("div", `nv-et nv-et--${cor}`, w, texto);
      // a etiqueta fica por cima da cena; o check, ao amostrar muito, lê a âncora girada de tamanho zero como coberta
      f.setAttribute("data-layout-allow-occlusion", "");
      f.style.fontSize = o.corpo + "px";
      caber(f, o.largura, 24);
      return f;
    }
    let atual = face(o.texto, o.cor);
    return {
      el: anc,
      get face() { return atual; },
      entrada(op) { const t = solta(); pop(t, atual, 0, op); return t; },
      // troca no lugar: a face atual dobra em Y e a nova abre do mesmo centro (texto e cor juntos)
      trocar(texto, cor) {
        const a = atual, b = face(texto, cor || o.cor);
        atual = b;
        const t = solta(), m = M("pousar", { duracao: 0.24 });
        t.to(a, { scaleY: 0, duration: 0.1, ease: "power3.in" }, 0);
        t.to(a, { autoAlpha: 0, duration: 0.04, ease: "none" }, 0.07);
        t.fromTo(b, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.04, ease: "none" }, 0.08);
        t.fromTo(b, { scaleY: 0 }, { scaleY: 1, duration: m.d, ease: m }, 0.08);
        return t;
      },
      saida() { const t = solta(); despop(t, atual, 0); return t; },
    };
  }

  // ======================================================================================================
  // 3a. BALÃO DE FALA · NOVELA.balao(pai, {texto, x, y, lado, corpo, largura})
  //     x, y = a ponta do rabo (perto da cabeça de quem fala, sem cobrir o rosto). lado: "centro", "esq" (quem fala
  //     está embaixo à esquerda da ponta) ou "dir". Rabo em degraus de 9 px. Métodos: entrada(), saida().
  // ======================================================================================================
  const RABOS = { // # = traço escuro, o = branco; a 1ª linha cobre a borda de baixo da caixa
    centro: ["#oooooo#", ".#oooo#.", "..#oo#..", "...##..."],
    lado: ["#oooo#", "#ooo#.", "#oo#..", "#o#...", "##...."],
  };
  function rabo(lado) {
    const mapa = lado === "centro" ? RABOS.centro : RABOS.lado, u = 9;
    const s = svg("svg", { width: mapa[0].length * u, height: mapa.length * u, "shape-rendering": "crispEdges" });
    mapa.forEach((linha, r) => [...linha].forEach((c, k) => {
      if (c === ".") return;
      svg("rect", { x: k * u, y: r * u, width: u, height: u, fill: c === "#" ? cor("--nv-contorno", "#0a0c12") : cor("--nv-branco", "#ffffff") }, s);
    }));
    return { s, alto: mapa.length * u };
  }
  function balao(pai, o) {
    o = Object.assign({ texto: "", x: 540, y: 600, lado: "centro", corpo: 64, largura: 900 }, o || {});
    const anc = pos(criar("div", "", pai), o.x, o.y);
    anc.style.cssText += ";position:absolute;width:0;height:0";
    const corpo = criar("div", `nv-bl-corpo nv-bl-corpo--${o.lado}`, anc);
    const b = criar("div", `nv-bl nv-bl--${o.lado}`, corpo, o.texto);
    b.style.fontSize = o.corpo + "px";
    caber(b, o.largura, 28);
    const r = rabo(o.lado);
    b.appendChild(r.s);
    r.s.style.top = "100%";
    const desce = r.alto - 9; // da borda de baixo da caixa até a ponta
    corpo.style.bottom = desce + "px";
    b.style.transformOrigin = o.lado === "centro" ? `50% calc(100% + ${desce}px)`
      : o.lado === "esq" ? `64px calc(100% + ${desce}px)` : `calc(100% - 64px) calc(100% + ${desce}px)`;
    return {
      el: anc,
      entrada(op) { const t = solta(); pop(t, b, 0, Object.assign({ de: 0.45, duracao: 0.24 }, op)); return t; },
      saida() { const t = solta(); despop(t, b, 0); return t; },
    };
  }

  // ======================================================================================================
  // 3b. EMOTE · NOVELA.emote(pai, {tipo, x, y, escala})  tipo: "gota", "!", "?"
  //     x, y = centro da base do emote (logo acima da cabeça). Pixel art em SVG. Métodos: entrada(), saida().
  // ======================================================================================================
  const EMOTES = {
    gota: { cores: { "#": "#0a0c12", b: "#5fb8ff", w: "#e9f7ff", d: "#2f7fd0" }, px: [
      "...##...", "...##...", "..#bb#..", "..#wb#..", ".#wbbb#.", ".#wbbb#.", "#wbbbbb#", "#bbbbbb#", "#bbbbbd#", ".#bbdd#.", "..####.."] },
    "!": { cores: { "#": "#0a0c12", y: "#ffd23f", d: "#e0a400" }, px: [
      ".####.", "#yyyy#", "#yyyy#", "#yyyy#", "#yyyd#", ".#yd#.", ".#yd#.", "..##..", "......", ".####.", ".#yd#.", ".####."] },
    "?": { cores: { "#": "#0a0c12", y: "#ffd23f", d: "#e0a400" }, px: [
      "..#####..", ".#yyyyy#.", "#yyy#yyy#", "#yy#.#yy#", ".##..#yy#", "....#yyd#", "...#yyd#.", "..#yyd#..",
      "..#yd#...", "..####...", ".........", "..####...", "..#yd#...", "..#yd#...", "..####..."] },
  };
  function emote(pai, o) {
    o = Object.assign({ tipo: "gota", x: 540, y: 600, escala: 10 }, o || {});
    const def = EMOTES[o.tipo];
    if (!def) throw new Error(`NOVELA.emote: tipo «${o.tipo}» (há: ${Object.keys(EMOTES).join(", ")})`);
    const w = def.px[0].length, h = def.px.length;
    const s = svg("svg", { class: "nv-emote", width: w * o.escala, height: h * o.escala, viewBox: `0 0 ${w} ${h}`, "shape-rendering": "crispEdges" }, pai);
    def.px.forEach((linha, r) => [...linha].forEach((c, k) => {
      if (c !== ".") svg("rect", { x: k, y: r, width: 1.02, height: 1.02, fill: def.cores[c] }, s);
    }));
    pos(s, o.x - (w * o.escala) / 2, o.y - h * o.escala);
    return {
      el: s,
      entrada() { const t = solta(); chega(t, s, 0, { dist: -60, duracao: 0.32, fade: 0.08 }); return t; },
      saida() { const t = solta(); vai(t, s, 0, { dist: -40, duracao: 0.16 }); return t; },
    };
  }

  // ======================================================================================================
  // 4. BARRA DE JOGO · NOVELA.barra(pai, {y, dias, rotuloDias, unidade, rotulo, valor})
  //    Relógio «FALTAM N DIAS» e medidor com rótulo, trilho e porcentagem. Métodos: entradaRelogio(),
  //    entradaMedidor(), saida(), volta() (as duas caixas de novo), medir(valor, op) e contar(dias, op): o número
  //    gira na roleta desta skill (assets/roleta.js) e o trilho anda em MOLA("estado").
  // ======================================================================================================
  let sementeRoleta = 7301;
  function rolar(t, caixa, antigo, texto, o) {
    o = o || {};
    const novo = criar(antigo.tagName.toLowerCase(), antigo.className, caixa);
    if (antigo.getAttribute("style")) novo.setAttribute("style", antigo.getAttribute("style"));
    // o novo fica por cima do antigo, fora do fluxo: no fluxo, os dois somavam largura (o «40» ganhava um buraco ao
    // lado e o «39 DIAS» vazava da caixa). O antigo segue no fluxo, apagado, e dá a largura.
    if (raiz.getComputedStyle(antigo).position === "static") { novo.style.position = "absolute"; novo.style.left = "0"; novo.style.top = "0"; }
    t.to(antigo, { autoAlpha: 0, duration: 0.03, ease: "none" }, 0);
    t.fromTo(novo, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.03, ease: "none" }, 0);
    raiz.ROLETA.animar(t, novo, {
      valor: texto, inicio: 0, pousos: { de: o.de == null ? 0.45 : o.de, ate: o.ate == null ? 0.7 : o.ate },
      ordem: "dir-esq", cor: o.cor || cor("--nv-quente", "#f5a441"), arranque: 0.06, semente: o.semente || (sementeRoleta += 977),
    }, (x) => x);
    return novo;
  }
  function barra(pai, o) {
    o = Object.assign({ y: 240, dias: 40, rotuloDias: "FALTAM", unidade: "DIAS", rotulo: "", valor: 2 }, o || {});
    const b = pos(criar("div", "nv-barra", pai), 72, o.y);
    b.style.left = "72px";
    const rel = criar("div", "nv-barra-caixa nv-barra-relogio", b);
    criar("div", "nv-barra-rotulo", rel, o.rotuloDias);
    const val = criar("div", "nv-barra-valor", rel);
    const caixaDias = criar("span", "", val);
    caixaDias.style.cssText = "position:relative;display:inline-block";
    let dnum = criar("span", "", caixaDias, String(o.dias));
    criar("span", "", val, " " + o.unidade);
    const med = criar("div", "nv-barra-caixa nv-barra-medidor", b);
    const rot = criar("div", "nv-barra-rotulo", med, o.rotulo);
    caber(rot, 560, 22);
    const linha = criar("div", "nv-barra-linha", med);
    const trilho = criar("div", "nv-barra-trilho", linha);
    const nivel = criar("div", "nv-barra-nivel", trilho);
    const pct = criar("div", "nv-barra-pct", linha);
    let num = criar("div", "nv-barra-num", pct, o.valor + "%");
    const esc = (v) => Math.max(14 / 400, Math.min(1, v / 100)); // 2 % ainda aparece como um toco
    nivel.style.transform = `scaleX(${esc(o.valor)})`;
    let valor = o.valor, mostrouRel = false, mostrouMed = false;
    return {
      el: b, relogio: rel, medidor: med,
      entradaRelogio() { const t = solta(); chega(t, rel, 0, { dist: -300, duracao: 0.32, fade: 0.08, ir: !mostrouRel }); mostrouRel = true; return t; },
      entradaMedidor() { const t = solta(); chega(t, med, 0, { dist: -300, duracao: 0.32, fade: 0.08, ir: !mostrouMed }); mostrouMed = true; return t; },
      saida() { const t = solta(); vai(t, rel, 0, { dist: -300, duracao: 0.22 }); vai(t, med, 0.04, { dist: -300, duracao: 0.22 }); return t; },
      volta() {
        const t = solta();
        chega(t, rel, 0, { dist: -300, duracao: 0.32, fade: 0.08, ir: !mostrouRel });
        chega(t, med, 0.06, { dist: -300, duracao: 0.32, fade: 0.08, ir: !mostrouMed });
        mostrouRel = mostrouMed = true;
        return t;
      },
      medir(novo, op) {
        const t = solta(), m = M("estado", { duracao: 0.7 });
        t.fromTo(nivel, { scaleX: esc(valor) }, { scaleX: esc(novo), duration: m.d, ease: m, immediateRender: false }, 0);
        num = rolar(t, pct, num, novo + "%", op);
        valor = novo;
        return t;
      },
      contar(dias, op) { const t = solta(); dnum = rolar(t, caixaDias, dnum, String(dias), Object.assign({ cor: cor("--nv-claro", "#f3f1ec") }, op)); return t; },
    };
  }

  // ======================================================================================================
  // 5. CENA ILUSTRADA · NOVELA.cena(pai, {fundo, frente, sprites, foco, luz, reforco})
  //    fundo/frente: {src, tamanho:[w,h], escala, fx, fy, desfoque, luz}. A frente é uma imagem do mesmo tamanho
  //    do fundo, com alfa, só com o objeto cortado na borda de baixo.
  //    sprites: [{id, poses:{nome: src} (ou src), pose, x (centro), topo, altura, sombra, entra:{de, atraso}}].
  //    A luz do lugar vem pintada no sprite (componentes/iluminar.py, perfis quente, fria e tela-azul); `luz` +
  //    `reforco` (0 a 1, padrão 0) acendem um radial suave da mesma cor atrás da personagem.
  //    Métodos: entrada(), saida(), empurrao(dur, op), rosto(op), abrir(), pose(id, nome), recorte(ids, op),
  //    soltar(), entrar(id, op), sair(id).
  // ======================================================================================================
  const LUZES = { quente: "255,184,103", fria: "156,196,255", "tela-azul": "89,180,255" };
  function enquadrar(e, f) {
    const [w, h] = f.tamanho || [1520, 2688];
    const s = Math.max(1080 / w, 1920 / h) * (f.escala || 1.08);
    const W = w * s, H = h * s, B = 30; // sobra mínima na borda, para o desfoque não mostrar a beirada
    const fx = f.fx == null ? 0.5 : f.fx, fy = f.fy == null ? 0.5 : f.fy;
    const lim = (v, lo, hi) => (lo > hi ? (lo + hi) / 2 : Math.min(hi, Math.max(lo, v)));
    const x = lim((1080 - W) * fx, 1080 - W + B, -B), y = lim((1920 - H) * fy, 1920 - H + B, -B);
    e.style.cssText += `;left:${x.toFixed(1)}px;top:${y.toFixed(1)}px;width:${W.toFixed(1)}px;height:${H.toFixed(1)}px;background-image:url("${f.src}")`;
    e.style.setProperty("--nv-desf", String(f.desfoque == null ? 4 : f.desfoque));
    e.style.setProperty("--nv-luz", String(f.luz == null ? 0.86 : f.luz));
  }
  function cena(pai, o) {
    o = Object.assign({ fundo: null, frente: null, sprites: [], foco: [540, 900], luz: null, reforco: 0 }, o || {});
    const root = criar("div", "nv-cena", pai);
    const cam = criar("div", "nv-cam", root);
    const origem = `${o.foco[0]}px ${o.foco[1]}px`;
    const pf = criar("div", "nv-plano", cam), pm = criar("div", "nv-plano", cam);
    const planos = [[pf, 0.4], [pm, 0.7]];
    const fimg = criar("div", "nv-fundo-img", pf);
    if (o.fundo) enquadrar(fimg, o.fundo);
    let frimg = null;
    if (o.frente) {
      const pfr = criar("div", "nv-plano", cam);
      frimg = criar("div", "nv-frente-img", pfr);
      enquadrar(frimg, Object.assign({ desfoque: 3, luz: 1 }, o.frente));
      planos.push([pfr, 1]);
    }
    planos.forEach(([p]) => { p.style.transformOrigin = origem; });
    const base = { fd: o.fundo ? (o.fundo.desfoque == null ? 4 : o.fundo.desfoque) : 4, fl: o.fundo ? (o.fundo.luz == null ? 0.86 : o.fundo.luz) : 0.86,
      rd: o.frente ? (o.frente.desfoque == null ? 3 : o.frente.desfoque) : 3, rl: o.frente ? (o.frente.luz == null ? 1 : o.frente.luz) : 1 };
    const S = {};
    o.sprites.forEach((d) => {
      const poses = d.poses || { base: d.src };
      const fim = d.topo + d.altura;
      if (o.luz && o.reforco > 0) {
        const L = criar("div", "nv-luz", pm), r = d.altura * 0.62;
        pos(L, d.x - r, d.topo + d.altura * 0.22 - r);
        L.style.width = L.style.height = 2 * r + "px";
        L.style.background = `radial-gradient(closest-side, rgba(${LUZES[o.luz]},${o.reforco}), rgba(${LUZES[o.luz]},0))`;
      }
      if (d.sombra === true || (d.sombra !== false && fim < 1900)) {
        const sb = criar("div", "nv-sombra", pm), w = d.altura * 0.42, h = d.altura * 0.075;
        pos(sb, d.x - w / 2, fim - h * 0.55);
        sb.style.width = w + "px"; sb.style.height = h + "px";
      }
      const sp = pos(criar("div", "nv-sprite", pm), d.x, d.topo);
      sp.style.height = d.altura + "px";
      const box = criar("div", "nv-sprite-poses", sp);
      const imgs = {};
      Object.keys(poses).forEach((nome) => {
        const im = criar("img", "nv-pose", box);
        im.src = poses[nome]; im.alt = ""; im.style.height = d.altura + "px";
        imgs[nome] = im;
      });
      const inicial = d.pose || Object.keys(poses)[0];
      Object.keys(imgs).forEach((n) => { if (n !== inicial) imgs[n].style.visibility = "hidden"; });
      S[d.id] = { d, sp, box, imgs, pose: inicial, mexeu: false };
    });
    let camAtual = { x: 0, y: 0, scale: 1 }, recortado = false;
    function camera(t, alvo) {
      t.fromTo(cam, Object.assign({}, camAtual), Object.assign({ duration: CORTE, ease: "none", immediateRender: false }, alvo), 0);
      camAtual = alvo;
    }
    function trocaPose(t, id, nome, at) {
      const s = S[id];
      if (!s || !s.imgs[nome]) throw new Error(`NOVELA.cena: pose «${nome}» de «${id}» não existe`);
      if (s.pose === nome) return;
      t.fromTo(s.imgs[s.pose], { autoAlpha: 1 }, { autoAlpha: 0, duration: CORTE, ease: "none", immediateRender: false }, at);
      t.fromTo(s.imgs[nome], { autoAlpha: 0 }, { autoAlpha: 1, duration: CORTE, ease: "none", immediateRender: false }, at);
      s.pose = nome;
    }
    function entraSprite(t, s, at, de) {
      const m = { baixo: ["y", 160], cima: ["y", -160], esq: ["x", -240], dir: ["x", 240] }[de || "baixo"];
      chega(t, s.sp, at, { eixo: m[0], dist: m[1], duracao: 0.4, ir: !s.mexeu });
      s.mexeu = true;
    }
    return {
      el: root, camera: cam, sprite: (id) => S[id] && S[id].sp,
      entrada() {
        const t = solta();
        t.fromTo(root, { autoAlpha: 0 }, { autoAlpha: 1, duration: CORTE, ease: "none" }, 0);
        Object.values(S).forEach((s) => { if (s.d.entra) entraSprite(t, s, s.d.entra.atraso || 0, s.d.entra.de); });
        return t;
      },
      saida() { const t = solta(); t.to(root, { autoAlpha: 0, duration: CORTE, ease: "none" }, 0); return t; },
      // empurrão lento com paralaxe: fundo 0,4 · personagem 0,7 · frente 1,0 do movimento
      empurrao(dur, op) {
        op = Object.assign({ ate: 1.06, dx: 0, dy: 0, ease: "none" }, op || {});
        const t = solta();
        planos.forEach(([p, k]) => {
          t.fromTo(p, { scale: 1, x: 0, y: 0 }, { scale: 1 + (op.ate - 1) * k, x: op.dx * k, y: op.dy * k, duration: dur, ease: op.ease }, 0);
        });
        return t;
      },
      // corte para o rosto: a câmera salta para um recorte mais fechado (sem animar a escala); pose opcional
      rosto(op) {
        op = Object.assign({ x: 540, y: 900, escala: 1.6, centro: [540, 760], pose: null }, op || {});
        const t = solta(), sc = op.escala;
        const lim = (v, lo) => Math.min(0, Math.max(lo, v));
        camera(t, { scale: sc, x: +lim(op.centro[0] - op.x * sc, 1080 - 1080 * sc).toFixed(1), y: +lim(op.centro[1] - op.y * sc, 1920 - 1920 * sc).toFixed(1) });
        if (op.pose) trocaPose(t, op.pose[0], op.pose[1], 0);
        return t;
      },
      abrir() { const t = solta(); camera(t, { scale: 1, x: 0, y: 0 }); return t; },
      pose(id, nome) { const t = solta(); trocaPose(t, id, nome, 0); return t; },
      // piada física: fundo escurece e desfoca, quem não é recortado apaga, o recortado ganha contorno branco
      recorte(ids, op) {
        op = Object.assign({ escurece: 0.5, desfoque: 6, contorno: 5 }, op || {});
        ids = [].concat(ids);
        const t = solta(), ml = M("luz", { duracao: 0.3 }), mc = M("assentar", { duracao: 0.18 });
        t.fromTo(fimg, { "--nv-luz": base.fl, "--nv-desf": base.fd }, { "--nv-luz": base.fl * op.escurece, "--nv-desf": base.fd + op.desfoque, duration: ml.d, ease: ml, immediateRender: false }, 0);
        if (frimg) t.fromTo(frimg, { "--nv-luz": base.rl, "--nv-desf": base.rd }, { "--nv-luz": base.rl * op.escurece, "--nv-desf": base.rd + op.desfoque, duration: ml.d, ease: ml, immediateRender: false }, 0);
        Object.keys(S).forEach((id) => {
          const box = S[id].box;
          if (ids.includes(id)) t.fromTo(box, { "--nv-c": "0px", "--nv-ca": 0 }, { "--nv-c": op.contorno + "px", "--nv-ca": 1, duration: mc.d, ease: mc, immediateRender: false }, 0.04);
          else t.fromTo(box, { "--nv-sl": 1 }, { "--nv-sl": op.escurece, duration: ml.d, ease: ml, immediateRender: false }, 0);
        });
        recortado = { ids, op };
        return t;
      },
      soltar() {
        const t = solta();
        if (!recortado) return t;
        const { ids, op } = recortado, ml = M("luz", { duracao: 0.3 });
        t.to(fimg, { "--nv-luz": base.fl, "--nv-desf": base.fd, duration: ml.d, ease: ml }, 0);
        if (frimg) t.to(frimg, { "--nv-luz": base.rl, "--nv-desf": base.rd, duration: ml.d, ease: ml }, 0);
        Object.keys(S).forEach((id) => {
          if (ids.includes(id)) t.to(S[id].box, { "--nv-c": "0px", "--nv-ca": 0, duration: 0.14, ease: "power3.in" }, 0);
          else t.to(S[id].box, { "--nv-sl": 1, duration: ml.d, ease: ml }, 0);
        });
        recortado = false;
        return t;
      },
      entrar(id, op) { const t = solta(); entraSprite(t, S[id], 0, op && op.de); return t; },
      sair(id) { const t = solta(); vai(t, S[id].sp, 0, { dist: 160, duracao: 0.24 }); return t; },
    };
  }

  // ======================================================================================================
  // 6. TRANSIÇÕES · NOVELA.chicote(sai, entra, op) · NOVELA.corte(sai, entra)
  //    Chicote: os dois quadros andam juntos de lado, como uma faixa, com borrão só na horizontal (filtro SVG).
  //    op: {direcao: "esq" (o novo vem da direita) | "dir", dur: 0.26, borrao: 70}. Para cenas em composições
  //    diferentes, cada lado chama a sua metade no mesmo instante: NOVELA.chicote.sai(el, op) / .entra(el, op).
  //    Corte seco: troca em 0,02 s. Metades: NOVELA.corte.sai(el) / .entra(el).
  // ======================================================================================================
  function borrao(e) {
    const id = novoId("borrao");
    const s = svg("svg", { width: 0, height: 0, "aria-hidden": "true" }, e.parentNode);
    s.style.position = "absolute";
    const f = svg("filter", { id, x: "-5%", y: "0%", width: "110%", height: "100%", "color-interpolation-filters": "sRGB" }, s);
    const g = svg("feGaussianBlur", { in: "SourceGraphic", stdDeviation: "0 0" }, f);
    e.style.filter = `url(#${id})`;
    return g;
  }
  function metadeChicote(e, op, entra) {
    op = Object.assign({ direcao: "esq", dur: 0.26, borrao: 70 }, op || {});
    const s = op.direcao === "esq" ? -1 : 1, g = borrao(e), t = solta(), d = op.dur;
    if (entra) {
      t.fromTo(e, { autoAlpha: 0 }, { autoAlpha: 1, duration: CORTE, ease: "none" }, 0);
      t.fromTo(e, { x: -s * 1080 }, { x: 0, duration: d, ease: "power3.inOut" }, 0);
    } else {
      t.fromTo(e, { x: 0 }, { x: s * 1080, duration: d, ease: "power3.inOut", immediateRender: false }, 0);
      t.to(e, { autoAlpha: 0, duration: CORTE, ease: "none" }, d);
    }
    t.fromTo(g, { attr: { stdDeviation: "0 0" } }, { attr: { stdDeviation: `${op.borrao} 0` }, duration: d / 2, ease: "power2.in", immediateRender: false }, 0);
    t.to(g, { attr: { stdDeviation: "0 0" }, duration: d / 2, ease: "power2.out" }, d / 2);
    return t;
  }
  function chicote(sai, entra, op) {
    const t = solta();
    if (sai) t.add(metadeChicote(sai, op, false), 0);
    if (entra) t.add(metadeChicote(entra, op, true), 0);
    return t;
  }
  chicote.sai = (e, op) => metadeChicote(e, op, false);
  chicote.entra = (e, op) => metadeChicote(e, op, true);
  function corte(sai, entra) {
    const t = solta();
    if (sai) t.fromTo(sai, { autoAlpha: 1 }, { autoAlpha: 0, duration: CORTE, ease: "none", immediateRender: false }, 0);
    if (entra) t.fromTo(entra, { autoAlpha: 0 }, { autoAlpha: 1, duration: CORTE, ease: "none" }, 0);
    return t;
  }
  corte.sai = (e) => corte(e, null);
  corte.entra = (e) => corte(null, e);

  // ======================================================================================================
  // 7. TELEFONE · NOVELA.telefone(pai, {tamanho, miolo, hora, rotulo, chapada, conversa|perfil|post|video})
  //    tamanho: "conversa" (corpo x 200–880, y 390–1430) ou "grande" (vídeo 9:16 de 720×1280, corpo até y 1642,
  //    exceção planejada: a barra e a legenda saem). Tela chapada da pele com grade de pontos atrás (chapada: false tira).
  //    Métodos: entrada({sobe}), saida() e os do miolo:
  //    conversa → mensagem(i), digitando(i, dur) · perfil → destacar(i) · post → teia() · video → nenhum.
  //    Vídeo real: a composição escreve o <video> no HTML dela (class="clip", muted, playsinline, data-start e
  //    data-duration no tempo da composição, data-track-index) e passa o elemento em `video`; o componente só o põe
  //    na tela. Nunca play() nem seek: o HyperFrames toca.
  // ======================================================================================================
  const CEL = { conversa: { x: 200, y: 390, w: 680, h: 1040, borda: 16 }, grande: { x: 158, y: 318, w: 764, h: 1324, borda: 22 } };
  function avatar(pai, a, tam) {
    const e = criar("div", "nv-avatar", pai);
    e.style.width = e.style.height = tam + "px";
    e.style.fontSize = Math.round(tam * 0.36) + "px";
    a = a || {};
    if (a.cor) e.style.backgroundColor = a.cor;
    if (a.src) { e.style.backgroundImage = `url("${a.src}")`; e.style.backgroundSize = a.tamanho || "260%"; e.style.backgroundPosition = a.posicao || "50% 6%"; }
    else e.textContent = a.iniciais || "";
    return e;
  }
  function statusBar(tela, hora) {
    const s = criar("div", "nv-cel-status", tela);
    criar("span", "", s, hora || "");
    criar("i", "", s);
    return s;
  }
  function mioloConversa(tela, c, W) {
    statusBar(tela, c.hora);
    const topo = criar("div", "nv-cv-topo", tela);
    criar("div", "nv-cv-voltar", topo, "‹");
    avatar(topo, c.avatar, 72);
    const nomes = criar("div", "", topo);
    criar("div", "nv-cv-nome", nomes, c.contato || "");
    const sub = criar("div", "nv-cv-sub", nomes);
    sub.setAttribute("data-layout-allow-overlap", ""); // «online» e «digitando…» se revezam no mesmo lugar
    const online = criar("span", "", sub, c.sub || "online");
    const digit = criar("span", "", sub, "digitando…");
    digit.style.visibility = "hidden";
    const corpo = criar("div", "nv-cv-corpo", tela);
    let y = 30;
    const msgs = (c.mensagens || []).map((m) => {
      const e = criar("div", `nv-msg nv-msg--${m.de === "eu" ? "eu" : "eles"}`, corpo);
      criar("span", "", e, m.texto);
      if (m.hora) { const h = criar("span", "nv-msg-hora", e, m.hora); h.setAttribute("data-layout-ignore", ""); }
      e.style.top = y + "px";
      e.style.maxWidth = Math.round((W - 52) * 0.84) + "px";
      y += e.offsetHeight + 22;
      return e;
    });
    const dig = criar("div", "nv-msg nv-msg--eles nv-msg--digitando", corpo);
    const pontos = [0, 1, 2].map(() => criar("b", "", dig));
    dig.style.visibility = "hidden";
    const mostradas = new Set();
    return {
      mensagem(i) {
        const t = solta(), e = msgs[i];
        chega(t, e, 0, { dist: 26, duracao: 0.3, fade: 0.1, ir: !mostradas.has(i) });
        t.fromTo(e, { scale: 0.96 }, { scale: 1, duration: 0.3, ease: M("assentar", { duracao: 0.2 }), immediateRender: !mostradas.has(i) }, 0);
        mostradas.add(i);
        return t;
      },
      // «digitando…»: bolha com três pontos no lugar da mensagem i e o subtítulo do topo trocado, por dur segundos
      digitando(i, dur) {
        dur = dur || 0.8;
        const t = solta();
        dig.style.top = msgs[i] ? msgs[i].style.top : y + "px";
        t.fromTo(dig, { autoAlpha: 0, y: 14 }, { autoAlpha: 1, y: 0, duration: 0.16, ease: "power3.out", immediateRender: false }, 0);
        t.fromTo(online, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.06, immediateRender: false }, 0);
        t.fromTo(digit, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.06, immediateRender: false }, 0.03);
        const voltas = Math.max(1, Math.floor((dur - 0.1) / 0.6));
        pontos.forEach((p, k) => t.fromTo(p, { opacity: 0.3 }, { opacity: 1, duration: 0.3, ease: "sine.inOut", repeat: voltas * 2 - 1, yoyo: true, immediateRender: false }, 0.05 + k * 0.15));
        t.to(dig, { autoAlpha: 0, duration: 0.08, ease: "power3.in" }, dur);
        t.to(digit, { autoAlpha: 0, duration: 0.06 }, dur);
        t.to(online, { autoAlpha: 1, duration: 0.06 }, dur + 0.03);
        return t;
      },
    };
  }
  function mioloPerfil(tela, p, W) {
    statusBar(tela, p.hora);
    criar("div", "nv-pf-topo", tela, p.usuario || "");
    const cab = criar("div", "nv-pf-cab", tela);
    avatar(cab, p.avatar, 150);
    const nums = criar("div", "nv-pf-nums", cab);
    [[p.posts, "posts"], [p.seguidores, "seguidores"], [p.seguindo, "seguindo"]].forEach(([n, r]) => {
      const e = criar("div", "nv-pf-num", nums);
      criar("b", "", e, String(n == null ? "" : n));
      criar("span", "", e, r);
    });
    let y = 340;
    const nome = criar("div", "nv-pf-nome", tela, p.nome || "");
    nome.style.top = y + "px"; y += nome.offsetHeight + 8;
    const bio = criar("div", "nv-pf-bio", tela, p.bio || "");
    bio.style.top = y + "px"; y += bio.offsetHeight + 22;
    const bt = criar("div", "nv-pf-botao", tela, p.botao || "Editar perfil");
    bt.style.top = y + "px"; y += 66 + 26;
    const grade = criar("div", "nv-pf-grade", tela);
    grade.style.top = y + "px";
    const aneis = (p.grade || []).map((g) => {
      const e = criar("div", "nv-pf-post", grade, g.texto || "");
      e.setAttribute("data-layout-ignore", ""); // miniatura: textura, não leitura (o post aberto é o que se lê)
      e.style.background = g.cor || cor("--nv-dourado", "#f0cd78");
      if (g.views) criar("div", "nv-pf-views", e, "▶ " + g.views);
      const anel = criar("div", "nv-pf-anel", e);
      anel.style.visibility = "hidden";
      return anel;
    });
    return {
      destacar(i) {
        const t = solta(), m = M("assentar", { duracao: 0.3 });
        t.fromTo(aneis[i], { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.08, immediateRender: false }, 0);
        t.fromTo(aneis[i], { scale: 1.12 }, { scale: 1, duration: m.d, ease: m, immediateRender: false }, 0);
        return t;
      },
    };
  }
  const ICONES = {
    coracao: "M23 40 C10 31 4 24 4 16 C4 9 9 5 15 5 C19 5 21 8 23 10 C25 8 27 5 31 5 C37 5 42 9 42 16 C42 24 36 31 23 40 Z",
    balao: "M23 5 C34 5 42 12 42 21 C42 30 34 37 23 37 C20 37 17 36 15 35 L6 39 L9 31 C6 28 4 25 4 21 C4 12 12 5 23 5 Z",
    envio: "M4 21 L42 5 L30 41 L22 26 Z M22 26 L42 5",
  };
  function mioloPost(tela, p, W, H) {
    statusBar(tela, p.hora);
    const cab = criar("div", "nv-po-cab", tela);
    avatar(cab, p.avatar, 64);
    criar("span", "", cab, p.usuario || "");
    let y = 170;
    // a imagem cede altura para o resto caber na tela (ações, visualizações, legenda e o botão)
    const alt = Math.min(W, H - y - 330);
    const img = criar("div", "nv-po-img", tela, p.texto || "");
    img.style.top = y + "px"; img.style.height = alt + "px"; img.style.background = p.cor || cor("--nv-claro", "#f3f1ec");
    y += alt + 14;
    const acoes = criar("div", "nv-po-acoes", tela);
    acoes.style.top = y + "px";
    ["coracao", "balao", "envio"].forEach((k) => {
      const s = svg("svg", { viewBox: "0 0 46 46" }, acoes);
      svg("path", { d: ICONES[k], fill: "none", stroke: cor("--nv-claro", "#f3f1ec"), "stroke-width": 3.4, "stroke-linejoin": "round" }, s);
    });
    y += 72;
    const views = criar("div", "nv-po-views", tela, p.views || "");
    views.style.top = y + "px"; y += views.offsetHeight + 8;
    if (p.legenda) { const l = criar("div", "nv-po-legenda", tela, p.legenda); l.style.top = y + "px"; y += l.offsetHeight + 18; }
    const ins = criar("div", "nv-po-insights", tela, p.insights || "Ver insights");
    ins.style.top = y + "px";
    // teia de aranha sobre o botão: fios que se desenham do canto
    const L = W - 60, A = 76;
    const teia = svg("svg", { class: "nv-po-teia", width: L + 40, height: A + 40, viewBox: `-20 -20 ${L + 40} ${A + 40}` }, tela);
    pos(teia, 10, y - 20);
    const fios = [];
    const cx = L - 6, cy = 4;
    [[-1, 0.15], [-1, 0.55], [-1, 1.1], [-0.6, 1.6], [-0.25, 1.9]].forEach(([dx, dy]) => {
      fios.push(svg("path", { d: `M${cx} ${cy} L${cx + dx * 300} ${cy + dy * 60}`, pathLength: 1 }, teia));
    });
    [70, 140, 220].forEach((r) => {
      const pts = [[-1, 0.15], [-1, 0.55], [-1, 1.1], [-0.6, 1.6], [-0.25, 1.9]].map(([dx, dy]) => {
        const n = Math.hypot(dx * 300, dy * 60);
        return [cx + (dx * 300 * r) / n, cy + (dy * 60 * r) / n];
      });
      let d = `M${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)}`;
      for (let k = 1; k < pts.length; k++) d += ` Q${((pts[k - 1][0] + pts[k][0]) / 2 + 10).toFixed(1)} ${((pts[k - 1][1] + pts[k][1]) / 2 - 6).toFixed(1)} ${pts[k][0].toFixed(1)} ${pts[k][1].toFixed(1)}`;
      fios.push(svg("path", { d, pathLength: 1 }, teia));
    });
    fios.forEach((f) => { f.setAttribute("fill", "none"); f.setAttribute("stroke", "rgba(243,241,236,0.85)"); f.setAttribute("stroke-width", "2.5"); f.setAttribute("stroke-dasharray", "1"); f.setAttribute("stroke-dashoffset", "1"); });
    return {
      teia() {
        const t = solta();
        fios.forEach((f, k) => t.fromTo(f, { attr: { "stroke-dashoffset": 1 } }, { attr: { "stroke-dashoffset": 0 }, duration: 0.35, ease: "power2.out", immediateRender: false }, k * 0.05));
        return t;
      },
    };
  }
  function telefone(pai, o) { return visivel(pai, () => telefone_(pai, o)); }
  function telefone_(pai, o) {
    o = Object.assign({ tamanho: "conversa", miolo: "conversa", hora: "", rotulo: null, chapada: true }, o || {});
    const g = CEL[o.tamanho];
    const root = criar("div", "nv-camada", pai);
    const fundo = o.chapada ? criar("div", "nv-chapada", root) : null;
    const cel = pos(criar("div", "nv-cel", root), g.x, g.y);
    cel.style.width = g.w + "px"; cel.style.height = g.h + "px";
    const tela = criar("div", "nv-cel-tela", cel);
    tela.style.inset = g.borda + "px";
    const W = g.w - 2 * g.borda;
    let api = {};
    const dados = Object.assign({ hora: o.hora }, o[o.miolo] || {});
    if (o.miolo === "conversa") api = mioloConversa(tela, dados, W);
    else if (o.miolo === "perfil") api = mioloPerfil(tela, dados, W);
    else if (o.miolo === "post") api = mioloPost(tela, dados, W, g.h - 2 * g.borda);
    else if (o.miolo === "video") {
      if (!o.video) throw new Error("NOVELA.telefone: o miolo «video» pede o <video> da composição em `video`");
      o.video.classList.add("nv-cel-video");
      tela.appendChild(o.video);
    }
    if (o.miolo !== "video") criar("div", "nv-cel-furo", tela);
    const rot = o.rotulo ? etiqueta(root, { texto: o.rotulo, cor: "dourada", x: 540, y: g.y - 30, giro: -4, corpo: 46, largura: 760 }) : null;
    return Object.assign({
      el: root, tela, corpo: cel,
      entrada(op) {
        op = Object.assign({ sobe: true }, op || {});
        const t = solta();
        if (fundo) t.fromTo(fundo, { autoAlpha: 0 }, { autoAlpha: 1, duration: CORTE, ease: "none" }, 0);
        if (op.sobe) {
          chega(t, cel, 0, { dist: 220, duracao: 0.45, fade: 0.12 });
        } else t.fromTo(cel, { autoAlpha: 0 }, { autoAlpha: 1, duration: CORTE, ease: "none" }, 0);
        if (rot) t.add(rot.entrada(), op.sobe ? 0.18 : 0);
        return t;
      },
      saida(op) {
        op = Object.assign({ desce: true }, op || {});
        const t = solta();
        if (op.desce) vai(t, cel, 0, { dist: 160, duracao: 0.24 });
        else t.to(cel, { autoAlpha: 0, duration: CORTE, ease: "none" }, 0);
        if (rot) t.add(rot.saida(), 0);
        if (fundo) t.to(fundo, { autoAlpha: 0, duration: CORTE, ease: "none" }, op.desce ? 0.24 : 0);
        return t;
      },
    }, api);
  }

  // ======================================================================================================
  // 8a. CARTÃO DO MEDIDOR · NOVELA.cartaoMedidor(pai, {rotulo, valor, sprite})
  //     Tela cheia, sem barra: rótulo em duas linhas, trilho quase vazio, percentual vermelho inclinado e a
  //     personagem pequena embaixo. sprite: {src, altura, x, topo}; atrasoPct: s da entrada até o percentual pousar
  //     (padrão 0,72). Métodos: entrada(), saida().
  // ======================================================================================================
  function cartaoMedidor(pai, o) { return visivel(pai, () => cartaoMedidor_(pai, o)); }
  function cartaoMedidor_(pai, o) {
    o = Object.assign({ rotulo: "", valor: 2, sprite: null, atrasoPct: null }, o || {});
    const root = criar("div", "nv-camada", pai);
    const fundo = criar("div", "nv-chapada", root);
    const rot = criar("div", "nv-texto nv-cm-rotulo", root, o.rotulo);
    rot.style.top = "330px";
    const tr = criar("div", "nv-cm-trilho", root);
    tr.style.top = (330 + rot.offsetHeight + 60) + "px";
    const nivel = criar("div", "nv-cm-nivel", tr);
    const yPct = 330 + rot.offsetHeight + 60 + 82 + 150;
    const anc = pos(criar("div", "nv-ancora", root), 540, yPct);
    anc.style.transform = "rotate(-6deg)";
    const pct = criar("div", "nv-texto nv-contorno-txt nv-cm-pct", anc, o.valor + "%");
    pct.setAttribute("data-layout-allow-occlusion", ""); // mesmo falso positivo da etiqueta (âncora girada)
    let sp = null;
    if (o.sprite) {
      sp = criar("img", "nv-pixel", root);
      sp.src = o.sprite.src; sp.alt = "";
      sp.style.cssText += `;position:absolute;height:${o.sprite.altura}px;left:${o.sprite.x}px;top:${o.sprite.topo}px`;
      if (o.sprite.largura) sp.style.width = o.sprite.largura + "px";
    }
    const v = Math.max(14 / 828, Math.min(1, o.valor / 100));
    return {
      el: root, sprite: sp,
      entrada() {
        const t = solta();
        t.fromTo(fundo, { autoAlpha: 0 }, { autoAlpha: 1, duration: CORTE, ease: "none" }, 0);
        chega(t, rot, 0.04, { papel: "assentar", dist: 30, duracao: 0.4, fade: 0.14 });
        const ma = M("assentar", { duracao: 0.4 }), me = M("estado", { duracao: 0.5 });
        t.fromTo(tr, { scaleX: 0 }, { scaleX: 1, duration: ma.d, ease: ma }, 0.18);
        // atrasoPct (padrão 0,72): quando o percentual pousa depois da entrada; o nível anda 0,22 s antes dele. Ponha
        // a diferença entre a palavra do número e a da entrada (ex.: «Chance» 64,34 → «2%» 66,04 = 1,70).
        const ap = o.atrasoPct == null ? 0.72 : o.atrasoPct;
        t.fromTo(nivel, { scaleX: 0 }, { scaleX: v, duration: me.d, ease: me }, Math.max(0.3, ap - 0.22));
        pop(t, pct, ap, { duracao: 0.26 });
        if (sp) chega(t, sp, 0.3, { dist: 120, duracao: 0.4 });
        return t;
      },
      saida() {
        const t = solta();
        [rot, tr, pct.parentNode, sp].filter(Boolean).forEach((e, k) => t.to(e, { autoAlpha: 0, duration: 0.16, ease: "power3.in" }, k * 0.03));
        t.to(fundo, { autoAlpha: 0, duration: CORTE, ease: "none" }, 0.22);
        return t;
      },
    };
  }

  // ======================================================================================================
  // 8b. CARTÃO DAS DUAS OPÇÕES · NOVELA.cartaoOpcoes(pai, {faixa, esq, dir, pergunta})
  //     esq/dir: {nome, acao, custo, sprite:{src, altura}}. Faixa creme no topo (y 0–480) com espaço para a barra
  //     (que é a camada própria, por cima), metades tijolo e azul da pele com o mesmo peso, «OU» no meio e a
  //     pergunta numa etiqueta creme inclinada em y 1420–1580 (data-layout-allow-caption-zone: a legenda sai).
  //     Métodos: entrada() (metades, faixa, nomes, OU, personagens), pergunta(), saida().
  // ======================================================================================================
  function cartaoOpcoes(pai, o) { return visivel(pai, () => cartaoOpcoes_(pai, o)); }
  function cartaoOpcoes_(pai, o) {
    o = Object.assign({ faixa: "COMENTE UMA PALAVRA", esq: {}, dir: {}, pergunta: "" }, o || {});
    const root = criar("div", "nv-camada", pai);
    const topo = criar("div", "nv-op-faixa-topo", root);
    const lados = ["esq", "dir"].map((lado) => {
      const d = o[lado] || {};
      const m = criar("div", `nv-op-metade nv-op-metade--${lado}`, root);
      m.setAttribute("data-layout-allow-overflow", ""); // entra de fora do quadro
      const nome = criar("div", "nv-texto nv-contorno-txt nv-op-nome", m, d.nome || "");
      caber(nome, 500, 56);
      nome.style.left = "0"; nome.style.right = "0";
      const acao = criar("div", "nv-texto nv-op-acao", m, d.acao || "");
      const custo = criar("div", "nv-texto nv-op-custo", m);
      if (d.custo) { criar("b", "", custo, "CUSTA: "); custo.appendChild(doc.createTextNode(d.custo)); }
      custo.style.top = (176 + acao.offsetHeight + 16) + "px";
      let sp = null;
      if (d.sprite) {
        const fundoTexto = 176 + acao.offsetHeight + 16 + custo.offsetHeight;
        const alt = d.sprite.altura || 500, topoSp = Math.max(fundoTexto + 40, 900 - alt);
        // faixa da largura da metade, com a pose centrada por flex (sem translate, que o GSAP moveria)
        sp = criar("div", "", m);
        sp.style.cssText = `position:absolute;left:0;right:0;top:${topoSp}px;height:${alt}px;display:flex;justify-content:center`;
        const im = criar("img", "nv-pixel", sp);
        im.src = d.sprite.src; im.alt = ""; im.style.height = alt + "px"; im.style.flex = "none";
      }
      return { m, nome, acao, custo, sp, lado };
    });
    const faixa = etiqueta(root, { texto: o.faixa, cor: "escura", x: 540, y: 420, giro: 0, corpo: 46, largura: 860 });
    const ouW = pos(criar("div", "nv-ancora", root), 540, 1110);
    const ou = criar("div", "nv-texto nv-op-ou", ouW, "OU");
    ou.style.position = "relative"; ou.style.left = "0"; ou.style.top = "0";
    const perg = o.pergunta ? etiqueta(root, { texto: o.pergunta, cor: "creme", x: 540, y: 1500, giro: 4, corpo: 52, largura: 880,
      atributos: { "data-layout-allow-caption-zone": "" } }) : null;
    if (perg) perg.face.setAttribute("data-layout-allow-caption-zone", "");
    return {
      el: root,
      entrada() {
        const t = solta();
        t.fromTo(topo, { autoAlpha: 0 }, { autoAlpha: 1, duration: CORTE, ease: "none" }, 0);
        // medido: as metades entram das bordas para o centro em ~0,3 s; o resto pousa quando elas se fecham
        lados.forEach(({ m, lado }) => t.fromTo(m, { xPercent: lado === "esq" ? -100 : 100 }, { xPercent: 0, duration: 0.3, ease: "power3.out" }, 0));
        const fx = M("assentar", { duracao: 0.2 });
        t.fromTo(faixa.face, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.05 }, 0);
        t.fromTo(faixa.face, { scaleX: 0 }, { scaleX: 1, duration: fx.d, ease: fx }, 0);
        lados.forEach(({ nome, acao, custo, sp }, k) => {
          pop(t, nome, 0.28 + k * 0.04, { de: 0.7, duracao: 0.24 });
          chega(t, acao, 0.36 + k * 0.04, { papel: "assentar", dist: 18, duracao: 0.3, fade: 0.12 });
          chega(t, custo, 0.42 + k * 0.04, { papel: "assentar", dist: 18, duracao: 0.3, fade: 0.12 });
          if (sp) chega(t, sp, 0.3 + k * 0.17, { dist: -320, duracao: 0.34, fade: 0.08 });
        });
        pop(t, ou, 0.3, { duracao: 0.24 });
        return t;
      },
      pergunta() { return perg ? perg.entrada({ duracao: 0.26 }) : solta(); },
      saida() { const t = solta(); t.to(root, { autoAlpha: 0, duration: 0.2, ease: "power3.in" }, 0); return t; },
    };
  }

  raiz.NOVELA = { pronto, raizDe, solta, visivel, caber, legenda, etiqueta, balao, emote, barra, cena, chicote, corte, telefone, cartaoMedidor, cartaoOpcoes, EMOTES };
})(typeof window !== "undefined" ? window : globalThis);
