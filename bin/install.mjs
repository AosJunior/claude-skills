#!/usr/bin/env node
// Instala as skills deste repo em ~/.claude/skills. Cada skill instalada substitui a pasta inteira
// (apaga e copia), para não sobrar arquivo que saiu do repo numa versão nova.
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const src = join(dirname(fileURLToPath(import.meta.url)), "..", "skills");
const dest = join(homedir(), ".claude", "skills");

mkdirSync(dest, { recursive: true });

const PACOTES = { edicao: ["decupar", "inserir", "sonorizar", "criticar", "minha-edicao"] };

const todas = readdirSync(src, { withFileTypes: true }).filter((e) => e.isDirectory());
const disponiveis = todas.map((e) => e.name);

// Argumentos: nome de pacote (ex.: edicao) ou nome(s) de skill. Sem argumento, instala todas.
const args = process.argv.slice(2);
const pedidas = args.length
  ? args.flatMap((a) => (PACOTES[a] ? PACOTES[a] : [a]))
  : disponiveis;

const invalidas = pedidas.filter((n) => !disponiveis.includes(n));
if (invalidas.length) {
  console.error(`\n❌ Não encontrei: ${invalidas.join(", ")}\n`);
  console.error(`Pacotes: ${Object.keys(PACOTES).join(", ")}`);
  console.error(`Skills: ${disponiveis.join(", ")}\n`);
  process.exit(1);
}

const skills = [...new Set(pedidas)];
const substituidas = [];
for (const nome of skills) {
  const alvo = join(dest, nome);
  if (existsSync(alvo)) {
    rmSync(alvo, { recursive: true, force: true });
    substituidas.push(nome);
  }
  cpSync(join(src, nome), alvo, { recursive: true });
}

console.log("\n✅ Skills instaladas em ~/.claude/skills:\n");
for (const nome of skills) console.log(`   /${nome}${substituidas.includes(nome) ? "  (substituída)" : ""}`);
if (substituidas.length) {
  console.log("\nA pasta de cada skill substituída foi apagada e copiada de novo: arquivo de versão antiga não fica.");
  console.log("O que você tinha guardado dentro dessas pastas saiu junto; a sua pasta de edição não é tocada.");
}
console.log("\nAbra o Claude Code em qualquer projeto e digite o nome da skill.");
console.log("Pra atualizar, rode o mesmo comando de novo.\n");
console.log("É importante manter sempre o Claude descomplicado. 🎯\n");
