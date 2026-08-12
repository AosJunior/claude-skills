# claude-skills

Skills do Claude Code prontas pra instalar. Cada pasta em [skills/](skills/) é uma skill completa — basta copiar pra `~/.claude/skills/` e ela passa a funcionar em qualquer projeto da sua máquina.

## Skills disponíveis

| Skill | O que faz |
|---|---|
| [`/docs-init`](skills/docs-init/SKILL.md) | Funda o modelo de documentação em 4 camadas num projeto novo ou existente: escaneia o repo, te entrevista (formato grilling) e cria `docs/` já preenchidos — ROADMAP, EXECUTION-LOG, DEBT, MODULES-STATUS, features/, `exports/specs/` e a seção no CLAUDE.md/AGENTS.md. |

## Instalação

Um comando só:

```bash
git clone https://github.com/AosJunior/claude-skills.git /tmp/claude-skills && mkdir -p ~/.claude/skills && cp -R /tmp/claude-skills/skills/* ~/.claude/skills/ && rm -rf /tmp/claude-skills
```

Depois é só abrir o Claude Code em qualquer projeto e digitar `/docs-init`.

Pra atualizar no futuro, rode o mesmo comando de novo.

## Como usar o `/docs-init`

1. Abra o Claude Code na raiz do projeto (novo ou existente).
2. Digite `/docs-init`.
3. Ele escaneia o repo, faz as perguntas em rodadas (identidade, convenções, roadmap, dívidas) e cria toda a documentação preenchida com as suas respostas — nunca esqueletos vazios.

---

*É importante manter sempre o Claude descomplicado.*
