# claude-skills

Skills do Claude Code prontas pra instalar. Cada pasta em [skills/](skills/) é uma skill completa — basta copiar pra `~/.claude/skills/` e ela passa a funcionar em qualquer projeto da sua máquina.

## Skills disponíveis

| Skill | O que faz |
|---|---|
| [`/decupar`](skills/decupar/SKILL.md) | **Chat 1 — corte e cor.** Transcreve no seu computador, tira partes gravadas de novo, vícios e pausas, aponta os começos fortes e deixa o vídeo em 9:16. No v2: acelera a fala (ex.: 1,2×), alterna o zoom em níveis fixos a cada corte, aplica a sua cor por LUT (copiada do seu CapCut) e grava o tempo de cada palavra para as outras skills se prenderem à fala. Entrega o vídeo cortado, a legenda `.srt`, o XML para Premiere/DaVinci e o passo a passo do CapCut. Precisa de ffmpeg e uv. |
| [`/inserir`](skills/inserir/SKILL.md) | **Chat 2 — legenda e camadas.** Lê a fala decupada, propõe as inserções e grava tudo no vídeo. No v2: legenda de 1 palavra com o destaque subindo em outra fonte, tela dividida no gancho (headline na emenda, laterais borradas), camadas de vídeo, imagem, faixa e lettering atrás de você (com máscara), na frente ou na metade de cima, cada uma presa a uma palavra da fala. Com pedido de animação no estilo Apple ou de vídeo só com a voz, faz o motion em HyperFrames + GSAP (o rosto em janela ou só a voz), com o tempo de cada palavra por alinhamento forçado. Na animação, a versão do HyperFrames fica fixa (0.9.26): ele testa a sua máquina antes da primeira animação, refaz só o trecho que mudou em vez de renderizar o vídeo todo e volta o projeto de animação a um ponto anterior quando uma mudança dá errado (isso vale para os arquivos da pasta da animação, não para o mapa de inserções). Precisa de ffmpeg e uv (e Node 22 ou mais para o motion). |
| [`/sonorizar`](skills/sonorizar/SKILL.md) | **Chat 3 — som e entrega.** Trilha e efeitos sonoros para vídeo falado: propõe o clima, poucos efeitos (cada um com motivo) e mixa com a música abaixando sozinha quando você fala, em -14 LUFS, com os créditos de cada som. No v2: duas trilhas com troca na virada de bloco, efeitos presos às camadas, identificação das músicas dos seus Reels (Shazam) e a pasta `entrega/` pronta. Também acha o áudio em alta no trecho que os Reels usam e põe a roleta curta só no número principal. Usa sons da sua pasta ou do Epidemic Sound. Precisa de ffmpeg e uv. |
| [`/criticar`](skills/criticar/SKILL.md) | **Chat 4 — crítica.** Mede o vídeo pronto (emendas, gagueira, quadros soltos, zona segura, posições repetidas, tempo sem nada acontecer, legenda, volume) e um editor-chefe compara com a sua referência. Cada item sai como passa ou reprova, com a medida e o tempo, e volta para a skill que corrige. Precisa de ffmpeg e uv. |
| [`/reel-novela`](skills/reel-novela/SKILL.md) | **Anúncio ou Reel em episódios, sem gravar.** Uma personagem de ficção em pixel art tem um problema com prazo, um relógio e um medidor de jogo ficam no topo, um trecho real do seu vídeo ou aula é a virada, e o episódio termina em duas opções de uma palavra («Comenta uma palavra»). A skill conduz a bíblia da série, o elenco e os cenários, o roteiro na grade de batidas, a narração por IA com o tempo de cada palavra, as cenas em HyperFrames + GSAP, o som e a entrega. Roda sozinha, sem as outras skills. Precisa de ffmpeg, uv, Node 22 ou mais, uma chave do ElevenLabs e um gerador de imagem; trilha e efeitos vêm da sua pasta ou do Epidemic Sound. |
| [`/minha-edicao`](skills/minha-edicao/SKILL.md) | Escreve o seu jeito de editar a partir dos seus Reels: o **estilo** (legenda, zoom, cor por LUT, letterings, tela dividida, trilha) em `marca/estilo.md`, que as 4 skills acima leem, e uma skill por **formato** (blocos, gancho e a composição de cada bloco em px). Mede o Reel de referência, pergunta só o que é decisão sua e mostra a receita no seu vídeo antes de gravar. Quem gravou o estilo na aula de 17/10 roda uma vez e ele **importa** a receita antiga para o `marca/estilo.md`. Exemplos prontos em `exemplos/`. |
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

Só a do anúncio em episódios (`/reel-novela`):

```bash
npx github:AosJunior/claude-skills reel-novela
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

O que cada comando instala:

| Comando | Instala |
|---|---|
| `npx github:AosJunior/claude-skills` (sem nada depois) | **todas** as skills do repositório |
| `npx github:AosJunior/claude-skills edicao` | só as cinco do kit de edição: `/decupar`, `/inserir`, `/sonorizar`, `/criticar` e `/minha-edicao` |
| `npx github:AosJunior/claude-skills reel-novela` (ou o nome de qualquer outra skill) | só essa |

<details>
<summary>Alternativa sem npx (git puro)</summary>

```bash
git clone https://github.com/AosJunior/claude-skills.git /tmp/claude-skills && mkdir -p ~/.claude/skills && cp -R /tmp/claude-skills/skills/* ~/.claude/skills/ && rm -rf /tmp/claude-skills
```

</details>

## Se você instalou na aula de 17/10

**O comando é o mesmo.** Rode `npx github:AosJunior/claude-skills edicao` (só o kit de edição) ou, sem nada
depois, o comando que instala tudo. A versão nova substitui a antiga; não precisa desinstalar nada.

**O que some.** O instalador apaga a pasta de cada skill que ele instala e copia de novo. Se você pôs arquivos
dentro das pastas das skills do kit (`decupar`, `inserir`, `sonorizar`, `criticar`, `minha-edicao`, e `reel-novela`
ou outra, se instalou) ou mudou algum arquivo delas, isso sai junto. Copie para outro lugar o que quiser guardar
**antes** de rodar.

**O que fica.**
- As skills **suas**, com outro nome: o instalador só mexe nas skills do kit, por isso a receita que a
  `/minha-edicao` gravou na aula (ex.: uma `legenda-limpa` ou uma receita de formato) continua em `~/.claude/skills`.
- Os seus vídeos e as pastas de trabalho de cada um (`decupagem/`, `insercoes/`, `som/`): continuam valendo, sem
  mover nada. A pasta `marca/` é a novidade, e você ganha ela no passo abaixo.

**O passo do estilo (uma vez).** Em 17/10 a `/minha-edicao` gravava o seu estilo como uma skill em
`~/.claude/skills/<nome>`, e a `/decupar` lia o seu look de lá. Hoje o estilo mora em `marca/estilo.md`, dentro da
sua pasta de edição, e é de lá que a `/decupar`, a `/inserir`, a `/sonorizar` e a `/criticar` leem. Para trazer o
que você já gravou: abra o Claude Code na sua pasta de edição e digite `/minha-edicao`. Ele acha a receita de estilo
da aula, pergunta se pode **importar**, grava o `marca/estilo.md` com o que ela tinha (legenda, cor, som, cartões) e
pergunta só o que faltou (por exemplo, o arquivo de uma fonte, as faixas da sua trilha e o que a edição nunca
faz). A receita antiga não é apagada sem você dizer. Receita de **formato** da aula continua funcionando como está.

## Requisitos de cada skill

| Skill | Precisa de | Baixa na primeira vez |
|---|---|---|
| `/decupar` | ffmpeg e uv | Whisper, cerca de 2 GB (e o OpenCV, uns 50 MB, se o vídeo for horizontal) |
| `/inserir` | ffmpeg e uv. Node 22 ou mais, **só** para a animação. Para «vídeo atrás de você»: Mac com chip M (e as Command Line Tools); no Windows e no Mac Intel ela baixa um modelo de recorte de 15 MB | o navegador que desenha os cartões, cerca de 600 MB |
| `/sonorizar` | ffmpeg e uv; sons da sua pasta ou conta no Epidemic Sound | o Whisper, se a `/decupar` ainda não baixou (cerca de 2 GB) |
| `/criticar` | ffmpeg e uv | o Whisper, se a `/decupar` ainda não baixou (cerca de 2 GB) |
| `/minha-edicao` | ffmpeg e uv | o navegador da prova, cerca de 600 MB (e o OpenCV, uns 50 MB) |
| `/reel-novela` | ffmpeg, uv e Node 22 ou mais; uma chave do ElevenLabs e uma conta num gerador de imagem | — |

- **Espaço em disco:** deixe uns 4 GB livres só para o que as skills baixam, mais ao menos 1,5 GB por minuto de
  vídeo final quando a `/decupar` aplica velocidade ou zoom (os pedaços intermediários ficam em `.dados/` e podem ser
  apagados depois de publicar). A `/reel-novela` pede 5 GB livres ou mais.
- **A primeira execução de cada skill demora:** o uv prepara o ambiente dela por 4 a 5 minutos e a tela parece
  parada. Isso é normal e não é travamento; da segunda vez em diante é rápido.
- **Telemetria do HyperFrames:** a animação da `/inserir` usa o HyperFrames, que vem com a coleta de uso ligada.
  O que ele envia e como desligar estão explicados em
  [skills/inserir/SKILL.md](skills/inserir/SKILL.md) (seção «0. Conferir o ambiente»); a skill avisa você antes.

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

A primeira vez baixa o Whisper (cerca de 2 GB) e cada skill prepara o ambiente dela em 4 a 5 minutos (veja os requisitos acima). Faça isso antes de precisar.

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
