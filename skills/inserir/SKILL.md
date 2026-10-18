---
name: inserir
description: Inserções e legenda gravadas no vídeo de Reels, depois da /decupar. Lê a fala, propõe onde entra cada peça (cartão, número grande, print real da marca citada, vídeo atrás da pessoa, tela dividida no gancho), desenha tudo e a legenda de 1 a 4 palavras no estilo da pessoa e entrega o vídeo pronto. Use quando a pessoa mandar /inserir ou pedir inserções, cartões, grafismos, letterings ou legenda na imagem de um vídeo já decupado.
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

**Réguas padrão.** Valem quando não há formato: nada no primeiro segundo (o gancho é do rosto, menos a tela
dividida), cada peça que cobre o rosto fica de 1,5 a 6 s (painel até 10 s), uns 2 s de rosto entre uma e a
próxima. Se a receita de formato ou o `marca/estilo.md` diz outra coisa, eles mandam: escreva os números
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
