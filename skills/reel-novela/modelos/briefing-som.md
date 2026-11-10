<!-- Modelo do briefing de som: <ep>/sequencia/som/briefing-som.md. Vale para o som do piloto (passo 7) e para o
     agente de som do passo 8, que faz trilha, efeitos e a mix única. Quem escreve troca cada {{…}}, apaga este
     comentário e confere três coisas antes de abrir o agente:
     - a narração aprovada, com a aula encaixada, e o palavras-voz.json validado estão no projeto motion;
     - cada revelação tem o tempo real e a palavra;
     - a bíblia diz se a série sai com trilha ou só com efeitos, e qual é a frase do que a trilha conta. -->
# Som de {{série}} ep. {{NN}}

## O pedido, nas palavras da pessoa

> «{{o que a pessoa disse sobre o som, com a data}}»

- Aprovou: {{…}}.
- Reprovou: {{…}}.

## O episódio

- **Pasta:** `{{ep}}/` (estado no `README.md` da série).
- **Vídeo:** anúncio 9:16 em pixel art, sobre a narração aprovada: {{narrador}}, {{modelo}} a {{velocidade}}×, em
  `sequencia/motion/narracao.wav` ({{duração}} s).
- **Mix:** {{com trilha | só efeitos}}, um arquivo só: `sequencia/exports/{{slug}}-ep{{NN}}.mp4`.
- **Trilha** (se houver): «{{título}}», de {{autor}} ({{fonte}}, {{licença}}), em `{{arquivo}}`. O que ela conta:
  {{a frase da bíblia}}.
- **Atos no tempo real** (do `index.html`): {{ato1 início–fim · …}}.
- **Viradas:** {{t · …}} (fins de bloco do `narracao-blocos.json` em que o ato troca).
- **Revelações**, com mergulho da trilha e golpe: {{t «palavra» · …}}.
- **Janela da aula** (do `brutos/narracao/aula-janela.json`): {{silencio_ini}}–{{silencio_fim}}. Nela, nenhum efeito, e
  a trilha sai (`trilha.fora`).

## Tempo

- O som trabalha em tempo real. As palavras, com o tempo real, estão em `sequencia/motion/briefings/palavras-voz.json`.
- Num evento, `"t"` é o tempo do código, o mesmo que o ato passa ao `a()`; o `efeitos.py` converte. `"t_real"` é o
  tempo do vídeo. `node sequencia/motion/briefings/tempo-real.cjs <t>` mostra a conversão.

## Leia antes

- `{{pasta desta skill}}/referencias/som.md`: a régua, a paleta com os IDs e as medidas.
- O `--help` do script que você usa: ele traz o formato do arquivo que o script lê.
- `{{pasta da série}}/biblia.md` e `{{ep}}/roteiro.json`; as batidas que os agentes de ato devolveram e os
  `compositions/atoN.html`.

## Você é dono de

`sequencia/som/` inteira (`trilha/`, `eventos/`, `sons/`, `paleta.json` se mudar, `mix.json`) e o arquivo de
`sequencia/exports/`. Você não edita `sequencia/motion/`.

## Comandos

```
uv run "{{pasta desta skill}}/scripts/montar_trilha.py" "{{ep}}/sequencia/som/trilha/planta.json" --grade
uv run "{{pasta desta skill}}/scripts/montar_trilha.py" "{{ep}}/sequencia/som/trilha/planta.json"
uv run "{{pasta desta skill}}/scripts/sons.py" --baixar "<link>" "{{ep}}/sequencia/som/sons/<arquivo da paleta>"
uv run "{{pasta desta skill}}/scripts/efeitos.py" "{{ep}}"
uv run "{{pasta desta skill}}/scripts/variar.py" "{{ep}}"
uv run "{{pasta desta skill}}/scripts/mixar.py" "{{ep}}/sequencia/som/mix.json" {{--sem-trilha, se só efeitos}}
uv run "{{pasta desta skill}}/scripts/mixar.py" "{{ep}}/sequencia/som/mix.json" --trecho <início> <fim>
uv run "{{pasta desta skill}}/scripts/medir.py" "<entrega>" --voz "{{ep}}/sequencia/motion/narracao.wav"
uv run "{{pasta desta skill}}/scripts/ganho_voz.py" "<entrega>" --voz "{{ep}}/sequencia/motion/narracao.wav"
uv run "{{pasta desta skill}}/scripts/ouvir.py" "<entrega>" --base "<sem trilha>" --de MM:SS --ate MM:SS
```

## Regras

- Sons só prontos: do Epidemic Sound, pelo conector (carregue `SearchSoundEffects`, `DownloadSoundEffect`,
  `SearchRecordings` e `DownloadRecording` com o ToolSearch), ou da pasta da pessoa, com a licença anotada. Som novo:
  anote título e ID para o `creditos.md`.
- Uns 40 a 50 efeitos à mão a cada 90 s; nenhum na janela da aula; roleta só no principal de cada ato.
- Junte os ajustes e mixe uma vez.
- O arquivo de chave você não abre nem copia. Você não fala com a pessoa, não abre arquivo para ela e não renderiza o
  vídeo.

## Devolva

Em até {{N}} linhas, sem colar código:

- **Trilha:** os trechos e as emendas da planta, o caminho da trilha editada e as revelações.
- **Efeitos:** o total e por ato, o que o `efeitos.py` tirou, o pico da soma e os sons novos, com título e ID.
- **Mix:** as medidas de `som.md` com os números e o caminho da entrega.

Esforço: high. Teto: uns {{N}} turnos.
