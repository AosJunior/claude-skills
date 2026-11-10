# Som: trilha, efeitos, mixagem e medidas

A régua de som da novela. O episódio sai numa **mix só**: com trilha ou só com efeitos, como a bíblia diz. O formato de
cada arquivo (`planta.json`, `eventos/<ato>.json`, `mix.json`) está no `--help` do script que o lê. `<ep>` é a pasta
do episódio; `<voz>` é `<ep>/sequencia/motion/narracao.wav`.

## A régua

- **A voz manda.** A voz recebe só passa-altas e compressor suave. Trilha e efeitos ficam abaixo dela. Tratamento
  pesado (redução de ruído, EQ, compressor 3:1) já subiu o ruído e foi reprovado.
- **A trilha faz efeito nas subidas e nos golpes**, e não no volume sob a fala: a −19 LU sob a fala ela «não fazia
  efeito»; a −15,5, ficou «muito alto, eu não consegui ouvir».
- **Efeito é pontuação com motivo:** cada um nasce de algo que acontece na imagem, e é um som pronto.
- **A aula toca sozinha.** Na janela da aula (`aula-janela.json`), a voz de quem vende fica sem música e sem efeito
  por cima (proposta, a calibrar no piloto).

## Trilha

Só se a bíblia diz «com trilha». Uma trilha por série, a mesma em todos os episódios, para a série ter assinatura.

### Escolher

Antes de buscar, escreva em uma frase o que a música conta nesta série («comédia de costumes com prazo correndo»). A
busca por estilo no catálogo, sem referência, já foi reprovada duas vezes («mais com formato de rede social»). Procure
pelo dado real, nesta ordem:

1. **A música de um vídeo de referência** que a pessoa aponta: separe a voz e passe a música num identificador
   (Shazam) em várias janelas. Se nenhuma reconhece, é música de biblioteca e esse caminho acaba.
2. **O áudio em alta** no Instagram, quando houver como medir.
3. **Parecida com uma que já deu certo.** No conector do Epidemic Sound, `SearchExternalReferences` acha a música
   conhecida e `SearchSimilarToRecording` traz as parecidas do catálogo.

Mande duas ou três para a pessoa ouvir no piloto, e ela escolhe. Música de referência que não é do catálogo fica só
local, para comparar, e nunca entra no export. Música comercial no arquivo pode deixar o Reel mudo.

### Editar no compasso

`montar_trilha.py` corta a música no compasso para a estrutura do episódio:

1. `uv run "<pasta desta skill>/scripts/montar_trilha.py" "<ep>/sequencia/som/trilha/planta.json" --grade` lista os
   compassos (índice e segundo).
2. Ouça os trechos candidatos e escreva a `planta.json`: um trecho por momento, cada um começando num compasso.
3. Rode sem `--grade`, para montar.

O que funciona:

- o golpe mais forte da música cai na palavra-chave da abertura;
- a música muda junto com o ato: cada trecho entra na virada (emenda `compasso`);
- revelação com emenda `mergulho`: a música afunda logo antes e o trecho novo entra no ataque;
- a música para antes da aula e volta depois dela, num compasso forte;
- o cartão das duas opções repete os compassos mais intensos, com o golpe forte depois da última palavra;
- esticar só o necessário para caber em compassos inteiros (0,97 a 0,98);
- depois de uma pausa inserida ([`voz.md`](voz.md), «Segurar a tela»), a emenda anda em tempos inteiros da música.

### Nivelar

O `mixar.py` não abaixa a música por igual: um nivelador segue o volume dela de 400 em 400 ms e a leva a uma
curva-alvo, em LU abaixo da voz:

| Momento | Alvo | Campo do `mix.json` |
|---|---|---|
| Sob a fala | −20,3 (nenhum trecho de 400 ms passa de −20) | `trilha.sob_fala` |
| Respiros de 0,5 s ou mais, viradas e depois da última palavra | −7,5; sobe 0,15 s depois da palavra e desce 0,15 s antes da seguinte | `trilha.respiro` |
| Os 0,35 s antes de cada revelação | −36 (o mergulho); volta no ataque | `trilha.revelacoes` |
| Um trecho em crescendo | rampa entre dois valores, até −18,5 sob a fala | `trilha.crescendos` |
| A janela da aula | a música sai | `trilha.fora`: `[[silencio_ini, silencio_fim]]` do `aula-janela.json` |

- **Revelações:** 3 ou 4 a cada 90 s, nos momentos em que a tela dá a resposta (o desmentido, a lei). Cada uma precisa
  de uma emenda `mergulho` na planta, ou de um ataque forte da música, no mesmo instante.
- **As viradas saem do `narracao-blocos.json`:** o fim de um bloco quando o seguinte é de outro ato.
- A curva calculada fica em `sequencia/som/.dados/curva-trilha.json`.

| Pedido | Ajuste |
|---|---|
| «Música mais baixa» | `sob_fala` −21 ou −22 |
| «Música mais alta» | `sob_fala` −19,5; nunca acima de −19 |
| «A música não faz efeito» | `respiro` −6,5, ou mais revelações com golpe |

## Efeitos

### Sons prontos

Efeito é sempre um som pronto, usado como está: só cortado e alinhado. A roleta montada tique por tique foi
reprovada como «bem ruim». Para efeito de nome comum (roleta, notificação, aplauso), procure o som pronto.

- **Baixar** pelo conector do Epidemic Sound (`DownloadSoundEffect` com o ID; carregue as ferramentas
  `SearchSoundEffects`, `DownloadSoundEffect`, `SearchRecordings` e `DownloadRecording` com o ToolSearch). O link vale
  minutos; baixe na hora, com o nome que a paleta pede:
  `uv run "<pasta desta skill>/scripts/sons.py" --baixar "<link>" "<ep>/sequencia/som/sons/<arquivo>"`.
- **Sem o conector:** sons que a pessoa já tem (com a licença anotada), a Biblioteca de áudio do YouTube ou o
  Pixabay, salvos com os nomes da paleta. `sons.py <pasta>` lista os sons com duração e volume.
- O `efeitos.py` lista o que falta, com o título e o ID, e para. Som novo, fora da paleta: anote título e ID para o
  `creditos.md`.
- Na série, os sons baixados no ep. 1 servem aos seguintes: copie `sequencia/som/sons/` do episódio anterior.

### Paleta inicial

A fonte da verdade é o `scripts/paleta.json`: arquivo, corte, ponto que alinha e volume de cada tipo. Para mudar numa
série, copie para `<ep>/sequencia/som/paleta.json` e edite lá. Na novela, a camada de jogo pede sons de interface de
jogo (cartão, brilho) mais que de telejornal; troque os arquivos, não os tipos.

| Tipo | Quando usar | Vol |
|---|---|---|
| `virada` | troca de lugar ou de ato: o pico cai no fim da saída, dentro do respiro | −3 |
| `camera` | empurrão ou chicote que viaja; pico no meio do movimento; no máximo 3 no episódio | −5 |
| `golpe` | o desmentido, a lei, a frase que bate | +4 |
| `grave` | só o impacto: reforço de uma batida da música (`so_com_trilha`) | +2 |
| `subida` | tensão antes de uma revelação: corta seco no instante | +1 sob a fala, +3 no respiro |
| `cartao` | etiqueta, balão, emote ou cartão que entra. Var 1: clique seco; var 2: toque grave; var 3: pop de vidro | +1 |
| `brilho` | algo acende com motivo forte (o medidor sobe, a opção certa da personagem) | −3 |
| roleta | o relógio ou o medidor que gira, quando é o principal do ato (`"principal": true`) | −2 |

| Arquivo em `sequencia/som/sons/` | Título no Epidemic Sound | ID | Tipo |
|---|---|---|---|
| `whoosh-grave.wav` | Swooshes, Whoosh, Deep, Low, Cinematic | 689b1489-8811-4963-a9af-28187d5c7486 | virada |
| `whoosh-ar.wav` | Swooshes, Whoosh, Designed, Generic, Air | c406a00b-d4b3-42e9-ba76-707ba5174543 | camera 1 |
| `whoosh-digital.wav` | Swooshes, Whoosh, Designed, Digital, Wide | 042c787b-68bb-41da-849c-c8ec42b16763 | camera 2 |
| `whoosh-curto.wav` | Swooshes, Whoosh, Short, Deep Reversed, Dry | 14f0f3a4-cc2b-4d8b-b453-49fd070c591d | golpe |
| `impacto-grave.wav` | Designed, Boom, Low Hit | 6d82b75c-2d2f-40b3-9e1b-4d822c1173d5 | golpe, grave |
| `subida.wav` | Designed, Riser, Metal Hit, Reverse, Build, Crescendo | 0e565244-d80e-4d88-801e-5183a6335937 | subida |
| `clique-seco.wav` | User Interface, Click, Hard, Short | db6b8aed-e2b5-4597-af29-088f0a3bd988 | cartao 1 |
| `toque-grave.wav` | User Interface, Alert, Pops, Plastic, Tap, Pops | ba6ef87a-a4ea-4901-bf6e-1311b3e3ddfa | cartao 2 |
| `pop-vidro.wav` | User Interface, Click, Pops, Glass, UI, Pops | 9da883ac-6b03-4df0-b8e6-cd85c7c926a5 | cartao 3 |
| `acorde-quente.wav` | Games, Video, GUI Menu Button, Select OK, Warm, Chorus, Chord | e40b6261-bc09-408b-94f5-e6a32b6ec0ae | brilho 1 |
| `tom-confirma.wav` | User Interface, Alert, Tonal, Digital Button Confirm | 36f8a2b1-9eb9-4928-96f9-17f44e7c72fa | brilho 2 |
| `bipe-quente.wav` | User Interface, Alert, Notification, Beep, Confirmation, Warm | 5a7fde22-95f5-496a-962d-f8ee9369a270 | brilho 3 |
| `roda-de-premios.wav` | Mechanical, Roller, Wheel Spin, Wheel Of Fortune Style 01 | 97caed1c-c294-44b7-924a-e39906605838 | roleta |

### Roleta

O relógio e o medidor giram na roleta quando mudam ([`roleta.md`](roleta.md)), mas a roda de prêmios soa só no número
principal de cada ato, no máximo um. Marque no `eventos/<ato>.json`: `"roletas": {"<nome>": {"principal": true}}`.
Roleta sem principal gira muda, e o `efeitos.py` avisa. A roda é curta: 0,55 s de giro antes do último estalo forte,
mais 0,14 s de cauda; o estalo cai na última trava, e nenhum outro som vai em cima dele. `"vol": -60` deixa muda.

### Quantidade

O `efeitos.py` aplica sozinho e relata o que tirou:

- **Swoosh** (virada, câmera e o whoosh do golpe) só nas viradas e em até 3 câmeras, a 5 s ou mais um do outro.
  Quando dois brigam, ficam primeiro o `fixo`, depois a virada, o golpe e a câmera.
- **Repetição:** o mesmo arquivo a menos de 2 s do anterior sai.
- **Variações:** o evento sem `var` alterna sozinho; com `var`, vale a escolhida.
- **Som repetido varia de tom:** depois de cada `efeitos.py`, rode o `variar.py`, que dá a cada cartão um tom e um
  volume levemente diferentes (±1 semitom, ±1,5 dB, semente fixa). `"tamanho": "grande"` soa mais grave:
  `uv run "<pasta desta skill>/scripts/variar.py" "<ep>"`.
- **Pico** da soma dos efeitos em −1 dBFS ou menos.

O que fica com quem escreve os eventos:

- uns 40 a 50 efeitos à mão a cada 90 s (105 em 97 s já foi reprovado como «exagerado»);
- linhas que entram em cascata ganham um som só;
- `"fixo": true` no golpe da revelação principal, que nunca sai;
- nenhum efeito dentro da janela da aula;
- efeito não cai em cima da palavra que carrega a frase: vai para o respiro logo depois (um efeito na palavra-chave
  subiu 3,2 dB na faixa da fala e foi bloqueante).

| Na imagem | Evento |
|---|---|
| Etiqueta, balão ou emote pousa | `cartao` var 3 |
| O relógio ou o medidor muda (sem roleta principal) | `cartao` var 1 |
| Cartão cheio ou bloco assenta | `cartao` var 2 |
| Empurrão ou chicote | `camera`, pico no meio do movimento |
| Troca de ato | `virada` que sobe e corta seco no T da emenda, uma por emenda |
| O desmentido ou a lei pousa | `golpe` |
| A tensão sobe até a virada | `subida`, cortando no instante |
| Algo acende com motivo forte | `brilho` |
| Uma batida da música pede reforço | `grave` com `"so_com_trilha": true` |

Volume (`vol`): o pico do efeito fica em −12 + vol dBFS. Golpe a +4 ou +5; em cima da fala, mais baixo. Abaixo de −6
o efeito some.

## Mixagem

Um mapa só (`<ep>/sequencia/som/mix.json`), com o `video` apontando para o render de rascunho ou de entrega:

```
uv run "<pasta desta skill>/scripts/mixar.py" "<ep>/sequencia/som/mix.json"                 com trilha
uv run "<pasta desta skill>/scripts/mixar.py" "<ep>/sequencia/som/mix.json" --sem-trilha    só efeitos
uv run "<pasta desta skill>/scripts/mixar.py" "<ep>/sequencia/som/mix.json" --trecho <ini> <fim>   prévia de um pedaço
```

Rode só a forma que a bíblia pede. A saída vai para o campo `saida` (com trilha) ou `saida_sem_trilha` do `mix.json`;
aponte os dois para `../exports/<slug>-epNN.mp4`, sem número de versão.

- **Voz:** passa-altas e compressor suave 2:1, nada mais.
- **Trilha:** o nivelador da curva-alvo.
- **Efeitos:** limitador só no barramento deles (−1 dBFS), que também cede onde a soma passaria do teto.
- **Master:** ganho linear até −14 LUFS e limitador de pico verdadeiro (−1,5 dBTP). O loudnorm dinâmico mudava o
  volume ao longo do vídeo e saiu.
- **Prévia de um pedaço** (`--trecho`) sai em `sequencia/previas/previa-trecho.mp4`, no nível do vídeo inteiro. Junte
  os ajustes e mixe uma vez.

### Voz com pico

Uma palavra dita com força passa do pico que o limitador do master segura, e o ganho da voz varia mais de 0,3 dB.
Guarde a narração do projeto em `<ep>/brutos/narracao/narracao-pre-ganho.wav`, ponha um limitador suave só nela e mixe
de novo:

```
ffmpeg -i "<ep>/brutos/narracao/narracao-pre-ganho.wav" -af "alimiter=limit=0.5:attack=3:release=50:level=false:latency=true" -c:a pcm_s16le "<ep>/sequencia/motion/narracao.wav"
```

- A voz limitada fica no lugar da `sequencia/motion/narracao.wav`, e a medida é contra ela.
- Varra nos dois sentidos, de 0,06 em 0,06 em volta de `limit=0.5`: a curva não desce sempre.
- Quando nenhum valor fecha, quem pega a voz é o limitador do master, nos golpes de efeito. A até 0,05 dB acima da
  régua, a medida entra como MENOR, com o número na entrega.
- No zsh, o limite vai entre chaves numa variável (`limit=${L}:attack=3`): com `$L:attack`, o zsh lê o `:a` como
  modificador e o filtro quebra com «Undefined constant».
- O `latency=true` compensa o atraso do limitador: o tempo das palavras não muda.

## Medidas

A fala inteligível sozinha não basta (o `ouvir.py` deu 100 % numa trilha que ninguém conseguia ouvir por cima): quem
manda é o volume medido.

| Medida | Como | Alvo |
|---|---|---|
| Volume e pico | o fim do `mixar.py` | −14 LUFS (±0,5); pico de −1,5 dBTP ou menos |
| Ganho da voz | `uv run "<pasta desta skill>/scripts/ganho_voz.py" "<entrega>" --voz "<voz>"` | variação de 0,3 dB ou menos |
| Trilha sob a fala e nos respiros | `uv run "<pasta desta skill>/scripts/medir.py" "<entrega>" --voz "<voz>"` (só com trilha) | −21,5 a −19,5 sob a fala; −7 a −9 nos respiros de 0,8 s ou mais |
| Fala do narrador | `uv run "<pasta desta skill>/scripts/ouvir.py" "<entrega>" --base "<sem trilha>" --de MM:SS --ate MM:SS` | 95 % ou mais, numa janela que começa e acaba em pausa |
| Fala da aula | o mesmo `ouvir.py`, na janela `aula_ini`–`aula_fim` | 95 % ou mais |
| Soma dos efeitos | o fim do `efeitos.py` | pico de −1 dBFS ou menos |

- O `medir.py` precisa da versão sem trilha ao lado, pelo nome: rode uma vez `mixar.py --sem-trilha` para a medida,
  mesmo quando a entrega é com trilha, e apague essa cópia depois. O respiro com mergulho e a janela `fora` ficam fora
  da régua.
- Na entrega só com efeitos, a medida da trilha não se aplica, e o `ouvir.py` roda com a própria entrega como `--base`.

## Créditos

O `creditos.md` do episódio leva:

- a narração: narrador, modelo e velocidade;
- a trilha: título, autor, fonte e licença;
- cada efeito: arquivo, título, ID, licença («assinatura Epidemic Sound da conta conectada», ou a da fonte) e quantas
  vezes toca, contado no `efeitos.json`;
- o trecho da aula: de que vídeo, de quem, com a autorização.
