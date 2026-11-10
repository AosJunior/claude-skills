<!-- Modelo do briefing de um ato: <ep>/sequencia/motion/briefings/atoN.md. O agente do ato sabe só o que está aqui,
     na _regua.md e no README dos componentes. Quem escreve troca cada {{…}}, apaga este comentário e confere três
     coisas antes de abrir o agente:
     - cada texto de tela está no roteiro.json, na forma exata, e cada número, no fatos-verificados.md;
     - cada batida tem a palavra que a dispara e o tempo dela, tirado do briefings/palavras-voz.json;
     - o ato recebe o que o anterior entrega (tabela de fronteiras da _regua.md). -->
# Ato {{N}} ({{início}}–{{fim}} s): {{o que o ato mostra, em poucas palavras}}

Arquivo `compositions/ato{{N}}.html`, id `ato{{N}}`, prefixo `a{{N}}-`. O ato já está no `index.html` com
`data-start="{{início real}}" data-duration="{{duração}}"`, e no código `T0 = {{início no tempo do código}}`. Leia
antes a `briefings/_regua.md` e o README dos componentes que ela aponta.

## Fala

Início de cada palavra, no tempo do código; `|` marca pausa ou fim de frase.

{{palavra@tempo palavra@tempo … | palavra@tempo … | (próximo ato: palavra@tempo)}}

## Planos

| Em (palavra@tempo) | Cenário | Personagem e pose | Luz | Movimento |
|---|---|---|---|---|
| {{Ela@0.12}} | `{{assets/cenarios/festa/}}` | `{{assets/elenco/bia/sorriso-amarelo.png}}` | {{quente}} | {{empurrão 1,00 → 1,06}} |

Copie para `assets/ato{{N}}/` só o que este ato usa, das pastas `elenco/` e `cenarios/` da série.

## Textos

| Em (palavra@tempo) | Voz | Texto exato | Componente |
|---|---|---|---|
| {{Teve@1.84}} | etiqueta vermelha | {{3 PEDIDOS NO MÊS}} | `NOVELA.etiqueta` |

Nada além destes textos. Fora deles, nenhuma afirmação nova.

## Ideia

{{Uma ou duas frases: a imagem que o ato constrói, quem é o protagonista de cada momento e por quê.}}

{{Só no ato 1: no quadro 0 algo já se lê e algo se move. Do ep. 2 em diante, a devolução («Vocês escolheram: X» ou o
que ela fez) está na tela no quadro 0.}}

## Batidas

Tempo do código; ajuste fino pela fala.

1. **{{início}}–{{fim}}, «{{trecho da fala}}».** {{O que entra, onde e por quê; a palavra que dispara cada mudança.}}
2. **{{…}}, «{{…}}».** {{A mudança e o que na tela a causa.}}
3. **{{saída}}.** {{O que o ato entrega: o último quadro que segura de T até T + 0,30.}}

## Roletas

{{Só se o ato gira algum número além da barra: nome `a{{N}}-…`, valor, início, pousos, cor, semente
(`referencias/roleta.md`). O relógio e o medidor são da barra: não registre.}}

## Recebe e entrega

- **Recebe:** {{o último quadro do ato anterior, que segura até T + 0,30}}. A transição de entrada é sua
  ({{chicote para a esquerda | corte}}).
- **Entrega:** {{o que fica na tela no fim}}. Nada do ato aparece depois da janela.

## Conferência mínima no snapshot

`--at {{tempos reais das palavras-gatilho e de T − 0,2 e T + 0,1 das fronteiras, de briefings/tempo-real.cjs}}`. Olhe
cada quadro: {{um protagonista; três planos; luz do código; nenhum texto sobre outro nem na faixa da barra; a
personagem igual à folha}}.

## Devolva

Em até 10 linhas, sem colar código: as batidas com o tempo de cada uma, os snapshots (pasta), o resultado do `check` e
do `conferir-faixa`, e o que ficou pendente.

Esforço: high. Teto: uns 40 turnos.
