// Rede para a faixa de baixo: acusa texto de cena abaixo de y 1430, onde ficam a legenda e a interface do Instagram.
// Uso (na raiz do projeto motion): node briefings/conferir-faixa.cjs
// Roda o check do HyperFrames com a faixa y 1430–1920 reservada e 99 amostras ao longo do vídeo (uma a cada 1 %).
// A legenda fica liberada pelo data-layout-allow-caption-zone do #lg-palco. Texto de cena na faixa sai como erro
// caption_zone_collision, com o seletor e os instantes. Só vê texto: barra, moldura e halo se conferem no snapshot.
const { spawnSync } = require("child_process");
const fs = require("fs"), path = require("path");
if (process.argv.includes("--help") || process.argv.includes("-h")) {
  console.log("Uso: node briefings/conferir-faixa.cjs  (na raiz do projeto motion; sai com o código do check)");
  process.exit(0);
}
const raiz = path.join(__dirname, "..");
// a mesma versão do HyperFrames do package.json do projeto
const pkg = JSON.parse(fs.readFileSync(path.join(raiz, "package.json"), "utf8"));
const versao = (/hyperframes@[\w.-]+/.exec((pkg.scripts || {}).check || "") || ["hyperframes"])[0];
const seek = Array.from({ length: 99 }, (_, i) => ((i + 1) / 100).toFixed(2)).join(",");
const faixa = `x0=0;y0=${(1430 / 1920).toFixed(4)};x1=1;y1=1;severity=error;seek=${seek}`;
const win = process.platform === "win32"; // no Windows o npx é um .cmd: precisa de shell e do argumento entre aspas
const r = spawnSync("npx", ["--yes", versao, "check", "--caption-zone", win ? `"${faixa}"` : faixa],
  { cwd: raiz, stdio: "inherit", shell: win });
process.exit(r.status === null ? 1 : r.status);
