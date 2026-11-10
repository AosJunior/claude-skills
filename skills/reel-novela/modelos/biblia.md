<!-- Modelo da bíblia de uma série da novela. Copie para <pasta da série>/biblia.md e preencha com a pessoa numa
     rodada de perguntas só (passo 1 do SKILL.md). Cada campo fica preenchido ou marcado «não se aplica» pela pessoa.
     Depois do portão 1, mudança entra como adendo datado no topo. No fim deste arquivo há um exemplo preenchido,
     inventado; apague-o e este comentário na cópia. -->
# Série: <título curto>

Estado: <rascunho | aprovada em DD/MM/AAAA>. Episódio atual: <N>.

## Adendos

<!-- AAAA-MM-DD: o que mudou, quem pediu, a frase literal. O mais novo em cima. -->

## Oferta e aula

- **Oferta:** <nome, preço, o que é>, com a fonte no `fatos-verificados.md`.
- **Aula que a personagem assiste:** <qual vídeo de quem vende, arquivo ou link>. É o mesmo que a mensagem automática
  entrega. Autorização de uso: <de quem, em que data>.
- **Leis da aula** que a série usa, uma por episódio, cada uma com o trecho em `aula/<lei>.mp4` (início e fim na fonte)
  e a frase literal de quem vende:
  - Ep. 1: «…» (`aula/<lei>.mp4`, MM:SS–MM:SS)

## Veiculação

- **Modo:** voto real | anúncio fechado (`SKILL.md`, «Modos de veiculação»).
- **Automação:** <ferramenta>, as palavras de cada episódio e o link da aula. Conferido que ela escuta o comentário
  onde o episódio roda (perfil ou anúncio): sim | não.
- **Cadência:** <um por dia | ordem do remarketing>.

## Premissa

<Uma frase: quem é a personagem, a mentira ou o problema, o prazo e o que ela perde se o prazo vencer.>

## Relógio e medidor

- **Relógio:** «Faltam <N> dias». <Por que esse prazo; de preferência, o prazo da própria oferta.>
- **Medidor:** «<Chance de …>: <N>%». Valor por episódio: <ep. 1 → ep. 2 → ep. 3>, subindo até 5 pontos por vez.

## Elenco

| Personagem | Função na história | Cor-assinatura e marcas fixas | Poses além das mínimas |
|---|---|---|---|
| **<protagonista>** | <o que ela quer e o que a atrapalha> | <hex; marcas> | <…> |
| **<testemunha>** | testemunha e apoio; a graça carinhosa | | |
| **<antagonista>** | a injustiça e a tentação de copiar | | |
| **<tentação>** | o atalho | | |
| **<dono do prazo>** | o prazo; só em mensagem | foto de perfil e nome | não tem |
| **<quem vende>** | ele mesmo, em vídeo real na tela do telefone | não tem | não tem |

## Cenários e luz

| Lugar | Frente · meio · fundo | Três objetos que caracterizam | Luz |
|---|---|---|---|
| <lugar> | <objeto cortado embaixo> · <personagem> · <fundo iluminado> | <…> | quente · fria · cor do antagonista |

Regra de luz da série: <quente quando…, fria quando…, <cor> quando…>.

## Pele da camada de jogo

As cores e a fonte da barra do topo, das telas chapadas, das etiquetas e do cartão das duas opções. Vêm da pele da
oferta, para o vídeo combinar com a página da aula. Viram os tokens `--nv-*` do `componentes/novela.css` da série.

- Fundo chapado: <hex> · borda: <hex> · vermelho de alerta: <hex> · as duas cores do cartão: <hex> e <hex>
- Fonte: <família e pesos, com o caminho do arquivo; a biblioteca traz a Montserrat>

## Narrador

- **Voz:** <nome e `voice_id`>, eleven_v4 a 1,25×, escolhida nas amostras de DD/MM/AAAA.
- **Tom:** terceira pessoa, seco, telegráfico, com graça nas provas.
- **Trilha:** <trilha do Epidemic, com o porquê em uma frase | só efeitos>.

## Episódios

Cada episódio segue a grade (`referencias/grade-de-batidas.md`). Uma tabela por episódio:

### Ep. <N>: <título> (<para quem: nunca viu | viu o anterior>)

| Batida | Conteúdo |
|---|---|
| Abertura | <a frase do gancho e a prova contra> |
| … | … |
| A aula | <quem manda, a lei, o trecho> |
| Medidor | <N>% |
| Duas opções | **<PALAVRA>** (custa <…>) ou **<PALAVRA>** (custa <…>) |

## Limites desta série

- Ficção declarada: <onde aparece>.
- Resultado da personagem: <o que ela conquista, pequeno de propósito>.
- O que a série não afirma em nome próprio: <ex.: nenhuma promessa de faturamento>.
- Política de anúncios conferida em <data>: <o que vale para esta persona>.

## Pendências com a pessoa

1. <…>

---

## Exemplo preenchido (inventado)

Uma série fictícia, só para mostrar o nível de detalhe. A oferta, a professora e as personagens não existem; o mesmo
exemplo aparece em `roteiro-episodio.md` e `veiculacao.md`.

- **Série:** A vitrine da Bia. **Modo:** anúncio fechado. **Cadência:** ordem do remarketing.
- **Oferta:** «Vitrine Cheia», curso online de vendas pelo Instagram para confeitaria, R$ 497 (fictícia).
- **Aula:** a aula gratuita da professora do curso; ep. 1, lei «Foto de bolo não vende; vende quem mostra a mão
  fazendo» (`aula/lei-1.mp4`).
- **Premissa:** Bia, confeiteira há 9 anos, faz bolo por encomenda na cozinha de casa e reservou um ponto para abrir a
  doceria com vitrine que desenhou aos 20 anos; o sinal vence em 40 dias, e sem encomenda ela perde o ponto.
- **Relógio e medidor:** «Faltam 40 dias» (o sinal do ponto) · «Chance de abrir a doceria»: 2% → 4% → 7%.

| Personagem | Função na história | Cor-assinatura e marcas fixas |
|---|---|---|
| **Bia** | quer a doceria; esconde que as encomendas não vêm | mostarda `#E0A526`; avental mostarda, lenço vermelho no cabelo, tênis branco; de costas, o laço grande do avental |
| **Dona Lurdes** | vizinha e cliente mais fiel; testemunha e apoio | verde-água `#4FA89A`; óculos na corrente, sacola de feira |
| **Rafa** | a doceria da esquina que posta todo dia; a tentação de copiar | roxo `#7B3FA0`; dólmã roxa, telefone sempre na mão |
| **Kiko** | o sobrinho que vende pacote de seguidores; o atalho | verde-limão `#9BC53D`; boné virado, fone no pescoço |
| **Seu Orlando** | dono do ponto; o prazo, só em mensagem | foto de perfil e nome |
| **A professora do curso** | ela mesma, em vídeo real na tela do telefone | não tem |

| Lugar | Frente · meio · fundo | Três objetos | Luz |
|---|---|---|---|
| festa da prima | mesa de doces cortada embaixo · Bia · salão com varal de luz | bolo de três andares, copo de refrigerante, balões dourados | quente |
| cozinha de casa | bancada com farinha · Bia · janela no fim de tarde | batedeira velha, caderno de receitas, pote de granulado | fria |
| quarto, madrugada | travesseiro · Bia com o telefone · parede escura | ring light desligado, avental na cadeira, calendário | tela-azul |

Ep. 1 (nunca viu): abertura «Ela acabou de dizer que as encomendas estão bombando. Teve 3 pedidos no mês. Dois são da
mãe.»; a aula chega pela Dona Lurdes («Minha neta assistiu isso»); duas opções **GRAVA** (custa a vergonha de
aparecer) ou **ESPERA** (custa mais uma semana do prazo).
