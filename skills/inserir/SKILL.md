---
name: inserir
description: Inserções e legenda gravadas no vídeo de Reels, depois da /decupar. Lê a fala, propõe onde entra cada cartão (lista, número grande, comparação, passo a passo, print real da marca citada), desenha os cartões e a legenda de 2 a 4 palavras no estilo da pessoa e entrega o vídeo pronto. Use quando a pessoa mandar /inserir ou pedir inserções, cartões, grafismos ou legenda na imagem de um vídeo já decupado.
---

# /inserir

A pessoa traz a pasta `decupagem/` que a `/decupar` gerou (vídeo cortado, `legenda.srt`, transcrição).
Você lê a fala, propõe onde entra cada inserção, confirma uma vez e entrega o vídeo com os cartões e a
legenda gravados na imagem. Quem usa é leigo, no Claude Desktop, no Mac ou no Windows. Tudo em português.
Se ela trouxer só o vídeo bruto, diga que primeiro vem a `/decupar` (corta e gera a legenda) e pare.

O vídeo cortado só é lido: todo arquivo novo nasce em `<pasta do vídeo>/insercoes/` (a pasta irmã da
`decupagem/`). Os scripts ficam em `<pasta desta skill>/scripts/` e o desenho dos cartões em
`<pasta desta skill>/modelos/cartao.html`.

## Conversa

Frases curtas, sem termo técnico: "cartão", "número grande", "print do site", "legenda na imagem".
Nunca peça para a pessoa abrir terminal, editar JSON ou rodar comando: isso é trabalho seu. Antes de cada
etapa que demora, diga quanto tempo leva:

| Etapa | Mac com chip M | Windows ou Mac Intel |
|---|---|---|
| Primeira vez: baixa o navegador que desenha os cartões (uns 200 MB, só uma vez por computador) | 1 a 3 min | 2 a 5 min |
| Cartões para conferir | uns 10 s | 20 a 40 s |
| Vídeo final | uns 20 s por minuto de vídeo | 1 a 2 min por minuto |

A única pergunta do fluxo é a confirmação do mapa (passo 3). O resto você executa.

## 0. Conferir o ambiente

`ffmpeg -version` e `uv --version`. Se faltar um, diga em uma linha o que falta e ofereça instalar;
instale só depois do sim (Mac: `brew install ffmpeg uv`; Windows: seção [Windows](#windows)).
Pronto quando os dois respondem com a versão.

## 1. Ler a fala e o estilo

- Leia a `legenda.srt` inteira (o tempo dela já é o do vídeo cortado) e a seção "Onde cabe imagem ou
  grafismo" da `decupagem.md`, se existir.
- **Estilo**: procure na pasta de skills da pessoa (`~/.claude/skills/`; no Windows,
  `%USERPROFILE%\.claude\skills\`) uma receita de estilo feita com a `/minha-edicao` que fale de
  legenda ou letterings. Dela saem fonte, fonte de destaque, tamanho, cor e posição, que vão para o
  bloco `estilo` do `insercoes.json`. Sem receita, fique com o padrão do script (fonte do sistema, que
  tem acentuação completa) e diga isso em uma linha.
- **Fonte** é um arquivo `.otf` ou `.ttf` no computador. Fonte que só existe dentro do CapCut ou do Canva
  não é arquivo: peça o arquivo à pessoa ("arrasta aqui o arquivo da fonte") ou fique com a do sistema.
  No Mac, as fontes instaladas ficam em `~/Library/Fonts/` ou `/Library/Fonts/`; no Windows, em
  `C:\Windows\Fonts\` ou `%LOCALAPPDATA%\Microsoft\Windows\Fonts\`.
- Olhe 3 ou 4 quadros do vídeo cortado (`ffmpeg -ss <s> -i <vídeo> -frames:v 1 -vf scale=540:-2 q.jpg`)
  para ver onde fica a cabeça. Plano aberto, com a cabeça abaixo de uns 700 px (no quadro de 1920),
  pede **painel** no alto da tela: o rosto e o que ela mostra continuam à vista. Close pede **tela cheia**.

Pronto quando você sabe o tempo de cada frase, o estilo e a posição do rosto.

## 2. Mapa de inserções (você julga)

Uma inserção entra quando a fala pede imagem. A **forma da fala** decide o tipo:

| A fala tem | Tipo | Como aparece |
|---|---|---|
| lista ("três erros", "primeiro... segundo...") | `lista` | os itens entram um a um, cada um no tempo em que é dito |
| número ("100 mil", "R$ 18 milhões") | `numero` | o número grande e uma linha do que ele é |
| comparação (antes e hoje, isto e aquilo) | `comparacao` | dois lados; o segundo entra quando a fala chega nele |
| passo a passo | `etapas` | etapas numeradas que entram uma a uma |
| marca, site ou app citado | `print` | print real da página, tirado com `print.py` |
| conceito com nome ("conformidade social") | `frase` | o nome em letra grande |

Réguas, todas obrigatórias:

- **Gancho e emoção são do rosto**: nada no primeiro segundo do vídeo nem em fala pessoal ou emocional.
- **Respiro**: uns 2 s de rosto entre uma inserção e a próxima; cada inserção fica de 1,5 a 6 s na tela cheia (painel, até 10 s).
- **Ritmo**: "algo novo a cada 2,5 s" serve para dica rápida; história e depoimento pedem respiro.
- **Só o que foi dito**: todo número, nome e dado do cartão sai da fala ou de fonte que você conferiu.
  Sem dado, sem cartão.
- **Marca é print real**: `uv run "<pasta desta skill>/scripts/print.py" "<site>" "<pasta insercoes>/prints/<marca>.png"`
  (tela de celular; `--computador` para a de computador). Abra o PNG e confira página certa, sem aviso
  de cookies na frente e sem dado pessoal; página em branco ou bloqueio pede outro endereço (loja
  oficial, perfil da marca). Ícone genérico não serve.
- **Imagem ou vídeo gerado** (Higgsfield, GPT Image, Nano Banana): escreva só o prompt em
  `<pasta insercoes>/prompts.md` (modelo abaixo), sem gastar crédito. Quando a pessoa trouxer o arquivo,
  ele entra como tipo `imagem`.
- **Legenda**: escolha as palavras de destaque (uma a cada 5 a 8 s, a palavra que carrega a frase) e
  corrija em `correcoes` o que o Whisper ouviu errado.

Grave o `insercoes.json` (formato abaixo). Pronto quando cada momento de lista, número, comparação,
passo a passo ou marca da fala virou inserção ou tem o motivo de ter ficado de fora.

## 3. Confirmar

Mande no chat uma linha por inserção (tempo, tipo, o que aparece), as palavras de destaque e uma
pergunta só: "Faço assim? Se quiser mudar, é só dizer (por exemplo: 'tira o cartão de 0:42', 'põe o
número de 1:05')."

## 4. Cartões

```
uv run "<pasta desta skill>/scripts/inserir.py" "<pasta decupagem>" --cartoes
```

Grava `cartoes.png` com todos os cartões. Abra e confira: texto certo e com acento, nada cortado,
destaque na palavra certa. Todo "ATENÇÃO" e todo "Aviso" do script pede correção no `insercoes.json`
antes de seguir; "a fonte não tem Ã" quer dizer que essa letra sairia em outra fonte.

Pronto quando o script roda sem "ATENÇÃO" e o `cartoes.png` passa na conferência.

## 5. Vídeo

```
uv run "<pasta desta skill>/scripts/inserir.py" "<pasta decupagem>"
```

Opções: `--video <arquivo>` (padrão: `final.mp4`, senão `previa.mp4` da decupagem), `--saida
<arquivo.mp4>`, `--pasta <pasta de trabalho>`. Rode com tempo-limite de 10 minutos.

Ele grava o vídeo, a `legenda-curta.srt` (a legenda de 2 a 4 palavras, para usar no editor) e a pasta
`quadros/` com um quadro de cada cartão e das legendas com destaque, com acento e a mais longa, todos
juntos em `quadros/folha.jpg`. Abra a folha (e o quadro inteiro do que estiver em dúvida) e confira:

- a legenda se lê e não encosta no rosto nem nos botões do Instagram;
- o acento sai na mesma fonte da palavra (o "Ã" do "NÃO");
- nenhum cartão em painel cobre o rosto.

Pronto quando todos os quadros passam. Entregue assim, uma linha por arquivo:

- `<vídeo>-insercoes.mp4`: o vídeo com os cartões e a legenda na imagem, pronto para postar ou para a
  música.
- `legenda-curta.srt`: a mesma legenda em pedaços de 2 a 4 palavras, para quem quiser estilizar no
  CapCut ou no Premiere.
- `prompts.md` (se houver): os prompts das imagens que valem a pena gerar.
- E uma linha por inserção: tempo, o que aparece e por quê.

## 6. Corrigir

A pessoa diz o que mudar; edite o `insercoes.json` e rode o passo 5 de novo. Só os cartões e legendas
que mudaram são redesenhados.

## insercoes.json

Tempos do vídeo cortado, em `"mm:ss,cc"` ou segundos. Caminhos relativos à pasta `insercoes/`.

```json
{
  "estilo": {
    "fonte": "/caminho/da/fonte-Regular.otf",
    "fonte_destaque": "/caminho/da/fonte-destaque.ttf",
    "tamanho": 64, "cor": "#FFFFFF", "cor_destaque": "#FFFFFF", "escala_destaque": 1.12,
    "sombra": 0.45, "maiusculas": false, "legenda_y": 1400,
    "cartao_fundo": "#141414", "cartao_tinta": "#F5F2EC", "cartao_destaque": "#E8C27A"
  },
  "destaques": ["milhões", "conteúdo"],
  "correcoes": {"alugas": "aluga-se"},
  "insercoes": [
    {"tipo": "lista", "de": "00:12,40", "ate": "00:16,80", "titulo": "Três *erros*",
     "itens": [{"texto": "Preço sem conta", "t": "00:12,90"}, {"texto": "Vitrine apagada", "t": "00:14,10"}]},
    {"tipo": "numero", "de": 42.9, "ate": 45.0, "numero": "+100 mil", "texto": "produtos vendidos"},
    {"tipo": "comparacao", "de": 80.5, "ate": 86.4, "t_direita": 84.5,
     "esquerda": {"titulo": "A marca diz", "texto": "você desconfia"},
     "direita": {"titulo": "Gente como você", "texto": "você confia"}},
    {"tipo": "etapas", "de": 20, "ate": 25, "titulo": "Como fazer", "itens": ["Grave", "Corte", "Poste"]},
    {"tipo": "print", "de": 35.2, "ate": 38.6, "imagem": "prints/marca.png", "marca": "Marca", "endereco": "marca.com.br"},
    {"tipo": "frase", "de": 75.3, "ate": 77.6, "texto": "Conformidade *social*"},
    {"tipo": "imagem", "de": 90, "ate": 92, "imagem": "geradas/cena.png"}
  ]
}
```

- `estilo`: só o que difere do padrão. `legenda_y` é o pé das letras, em px num quadro de 1080×1920
  (1400 deixa a legenda acima dos botões do Instagram). `sombra` vai de 0 a 1.
- `*palavra*` em qualquer texto de cartão sai na fonte e na cor de destaque.
- `"formato": "painel"` põe o cartão numa caixa no alto da tela, com o vídeo em volta; sem ele, o cartão
  ocupa a tela toda e a legenda continua por cima. Painel só quando o rosto fica abaixo da caixa.
- Item de lista ou etapa sem `"t"` entra sozinho, espalhado na primeira metade da inserção.
- `"nota"` (opcional) guarda a frase da fala que justifica o cartão; o script ignora.

## prompts.md

```markdown
# Prompts de imagem e vídeo: <nome do vídeo>

## 00:16 · placas de "aluga-se" (fala: «um monte de placa de aluga-se»)
- Ferramenta sugerida: Nano Banana (imagem) ou Higgsfield (vídeo de 3 s)
- Prompt: <cena, enquadramento vertical 9:16, luz, estilo, o que NÃO pode aparecer>
- Entra como: tela cheia, 2 s
```

## Windows

Tudo funciona igual; muda a instalação e o jeito de escrever caminhos.

- **Instalar**: `winget install Gyan.FFmpeg astral-sh.uv` no PowerShell (aceite os termos se ele
  perguntar). Depois a pessoa fecha e abre o Claude: o Windows só enxerga programa novo numa janela nova.
- **Primeira vez**: o navegador dos cartões é baixado para `%LOCALAPPDATA%\ms-playwright\`. Se o
  antivírus perguntar, é seguro permitir. Se o download falhar (rede da empresa, proxy), rode de novo.
- **Caminhos no `insercoes.json`**: use barra normal, `"C:/Users/Ana/Fontes/Fonte-Regular.otf"`. Barra
  invertida só dobrada (`"C:\\Users\\..."`), senão o JSON quebra.
- **Comandos**: rode como no Mac, com aspas duplas em volta de todo caminho (nome de pasta com espaço e
  acento é comum no Windows: `"C:/Users/Ana/Vídeos/Reel 1/decupagem"`).
- **Fonte padrão**: sem fonte no estilo, a legenda sai em Segoe UI, que tem acentuação completa.
- **Tempo**: o vídeo final leva 1 a 2 min por minuto de vídeo; avise antes e rode com tempo-limite de
  10 minutos.

## Limites

- O ffmpeg do Homebrew não desenha texto: cada legenda e cada cartão é um PNG desenhado pelo navegador
  e posto por cima do vídeo no tempo dele. Os cartões entram e saem em corte seco, sem animação.
- A fonte da pessoa fica no computador dela; o script só lê o arquivo.
- Print de site depende do site: alguns bloqueiam robô ou abrem em branco. Aí vale a loja oficial ou o
  perfil da marca.
