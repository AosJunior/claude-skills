---
name: inserir
description: Inserções e legenda gravadas no vídeo de Reels, depois da /decupar. Lê a fala, propõe onde entra cada peça (cartão, número grande, print real da marca citada, vídeo atrás da pessoa, tela dividida no gancho), desenha tudo e a legenda de 1 a 4 palavras no estilo da pessoa e entrega o vídeo pronto. Use quando a pessoa mandar /inserir ou pedir inserções, cartões, grafismos, letterings ou legenda na imagem de um vídeo já decupado. Com pedido de animação suave no estilo Apple ou de vídeo 100% motion só com a voz, faz o motion em HyperFrames + GSAP (o rosto em janela ou só a voz).
---

# /inserir

A pessoa traz a pasta `decupagem/` que a `/decupar` gerou (vídeo cortado, `palavras-corte.json`,
`legenda.srt`, `transcricao.txt`). Você lê a fala, propõe onde entra cada peça, confirma uma vez e entrega
o vídeo com tudo gravado na imagem, num render só. Quem usa é leigo, no Claude Desktop, no Mac ou no
Windows. Tudo em português. Se ela trouxer só o vídeo bruto, diga que primeiro vem a `/decupar` e pare.

O vídeo cortado só é lido: todo arquivo novo nasce em `<pasta do vídeo>/insercoes/`. Os scripts ficam em
`<pasta desta skill>/scripts/`. O formato completo do `insercoes.json` está em
[referencia.md](referencia.md); leia antes de escrever o mapa. No Windows, leia também [windows.md](windows.md).
O contrato entre as skills do kit (pastas, âncoras, saídas) é o `docs/edicao-contrato.md` do repositório.

## Conversa

Frases curtas, sem termo técnico: "cartão", "número grande", "vídeo atrás de você", "legenda na imagem".
A pessoa nunca abre terminal, edita JSON ou roda comando: isso é trabalho seu. Antes de cada etapa que
demora, diga quanto tempo leva:

| Etapa | Mac com chip M | Windows ou Mac Intel |
|---|---|---|
| Primeira vez: baixa o navegador que desenha (uns 200 MB, uma vez por computador) | 1 a 3 min | 2 a 5 min |
| Desenhar legenda e peças (`--cartoes`) | 10 a 30 s (depois, só o que mudou) | 30 s a 1 min |
| Máscara da pessoa (só com vídeo atrás dela; fica guardada) | uns 8 s por segundo de trecho | uns 10 s por segundo de trecho |
| Vídeo final só com cartões e legenda | uns 20 s por minuto de vídeo | 1 a 2 min por minuto |
| Vídeo final com camadas ou tela dividida | uns 25 s por minuto de vídeo | 2 a 4 min por minuto |

A única pergunta do fluxo é a confirmação do mapa (passo 3). O resto você executa.

## Pedido completo (decupar, inserir e sonorizar de uma vez)

Quando a pessoa pede o vídeo inteiro de uma vez ("decupa, insere e sonoriza", "edita tudo", "só quero ver o final"),
as três skills rodam em sequência, mas **antes de abrir qualquer agente** faça um grilling curto, uma pergunta por
vez, até fechar:

1. **Mensagem e clima**: o que ela quer que o público sinta e leve. Isso guia a trilha, o gancho e os cortes.
2. **Gancho**: a ideia da tela de abertura em uma frase.
3. **Trilha**: Reels ou áudio de referência, se ela tiver. Sem referência, você resolve sozinho (veja a `/sonorizar`).
4. **Fala intocável**: frases que não podem sair, mesmo para acelerar.
5. **Orçamento**: diga o plano (quantos agentes, quantas rodadas, quais trechos em motion) e espere o sim.

Depois do grilling, na ordem e sem voltar:

- **Fatos fechados antes das peças**: todo número e nome que vai para a tela entra no `fatos-verificados.md` da pasta
  do vídeo antes de desenhar.
- **Estado em disco**: mantenha `estado.md` na pasta do vídeo (etapa, arquivos vigentes, decisões com a frase dela, o
  que falta) e atualize no fim de cada etapa.
- **Conversa enxuta**: cada turno relê a conversa inteira, então o que entra nela pesa em todos os seguintes. Leia os
  resumos dos agentes e a saída curta dos comandos; quadro, folha de contato, cena e log ficam com quem os fez.
- **Uma conversa por skill**: a decupagem, as inserções e o som podem rodar cada um numa conversa nova, que começa
  lendo o `estado.md`. No fim de cada uma, diga em uma linha para ela abrir a próxima conversa com a skill seguinte.
- **Uma renderização final só**: o 1080 roda depois que ela aprova a prévia leve **com som**. Correção pequena
  depois disso refaz só o trecho.
- **Mixagem em lote**: junte todas as mudanças de som, mixe uma vez e confira.
- Use sempre os scripts e modelos das skills; não copie o motor ou o mixer de outro vídeo.

## 0. Conferir o ambiente

`ffmpeg -version` e `uv --version`. Se faltar um, diga em uma linha o que falta e ofereça instalar; instale
só depois do sim (Mac: `brew install ffmpeg uv`; Windows: [windows.md](windows.md)). Pronto quando os dois
respondem com a versão. Vídeo atrás da pessoa usa o Apple Vision no Mac com chip M (precisa das Command
Line Tools: `xcode-select --install`); sem elas, o script cai sozinho num recorte que roda em qualquer
computador e avisa em uma linha.

## 1. Ler a fala, a marca e o estilo

- **Marca**: todo script imprime `Marca: <pasta>` ou `Marca: nenhuma`. Com marca, leia o `marca/estilo.md`
  inteiro: ele manda em fontes, legenda, cor, composição e réguas. Caminho que começa com `marca/` no JSON
  vale contra essa pasta. Sem marca, procure em `~/.claude/skills/` uma receita feita com a `/minha-edicao`
  que fale de legenda ou letterings; sem receita, fique com o padrão do script e diga isso em uma linha.
- **Fala**: leia a `decupagem/transcricao.txt` (cada frase tem um id `F<n>`) e o `palavras-corte.json`
  (o que ficou no corte, com o tempo de cada palavra). Escreva os tempos do mapa como **âncoras na fala**
  (`"F15:repente"`, `"F17:fim+0.1"`; formas em [referencia.md](referencia.md#âncoras)): elas sobrevivem a
  um novo corte. Leia também a seção "Onde cabe imagem ou grafismo" da `decupagem.md`, se existir.
- **Fonte** é um arquivo `.otf` ou `.ttf`. Fonte que só existe no CapCut ou no Canva não é arquivo: peça o
  arquivo ("arrasta aqui o arquivo da fonte") ou fique com a do sistema.
- Olhe 3 ou 4 quadros do vídeo (`ffmpeg -ss <s> -i <vídeo> -frames:v 1 -vf scale=540:-2 q.jpg`) para ver
  onde fica a cabeça: é ela que decide onde cabe peça sem cobrir o rosto.

Pronto quando você sabe o tempo de cada frase, o estilo e a posição do rosto.

## 2. Mapa de inserções (você julga)

Uma peça entra quando a fala pede imagem. A **forma da fala** decide a peça:

| A fala tem | Peça |
|---|---|
| lista, passo a passo, comparação | cartão `lista`, `etapas`, `comparacao` (itens entram no tempo em que são ditos) |
| número ("100 mil", "R$ 18 milhões") | cartão `numero` ou camada `html` com o lettering da marca |
| conceito com nome ("conformidade social") | cartão `frase` ou camada `html` |
| marca, site ou app citado | cartão `print` (print real, com `print.py`) |
| "isso aqui apareceu em todo lugar", gente usando o produto | camadas `video` com `lugar: "atras"`: vídeos reais em volta da cabeça, atrás da pessoa |
| gancho com uma cena ("placa de aluga-se") | `divididas` + camada `video` no `topo` + camada `faixa` com a pergunta |

Cartões (`insercoes`) cobrem a tela ou um painel; camadas (`camadas`) são peças soltas que entram com pop.
Use o que o `marca/estilo.md` pede; sem ele, cartões. Exemplo curto de camadas (formato completo na
[referencia.md](referencia.md#camadas)):

```json
"divididas": [{"id": "gancho", "de": 0, "ate": "F7:fim", "corte": 960,
               "pessoa": [{"de": 0, "recorte_y": 150, "escala": 0.72}, {"de": "F3", "recorte_y": 450}]}],
"camadas": [
  {"id": "placa", "tipo": "video", "arquivo": "../brutos/videos/aluga-se.mp4", "src": 22.0, "de": 0, "ate": "F7:fim",
   "lugar": "topo", "recorte": [{"t": 0, "caixa": [21, 347, 699, 932]}, {"t": 1.0, "caixa": [105, 347, 495, 660]}]},
  {"id": "headline", "tipo": "faixa", "texto": "Ter loja virou coisa de pobre?", "de": 0, "ate": "F1:fim+0.25",
   "y": 908, "fonte": "marca/fontes/NeueMontreal-Bold.otf"},
  {"id": "feed-1", "tipo": "video", "arquivo": "../brutos/videos/review-1.mp4", "src": 114, "de": "F15:repente",
   "ate": "F17:fim", "x": 30, "y": 300, "w": 390, "rot": -6, "raio": 26, "sombra": 0.35, "lugar": "atras",
   "entra": {"efeito": "pop", "dur": 0.18}, "sai": 0.12}
]
```

**Réguas padrão.** Valem quando não há formato. **Gancho com peça desde o quadro 0**: rosto falando sozinho no
começo não para o scroll (1,4 s só de rosto foi o defeito de um Reel). O gancho abre com um título grande e
chamativo (a promessa ou o conflito da fala), que já se lê no quadro 0, e com algo que se move: de preferência a
tela dividida, com a cena da fala em cima e a pessoa embaixo. Emoção pessoal no meio do vídeo continua sendo do
rosto, sem peça. Cada peça que cobre o rosto fica de 1,5 a 6 s (painel até 10 s), com uns 2 s de rosto entre uma e
a próxima. Se a receita de formato ou o `marca/estilo.md` diz outra coisa, eles mandam: escreva os números
deles em `estilo.reguas` e o script passa a avisar por eles. Camada atrás da pessoa e topo da dividida não
cobrem o rosto e ficam fora dessas réguas. Ritmo: "algo novo a cada 2,5 s" é de dica rápida; história e
depoimento pedem respiro.

**Zona segura.** Texto e peça da frente ficam entre `y` 260 e 1600 (`estilo.zona_segura`): acima e abaixo
disso o Instagram põe o nome do perfil, a legenda dele e os botões. Peça que precisa sair dela leva
`"aceito": "<motivo>"`.

**Só o que foi dito**: todo número, nome e dado sai da fala ou de fonte que você conferiu. Sem dado, sem peça.

**Origem obrigatória**: imagem e vídeo de terceiros vão para `brutos/imagens/` ou `brutos/videos/`, com uma
linha em `brutos/fontes.md` que tem o nome do arquivo, o endereço e a licença. Camada de `brutos/` sem essa
linha faz o script parar. Print de marca: `uv run "<pasta desta skill>/scripts/print.py" "<site>"
"<pasta insercoes>/prints/<marca>.png"`; abra e confira página certa, sem aviso de cookies e sem dado pessoal.

**Imagem ou vídeo gerado** (Higgsfield, GPT Image, Nano Banana): escreva só o prompt em
`<pasta insercoes>/prompts.md` ([modelo](referencia.md#promptsmd)), sem gastar crédito.

**Legenda**: escolha as palavras de destaque (uma a cada 5 a 8 s, a que carrega a frase), corrija em
`correcoes` o que o Whisper ouviu errado e use a lista `legenda` para subir, mover ou esconder a legenda
num trecho (nunca inserção vazia).

Grave o `insercoes.json`. Pronto quando cada momento de lista, número, comparação, passo a passo, marca ou
cena citada virou peça ou tem o motivo de ter ficado de fora.

## 3. Confirmar

Mande no chat uma linha por peça (tempo, o que aparece, onde), as palavras de destaque e uma pergunta só:
"Faço assim? Se quiser mudar, é só dizer (por exemplo: 'tira o cartão de 0:42', 'põe o número de 1:05')."

## 4. Desenhar e conferir

```
uv run "<pasta desta skill>/scripts/inserir.py" "<pasta decupagem>" --cartoes
```

Grava `cartoes.png` (cartões, faixas e letterings), a `legenda-curta.srt` e o `.dados/geometria.json`. Abra
o `cartoes.png` e confira texto certo e com acento, nada cortado, destaque na palavra certa. Todo "Aviso"
é de régua: ajuste o mapa ou, se a receita pede outro número, `estilo.reguas`. "ATENÇÃO" (zona segura,
letra que a fonte não tem) faz o script sair com código 2 e não gravar o vídeo.

Pronto quando o script sai com código 0, sem "Aviso" que você não saiba explicar, e o `cartoes.png` passa.

## 5. Vídeo

```
uv run "<pasta desta skill>/scripts/inserir.py" "<pasta decupagem>"
```

Opções: `--video <arquivo>` (padrão: `final.mp4`, senão `previa.mp4` da decupagem), `--saida <arquivo.mp4>`,
`--pasta <pasta de trabalho>`, `--mascara auto|vision|rvm`. Rode com tempo-limite de 10 minutos. Com
camada atrás da pessoa, a máscara é gerada antes, só nos trechos dela, e fica guardada.

Ele grava o vídeo e a pasta `quadros/` com um quadro de cada cartão, camada, dividida e das legendas de
destaque, juntos em `quadros/folha.jpg`. Abra a folha (e o quadro inteiro do que estiver em dúvida):

- a legenda se lê e não encosta no rosto nem nos botões;
- o acento sai na mesma fonte da palavra (o "Ã" do "NÃO");
- nada da frente cobre o rosto; o que está atrás da pessoa fica atrás do cabelo e das mãos, sem halo.

Pronto quando todos os quadros passam.

## 6. Crítica e entrega

Se a `/criticar` estiver instalada, chame-a agora com a pasta do vídeo: ela mede o que o olho erra
(zona segura, tempo sem evento, legenda contra o SRT) e devolve o que corrigir. Corrija e rode o passo 5
de novo. Entregue uma linha por arquivo:

- `<vídeo>-insercoes.mp4`: o vídeo com tudo na imagem, pronto para postar ou para a `/sonorizar`.
- `legenda-curta.srt`: a mesma legenda que está na imagem, para quem quiser estilizar no editor.
- `prompts.md` (se houver): os prompts das imagens que valem a pena gerar.
- E uma linha por peça: tempo, o que aparece e por quê.

## 7. Corrigir

A pessoa diz o que mudar; edite o `insercoes.json` e rode o passo 5 de novo. Só o que mudou é redesenhado.

## Motion em HyperFrames + GSAP (quando a pessoa pede animação)

As peças deste fluxo entram em corte seco ou com pop. Quando a pessoa pede animação "smooth", "profissional",
"estilo Apple", "tudo o que eu falo acontece na tela" ou um vídeo **100 % motion só com a voz**, o vídeo é feito em
**HyperFrames** (HTML renderizado em vídeo, Apache-2.0, roda no Mac e no Windows com Node 22+) e **GSAP**. Antes de
escrever a primeira cena, leia `<pasta desta skill>/referencias/gsap-hyperframes.md` (o contrato do render e a régua
de movimento). As consultas estão copiadas em `referencias/hyperframes/` e `referencias/gsap/`; esta skill não
depende de outra instalada.

- **Projeto**: `npx hyperframes init <pasta do vídeo>/motion` uma vez. Raiz 1080×1920 (`data-width`/`data-height`),
  `data-duration` igual à duração da fala cortada. Uma cena por subcomposição (`data-composition-src`), cada uma com
  sua timeline pausada e ids prefixados com o nome da cena.
- **Dois modos**:
  - **Com rosto**: o vídeo cortado da `/decupar` entra como `<video>` (sem `crossorigin`). Nos trechos de conteúdo ele
    encolhe para uma janela arredondada embaixo e o conteúdo fica em cima; no gancho, tela dividida desde o quadro 0.
    A geometria de cada trecho vira tweens do contêiner do vídeo (`x`, `y`, `scale`, `borderRadius`), nunca do
    `<video>` com `data-start`.
  - **100 % motion (só a voz)**: a voz entra como `<audio id="voz">`; não há janela nem rosto. Cada frase vira uma
    cena com transição causada por algo na tela.
- **Tempo da fala**: o tempo de cada palavra vem de alinhamento forçado da voz com o texto corrigido (a transcrição
  da `/decupar` ou o roteiro), por exemplo o do ElevenLabs (`POST /v1/forced-alignment`, com números e siglas por
  extenso no texto). O `palavras-corte.json` e o `npx hyperframes transcribe` vêm do Whisper, que já errou até
  0,6 s. Confira nas pausas da onda (`silencedetect` do ffmpeg): nenhuma palavra começa dentro de uma pausa de
  120 ms ou mais. Cada coisa dita entra na palavra em que é dita. Legenda por palavra, de 2 a 4 palavras por grupo,
  logo acima do vídeo (ou no terço de baixo no modo só voz).
- **Dados reais**: mockup de perfil com a foto, o nome e os posts reais (sem posts políticos); conversa do Claude com o
  pedido de verdade; número só da fala ou do `fatos-verificados.md`. Interface filmada da tela é redesenhada em HTML a
  partir do código e dos quadros, com letra maior para o celular.
- **Número na tela** pode girar como roleta até travar na palavra. O som da roda é da `/sonorizar`: só no número
  principal e curto.
- **Antes de desenhar**: procure o efeito no registro (`npx hyperframes catalog --query <efeito> --json`,
  `referencias/hyperframes/registry.md`) antes de fazer à mão.
- **Gancho**: movimento e título que já se leem no quadro 0; a ação presa às palavras; o quadro do impacto vira a capa.
  Um gancho só, em high (segunda versão só se a pessoa pedir), aprovado com som antes das outras cenas.
- **Equipe e orçamento**: um agente por cena, em paralelo, com briefing em arquivo e teto de uns 40 turnos. Ele roda
  `npx hyperframes check` e confere 3 quadros-chave (`npx hyperframes snapshot --at ...`), nunca a sequência inteira.
  Depois, **um** revisor de olhos novos lê uma folha de contato do vídeo montado e devolve a lista de correções; não
  há revisor por trecho, crítico extra nem auditoria quadro a quadro.
- **CTA**: o toque no ícone abre o app com mola e a palavra do CTA é digitada na barra de comentário.
- **Ordem**: `check` limpo → prévia leve com som para a pessoa aprovar (`npx hyperframes preview --background` ou
  render em qualidade de rascunho) → `npx hyperframes render` em 1080×1920 uma vez. Correção depois disso renderiza
  só o trecho. O som final sai na `/sonorizar` sobre o vídeo renderizado.
- **Pasta**: trabalhe fora da Mesa e de Documentos quando o disco estiver quase cheio (o iCloud tira os arquivos do
  disco: "Operation timed out").
- **Revisão**: legenda contra balões e cartões, elementos que sobram depois da saída da cena e palavras da fala que
  ficam baixas (essas sobem na `/sonorizar`, «Fala baixa»).

## Limites

- Cada legenda, cartão, faixa e lettering é um PNG desenhado pelo navegador. Sem camadas nem tela dividida,
  o ffmpeg põe tudo por cima do vídeo (caminho rápido); com elas, o `compor.py` monta quadro a quadro, em
  blocos paralelos, uma geração de compressão só.
- A máscara do Apple Vision é limpa na borda, mas pode deixar de fora um objeto fino na mão; o recorte
  RobustVideoMatting (Windows, Mac Intel) pega mais fio de cabelo e às vezes um pedaço do fundo. Confira no
  quadro da camada.
- A fonte da pessoa fica no computador dela; o script só lê o arquivo.
- Print de site depende do site: alguns bloqueiam robô ou abrem em branco. Aí vale a loja oficial ou o
  perfil da marca.

## Esforço

- Peças simples, legenda e mapa de inserções: **medium**.
- Motion: o gancho e as cenas com gráfico ou componente novo rodam em **high**, no Opus. A cena simples, que repete
  um componente já aprovado sem gráfico novo, roda em **high** no Sonnet (`model: "sonnet"`).
- A revisão final de olhos novos: **max** (`effort: "max"`), só ela.
- Orquestração, montagem, render e mixagem: **medium**.
