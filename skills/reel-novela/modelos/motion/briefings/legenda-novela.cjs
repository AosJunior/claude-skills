// Legenda da novela: o legenda-grupos.cjs sem as aspas « » (a fala da personagem já está no balão;
// as aspas na legenda viravam ruído). Lê o briefings/palavras-voz.json, grava briefings/palavras-legenda.json sem « » e
// chama o legenda-grupos.cjs com ele e com os flags que você passar (os mesmos do legenda-grupos.cjs).
// Uso (na raiz do projeto motion): node briefings/legenda-novela.cjs --a "…" --sem …
const fs = require("fs"), path = require("path"), { spawnSync } = require("child_process");
const aqui = __dirname;
const pal = JSON.parse(fs.readFileSync(path.join(aqui, "palavras-voz.json"), "utf8"));
const limpo = pal.map((p) => Object.assign({}, p, { w: p.w.replace(/[«»]/g, "") })).filter((p) => p.w.trim());
const saida = path.join(aqui, "palavras-legenda.json");
fs.writeFileSync(saida, JSON.stringify(limpo, null, 1));
const r = spawnSync(process.execPath, [path.join(aqui, "legenda-grupos.cjs"), "--palavras", saida, ...process.argv.slice(2)],
  { cwd: path.join(aqui, ".."), stdio: "inherit" });
process.exit(r.status === null ? 1 : r.status);
