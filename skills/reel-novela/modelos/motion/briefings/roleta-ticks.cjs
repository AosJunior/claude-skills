// Eventos de som de todas as roletas registradas em assets/roletas.js, já no tempo real do vídeo (assets/voz.js).
// Uso (na raiz do projeto motion): node briefings/roleta-ticks.cjs [--travas] [nome …]
//   sem nome  = todas as roletas registradas; com nomes = só essas
//   --travas  = só as travas e a última (para escolher os tempos do snapshot)
// Saída (stdout): JSON, uma lista em ordem de tempo de { roleta, t, tipo, digito }.
//   t       segundos no tempo real do vídeo, 3 casas
//   tipo    "tique" = troca de dígito que não trava; "trava" = o dígito travou; "ultima" = a última trava do número
//           (vem junto, no mesmo instante, da "trava" do último dígito)
//   digito  posição no número (0 = o da esquerda, sem contar os pontos)
// stderr: contagem por roleta. Uma roleta com configuração quebrada vai para o stderr e as outras saem mesmo assim
// (código de saída 2).
// A agenda é a mesma que a tela desenha: os instantes da configuração passam pelo VOZ.w com o mesmo arredondamento do
// a() das cenas, e a física do giro corre em segundos reais entre eles.
const fs = require("fs"), path = require("path"), vm = require("vm");
const ctx = { window: {} };
vm.createContext(ctx);
for (const f of ["voz.js", "roleta.js", "roletas.js"]) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "assets", f), "utf8"), ctx, { filename: f });
}
const { VOZ, ROLETA, ROLETAS } = ctx.window;
const real = (t) => +VOZ.w(t).toFixed(3);
const args = process.argv.slice(2);
if (args.includes("--help") || args.includes("-h")) {
  console.log("Uso: node briefings/roleta-ticks.cjs [--travas] [nome …]  (JSON no stdout, contagem no stderr)");
  process.exit(0);
}
const soTravas = args.includes("--travas");
const pedidos = args.filter((x) => !x.startsWith("--"));
const nomes = pedidos.length ? pedidos : Object.keys(ROLETAS);
const eventos = [];
let falhou = false;
for (const nome of nomes) {
  if (!ROLETAS[nome]) { console.error(`roleta «${nome}» não existe em assets/roletas.js`); falhou = true; continue; }
  let ev;
  try { ev = ROLETA.tiques(ROLETAS[nome], real); }
  catch (e) { console.error(`roleta «${nome}» com configuração quebrada: ${e.message}`); falhou = true; continue; }
  const conta = { tique: 0, trava: 0, ultima: 0 };
  for (const e of ev) {
    conta[e.tipo]++;
    if (!soTravas || e.tipo !== "tique") eventos.push({ roleta: nome, ...e });
  }
  console.error(`${nome}: ${conta.tique} tiques, ${conta.trava} travas, ${conta.ultima} última · ${ev[0].t}–${ev[ev.length - 1].t} s`);
}
eventos.sort((x, y) => x.t - y.t);
console.log(JSON.stringify(eventos, null, 1));
if (falhou) process.exitCode = 2;
