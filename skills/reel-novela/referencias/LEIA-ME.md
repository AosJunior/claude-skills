# Referências copiadas

Cópias para a skill funcionar sozinha, sem depender de outras skills instaladas. Copiadas em 25/10/2026.

- [`gsap-hyperframes.md`](gsap-hyperframes.md): o resumo em português, escrito para esta skill. **Leia primeiro**; as
  outras são consulta.
- `hyperframes/`: contrato de composição, determinismo, legendas, som, formato, régua de movimento, adaptador GSAP
  e registro de blocos. Fonte: HyperFrames v0.8.200 (HeyGen, Apache-2.0, github.com/heygen-com/hyperframes). A skill
  roda o HyperFrames 0.9.6; onde a cópia diverge, vale o `--help` do comando.
- `gsap/`: skills oficiais do GSAP que valem para vídeo renderizado (core, timeline, plugins, utils, performance).
  Fonte: github.com/greensock/gsap-skills, commit aed9cfd de 21/04/2026, licença MIT.
- A biblioteca GSAP (GreenSock) não vem copiada: o `scripts/montar_projeto.py` a baixa do pacote oficial (jsDelivr, `gsap@3.14.2`) para
  `assets/gsap.min.js` de cada projeto. A licença dela é a de gsap.com/standard-license, e o aviso fica no cabeçalho do arquivo.
- `modelos/componentes/fontes/` e `modelos/motion/assets/fontes/`: Montserrat, SIL Open Font License 1.1
  (`OFL-montserrat.txt` ao lado das fontes).

Links internos dessas cópias podem apontar para arquivos que não vieram; o essencial para vídeo está aqui. As regras
de mola e ease das cópias são gerais: na novela, vale [`movimento.md`](movimento.md).
