# Medir a referência e o vídeo da pessoa

O objetivo é a **ficha**: os fatos de cada vídeo que viram regra na receita. Você mede, olha e anota. O que não der para ver fica "não deu para ver" e vira pergunta; nada é chutado.

Grave tudo numa subpasta `medidas/` da pasta aberta no Claude Code. O vídeo original da pessoa é só lido: nunca editado, movido ou apagado. Caminhos sempre entre aspas duplas (nomes com espaço e acento). Os comandos abaixo funcionam igual no Mac e no Windows.

## Link de Reel

```
uvx yt-dlp -o "medidas/referencia.%(ext)s" "<link>"
```

O `uv` vem no kit. O Instagram costuma pedir login e o download falha: aí peça à pessoa para salvar o Reel no celular e arrastar o arquivo aqui, ou mandar 3 prints (começo, meio com legenda, fim) e a duração que aparece no player. Siga com o que vier, sem travar a entrevista.

## Com ffmpeg

Para cada vídeo (`<v>` = caminho do arquivo, `<n>` = `ref` ou `meu`):

1. **Duração e tamanho**
   ```
   ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 "<v>"
   ```
2. **Trocas de plano (cortes)**
   ```
   ffmpeg -hide_banner -i "<v>" -vf "select='gt(scene,0.3)',showinfo" -an -f null - 2> "medidas/<n>_cortes.txt"
   ```
   Cada linha com `pts_time:` é um corte. Ritmo = duração ÷ (cortes + 1), em segundos por plano. Pessoa falando parada para a câmera: o corte seco quase não muda a imagem e escapa com 0.3; se achar poucos cortes nesse tipo de vídeo, rode de novo com `0.1` e confira nas folhas.
3. **Pausas**
   ```
   ffmpeg -hide_banner -i "<v>" -af "silencedetect=noise=-35dB:d=0.4" -vn -f null - 2> "medidas/<n>_pausas.txt"
   ```
   Cada `silence_duration` é uma pausa acima de 0,4 s que ficou no vídeo. Zero pausas com fala = corte "sem respiro". Com música de fundo o silêncio não aparece: anote "não deu para ver".
4. **Folhas de contato** (1 quadro por segundo, 12 por folha)
   ```
   ffmpeg -hide_banner -loglevel error -i "<v>" -vf "fps=1,scale=270:-1,tile=4x3" "medidas/<n>_folha_%02d.jpg"
   ```
   Abra cada folha e anote: o que aparece e o que está escrito nos 3 primeiros segundos (o gancho), os blocos do vídeo, zoom no rosto, letterings, transições, cor geral (quente, fria, neutra) e o pedido do fim.
5. **Legenda de perto** (3 s do meio, 4 quadros por segundo; `<meio>` = metade da duração, em segundos)
   ```
   ffmpeg -hide_banner -loglevel error -ss <meio> -t 3 -i "<v>" -vf "fps=4,scale=540:-1,tile=4x3" -frames:v 1 "medidas/<n>_legenda.jpg"
   ```
   Anote: palavras por vez, letra maiúscula ou normal, fonte aparente (com ou sem serifa, fina ou grossa), cor, destaque, contorno, fundo ou sombra, posição (em % da altura, de cima para baixo) e quanto da largura a frase ocupa.

## Sem ffmpeg

Peça a duração (aparece no player) e 3 prints arrastados para o chat: começo, meio com legenda, fim. Olhe os prints do mesmo jeito que as folhas. O que só o ffmpeg mede (cortes, pausas) vira pergunta simples: "os cortes são rápidos, tipo a cada 1 ou 2 segundos, ou mais calmos?". Ofereça instalar para a próxima vez: Mac `brew install ffmpeg`, Windows `winget install Gyan.FFmpeg`.

## A ficha

Grave em `medidas/ficha.md`, uma coluna por vídeo:

| Item | Referência | Vídeo dela |
|---|---|---|
| Duração · orientação | | |
| Trocas de plano (quantas · s por plano) | | |
| Pausas acima de 0,4 s | | |
| Gancho (0–3 s: o que se vê, o que se lê) | | |
| Blocos (em ordem, com segundos) | | |
| Pedido do fim | | |
| Legenda: palavras por vez · maiúscula ou normal | | |
| Legenda: fonte aparente · cor · destaque | | |
| Legenda: contorno, fundo ou sombra | | |
| Legenda: posição (% da altura) · largura | | |
| Letterings · zoom no rosto · transições | | |
| Cor geral | | |

Linha sem valor: "não deu para ver".
