#!/usr/bin/env node
// Instala as skills deste repo em ~/.claude/skills (copia, sobrescrevendo versões antigas).
import { cpSync, mkdirSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const src = join(dirname(fileURLToPath(import.meta.url)), "..", "skills");
const dest = join(homedir(), ".claude", "skills");

mkdirSync(dest, { recursive: true });

const PACOTES = { edicao: ["decupar", "inserir", "sonorizar", "minha-edicao"] };

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

const skills = [...new Set(pedidas)].map((name) => ({ name }));
for (const s of skills) {
  cpSync(join(src, s.name), join(dest, s.name), { recursive: true });
}

console.log("\n✅ Skills instaladas em ~/.claude/skills:\n");
for (const s of skills) console.log(`   /${s.name}`);
console.log("\nAbra o Claude Code em qualquer projeto e digite o nome da skill.");
console.log("Pra atualizar, rode o mesmo comando de novo.\n");
console.log("É importante manter sempre o Claude descomplicado. 🎯\n");
