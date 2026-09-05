# Catálogo de conceitos

Referência do passo 2 de [SKILL.md](SKILL.md): por estado, os conceitos cujo **Sinal de lacuna** aparece, o **Padrão** que o item cumpre e a linha **Buscar** (inglês, para o acervo; `(flows)` quando é jornada).

## Time-to-value e momento aha

O tempo entre o cadastro e a primeira vez que a pessoa sente o valor prometido; o momento aha é o gesto que, feito, faz a pessoa ficar. Quando o dono não decidiu, proponha um candidato: o primeiro objeto que o produto devolve e que a pessoa não teria feito sozinha (ex.: a grade da semana montada; a primeira categorização automática dos gastos; o primeiro gráfico com evento real).

- **Sinal de lacuna:** ninguém diz qual gesto, se a pessoa fizer, ela fica; o onboarding termina numa tela em branco.
- **Padrão:** decisão de produto com candidato proposto; o onboarding termina no objeto que o gesto produz, e cada estado puxa em direção a ele.
- **Buscar:** `onboarding to first success completion moment` (flows)

## Hierarquia por valor

Peso visual distribuído pelo valor que cada ação gera: um acento na que gera mais (ex.: registrar o post de hoje pesa mais que o menu; "conectar conta" pesa mais que "explorar categorias").

- **Sinal de lacuna:** dois elementos com peso de CTA na mesma tela; a ação de valor pesa igual ao menu.
- **Padrão:** um acento por tela na ação primária; o resto cede (cor neutra, tamanho menor, ou atrás de um gesto).
- **Buscar:** `single primary action emphasis dashboard hierarchy`

## Carga de decisão e próxima melhor ação

Sobrecarga de escolha (Iyengar & Lepper 2000). As meta-análises (Scheibehenne, Greifeneder & Todd 2010; Chernev, Böckenholt & Goodman 2015) acham efeito médio pequeno, forte quando quem escolhe não tem preferência formada e as opções se parecem: o leigo na primeira sessão.

- **Sinal de lacuna:** nenhuma ação domina; nenhuma responde "o que eu faço agora?".
- **Padrão:** um card (Duolingo "Continue", Linear Inbox, Headspace "Today"), o resto rebaixado ou atrás de um gesto; o aberto acima do feito (Zeigarnik/Ovsiankina como heurística; replicações fracas). Ex.: "seu post de hoje" acima da grade; "instale o snippet" acima dos gráficos vazios.
- **Buscar:** `home continue where you left off single recommended action`

## Empty state em quatro níveis

Estado sem dado que ensina o próximo gesto. Quatro níveis: **declarativo** ("não há nada aqui") · **instrutivo** (o gesto e o porquê: "+ sua foto") · **demonstrativo** (o fantasma do objeto futuro já no lugar, com "faltam X"; ex.: a escada de marcos no dia 1; o gráfico de gastos em cinza com "conecte para preencher") · **dados de exemplo / caminho manual** (o objeto inteiro funcionando com dado rotulado como exemplo; entrada manual como alternativa ao conector; "enviar instruções para quem instala" quando o setup é de outra pessoa: Mixpanel, PostHog, templates do Notion).

- **Sinal de lacuna:** a tela sem dado é a tela com dado, só que vazia; sem setup a home é bloqueio.
- **Padrão:** demonstrativo sempre que o objeto futuro tem forma conhecida; quarto nível quando o valor depende de setup adiável ou de outra pessoa.
- **Buscar:** `empty state ghost placeholder preview of future content` · `sample data demo mode before integration connected`

## Objeto degenerado

Dado real, mas pouco para o objeto ter forma: gráfico de uma fatia, categoria "Outros" dominante, média de um item. Ex.: a grade da semana com um post só; a rosca 100 % "Mercado" após o primeiro lançamento; o funil com um evento.

- **Sinal de lacuna:** o objeto renderiza com dado real e não diz nada; nenhuma linha diz quanto falta.
- **Padrão:** "faltam ~N para <o objeto falar>" + a ação que completa (classificar os N, lançar mais) no acento; o resto do objeto em fantasma, como no demonstrativo.
- **Buscar:** `not enough data yet chart partial state`

## Estado pós-ação (done state) [se houver cadência]

Depois do gesto do ciclo, a tela vira outra folha: confirmação, consequência visível e uma próxima ação. Ex.: post registrado → ofensiva +1 e "amanhã: …"; gasto categorizado → saldo do mês atualizado e "próximo: revisar assinaturas".

- **Sinal de lacuna:** depois do gesto principal só o botão muda de cor.
- **Padrão:** confirmação + consequência visível + uma "próximo: …". Um estado é uma folha com conteúdo próprio.
- **Buscar:** `all done for today completed state` (acervos rendem mais em `done state` que em `habit`)

## Progresso concedido

Progresso que começa acima de zero é mais completado (Nunes & Drèze 2006), mais ainda quando vem com a razão ("porque você já se cadastrou"). Honesto quando o passo concedido é real e nomeado; "25 %" sem dizer o quê é contador falso. Streak/ofensiva nasce em zero por definição; o contador da jornada (dia, etapa) nasce acima de zero (ex.: "dia 1 de 40" nasce em 1; "1 de 4: conta criada, falta conectar o banco").

- **Sinal de lacuna:** barra em 0 %, contador em zero, ou nenhum progresso mostrado onde já houve um passo cumprido.
- **Padrão:** o cadastro acende o primeiro ponto, nomeado, com a razão.
- **Buscar:** `progress bar starts partially complete onboarding`

## Gradiente da meta [se houver meta]

O esforço acelera perto da meta (Hull 1932; Kivetz, Urminsky & Zheng 2006). 95 % parece diferente de 30 % (ex.: dia 38 de 40; R$ 9.400 de R$ 10.000 da reserva).

- **Sinal de lacuna:** a reta final usa a mesma folha do meio do caminho.
- **Padrão:** brilho, tamanho ou fita quase cheia crescem com a proximidade; "faltam X" em destaque quando X é pequeno.
- **Buscar:** `almost there final stretch progress emphasis`

## Revelação progressiva e teaser trancado

Mostrar o necessário agora e anunciar o resto. Anunciar é o default; esconder é exceção que o dono assina (decisão de produto, com custo). Trancado = visível, com a condição que abre: data, nível, plano, dado suficiente (ex.: aba "semana 2" trancada com a data; "relatório anual" trancado com "após 30 dias de dados"; "funis" trancado com "no plano Pro").

- **Sinal de lacuna:** rota que redireciona antes de abrir; recurso que aparece sem aviso num dia qualquer.
- **Padrão:** item visível, trancado, com a condição que abre escrita ao lado.
- **Buscar:** `locked feature unlock later teaser tab`

## Checklist de começo (getting started)

3–5 gestos de setup com progresso, que some ao cumprir (Slack, Notion, Linear, Stripe); o primeiro item já marcado. Ex.: "foto · nicho · primeiro post"; "conta criada ✓ · conectar banco · definir meta"; "conta ✓ · instalar snippet · primeiro evento".

- **Sinal de lacuna:** o valor depende de 2+ passos e a home não diz em qual a pessoa está.
- **Padrão:** lista curta no lugar da home, primeiro item marcado, some ao cumprir.
- **Buscar:** `getting started checklist card home progress`

## Fase inicial nomeada

Quando a primeira fase é diferente por construção (semana de leitura, trial, modo demo), o nome dela visível onde a cobrança apareceria. Ex.: "semana de leitura, sem post cobrado" na home; "14 dias de trial, dados de exemplo"; "modo demo até o primeiro evento".

- **Sinal de lacuna:** a primeira fase é apresentada como um dia qualquer.
- **Padrão:** nome da fase + o que ela dispensa + quando termina, no lugar do contador ou da cobrança.
- **Buscar:** `trial mode banner first week onboarding phase`

## Dica contextual única

Uma dica, no lugar, só na primeira vez, some após o gesto (ex.: "toque para ver o conteúdo de hoje"; "cole o snippet antes do `</head>`"; "arraste para categorizar").

- **Sinal de lacuna:** tour de várias telas no primeiro acesso; ou nenhuma dica onde o gesto não é óbvio.
- **Padrão:** uma dica ao lado do objeto, uma vez, some com o gesto.
- **Buscar:** `single contextual hint first time tooltip`

## Auto-segmentação na entrada

Pedir na entrada o eixo que muda o caminho (ritmo, nível, objetivo, papel, tamanho) e devolver a escolha na tela, para o leigo se comparar ao ritmo que ele mesmo escolheu. Papel diferente (quem instala não é quem lê) pede handoff. Ex.: "você escolheu 5 por semana" na home; "meta: guardar R$ 500/mês" no topo; "enviar o snippet para o dev".

- **Sinal de lacuna:** a escolha do onboarding some da interface depois; um só caminho para expert e leigo.
- **Padrão:** a escolha visível onde a cobrança aparece; handoff quando o papel é outro. Decisão de produto quando mostrar expõe comparação indesejada.
- **Buscar:** `onboarding choose your pace level beginner` (flows)

## Ciclo de investimento (Hook, Nir Eyal 2014)

Gatilho → ação → recompensa variável → investimento. Investimento é o que a pessoa deposita (registro, categoria corrigida, tag) e o produto devolve (histórico, relatório, recomendação); honesto quando devolve valor real. Ex.: o post registrado entra na grade na hora; o gasto corrigido muda a projeção do mês.

- **Sinal de lacuna:** o formulário salva e a tela volta ao que era.
- **Padrão:** o item entra na história no mesmo gesto, visível.
- **Buscar:** `log entry then see it added to history immediately` (flows)

## Pedido de permissão no momento do valor

Notificação, localização e conexão bancária são pedidos de confiança: pedir depois de a pessoa ter sentido o valor. Ex.: pedir notificação depois do primeiro post registrado ("quer o lembrete de amanhã?"); pedir a conexão bancária depois de a pessoa ver o resumo de exemplo.

- **Sinal de lacuna:** diálogo nativo na primeira abertura; pedido negado que nunca volta.
- **Padrão:** tela própria com o porquê, depois do primeiro valor; quando o dado é sensível, o porquê vem com o que o produto não pode fazer (não vê senha, não movimenta); se negado, um lembrete no lugar do valor que a permissão liberaria.
- **Buscar:** `permission priming screen before system prompt` (flows)

## Erro e recuperação do gesto

O leigo não sabe se foi ele ou o sistema (Nielsen #9). Ex.: o upload da foto falhou; a conexão bancária caiu; o snippet foi colado no lugar errado.

- **Sinal de lacuna:** erro em código ou frase genérica; o que a pessoa digitou some; o gesto de saída fora do acento.
- **Padrão:** o que aconteceu em uma linha, de quem é (você ou nós), o gesto de saída no acento, o que a pessoa fez preservado.
- **Buscar:** `inline error recovery retry friendly message`

## Recaída e volta

Quem falhou (streak zerada) ou sumiu e voltou vê tela própria, com caminho de recomeço. Ex.: "você parou no dia 12: recomece de onde parou ou do zero"; "3 semanas sem registrar: importe o período ou comece de hoje".

- **Sinal de lacuna:** quem voltou vê a mesma tela de quem nunca falhou.
- **Padrão:** o intervalo reconhecido em uma linha + uma ação de recomeço no acento; a streak zerada com o histórico preservado.
- **Buscar:** `welcome back streak lost restart screen`

## Retorno (segunda sessão)

A primeira sessão vende, a segunda decide: retomar no lugar certo, contexto de ontem em uma linha, dica da primeira vez já sumida. Ex.: "ontem você registrou; hoje é dia 2"; "desde ontem: 3 gastos novos"; "primeiros 120 eventos recebidos".

- **Sinal de lacuna:** a segunda abertura renderiza igual à primeira (dica de novo, home sem "desde a última vez").
- **Padrão:** uma linha de "desde a última vez" + a próxima melhor ação; a dica sumiu.
- **Buscar:** `returning user welcome back what changed since`

## Pico-fim

A memória é o pico mais o fim (Kahneman, Fredrickson, Schreiber & Redelmeier 1993); o pico pode ser negativo. O fim do ciclo (ex.: retrospectiva dos 40 dias; relatório do mês; fim do trial) recebe o tratamento mais singular; o erro mais provável recebe recuperação desenhada.

- **Sinal de lacuna:** a tela final usa mais o esqueleto padrão que qualquer outra; o erro mais frequente cai no toast genérico.
- **Padrão:** fim do ciclo com folha própria; o erro mais provável tratado por **Erro e recuperação do gesto**.
- **Buscar:** `end of cycle summary celebration recap screen`

## Básicos antes do encanto

Kano: o básico ausente destrói, o encanto presente só soma. A estética compra tolerância para a função (Kurosu & Kashimura 1995; Tractinsky, Katz & Ikar 2000). Visibilidade do estado do sistema (Nielsen #1) com os três limites (Nielsen 1993; Miller 1968): 0,1 s = reconhecimento do toque (estado pressionado, UI otimista); até 1 s sem indicador; >1 s skeleton com a forma do que vem; >10 s progresso com estimativa e cancelar. Ex.: registrar o post responde em 0,1 s; sincronizar o banco mostra o skeleton do extrato; importar histórico mostra "3 de 12 meses · cancelar".

- **Sinal de lacuna:** texto cortado, controle preso, toque que grava sem resposta, espera sem forma.
- **Padrão:** todo texto inteiro, todo controle solto, todo toque que grava reconhecido em 0,1 s, toda espera com a forma do que vem.
- **Buscar:** sem busca útil em acervo

## Saída sem culpa

Lei de Jakob: a quebra por identidade tem gesto convencional de saída. Contadores reais, cancelamento à vista, saída sem culpa: a confiança que a estética conquistou é o que padrões escuros gastam. Ex.: "faltam 3" só quando faltam 3; cancelar o desafio em um toque; desconectar o banco na mesma tela que conectou.

- **Sinal de lacuna:** contador que mente; cancelar atrás de menu; "tem certeza?" com o botão de ficar no acento.
- **Padrão:** contador real; cancelar, desconectar e sair onde entrou, com um gesto e confirmação neutra.
- **Buscar:** `cancel subscription flow no dark pattern` (flows)

## Sinal de coorte

Pertencimento é o que mais falta num produto usado sozinho (Deci & Ryan); um número de outras pessoas fazendo o mesmo gesto é a peça barata. Ex.: "38 pessoas registraram hoje"; "12 contas do seu porte fecharam o mês"; "1.200 sites receberam o primeiro evento esta semana".

- **Sinal de lacuna:** nenhum traço de outras pessoas em nenhuma tela; o número, quando existe, é inventado.
- **Padrão:** um número real de coorte na home, perto do gesto de valor, só quando o número é honesto (ver **Saída sem culpa**).
- **Buscar:** `social proof others active today community count`
