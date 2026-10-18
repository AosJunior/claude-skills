# claude-skills

Skills do Claude Code prontas pra instalar. Cada pasta em [skills/](skills/) é uma skill completa — basta copiar pra `~/.claude/skills/` e ela passa a funcionar em qualquer projeto da sua máquina.

## Skills disponíveis

| Skill | O que faz |
|---|---|
| [`/decupar`](skills/decupar/SKILL.md) | **Chat 1 — corte e cor.** Transcreve no seu computador, tira partes gravadas de novo, vícios e pausas, aponta os começos fortes e deixa o vídeo em 9:16. No v2: acelera a fala (ex.: 1,2×), alterna o zoom em níveis fixos a cada corte, aplica a sua cor por LUT (copiada do seu CapCut) e grava o tempo de cada palavra para as outras skills se prenderem à fala. Entrega o vídeo cortado, a legenda `.srt`, o XML para Premiere/DaVinci e o passo a passo do CapCut. Precisa de ffmpeg e uv. |
| [`/inserir`](skills/inserir/SKILL.md) | **Chat 2 — legenda e camadas.** Lê a fala decupada, propõe as inserções e grava tudo no vídeo. No v2: legenda de 1 palavra com o destaque subindo em outra fonte, tela dividida no gancho (headline na emenda, laterais borradas), camadas de vídeo, imagem, faixa e lettering atrás de você (com máscara), na frente ou na metade de cima, cada uma presa a uma palavra da fala. Precisa de ffmpeg e uv. |
| [`/sonorizar`](skills/sonorizar/SKILL.md) | **Chat 3 — som e entrega.** Trilha e efeitos sonoros para vídeo falado: propõe o clima, poucos efeitos (cada um com motivo) e mixa com a música abaixando sozinha quando você fala, em -14 LUFS, com os créditos de cada som. No v2: duas trilhas com troca na virada de bloco, efeitos presos às camadas, identificação das músicas dos seus Reels (Shazam) e a pasta `entrega/` pronta. Usa sons da sua pasta ou do Epidemic Sound. Precisa de ffmpeg e uv. |
| [`/criticar`](skills/criticar/SKILL.md) | **Chat 4 — crítica.** Mede o vídeo pronto (emendas, gagueira, quadros soltos, zona segura, posições repetidas, tempo sem nada acontecer, legenda, volume) e um editor-chefe compara com a sua referência. Cada item sai como passa ou reprova, com a medida e o tempo, e volta para a skill que corrige. Precisa de ffmpeg e uv. |
| [`/minha-edicao`](skills/minha-edicao/SKILL.md) | Escreve o seu jeito de editar a partir dos seus Reels: o **estilo** (legenda, zoom, cor por LUT, letterings, tela dividida, trilha) em `marca/estilo.md`, que as 4 skills acima leem, e uma skill por **formato** (blocos, gancho e a composição de cada bloco em px). Mede o Reel de referência, pergunta só o que é decisão sua e mostra a receita no seu vídeo antes de gravar. Exemplos prontos em `exemplos/`. |
| [`/docs-init`](skills/docs-init/SKILL.md) | Funda o modelo de documentação em 4 camadas num projeto novo ou existente: escaneia o repo, te entrevista (formato grilling) e cria `docs/` já preenchidos — ROADMAP, EXECUTION-LOG, DEBT, MODULES-STATUS, features/, `exports/specs/` e a seção no CLAUDE.md/AGENTS.md. |
| [`/primeiro-valor`](skills/primeiro-valor/SKILL.md) | Revisa ou desenha a primeira sessão de um app pelo olhar de quem nunca usou: onboarding, tela vazia, o que aparece depois da ação, progresso, recurso trancado e home com escolhas demais — devolve o que falta como itens de spec e as decisões que só você toma. |

## Instalação

Precisa do Node instalado — quem usa Claude Code já tem.

Todas as skills do repo de uma vez, em `~/.claude/skills`:

```bash
npx github:AosJunior/claude-skills
```

Só as skills do kit de edição de vídeo (decupar, inserir, sonorizar, criticar, minha-edicao):

```bash
npx github:AosJunior/claude-skills edicao
```

Só uma skill, pela CLI `skills` (escopo global):

```bash
npx skills add https://github.com/AosJunior/claude-skills --skill primeiro-valor -g
```

Depois é só abrir o Claude Code em qualquer projeto: cada skill instalada responde pelo nome (`/docs-init`, `/primeiro-valor`).

Pra atualizar no futuro, rode o mesmo comando de novo — o npx sempre baixa o estado atual do repo. O instalador apaga a pasta de cada skill que ele instala e copia de novo, para não sobrar arquivo de versão antiga (o que você guardou dentro dessas pastas some junto; a sua pasta de edição não é tocada):

```bash
npx github:AosJunior/claude-skills
```

<details>
<summary>Alternativa sem npx (git puro)</summary>

```bash
git clone https://github.com/AosJunior/claude-skills.git /tmp/claude-skills && mkdir -p ~/.claude/skills && cp -R /tmp/claude-skills/skills/* ~/.claude/skills/ && rm -rf /tmp/claude-skills
```

</details>

## Kit de edição: a pasta de edição

As skills de edição trabalham numa **pasta de edição**: uma pasta sua, com qualquer nome, onde moram a sua
marca e os seus vídeos. Elas não importam código umas das outras; se falam pelos arquivos dessa pasta
(formato em [docs/edicao-contrato.md](docs/edicao-contrato.md)).

```
<pasta de edição>/
  marca/
    estilo.md                      o seu jeito de editar (a /minha-edicao escreve)
    fontes/  cor/<nome>.cube  sons/{trilhas,efeitos}/ + sons/creditos.md  referencias/  letterings/
  videos/<AAAA-MM-DD-assunto>/
    bruto.<ext>                    só leitura
    brutos/{imagens,videos}/ + brutos/fontes.md   mídia de terceiros com a origem anotada
    decupagem/   insercoes/   som/   critica/   entrega/
```

Cada skill acha a marca subindo a partir da pasta do vídeo até encontrar `marca/estilo.md`.

## Como usar o kit de edição

1. Instale o ffmpeg e o uv. Mac: `brew install ffmpeg uv`. Windows: `winget install Gyan.FFmpeg astral-sh.uv`, depois feche e abra o Claude. Ou peça ao próprio Claude: "confere e instala o que falta para a /decupar".
2. Uma vez: abra o Claude Code na sua pasta de edição, digite `/minha-edicao` e mande um Reel seu aprovado. Ele grava o `marca/estilo.md`.
3. A cada vídeo: ponha o bruto em `videos/<data>-<assunto>/` e peça, em ordem, `/decupar`, `/inserir`, `/sonorizar` e `/criticar` (ou a skill do seu formato, que chama as 4). O bruto nunca é alterado.
4. Para corrigir, diga em texto o que mudar ("tira a frase X", "o número entra na palavra milhões"). Ele refaz só dali para frente.

A primeira vez baixa o Whisper (cerca de 2 GB). Faça isso antes de precisar.

## Como usar o `/docs-init`

1. Abra o Claude Code na raiz do projeto (novo ou existente).
2. Digite `/docs-init`.
3. Ele escaneia o repo, faz as perguntas em rodadas (identidade, convenções, roadmap, dívidas) e cria toda a documentação preenchida com as suas respostas — nunca esqueletos vazios.

## Como usar o `/minha-edicao`

1. Abra o Claude Code (o app Desktop serve) na sua pasta de edição e digite `/minha-edicao`.
2. Diga se quer gravar o seu **estilo** ou um **formato** e arraste um Reel de referência e um vídeo seu aprovado. Para copiar a sua cor, mande também um bruto e o mesmo vídeo exportado do seu editor.
3. Responda as perguntas (no máximo 3 rodadas, só o que é decisão sua) e confira a prova: um quadro por bloco, com o seu vídeo ao lado da referência.
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
