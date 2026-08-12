# INSTRUÇÃO DOCS — Regras de documentação (modelo de 4 camadas)

> Fonte única das regras de como documentar trabalho neste projeto. Fundado em {{DATA_FUNDACAO}} via skill docs-init. Ao mudar uma regra, date a mudança aqui neste cabeçalho.

---

## O modelo

A documentação do projeto vive em **4 camadas**. Cada fato pertence a UMA camada — se está em duas, a estrutura está errada.

| Camada | Pergunta que responde | Onde vive |
|---|---|---|
| 1 — Direção futura | "O que vem depois?" | [ROADMAP.md](ROADMAP.md) |
| 2 — O que aconteceu | "Como chegamos aqui?" | [EXECUTION-LOG.md](EXECUTION-LOG.md) |
| 3 — Estado por feature | "Como essa feature funciona hoje?" | [features/](features/) |
| 4 — Dívida e status | "O que está pendente / quebrado?" | [DEBT.md](DEBT.md), [MODULES-STATUS.md](MODULES-STATUS.md) |

**Princípio único:** cada fato em uma fonte só. Na dúvida "isso devia estar onde?", a resposta está no nome da camada que responde à pergunta que esse fato responde.

O `CLAUDE.md`/`AGENTS.md` do projeto **aponta, não duplica**: índice + regras de engajamento. Mudou um pattern arquitetural? Vai pra `features/X.md › Arquitetura`, não pro arquivo de memória.

---

## Fluxo entre camadas

- **DEBT → ROADMAP:** débito que sobe de prioridade vira item "Agora" ou "Próximo".
- **ROADMAP → EXECUTION-LOG:** item entregue sai do roadmap, ganha entrada no log.
- **Entrega → DEBT:** entrega que resolve débito baixa o item correspondente no DEBT.
- **EXECUTION-LOG → features:** mudança de comportamento observável atualiza o context file da feature (Resumo executivo + Decisões/Arquitetura).

---

## Antes de executar qualquer código

1. Leia `docs/features/[feature].md` da feature que será alterada.
2. Se o context file não existir, crie-o com o template abaixo (com **Resumo executivo** preenchido — obrigatório).
3. Consulte [DEBT.md](DEBT.md) pra ver se já há débito conhecido relacionado.

---

## Checklist de fim de sessão

Toda sessão de trabalho com impacto observável (UI, fluxo, schema, API, performance) termina com este checklist:

- [ ] **EXECUTION-LOG.md** ganhou entrada da sessão (template abaixo, **com a branch dos hashes nomeada** se não for main).
- [ ] **Cada feature tocada** tem context file atualizado: Resumo executivo (se mudou estado) + Decisões/Arquitetura (se virou padrão novo).
- [ ] **MODULES-STATUS.md** reflete mudança de status, se houve (regra de branch abaixo).
- [ ] **DEBT.md** ganhou débitos novos OU baixou débitos resolvidos.
- [ ] **ROADMAP.md** — item concluído saiu de "Agora" / "Próximo".

### Regra de branch (multi-branch)

- **"concluído" / "em produção" só vale pra código em main.** Pronto em branch = "em desenvolvimento (branch X)" ou "concluído (pendente deploy, branch X)".
- Entrada no EXECUTION-LOG com hash fora da main **nomeia a branch** ao lado do hash.
- Feature entregue em branch A que outra branch B referencia (rota, link, import) → registrar a dependência no ROADMAP "Agora" (é bloqueio de deploy, não débito passivo).

### Rótulos relativos banidos

Banido: "recém-lançado", "semana passada" e qualquer parente relativo — apodrecem sem ninguém notar. Usar sempre âncora absoluta: **"em YYYY-MM-DD"**.

---

## Template do context file (Camada 3)

```markdown
# [Nome da Feature]

**Status:** não iniciado | em desenvolvimento (branch X, se fora da main) | concluído | concluído (polido em YYYY-MM-DD)
**Módulo:** `/[rota ou path]`

> [1-2 linhas explicando o que essa feature é, alto nível]

---

## Resumo executivo

**O que existia antes:**
[1-3 linhas — estado anterior ao retrabalho/feature mais recente]

**Estado atual:**
[bullets do que existe hoje]

**O que esta feature toca (escopo):**
[1-2 linhas — tabelas/rotas/conceitos. Diferenciar de features adjacentes que confundem.]

**Em produção desde:** YYYY-MM-DD

**Destaques:**
- [bullet do que é único / técnica não-óbvia / decisão importante]

---

## Decisões de design
[Por que cada escolha foi feita. Alternativas descartadas com razão.]

## Lógica de negócio
[Schema/estruturas tocadas, regras de validação, fluxos de estado, APIs envolvidas.]

## Componentes
| Componente | Path | Responsabilidade |
|---|---|---|

## Arquitetura
[OBRIGATÓRIA — mesmo que vazia. Padrões estruturais que NÃO envelhecem.
 Onde não há nada pra documentar: `_a documentar_` (placeholder explícito).]

## Dependências
- [libs / tabelas / convenções externas de que a feature depende]

## TODOs
- [ ] pendente / [x] resolvido (com hash)
```

**NOTAS:**
- Sem `## Changelog` — duplica EXECUTION-LOG. Histórico se grep-a por feature no log.
- Sem `**Última atualização:**` no header — drift crônico. Status fica visível pelo git log.
- `## Arquitetura` é mandatória — verificável: `grep -L "^## Arquitetura" docs/features/*.md` retorna vazio.

---

## Critérios mínimos pra um context file útil

Um context file só serve se um agente novo (sem contexto prévio) puder responder estas **5 perguntas** só de ler o arquivo:

1. **O que existia antes?**
2. **O que mudou?** — escopo da entrega, em bullets.
3. **O que ESTA feature toca?** — limites; diferencia de features vizinhas que confundem.
4. **Quando entrou em produção?** — data clara, não só hashes.
5. **O que é único / vale destacar?**

A seção `## Resumo executivo` no topo é **a resposta dessas 5 perguntas**. É o primeiro lugar onde um agente vai olhar — mantenha sempre atualizada; o EXECUTION-LOG não cobre por ela (log é cronologia; Resumo é estado atual).

---

## Template de entrada no EXECUTION-LOG (Camada 2)

```markdown
## YYYY-MM-DD — [Descrição curta da sessão]

**Feature:** [nome do módulo]
**Escopo:** [1 linha — o que esta sessão entregou]

**Problema:** [opcional, mas recomendado pra mudanças não-triviais — qual dor motivou]

**O que foi feito:**
- [item 1]
- [item 2]

**Validação:** [como foi testado — manual? typecheck? build?]

**Arquivos criados:** [lista, ou "nenhum"]
**Arquivos modificados:** [lista]
**Hashes:** `[hash1]`, `[hash2]` (nomear a branch se fora da main)
```

---

## Quando criar o quê

- **Entrada no EXECUTION-LOG:** o que aconteceu nesta sessão — cobertura completa do trabalho.
- **Item no ROADMAP:** trabalho futuro decidido (não débito passivo — esse fica no DEBT).
- **Item no DEBT:** workaround, bug aceito, deprecation pendente, dívida P0/P1/P2/P3.
- **Pasta de SPEC/pesquisa (`exports/specs/`):** ciclo de specs de uma iniciativa — SEMPRE lá (gitignored), nunca em `docs/`. Nomenclatura na seção abaixo.

---

## Nomenclatura de `exports/specs/`

Toda iniciativa de SPEC/pesquisa nasce em `exports/specs/` seguindo este padrão — sem exceção:

### Pasta: `YY-MM-DD-escopo`

- **Data = dia do kickoff** (quando a pasta nasce). Nunca muda — data de conclusão vai no `STATUS.md`, não no nome.
- **Ano→mês→dia** é obrigatório: é o que faz `ls` listar em ordem cronológica. Dia-primeiro quebra a ordenação.
- **Escopo:** kebab-case, minúsculas, até 3 palavras, sem enchimento. Ex.: `26-07-09-mobile-first-alunos`.
- Sem espaços no nome.

### Arquivos internos: sem prefixo `SPEC-`

A pasta já diz que aquilo é spec — prefixo repetido não informa nada.

```
YY-MM-DD-exemplo-iniciativa/
  00.md            ← contexto/master
  A-tokens.md      ← uma spec por letra: A-<slug>.md, B-<slug>.md, ...
  B-sheet.md
  STATUS.md        ← estado do ciclo
  PESQUISA.md      RELATORIO.md      CHECKLIST.md      ← reservados, se houver
  mockups/  spike/  data/  backups/                    ← subpastas padronizadas
```

### Gramática do slug (4 regras)

1. **Nunca repita o que a pasta já diz.** Dentro de `26-07-09-mobile-first-alunos`, é `G-roteiros.md`, não `G-roteiros-mobile.md`.
2. **Slug = substantivo da superfície alterada.** Verbo só quando a ação É a entrega (ex.: `B-delete-sprints.md`).
3. **Máx. 2 palavras**, minúsculas, kebab-case. Se 1 palavra desambigua dentro da pasta, use 1.
4. **Nomes reservados fixos:** `00.md`, `STATUS.md`, `PESQUISA.md`, `RELATORIO.md`, `CHECKLIST.md`. Sufixo de tema só quando há dois do mesmo tipo (`RELATORIO-custos.md`).

### STATUS.md

Primeira linha sempre: `Estado: rascunho | em execução | concluído (YYYY-MM-DD) | descontinuado (YYYY-MM-DD)`. É onde o ciclo de vida fica registrado — a pasta nunca é renomeada nem movida ao fechar.

---

## Rigor por tipo de mudança

| Mudança | Atualizar? |
|---|---|
| Bug fix sem mudança visível | só EXECUTION-LOG |
| Refactor interno (sem mudança API/UI) | só EXECUTION-LOG |
| Nova feature / retrabalho com impacto visual ou funcional | **Resumo executivo** + Decisões + Componentes + EXECUTION-LOG |
| Mudança de schema/dados | Resumo + Lógica de negócio + Dependências + EXECUTION-LOG |
| Performance | EXECUTION-LOG (com métricas antes/depois) + Arquitetura da feature se virou padrão |
| Dívida técnica criada / resolvida | **DEBT.md** + EXECUTION-LOG |
| Status do módulo mudou | **MODULES-STATUS.md** + Resumo executivo |
| Item de roadmap entregue | ROADMAP.md (remover) + EXECUTION-LOG + outros conforme o tipo |
| Decisão arquitetural cross-feature | Arquitetura da(s) feature(s) afetada(s) + EXECUTION-LOG |

---

## Onde NÃO documentar

- **No CLAUDE.md/AGENTS.md:** apenas índice + regras de engajamento. Ele aponta, não duplica.
- **Em comentários no código:** o WHY que sobrevive ao próximo dev vai no context file da feature. Comentários no código são pra invariantes locais e workarounds não-óbvios.
- **Em commit messages como única fonte:** commit message complementa o EXECUTION-LOG; não substitui.
