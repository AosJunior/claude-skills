---
name: decupar
description: Decupagem de vídeo falado para Reels (talking head de celular ou câmera). Transcreve, tira retakes e pausas, aponta ganchos, recorta 9:16 no rosto quando o vídeo é horizontal, faz correção de cor leve (opcional) e entrega prévia cortada, legenda SRT, XML para Premiere/DaVinci e guia do CapCut. Use quando a pessoa mandar /decupar ou pedir para decupar, cortar pausas e erros, deixar vertical, corrigir a cor ou legendar um vídeo bruto.
---

# /decupar

A pessoa traz um vídeo bruto em que ela fala para a câmera (Reels 9:16, gravado no celular). Você
transcreve, julga o que fica, confirma uma vez e entrega o vídeo cortado com legenda e os arquivos
para o editor dela. Quem usa é leigo, no Claude Desktop, no Mac ou no Windows. Tudo em português.

O bruto só é lido: todo arquivo novo nasce em `<pasta do vídeo>/decupagem/`, e os scripts cuidam
disso. Se o caminho é um atalho (symlink) para o bruto, a decupagem nasce ao lado do atalho. Os scripts ficam em `<pasta desta skill>/scripts/` (a pasta aparece quando a skill carrega).

**Pasta de edição**: se houver `marca/estilo.md` na pasta do vídeo ou até 3 pastas acima dela, leia antes
de começar. A cor do passo 2b sai de lá (o look descrito no estilo) e vale mais que a receita da `/minha-edicao`.

## Conversa

Frases curtas, sem termo técnico: "partes gravadas de novo", "pausas", "começo forte". Antes de cada
etapa que demora, diga quanto tempo leva:

| Etapa | Mac com chip M | Windows ou Mac Intel |
|---|---|---|
| Primeira vez: instala o Whisper e baixa o modelo (cerca de 2 GB) | 5 a 15 min, depende da internet | igual |
| Transcrever | uns 10 s por minuto de vídeo | 1 a 2 min por minuto de vídeo |
| Prévia (e cada correção) | 5 a 15 s por minuto de vídeo | cerca de 1 min por minuto |
| Vídeo final 1080×1920 | uns 15 s por minuto de vídeo (bruto 4K: uns 90 s por minuto de vídeo final) | 1 a 2 min por minuto |
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
vídeos: pergunte qual, um por vez.

```
uv run "<pasta desta skill>/scripts/transcrever.py" "<vídeo>"
```

Rode com tempo-limite de 10 minutos. Na primeira vez da máquina (instala o Whisper e baixa o modelo)
ou num vídeo longo no Windows, rode em segundo plano e espere o aviso de término.

Ele imprime a pasta da decupagem, o vídeo (duração, tamanho), as pausas e as **pistas**. No fim solta
em segundo plano uma cópia leve do vídeo, que deixa a prévia e as correções rápidas; siga sem esperar.
Rodar de novo com o mesmo vídeo usa o cache e leva menos de 1 s.

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
- **Começo e fim**: o vídeo começa na primeira frase útil e termina na última (CTA incluído).
- **Pausas e respingos**: o corte tira sozinho as pausas maiores que `pausa_max` (entre palavras e as
  medidas no som, deixando um respiro curto) e os sons sem palavra de 0,15 s ou mais dentro da frase;
  você não lista pausas. Palavra que emenda na voz com a seguinte ("Aí, até") não se separa: sai junto
  ou fica junto.
- **Ganchos**: as 3 frases que poderiam abrir o Reel (afirmação forte, número, promessa, conflito),
  com o tempo no vídeo cortado e o porquê.
- **Imagem ou grafismo**: listas, números, exemplos e nomes de ferramenta, com o tempo no vídeo
  cortado e o que mostrar.

Grave o `cortes.json` (formato abaixo) e confira na hora a duração antes e depois e o tempo de cada
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
tela é vertical: não recorte). Se ele disser **horizontal** e o destino for Reel:

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
tom puxado da luz), depois **um look só**, vindo da skill de estilo da pessoa (a que ela fez com a
/minha-edicao) ou do que ela disser do filtro dela. Nunca dois looks por cima; nunca saturar.

```json
"cor": {"corrigir": true,
        "look": {"nome": "Gastronômico + Verão Italiano", "contraste": -4, "sombra": -2, "calor": 0.55, "saturacao": -5}}
```

- `contraste` e `sombra` na escala do CapCut (-50 a 50; o script limita a ±20). `calor` de 0 a 1 é o
  tom quente suave que aproxima filtros quentes do CapCut. `saturacao` de -10 a 5 (opcional).
- Sem look: só `"corrigir": true`. Sem correção: `"corrigir": false` e o look.

```
uv run "<pasta desta skill>/scripts/cor.py" "<pasta decupagem>"
```

Ele mede, grava o filtro e monta a `cor-antes-depois.jpg` com 2 quadros do vídeo cortado (em cima
antes, embaixo depois). Abra (Read) e olhe a pele: rosada e natural, sem laranja nem cinza. Com
"ATENÇÃO" (cor subiu mais de 10% ou ficou lavada), baixe o `calor` ou ponha `saturacao` -3 a -5 e
rode de novo. O cortar.py aplica a mesma cor na prévia e no final.

## 3. Confirmar

Mande no chat: antes → depois, de 3 a 6 itens do que saiu, os 3 ganchos e uma pergunta só: "Gero a
prévia assim? Se quiser mudar, é só dizer (por exemplo: 'tira a frase sobre X', 'abre com o gancho
2')." Se ela pedir mudança, aplique como no passo 5, rode o `--resumo` e confirme em uma linha.

## 4. Entregar

```
uv run "<pasta desta skill>/scripts/cortar.py" "<pasta decupagem>"
```

Gera `previa.mp4` (1080 de altura, rápida, para conferir), `legenda.srt`, `premiere.xml` e
`capcut.md`. Se a cópia leve ainda estiver sendo feita, ele espera por ela.

Pronto quando ele imprime a duração da prévia sem "ATENÇÃO" (e "com cor" ou "recorte 9:16" quando
pediu). Com "ATENÇÃO", rode de novo uma vez; se
repetir, conte à pessoa que a prévia saiu com duração diferente da esperada.

Entregue assim, uma linha por arquivo:

- `previa.mp4`: o vídeo cortado, para conferir. Vai sem legenda na imagem.
- `legenda.srt`: a legenda no tempo do vídeo cortado, em frases curtas.
- `premiere.xml`: abre já cortado no Premiere (Arquivo → Importar) ou no DaVinci (Arquivo → Importar
  → Linha do tempo), usando o vídeo original. Deixe o original onde está.
- `capcut.md`: o passo a passo para o CapCut no computador.
- `decupagem.md`: o que saiu e por quê, ganchos e onde cabe imagem.

E ofereça o final: "Quer o vídeo final em 1080×1920 para publicar? Leva uns N min." Com o sim, rode
o mesmo comando com `--final` (tempo-limite de 10 minutos), que grava `final.mp4` a partir do original.

Confira as emendas transcrevendo o vídeo cortado (uns 20 s): `uv run "<pasta desta skill>/scripts/transcrever.py"
"<pasta decupagem>/final.mp4"` (ou a prévia), copiado antes para uma pasta à parte, para não misturar
com a decupagem do bruto. Palavra que sumiu no fim de um trecho (o Whisper às vezes encurta a última
palavra antes de uma pausa: "produ-", "experimen-") se resolve com um trecho `"exato": true` indo até
o começo do silêncio seguinte; sobra de palavra cortada no começo, com `"exato"` começando depois dela.

## 5. Corrigir

A pessoa diz em texto o que mudar. Edite o `cortes.json` e a `decupagem.md` e rode o `cortar.py` de
novo (com `--final` se ela já tinha o final). A transcrição fica em cache: só o corte refaz.

- "Tira tal frase": divida o trecho em volta dela.
- "Abre com o gancho N": ponha o trecho do gancho no topo da lista e tire-o do lugar antigo. Se ele
  continuar nos dois lugares, o script avisa que a fala aparece duas vezes.
- "Ficou corrido": suba `pausa_max` para 0.5 ou 0.6. "Ainda tem pausa": desça para 0.25.
- Gesto ou sorriso sem fala no fim: trecho com `"exato": true`.

## cortes.json

```json
{
  "pausa_max": 0.35,
  "trechos": [
    {"de": "F2", "ate": "F9", "nota": "abertura"},
    {"de": "F14", "ate": "01:47,30", "nota": "segunda versão da explicação; a primeira (F10–F13) saiu"},
    {"de": "F30", "ate": "02:41,00", "exato": true, "nota": "fica o sorriso do fim"}
  ]
}
```

- A ordem da lista é a ordem do vídeo final.
- `de` e `ate` aceitam a frase (`"F12"`: início ou fim dela), o tempo `"mm:ss,cc"` da transcrição ou
  segundos (`83.45`), sempre do vídeo bruto.
- Fica a palavra cujo meio cai dentro do trecho; a borda do corte se ajusta sozinha à fala, com folga.
- `"exato": true` usa `de` e `ate` como estão, sem ajustar às palavras nem tirar pausas.
- `"vertical"` (opcional, só vídeo horizontal): `true` usa o centro achado pelo enquadrar.py;
  `{"centro_x": 0.42}` fixa à mão.
- `"cor"` (opcional): veja o passo 2b.

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
  sem legenda queimada; o estilo da legenda se faz no CapCut, no Premiere ou no DaVinci.
- Vídeo HDR do iPhone: se o ffmpeg não converter as cores (o script avisa), a prévia pode sair com
  cor diferente. O `premiere.xml` usa o original, com a cor certa.
- O `premiere.xml` aponta para o vídeo original. Se ele mudar de lugar, o editor pede para localizar.
- Recorte 9:16 e cor saem só na prévia e no final (mp4). O `premiere.xml` abre na geometria do bruto e
  sem cor: no Premiere, use Sequência → Reenquadramento automático e o Lumetri com os mesmos valores.
