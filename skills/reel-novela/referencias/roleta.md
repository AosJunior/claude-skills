# Roleta: o número que gira

Na novela, giram na roleta o relógio («FALTAM 30 DIAS») e o medidor da barra de jogo quando mudam, e qualquer número
que um ato decida girar. Cada dígito é um rolo que troca em passos rápidos e perde força até travar no seu pouso; a
trava é um estalo em y com flash e halo na cor do número, nunca escala.

| Arquivo (no projeto motion) | Papel |
|---|---|
| `assets/roleta.js` | o motor (`window.ROLETA`); ninguém edita |
| `assets/roletas.js` | o registro dos números (`window.ROLETAS`), um bloco por dono |
| `briefings/roleta-ticks.cjs` | os eventos de som de todo número registrado, no tempo real |

O bloco da barra no `roletas.js` é gerado pelo `montar_projeto.py` a partir da lista `barra` do `roteiro.json`, com
os pousos nos `giro` de cada `relogio_muda`. Nenhum ato edita esse bloco.

## Registrar um número num ato

No bloco do ato (`// ---------- atoN (aN-) ----------`), sempre com Edit, sem reescrever o arquivo:

```js
Object.assign(window.ROLETAS, {
  "a3-pedidos": {
    valor: "12",                      // número final, com a pontuação
    inicio: 30.1,                     // começo do giro, no tempo do código
    pousos: { de: 31.2, ate: 31.5 },  // primeira e última trava, no tempo do código
    ordem: "esq-dir",
    cor: "#ffd23f",                   // cor na trava
    semente: 12,                      // outra semente = outra sequência
    acender: 0.5,                     // número que nasce na tela
  },
});
```

- Tempos do código (os do `palavras-voz.json`); a cena converte pelo `a()` e o som pelo `VOZ.w`.
- Pelo menos 0,6 s entre o `inicio` e a primeira trava: com menos, não se lê como roleta.
- Números lado a lado: mesmos tempos, sementes diferentes.
- Registre só o que o ato anima: o som sai de tudo o que está registrado.

## Usar e conferir

```js
const num = $("#a3-num");
ROLETA.montar(num, ROLETAS["a3-pedidos"]);
const r = ROLETA.animar(tl, num, ROLETAS["a3-pedidos"], a);   // {inicio, travas, ultima, fim}, no tempo local
```

- Só o hospedeiro se anima (`autoAlpha`, `y`, `color`); tween dentro do número briga com o motor.
- Um giro por vez no mesmo elemento; o próximo começa depois da `ultima` + 0,75 s.
- Deixe uns 40 px livres em volta (flash e halo vazam de propósito) e nenhum `overflow: hidden` mais baixo que o
  `line-height`. O `line_unread` do `check` nos dígitos é falso positivo.
- Conferência: `node briefings/roleta-ticks.cjs --travas <nome>` dá as travas em tempo real. Snapshot no `inicio`
  (já girando, nenhum número errado legível), em cada trava e na `ultima` + 0,8 s (o número final limpo, igual ao do
  roteiro).
- Som: a roda de prêmios só no principal de cada ato ([`som.md`](som.md), «Roleta»).
