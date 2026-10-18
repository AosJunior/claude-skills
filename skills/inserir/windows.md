# /inserir no Windows

Tudo funciona igual; muda a instalação, o jeito de escrever caminhos e o tempo.

- **Instalar**: `winget install Gyan.FFmpeg astral-sh.uv` no PowerShell (aceite os termos se ele perguntar).
  Depois a pessoa fecha e abre o Claude: o Windows só enxerga programa novo numa janela nova.
- **Primeira vez**: o navegador que desenha é baixado para `%LOCALAPPDATA%\ms-playwright\`. Se o antivírus
  perguntar, é seguro permitir. Se o download falhar (rede da empresa, proxy), rode de novo.
- **Vídeo atrás da pessoa**: a máscara usa o RobustVideoMatting, baixado na primeira vez (15 MB) para
  `%USERPROFILE%\.cache\claude-skills\inserir\`. Leva uns 10 s por segundo de trecho e fica guardada.
- **Caminhos no `insercoes.json`**: use barra normal, `"C:/Users/Ana/Fontes/Fonte-Regular.otf"`. Barra
  invertida só dobrada (`"C:\\Users\\..."`), senão o JSON quebra. Caminho `marca/...` e `../brutos/...`
  funcionam igual ao Mac.
- **Comandos**: rode como no Mac, com aspas duplas em volta de todo caminho (nome de pasta com espaço e
  acento é comum no Windows: `"C:/Users/Ana/Vídeos/Reel 1/decupagem"`).
- **Fonte padrão**: sem fonte no estilo, a legenda sai em Segoe UI, que tem acentuação completa.
- **Tempo**: vídeo só com cartões e legenda leva 1 a 2 min por minuto; com camadas ou tela dividida, 2 a 4
  min por minuto (o vídeo é codificado no processador, sem o chip de vídeo do Mac). Avise antes e rode com
  tempo-limite de 10 minutos.
