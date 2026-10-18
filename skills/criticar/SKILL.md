---
name: criticar
description: Crítica do vídeo editado antes da entrega. Mede emendas, gagueira, quadros soltos, margem, posições, legenda e volume, e um editor-chefe julga gancho, trilha e legibilidade. Use antes de entregar qualquer vídeo editado ou quando a pessoa mandar /criticar.
---

# /criticar

Um vídeo editado (saída da `/decupar`, da `/inserir` e da `/sonorizar`, ou de outra edição) está para ser
entregue. Você mede tudo o que dá para medir, entrega as folhas a um editor-chefe que não participou da edição,
corrige o que ele e as medidas reprovarem e mede de novo. Quem usa é leigo, no Claude Desktop, no Mac ou no
Windows. Tudo em português.

**Assistir o vídeo inteiro** quer dizer: a folha de quadros cobre 100 % da duração, 1 quadro a cada segundo,
mais todos os quadros em volta de cada corte (2 antes e 2 depois). Amostras de alguns trechos não contam. O
script grava essa folha; você e o editor-chefe olham todas as páginas dela antes de dizer que um item passa.

A pasta do vídeo só é lida. Todo arquivo novo nasce em `<pasta do vídeo>/critica/`. Os scripts ficam em
`<pasta desta skill>/scripts/` e a régua do editor-chefe em `<pasta desta skill>/critica.md`.

## Conversa

Frases curtas, sem termo técnico: "quadro solto", "emenda", "margem", "palavra repetida". Antes do que demora,
diga quanto leva:

| Etapa | Mac com chip M | Windows ou Mac Intel |
|---|---|---|
| Primeira vez sem a `/decupar` no computador: instala o Whisper e baixa o modelo (uns 1,6 GB) | 5 a 15 min | igual |
| Medir (ler o vídeo inteiro e transcrever) | uns 30 s por minuto de vídeo | 2 a 3 min por minuto |
| Medir de novo o mesmo vídeo (transcrição em cache) | uns 15 s por minuto | uns 40 s por minuto |
| Editor-chefe | 2 a 4 min | igual |

## 0. Conferir o ambiente

`ffmpeg -version` e `uv --version`. Se faltar um, diga em uma linha o que falta e ofereça instalar; instale só
depois do sim (Mac: `brew install ffmpeg uv`; Windows: `winget install Gyan.FFmpeg astral-sh.uv` e depois a
pessoa fecha e abre o Claude). Pronto quando os dois respondem com a versão.

## 1. Medir

```
uv run "<pasta desta skill>/scripts/criticar.py" "<pasta do vídeo>"
```

A pasta do vídeo é a que tem `decupagem/`, `insercoes/`, `som/` e `entrega/`. O script acha sozinho o vídeo
mais novo em `entrega/` (senão a saída do `som.json`, o vídeo da `/inserir` ou o final da `/decupar`) e acha a
`marca/` subindo as pastas. Para outro arquivo, `--video "<arquivo>"`. Rode com tempo-limite de 10 minutos; na
primeira vez da máquina, em segundo plano.

Ele grava em `critica/`:

- `relatorio.md`: cada item com **passa**, **reprova**, **atenção** ou **pulado**, a medida e onde (tempo), e a
  correção de cada reprovação (skill · arquivo · campo).
- `medidas.json`: as mesmas medidas, completas.
- `folha-NN.jpg` (1 quadro por segundo), `folha-cortes-NN.jpg` (os quadros em volta de cada corte),
  `folha-referencia.jpg` (com vídeos em `marca/referencias/`) e `letras/` (cada palavra estilizada ampliada).
- `fala-final.json`: a transcrição do vídeo final com tempo por palavra.

O que falta ele avisa e pula: sem `insercoes/.dados/geometria.json` saem margem, posições e a comparação da
legenda; sem `decupagem/palavras-corte.json` as emendas vêm dos cortes da imagem e não há texto esperado.
Diga à pessoa, em uma linha, o que ficou de fora.

Pronto quando ele imprime "Pronto" e o item "Folha de quadros" passa (cobertura de 100 %).

## 2. Editor-chefe (subagente de contexto limpo)

Abra um subagente novo (ferramenta Agent ou Task) que **não** recebe a conversa nem o que você fez na edição.
O prompt dele leva só caminhos e a tarefa:

```
Você é o editor-chefe deste vídeo. Leia a régua em "<pasta desta skill>/critica.md" e siga-a.
Material: "<pasta do vídeo>/critica/" (relatorio.md, medidas.json, todas as folha-*.jpg, letras/),
"<marca>/estilo.md", "<marca>/referencias/" e "<pasta do vídeo>/som/som.json" (ou creditos.md).
Olhe todas as páginas da folha e todos os arquivos de letras/ antes de julgar.
Devolva a tabela dos 9 itens com passa/reprova, motivo, onde e a correção, e a linha de veredito.
```

Sem ferramenta de subagente no ambiente, faça você mesmo a leitura com a régua, abrindo só esse material, e
anote no relatório da entrega que não foi um olhar de fora.

Pronto quando o subagente devolve os 9 itens e o veredito. Grave a resposta em `critica/editor-chefe.md`.

## 3. Corrigir e medir de novo

Cada reprovação, do relatório ou do editor-chefe, vira uma mudança no arquivo da skill de origem. Você aplica,
roda a skill de origem e volta ao passo 1.

| Reprovação | Skill · arquivo · campo |
|---|---|
| Quadro solto | `/inserir` · `insercoes.json` · `de`/`ate` da camada ou da dividida que troca 1 quadro antes do corte (as duas bordas no mesmo quadro); ou `/decupar` · `cortes.json` · `ajustes` `"T5.ate"` |
| Emenda: pausa longa, sem respiro, corta dentro do som | `/decupar` · `cortes.json` · `ajustes` `{"T5.ate": -0.04, "T6.de": 0.04}` ou `pausa_max` |
| Emenda: volume da voz pula | `/decupar` · `cortes.json` · trocar a tomada do trecho (outro `de`/`ate`) |
| Gagueira, repetição, palavra que sumiu | `/decupar` · `cortes.json` · `trechos`: começar ou terminar o trecho na palavra certa (`"de": "F3:2"`) |
| Margem | `/inserir` · `insercoes.json` · `estilo.legenda_y`, `estilo.destaque_y` ou o `y` da camada |
| Posições todas na mesma zona | `/inserir` · `insercoes.json` · `x`, `y` e `lugar` das camadas |
| Tempo sem evento | `/inserir` · `insercoes.json` · uma camada no meio do trecho; ou `/decupar` · `cortes.json` · outro `zoom` |
| SRT diferente da gravada, SRT depois do fim | `/inserir` · refazer pelo `inserir.py` (as duas saem da mesma lista) |
| Volume | `/sonorizar` · `som.json` · mixar de novo |
| Palavra estilizada ilegível | `/inserir` · `insercoes.json` · `estilo.fonte_destaque` (ou o modelo do lettering em `marca/letterings/`) |
| Trilha fora do universo | `/sonorizar` · `som.json` · `sons` e `trilha` com uma trilha de `marca/sons/` |
| Gancho fraco, fora da referência | o item da `/inserir` ou da `/decupar` que o editor-chefe apontou; confirme o novo gancho com a pessoa |

Mudança de gancho ou de trilha muda o vídeo que a pessoa vai ver: mostre a proposta e espere o sim. O resto você
aplica sem perguntar.

## Pronto quando

Nenhum item sai reprovado, nem no relatório nem no editor-chefe, **ou** a pessoa aceitou por escrito cada item
que ficou ("pode ir com a pausa do 00:04"). Itens em **atenção** você ouve ou olha e conta em uma linha o que
achou. Na entrega, diga quantas rodadas foram e o que mudou em cada uma.

## Windows

Igual ao Mac: os comandos rodam no PowerShell com aspas duplas em volta de todo caminho. A transcrição usa o
faster-whisper na CPU, mais lenta (veja a tabela). Se o antivírus perguntar sobre o `uv` ou o `ffmpeg`, é seguro
permitir.

## Limites

- O script não ouve a trilha: o gosto musical fica com o editor-chefe, pelos créditos e pela marca.
- Emenda sem `palavras-corte.json` é aproximada pelos cortes da imagem: o que ela aponta, ouça antes de mexer.
- Diferença entre o texto falado e o esperado longe de uma emenda costuma ser variação do Whisper; fica em
  **atenção**.
