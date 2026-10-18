# Aplicar a receita no editor da pessoa

Nome de menu muda entre versões e idiomas. Na receita, descreva o passo pela função ("no painel de texto, onde se escolhe a fonte") e ponha o nome do menu só como pista. Se a pessoa disser que no editor dela o caminho é outro, isso é correção: entra na receita pelo bloco de melhoria.

O kit entrega o vídeo pronto: a `/inserir` grava a legenda na imagem (desenhada pelo navegador, na fonte do
estilo) junto com as camadas, e a `legenda-curta.srt` sai com o mesmo tempo da legenda gravada. Este arquivo
só vale para quem termina o vídeo num editor: aí ela pede à `/inserir` o vídeo sem legenda e aplica o estilo
no editor, a partir da `legenda-curta.srt`.

## O que o Claude entrega em cada caso

| Onde a pessoa termina | Entrega |
|---|---|
| No kit (recomendado) | `entrega/`: vídeo final com legenda, camadas, cor e som em -14 LUFS, `legenda-curta.srt` e créditos |
| CapCut no computador | vídeo da `/inserir` sem legenda (ou da `/decupar`, se ela faz as inserções no CapCut) + `legenda-curta.srt` + lista curta do que fazer no CapCut |
| CapCut no celular | o mesmo vídeo (para levar ao celular: AirDrop, WhatsApp para si mesma ou Google Drive) + os valores do estilo para repetir à mão. O CapCut do celular não importa `.srt`: ela usa a legenda automática dele |
| Premiere | o que a `/decupar` gera para o Premiere (linha do tempo em XML) + `legenda-curta.srt` + lista curta do que fazer |
| Outro editor | vídeo sem legenda + `legenda-curta.srt` + os valores do estilo |

## CapCut no computador

- **Legenda**: importar o `.srt` (aba Texto ou Legendas; procure "legendas locais" ou "importar legendas") e soltar na linha do tempo. Clicar numa legenda e ajustar no painel da direita: fonte, tamanho, cor, contorno, sombra e fundo. A mudança de estilo costuma valer para a faixa inteira; se mudar só uma, selecione todas antes.
- **Posição**: arrastar a legenda na prévia até a altura da receita; o CapCut mostra guias de centro.
- **Zoom no rosto**: no trecho escolhido, aumentar a escala do vídeo para o nível do estilo (ex.: 100% → 112%) e voltar para 100% no plano seguinte.
- **Música embaixo da voz**: volume da música entre 10% e 20%, ou a função do CapCut que abaixa a música quando há voz, se ela usar.
- **Cor**: com LUT no estilo, importar o `.cube` de `marca/cor/` (Ajustes › LUT, onde a versão dela tiver) com intensidade 100%; sem LUT, o filtro e a intensidade em %, com o nome que aparece no CapCut dela.

## CapCut no celular

Legenda automática do CapCut (aba Texto ou Legendas) e depois o estilo da receita: fonte, tamanho, cor, contorno, sombra, fundo e posição, na mesma ordem da tabela de parâmetros. Legenda que juntou palavras demais: dividir em duas. Depois de acertar uma vez, salvar o estilo como favorito, se a versão dela tiver essa opção.

## Premiere

- **Legenda**: Arquivo › Importar o `.srt` e arrastar para a linha do tempo, que cria uma faixa de legendas. Estilo no painel Gráficos essenciais (ou Propriedades, nas versões novas): fonte, tamanho, cor, sombra, fundo e posição.
- **Estilo para todos os vídeos**: salvar o visual como estilo de faixa (Track Style), que vale para todas as legendas daquela faixa. Esse estilo pode ficar preso ao projeto: a receita guarda os valores para recriar quando ele não aparecer.
- **Zoom, música e cor**: escala no painel Controles de efeito; volume da música no mixador de áudio (ou o abaixamento automático do painel Som essencial); cor no painel Lumetri: o `.cube` de `marca/cor/` em Entrada LUT (ou Look), ou os valores anotados.
