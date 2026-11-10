# Orquestração

Como a novela distribui o trabalho: quem entra em cada passo, como cada agente é escolhido, o que vai no briefing,
quem é dono de cada arquivo e como manter a conversa principal pequena. Os números de custo são do ep. 1 da primeira
série feita com esta skill, medidos pelo `usage` com o `custo_sessao.py`.

## Papéis

- **Sessão principal** (você, em medium): conversa com a pessoa, escreve a bíblia, julga nos portões, escreve os
  briefings de área e registra no `README.md` da série. À mão, só ajuste de uma linha achado por busca.
- **Orquestrador de área**: um agente novo que toca uma área inteira, lança os agentes dela, julga o que voltou e
  devolve 15 linhas.
- **Agentes**: executam e devolvem o resumo e os caminhos. Quem fala com a pessoa e abre arquivo para ela é você.

## Orquestrador por área

Cada agente que termina acorda quem o lançou, e esse turno relê a conversa inteira de quem o lançou. No ep. 1 da
primeira série, a sessão principal lançou 23 agentes direto: foram 147 chamadas com uns 360 mil tokens de contexto
médio, um terço do custo do episódio. Por isso você lança **um orquestrador por área**, e quem acorda a cada agente
terminado passa a ser ele, com uma conversa nova e pequena.

| Nível | Abre | Devolve |
|---|---|---|
| Sessão principal | `README.md` da série, `roteiro.json` e o relatório de cada área | as decisões, os sins da pessoa e o registro |
| Orquestrador de área | o briefing da área e o que é dela: composições, quadros, folha de contato, logs | relatório de até 15 linhas |
| Agente | o briefing dele | resumo de até 10 linhas, para o orquestrador |

| Área | Passos | Quem toca | Lança (agentes) ou roda (scripts) | Para e devolve |
|---|---|---|---|---|
| Série, uma vez | 1 e 2 | você na bíblia; orquestrador Elenco, Opus high | fatos da oferta e do vídeo · corte e transcrição da aula · prompts e geração · recorte | portão 1 |
| Roteiro e voz | 3 a 5 | orquestrador, Opus high | fatos → roteirista → crítico; depois do portão 2, a voz e o `encaixar_aula.py` | portão 2; depois, a narração com a aula encaixada |
| Motion | 6 e 7 | orquestrador, Opus high | poses novas · `montar_projeto.py` · um briefing por ato · ato piloto · atos em paralelo · som do piloto · `entregar.py --rascunho` | portão 3; depois, o rascunho inteiro com a folha de contato julgada |
| Som | 8 | um agente só, Sonnet high, sem orquestrador | trilha, efeitos e a mix única | as medidas de `som.md` |
| Revisão e entrega | 9 e 10 | você | olhos novos · correções ao dono · `entregar.py` · `veiculacao.md` · `segunda_voz.py` | portão 4 |

- **Área de um ou dois agentes não ganha orquestrador.** Abrir um agente custa 50 a 80 mil tokens antes de ele
  trabalhar (cerca de US$ 0,01 no Haiku, 0,18 no Sonnet e 0,35 no Opus).
- **O orquestrador julga.** Abre os snapshots e a folha de contato que os agentes apontaram, manda a correção ao dono
  e só devolve o que passou. O que não fechou vai no relatório como pendência, com o caminho.
- **Comando pronto, ele mesmo roda** (os scripts, `check`, medidas), com a saída curta. Não abre agente para um
  comando.
- **No portão ele para** e devolve o caminho da prévia. Você mostra à pessoa e manda a resposta ao mesmo orquestrador
  por `SendMessage`. Depois de duas retomadas ou de umas 60 chamadas, abra outro, que retoma pelo `README.md` e pelo
  relatório do anterior.
- **O relatório completo fica no disco**, em `<ep>/sequencia/revisao/area-<área>.md`; na conversa vão as 15 linhas.
- **Olhos novos é seu.** Quem revisa não pode ter sido lançado por quem fez.
- **Gasto e chave ficam em cima.** O sim da pessoa e o teto de crédito chegam no briefing da área; o orquestrador não
  pede nada à pessoa e não abre arquivo de chave.
- O briefing da área segue [`../modelos/briefing-area.md`](../modelos/briefing-area.md); os agentes dela,
  [`briefing-ato.md`](../modelos/briefing-ato.md), [`briefing-som.md`](../modelos/briefing-som.md) e o esqueleto de
  «Briefing autocontido».

## Roteador de modelo e esforço

Quem lança não escolhe modelo caso a caso: lê a linha do trabalho e passa `model` e `effort` no lançamento. A tabela
vai inteira no briefing de cada área.

| O trabalho é | Modelo | Esforço | Na novela |
|---|---|---|---|
| um script ou comando que já existe | nenhum agente: quem orquestra roda | — | os scripts de `scripts/`, recorte, `check`, medidas |
| mecânico, com laço e conferência | Haiku | low | baixar, cortar e transcrever a aula, folha de quadros |
| mecânico que gasta crédito ou escolhe take | Sonnet | medium | voz e alinhamento, fatos |
| repetição de um padrão aprovado; som | Sonnet | high | ato que só usa componente da biblioteca, trilha e efeitos, `veiculacao.md` |
| novo e difícil | Opus | high | roteiro, ato piloto, ato com componente novo, prompts de personagem e cenário |
| julgar o trabalho de outro | Opus | high; max só nos olhos novos | crítico do roteiro, revisão do passo 9 |

Agente que falha duas vezes na mesma coisa não é retomado: um novo, um degrau acima (Haiku → Sonnet → Opus), recebe o
que já foi tentado. Um ato no Opus custou só US$ 1 a mais que no Sonnet: o que encarece é contexto grande relido muitas
vezes, não o modelo.

## Atos em paralelo

A unidade de motion é o ato: um plano contínuo que junta os blocos de uma mesma situação (o `ato` de cada bloco no
roteiro). O `montar_projeto.py` cria um `compositions/atoN.html` vazio e válido por ato e fecha o `index.html`.

1. **Ato piloto primeiro.** O ato 1, com a abertura, feito por um agente Opus em high, vai à pessoa com som (portão 3).
   Aprovado, os outros atos o copiam: mesma luz, mesma escala de texto, mesmo ritmo.
2. **Atos em paralelo**, cada agente dono só do seu `compositions/atoN.html`, de `assets/atoN/` e do bloco do ato no
   `assets/roletas.js` (Edit pontual). O `index.html`, a barra e a legenda ficam com o `montar_projeto.py`.
3. **Contrato de emenda**: o da `_regua.md` do episódio (quem entra faz a transição; quem sai segura o último quadro
   até T + 0,30). A tabela de fronteiras vai no briefing de todos os atos.
4. **Conferência do ato:** snapshots nas palavras-gatilho e em T − 0,2, T e T + 0,1 de cada fronteira. O agente vê só o
   lado dele; quem fecha as emendas é o orquestrador, na folha de contato do rascunho inteiro e nos quadros de T ± 0,2.
5. **Defeito de render vale para todos.** O primeiro dono que acha um defeito do navegador avisa o orquestrador, que
   repassa a regra aos outros donos na hora.
6. **Custo para planejar:** um ato no Opus, uns US$ 2,8; no Sonnet, uns 1,3. Teto de uns 40 turnos por agente de ato.

## Briefing autocontido

O agente sabe só o que está no briefing. Briefing de ato e de som seguem os modelos; os outros, este esqueleto:

```markdown
# Briefing: <papel> · <série> ep. <NN>

## O pedido, nas palavras da pessoa
> «...» (com a data), e o que ela já aprovou e reprovou, também nas palavras dela.

## Sua tarefa
<o que fazer, em 3 a 6 linhas, e o que fica com outro agente>

## Leia antes
- <pasta desta skill>/referencias/<o que pesa nesta tarefa>
- <pasta da série>/README.md, biblia.md, <ep>/roteiro.json, <os arquivos de entrada>

## Você é dono de
<os arquivos>. O resto você só lê. Mudança em arquivo de outro: peça ao dono por SendMessage (<endereço>).

## Regras
- <as regras da régua e da grade que pesam nesta tarefa>
- Arquivo de chave você não abre nem copia: os scripts leem a chave.
- Você não fala com a pessoa, não abre arquivo para ela e não renderiza a entrega.

## Devolva
Em até <N> linhas: o que fez, os caminhos, o que conferiu (com os números) e o que ficou pendente. Sem colar código.

Esforço: <low | medium | high | max>. Teto: uns <N> turnos.
```

O pedido vai entre aspas, como a pessoa disse: um resumo seu perde o tom do que ela aprovou ou reprovou. O agente de
ato lê o briefing dele, a `_regua.md` e o README dos componentes; não lê este arquivo nem o `SKILL.md`.

## Um dono por arquivo

| Arquivo | Dono |
|---|---|
| `README.md`, `biblia.md`, `<ep>/briefing.md` | sessão principal |
| `fatos-verificados.md` | agente de fatos; depois, a sessão principal |
| `aula/` | agente da aula (Haiku) |
| `elenco/`, `cenarios/` | orquestrador Elenco e os agentes dele |
| `<ep>/roteiro.json` | roteirista até o portão 2; depois, só com outro sim da pessoa |
| `<ep>/brutos/narracao/` | agente de voz e o `encaixar_aula.py` |
| `index.html`, `compositions/barra.html`, `compositions/legenda.html`, `assets/legenda-grupos.js`, `assets/barra-eventos.js`, `briefings/_regua.md` (fora dos `[PREENCHER]`) | o `montar_projeto.py`; ninguém edita à mão |
| `compositions/atoN.html`, `assets/atoN/`, `briefings/atoN.md` | o agente do ato (o briefing, o orquestrador) |
| `assets/roletas.js` | cada agente de ato, só no seu bloco e com Edit; o bloco da barra, o `montar_projeto.py` |
| `assets/roleta.js`, `assets/mola.js`, `assets/novela/` | ninguém no episódio: a fonte é a skill e `<pasta da série>/componentes/` |
| `assets/voz.js` | só o `ancorar.py` (pelo `segunda_voz.py` ou à mão) |
| `sequencia/som/` | o agente de som |
| `sequencia/exports/` | o `mixar.py` |

Quem vê erro no arquivo de outro avisa o dono. Com atos em paralelo, o `check` mostra também erros dos outros, que
podem estar no meio do trabalho: cada um corrige só o seu. Se o `snapshot` falhar por porta ocupada, espere uns
segundos e repita.

## Render numa cópia

Enquanto houver agente editando o projeto, quem renderiza trabalha numa cópia, fora do episódio:

- Mac: `rsync -a --exclude renders "<ep>/sequencia/motion/" "<cópia>/"`
- Windows: `robocopy "<ep>\sequencia\motion" "<cópia>" /E /XD renders`

Na cópia, `python3 "<pasta desta skill>/scripts/entregar.py"` não serve (ele espera a pasta do episódio): rode
`npx --yes hyperframes@0.9.6 render -o "<ep>/sequencia/previas/<nome>.mp4" -q draft` na raiz da cópia. Um segundo HTML
na raiz do projeto quebra o `check` de quem trabalha; na cópia, não atrapalha. O render de entrega roda no próprio
projeto, com os agentes de ato parados.

## Prévias cedo

- Mostre algo a cada passo: as amostras de voz, a narração com a aula, o piloto com som, a folha de contato e o
  rascunho inteiro.
- Só os 4 portões esperam resposta. Nas outras prévias, diga «sigo; se quiser mudar algo, é só dizer».
- Prévias ficam em `<ep>/sequencia/previas/`. A entrega a pessoa só recebe no passo 10, depois da revisão.
- Mac: `open -a "QuickTime Player" "<arquivo>"`. Windows: `start "" "<arquivo>"`.

## SendMessage para coordenar

- **Endereço:** o lançamento de cada agente devolve um ID; anote os vivos no `README.md` da série, com o papel de cada
  um, e passe no briefing os endereços de quem precisa falar com quem.
- **Correção da pessoa:** na mesma fase, para o agente que fez o trabalho, que continua com o contexto. Numa fase
  seguinte, o agente anterior já não existe: um novo recebe um briefing curto, com o pedido, o arquivo e o que mudar.
- **Contrato comum:** quando muda algo que outros leem (o tempo de um bloco, a janela de um ato), avise todos os
  donos afetados de uma vez.

## Sessão enxuta

Cada turno seu relê a conversa inteira, e o que entra nela custa em todos os turnos seguintes.

- Você lê o `README.md`, o `roteiro.json`, os relatórios das áreas e a saída curta dos comandos (com `| tail -5`).
- Não abre na conversa: composição, imagem, quadro, folha de contato, log de render, transcrição, página de pesquisa.
  Quem julga imagem é um agente juiz, que devolve o veredito e no máximo uma imagem pequena. A prévia você abre para a
  pessoa no player, e isso não passa pelo seu contexto.
- **Agente novo por trabalho, com passagem por arquivo.** Não retome o mesmo agente pela terceira vez: abra outro e
  aponte o `README.md` e o arquivo de entrada. Um agente que passa de ~60 chamadas está caro.
- **Mecânico é script, não agente.** Montar o projeto, encaixar a aula, fazer a segunda voz, renderizar, medir e montar
  a folha têm script (`scripts/README.md`). O montador do projeto feito por agente custou US$ 17 no ep. 1; o
  `montar_projeto.py` faz o mesmo em segundos.
- **Roteiro em uma passada:** história em 5 linhas, crítico independente, texto final. Reescrever três vezes no mesmo
  agente custou o triplo.
- **Um render de entrega por versão.** Direção e revisão acontecem em rascunho.

## Uma conversa por fase

| Fase | Passos | Termina quando |
|---|---|---|
| Série | 1 e 2 | portão 1 |
| Roteiro e voz | 3 a 5 | a narração com a aula encaixada |
| Motion | 6 e 7 | o rascunho inteiro passou no `entregar.py --rascunho` |
| Som e entrega | 8 a 10 | portão 4; as correções depois dele ficam nesta conversa |

- A fase só fecha com os agentes dela terminados: o endereço de um agente não vale na conversa seguinte.
- No fim da fase, o `README.md` da série diz o episódio e o passo seguinte, os arquivos vigentes, as decisões com a
  frase da pessoa e o que falta. A pessoa recebe uma linha: «Fase pronta. Abra uma conversa nova e mande
  `/reel-novela continuar <pasta da série>/epNN`.»
- Se o episódio couber numa conversa abaixo de 200 mil tokens de contexto (o `ctx` da sessão principal no
  `custo_sessao.py`), não precisa trocar.

## Custo por área

No fim de cada fase, `python3 "<pasta desta skill>/scripts/custo_sessao.py" <id-da-sessão>` soma o custo pelo
`usage` de cada chamada, por área, e mostra o contexto médio de cada agente. Anote no `README.md` da série.

Custo do ep. 1 da primeira série (formato e série nascendo juntos, duas vozes): **US$ 121** em equivalente de API.

| Para onde foi | US$ | Repete no ep. 2? |
|---|---|---|
| Sessão principal (147 chamadas, contexto médio de ~360 mil tokens) | 37 | sim, e é o maior ralo |
| Montador do projeto (retomado 4 vezes, 136 chamadas) | 17 | não: hoje é o `montar_projeto.py` |
| Biblioteca de componentes | 14 | não: vem pronta em `modelos/componentes/` |
| Roteiro (3 passadas no mesmo agente) | 12 | sim, em 1 passada |
| Cinco atos (3 Opus a ~2,8; 2 Sonnet a ~1,3) | 11 | sim |
| Som (trilha, efeitos, 3 mixagens) | 6 | sim, menos: a paleta é fixa |
| Formato, prévias paradas e elenco | 18 | não |
| Revisão de olhos novos | 4 | sim |
| Voz (duas vozes) | 1 | sim |

Gasto de crédito no mesmo episódio: 10,5 créditos de imagem (elenco de 3 personagens, 4 cenários e a calibração),
11.360 caracteres no ElevenLabs (4 takes por voz), 1 trilha e 18 efeitos do Epidemic Sound, 3 renders de entrega por
versão (a meta é 1).

Meta de um episódio com elenco, componentes, voz e som já prontos: **até US$ 35** (estimativa, ainda não medida num
episódio inteiro). Teto por área: sessão principal 6 · roteiro e voz 6 · motion 13 · som 4 · revisão e entrega 4 ·
poses novas 2. Área que estourar o teto vira lição em [`licoes.md`](licoes.md), com a causa.
