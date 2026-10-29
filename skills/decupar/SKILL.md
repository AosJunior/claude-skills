---
name: decupar
description: Decupagem de vídeo falado para Reels (talking head de celular ou câmera). Transcreve, tira retakes, gaguejos e pausas, aponta ganchos, deixa vertical, acerta a cor e entrega prévia, final com zoom e velocidade, legenda SRT, XML para Premiere/DaVinci e guia do CapCut. Use quando a pessoa mandar /decupar ou pedir para decupar, cortar pausas e erros, deixar vertical, corrigir a cor ou legendar um vídeo bruto.
---

# /decupar

A pessoa traz um vídeo bruto em que ela fala para a câmera (Reels 9:16, gravado no celular). Você
transcreve, julga o que fica, confirma uma vez e entrega o vídeo cortado com legenda e os arquivos
para o editor dela. Quem usa é leigo, no Claude Desktop, no Mac ou no Windows. Tudo em português.

O bruto só é lido: todo arquivo novo nasce em `<pasta do vídeo>/decupagem/`, e os scripts cuidam
disso. Se o caminho é um atalho (symlink) para o bruto, a decupagem nasce ao lado do atalho. Os scripts
ficam em `<pasta desta skill>/scripts/` (a pasta aparece quando a skill carrega).

**Pasta de edição**: o transcrever imprime `Marca: <caminho>` (a pasta `marca/` mais perto, subindo a
partir do vídeo) ou `Marca: nenhuma`. Com marca, leia o `marca/estilo.md` antes de decupar: a cor
(passo 2b), a velocidade e o zoom (passo 2c) saem de lá e valem mais que a receita da `/minha-edicao`.
Um caminho que começa com `marca/` no `cortes.json` aponta para essa pasta.

## Conversa

Frases curtas, sem termo técnico: "partes gravadas de novo", "pausas", "começo forte". Antes de cada
etapa que demora, diga quanto tempo leva:

| Etapa | Mac com chip M | Windows ou Mac Intel |
|---|---|---|
| Primeira vez: instala o Whisper e baixa o modelo (cerca de 2 GB) | 5 a 15 min, depende da internet | igual |
| Transcrever | uns 10 s por minuto de vídeo | 1 a 2 min por minuto de vídeo |
| Prévia (e cada correção) | 5 a 15 s por minuto de vídeo | cerca de 1 min por minuto |
| Prévia com velocidade ou zoom | uns 20 s por minuto de vídeo final; uma correção refaz só o que mudou | 1 a 2 min por minuto |
| Vídeo final 1080×1920 | uns 15 s por minuto de vídeo (bruto 4K: uns 90 s por minuto de vídeo final) | 1 a 2 min por minuto |
| Vídeo final com velocidade ou zoom (bruto 4K) | uns 80 s por minuto de vídeo final; uma correção refaz só o que mudou | 3 a 5 min por minuto |
| Achar o rosto (vídeo horizontal; na primeira vez instala o OpenCV, uns 50 MB) | 20 a 40 s | 1 a 2 min |
| Medir a cor e montar a folha antes × depois | menos de 10 s | uns 30 s |

A única pergunta do fluxo é a confirmação do mapa de cortes (passo 3). O resto você executa.

## 0. Conferir o ambiente

```
ffmpeg -version
uv --version
```

Os dois respondem igual no Terminal do Mac, no PowerShell e no Git Bash. Se um faltar, diga em uma
linha o que falta e para que serve, e ofereça instalar; instale só depois do sim:

- Mac: `brew install ffmpeg uv`. Sem o `brew`, a pessoa instala o Homebrew colando no Terminal o
  comando do site brew.sh (ele pede a senha do Mac, então é ela quem roda).
- Windows: `winget install Gyan.FFmpeg astral-sh.uv` (aceite os termos se ele perguntar). Depois a
  pessoa fecha e abre o Claude: o Windows só enxerga programa novo numa janela nova.

Pronto quando os dois comandos respondem com a versão.

## 1. Transcrever

Pegue o caminho do vídeo (a pessoa arrasta o arquivo para o chat ou diz onde está). Pasta com vários
vídeos: pergunte qual, um por vez. Se forem partes do mesmo vídeo, na ordem (bruto1, bruto2...), junte sem
recomprimir e decupe o arquivo junto. A emenda mantém o giro do iPhone:
`ffmpeg -f concat -safe 0 -i lista.txt -map 0:v:0 -map 0:a:0 -c copy bruto-completo.MOV`, com `lista.txt`
trazendo uma linha `file 'bruto1.MOV'` por parte.

```
uv run "<pasta desta skill>/scripts/transcrever.py" "<vídeo>"
```

Rode com tempo-limite de 10 minutos. Na primeira vez da máquina (instala o Whisper e baixa o modelo)
ou num vídeo longo no Windows, rode em segundo plano e espere o aviso de término.

Ele imprime a pasta da decupagem, a marca, o vídeo (duração, tamanho), as pausas e as **pistas**. No
fim solta em segundo plano uma cópia leve do vídeo, que deixa a prévia e as correções rápidas; siga
sem esperar. Rodar de novo com o mesmo vídeo usa o cache e leva menos de 1 s.

Pronto quando ele imprime "Pronto" e a `decupagem/transcricao.txt` existe.

## 2. Decupar (você julga)

Leia a `transcricao.txt` inteira e resolva cada pista antes de cortar:

- **voz sem texto** ou **tempos quebrados**: escute de novo só aquele pedaço (uns 10 s):
  `uv run "<pasta desta skill>/scripts/transcrever.py" "<vídeo>" --ouvir 01:28,2 01:30,6`.
  Se ele ouvir uma fala que faltava ou estava errada, rode o mesmo comando com `--trocar` no fim: a
  transcrição é corrigida e as frases renumeradas. O Whisper costuma pular justamente a fala
  repetida, que é o retake.
- **possível retake**: é sugestão; confirme lendo as duas frases.

Depois decida, frase por frase:

- **Retake**: a mesma ideia dita mais de uma vez fica na **última versão boa** (completa, sem
  tropeço). Sai junto o que foi dito entre as versões ("pera", "de novo", "corta").
- **Frase recomeçada ou palavra cortada**: fica a partir do recomeço.
- **Gagueira dentro da frase** sai com `F:n`: o trecho começa ou termina numa palavra
  (`{"de": "F3:2", "ate": "F3:fim"}` tira o "até até" do começo da F3). Palavras que emendam na voz
  ("Aí, até") saem juntas ou ficam juntas.
- **Começo e fim**: o vídeo começa na primeira frase útil e termina na última (CTA incluído).
- **A fala é da pessoa**: tire só retake, tropeço e o que ela pediu. Pedido de "cortar mais" ou "acelerar" vira
  proposta (as frases e o tempo ganho) e espera o sim; nunca corte frase boa por conta própria. Deixe o respiro
  natural no fim da frase: pausa apertada demais soa cortada.
- **Pausas e respingos**: o corte tira sozinho as pausas maiores que `pausa_max` e os sons sem
  palavra dentro da frase, e acha a borda de cada fala pelo volume (`"bordas": "som"`). A sua lista
  é só de trechos.
- **Ganchos**: as 3 frases que poderiam abrir o Reel (afirmação forte, número, promessa, conflito),
  com o tempo no vídeo cortado e o porquê.
- **Imagem ou grafismo**: listas, números, exemplos e nomes de ferramenta, com o tempo no vídeo
  cortado e o que mostrar.

Grave o `cortes.json` (formato no fim) e confira na hora a duração antes e depois e o tempo de cada
frase no vídeo cortado:

```
uv run "<pasta desta skill>/scripts/cortar.py" "<pasta decupagem>" --resumo
```

Escreva a `decupagem.md` com esses números (modelo abaixo): o que saiu leva o tempo do bruto; ganchos
e grafismos, o tempo do vídeo cortado.

Pronto quando cada frase F da transcrição está dentro de um trecho do `cortes.json` ou aparece em
"O que saiu" da `decupagem.md` com o motivo.

## 2a. Vertical (só se o vídeo for horizontal)

O transcrever imprime a orientação já com o giro do arquivo aplicado (iPhone deitado com giro de 90° na
tela é vertical: fica como está). Se ele disser **horizontal** e o destino for Reel:

```
uv run "<pasta desta skill>/scripts/enquadrar.py" "<pasta decupagem>"
```

Ele olha 12 quadros dos trechos, acha o rosto e grava o centro do recorte 9:16 (a mediana: se a pessoa
se mexe, vale a posição do meio). Abra a `enquadrar.jpg` (Read): a parte clara é o que fica. Ponha no
`cortes.json` `"vertical": true`. Se o rosto não foi achado ou a janela corta a pessoa, escreva o centro
à mão olhando a folha: `"vertical": {"centro_x": 0.42}` (fração da largura, 0 = borda esquerda).
Prévia e final saem 9:16 (608×1080 e 1080×1920). Confira 3 quadros do final antes de entregar.

## 2b. Cor saudável (opcional, leve)

Ofereça na confirmação (passo 3), junto com o mapa: "Quer que eu acerte a cor também? Fica leve."
Ordem fixa: primeiro **corrigir** (exposição só se estiver escuro ou claro demais; branco, que tira o
tom puxado da luz), depois **um look só**, leve, com a pele rosada e natural. O look vem do
`estilo.md` da marca ou do que ela disser do filtro dela:

- **LUT da marca** (a `/minha-edicao` copia a cor do CapCut da pessoa para um `.cube`): já traz a
  correção, então `"corrigir": false`.
  ```json
  "cor": {"corrigir": false, "look": {"lut": "marca/cor/look.cube"}}
  ```
- **Look por números**:
  ```json
  "cor": {"corrigir": true,
          "look": {"nome": "Gastronômico + Verão Italiano", "contraste": -4, "sombra": -2, "calor": 0.55, "saturacao": -5}}
  ```
  `contraste` e `sombra` na escala do CapCut (-50 a 50; o script limita a ±20). `calor` de 0 a 1 é o
  tom quente suave que aproxima filtros quentes do CapCut. `saturacao` de -10 a 5 (opcional).
- Sem look: só `"corrigir": true`. Sem correção: `"corrigir": false` e o look.

```
uv run "<pasta desta skill>/scripts/cor.py" "<pasta decupagem>"
```

Ele mede, grava o filtro e monta a `cor-antes-depois.jpg` com 2 quadros do vídeo cortado (em cima
antes, embaixo depois). Abra (Read) e olhe a pele: rosada e natural, sem laranja nem cinza. Com
"ATENÇÃO" (cor subiu mais de 10% ou ficou lavada), baixe o `calor` ou ponha `saturacao` -3 a -5 e
rode de novo. O cortar.py aplica a mesma cor na prévia e no final.

## 2c. Ritmo: velocidade e zoom (quando o estilo pede)

Use o que o `estilo.md` disser; sem estilo, só se a pessoa pedir.

- `"velocidade": 1.2` acelera vídeo e voz juntos (a voz não afina). Todo tempo que o script imprime
  já sai acelerado.
- `"zoom"`: `ancora` é o ponto dos olhos no quadro (fração `[x, y]`; olhe um quadro da prévia),
  `niveis` são os níveis do estilo e `alternar_na_pausa: true` troca o nível em cada pausa tirada
  dentro de um trecho, o que esconde o pulo da emenda. Cada trecho ganha um `"zoom"`: 1.0 na fala
  normal, o maior nos números e nas frases de ênfase.

Com velocidade ou zoom, o vídeo sai em pedaços guardados em `.dados/`: a primeira vez demora mais e
cada correção refaz só os pedaços que mudaram.

## 3. Confirmar

Pedido completo (decupar, inserir e sonorizar de uma vez): siga o grilling da `/inserir` antes de cortar, e não
gere o final em 1080 aqui; ele sai uma vez só, no fim.

Mande no chat: antes → depois, de 3 a 6 itens do que saiu, os 3 ganchos e uma pergunta só: "Gero a
prévia assim? Se quiser mudar, é só dizer (por exemplo: 'tira a frase sobre X', 'abre com o gancho
2')." Se ela pedir mudança, aplique como no passo 5, rode o `--resumo` e confirme em uma linha.

## 4. Entregar

```
uv run "<pasta desta skill>/scripts/cortar.py" "<pasta decupagem>"
```

Gera `previa.mp4` (1080 de altura, rápida, para conferir), `legenda.srt`, `premiere.xml`,
`capcut.md` e `palavras-corte.json` (o tempo de cada palavra no vídeo cortado, que a `/inserir`, a
`/sonorizar` e a `/criticar` leem). Se a cópia leve ainda estiver sendo feita, ele espera por ela.

Pronto quando ele imprime a duração da prévia sem "ATENÇÃO" (e "com cor" ou "recorte 9:16" quando
pediu). Com "ATENÇÃO", rode de novo uma vez; se repetir, conte à pessoa que a prévia saiu com duração
diferente da esperada.

Entregue assim, uma linha por arquivo:

- `previa.mp4`: o vídeo cortado, para conferir. Vai sem legenda na imagem.
- `legenda.srt`: a legenda no tempo do vídeo cortado, em frases curtas.
- `premiere.xml`: abre já cortado no Premiere (Arquivo → Importar) ou no DaVinci (Arquivo → Importar
  → Linha do tempo), usando o vídeo original, que fica onde está.
- `capcut.md`: o passo a passo para o CapCut no computador.
- `decupagem.md`: o que saiu e por quê, ganchos e onde cabe imagem.

E ofereça o final: "Quer o vídeo final em 1080×1920 para publicar? Leva uns N min." Com o sim, rode
o mesmo comando com `--final` (tempo-limite de 10 minutos), que grava `final.mp4` a partir do original.

Confira as emendas transcrevendo o vídeo cortado (uns 20 s): `uv run "<pasta desta skill>/scripts/transcrever.py"
"<pasta decupagem>/final.mp4"` (ou a prévia), copiado antes para uma pasta à parte, para não misturar
com a decupagem do bruto. Compare com o texto esperado. Uma sobra de palavra ou um fim comido se
acerta em `ajustes` (`"T5.de": 0.05` começa o 5º trecho 50 ms depois; `"T5.ate": 0.05` termina 50 ms
depois), e o `--final` refaz só aquele pedaço.

Com a `/criticar` instalada (ela aparece na sua lista de skills), rode-a no `final.mp4` antes de
entregar: ela mede emendas, gagueira, quadros soltos e volume e diz quais `ajustes` pôr no
`cortes.json`. Aplique e rode o `--final` de novo.

## 5. Corrigir

A pessoa diz em texto o que mudar. Edite o `cortes.json` e a `decupagem.md` e rode o `cortar.py` de
novo (com `--final` se ela já tinha o final). A transcrição fica em cache: só o corte refaz.

- "Tira tal frase": divida o trecho em volta dela.
- "Abre com o gancho N": ponha o trecho do gancho no topo da lista e tire-o do lugar antigo. Se ele
  continuar nos dois lugares, o script avisa que a fala aparece duas vezes.
- "Ficou corrido": suba `pausa_max` para 0.35 ou 0.5. "Ainda tem pausa": desça para 0.18.
- Gesto ou sorriso sem fala no fim: trecho com `"exato": true`.

## cortes.json

```json
{
  "pausa_max": 0.22,
  "bordas": "som",
  "trechos": [
    {"de": "F2", "ate": "F9", "nota": "abertura"},
    {"de": "F14:2", "ate": "F17", "nota": "segunda versão da explicação (F10–F13 saíram) sem o 'eu eu'"},
    {"de": "F30", "ate": "02:41,00", "exato": true, "nota": "fica o sorriso do fim"}
  ]
}
```

- A ordem da lista é a ordem do vídeo final. `de` e `ate` são do vídeo bruto: a frase (`"F12"`), uma
  palavra dela (`"F12:3"`, `"F12:loja"`, `"F12:fim"`), o tempo `"mm:ss,cc"` ou segundos.
- Fica a palavra cujo meio cai dentro do trecho. `"exato": true` usa `de` e `ate` como estão.
- Opcionais: `"vertical"` (passo 2a), `"cor"` (passo 2b), `"velocidade"` e `"zoom"` (passo 2c),
  `"ajustes"` (passo 4).
- A referência completa (todas as âncoras, zoom, bordas, render em pedaços) está em
  `<pasta desta skill>/referencia.md`. Leia quando for usar um campo pela primeira vez.

## decupagem.md

```markdown
# Decupagem: <nome do vídeo>

**Antes:** 2 min 45 s → **Depois:** 1 min 58 s (saíram 47 s)

## O que saiu e por quê
- 00:12–00:31 (F4–F7): primeira tentativa da explicação sobre X; ficou a segunda, mais completa.
- Pausas: 31 s de respiro e silêncio, tirados pelo corte.

## Ganchos para abrir o Reel (tempo no vídeo cortado)
1. **00:39** «frase» — por que prende.

## Onde cabe imagem ou grafismo (tempo no vídeo cortado)
- 00:22 «três ferramentas…»: lista na tela.

## Confira
- O que a pessoa deve ouvir antes de publicar (pistas que ficaram em aberto).
```

## Limites

- A legenda sai só como `.srt`. O ffmpeg do Homebrew não desenha texto na imagem, então a prévia vai
  sem legenda queimada; a legenda na imagem é da `/inserir` ou do editor da pessoa.
- Vídeo HDR do iPhone: se o ffmpeg não converter as cores (o script avisa), a prévia pode sair com
  cor diferente. O `premiere.xml` usa o original, com a cor certa.
- O `premiere.xml` aponta para o vídeo original. Se ele mudar de lugar, o editor pede para localizar.
- Recorte 9:16, cor, velocidade e zoom saem só na prévia e no final (mp4). O `premiere.xml` abre na
  geometria do bruto, em 1× e sem cor: no Premiere, use Sequência → Reenquadramento automático, o
  Lumetri e a Velocidade/Duração com os mesmos valores.
- Os pedaços do final com velocidade ou zoom ficam em `.dados/pedacos-final/` (uns 25 MB por segundo
  de vídeo final). Depois de publicar, a pasta pode ser apagada.

## Esforço

Esta etapa é mecânica: rode em esforço **low ou medium**. Agentes que você abrir para ela usam `effort: "low"`.
