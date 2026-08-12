---
name: docs-init
description: Funda o modelo de documentação em 4 camadas num projeto novo ou existente — entrevista o usuário e cria os docs já preenchidos.
disable-model-invocation: true
---

# docs-init

Funda o modelo de documentação em 4 camadas no projeto atual. A saída são docs **preenchidos com fatos reais** — nunca esqueletos vazios pra preencher depois. Tudo em pt-BR, datas sempre absolutas (`YYYY-MM-DD`).

## 1. Escanear antes de perguntar

Fatos são trabalho seu, nunca do usuário. Levante do repo:

- **Stack e convenções detectáveis** — `package.json` (ou equivalente), configs, estrutura de pastas, lockfile.
- **Arquivo de memória existente** — o projeto usa `CLAUDE.md` ou `AGENTS.md`? A seção de docs vai no que existir; se nenhum existe, será criado `CLAUDE.md`.
- **Código existente** — módulos/rotas/features identificáveis. Vira proposta de lista pra `docs/features/` e pro `MODULES-STATUS.md`.
- **`git log`** — matéria-prima da primeira entrada do `EXECUTION-LOG.md` num projeto existente.
- **Docs que já existem** — se há documentação prévia, mapear o que ela cobre pra migrar/apontar, não duplicar.

## 2. Entrevistar (formato /grilling)

Rode a entrevista em rodadas de frontier: perguntas numeradas, cada uma com a sua recomendação, espere as respostas antes da próxima rodada. Pauta mínima:

1. **Identidade** — o que é o projeto, pra quem, qual promessa.
2. **Convenções que o scan não revela** — decisões de arquitetura, regras não escritas, o que é proibido e por quê.
3. **Roadmap** — o que é "Agora", o que é "Próximo".
4. **Dívidas e riscos** já conhecidos no dia zero.

O que o scan já respondeu não vira pergunta — vira afirmação a confirmar ("detectei Next.js 16 + Supabase; confirma?").

## 3. Materializar

Criar, preenchendo com as respostas da entrevista e os achados do scan:

- `docs/INSTRUCAO_DOCS.md` — copiar de [templates/INSTRUCAO_DOCS.md](templates/INSTRUCAO_DOCS.md). É a fonte única das regras de documentação dentro do projeto; a partir daqui ela evolui com o projeto, datando cada mudança no cabeçalho.
- `docs/ROADMAP.md` — seções Agora / Próximo / Depois, preenchidas, com linha `Última revisão: YYYY-MM-DD`.
- `docs/EXECUTION-LOG.md` — primeira entrada é a própria fundação dos docs (template no INSTRUCAO_DOCS); em projeto existente, uma segunda entrada resume o histórico do git até aqui.
- `docs/DEBT.md` — dívidas declaradas na entrevista, com prioridade (P0–P3); se nenhuma, registrar "Sem débitos registrados em YYYY-MM-DD".
- `docs/MODULES-STATUS.md` — tabela dos módulos detectados no scan com status confirmado na entrevista.
- `docs/features/<modulo>.md` — **só** para módulos que já existem no código, com `## Resumo executivo` preenchido (template e critérios no INSTRUCAO_DOCS).
- `exports/specs/` criada + `exports/` no `.gitignore` (specs de iniciativa vivem lá, fora do git — nomenclatura no INSTRUCAO_DOCS).
- Seção **"Documentação — modelo de 4 camadas"** no `CLAUDE.md`/`AGENTS.md` do passo 1: a tabela das 4 camadas + ponteiro pro `INSTRUCAO_DOCS.md`. O arquivo de memória **aponta, não duplica** — regra nenhuma é copiada pra lá.

Se o projeto já tem stack/framework bem definido, as regras de engajamento correspondentes (comandos de build/test/lint, convenções detectadas e confirmadas) entram no `CLAUDE.md`/`AGENTS.md` na mesma passada.

## 4. Conferir

- Todo link interno entre os arquivos criados resolve.
- Nenhuma data relativa ("recente", "semana passada") — só âncora absoluta `YYYY-MM-DD`.
- Cada `docs/features/*.md` criado responde as 5 perguntas do Resumo executivo (lista no INSTRUCAO_DOCS) pra um leitor sem contexto prévio.
- Terminar mostrando ao usuário a árvore criada e o diff da seção adicionada ao `CLAUDE.md`/`AGENTS.md`.
