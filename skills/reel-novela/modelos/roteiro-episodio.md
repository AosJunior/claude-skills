# O `roteiro.json` do episódio

Fica em `<pasta da série>/epNN/roteiro.json`. É o texto do episódio, um bloco por batida, e é o que o `narrar.py` lê
para narrar, conferir e alinhar. Escreva no passo 4 e só narre depois do portão 2.

## Campos de base

```json
{
  "voz": "<voice_id da bíblia>",
  "modelo": "eleven_v4",
  "velocidade": 1.25,
  "geracao": "inteira",
  "blocos": [
    {"cena": "abertura", "fala": "...", "texto": "...", "tela": "..."}
  ]
}
```

| Campo | O que é |
|---|---|
| `voz` | o `voice_id` do narrador da bíblia, o mesmo na série toda |
| `modelo` | `eleven_v4` ([`../referencias/voz.md`](../referencias/voz.md), «Modelo, velocidade e estabilidade») |
| `velocidade` | 1,2 a 1,3, padrão 1,25; o script acelera depois, sem mudar o tom |
| `geracao` | `inteira` (padrão): cada take é o roteiro inteiro numa geração só, e a voz fica igual do começo ao fim. `blocos` só como saída de emergência |
| `take` | opcional, na raiz, depois do `conferir`: o take que entra no episódio todo |
| `titulo` | opcional: o título do episódio, que vai para a `_regua.md` |
| `cena` | nome curto do bloco, minúsculo, sem acento nem espaço (`abertura`, `prazo`, `voto`) |
| `fala` | o que o narrador lê: marcas de emoção e números e siglas por extenso |
| `texto` | as mesmas palavras como a legenda mostra, com algarismos, siglas e pontuação; o alinhamento sai dele |
| `tela` | o que aparece, com a palavra-gatilho entre «»; o script ignora, serve para a pessoa aprovar e para o briefing do ato |

### A `fala`

- **Marca de emoção** em inglês, entre colchetes, no começo de cada frase que muda de tom (`[mischievously]`,
  `[serious]`, `[curious]`, `[dramatic]`, `[calm]`); pelo menos uma por bloco. A lista está em `voz.md`.
- **Número por extenso**, do jeito que se fala (`quarenta dias`, `três pedidos`); **sigla soletrada** (`í-bê-gê-é`).
- **Ênfase** pela marca, com a fala em minúsculas: maiúscula de ênfase deu problema na voz.
- **Nome que a voz erra nas amostras:** na `fala`, como soa; no `texto`, a grafia certa.
- **Pausa** é vírgula, ponto ou bloco novo. Reticências ficam de fora: nelas a voz repete palavra.

### O `texto`

As mesmas palavras da `fala`, na mesma ordem; muda só a forma dos números e das siglas, e as marcas ficam de fora. O
número do `texto` se lê exatamente como a `fala` diz (`quarenta dias` → `40 dias`; `três vírgula quatro` → `3,4`),
porque o alinhamento casa palavra com palavra. Ponto no milhar e vírgula decimal. Todo número sai do
`fatos-verificados.md`.

## Campos da novela

Quatro campos a mais por bloco, que o `narrar.py` ignora e os agentes de ato leem:

| Campo | O que é |
|---|---|
| `batida` | o número e o nome da batida na grade (`referencias/grade-de-batidas.md`), ex.: `"5 aula"` |
| `planos` | as imagens do bloco, na ordem: cada uma com a palavra que a troca (`em`), o cenário, a personagem e a pose (caminhos em `elenco/` e `cenarios/`) e a luz do código |
| `textos` | as vozes de texto além da legenda: `etiqueta` (com a cor), `balao` (com quem fala) ou `cartao`, cada uma com a palavra que a faz entrar |
| `barra` | relógio e medidor na tela durante o bloco; `null` quando a barra não aparece (antes do retrato no ep. 1, nos cartões cheios, na aula) |

Um campo só no bloco que antecede a aula:

| Campo | O que é |
|---|---|
| `aula_depois` | o trecho que toca logo depois da última palavra do bloco: `arquivo` em `aula/`, `duracao` em segundos e `lei`, a frase literal de quem vende, que vira etiqueta |

A aula não é um bloco: a voz de quem vende não passa pelo ElevenLabs. No passo 5 do `SKILL.md`, o `encaixar_aula.py`
abre a pausa no fim desse bloco (pelo `pausa.py`) e põe o trecho nela.

Um bloco por batida. Batida longa (a volta, a travessia) pode virar dois blocos, cada um com a sua `cena`. Cada plano
fica de 3 a 4,7 s no ar; quem dá o ritmo é o `em` de cada plano.

## Exemplo

Exemplo inventado: anúncio fechado, ep. 1 da série «A vitrine da Bia» (o exemplo do fim de `modelos/biblia.md`). Só
três blocos, para mostrar os campos. A lei está como marcador, porque nenhuma lei entra sem trecho em `aula/`.

```json
{
  "voz": "",
  "modelo": "eleven_v4",
  "velocidade": 1.25,
  "geracao": "inteira",
  "blocos": [
    {
      "cena": "abertura",
      "batida": "1 abertura na mentira",
      "fala": "[mischievously] Ela acabou de dizer que as encomendas estão bombando. [sarcastic] Teve três pedidos no mês. Dois são da mãe.",
      "texto": "Ela acabou de dizer que as encomendas estão bombando. Teve 3 pedidos no mês. Dois são da mãe.",
      "tela": "Quadro 0: Bia na festa da prima, copo na mão, balão «TÁ BOMBANDO!». Em «Teve», etiqueta vermelha «3 PEDIDOS NO MÊS» sobre o queixo dela.",
      "planos": [
        {"em": "Ela", "cenario": "cenarios/festa", "personagem": "elenco/bia", "pose": "sorriso-amarelo", "luz": "quente"}
      ],
      "textos": [
        {"tipo": "balao", "quem": "bia", "texto": "TÁ BOMBANDO!", "em": "Ela"},
        {"tipo": "etiqueta", "cor": "vermelha", "texto": "3 PEDIDOS NO MÊS", "em": "Teve"}
      ],
      "barra": null
    },
    {
      "cena": "lurdes-manda",
      "batida": "5 aula",
      "fala": "[calm] Dona Lurdes manda um vídeo. [curious] Minha neta assistiu isso.",
      "texto": "Dona Lurdes manda um vídeo. Minha neta assistiu isso.",
      "tela": "Em «manda», o telefone entra com a conversa da Dona Lurdes e o vídeo chegando. Em «isso», ele cresce até ocupar a tela.",
      "planos": [
        {"em": "Dona", "cenario": "cenarios/cozinha", "personagem": "elenco/bia", "pose": "olhando-telefone", "luz": "fria"}
      ],
      "textos": [
        {"tipo": "balao", "quem": "lurdes", "texto": "MINHA NETA ASSISTIU ISSO", "em": "Minha"}
      ],
      "barra": {"relogio": "Faltam 40 dias", "medidor": 2},
      "aula_depois": {"arquivo": "aula/lei-1.mp4", "duracao": 0, "lei": "[lei 1 da aula]"}
    },
    {
      "cena": "voto",
      "batida": "9 duas opções",
      "fala": "[serious] Grava ou espera? [calm] Comenta uma palavra que eu te mando a aula que ela assistiu.",
      "texto": "Grava ou espera? Comenta uma palavra que eu te mando a aula que ela assistiu.",
      "tela": "Cartão das duas opções: GRAVA (custa a vergonha de aparecer) e ESPERA (custa mais uma semana do prazo). Fica parado 5 s.",
      "planos": [],
      "textos": [
        {"tipo": "cartao", "texto": "GRAVA | ESPERA", "em": "Grava"}
      ],
      "barra": {"relogio": "Faltam 40 dias", "medidor": 2}
    }
  ]
}
```

## Conferência antes de mandar à pessoa

A sessão confere, e cada item sai sim ou não:

- [ ] as réguas de fala da grade: palavras por segundo, por frase e a fração de frases curtas;
- [ ] cada batida da grade do episódio (piloto ou sequência) existe, na faixa de posição dela;
- [ ] os 11 mecanismos da grade;
- [ ] as regras do modo (`SKILL.md`, «Modos de veiculação») e os limites;
- [ ] todo número e nome está no `fatos-verificados.md`, e a `lei` é a frase literal do trecho;
- [ ] cada `plano` aponta para um arquivo aprovado, ou está na lista do passo 6.

## Para a pessoa aprovar

Uma tabela, sem JSON, a duração estimada (palavras do `texto` ÷ 2,7, mais a duração da aula) e o resultado da
conferência:

| Batida | O que a voz diz | O que aparece |
|---|---|---|
| 1 abertura na mentira | Ela acabou de dizer que as encomendas estão bombando. Teve 3 pedidos no mês. Dois são da mãe. | Bia na festa com o balão «TÁ BOMBANDO!»; etiqueta «3 PEDIDOS NO MÊS» |

## Campos para montar o projeto

Lidos pelo `scripts/montar_projeto.py` e pelo `scripts/segunda_voz.py` (o `narrar.py` e os agentes de cena os ignoram).
Tudo é preso a uma **palavra do bloco** (`cena` + palavra), nunca a um tempo: se a narração mudar, os tempos se refazem.

| Onde | Campo | O que é |
|---|---|---|
| bloco | `ato` | número do ato (1, 2, …) do bloco. Obrigatório; cresce de 1 em 1 e não volta. Um ato = uma janela, um `atoN.html` |
| bloco | `legenda.chave` | lista de palavras ou nomes que a legenda pinta de vermelho (`--a` do legenda-grupos). Vale no episódio todo; a lista de todos os blocos é unida. Opcionais: `chave_b` (ouro, `--b`), `cta` (a palavra do CTA, `--e`), `numeros` (`--n`) |
| raiz | `legenda.fora` | janelas sem legenda, cada uma `{"nome": "...", "de": REF, "ate": REF}` (a legenda sai porque a frase já está grande na tela) |
| raiz | `barra` | lista de eventos da barra de jogo, cada um `{"em": {"bloco": "...", "palavra": "..."}, "faz": "...", ...}` |

**REF** (em `legenda.fora` e no `em` da barra) é um destes:

| REF | Vale |
|---|---|
| `{"bloco": "prazo"}` | o início do bloco (com `"ponto": "fim"`, o fim dele) |
| `{"bloco": "prazo", "palavra": "quarenta"}` | o início da palavra ou frase (`"No último"`) no bloco. `"n": 2` pega a 2ª ocorrência; `"ponto": "fim"` pega o fim; `"desloc": 0.1` soma segundos. Aceita a palavra como falada (`quarenta`) ou como escrita no `texto` (`40`) |
| `{"aula": "silencio_ini"}` | `silencio_ini`, `aula_ini`, `aula_fim` ou `silencio_fim` do `aula-janela.json` |
| `{"video": "fim"}` | a duração da narração |

**Eventos da barra** (`faz`): `relogio` (cai de cima, com `dias`) · `relogio_muda` (gira para `dias`; `giro: [0.45, 0.70]` são os
instantes de pouso, em s depois da palavra) · `medidor` (cai de cima, com `rotulo` e `valor`) · `sai` (sobe e sai, para o
telefone grande) · `corte` (some em 0,02 s, para o cartão cheio) · `volta` (reaparece). O relógio começa nos `dias` do
primeiro `relogio`; o medidor, no `rotulo` e `valor` do primeiro `medidor`. Esse `barra` da raiz não é o `barra` de cada
bloco (que descreve o que o agente de cena vê).

```json
{
  "blocos": [
    {"cena": "prazo", "ato": 1, "legenda": {"chave": ["40 dias"]}, "texto": "E o contrato vence em 40 dias. …"},
    {"cena": "perfil", "ato": 2, "legenda": {"chave": ["Dona Lurdes"]}, "texto": "Por isso, no dia seguinte, … No último post, …"}
  ],
  "legenda": {"fora": [
    {"nome": "aula", "de": {"aula": "silencio_ini"}, "ate": {"aula": "silencio_fim"}},
    {"nome": "cartão final", "de": {"bloco": "opcoes"}, "ate": {"video": "fim"}}
  ]},
  "barra": [
    {"em": {"bloco": "prazo", "palavra": "quarenta"}, "faz": "relogio", "dias": 40},
    {"em": {"bloco": "perfil", "palavra": "seguinte,"}, "faz": "relogio_muda", "dias": 39},
    {"em": {"bloco": "perfil", "palavra": "No último"}, "faz": "medidor", "rotulo": "ABRIR A DOCERIA", "valor": 2},
    {"em": {"bloco": "chamado", "palavra": "isso."}, "faz": "sai"},
    {"em": {"bloco": "ponte", "palavra": "A"}, "faz": "volta"}
  ]
}
```

**Por que o «cartão final» começa no bloco inteiro** (`"de": {"bloco": "opcoes"}`) e não na palavra da pergunta: o cartão
das duas opções entra com o bloco, e a pergunta dele cai na faixa da legenda (y 1440–1580) já na primeira palavra. Com a
janela começando mais tarde (testado com `"palavra": "Comenta"`), as palavras do começo do bloco ainda aparecem por cima
da pergunta, e o `check` acusa `content_overlap` entre a legenda e o texto do cartão (`GRAVA OU ESPERA?`, em 9,7 a
10,2 s). A mesma regra vale para qualquer cartão cheio com texto na faixa da legenda: a janela `fora` começa quando o
cartão entra.

O bloco com `aula_depois` (já descrito acima) é o que o `encaixar_aula.py` usa; sem ele, `--depois <cena>` (a cópia do
roteiro da segunda voz, que o `segunda_voz.py --preparar` cria, já o leva).
