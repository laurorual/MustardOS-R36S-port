# C40 — preparação de um core de diagnóstico Libretro

O próximo recorte usa o host nativo muOS `muxretro`. A referência
`internal/script/launch/mu-general.sh` chama esse executável; o caminho alternativo
`lr-general.sh` usa RetroArch. O C38 contém o frontend, mas nenhum desses hosts
foi compilado/instalado. A escolha segue a prioridade do port por código nativo.

## Preparação executada no host

Core original MIT `port/diagnostics/phase4-libretro-smoke.c`: não precisa de ROM,
BIOS ou arquivo de conteúdo; desenha um quadrado movido pelo direcional sobre
fundo quadriculado RGB565/160x120/60fps. Produz apenas zeros estéreo a44100Hz.
Não escreve arquivos, saves, firmware, rede ou energia. Rejeita conteúdo externo.

O checker carrega a biblioteca por `dlopen(RTLD_NOW)` e confere os entrypoints
Libretro, suporte a no-content, formato/geometria, mudança real de imagem pelo
input, restauração do frame por reset, áudio batch e callback individual sem
amostras não-zero. Resultado:11frames de vídeo e8085frames de áudio verificados.
Isso valida o contrato do core; não valida apresentação ou áudio no hardware.

Build isolado no SDK existente: AArch64/Cortex-A35, -Werror, PIC/shared ouPIE,
RELRO/NOW. Readelf e checkerQEMU com loader/userspace doC38 passaram. Configuração
SDK permanece idêntica ao baseline. Nenhum ELF foi enviado ao console, nenhuma
imagem ou política nativa mudou. Stage privado:
`build/phase4/libretro-smoke/build.d0odvlcz` (latest). Prova semELF em
`dist/phase4/libretro-smoke-preparation`.

HeaderAPI foi conferido byte-a-byte com arquivo do snapshot já usado pelo
frontend, revisão `5e8635b3b485eec9ad2ace141c415fd2df47d8f1`, archiveSHA
`c638d1afd4d995792f5ee09ea647de6976a60ca80e82014591a3fdff400ee5ff`.
Licença permissiva do header foi lida e seu aviso preservado na prova; nenhum
código de implementação upstream foi copiado para o core original.

## Próxima implementação concreta

1. Compilar `muxretro` em cópia privada do MESMO snapshot, usando o SDK e as libs
   de frontend já auditadas; não executar make em refs/ nem recompilar/substituir
   as seisELFs aprovadas. O Makefile retro usa também rcheevos/libarchive/OpenSSL:
   conferir headers/libs/proveniência e disponibilidade offline antes do link.
2. Tratar no-content explicitamente no host: o parser atual exige core+content
   (`startup.c`, argc>=3). Não passar arquivo inventado nem marcar lançamento
   aprovado a partir de `--help` ou QEMU. Preparar a adaptação mínima e testes
   do parser/lifecycle antes de qualquer sessão física.
3. Planejar uma sessão opt-in que acompanhe o PID/geração do core, reserve os
   writers em RAM e garanta término dos descendentes, restauração de DRM/mixer/
   preferências e retorno ao menu/C07. O workerC22 atual só acompanha a cadeia
   UI/core/input; não supor que um processo novo será limpo pelo lease existente.
4. Somente depois de ABI/loader/guardas e limpeza passarem, executar no console
   por lease, com usuário presente e ações definidas. Usar conteúdo sintético
   original; preservar política de áudioC36,55/70 e cartão original32.

Não habilitar launcher permanente, rearmarC12, gravar imagemC38 ou modificar
contador/partições para preparar esse teste. C39 de áudio é evidência separada.

## Atualização após C41–C43

O hostmuxretro já foi compilado em cópia privada e o caminho no-content foi
implementado. Loader/CLI e testes de componentes passaram; version/help e
checkerC40 também executaram na CPU real emRAM. DadosRO+aliasesRAM foram
qualificados separadamente. A imagemC38 e a raiz instalada permanecem iguais.
[Estado completo e worker gráfico pendente](phase4-muxretro-integration.md).
