// Converte tempos do código (os escritos nas cenas, do briefings/palavras-voz.json) para o tempo real do vídeo.
// Uso (na raiz do projeto motion): node briefings/tempo-real.cjs 12.4 15.7 …
// Imprime «código → real» por linha. Passe os reais ao --at do snapshot e ao data-start das janelas do index.html.
// Com o assets/voz.js vazio (a narração é a mesma em que as cenas foram escritas), os dois são iguais.
const fs = require("fs"), path = require("path"), vm = require("vm");
const ctx = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "..", "assets", "voz.js"), "utf8"), ctx);
const args = process.argv.slice(2);
if (!args.length || args.includes("--help") || args.includes("-h")) {
  console.log("Uso: node briefings/tempo-real.cjs <tempo do código> [<tempo do código> …]");
  process.exit(args.length ? 0 : 1);
}
const ts = args.map(Number);
console.log(ts.map((t) => `${t} → ${ctx.window.VOZ.w(t).toFixed(3)}`).join("\n"));
