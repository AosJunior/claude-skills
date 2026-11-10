<!-- Modelo do pacote de veiculação: <pasta da série>/epNN/veiculacao.md, escrito no passo 10 por um agente Sonnet e
     aprovado pela pessoa no portão 4. Preencha só a seção do modo da série (biblia.md, «Veiculação») e apague a outra,
     o exemplo do fim e este comentário. Todo número e nome vem do roteiro aprovado e do fatos-verificados.md. -->
# Veiculação: <série>, ep. <N>

- **Arquivo:** `sequencia/exports/<slug>-epNN.mp4` (<duração> s)
- **Modo:** voto real | anúncio fechado
- **Para quem:** <todos | quem assistiu ao ep. N−1>

## As duas palavras

| Palavra | Custo no cartão | Variações cadastradas na automação |
|---|---|---|
| **<PALAVRA1>** | <custa …> | <maiúscula, minúscula, com acento, plural> |
| **<PALAVRA2>** | <custa …> | <…> |

As duas disparam a mesma mensagem.

## Mensagem automática

Curta, sobre a personagem e não sobre quem comentou, com o link da mesma aula que ela assistiu. Sem promessa de
resultado.

> <PALAVRA> anotada. 👀
> Esta é a aula que a <personagem> assistiu: <link da aula>
> <Uma linha sobre a lei que ela aprendeu, nas palavras de quem vende.>

---

## Voto real

**Legenda do post**, nesta ordem:

```
<resumo do episódio em uma linha, com emoji>
<a tentação nova, em uma linha>

<emoji> <PALAVRA1>
<emoji> <PALAVRA2>

Comenta UMA palavra. A mais votada vira o próximo episódio.
<contador: «Dia N de 40» ou «A <prazo> vence em N dias»>
<detalhe escondido, se houver: «Tem 1 detalhe errado nesse vídeo 👀»>

Personagem e história fictícias.
```

**Contagem:** quem conta, quando fecha (até 24 h depois da postagem) e o resultado, com data e hora, no `README.md` da
série. O ep. N+1 só começa depois disso.

## Anúncio fechado

**Texto do anúncio**, na mesma ordem, com estas trocas: o pedido é «Comenta UMA palavra que eu te mando a aula que ela
assistiu.»; nenhuma linha diz que o público decide a história.

```
<resumo do episódio em uma linha, com emoji>
<a tentação nova, em uma linha>

<emoji> <PALAVRA1>
<emoji> <PALAVRA2>

Comenta UMA palavra que eu te mando a aula que ela assistiu.
<contador>

Personagem e história fictícias.
```

**Sequência:** público do anúncio (<quem>), o episódio seguinte (<epNN+1>) e para quem ele vai (<quem assistiu a este>).

## Conferência antes do portão 4

- [ ] as palavras e os custos são os do cartão no vídeo, letra por letra;
- [ ] a automação escuta comentários onde o episódio roda, e as duas palavras foram testadas com um comentário real;
- [ ] a mensagem leva a mesma aula que aparece no telefone da personagem;
- [ ] nenhuma frase afirma atributo de quem assiste nem promete o resultado da personagem;
- [ ] «Personagem e história fictícias.» está no texto;
- [ ] no anúncio fechado, nenhuma linha fala em voto, mais votada ou «vocês».

---

## Exemplo preenchido (inventado)

O ep. 1 da série fictícia «A vitrine da Bia» (exemplo do fim de `biblia.md`), em anúncio fechado.

| Palavra | Custo no cartão | Variações cadastradas na automação |
|---|---|---|
| **GRAVA** | custa a vergonha de aparecer | grava, Grava, GRAVA, gravar |
| **ESPERA** | custa mais uma semana do prazo | espera, Espera, ESPERA, esperar |

> GRAVA anotada. 👀
> Esta é a aula que a Bia assistiu: <link da aula>
> Foto de bolo não vende; vende quem mostra a mão fazendo.

```
🎂 A Bia disse que as encomendas estão bombando. Foram 3 no mês.
📱 E o sinal do ponto vence em 40 dias.

🎥 GRAVA
⏳ ESPERA

Comenta UMA palavra que eu te mando a aula que ela assistiu.
Faltam 40 dias.

Personagem e história fictícias.
```

**Sequência:** público frio de confeitaria e doces; o ep. 2 vai para quem assistiu a este.
