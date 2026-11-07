# Fase 4 — muinput do sysroot próprio com uinput real

Ensaio de 24/10/2026 no R35S, model `R36S-V12 2023-08-18 Panel 0`.
**Resultado:** criação do controle, captura de todos os controles solicitados,
remoção do dispositivo e liberação do grab passaram. O caso duplo isolado de
L3 não reapareceu. Não houve teste de Power, SDL/controller mapping ou frontend.

## Artefato e caminho de execução

Foi usado o mesmo `core-staging.tar.gz` extraído da imagem ext4 core,
SHA256 `597bb170e4db4dc8574332e8fa92f02a0c63d49bf776f021af5163de55c95334`.
Imagem de origem: `dist/phase4/core-native/rootfs.ext4`, SHA256
`5a19d6d5831206cb39582a77061de4a776ad3bd7917010b294eabbf613b18e23`.
O pacote histórico e seu manifesto não foram sobrescritos para incorporar
retroativamente esta prova.

O muinput é recompilado do frontend `5e8635b3…`, GPLv3, com o perfil
[R35S](../../port/patches/0002-muinput-r35s-panel0-profile.patch) e o
[ajuste para headers 4.4](../../port/patches/0004-muinput-linux44-uapi.patch).
Usa o loader/glibc da imagem Buildroot; nenhum executável Debian de muinput
ou biblioteca do sistema instalado foi ligado ao chroot.

O preprocessamento com o SDK real não define `UI_DEV_SETUP` nem
`UI_ABS_SETUP` (`build/phase4/core/input-sdk-macros.txt`). Assim, este build
usa `write_legacy_setup()` e `UI_DEV_CREATE`, não o setup moderno. A criação
real foi exercitada; o teste anterior `--list-devices` não demonstrava isso.

O [runner](../../port/scripts/run-phase4-input-session.sh) usa namespaces
privados, staging em `/tmp` tmpfs, timeout de 110 s e restauração independente
a 150 s. O fixture expõe apenas nós básicos, `/dev/uinput` e os dois evdev
identificados por nome (`GO-Super Gamepad`, `odroidgo3-keys`). Não expõe
framebuffer, GPU, ALSA nem o evdev Power. Áudio fica desligado e `input=1`
vale somente no `/etc/default/muos-core` privado desse ensaio.

## Verificações observadas

Primeiro houve criação/inspeção/parada automática curta. Depois o usuário
executou a sequência em uma captura de 80 s. O hook
[phase4-input-native.py](../../port/scripts/phase4-input-native.py) encontrou:

```text
name = muOS-Keys
input_id = bus 0x0006, vendor 0x756d, product 0x3504, version 0x736f
source isolada = /dev/muinput/rk-r35s-p0-source, no /dev privado
EVIOCGRAB por segundo consumidor = EBUSY enquanto muinput estava ativo
PHASE4_INPUT_STOP_AND_RELEASE=OK
PHASE4_CORE_WORKER_EXIT_STATUS=0
MIXER_AND_SERVICES_RESTORED
```

Após a parada, não restou o dispositivo virtual e uma nova tentativa de grab
na fonte física passou e foi imediatamente liberada. A mudança de nome da
fonte ocorreu somente no `/dev` privado; não renomeou nós do launcher.
O processo muinput usa a libc nova; o gravador dos eventos é Python do host
dArkOSen, com `input_event` de 24 bytes. Isso é evidência de evdev/uinput,
sem provar um consumidor SDL ou o boot próprio do daemon.

| Controle | Resultado normalizado |
| --- | --- |
| D-pad cima/baixo e esquerda/direita | HAT0Y/HAT0X: `[-1,0,1,0]` em cada eixo |
| A/B/X/Y | Códigos `305,304,307,308`, cada um com release |
| L1/R1/L2/R2 | `310,311,312,313` |
| Select/Start/Fn | `314,315,316` |
| L3/R3 | `317,318`; um par em cada um |
| Volume −/+ | `114,115`; apenas eventos, sem executar mixer |
| Sticks esquerdo/direito | ABS 0/1/3/4, de −32767 a 32767, direção inicial negativa e retorno final a zero |

O [analisador](../../port/scripts/analyze-phase4-input.py) verificou os 56
eventos sem remover duplicatas: ordem exata, releases balanceados, ausência
de teclas presas e de SYN_DROPPED, hats e extremos/centro dos quatro eixos.
L3 ocorreu em 49,6496/49,8776 s, um único pressionar/soltar. Um ensaio sem
recorrência não exclui problema intermitente futuro.

## Integridade, provas e limites

O coletor [collect-phase4-session.py](../../port/scripts/collect-phase4-session.py)
arquivou logs/scripts/estados antes de limpar os dois diretórios remotos.
Mixer final idêntico ao inicial, serviços previamente ativos restaurados,
taint 0, cinco contadores Btrfs zero, root/boot rw e Image instalado
`31bdb671…b0577`. Não surgiram marcadores de falha no dmesg.

Provas locais: `build/phase4/core/input-smoke-run.log`,
`input-capture-run.log`, `input-capture-analysis.json` e diretórios indicados
por `latest-input-smoke`/`latest-input-capture`. Pacote de evidências:
`dist/phase4/core-input-native/`, com checksums, scripts exatos das sessões
e referência ao arquivo core usado; sem nova imagem de firmware.

O perfil core de produto continua com `input=0`. Antes de ativá-lo no init
completo, conferir a enumeração/mapping da SDL nova e sua integração com o
frontend. Power, rumble, coldplug/eudev em boot próprio, convivência com
outros consumidores e estabilidade prolongada permanecem não testados.
