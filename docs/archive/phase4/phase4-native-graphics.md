# Fase 4 — C03: SDL/GLES no kernel próprio

**Estado: primeiro boot C03 aprovado no kernel próprio**, com confirmação
visual, logs, fsck e retorno saudável ao dArkOSen. A Fase 4 permanece aberta.
Recorte: EGL/readback de buffer, depois SDL/KMSDRM por 30 s no kernel
`4.4.189-muos-r35s-p4`, com retorno à tela diagnóstica e root ro. Sem
frontend/áudio/rede e sem pedir acionamento de controles.

## Resultado físico e logs

O usuário confirmou o padrão, orientação, movimento e retorno ao texto na
primeira tentativa. DIAG05/BOOT0004, status 0, kernel
`4.4.189-muos-r35s-p4` e BusyBox PID 1 confirmados.

```text
EGL_version=1.4 vendor=ARM
GL_renderer=Mali-G31
GL_version=OpenGL ES 3.2 v1.r13p0-01rel0.8747d14aec16ec21ac2b2da252c4ec5f
readback_rgba=32,128,191,255 gl_error=0x0
video_driver=KMSDRM
renderer=opengles2
renderer_flags=0xe
output_size=640x480
readback_red_pixel=PASS
frames=1789
elapsed_seconds=30.002
average_fps=59.630
render_failures=0
frame_interval_median_ms=16.687
frame_interval_p95_ms=16.904
sdl_probe_exit_status=0
DRM_MODE_RESTORED=1
C03_GRAPHICS_STATUS=0
```

Isso comprova contexto/readback e desenho GLES2; a string ES 3.2 do driver
não equivale a teste de todos os seus recursos. O modo DRM antes/depois foi
idêntico: CRTC 60, 640×480, clock 29000 kHz, htotal 732, vtotal 661,
HSYNC/VSYNC 2, taxa calculada 59,935683 Hz. O usuário confirmou a restauração
do console, complementando essa comparação de modo.

Regressão C02: seed consumido com crédito, prontidão após 6811 ms, refresh
nativo e rotação na parada aprovados; aviso conservador do próprio seedrng
preservado, sem avisos prematuros de consumidores. Muinput/mapping/D-Bus,
parada da cadeia, taint 0, root ro e FAT desmontada passaram. Report em
uptime 48,39 s. As buscas documentadas não encontraram Oops/BUG/panic,
erros de I/O/ext4/MMC ou padrões de fault/timeout de GPU nessa janela.
Avisos BSP anteriores não ficam automaticamente resolvidos por esse teste.

Fsck offline retornou 0. Após voltar ao original: Image inalterado, taint
0, cinco contadores Btrfs 0, ES/ogage/Fn ativos, nenhuma unidade muos
carregada. Temporário removido, raiz candidata desmontada; montagens FAT
globais do dArkOSen preservadas. Nenhum teste/gravação crítico ativo.

## Abordagem e evidências

Reutiliza o blueprint C02 sem seed e a política de prontidão corrigida.
Não clona a raiz viva nem coleta bytes/hashes do seed. O estado privado e
o contador de boots são preservados na atualização do cartão de 128 GB.
O original de 32 GB continua sendo a recuperação e fica fora durante o
boot. Kernel/DTB/U-Boot e particionamento não mudam.

Os probes originais do port são recompilados para o SDK próprio, armv8-a /
cortex-a35, PIE/RELRO/NOW, sem binários Debian:

- [EGL](../../port/probes/phase4-egl-context.c): contexto GBM 64×64, GLES2,
  glReadPixels esperado ~32,128,191,255 e swap, sem modeset.
- [SDL](../../port/diagnostics/sdl-video-probe.c): KMSDRM + renderer
  opengles2 acelerado/vsync, 640×480, pixel vermelho conferido, quadrantes
  RGB/branco e retângulo amarelo móvel, métricas de frames/intervalos.
- [DRM](../../port/diagnostics/drm-mode-probe.c): consulta do modo ativo
  antes/depois; exige o mesmo resultado e 640×480.

Os dois primeiros passaram anteriormente no kernel instalado, conforme
[ensaio r13](phase4-r13-runtime.md); isso não aprova o novo BSP. A SDL
2.30.12 em `build/phase4/graphics-config/output/build/sdl2-2.30.12/src/video/kmsdrm/SDL_kmsdrmvideo.c:1083`
restaura o CRTC/modo/buffer TTY ao destruir as superfícies. O teste exige
comparação do modo e confirmação visual do console; comparar o modo não
prova sozinho identidade do framebuffer nem todos os estados do display.
Não usa mmap de /dev/fb0.

## Limites e encerramento

Probes EGL/SDL são limitados pelo executor já aprovado a 10/45 s;
consultas DRM, 5 s. SDL normal trata TERM/INT, encerra e restaura o CRTC.
Crash/SIGKILL ou I/O preso no kernel podem impedir a restauração completa;
por isso o runner tenta parar serviços, salvar status/dmesg, sync e root
ro também se o probe falhar. Se a tela ficar preta, aguardar dois minutos
antes de desligar e coletar. Não interpretar tela preta como aprovação.

A ativação exige marcador C03 separado; S05 continua usando marcador C02.
Bootstrap com guarda C03 é instalado primeiro e marcador por último.
DIAG05/BOOTnnnn contém os logs desta rodada; DIAG04 anterior é preservado.
Atualização incremental restrita a seis arquivos, preimages/CIDs, hash
do provider/SDL/política, backup só de código, fsck e saúde do original.
Não modifica o seed. O provider r13p0 permanece apenas para uso privado;
a licença vinculada ao ZIP continua pendente.

[Preparador](../../port/scripts/prepare-phase4-native-graphics.py) confere
ELF/loader no rootfs próprio com QEMU Cortex-A35, SDL --info, contrato de
símbolos, shell e ext4/fsck. Fixtures executam a orquestração real com
probes substituídos: sucesso, EGL falhando sem iniciar SDL, SDL falhando
mas consultando o modo depois e modo divergente. Não simulam hardware.
[Analisador](../../port/scripts/analyze-phase4-native-graphics.py) exige
logs, leitura de pixels, retorno, regressão C02, fsck e confirmação física.

## Procedimento físico executado

Desligar pelo dArkOSen; original de 32 GB guardado, test128 no slot OS,
segundo slot vazio, dongle retirado. Ligar sem pressionar botões, observar
30 s do padrão e esperar C03 EGL / SDL / INPUT OK, root ro e DIAG05 salvo.
Transcrever STOPPED ou anomalias antes de retornar ao dArkOSen e à rede.
Coletar por FAT ro em namespace privado; analisar antes de declarar sucesso.
Este ensaio não aprova frontend/áudio no kernel novo, eventos físicos,
shutdown normal, rede, outros painéis ou estabilidade prolongada.

Preparação concluída: `build/phase4/linux-diagnostic/native-graphics.6qz6i3e7`,
ponteiro `latest-native-graphics`. Prova imutável pré-boot:
`dist/phase4/native-graphics-preboot/`. Atualização de seis arquivos passou;
nenhuma cópia de bibliotecas ou regravação de imagem foi necessária.

Prova do boot/retorno: `dist/phase4/native-graphics-boot/`, com report,
dmesg, resultado, confirmação física, análises gráfica/entropia, saúde
final e fontes do port. Checksums separados preservam pré-boot e pós-boot.
Não contém rootfs vivo, seed ou biblioteca proprietária.

Próximo menor incremento: primeiro frontend pelo serviço supervisionado no
kernel próprio, inicialmente sem áudio nem hotkeys de Power/volume/brilho;
confirmar menu/submenus e stop/root ro. Áudio/ajustes vêm depois, preservando
logs por boot, seed e retorno ao original. Antes de nova escrita, conferir
os preimages C03 atuais; instaladores C01/C02 antigos não se aplicam ao
bootstrap/runner agora modificados. Não regravar um raw antigo por cima.

Continuação: o [C04](phase4-native-frontend.md) aprovou posteriormente o
frontend supervisionado silencioso no kernel próprio. Áudio/hotkeys seguem
como próximo recorte, sem alterar a validade específica da prova C03.
