// Grupos da legenda a partir do briefings/palavras-voz.json. Grava o assets/legenda-grupos.js, que o
// compositions/legenda.html carrega. A legenda vive no tempo real: os tempos saem do palavras-voz.json da narração que
// está no vídeo e entram na legenda sem VOZ.w. Rode de novo sempre que a narração mudar, no texto ou no tempo; edição à
// mão no arquivo gerado se perde.
//
// Uso (na raiz do projeto motion):
//   node briefings/legenda-grupos.cjs [--de S] [--ate S] [--sem INI-FIM,…] [--a "Nome,…"] [--b "Nome,…"]
//                                    [--e "PALAVRA"] [--n "SIGLA,…"] [--palavras ARQ] [--saida ARQ]
//   --de, --ate  só as palavras que começam nesse trecho, em segundos do palavras-voz.json. O gancho com a frase escrita
//                na tela fica sem legenda: comece no fim dele (--de 5.6).
//   --sem        trechos sem legenda porque a frase já está grande na tela, ex.: --sem 13.6-14.6,40.1-41
//   --a, --b     nomes de cada lado, pintados na cor do lado (800). Nome composto vai inteiro: --a "Lia Prado,Lia"
//   --e          a palavra do CTA (o que comentar), em 900 a 1,2 em
//   --n          palavras em branco 800 além das automáticas (números, siglas e a unidade depois do número)
//   --palavras   padrão briefings/palavras-voz.json · --saida padrão assets/legenda-grupos.js
//
// Regras:
// - 2 a 4 palavras por linha, quebra na pontuação e nas pausas de 0,25 s ou mais;
// - o número fica com a palavra seguinte («1,2 milhão», «300 mil»), e a sigla fica com a de antes («o IBGE»);
// - nenhuma linha passa de 840 px: o corpo 60 desce até 52 e, se ainda não couber, o grupo se divide;
// - até duas palavras coloridas por linha (CTA, depois os lados, depois os números).
// A largura sai dos avanços do Inter 700/800/900 (tabela abaixo, tirada dos .woff2 de assets/fontes) com o
// letter-spacing da legenda. Medida no Chromium, a linha real fica até 4 px mais estreita que a estimativa (o kerning).
// Fonte trocada pede tabela nova.
// Saída: o arquivo e, no stdout, cada linha com o início, o corpo e a largura, mais os avisos.
"use strict";
const fs = require("fs"), path = require("path");
const RAIZ = path.join(__dirname, "..");

const LIMITE = 840;        // largura segura da linha (x 110–950)
const FOLGA = 0.99;        // a estimativa tem de caber em 99 % do limite
const CORPO = 60, CORPO_MIN = 52;
const ESPACO = -0.012;     // letter-spacing da .lg-linha, em em
const PAUSA = 0.25;        // pausa que quebra a linha
const PAUSA_LONGA = 0.6;   // pausa em que a legenda.html limpa a tela: palavra sozinha não se junta por cima dela

// Avanços do Inter (milésimos de em) por peso, na ordem de CARACTERES.
const CARACTERES =
  " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\u00a0¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿıŒœʻʼˆ˚˜\u0300\u0301\u0303\u0304\u0308\u0309\u0323\u2002\u2009\u200b–—‘’‚“”„•…′″‹›⁄€™↑↓−\ufeff";
const AVANCO = {
  700: [
    237, 338, 552, 649, 655, 1016, 672, 339, 377, 377, 559, 679, 334, 468, 334, 388, 674, 431, 630, 646, 676,
    622, 649, 582, 651, 649, 334, 343, 679, 679, 679, 560, 1016, 747, 662, 740, 722, 607, 587, 750, 747, 281,
    584, 719, 565, 932, 762, 771, 648, 777, 657, 655, 667, 732, 747, 1038, 738, 731, 664, 377, 388, 377, 487,
    476, 365, 581, 630, 588, 630, 596, 398, 632, 623, 271, 271, 580, 271, 913, 623, 613, 630, 630, 407, 560,
    366, 623, 600, 850, 580, 602, 573, 469, 372, 469, 679, 237, 338, 588, 639, 762, 570, 339, 568, 623, 914,
    464, 660, 679, 662, 439, 459, 679, 460, 472, 365, 628, 599, 334, 364, 333, 490, 660, 846, 881, 920, 560,
    747, 747, 747, 747, 747, 747, 1022, 740, 607, 607, 607, 607, 281, 281, 281, 281, 760, 762, 771, 771, 771,
    771, 771, 679, 771, 732, 732, 732, 732, 731, 669, 657, 581, 581, 581, 581, 581, 581, 910, 588, 596, 596,
    596, 596, 271, 271, 271, 271, 599, 623, 613, 613, 613, 613, 613, 679, 613, 623, 623, 623, 623, 602, 630,
    602, 271, 1018, 988, 293, 311, 460, 365, 502, 0, 0, 0, 0, 0, 0, 288, 500, 157, 0, 500, 1000, 311, 311, 289,
    540, 532, 510, 474, 1002, 274, 547, 431, 431, 210, 685, 640, 905, 905, 679, 0
  ],
  800: [
    219, 358, 586, 655, 660, 1029, 683, 354, 382, 382, 583, 686, 353, 471, 353, 400, 692, 441, 638, 657, 688,
    634, 662, 588, 664, 662, 353, 360, 686, 686, 686, 579, 1036, 770, 665, 744, 723, 610, 585, 752, 749, 286,
    590, 738, 565, 943, 766, 773, 652, 782, 662, 660, 677, 727, 770, 1059, 761, 752, 679, 382, 400, 382, 493,
    484, 382, 588, 638, 595, 638, 601, 410, 639, 635, 283, 283, 593, 283, 927, 635, 619, 638, 638, 420, 573,
    382, 635, 615, 863, 594, 618, 581, 486, 388, 486, 686, 219, 358, 595, 650, 776, 579, 367, 568, 635, 914,
    468, 691, 686, 661, 423, 461, 686, 467, 482, 382, 646, 597, 353, 403, 345, 493, 691, 863, 895, 935, 579,
    770, 770, 770, 770, 770, 770, 1035, 744, 610, 610, 610, 610, 286, 286, 286, 286, 770, 766, 773, 773, 773,
    773, 773, 686, 773, 727, 727, 727, 727, 752, 683, 674, 588, 588, 588, 588, 588, 588, 907, 595, 601, 601,
    601, 601, 283, 283, 283, 283, 606, 635, 619, 619, 619, 619, 619, 686, 619, 635, 635, 635, 635, 618, 638,
    618, 283, 1023, 983, 304, 331, 479, 392, 501, 0, 0, 0, 0, 0, 0, 307, 500, 147, 0, 500, 1000, 331, 331, 308,
    581, 569, 546, 438, 1058, 295, 590, 450, 450, 218, 692, 652, 934, 934, 686, 0
  ],
  900: [
    199, 381, 625, 662, 666, 1044, 695, 372, 388, 388, 608, 693, 373, 475, 373, 412, 711, 452, 646, 669, 702,
    646, 675, 595, 679, 675, 373, 378, 693, 693, 693, 601, 1059, 795, 668, 748, 723, 613, 584, 754, 750, 291,
    596, 759, 565, 956, 770, 775, 656, 787, 668, 666, 687, 722, 795, 1082, 786, 775, 694, 388, 412, 388, 500,
    493, 401, 597, 646, 603, 646, 606, 422, 647, 649, 296, 296, 606, 296, 943, 649, 625, 646, 646, 434, 588,
    399, 649, 632, 877, 609, 636, 590, 505, 405, 505, 693, 199, 381, 603, 662, 793, 588, 397, 568, 649, 914,
    472, 726, 693, 659, 406, 463, 693, 475, 494, 401, 664, 596, 373, 446, 358, 496, 726, 883, 910, 952, 601,
    795, 795, 795, 795, 795, 795, 1047, 748, 613, 613, 613, 613, 291, 291, 291, 291, 781, 770, 775, 775, 775,
    775, 775, 693, 775, 722, 722, 722, 722, 775, 697, 692, 597, 597, 597, 597, 597, 597, 904, 603, 606, 606,
    606, 606, 296, 296, 296, 296, 613, 649, 625, 625, 625, 625, 625, 693, 625, 649, 649, 649, 649, 636, 646,
    636, 296, 1029, 978, 315, 353, 500, 422, 500, 0, 0, 0, 0, 0, 0, 327, 500, 137, 0, 500, 1000, 353, 353, 329,
    625, 610, 585, 398, 1119, 318, 637, 471, 471, 227, 700, 665, 966, 966, 693, 0
  ],
};

// ---------- largura ----------
const IDX = new Map([...CARACTERES].map((c, i) => [c, i]));
function larguraPalavra(w, peso, corpo) {
  let em = 0;
  for (const c of w) {
    const i = IDX.get(c);
    em += (i === undefined ? 620 : AVANCO[peso][i]) / 1000 + ESPACO; // caractere fora da tabela: um «o» largo
  }
  return em * corpo;
}
function pesoDe(cor) { return cor === "e" ? 900 : cor ? 800 : 700; }
function larguraGrupo(g, corpo) {
  let l = 0;
  g.forEach((p, k) => {
    l += larguraPalavra(p.w, pesoDe(p.cor), p.cor === "e" ? corpo * 1.2 : corpo);
    if (k < g.length - 1) l += larguraPalavra(" ", 700, corpo);
  });
  return l;
}
// corpo que cabe: 60, ou menor até 52; null quando nem a 52 cabe
function medir(g) {
  const l60 = larguraGrupo(g, CORPO);
  if (l60 <= LIMITE * FOLGA) return { fs: CORPO, px: l60 };
  const fs = Math.floor((CORPO * LIMITE * FOLGA) / l60);
  return fs >= CORPO_MIN ? { fs, px: larguraGrupo(g, fs) } : null;
}

// ---------- palavras ----------
const base = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^\p{L}\p{N}%$]+/gu, "").toLowerCase();
const limpa = (s) => s.replace(/^[^\p{L}\p{N}$]+|[^\p{L}\p{N}%]+$/gu, "");
const temDigito = (w) => /\d/.test(w);
const ehSigla = (w) => /^[\p{Lu}]{2,}$/u.test(limpa(w));
const UNIDADES = new Set(["mil", "milhao", "milhoes", "bilhao", "bilhoes", "trilhao", "trilhoes", "porcento"]);
const MOEDAS = new Set(["r$", "us$", "€", "£", "nº", "no."]);
// palavras que fecham mal uma linha. Artigo, demonstrativo e possessivo pedem a palavra seguinte («a intenção desse |
// vídeo»); preposição e conjunção, menos.
const PRESA = new Set(("a o as os um uma uns umas da do das dos na no nas nos ao aos à às pelo pela pelos pelas num " +
  "numa esse essa este esta desse dessa deste desta nesse nessa neste nesta seu sua seus suas meu minha meus minhas " +
  "teu tua teus tuas nosso nossa todo toda todos todas cada outro outra outros outras").split(" "));
const LIGA = new Set("de em e ou que se por pra para com sem nem mas como quando onde".split(" "));
// palavras que grudam no número seguinte: «quase 6 pontos», «mais de 10 milhões», «cerca de 300 mil»
const QUALIFICA = new Set("quase cerca uns umas até apenas só mais menos".split(" "));
const PONTUACAO = /[.,;:!?…]["'»”)\]]*$/;
const FIM_DE_FRASE = /[.!?…]["'»”)\]]*$/;

function lerPalavras(arq) {
  let bruto;
  try { bruto = JSON.parse(fs.readFileSync(arq, "utf8")); }
  catch (e) { sair(`não consegui ler ${arq}: ${e.message}`); }
  const lista = Array.isArray(bruto) ? bruto : bruto && (bruto.palavras || bruto.words);
  if (!Array.isArray(lista)) sair(`${arq} não é uma lista de palavras`);
  return lista.map((x, i) => {
    const w = x.w ?? x.palavra ?? x.text ?? x.word, ini = x.ini ?? x.start, fim = x.fim ?? x.end;
    if (typeof w !== "string" || !Number.isFinite(ini) || !Number.isFinite(fim)) {
      sair(`palavra ${i} sem w, ini e fim: ${JSON.stringify(x)}`);
    }
    return { i, w: w.normalize("NFC").trim(), ini, fim, cor: "" };
  });
}

function pintar(pal, o) {
  pal.forEach((p, k) => {
    const unidade = UNIDADES.has(base(p.w)) && k > 0 && temDigito(pal[k - 1].w);
    if (temDigito(p.w) || ehSigla(p.w) || unidade) p.cor = "n";
  });
  const marca = (nomes, cor) => {
    for (const nome of nomes) {
      const t = nome.split(/\s+/).map(base).filter(Boolean);
      if (!t.length) continue;
      for (let i = 0; i + t.length <= pal.length; i++) {
        if (t.every((x, k) => base(pal[i + k].w) === x)) for (let k = 0; k < t.length; k++) pal[i + k].cor = cor;
      }
    }
  };
  marca(o.n, "n"); marca(o.a, "a"); marca(o.b, "b"); marca(o.e, "e");
}

// pode haver troca de linha entre g[k] e g[k + 1]?
function podeCortar(g, k) {
  const p = g[k], q = g[k + 1], r = g[k + 2], o = g[k - 1];
  const num = (x) => x && temDigito(x.w);
  const pb = limpa(p.w).toLowerCase(), qb = limpa(q.w).toLowerCase();
  if (num(p) && !PONTUACAO.test(p.w)) return false;          // o número fica com a palavra seguinte
  if (MOEDAS.has(p.w.toLowerCase())) return false;           // R$ 18
  if (ehSigla(q.w) || q.cor === "e") return false;           // «o IBGE», «comente PALAVRA»
  if (num(q) && QUALIFICA.has(pb)) return false;             // «quase | 6» não
  if (num(q) && pb === "de" && o && QUALIFICA.has(limpa(o.w).toLowerCase())) return false; // «mais de | 10» não
  if (num(r) && qb === "de" && QUALIFICA.has(pb)) return false; // «mais | de 10» não
  return true;
}

// ---------- frases e grupos ----------
function frases(pal) {
  const out = [];
  let cur = [];
  pal.forEach((p, k) => {
    cur.push(p);
    const q = pal[k + 1];
    if (!q || PONTUACAO.test(p.w) || q.ini - p.fim >= PAUSA || q.i !== p.i + 1) { out.push(cur); cur = []; }
  });
  // palavra sozinha numa frase vai para a frase vizinha, sem passar por cima de pausa longa nem de trecho cortado
  for (let f = 0; f < out.length; f++) {
    if (out[f].length !== 1) continue;
    const p = out[f][0], prox = out[f + 1], ant = out[f - 1];
    const comProx = prox && prox[0].i === p.i + 1 && prox[0].ini - p.fim < PAUSA_LONGA && !FIM_DE_FRASE.test(p.w);
    const comAnt = ant && ant[ant.length - 1].i === p.i - 1 && p.ini - ant[ant.length - 1].fim < PAUSA_LONGA;
    if (comProx) { prox.unshift(p); out.splice(f--, 1); }
    else if (comAnt) { ant.push(p); out.splice(f--, 1); }
  }
  return out;
}

// divide uma frase em linhas de 2 a 4 palavras, equilibradas, sem cortar onde não pode e sem passar da largura
function dividir(fr, rigido) {
  const n = fr.length, melhor = [{ custo: 0, linhas: [] }];
  for (let fim = 1; fim <= n; fim++) {
    for (let tam = 1; tam <= Math.min(4, fim); tam++) {
      const ini = fim - tam;
      if (!melhor[ini]) continue;
      let custo = (tam - 3) ** 2;
      if (ini > 0 && !podeCortar(fr, ini - 1)) { if (rigido) continue; custo += 20; }
      const g = fr.slice(ini, fim), m = medir(g);
      if (!m && tam > 1) continue;
      if (tam === 1 && n > 1) custo += 8;
      custo += m ? (CORPO - m.fs) * 0.25 : 50;
      const ult = fr[fim - 1];
      const fecho = limpa(ult.w).toLowerCase();
      if (fim < n && !ult.cor) custo += PRESA.has(fecho) ? 6 : LIGA.has(fecho) ? 3 : 0; // linha terminando em «o», «de»
      const total = melhor[ini].custo + custo;
      if (!melhor[fim] || total < melhor[fim].custo) melhor[fim] = { custo: total, linhas: melhor[ini].linhas.concat([g]) };
    }
  }
  return melhor[n] ? melhor[n].linhas : null;
}

// até duas palavras coloridas por linha: CTA, depois os lados, depois os números
function limitarCores(g) {
  const ordem = { e: 0, a: 1, b: 1, n: 2 };
  const pintadas = g.filter((p) => p.cor).sort((x, y) => ordem[x.cor] - ordem[y.cor] || x.i - y.i);
  pintadas.slice(2).forEach((p) => { p.cor = ""; });
}

// ---------- programa ----------
function ajuda() { // o comentário do topo deste arquivo
  const linhas = [];
  for (const l of fs.readFileSync(__filename, "utf8").split("\n")) {
    if (!l.startsWith("//")) break;
    linhas.push(l.replace(/^\/\/ ?/, ""));
  }
  return linhas.join("\n");
}
function sair(msg) { console.error("legenda-grupos: " + msg); process.exit(1); }
const num = (v, k) => { const x = Number(v); if (!Number.isFinite(x)) sair(`${k} pede um número, veio «${v}»`); return x; };
const lista = (v) => v.split(",").map((s) => s.trim()).filter(Boolean);
function trecho(v) {
  const m = /^\s*([\d.]+)\s*-\s*([\d.]+)\s*$/.exec(v);
  if (!m) sair(`--sem pede trechos INI-FIM separados por vírgula, veio «${v}»`);
  return [Number(m[1]), Number(m[2])];
}
function opcoes(argv) {
  const o = { de: -Infinity, ate: Infinity, sem: [], a: [], b: [], e: [], n: [],
    palavras: "briefings/palavras-voz.json", saida: "assets/legenda-grupos.js" };
  for (let k = 0; k < argv.length; k++) {
    const chave = argv[k];
    if (chave === "--help" || chave === "-h") { console.log(ajuda()); process.exit(0); }
    if (k + 1 >= argv.length) sair(`falta o valor de ${chave}`);
    const v = argv[++k];
    if (chave === "--de") o.de = num(v, chave);
    else if (chave === "--ate") o.ate = num(v, chave);
    else if (chave === "--sem") o.sem.push(...v.split(",").map(trecho));
    else if (["--a", "--b", "--e", "--n"].includes(chave)) o[chave.slice(2)].push(...lista(v));
    else if (chave === "--palavras") o.palavras = v;
    else if (chave === "--saida") o.saida = v;
    else sair(`opção desconhecida: ${chave} (veja --help)`);
  }
  return o;
}
const f3 = (x) => +x.toFixed(3);
const virgula = (x, c = 2) => x.toFixed(c).replace(".", ",");

function main() {
  const o = opcoes(process.argv.slice(2));
  const arq = path.resolve(RAIZ, o.palavras), saida = path.resolve(RAIZ, o.saida);
  const todas = lerPalavras(arq);
  pintar(todas, o);
  const cortada = (p) => o.sem.some(([a, b]) => p.ini >= a && p.ini < b);
  const pal = todas.filter((p) => p.ini >= o.de && p.ini < o.ate && /[\p{L}\p{N}]/u.test(p.w) && !cortada(p));
  if (!pal.length) sair("nenhuma palavra no trecho pedido");

  const avisos = [], grupos = [];
  for (const fr of frases(pal)) {
    let linhas = dividir(fr, true);
    if (!linhas) {
      linhas = dividir(fr, false);
      avisos.push(`«${fr.map((p) => p.w).join(" ")}»: só deu para dividir cortando número, sigla ou CTA`);
    }
    if (!linhas) sair(`não consegui dividir «${fr.map((p) => p.w).join(" ")}»`);
    grupos.push(...linhas);
  }
  const out = grupos.map((g) => {
    limitarCores(g);
    const m = medir(g) || { fs: CORPO_MIN, px: larguraGrupo(g, CORPO_MIN) };
    const texto = g.map((p) => p.w).join(" ");
    if (g.length === 1) avisos.push(`«${texto}» ficou sozinha (pausa longa dos dois lados ou palavra larga)`);
    if (m.px > LIMITE) avisos.push(`«${texto}» passa de ${LIMITE} px mesmo a ${CORPO_MIN}: corte essa fala`);
    // fala seguinte fora do próximo grupo (trecho cortado): a legenda.html sai antes dela
    const ult = g[g.length - 1], prox = todas[ult.i + 1];
    const nx = prox && cortada(prox) ? prox.ini : undefined;
    return { g, fs: m.fs, px: m.px, texto, nx };
  });

  const linhasJs = out.map(({ g, fs: corpo, px, texto, nx }) => {
    const p = g.map((w) => `[${JSON.stringify(w.w)}, ${f3(w.ini)}, ${f3(w.fim)}, ${JSON.stringify(w.cor)}]`).join(", ");
    return `  { a: ${g[0].i}, b: ${g[g.length - 1].i}, fs: ${corpo},${nx !== undefined ? ` nx: ${f3(nx)},` : ""} p: [${p}] }, ` +
      `// ${texto} · ${Math.round(px)} px`;
  });
  const js = [
    "// Grupos da legenda, gerados pelo briefings/legenda-grupos.cjs a partir do " + o.palavras + ".",
    "// Narração nova (texto ou tempo): rode o script de novo (as opções estão no topo dele); edição à mão se perde.",
    "// a/b = índices da primeira e da última palavra no palavras-voz.json; fs = corpo da linha; nx = início da fala",
    "// seguinte quando ela ficou sem legenda; p = [palavra, ini, fim, cor], no tempo real (sem VOZ.w).",
    "// cor: \"\" branco 700 · \"a\" lado A 800 · \"b\" lado B 800 · \"n\" número ou sigla 800 · \"e\" palavra do CTA 900",
    "window.LEGENDA_GRUPOS = [",
    ...linhasJs,
    "];",
    "",
  ].join("\n");
  fs.mkdirSync(path.dirname(saida), { recursive: true });
  fs.writeFileSync(saida, js, "utf8");

  const corpos = {};
  out.forEach((x) => { corpos[x.fs] = (corpos[x.fs] || 0) + 1; });
  const tam = out.map((x) => x.g.length);
  console.log(out.map((x) => `${virgula(x.g[0].ini).padStart(7)}  ${x.texto}  (${x.fs} px · ${Math.round(x.px)} px)`).join("\n"));
  const faixa = Math.min(...tam) === Math.max(...tam) ? `${tam[0]}` : `${Math.min(...tam)} a ${Math.max(...tam)}`;
  console.log(`\n${out.length} linhas de ${faixa} palavras · corpo ` +
    Object.entries(corpos).sort((a, b) => b[0] - a[0]).map(([c, q]) => `${c}: ${q}`).join(", ") +
    ` · a primeira entra em ${virgula(Math.max(0, out[0].g[0].ini - 0.25))} s`);
  console.log(`gravado: ${path.relative(RAIZ, saida)}`);
  if (avisos.length) console.log("\navisos:\n" + avisos.map((a) => "- " + a).join("\n"));
}

main();
