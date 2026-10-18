# Medir a referência e o vídeo da pessoa

O objetivo é a **ficha**: os fatos de cada vídeo que viram regra na receita, medidos em px no quadro
1080×1920 (y = 0 é o topo) e em segundos. Você mede, olha e anota. O que não der para ver fica "não deu para
ver" e vira pergunta; nada é chutado.

Onde gravar, dentro da pasta de edição:

- vídeos de referência: `marca/referencias/<nome>.<ext>` (a `/criticar` compara o resultado com eles);
- medidas: `marca/referencias/medidas/<nome>/`; a ficha: `marca/referencias/ficha.md`.

O vídeo da pessoa é só lido: nunca editado, movido ou apagado. Caminhos sempre entre aspas duplas (nomes com
espaço e acento). Os comandos funcionam igual no Mac e no Windows. `<skill>` é a pasta desta skill; a `/decupar`
e a `/sonorizar` ficam ao lado dela (`<skill>/../decupar`, `<skill>/../sonorizar`).

## Primeiro: qual Reel é qual

Confira a identidade de cada vídeo **pela folha**, nunca pelo nome do arquivo nem pelo rótulo que veio
junto: abra a primeira folha e descreva em uma linha quem aparece e o que acontece nos 3 primeiros segundos
("moça de moletom vermelho na cama, sem tela dividida"). Os rótulos de uma pasta real já vieram trocados, e
o padrão de gancho foi atribuído ao vídeo errado. Só depois dessa linha o vídeo entra na ficha com um nome.

## Link de Reel

```
uvx yt-dlp -o "marca/referencias/<nome>.%(ext)s" "<link>"
```

O Instagram costuma pedir login e o download falha: aí peça à pessoa para salvar o Reel no celular e arrastar
o arquivo aqui, ou mandar 3 prints (começo, meio com legenda, fim) e a duração que aparece no player. Siga com
o que vier, sem travar a entrevista.

## Medidas automáticas

```
uv run "<skill>/scripts/medir.py" "<vídeo>" "marca/referencias/medidas/<nome>" [--de 0 --ate 13] [--zona 0 960]
```

Leva uns 2 a 4 min por minuto de vídeo (na primeira vez instala o OpenCV, uns 50 MB). Imprime o resumo e grava
`medidas.json` e as folhas. Vídeo de outro tamanho é escalado para 1080×1920 antes de medir.

| Linha do resumo | Como ler |
|---|---|
| Cortes · plano mediano · maior trecho sem corte | ritmo de corte; o maior trecho é o candidato a "tempo sem evento" |
| Zoom nos cortes | cada corte vira um nível (o maior entre o salto e o inverso dele: o vai e volta 1,0 → 1,2 → 1,0 dá 1,20). Níveis com muitos cortes são os do estilo; 1,08 ou 1,16 soltos costumam ser trocas entre dois níveis (1,3 ÷ 1,2) |
| Cortes para outra imagem | o fundo não casou: troca de cena, não zoom |
| Cortes a cada 10 s | o ritmo ao longo do vídeo |
| Linhas fixas | borda horizontal que fica parada no trecho: emenda de tela dividida, borda de caixa, tarja. Linha que atravessa a largura é emenda; trecho curto (menos de 150 px) costuma ser objeto do cenário |
| Texto branco por faixa de y | onde mora a legenda e o lettering. Objeto branco na cena também conta: confirme na folha |

Para um trecho especial, rode de novo só nele: o gancho (`--de 0 --ate <fim do gancho>`) e, na tela dividida,
o zoom só da metade de cima (`--zona 0 960`). As folhas trazem o tempo em cada quadro e uma régua amarela
a cada 240 px de y (números em 480, 960 e 1440): é com ela que você lê as posições.

Sem `uv`, ou para conferir uma medida, os comandos abaixo fazem o mesmo à mão.

## Com ffmpeg

Para cada vídeo (`<v>` = caminho do arquivo, `<n>` = nome curto, `<m>` = pasta de medidas):

1. **Duração e tamanho**: `ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of default=nw=1 "<v>"`
2. **Cortes**
   ```
   ffmpeg -hide_banner -i "<v>" -vf "scale=270:480,select='gt(scene,0.12)',showinfo" -an -f null - 2> "<m>/cortes.txt"
   ```
   Cada `pts_time:` é um corte. Pessoa falando parada para a câmera: o corte seco com zoom pequeno quase não
   muda a imagem; se achar poucos cortes, desça para `0.08` e confira nas folhas.
3. **Pausas**: `ffmpeg -hide_banner -i "<v>" -af "silencedetect=noise=-35dB:d=0.4" -vn -f null - 2> "<m>/pausas.txt"`.
   Com trilha por baixo o silêncio não aparece: anote "não deu para ver".
4. **Folhas com régua** (1 quadro por segundo, 6×4 por folha, linha a cada 240 px de y)
   ```
   ffmpeg -hide_banner -loglevel error -i "<v>" -vf "fps=1,scale=1080:1920,drawgrid=w=iw:h=240:t=3:c=yellow@0.6,scale=180:320,tile=6x4" "<m>/folha_%02d.jpg"
   ```
5. **Zoom entre dois planos**: o último quadro antes do corte `<t>` ao lado do primeiro depois.
   ```
   ffmpeg -hide_banner -loglevel error -ss <t-0.07> -i "<v>" -ss <t+0.07> -i "<v>" -filter_complex "[0:v]scale=540:960[a];[1:v]scale=540:960[b];[a][b]hstack" -frames:v 1 "<m>/zoom_<t>.jpg"
   ```
   Meça a mesma distância nos dois lados (entre os olhos, a largura de um quadro na parede): a razão é o nível.
6. **Uma faixa de perto** (para borda de caixa e emenda): `-vf "crop=1080:200:0:<y-100>"` no lugar do `scale` do item 5.
7. **Legenda de perto** (3 s do meio, 4 quadros por segundo)
   ```
   ffmpeg -hide_banner -loglevel error -ss <meio> -t 3 -i "<v>" -vf "fps=4,scale=1080:1920,drawgrid=w=iw:h=240:t=3:c=yellow@0.6,scale=540:960,tile=4x3" -frames:v 1 "<m>/legenda.jpg"
   ```

## O que olhar

- **Tela dividida e caixas**: as bordas horizontais constantes dão a emenda (y) e a caixa da headline (y de
  cima e de baixo; x pela folha de perto). Anote também a largura da parte nítida da metade de cima (720 px
  com laterais borradas, ou a largura toda), de quando a quando a dividida fica e o que acontece na metade
  de cima (pares "aberto + zoom seco", com a duração de cada um).
- **Zoom entre cortes**: os níveis, a âncora (o ponto que não se mexe: perto dos olhos) e o padrão (vai e
  volta para 1,0, ou escada).
- **Posições**: conte, pelas folhas, em quantos quadros a legenda e cada tipo de inserção estão em cada zona:
  topo (0 a 260), alto (260 a 780), meio (780 a 1100), peito (1100 a 1440), baixo (1440 a 1920). Some com o
  "texto branco por faixa" do script. A legenda: pé em y, palavras por vez, minúscula ou não, destaque (fonte,
  escala, para onde sobe). As inserções: tipo, caixa em px, lugar (atrás dela, na frente, metade de cima).
- **Ritmo**: eventos visuais a cada 10 s (cortes do script mais as camadas e letterings que entram, contados
  na folha) e o maior trecho sem evento.
- **Trilha**: o gênero de ouvido (cordas, jazz, lo-fi, pop) e o nome pelo Shazam:
  ```
  uv run --python 3.12 "<skill>/../sonorizar/scripts/identificar.py" "<v1>" "<v2>"
  ```
  Rode nos Reels dela e nas referências: as faixas que voltam definem o universo da trilha.
- **Cor**: com o bruto dela e o mesmo vídeo exportado do editor dela (com o filtro que ela usa), gere o LUT:
  ```
  uv run "<skill>/../decupar/scripts/lut_capcut.py" "<bruto>" "<exportação do editor>" "marca/cor/<nome>.cube"
  ```
  A última linha é um JSON com o ΔE00 médio num trecho fora do ajuste e o `resultado`: `aceita` (até 2: é a
  cor dela; o look feito no olho deu 5,46, o LUT 1,43), `atenção` (de 2 a 3: mostre o
  `<nome>-comparacao.jpg` e ela decide) ou `refaz` (acima de 3: confira se os dois vídeos são o mesmo trecho
  e se o filtro vale no vídeo todo). `--comparar "<outro.cube>"` mede outro LUT nos mesmos quadros.
  Sem os dois arquivos, a cor fica como descrição (quente, fria, contraste) e o LUT é pedido para depois.

## Sem ffmpeg

Peça a duração e 3 prints arrastados para o chat: começo, meio com legenda, fim. Olhe os prints do mesmo
jeito que as folhas. O que só a medida dá (cortes, níveis de zoom, pausas) vira pergunta simples: "os cortes
são rápidos, tipo a cada 2 segundos, ou mais calmos?". Ofereça instalar para a próxima vez: Mac
`brew install ffmpeg uv`, Windows `winget install Gyan.FFmpeg astral-sh.uv`.

## A ficha

Grave em `marca/referencias/ficha.md`, uma coluna por vídeo, com a linha de identidade da folha no topo:

| Item | Referência | Vídeo dela |
|---|---|---|
| Quem aparece e o que acontece em 0–3 s (pela folha) | | |
| Duração · fps · velocidade da fala | | |
| Cortes · plano mediano · maior trecho sem evento | | |
| Níveis de zoom · âncora · padrão | | |
| Gancho: tela dividida (emenda, metade de cima, de quando a quando) | | |
| Gancho: headline (caixa em px, cor, fonte, tamanho, até quando) | | |
| Blocos (em ordem, com segundos) e pedido do fim | | |
| Legenda: palavras por vez · minúscula · fonte · tamanho | | |
| Legenda: pé em y (normal, na dividida, com inserção no peito) | | |
| Destaque: fonte · escala · y · quando | | |
| Letterings: tipos, zona em y, quantos por minuto | | |
| Camadas: tipo, caixa, lugar (atrás, frente, topo), máscara | | |
| Posições por zona (legenda e inserções) | | |
| Eventos a cada 10 s | | |
| Trilha: gênero · faixas (Shazam) · troca | | |
| Efeitos sonoros e o momento de cada | | |
| Cor: LUT e ΔE, ou descrição | | |

Linha sem valor: "não deu para ver".
