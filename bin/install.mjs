#!/usr/bin/env node
// Instala as skills deste repo em ~/.claude/skills (copia, sobrescrevendo versões antigas).
import { cpSync, mkdirSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const src = join(dirname(fileURLToPath(import.meta.url)), "..", "skills");
const dest = join(homedir(), ".claude", "skills");

mkdirSync(dest, { recursive: true });

const skills = readdirSync(src, { withFileTypes: true }).filter((e) => e.isDirectory());
for (const s of skills) {
  cpSync(join(src, s.name), join(dest, s.name), { recursive: true });
}

console.log("\n✅ Skills instaladas em ~/.claude/skills:\n");
for (const s of skills) console.log(`   /${s.name}`);
console.log("\nAbra o Claude Code em qualquer projeto e digite o nome da skill.");
console.log("Pra atualizar, rode o mesmo comando de novo.\n");
console.log("É importante manter sempre o Claude descomplicado. 🎯\n");
