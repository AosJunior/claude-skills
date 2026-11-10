# Briefing do orquestrador de área

Modelo do briefing que você escreve para o agente que toca uma área inteira
([`../referencias/orquestracao.md`](../referencias/orquestracao.md), «Orquestrador por área»). Copie para
`<ep>/sequencia/revisao/briefing-area-<área>.md`, preencha os `<…>` e apague o que não vale.

```markdown
# Briefing: orquestrador da área <elenco | roteiro e voz | motion> · <série> ep. <NN>

Você toca esta área do começo ao fim: lança os agentes, julga o que voltar, manda corrigir e me devolve um relatório
curto. Você não executa ato, voz nem pesquisa por conta própria, e não fala com a pessoa.

## O pedido, nas palavras da pessoa
> «...» (com a data), e o que ela já aprovou e reprovou, também nas palavras dela.

## A área
- Passos: <N a M> de <pasta desta skill>/SKILL.md. Leia só esses passos e, de `referencias/orquestracao.md`, as seções
  «Atos em paralelo», «Briefing autocontido», «Um dono por arquivo» e «Render numa cópia».
- Entrada: <pasta da série>/README.md, biblia.md, <ep>/roteiro.json, <os arquivos que a área recebe prontos>.
- Pronta quando: <o critério do último passo da área, com os números>.
- Você para e me devolve em: <o portão, se houver> e no fim.

## Quem você lança
Um briefing autocontido por agente, pelos modelos da skill (`modelos/briefing-ato.md`, `modelos/briefing-som.md`).
Passe `model` e `effort` em todo lançamento, por esta tabela, sem decidir caso a caso:

| O trabalho é | Modelo | Esforço |
|---|---|---|
| um script ou comando que já existe | nenhum agente: você roda, com `| tail -5` | — |
| mecânico, com laço e conferência | haiku | low |
| mecânico que gasta crédito ou escolhe take | sonnet | medium |
| repetição de um padrão aprovado; som | sonnet | high |
| novo e difícil | opus | high |
| julgar o trabalho de outro | opus | high |

<a lista dos agentes desta área, com o arquivo de que cada um é dono e o que roda em paralelo>

- Agente que falha duas vezes na mesma coisa: abra um novo, um degrau acima, com o que já foi tentado.
- Peça a cada agente o resumo «em até 10 linhas, sem colar código».
- Não lance revisor de olhos novos: essa revisão é minha.

## Você julga
Abra os snapshots e a folha de contato que os agentes apontarem e confira pela régua (<ep>/sequencia/motion/briefings/
_regua.md e <pasta desta skill>/referencias/regua-visual.md). Mande a correção ao dono do arquivo por SendMessage. Só
me devolva o que passou.

## Limites
- Gasto: <teto de crédito de voz e imagem, com o sim da pessoa e a data>. Acima disso, pare e me avise.
- Arquivo de chave você não abre nem copia: os scripts leem a chave (<caminho do arquivo da chave, se houver>).
- Teto: uns <60> turnos seus. Perto disso, feche o que estiver aberto e devolva com as pendências.

## Devolva
1. O relatório completo em `<ep>/sequencia/revisao/area-<área>.md`: o que cada agente fez, os caminhos, as medidas,
   o que você mandou corrigir e o que ficou pendente.
2. Na resposta, até 15 linhas: pronto ou não (com os números do critério), os caminhos da prévia e do final, o que eu
   preciso decidir e as pendências. Sem colar código nem log.

Esforço: high.
```

O pedido vai entre aspas, como a pessoa disse. A tabela do roteador vai inteira no briefing: o orquestrador não lê a
referência de novo para escolher modelo.
