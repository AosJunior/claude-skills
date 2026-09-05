# claude-skills

Skills do Claude Code prontas pra instalar. Cada pasta em [skills/](skills/) é uma skill completa — basta copiar pra `~/.claude/skills/` e ela passa a funcionar em qualquer projeto da sua máquina.

## Skills disponíveis

| Skill | O que faz |
|---|---|
| [`/docs-init`](skills/docs-init/SKILL.md) | Funda o modelo de documentação em 4 camadas num projeto novo ou existente: escaneia o repo, te entrevista (formato grilling) e cria `docs/` já preenchidos — ROADMAP, EXECUTION-LOG, DEBT, MODULES-STATUS, features/, `exports/specs/` e a seção no CLAUDE.md/AGENTS.md. |
| [`/primeiro-valor`](skills/primeiro-valor/SKILL.md) | Revisa ou desenha a primeira sessão de um app pelo olhar de quem nunca usou: onboarding, tela vazia, o que aparece depois da ação, progresso, recurso trancado e home com escolhas demais — devolve o que falta como itens de spec e as decisões que só você toma. |

## Instalação

Precisa do Node instalado — quem usa Claude Code já tem.

Todas as skills do repo de uma vez, em `~/.claude/skills`:

```bash
npx github:AosJunior/claude-skills
```

Só uma skill, pela CLI `skills` (escopo global):

```bash
npx skills add https://github.com/AosJunior/claude-skills --skill primeiro-valor -g
```

Depois é só abrir o Claude Code em qualquer projeto: cada skill instalada responde pelo nome (`/docs-init`, `/primeiro-valor`).

Pra atualizar no futuro, rode o mesmo comando de novo com `@latest` implícito — o npx sempre baixa o estado atual do repo:

```bash
npx github:AosJunior/claude-skills
```

<details>
<summary>Alternativa sem npx (git puro)</summary>

```bash
git clone https://github.com/AosJunior/claude-skills.git /tmp/claude-skills && mkdir -p ~/.claude/skills && cp -R /tmp/claude-skills/skills/* ~/.claude/skills/ && rm -rf /tmp/claude-skills
```

</details>

## Como usar o `/docs-init`

1. Abra o Claude Code na raiz do projeto (novo ou existente).
2. Digite `/docs-init`.
3. Ele escaneia o repo, faz as perguntas em rodadas (identidade, convenções, roadmap, dívidas) e cria toda a documentação preenchida com as suas respostas — nunca esqueletos vazios.

## Como usar o `/primeiro-valor`

Ele dispara sozinho quando o Claude está desenhando ou revisando onboarding, empty state, done state, progresso, recurso trancado ou uma home com escolhas demais — ou você chama pelo nome, `/primeiro-valor`, com a tela ou a spec em questão.

O que ele entrega:

1. Uma tabela dos estados da tela (antes do primeiro dado, sem dado por escolha, com erro, depois da ação, bloqueado, retorno…) classificada contra o catálogo de conceitos.
2. Itens de spec só para as lacunas — onde o padrão do conceito ainda falta naquele estado.
3. As decisões que só o dono do produto toma, com as opções e o custo de cada uma.

Nasceu de um produto real e generaliza para qualquer app que tenha uma primeira sessão.

---

*É importante manter sempre o Claude descomplicado.*
