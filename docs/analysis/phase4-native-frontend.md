# Fase 4 — C04: frontend supervisionado no kernel próprio

**Estado: C04 aprovado no primeiro boot físico**, com menu/navegação,
parada pelo serviço, logs, fsck e retorno saudável ao original. Recorte: S99,
muos-ui-supervisor e frontend reais por 75 s, sem áudio/hotkeys, seguidos
de stop do serviço, logs DIAG06/BOOTnnnn, sync e root ro.

## Resultado observado

DIAG06/BOOT0005 retornou status 0 no kernel `4.4.189-muos-r35s-p4`, BusyBox
PID 1. Usuário confirmou texto/orientação, Informações/Configurações,
ajuda e retorno automático ao diagnóstico. A janela foi configurada para
75 s; não há medição independente da duração exata de cada interação.

```text
UI_ID manager=1925 frontend=1927 parent=1925
UI_WINDOW_STARTED
UI_MODULE=muxlaunch
UI_MODULE=muxinfo
UI_MODULE=muxlaunch
UI_MODULE=muxconfig
UI_MODULE=muxlaunch
UI_MODULE=muxplore
UI_MODULE=muxlaunch
UI_WINDOW_ENDED
CHILD frontend 1927
STOP reason=stop signal=15
C04_UI_STOPPED=1
```

O processo real `/opt/muos/frontend/muxfrontend` tinha o supervisor como
pai, com first_paint novo e ready. Não houve filho hotkey nem marcador de
falha do supervisor. Explorar também foi observado, sem evidência de
lançamento de conteúdo; isso não aprova emuladores/cores ou todo o menu.
S99 stop removeu UI e supervisor. Modo DRM antes/depois idêntico: CRTC 60,
640×480, clock 29000 kHz, htotal 732/vtotal 661. Usuário confirmou o texto
diagnóstico de volta. O bind temporário foi desmontado e enabled0 original
relido antes da raiz ro; não se habilitou UI permanente no cartão.

Regressão C02 persistida passou: crédito do seed, prontidão após 7208 ms,
refresh nativo sem crédito do fallback conservador e rotação na parada.
O aviso inicial do próprio seedrng foi preservado; nenhum prematuro de
consumidores. Input/mapping, D-Bus, parada, taint 0, root ro e FAT desmontada
aprovados. Report em uptime 98,11 s, fsck offline status 0 e sem falhas nos
padrões de kernel pesquisados. A janela não prova estabilidade prolongada.

Após retorno ao dArkOSen: Image `31bdb671…b0577` inalterado, taint 0,
cinco contadores Btrfs 0, ES/ogage/Fn ativos, nenhuma unidade muos carregada.
Temporários removidos e raiz candidata desmontada; montagens FAT globais
preservadas. Prova imutável `dist/phase4/native-frontend-boot/`, com logs,
análises de serviço e entropia, confirmação física, saúde e fontes.
A análise C04 verifica modo DRM e supervisão; a prova de render/readback
continua sendo a C03, não um novo benchmark desta UI.

## Implementação e evidências

Usa o blueprint C03 sem seed, bibliotecas/binários inalterados. Instala só
bootstrap/runner/marcador C04, com preimages e identidade do secundário.
Não clona raiz viva, nem lê/copia/hasha seed. C02/C03 markers continuam
presentes; bootstrap exige C04 novo antes de iniciar BusyBox. Kernel/DTB,
U-Boot e tabela não mudam. Original de 32 GB guardado durante o teste.

A [sessão](../../port/device/rk-r35s-p0/frontend-diagnostic/session.sh)
inicia a cadeia já aprovada com UI disabled; depois faz bind temporário
de enabled1/hotkeys0 sobre o arquivo de configuração, inicia pelo S99 e
exige first_paint novo, pai supervisor real e executável correto. Observa
comm do processo por até 75 s e para pelo S99, inclusive após falha de
start. Remove o bind antes do root ro, sem habilitar UI permanentemente.
Áudio continua desligado no core e backend SDL dummy; idle é desativado.

O [supervisor existente](../../port/utils/muos-ui-supervisor.c) conserva
PID/starttime, subreaper e limites de stop já testados no kernel instalado;
não foi modificado nem recompilado nesta rodada. Evidência upstream:
`refs/muos/frontend/module/muxfrontend.c:787` exige pai vivo;
`common/platform/display.c:1131` produz first_paint; `common/runtime/exec.c:134`
pode destacar helpers com setsid/duplo fork. O dispatcher upstream
`refs/muos/internal/script/mux/frontend.sh` inclui conteúdo/energia ainda
fora do recorte. Não substituí-lo por alegação de firmware completo.

O [preparador](../../port/scripts/prepare-phase4-native-frontend.py) clona
somente imagem host sem seed, confere hashes, ELF/loader Cortex-A35/QEMU,
shell e ext4/fsck. Não testa pixels em QEMU. O
[analisador](../../port/scripts/analyze-phase4-native-frontend.py) exige
confirmação física de menu/Informações/Configurações/ajuda, transições
observadas, stop/retorno DRM, regressão C02, fsck e saúde do original.

Após ligar sem dongle, testar A/B em Informações e Configurações, Fn/B na
ajuda, aguardando cerca de dois segundos nos submenus para observação.
Não modificar configurações, lançar conteúdo nem usar Power/volume/brilho.
Esperar retorno automático a C04 FRONTEND / INPUT OK, root ro e DIAG06.
Em STOPPED, registrar mensagem; se preto, aguardar dois minutos antes do
retorno orientado. Não repetir boots para substituir logs de falha.

Riscos/limites: o prazo só vale enquanto o kernel progride; I/O preso não
tem cancelamento rígido. Crash/stop podem falhar em restaurar vídeo, por
isso há logs e comparação DRM, além da confirmação visual. Áudio, hotkeys,
energia/shutdown normal, rede, conteúdo, outros painéis e estabilidade
prolongada permanecem pendentes. Provider r13p0 continua privado, com termos
pendentes para o relatório final solicitado pelo usuário.

Blueprint sem seed: `build/phase4/linux-diagnostic/native-frontend.urej9y1t`,
ponteiro `latest-native-frontend`. Transação de três arquivos, sem rebuild
ou cópia de ELF. Prova pré-boot `dist/phase4/native-frontend-preboot/`.
Saúde do original conferida e temporário de instalação removido antes do
poweroff. O usuário confirmou disponibilidade para acompanhar o ensaio.

Coleta/resultado: `native-frontend.urej9y1t/boot1` sob
`build/phase4/linux-diagnostic/`. Não inclui seed ou dump da raiz viva.
Preparação e boot têm checkpoints separados, sem sobrescrever C03/C02.

**Próximo incremento:** áudio no kernel próprio, começando por core e bipes
limitados para confirmar backend/sink/PCM/ganho; depois frontend sonoro e
hotkeys reais em ensaios separados. Não transportar aprovação de áudio do
kernel dArkOSen. UI de produto, shutdown normal, dispatcher/conteúdo, rede
e outros painéis seguem pendentes. A Fase 4 permanece aberta.
