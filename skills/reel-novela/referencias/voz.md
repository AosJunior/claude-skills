# Voz: narração, alinhamento e mudanças depois das cenas

Como escolher o narrador, gerar e escolher os takes, montar a narração, tirar o tempo de cada palavra e mexer na voz
depois que as cenas existem, sem gastar crédito à toa. O formato do `roteiro.json` e as regras da `fala` estão em
[`../modelos/roteiro-episodio.md`](../modelos/roteiro-episodio.md); as opções de cada comando, em
`uv run "<pasta desta skill>/scripts/narrar.py" --help`. `<ep>` é a pasta do episódio (`<pasta da série>/epNN`).

## Narrador

A voz se decide uma vez por série, no portão 1, ouvindo amostras, e fica fixa: cenas presas a uma voz que depois foi
trocada tiveram de ir para o tempo da voz nova.

- **Candidatos:** `narrar.py vozes --genero masculino` (ou `feminino`) lista os narradores em português da
  biblioteca do ElevenLabs, os mais usados primeiro, sem gastar crédito. Para novela, procure `narrative_story` e uma
  voz com cor (grave e dramática, ou leve e irônica, conforme o tom da bíblia).
- **Amostras:** 2 ou 3 narradores com uma frase do piloto, marcas de emoção incluídas:
  `uv run "<pasta desta skill>/scripts/narrar.py" amostras --texto "<frase>" --vozes <id,id,id> --saida "<pasta da série>/amostras"`.
  Abra para a pessoa os `-x1.25.wav`: já estão na velocidade do vídeo. O `voice_id` escolhido vai para a bíblia e para
  o campo `voz` de cada `roteiro.json`.
- **«A voz não está disponível na sua conta»:** `narrar.py vozes --adicionar <voice_id>` e rode de novo.

## Modelo, velocidade e estabilidade

- **eleven_v4** é o padrão: o mais expressivo em português. Ganhou o teste no mesmo ritmo contra o eleven_v3 (sem
  emoção, lento, voz variando) e o eleven_multilingual_v2 (bem menos expressivo; só quando a fala precisa caber num
  tempo fixo). Ele aceita só estabilidade e semelhança (0,75); não tem ajuste de velocidade. A `velocidade` do
  roteiro (1,2 a 1,3, padrão 1,25) é aplicada depois, com `atempo`, sem mudar o tom.
- **Estabilidade** (`--estabilidade`): 0,5, o natural. O 0 faz a voz variar e não resolve falta de emoção (a emoção
  vem das marcas); o 1 obedece menos às marcas. Mudar a estabilidade gera takes novos.
- **Saída** em mp3 de 192 kbps; se o plano não deixar, o script cai para 128.

## Marcas de emoção

Entre colchetes, em inglês, antes da frase que muda de tom; pelo menos uma por bloco. O modelo lê a marca como
direção, sem falar. A ênfase vem delas, e não de maiúsculas na `fala`.

| Marca | Serve para |
|---|---|
| `[excited]` | a abertura, o número que impressiona, o pedido do fim |
| `[mischievously]` | a quebra («só que…»), a mentira da personagem |
| `[sarcastic]` | o desmentido seco, na novela |
| `[curious]` | a pergunta que abre um bloco |
| `[serious]` | o dado que pesa, o prazo |
| `[dramatic]` | a revelação, a virada |
| `[confident]` | a explicação depois da pergunta |
| `[calm]` | o fecho, antes do pedido |

`[whispers]` também funciona. `[sighs]`, `[laughs]` e `[crying]` viram som (suspiro, riso, choro): use só quando a
história pede esse som.

## Takes

- **Um take é o roteiro inteiro**, numa geração só, com um parágrafo por bloco: a voz fica a mesma do começo ao fim.
  O script acelera o take, alinha (o alinhamento fica ao lado do take e só serve ao corte) e corta nos blocos, no meio
  do silêncio entre eles.
  `uv run "<pasta desta skill>/scripts/narrar.py" narrar "<ep>/roteiro.json" --saida "<ep>/brutos/narracao" --takes 2`
- **Quantos:** 2 no começo. Cada take gasta em crédito os caracteres da `fala` do roteiro inteiro (uns 1.600 num
  episódio de 70 s). O script mostra o total antes de gerar e o saldo no fim.
- **Reaproveitamento:** o take é guardado pela fala, voz, modelo e estabilidade. Trocar o `"take"` e rodar o `narrar`
  de novo não gasta nada. Mudar a `fala` de um bloco gera o roteiro inteiro de novo; os takes antigos ficam em
  `takes/`.
- **Escolha:** `uv run "<pasta desta skill>/scripts/narrar.py" conferir "<ep>/brutos/narracao"` transcreve cada bloco
  de cada take com o Whisper, sem dar o texto como dica, e compara com a `fala` («pra» e «para» contam igual). O take
  que entra vem marcado com `*`: texto igual em todos os blocos e mais entonação (desvio do tom, em semitons). Se for
  outro, ponha `"take": <n>` na raiz do roteiro e rode o `narrar` de novo, que remonta sem gastar. Um take só para o
  vídeo todo.
- **Sem dica, de propósito:** com o texto como dica, o Whisper completava a palavra que a voz engoliu, e um artigo
  perdido passava como texto igual.
- **O que não é erro:** nome próprio com outra grafia («trocou X → Y»), porque a `fala` escreve o nome como ele soa;
  palavra estrangeira dita como no idioma dela. Repetição de palavra aparece como «sobrou».
- **Nenhum take passou:** gere mais um (`--takes 3`), que é o roteiro todo de novo.
- **Saída de emergência:** `"geracao": "blocos"` no roteiro volta a uma geração por bloco, e aí
  `--takes 3 --bloco <cena>` gera takes só de um bloco. A voz desse bloco pode soar diferente das outras.
- O `conferir` não ouve o tom. A pessoa ouve a narração inteira como prévia.
- A primeira conferência instala o Whisper: diga à pessoa que leva de 5 a 15 min.

## Montagem

O `narrar` acelera o take escolhido, encurta as pausas internas e junta os blocos:

| O quê | Padrão | Por quê |
|---|---|---|
| Pausa interna máxima | 0,35 s | pausas mais longas soaram lentas; 0,45 foi reprovado |
| Pausa interna máxima no 1º bloco | 0,45 s | a pausa dramática da abertura; 0,6 foi reprovado |
| Respiro entre blocos | 0,35 s | onde a trilha sobe e a cena vira; 0,55 soou lento |
| Silêncio no fim | 1,6 s | o golpe final e o cartão parado |

O `narracao-blocos.json` diz onde cada bloco começa e acaba. Dele saem as janelas dos atos (o `montar_projeto.py` lê)
e as viradas da trilha (o `viradas` do `mix.json`).

## Alinhamento

O tempo de cada palavra vem da própria narração, por alinhamento forçado: o ElevenLabs recebe o áudio e o texto exato
e devolve o início e o fim de cada palavra e de cada letra. O Whisper erra até 0,6 s em trechos longos, e com ele a
tela vinha atrasada do meio ao fim sem ninguém notar na prévia.

```
uv run "<pasta desta skill>/scripts/narrar.py" alinhar "<ep>/brutos/narracao/narracao.wav" "<ep>/roteiro.json" --saida "<ep>/brutos/narracao/palavras-voz.json"
```

O `palavras-voz.json` é uma lista `{"w": "2020,", "ini": 4.24, "fim": 4.98}`: `w` é a palavra como está no `texto`
(com a pontuação, é o que a legenda mostra); `ini` e `fim` são segundos da narração, que começa no 0 do vídeo. Número
ou sigla é uma palavra só, e o tempo cobre tudo o que a voz disse para ela. Ao lado fica o `palavras-voz-bruto.json`,
com o tempo de cada letra.

O alinhador recebe a `fala` sem as marcas e devolve as palavras do `texto`, casadas pelos números e siglas por extenso.
Por isso o `texto` diz as mesmas palavras da `fala`, na mesma ordem. No fim, o script valida na onda:

- nenhuma palavra começando dentro de uma pausa de 120 ms ou mais (até 60 ms antes passa, por consoante fraca);
- nenhuma palavra inteira em silêncio;
- a confiança (loss médio): perto de 0,5 é bom; bem acima de 1 indica `fala` e áudio diferentes.

Quando a validação acusa palavra: compare o `texto` e a `fala` do bloco, corrija o `texto` e alinhe de novo (com
`--resposta "<ep>/brutos/narracao/palavras-voz-bruto.json"`, sem chamar a API). Se o texto está certo, corrija o tempo
à mão no JSON (o começo é onde a voz volta, que o bruto mostra letra a letra) e confira com
`narrar.py validar "<narracao.wav>" "<palavras-voz.json>"`.

A aula entra depois do alinhamento, pelo `encaixar_aula.py` (`scripts/README.md`): ele abre o silêncio com o
`pausa.py`, soma os tempos depois dele e grava a janela em `aula-janela.json`.

## Tempo do código e tempo real

As cenas escrevem os tempos do `palavras-voz.json` da narração em que foram escritas: é o **tempo do código**. O
`assets/voz.js` leva o tempo do código ao **tempo real** da narração que está no vídeo, pelo `VOZ.w(t)`. Enquanto a
narração não muda, as âncoras do `voz.js` ficam vazias e os dois tempos são iguais.

- A legenda vive em tempo real: é gerada a partir do `palavras-voz.json` vigente, sem o `VOZ.w`.
- Para o snapshot de uma palavra e para o `data-start` de uma janela, use o tempo real:
  `node briefings/tempo-real.cjs <t> …`, em `sequencia/motion/`.
- O som trabalha em tempo real. Num `eventos/<ato>.json`, `"t"` é o tempo do código e o `efeitos.py` converte;
  `"t_real"` é para o que não está preso ao código.
- Ato nenhum usa número solto de tempo (nem para a janela da aula, nem para a barra): é o que quebra a reancoragem.

## Narração mudou depois das cenas

As cenas não mudam: mudam as âncoras do `voz.js`, e a legenda é gerada de novo. Os arquivos:

| Arquivo | O que é |
|---|---|
| `brutos/narracao/narracao.wav` e `palavras-voz.json` | o que a narração grava, refeito a cada narração |
| `sequencia/motion/narracao.wav` e `briefings/palavras-voz.json` | as cópias que o projeto, a legenda, os efeitos e a mixagem usam |
| `sequencia/motion/briefings/palavras-cenas.json` | o tempo em que as cenas foram escritas: criado na primeira troca e nunca mais mudado |

Para a **segunda voz** do mesmo episódio (outro narrador, mesmas cenas), o `segunda_voz.py` faz tudo isto sozinho
numa cópia do projeto (`scripts/README.md`). À mão, para uma narração nova no mesmo projeto:

1. Na primeira troca, copie `briefings/palavras-voz.json` para `briefings/palavras-cenas.json`.
2. Narre e alinhe de novo; encaixe a aula de novo, se houver.
3. Copie as duas saídas novas por cima das cópias do projeto.
4. Leve as âncoras do `voz.js` ao tempo novo:
   `uv run "<pasta desta skill>/scripts/ancorar.py" "<ep>/sequencia/motion/briefings/palavras-cenas.json" "<ep>/sequencia/motion/briefings/palavras-voz.json" "<ep>/sequencia/motion/assets/voz.js" --fixa <fim antigo>=<fim novo>`
5. Rode o `montar_projeto.py` de novo: ele refaz as janelas, a barra e a legenda e não toca nos `atoN.html`.
6. Refaça os snapshots das palavras que mudaram, os efeitos, o render e a mixagem.

O que o `ancorar.py` faz e o que conferir:

- **Pareamento pela palavra.** Cada palavra igual nas duas réguas vira o par [tempo escrito, tempo novo], pelo começo
  da palavra. Palavra que mudou no `texto` fica sem âncora e sai da interpolação, sem desalinhar o resto.
- **Âncora fixa** (`--fixa ESCRITO=NOVO`) vale mais que o alinhador. Use no fim do vídeo (duração antiga=nova), em
  cada letra de uma sigla animada letra a letra e no começo e no fim do silêncio da aula.
- **Saltos.** Um bloco que muda de lugar deixa um salto no deslocamento, e a palavra curta da emenda («e», «a») pode
  casar com o bloco errado. O script lista cada salto: a emenda e a palavra que abre o bloco seguinte ganham `--fixa`
  com o tempo real delas. Confira com o node o `VOZ.w` de uns 15 tempos-chave: cada emenda, a primeira palavra de cada
  bloco e o fim.
- A batida presa ao fim de uma palavra pode escorregar onde a palavra mudou de duração: confira esses pontos no
  quadro.

## Segurar a tela

Quando a pessoa pede para a tela segurar mais («segura um segundinho a mais»), não narre de novo: ponha um silêncio na
narração aprovada e congele o ato durante ele.

1. Escolha o instante entre duas palavras, pelo `palavras-voz.json`, e rode
   `uv run "<pasta desta skill>/scripts/pausa.py" "<ep>" --em <s> --s <duração>`. O script põe o silêncio na
   `brutos/narracao/narracao.wav`, soma a duração aos tempos depois dele e guarda os originais.
2. Siga os passos 1, 3 e 4 de «Narração mudou depois das cenas», com dois `--fixa` no `ancorar.py`:
   `--fixa T=T --fixa T+0.01=T+0.01+<duração>`, em que `T` é o tempo do código em que o ato já assentou e a saída
   ainda não começou. O script imprime os valores.
3. Rode o `montar_projeto.py` (janelas e legenda) e refaça os efeitos, o render e a mixagem.
4. Na trilha, a emenda depois da pausa anda em tempos inteiros da música, para o respiro ter música cheia
   ([`som.md`](som.md), «Editar no compasso»).

## Crédito e chave

- **Gastam crédito:** `amostras` (os caracteres do trecho, uma vez por voz) e `narrar` (só os takes que ainda não
  existem, mais o alinhamento de cada take novo). O `alinhar` gasta pouco. `vozes`, `conferir` e `validar` não gastam.
- Diga a conta à pessoa antes de narrar: caracteres da `fala` do roteiro inteiro × takes.
- **Chave:** `ELEVENLABS_API_KEY` no ambiente, ou `--chave-arquivo "<arquivo>"` em cada comando do `narrar.py`. O
  script lê só essa linha e nunca imprime a chave. O arquivo da chave ninguém abre nem copia, e o briefing de um agente
  não leva a chave: leva o caminho do arquivo.

## Quando dá errado

| Sinal | Causa provável | O que fazer |
|---|---|---|
| 401 | chave errada ou vencida | peça a chave certa à pessoa |
| «Acabaram os créditos» | saldo do plano | os takes prontos ficam; diga quanto falta e espere a pessoa |
| Palavra repetida no take | reticências ou frase longa | vírgula ou ponto no lugar, e takes novos |
| Número lido errado | algarismo na `fala` | escreva por extenso na `fala` |
| Nome pronunciado errado | grafia que a voz não conhece | na `fala`, escreva como soa; no `texto`, a grafia certa |
| Voz mudou de um bloco para outro | takes misturados, geração por blocos ou estabilidade 0 | um take inteiro só, `"geracao": "inteira"` e estabilidade 0,5 |
| Narração sem emoção ou lenta | modelo antigo ou ritmo lento | eleven_v4 a 1,25 e marcas de emoção |
| Palavra da abertura estranha | maiúsculas de ênfase na `fala` | tire as maiúsculas e ponha a ênfase numa marca |
