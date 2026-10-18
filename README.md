# claude-skills

Skills do Claude Code prontas pra instalar. Cada pasta em [skills/](skills/) é uma skill completa — basta copiar pra `~/.claude/skills/` e ela passa a funcionar em qualquer projeto da sua máquina.

## Skills disponíveis

| Skill | O que faz |
|---|---|
| [`/decupar`](skills/decupar/SKILL.md) | **Chat 1 — decupagem e cor.** Transcreve no seu computador, tira partes gravadas de novo, vícios e pausas, aponta os começos fortes, deixa o vídeo em 9:16 e faz uma correção de cor leve. Entrega a prévia cortada, a legenda `.srt`, o XML para Premiere/DaVinci e o passo a passo do CapCut. Precisa de ffmpeg e uv. |
| [`/inserir`](skills/inserir/SKILL.md) | **Chat 2 — inserções e legenda.** Lê a fala decupada, propõe onde entra cada peça (cartão, número grande, print real da marca citada, vídeo atrás de você com recorte automático, tela dividida no gancho) e grava tudo com a legenda de 1 a 4 palavras no seu estilo, num render só. Precisa de ffmpeg e uv. |
| [`/docs-init`](skills/docs-init/SKILL.md) | Funda o modelo de documentação em 4 camadas num projeto novo ou existente: escaneia o repo, te entrevista (formato grilling) e cria `docs/` já preenchidos — ROADMAP, EXECUTION-LOG, DEBT, MODULES-STATUS, features/, `exports/specs/` e a seção no CLAUDE.md/AGENTS.md. |
| [`/minha-edicao`](skills/minha-edicao/SKILL.md) | Escreve a sua receita de edição de Reels como skill: uma por formato de conteúdo (dica rápida, react, bastidor, antes e depois) ou por estilo (legenda, cortes, ritmo, letterings, cor, som). Mede o seu Reel de referência, pergunta só o que falta e grava a skill nova em `~/.claude/skills/`. Exemplos prontos em `exemplos/`. |
| [`/sonorizar`](skills/sonorizar/SKILL.md) | **Chat 3 — som.** Trilha e efeitos sonoros para vídeo falado: lê a legenda, propõe o clima da trilha e poucos efeitos (cada um com motivo), mixa com a música abaixando sozinha quando você fala e entrega o vídeo no volume de publicação (-14 LUFS) com os créditos de cada som. Usa sons da sua pasta ou do Epidemic Sound. Precisa de ffmpeg e uv. |
| [`/primeiro-valor`](skills/primeiro-valor/SKILL.md) | Revisa ou desenha a primeira sessão de um app pelo olhar de quem nunca usou: onboarding, tela vazia, o que aparece depois da ação, progresso, recurso trancado e home com escolhas demais — devolve o que falta como itens de spec e as decisões que só você toma. |

## Instalação

Precisa do Node instalado — quem usa Claude Code já tem.

Todas as skills do repo de uma vez, em `~/.claude/skills`:

```bash
npx github:AosJunior/claude-skills
```

Só as skills da aula de edição de vídeo (decupar, inserir, sonorizar, minha-edicao):

```bash
npx github:AosJunior/claude-skills edicao
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

## Como usar o `/decupar`

1. Instale o ffmpeg e o uv. Mac: `brew install ffmpeg uv`. Windows: `winget install Gyan.FFmpeg astral-sh.uv`, depois feche e abra o Claude. Ou peça ao próprio Claude: "confere e instala o que falta para a /decupar".
2. Ponha o vídeo bruto numa pasta, abra o Claude Code e digite `/decupar` com o caminho do vídeo.
3. Confirme o mapa de cortes. Tudo sai em `decupagem/`, ao lado do vídeo; o bruto nunca é alterado.
4. Para corrigir, diga em texto o que mudar ("tira a frase X", "abre com o gancho 2"). Ele renderiza de novo sem transcrever de novo.

A primeira vez baixa o Whisper (cerca de 2 GB). Faça isso antes de precisar.

## Como usar o `/docs-init`

1. Abra o Claude Code na raiz do projeto (novo ou existente).
2. Digite `/docs-init`.
3. Ele escaneia o repo, faz as perguntas em rodadas (identidade, convenções, roadmap, dívidas) e cria toda a documentação preenchida com as suas respostas — nunca esqueletos vazios.

## Como usar o `/minha-edicao`

1. Abra o Claude Code (o app Desktop serve) e digite `/minha-edicao`.
2. Diga se quer uma receita de **formato** ou de **estilo** e, se tiver, arraste um Reel de referência e um vídeo seu já editado.
3. Responda as perguntas (no máximo 3 rodadas, cada uma com a recomendação dele). A skill nova aparece como `/<nome>` e entra sozinha nos próximos vídeos.
4. Depois de cada vídeo, diga o que você corrigiu na mão: ele atualiza a receita.

## Como usar o `/primeiro-valor`

Ele dispara sozinho quando o Claude está desenhando ou revisando onboarding, empty state, done state, progresso, recurso trancado ou uma home com escolhas demais — ou você chama pelo nome, `/primeiro-valor`, com a tela ou a spec em questão.

O que ele entrega:

1. Uma tabela dos estados da tela (antes do primeiro dado, sem dado por escolha, com erro, depois da ação, bloqueado, retorno…) classificada contra o catálogo de conceitos.
2. Itens de spec só para as lacunas — onde o padrão do conceito ainda falta naquele estado.
3. As decisões que só o dono do produto toma, com as opções e o custo de cada uma.

Nasceu de um produto real e generaliza para qualquer app que tenha uma primeira sessão.

---

*É importante manter sempre o Claude descomplicado.*
