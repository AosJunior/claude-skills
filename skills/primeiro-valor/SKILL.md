---
name: primeiro-valor
description: Primeiro valor de um leigo na primeira sessão. Use ao desenhar ou revisar onboarding, empty state, done state, progresso e streaks, recurso trancado, erro e recuperação, ou uma home com escolhas demais; ao escrever spec de polish desses estados; ao escolher evento de ativação e métrica, por que a retenção não sustenta, ou quando entra o upsell.
---

# Primeiro valor

Como a tela conduz alguém que nunca fez aquilo até o primeiro valor. O caso típico é a **maldição do conhecimento**: o produto do expert recebe o leigo, e a primeira tela pressupõe o que só o expert sabe. O caso silencioso é o produto feito para o leigo cuja primeira tela parece a vigésima: a mesma folha antes e depois do primeiro dado.

| Sintoma | Conceito (em [conceitos.md](conceitos.md)) |
|---|---|
| sem onboarding | **Time-to-value e momento aha** |
| empty state que só anuncia ausência | **Empty state em quatro níveis** |
| sem contraste para o que gera valor | **Hierarquia por valor** |
| home com escolhas demais | **Carga de decisão e próxima melhor ação** |

## Saída

Uma tabela, lacunas primeiro, ordenadas por quantos gestos faltam do estado até o primeiro valor (menos gestos vem antes); os estados depois do primeiro valor vão ao fim, na ordem em que ocorrem:

`estado · condição que o produz · o que a tela mostra hoje · fonte (código/captura/uso) · conceitos · classe · o que muda · gesto esperado · referência (opcional)`

Reforços e estados que não se aplicam vão em rodapé, uma linha cada, com o porquê de o Padrão estar satisfeito ou de o estado não existir, sem item de spec. Abaixo, as decisões de produto: `pergunta · opção A e custo · opção B e custo · recomendação se o dono não responder` (a recomendação é default, não decisão). Entra na spec em andamento quando houver; senão vai inteira na resposta.

## Passos

0. **Levantar o contrato.** Cinco linhas: quem chega; gesto de valor (ou "não decidido": proponha o candidato de **Time-to-value e momento aha** e vire pergunta); cadência (por dia, por semana, contínua, nenhuma; uma por caminho quando o valor tem dois caminhos); do que o valor depende que o usuário pode adiar ou falhar (conectar conta, instalar snippet, convidar, importar); o que o dono já decidiu. Feito quando as cinco linhas existem; "não sei" é resposta válida e vira pergunta do passo 4.

1. **Nomear os estados.** Derive por perguntas: antes do primeiro dado · sem dado por escolha (pulou o setup) · aguardando algo externo (carregando, sincronizando, escutando o primeiro evento) · com erro, e como sai · com dado · com dado insuficiente para o objeto ter forma · depois da ação primária [se cadência] · quase na meta [se meta] · bloqueado (plano, tempo, permissão) · retorno (segunda sessão) · recaída (falhou ou sumiu e voltou). Depois derive os do produto: todo ramo que troca o herói, o rótulo da ação primária ou o que a tela pede vira estado. Defina em uma frase os estados que se confundem (primeira vez = a primeira abertura; vazio = sem dado, pode durar dias). Feito quando todo ramo do código ou da captura que troca herói, rótulo da ação primária ou pedido está listado ou marcado "renderiza igual a <estado>" (é achado, vai ao passo 2); cada estado tem condição, render e fonte; e os que não se aplicam estão listados como tal.

2. **Classificar contra o catálogo.** Para cada estado, liste **todos** os conceitos de [conceitos.md](conceitos.md) cujo *Sinal de lacuna* aparece, cada um com a própria classe: **lacuna** (ao menos um elemento do Padrão não existe no estado), **reforço** (o Padrão inteiro existe e só muda a intensidade), **decisão de produto** (mudar depende de escolha que só o dono faz; já aqui com as duas opções e o custo de cada). Lacuna cuja correção depende de escolha do dono entra nas duas listas. Feito quando cada estado tem sua lista (conceito, classe) e cada decisão está na lista separada com pergunta, opções e custos.

3. **Aplicar só nas lacunas.** O item nomeia o **estado**, não só a tela ("`/hoje` no dia 1"; "dashboard sem snippet instalado"), cumpre a linha Padrão do conceito que o motivou e as duas regras transversais. Com a skill `refero-design` disponível, rode `refero_search_screens` com a linha **Buscar** do conceito com lacuna (as marcadas `(flows)` vão em `refero_search_flows`) e registre o achado na coluna referência. Feito quando cada lacuna tem item com estado, gesto esperado e o que muda, e o item nomeia o elemento do Padrão que faltava (o mesmo que motivou a classe lacuna no passo 2).

4. **Entregar as perguntas ao dono.** Confira que toda decisão de produto está na lista separada e que cada item de spec cita só o que o dono já decidiu. Feito quando a lista de decisões está completa (pergunta · A e custo · B e custo · recomendação).

Quando a pergunta for "o que medir", "por que o hábito não sustenta" ou "quando entra a oferta", leia [fora-da-tela.md](fora-da-tela.md).

## Regras transversais

Valem em todo item que a skill produz, esteja o conceito na lista do estado ou não; a regra de cada conceito vive na linha Padrão do catálogo.

- **Um acento visual por tela** (Padrão de **Hierarquia por valor**). Quando dois Padrões disputam o acento no mesmo estado, o acento vai ao gesto que a pessoa completa sem sair do app; o pedido de confiança (conta, permissão) vem no estado seguinte, ou vira decisão de produto com os dois custos.
- **Toda quebra de convenção tem saída convencional** (Padrão de **Saída sem culpa**): a identidade surpreende no gesto de entrada; o gesto de sair é o que todo app tem.
