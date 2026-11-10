# Referências copiadas

Cópias para a skill funcionar sozinha, sem depender de outras skills instaladas. Copiadas em 25/10/2026.

- `gsap-hyperframes.md`: o resumo em português. **Leia primeiro**; as outras são consulta.
- `hyperframes/`: contrato de composição, determinismo, legendas, som, formato, régua de movimento, adaptador GSAP
  e registro de blocos. Fonte: skills oficiais do HyperFrames (HeyGen, Apache-2.0, github.com/heygen-com/hyperframes)
  até a versão 0.8.200; parte dos arquivos vem de uma skill oficial depois aposentada. Em 10/11/2026 os pontos que
  contradiziam o contrato da 0.9.26 foram corrigidos à mão (vídeo cronometrado sem o invólucro, nada de `display`,
  `visibility` ou `autoAlpha` num `.clip`, `class="clip"` obrigatório, nada de `repeat: -1`) e os comandos passaram a
  levar a versão `0.9.26`.
- `gsap/`: skills oficiais do GSAP que valem para Reel (core, timeline, plugins, utils, performance). Fonte:
  github.com/greensock/gsap-skills, commit aed9cfd de 21/04/2026, licença MIT.

Links internos dessas cópias podem apontar para arquivos que não vieram; o essencial para Reel está aqui. Trechos que
citam outras skills, login ou serviço pago (`/media-use`, HeyGen, `feedback`, `publish`) não fazem parte desta skill:
ignore.

Cópia congelada; não atualize por aqui. Não rode `skills update` nem instale as skills oficiais: o motion usa só
esta pasta e a versão `0.9.26` fixa nos comandos.
