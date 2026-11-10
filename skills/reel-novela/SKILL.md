---
name: reel-novela
description: Reel ou anúncio animado em episódios, em pixel art e narrado por IA. Uma personagem de ficção com um problema e um prazo, relógio e medidor de jogo no topo, um trecho real do vídeo de quem vende como virada e duas opções de uma palavra no fim. Faz a bíblia da série, o elenco, o roteiro na grade, a narração com alinhamento forçado, as cenas em HyperFrames + GSAP, o som, a mixagem e o pacote de veiculação. Use quando a pessoa mandar /reel-novela ou pedir um reel novela, uma novela, um anúncio em episódios ou uma série com personagem.
---

# /reel-novela

A pessoa traz uma oferta e o vídeo de quem vende. Você entrega uma série de episódios 1080×1920 em pixel art, no
formato de novela: uma personagem fictícia carrega um problema com prazo, no meio do episódio assiste a um trecho real
desse vídeo, e o episódio termina em duas opções de uma palavra («Comenta uma palavra»). Quem comenta recebe por
mensagem automática o mesmo vídeo. Narrado por IA, 100 % motion. Tudo em português. Quem usa é leigo, no Claude
Desktop, no Mac ou no Windows; terminal, JSON e comando são trabalho seu.

Três regras valem para o episódio inteiro:

- **A voz manda.** Cada coisa entra na tela na palavra em que é dita; a trilha e os efeitos ficam abaixo da fala.
- **Fato só do `fatos-verificados.md`.** Preço, prazo da oferta, a lei e o trecho da aula. O que mostra o próprio
  vídeo (a duração, os atos) sai dos arquivos reais.
- **Ficção declarada.** A personagem é fictícia e o resultado dela é número de jogo («Limites»).

Scripts, modelos e referências ficam em `scripts/`, `modelos/` e `referencias/` da `<pasta desta skill>` (a pasta
deste arquivo); a skill não usa nenhuma outra instalada. O porquê de cada regra da novela está em
`referencias/licoes.md`.

## Antes de começar

Confira, sem pedir nada à pessoa:

```
ffmpeg -version
uv --version
node --version
python3 --version
```

| Precisa | Para quê | Se faltar |
|---|---|---|
| ffmpeg (com ffprobe) | cortar, medir e mixar | Mac: `brew install ffmpeg`. Windows: `winget install Gyan.FFmpeg` |
| uv | os scripts de voz e som, que instalam as próprias dependências | Mac: `brew install uv`. Windows: `winget install astral-sh.uv` |
| Node 22 ou mais | o HyperFrames (`npx --yes hyperframes@0.9.6`) e os scripts de `briefings/` | Mac: `brew install node`. Windows: `winget install OpenJS.NodeJS.LTS` |
| Python 3.9 ou mais | os scripts da novela | Mac: vem com as ferramentas de linha de comando (`xcode-select --install`). Windows: `winget install Python.Python.3.12` |
| Chave do ElevenLabs | narração e alinhamento forçado | `ELEVENLABS_API_KEY` no ambiente, ou um arquivo que a pessoa indica com a linha `ELEVENLABS_API_KEY=...`, passado como `--chave-arquivo "<arquivo>"`. Sem chave, pare antes do passo 1 e pergunte à pessoa onde ela está |
| Um gerador de imagem | elenco e cenários | o conector do Higgsfield (o calibrado em `referencias/elenco-e-cenarios.md`) ou outro que a pessoa já use, calibrado pela mesma referência |
| Sons | trilha e efeitos | o conector do Epidemic Sound nesta sessão; sem ele, sons da pessoa com a licença anotada, a Biblioteca de áudio do YouTube ou o Pixabay (`referencias/som.md`) |
| Disco | o episódio chega perto de 1 GB, e o render usa mais na hora | 5 GB livres ou mais |

- Se faltar algo, diga em uma linha o que falta e ofereça instalar; instale só depois do sim. No Windows, depois de
  instalar, a pessoa fecha e abre o Claude.
- O arquivo da chave você não abre, não lê e não copia: só passa o caminho aos scripts, que leem a linha da chave sem
  mostrá-la.
- **Windows:** caminho em JSON com barra normal (`C:/pasta/da/serie`), todo caminho entre aspas nos comandos e `python`
  no lugar de `python3` se for o nome instalado.

Pronto quando os quatro comandos respondem com a versão, a chave está no ambiente ou num arquivo que a pessoa
indicou, há um gerador de imagem e uma fonte de sons, e há espaço.

## Conversa

Frases curtas, sem termo técnico: «narrador», «trilha», «efeito», «roleta», «volume de publicação». A pessoa é chamada
nos 4 portões («Portões») e na rodada de perguntas da bíblia; no resto você executa e mostra prévias sem parar o
fluxo. Prévia abre no QuickTime no Mac (`open -a "QuickTime Player" "<arquivo>"`) e no player padrão no Windows
(`start "" "<arquivo>"`). Antes do que demora, diga quanto leva: o render leva de 1 a 2 min por minuto de vídeo num
Mac com chip M (mais no Windows), e a primeira conferência da voz instala o Whisper (5 a 15 min).

## Pasta da série

A pessoa escolhe onde a série mora; aqui ela é `<pasta da série>`, e `<ep>` é `<pasta da série>/epNN`. Evite a Mesa e
Documentos com o disco quase cheio: o iCloud tira os arquivos do disco, e a leitura dá «Operation timed out».

```
<pasta da série>/
  README.md              estado: episódio e passo atuais, decisões com a frase da pessoa, agentes vivos, custo
  biblia.md              de modelos/biblia.md
  fatos-verificados.md   oferta, vídeo de quem vende e cada episódio, com fonte e data
  aula/                  trechos reais do vídeo: <lei>.mp4, <lei>.wav (só a voz), <lei>.json (tempos), <lei>.txt (transcrição literal)
  elenco/<personagem>/   ficha, folha, poses recortadas, geracoes.md
  cenarios/<lugar>/      fundo, frente, quadro aprovado, geracoes.md
  componentes/           cópia de modelos/componentes/ com a pele da série
  epNN/
    briefing.md          o pedido do episódio; aponta para a bíblia e para o fatos-verificados.md
    roteiro.json         de modelos/roteiro-episodio.md
    brutos/narracao/     takes, narracao.wav, narracao-blocos.json, palavras-voz.json, aula-janela.json
    sequencia/motion/    projeto HyperFrames + GSAP (do montar_projeto.py)
    sequencia/som/       mix.json · eventos/<ato>.json · efeitos.json · sons/ · trilha/
    sequencia/previas/   tudo o que a pessoa vê antes da entrega
    sequencia/revisao/   briefings e relatórios das áreas
    sequencia/exports/   <slug>-epNN.mp4 · creditos.md
    veiculacao.md        de modelos/veiculacao.md
```

Atualize o `README.md` da série no fim de cada passo: é dele que uma conversa nova retoma («Fases»), e também uma
compactação. «A aula» é o trecho real do vídeo de quem vende (o especialista ou o dono da oferta), que a pessoa
entrega.

| Leia | Quando |
|---|---|
| [`modelos/biblia.md`](modelos/biblia.md) · [`roteiro-episodio.md`](modelos/roteiro-episodio.md) · [`veiculacao.md`](modelos/veiculacao.md) | passos 1, 4 e 10 |
| [`referencias/elenco-e-cenarios.md`](referencias/elenco-e-cenarios.md) | passos 2 e 6: folha, cenário em camadas, prompts, trava de gasto |
| [`referencias/grade-de-batidas.md`](referencias/grade-de-batidas.md) | passo 4: grade, réguas de fala, mecanismos, anúncio fechado |
| [`referencias/voz.md`](referencias/voz.md) | passos 1 e 5, e sempre que a narração mudar depois das cenas |
| [`referencias/regua-visual.md`](referencias/regua-visual.md) · [`movimento.md`](referencias/movimento.md) · [`gsap-hyperframes.md`](referencias/gsap-hyperframes.md) · [`roleta.md`](referencias/roleta.md) | passo 7 (vão no briefing de cada ato pela `_regua.md`) |
| [`referencias/som.md`](referencias/som.md) | passos 7 (som do piloto) e 8 |
| [`referencias/revisao.md`](referencias/revisao.md) | passo 9, pelo revisor |
| [`referencias/orquestracao.md`](referencias/orquestracao.md) · [`modelos/briefing-area.md`](modelos/briefing-area.md) · [`briefing-ato.md`](modelos/briefing-ato.md) · [`briefing-som.md`](modelos/briefing-som.md) | antes de lançar qualquer agente |
| [`scripts/README.md`](scripts/README.md) | passos 5, 7, 8 e 10: os scripts, a ordem e o que cada um prova |
| [`referencias/licoes.md`](referencias/licoes.md) | quando a pessoa reprovar algo, ou antes de mudar um passo |

## Ordem de trabalho

Os passos 1 e 2 rodam uma vez por série; do 3 ao 10, uma vez por episódio. Nada caro começa antes do portão anterior.
Quem executa cada passo está em «Quem faz o quê».

### 1. Bíblia da série

Você escreve `biblia.md` a partir de [`modelos/biblia.md`](modelos/biblia.md), com a pessoa, numa rodada de perguntas
só, numa mensagem, já com o que você sabe preenchido. Peça já nela o vídeo de quem vende (arquivo ou link), confirme
que ela pode usá-lo e pergunte a mix da série (com trilha ou só efeitos) e o teto de gasto do elenco.

- **Fatos:** um agente levanta os fatos da oferta e do vídeo para o `fatos-verificados.md`, cada um com fonte e data.
  O que a pessoa afirma no pedido também entra para ser conferido. O que a pesquisa corrigir, mostre a ela com a fonte.
- **Aula:** outro agente corta e transcreve os trechos em `aula/`, um por lei prevista, cada um com início e fim em
  pausa, a voz separada em `.wav`, a transcrição literal em `.txt` e o JSON de tempos no formato do `--help` do
  `encaixar_aula.py`.
- **Narrador:** 2 ou 3 amostras com uma frase do piloto ([`voz.md`](referencias/voz.md), «Narrador»). A pessoa escolhe
  ouvindo; o `voice_id` vai para a bíblia e fica fixo para a série toda.

Pronto quando: todo campo da bíblia está preenchido ou marcado «não se aplica» pela pessoa; cada afirmação sobre a
oferta e o vídeo tem fonte no `fatos-verificados.md`; a lei de cada episódio previsto tem um trecho em `aula/` com
início e fim em pausa e transcrição literal; o narrador, a mix, o modo de veiculação e o teto de gasto do elenco estão
escritos.

### 2. Elenco e cenários base

Folhas, poses e cenários da bíblia, pela [`elenco-e-cenarios.md`](referencias/elenco-e-cenarios.md), com a trava de
gasto de lá. O gerador calibrado e a configuração que funcionou estão na tabela dessa referência. Geração paga só
dentro do teto que a pessoa disse, com o custo de cada uma anotado no `geracoes.md`.

Pronto quando: cada personagem tem ficha, folha, as poses mínimas recortadas e a conferência de identidade registrada;
cada cenário tem fundo, frente e quadro aprovado; o gasto somado nos `geracoes.md` está dentro do teto. → **Portão 1.**

### 3. Fatos do episódio

O agente de fatos acrescenta a seção do episódio ao `fatos-verificados.md`: todo número, nome e data da fala e da
tela, e a lei com o trecho da aula. Pronto quando cada item tem fonte e data e o trecho existe em `aula/`.

### 4. Roteiro na grade

O roteirista escreve `<ep>/roteiro.json` pelo [`modelos/roteiro-episodio.md`](modelos/roteiro-episodio.md) e pela
[`grade-de-batidas.md`](referencias/grade-de-batidas.md), começando por «A história antes da grade», numa passada só:
história em 5 linhas, crítico independente, texto final. O crítico é um agente novo, que não escreveu o roteiro, e
ataca coesão, linha do tempo e fluidez; o roteirista responde a cada ponto. Você confere a lista de «Conferência antes
de mandar à pessoa» do modelo e manda à pessoa a tabela batida · voz · tela, a duração estimada e a conta de crédito da
voz (caracteres da `fala` do roteiro inteiro × 2 takes).

Pronto quando a conferência passa item a item e a pessoa aprova. → **Portão 2.** Depois do sim, a fala só muda com
outro sim.

### 5. Voz

Pela [`voz.md`](referencias/voz.md), com o narrador da bíblia e sem amostras novas. Acrescente
`--chave-arquivo "<arquivo>"` aos comandos do `narrar.py` quando a chave estiver num arquivo.

1. **Takes:** `uv run "<pasta desta skill>/scripts/narrar.py" narrar "<ep>/roteiro.json" --saida "<ep>/brutos/narracao" --takes 2`.
2. **Conferência:** `uv run "<pasta desta skill>/scripts/narrar.py" conferir "<ep>/brutos/narracao"`. Fica o take
   marcado com `*`, ou o que tiver texto igual em todos os blocos e mais entonação (`"take": <n>` na raiz do roteiro e
   `narrar` de novo, que remonta sem gastar). Nenhum passou: `--takes 3`.
3. **Alinhamento forçado:**
   `uv run "<pasta desta skill>/scripts/narrar.py" alinhar "<ep>/brutos/narracao/narracao.wav" "<ep>/roteiro.json" --saida "<ep>/brutos/narracao/palavras-voz.json"`.
   Se a validação acusar palavra, corrija o `texto` do bloco e alinhe de novo (`voz.md`, «Alinhamento»).
4. **A aula entra como pausa:**
   `python3 "<pasta desta skill>/scripts/encaixar_aula.py" "<ep>" --aula "<pasta da série>/aula/<trecho>.wav" --tempos "<pasta da série>/aula/<trecho>.json"`.
   Ele abre o silêncio no fim do bloco que tem `aula_depois`, leva a voz de quem vende ao volume da narração e grava a
   janela em `aula-janela.json`.
5. A narração vai à pessoa como prévia, sem parar o fluxo: o narrador já foi aprovado no portão 1.

Pronto quando o take passou no `conferir`, o alinhamento passou na validação e o trecho da aula toca inteiro na pausa.

### 6. Poses e cenários do episódio

Só o que o roteiro pede e ainda não existe na série, como no passo 2, com novo teto. Pronto quando cada `plano` do
`roteiro.json` aponta para um arquivo aprovado em `elenco/` ou `cenarios/`.

### 7. Projeto, ato piloto e atos

1. **Componentes (só no ep. 1):** copie `<pasta desta skill>/modelos/componentes/` para
   `<pasta da série>/componentes/` e troque a pele (`--nv-*` no `novela.css`) pelas cores da bíblia, medindo cada par
   texto × fundo (4,5:1 ou mais). Componente que a série pede e a biblioteca não tem é feito uma vez, por um agente
   Opus, nessa pasta, e entra no README dela. Depois de mexer na biblioteca:
   `python3 "<pasta da série>/componentes/sincronizar.py" "<ep>/sequencia/motion"`.
2. **Projeto:** `python3 "<pasta desta skill>/scripts/montar_projeto.py" "<ep>" --componentes "<pasta da série>/componentes"`.
   Ele copia o esqueleto, os componentes e a mola, põe a narração, calcula a janela de cada ato, cria os `atoN.html`
   vazios e válidos, a barra, a legenda e a `briefings/_regua.md`, e imprime as janelas. Depois, uma vez, `npm install`
   em `<ep>/sequencia/motion/`, para o `npx` achar o HyperFrames travado.
3. **Régua do episódio:** preencha os `[PREENCHER]` da `_regua.md` (personagem e dilema, a frase da pessoa, a pele, a
   tabela de fronteiras entre atos, a direção aprovada). O resto ela já aponta: a régua da novela, o movimento, o
   contrato do render e o README dos componentes.
4. **Briefing por ato:** um `briefings/atoN.md` por ato, de [`modelos/briefing-ato.md`](modelos/briefing-ato.md), com
   a fala no tempo do código, os planos, os textos exatos e as batidas presas às palavras.
5. **Ato piloto com som:** o ato 1 (a abertura) primeiro, por um agente Opus, e o som do piloto em paralelo, por um
   agente com [`modelos/briefing-som.md`](modelos/briefing-som.md) (a trilha editada, se a série tem trilha, os eventos
   do ato 1 e o `mix.json`). Depois, `python3 "<pasta desta skill>/scripts/entregar.py" "<ep>" --rascunho` e a prévia
   do trecho, com o `video` do `mix.json` nesse rascunho:
   `uv run "<pasta desta skill>/scripts/efeitos.py" "<ep>"` e
   `uv run "<pasta desta skill>/scripts/mixar.py" "<ep>/sequencia/som/mix.json" --trecho 0 <fim do ato 1>` (acrescente
   `--sem-trilha` se a série é só com efeitos). Abra `sequencia/previas/previa-trecho.mp4` para a pessoa. → **Portão 3.**
   Reprovado, refaça só o que ela apontou.
6. **Dúvida entre duas direções** (luz, enquadramento, cor da etiqueta) se resolve antes do render, numa folha só:
   monte cada direção numa cópia da pasta `sequencia/motion/` fora do episódio, sem `renders/`, e rode
   `npx --yes hyperframes@0.9.6 compare "<cópia A>" "<cópia B>" --at <t> --labels "A,B" --out "<ep>/sequencia/previas/ab-<t>.png"`
   nos tempos das palavras-gatilho. A pessoa escolhe pela folha, e as cópias são apagadas.
7. **Atos em paralelo:** um agente por ato, cada um dono só do seu `compositions/atoN.html`, de `assets/atoN/` e do
   bloco do ato no `assets/roletas.js`, com o piloto aprovado como padrão. Ato que só usa componente da biblioteca vai
   no Sonnet; ato com componente novo, no Opus. Ninguém mexe no `index.html`, na barra nem na legenda. Cada agente
   confere como manda a régua, «Conferência por snapshot»: `check`, `node briefings/conferir-faixa.cjs` e snapshots
   nas palavras-gatilho e nas fronteiras, com os tempos reais de `node briefings/tempo-real.cjs <t> …`, sem renderizar.
8. **Rascunho inteiro:** com os agentes de ato parados, `entregar.py "<ep>" --rascunho` faz o check, o render, as
   medidas e a folha de contato. Quem julga a folha e as emendas (T ± 0,2) é o orquestrador de motion.

Pronto quando o `check` e o `conferir-faixa` passam, cada palavra-gatilho tem snapshot conferido pela régua, as emendas
passaram na folha e o rascunho mede 1080×1920 com a duração da narração.

### 8. Som

Pela [`som.md`](referencias/som.md), com o briefing de som, um agente só, depois do rascunho inteiro:

- **Trilha** (só se a série tem): a do piloto, completada pela planta no compasso
  (`uv run "<pasta desta skill>/scripts/montar_trilha.py" "<ep>/sequencia/som/trilha/planta.json"`), com a música
  fora da janela da aula (`trilha.fora` no `mix.json`, proposta a calibrar no piloto).
- **Efeitos:** só sons prontos, um `eventos/<ato>.json` por ato, cada efeito com o motivo na imagem, nenhum na janela
  da aula. `uv run "<pasta desta skill>/scripts/efeitos.py" "<ep>"` grava o `efeitos.json` com as regras de quantidade
  e lista o som que falta, com nome e ID (baixe com o `sons.py` e rode de novo); depois,
  `uv run "<pasta desta skill>/scripts/variar.py" "<ep>"`.
- **Mix única:** `uv run "<pasta desta skill>/scripts/mixar.py" "<ep>/sequencia/som/mix.json"` (com `--sem-trilha` se
  a série é só com efeitos), com o `video` no rascunho.

Pronto quando as medidas de `som.md` passam na mix única: −14 LUFS (±0,5), pico de −1,5 dBTP ou menos, ganho da voz de
0,3 dB ou menos, a trilha (se houver) a −20 LU sob a fala e de −7 a −9 nos respiros, e a fala do narrador e a da aula
a 95 % ou mais no `ouvir.py`.

### 9. Revisão de olhos novos

Um agente que não fez nenhum passo, Opus em max, segue [`revisao.md`](referencias/revisao.md) no rascunho mixado e
devolve a lista BLOQUEANTE / MENOR / OK, sem corrigir. Cada BLOQUEANTE vai para o dono do arquivo; refaça o rascunho e
a mix que a correção pedir e confira o item de novo. MENOR: corrija o que for rápido e conte o resto na entrega.

Pronto quando nenhum BLOQUEANTE fica aberto.

### 10. Entrega e veiculação

1. **Render de entrega**, uma vez por versão: `python3 "<pasta desta skill>/scripts/entregar.py" "<ep>"` (sem
   `--rascunho`), com os agentes parados. Aponte o `video` do `mix.json` para ele e mixe de novo; confira as medidas
   do passo 8 nesse arquivo.
2. Em `sequencia/exports/` fica só `<slug>-epNN.mp4`, sem número de versão, e o `creditos.md`: narrador, modelo e
   velocidade; trilha com título, autor, fonte e licença; cada efeito com título, ID e licença; o gerador de cada
   imagem; o trecho da aula com a fonte e a autorização (`som.md`, «Créditos»).
3. O `veiculacao.md` pelo [`modelos/veiculacao.md`](modelos/veiculacao.md), com as duas palavras, a mensagem
   automática e a conferência do fim dele.
4. **Segunda voz**, se a bíblia pede: narre e alinhe em `<ep>-<voz>/brutos/narracao/`, encaixe a aula com
   `--depois <cena>`, `python3 "<pasta desta skill>/scripts/segunda_voz.py" "<ep>" "<ep>-<voz>"`, rascunho, mix e
   medidas. As cenas são as mesmas: nada é refeito à mão.
5. Atualize o `README.md` da série e abra o vídeo para a pessoa, com uma linha por arquivo. → **Portão 4.**

Pronto quando a pessoa aprova e as duas palavras e a mensagem automática estão no `veiculacao.md`. Correção depois
disso: refaça só o que mudou, passe de novo nas medidas e entregue.

**Depois de postado**, o episódio fica só com o final e com o que uma versão nova precisa: `briefing.md`,
`roteiro.json`, `creditos.md`, `veiculacao.md`, `brutos/narracao/` sem os takes, o projeto motion sem `node_modules/`
nem `renders/`, e `sequencia/som/` inteiro menos as prévias (`sons/`, `eventos/`, `efeitos.json`, `mix.json`, a voz
limitada e a trilha editada). Apagar `sons/` ou a voz limitada obriga a baixar e refazer tudo numa correção.

## Portões

| Portão | A pessoa aprova | Antes dele não começa |
|---|---|---|
| 1. Bíblia e elenco | a bíblia (o sim leva o narrador, a mix e o teto do elenco), depois as folhas e os cenários | o roteiro do ep. 1 |
| 2. Roteiro | a tabela batida · voz · tela, a duração e a conta da voz | a narração (gasta crédito) |
| 3. Ato piloto com som | a abertura no estilo final, com a camada de jogo | os demais atos |
| 4. Entrega | o vídeo e o pacote de veiculação | a subida |

Mesmo com «aja de maneira autônoma», o roteiro e o piloto esperam o sim: um episódio inteiro feito sem a pessoa ver o
roteiro é refeito inteiro.

## Quem faz o quê

Você, em medium, escreve a bíblia e os briefings de área, julga nos portões e registra no `README.md` da série. Você
não lança agente de ato, de voz nem de roteiro: lança **um orquestrador por área**, que lança os agentes da área pelo
roteador de modelo e esforço, julga o que voltou e devolve 15 linhas (briefing em
[`modelos/briefing-area.md`](modelos/briefing-area.md); o detalhe em [`orquestracao.md`](referencias/orquestracao.md)).
Cada agente que termina acorda quem o lançou, e assim quem acorda é uma conversa nova e pequena, não a sua. Num
episódio, você faz uns 6 lançamentos.

| Área | Passos | Quem toca | Para e devolve |
|---|---|---|---|
| Série, uma vez | 1 e 2 | você na bíblia; orquestrador Elenco, Opus high (fatos · aula · prompts e geração · recorte) | portão 1 |
| Roteiro e voz | 3 a 5 | orquestrador, Opus high (fatos → roteirista → crítico; depois do portão 2, a voz e o `encaixar_aula.py`) | portão 2; depois, a narração com a aula |
| Motion | 6 e 7 | orquestrador, Opus high (poses novas · `montar_projeto.py` · briefings · ato piloto · som do piloto · atos · rascunho) | portão 3; depois, o rascunho inteiro julgado |
| Som | 8 | um agente só, Sonnet high | as medidas de `som.md` |
| Revisão e entrega | 9 e 10 | você (olhos novos · correções ao dono · `entregar.py` · `veiculacao.md` · segunda voz) | portão 4 |

Passe `model` e `effort` em todo lançamento, pelo roteador de [`orquestracao.md`](referencias/orquestracao.md), que vai
inteiro no briefing de cada área. Agente que falha duas vezes na mesma coisa não é retomado: um novo, um degrau
acima, recebe o que já foi tentado. Geração paga: você colhe o sim e o teto da pessoa no chat e os põe no briefing da
área; o agente gera dentro do teto e devolve o custo de cada geração.

## Custo e como não gastar

O que encarece não é o modelo, é contexto grande relido muitas vezes. A primeira série custou US$ 121 no ep. 1, um
terço disso na sessão principal, que acordava a cada um de 23 agentes com ~360 mil tokens de conversa. Meta de um
episódio com elenco, componentes, voz e som já prontos: **até US$ 35** (a tabela e o teto por área estão em
`orquestracao.md`, «Custo por área»).

- **Sessão enxuta.** Você lê o `README.md`, o `roteiro.json`, os relatórios das áreas e a saída curta dos comandos.
  Composição, imagem, quadro, folha de contato, log e página de pesquisa ficam com o dono ou com um agente juiz.
- **Abrir agente tem piso:** 50 a 80 mil tokens antes de trabalhar. Não abra agente para um comando, nem orquestrador
  para área de um agente só.
- **Agente novo por trabalho, com passagem por arquivo.** Não retome o mesmo agente pela terceira vez.
- **Mecânico é script, não agente:** `encaixar_aula.py`, `montar_projeto.py`, `segunda_voz.py`, `entregar.py` e os
  scripts de voz e som.
- **Briefing de ato autossuficiente:** o agente de ato lê o briefing dele, a `_regua.md` e o README dos componentes;
  não lê este arquivo.
- **Um render de entrega por versão.** Direção e revisão acontecem em rascunho.
- No fim de cada fase, `python3 "<pasta desta skill>/scripts/custo_sessao.py" <id-da-sessão>` dá o custo por área;
  anote no `README.md`. Área que estourar o teto vira lição em `referencias/licoes.md`, com a causa.

## Quando a narração muda depois das cenas

As cenas não mudam: elas escrevem o tempo do código e seguem a narração nova pelo `assets/voz.js`. Fala nova (com o
sim da pessoa), outra voz, ou a tela que precisa segurar mais um pouco: siga [`voz.md`](referencias/voz.md),
«Narração mudou depois das cenas» e «Segurar a tela». A segunda voz é sempre pelo `segunda_voz.py`.

## Modos de veiculação

O modo é da série e fica na bíblia. As duas palavras disparam a mesma mensagem com a aula nos dois modos.

| | Voto real | Anúncio fechado |
|---|---|---|
| Onde vai | episódio no perfil | anúncio fora do perfil, sequência por remarketing |
| Quem decide o próximo | a palavra mais comentada, contada com data e hora no `README.md` | a bíblia: a história já está escrita |
| Abertura do ep. 2 em diante | «Vocês escolheram: X» no segundo 0 | o que ela fez, no segundo 0 |
| Pedido no fim | «Comenta uma palavra», e a legenda diz que a mais votada vira o próximo | «Comenta UMA palavra que eu te mando a aula que ela assistiu» |
| Proibido | escrever o episódio seguinte antes de fechar a contagem | «a mais votada vira o próximo episódio», «vocês mandaram», «vocês escolheram» ou qualquer frase que dê ao público a decisão |

No anúncio fechado, o ep. 1 funciona sozinho para quem nunca viu nada; o 2 e os seguintes vão para quem assistiu ao
anterior. O que muda na grade está na [`grade-de-batidas.md`](referencias/grade-de-batidas.md), «Anúncio fechado».

## Limites

- **Ficção declarada.** A personagem e a história são fictícias, e o `veiculacao.md` diz isso na legenda.
- **Resultado da personagem não é promessa.** O medidor é número de jogo. Seguidor, cliente ou faturamento da
  personagem ficam pequenos e nunca aparecem como efeito garantido da oferta.
- **A dor fica na personagem.** Fala, tela e legenda descrevem a personagem em terceira pessoa e não afirmam atributo
  de quem assiste (profissão, saúde, renda, problema). É o que a política de anúncios da Meta restringe; confira a
  regra vigente antes de cada série subir.
- **Fato só do `fatos-verificados.md`.** A lei que a personagem aprende é a que quem vende diz no trecho, literal.
- **Quem vende é real.** Aparece só no vídeo real, na tela do telefone da personagem, nunca desenhado, e o trecho é
  da pessoa ou do dono da oferta, com autorização para o uso.
- **Até 2:59** por episódio; a referência medida fica entre 74 e 99 s.
- **Créditos do ElevenLabs:** amostras e takes gastam por caractere da fala. Narre só com o roteiro aprovado e diga a
  conta antes. Trocar o take e remontar não gasta; mudar a fala de um bloco gera o roteiro inteiro de novo.
- **Música comercial** no arquivo pode deixar o Reel mudo. Com trilha comercial, entregue a mix só com efeitos e a
  música entra pelo Instagram na hora de postar.
- **Epidemic Sound:** o link de download vale minutos; baixe na hora com o `sons.py`. Efeito é sempre um som pronto,
  só cortado e alinhado.

## Fases e registro

Cada episódio anda em três conversas (roteiro e voz; motion; som e entrega), e a série e o elenco são uma conversa à
parte. No fim de cada fase, com os agentes dela terminados (agente não passa de uma conversa para outra), atualize o
`README.md` da série e diga à pessoa, em uma linha, para abrir uma conversa nova e mandar
`/reel-novela continuar <pasta da série>/epNN`. Ao receber esse pedido, leia o `README.md` e siga do passo em que ele
parou; para escrever briefings, leia o `roteiro.json` e só os títulos das seções do `fatos-verificados.md`. Se o
episódio couber numa conversa abaixo de 200 mil tokens de contexto (o `ctx` da sessão principal no
`custo_sessao.py`), não precisa trocar.

Quando a pessoa reprovar algo, a lição entra em [`referencias/licoes.md`](referencias/licoes.md) e a regra vai para o
passo, a régua ou a grade. Os componentes aprovados ficam em `<pasta da série>/componentes/`; a próxima série parte de
uma cópia deles e troca a pele (`--nv-*`).
