# Lições da novela

O porquê de cada regra desta skill, medido nas séries que produzimos. Leia quando uma regra parecer exagerada, quando
a pessoa reprovar algo ou antes de mudar um passo. As lições de voz, som e movimento que valem para qualquer vídeo
narrado por IA já estão escritas como regra, com o porquê, em `voz.md`, `som.md`, `movimento.md` e
`orquestracao.md`; aqui ficam as que são da novela.

## Como registrar

Na hora em que acontece, uma entrada por lição, numerada (N1, N2…), com:

- **O quê.** O que foi feito e o que deu errado ou certo, com o episódio e o passo.
- **Quando.** A data.
- **Fala.** As palavras de quem reprovou ou aprovou, literais e entre aspas.
- **Por quê.** A causa, em uma ou duas linhas.
- **Regra.** A regra nova e onde ela foi parar: o passo do `SKILL.md`, a régua, a grade ou o modelo. Uma lição sem
  lugar na skill vira lembrete, e lembrete não é aplicado.

Lição que só mede (um gerador que funcionou, um tempo de trecho que segurou) vai para a tabela do lugar dela, como a
calibração do gerador em [`elenco-e-cenarios.md`](elenco-e-cenarios.md), e não para cá.

## Lições

### N1. Roteiro copiou o ritmo e perdeu a história

- **O quê.** O 1º roteiro de um ep. 1 (passo 4) cumpria a grade inteira (batidas, palavras por segundo, frases curtas)
  e foi reprovado por não ser coeso nem coerente. Era uma fila de piadas: a mensagem de quem dava o prazo caía dentro
  do «uma hora antes», uma das provas acontecia não se sabia quando, e o sonho da personagem não era dito. O que
  segurou na versão aprovada foi o desejo dito cedo, contra a rotina que ela vive.
- **Por quê.** A grade mede ritmo, não causa. Um roteiro pode acertar todos os números e não contar nada.
- **Regra.** A grade ganhou a seção «A história antes da grade» (linha do tempo única, o desejo dito cedo, o teste do
  «por isso / mas» entre frases, cada detalhe como dicotomia). O passo 4 do `SKILL.md` passa por um crítico
  independente antes de ir à pessoa.

### N2. Personagem é cadastro, não figurante de um episódio

- **O quê.** A protagonista nasceu como personagem de uma série só, e logo foi preciso usá-la em outras.
- **Por quê.** A personagem é o ativo que se reaproveita; o episódio é uma aplicação dela. E cada item da ficha precisa
  fazer sentido e carregar uma dicotomia que provoque quem assiste.
- **Regra.** Toda protagonista tem `elenco/<nome>/ficha.md` com as dicotomias («o que ela é × o que o perfil mostra»),
  os fatos fixos e as relações; é essa ficha, com a folha e as poses, que outra série reaproveita
  (`elenco-e-cenarios.md`, «Folha de personagem»).

### N3. Mini CTA dentro da história

- **O quê.** O pedido de comentário só aparecia no fim.
- **Por quê.** Quem sai antes do fim nunca vê o pedido; e a mecânica do comentário, mostrada dentro da história, prepara
  o pedido final.
- **Regra.** A batida da aula carrega um mini CTA dito por personagem (ex.: quem manda a aula conta que «comentou uma
  palavra e recebeu isso»). Item na lista de mecanismos da grade.

### N4. Quem aparece quando o nome é dito

- **O quê.** Num ep. 1, a voz dizia o nome da protagonista e uma qualidade dela com a testemunha na tela, ainda sem
  nome, e a etiqueta da profissão em cima da testemunha. A revisão de olhos novos (passo 9) apontou como o ponto em que
  quem assiste sairia do vídeo: quem vê pela primeira vez acha que a testemunha é a protagonista.
- **Por quê.** O roteiro apontava o cenário e esqueceu que o espectador frio liga o nome dito ao rosto que está na
  tela.
- **Regra.** Quando a fala diz o nome de um personagem ou uma qualidade dele, é ele quem está no quadro. Personagem
  novo só entra na tela junto com a fala ou a etiqueta que o apresenta (`regua-visual.md`, conferência do passo 9).

### N5. Duas vozes saem de um motion só

- **O quê.** As duas versões de um ep. 1 (narrador e narradora) usaram as mesmas cenas: a segunda foi feita por
  reancoragem (`ancorar.py`, pelo `segunda_voz.py`) numa cópia do projeto, e 41 palavras-gatilho bateram quadro a quadro.
- **Por quê.** As cenas escrevem o tempo pelo `VOZ.w`; número solto de tempo é o que quebra a reancoragem.
- **Regra.** Nenhum ato usa número solto de tempo, nem para a janela da aula nem para a roleta da barra. A aula entra
  com âncoras fixas no começo e no fim de cada pedaço (passos 5 e 7 do `SKILL.md`; o `segunda_voz.py` faz isso).
