# Fase 4 — utilitários muOS e bootstrap de áudio no rootfs próprio

Ensaios de 24/10/2026 no R35S/R36S-V12 Panel 0. Continuação do
[rootfs headless](phase4-rootfs.md). **Incremento funcional parcial:** cache,
utilitários, D-Bus e ciclo de vida PipeWire/WirePlumber executaram nativamente
com loader e bibliotecas do novo rootfs. Os três bipes foram ouvidos somente
na repetição com software em 100%, ainda baixos. Volume confortável permanece
pendente. A Fase 4 continua aberta; não houve boot, gravação de mídia ou uso
do novo kernel.

## Fontes, build e limites

| Entrada | Revisão / implementação |
| --- | --- |
| Buildroot | `4f924fd52841608d68ac3dcb83fccee8b8c90316`, 2025.02.19 |
| muOS frontend | `5e8635b3b485eec9ad2ace141c415fd2df47d8f1`: `module/muvarctl.c`, `module/mulog.c`, `common/config/var_store.c`, `input/` |
| muOS internal | `550cc58f9cd3449a17f53ca55efcdc6c473b5a89`: `script/var/{base,config,log,audio}.sh`, `script/init/S80pipewire.sh`, `script/mux/audio_sink.sh`, configurações ALSA/PipeWire |
| muOS tool | `d5edf14a54ae6588355a75c67b2d493590f281dc`: `utils/fnv1a.c` |
| Integração própria | [pacote Buildroot](../../port/buildroot/package/muos-core/muos-core.mk), [perfil](../../port/device/rk-r35s-p0/core-config.json), [bootstrap](../../port/device/rk-r35s-p0/S95muos-core) |

As três licenças de topo muOS são GPLv3 e acompanham o snapshot usado.
O exportador lê objetos Git fixados quando o sparse checkout não materializa
os arquivos. Não se alteraram fontes dos refs. Patches são aplicados somente
às cópias de build. Não se copiaram binários Debian das fases anteriores.

A toolchain continua GCC 13.4/glibc 2.41/headers BSP 4.4.189/Cortex-A35.
O incremento acrescentou `muos-core`, jq 1.7.1 e procps-ng 4.0.5 à configuração
resolvida anterior. `build/phase4/core/config-diff.json` confirma que não houve
troca de libc, headers, compilador ou flags de filesystem. Reutilizou-se a
saída incremental; isso não demonstra reprodução bit a bit de um build limpo.
O artefato anterior `dist/phase4/rootfs-headless/` foi preservado e seus
checksums foram novamente conferidos.

O novo rootfs contém **248 ELF AArch64** e passou no fsck e na auditoria
ext4: 512 MiB, label ROOTFS, compat `0x3c`, incompat `0x242`, ro_compat `0x46b`.
SHA256 da imagem: `5a19d6d5831206cb39582a77061de4a776ad3bd7917010b294eabbf613b18e23`.
Não é uma imagem de cartão: faltam tabela de partições, bootloader e integração
completa do firmware.

## Contrato de inicialização escolhido

Buildroot permanece proprietário de BusyBox init, eudev e D-Bus. O novo
`/etc/init.d/S95muos-core` prepara o cache com `muvarctl build` e delega áudio
ao **S80pipewire nativo muOS**, com start/stop/status. Não liga `sysinit`,
`shutdown`, manutenção, storage, frontend, hotkeys ou Power do muOS.

```sh
"$vars" build
# D-Bus precisa existir; recusar outro socket PipeWire no mesmo runtime.
"$audio_service" start
# Além do status upstream, exigir WirePlumber e o sink esperado como default.
```

A flag upstream `audio/ready=1` também aparece em caminhos de erro de
`S80pipewire.sh`; isoladamente não é prova de sucesso. O bootstrap verifica
processos/socket/sink e a identidade do default. Em falha, salva grafo/status
antes de parar a sessão. O patch
[0005](../../port/patches/0005-muos-audio-service-logs.patch) mantém stdout/stderr
de PipeWire/WirePlumber em `/run/muos/core/`, em vez de descartá-los.

`/etc/default/muos-core` habilita áudio e deixa `input=0`. O muinput novo foi
compilado, ligado e listado; **não** foi exercitado com evdev/uinput real neste
rootfs. A aprovação de input da Fase 2 pertence ao outro artefato/sysroot.
A ocorrência histórica isolada de L3 não foi reensaiada.

## Compatibilidade de uinput com headers 4.4

O upstream já possui `write_legacy_setup`, mas referencia incondicionalmente
estruturas e ioctls introduzidos depois dos headers BSP usados aqui. O patch
[0004](../../port/patches/0004-muinput-linux44-uapi.patch) condiciona essas
referências a `defined(UI_ABS_SETUP) && defined(UI_DEV_SETUP)` e mantém o
caminho legado existente quando indisponíveis. Não foram inventados números
de ioctl ou substituídos headers para apenas fazer o build passar.

A compilação completa com headers BSP passou. A mesma unidade `uinput.c`
passou em `-fsyntax-only` com os headers modernos do container da Fase 1.
Execução real da criação do dispositivo legado continua pendente.

## RK817: observações e perfil

O preflight encontrou card0 `rockchiprk817co`, driver `asoc-simple-card`,
PCM `ff070000.i2s-rk817-hifi`, route `Playback Path=SPK_HP`, Playback
`95,95` na escala observada `0..237`, headphones desligados. Não se converte
essa escala em dB sem obter metadados válidos do driver instalado.

**Fato:** com ACP/UCM desativados, o grafo novo criou:

```text
device.name = alsa_card.platform-rk817-sound
node.name   = alsa_output.platform-rk817-sound.playback.0.0
media.class = Audio/Sink
```

O primeiro nome proposto, terminado em `.stereo-fallback`, não apareceu e
foi corrigido por essa evidência. O [perfil WirePlumber](../../port/device/rk-r35s-p0/core-wireplumber.conf)
limita o sink a dois canais FL/FR, pede period-size 1024/period-num 4 e desliga
suspend automático. Antes do limite, a enumeração solicitava 64 canais e o
driver retornava 8. Isso não demonstrava uma saída multicanal funcional.

Durante os bipes, `/proc/asound/card0/pcm0p/sub0/hw_params` mostrou:

```text
access: MMAP_INTERLEAVED
format: S32_LE
channels: 2
rate: 48000 (48000/1)
period_size: 512
buffer_size: 2048
```

São os parâmetros **efetivos** dessa sessão; diferem parcialmente dos pedidos.
O grafo ocioso de PipeWire 1.2.8 mostrava period-num 1024, mas seu
`spa/plugins/alsa/alsa-pcm.c:spa_alsa_emit_node_info` usa `default_period_size`
no ramo que imprime esse campo antes de negociar formato. Não se tomou esse
valor como medição do buffer em execução. O PCM ativo apresentou quatro
períodos de 512 frames. MMAP de ALSA não é o mapeamento de framebuffer usado
por musplash; este último permanece excluído.

`audio/control` foi deixado vazio para não executar o reset genérico de mixer
a 100%. O fixture restaura uma cópia privada do snapshot atual antes de iniciar
o stack, e o supervisor restaura o snapshot novamente ao devolver o launcher.
O S80 configura a route SPK. **Limite:** foram comparados snapshots antes e
depois; o ganho do codec durante o PCM ativo não foi capturado neste ensaio.
Não se deve inferir que a troca de route seja neutra em todas as versões do
driver a partir dessa comparação.

## Ensaios nativos e resultado auditivo

O [executor](../../port/scripts/run-phase4-core-session.sh) prepara o payload em
`/tmp` tmpfs e inicia chroot em namespaces privados de mount/PID/net/IPC/UTS.
Todos os executáveis testados usam as bibliotecas da imagem nova. `/lib`,
`/usr` e `/etc` do Debian não são ligados ao chroot. O supervisor Python e
`unshare` pertencem ao sistema instalado; não são o PID1 do futuro firmware.

Somente nós ALSA de controle, playback e timer são expostos, além dos nós
básicos de `/dev`. Não há capture PCM, input/uinput, framebuffer, DRM ou GPU.
`/sys` e metadados `/run/udev` existentes são vistos somente leitura.
Assim, o teste depende do kernel e do coldplug já realizados pelo dArkOSen;
não valida enumeração eudev em boot próprio.

| Ensaio | Resultado | Evidência |
| --- | --- | --- |
| QEMU Cortex-A35 | muinput/lista; fnv1a(`abc`)=`1a47e90b`; muvarctl build/set/get passaram | `build/phase4/core/audit/` |
| Inspeção nativa sem áudio | Loader próprio e ciclo start/start/status/stop/status=3/stop passaram | `native-inspect-2.txt` |
| Áudio com default 35% | Sink correto, aplay terminou, usuário não ouviu os bipes | `native-audio-6.txt`, `remote-audio-6/` |
| Repetição diagnóstica a 100% de software | Três bipes ouvidos, mas baixos; ciclo completo e aplay status 0 | `native-audio-7.txt`, `remote-audio-7/` |
| Restauração | Snapshot ALSA final idêntico ao inicial, ES/ogage/fn-menu-watcher ativos | `remote-audio-7/mixer-{before,after}.state`, `device-after-audio.txt` |

O fixture usa três pulsos de 300 ms a 1200 Hz, com fades, separados por
700 ms, estéreo 48 kHz e amplitude de pico 0,2 (~−14 dBFS). Não é um teste
calibrado de pressão sonora. O volume 35% do wpctl correspondeu a
`channelVolumes=[0.042875,0.042875]` no grafo. A repetição usou unity software
gain apenas na sessão privada; **o perfil do firmware continua em 35%**.
A confirmação do usuário comprova saída pelo speaker, não volume confortável.

Falhas de bancada corrigidas: `unshare --kill-child` no Debian exige
`pidfd_open`, ausente no BSP; a checagem de headphones exige `iface=CARD`;
o PATH de sudo não incluía `/usr/sbin`; a árvore intermediária TARGET_DIR
não tem os usuários gerados pelo mkusers. O staging agora vem da **imagem ext4
real**, extraída com debugfs sob fakeroot, preservando metadados ao empacotar.
O arquivo WAV é diagnóstico externo e só é inserido no chroot temporário.

Após a parada, os PIDs restantes eram `State: Z (zombie), PPid: 1`, conforme
`post-stop-processes.json`: o executor Python precisava recolher filhos
adotados. Com waitpid, a checagem de ausência de PW/WP e o ciclo completo
passaram. Isso não comprova o reaping de um boot real com BusyBox init.

O supervisor tem timeout de 110 s e arma uma unidade systemd de restauração
independente a 150 s antes de parar serviços. Falhas normais e restauração
foram exercitadas; **o disparo independente por perda de SSH não foi injetado**.
Logs incluem avisos de pthread_setname com proc somente leitura e componentes
opcionais ausentes de Bluetooth/câmera/logind. Capture PCM foi deliberadamente
omitido; não são aprovados microfone, fones ou esses subsistemas.

Ao final: raiz Btrfs rw com compress=zlib, boot FAT rw, taint 0, cinco contadores
Btrfs zerados e scan dmesg sem os marcadores antigos de falha. Image instalado
permaneceu `31bdb671…b0577`. Isso não resolve a causa histórica de mmap/MMC.

## Retomada e próximos passos

```sh
bash port/scripts/build-phase4-core.sh status
# Somente sem outro job ativo: preparar fontes/config, obter e compilar.
bash port/scripts/build-phase4-core.sh prepare
bash port/scripts/build-phase4-core.sh fetch
bash port/scripts/build-phase4-core.sh build
# Esperar build.exit=0 e container parado.
bash port/scripts/audit-phase4-core.sh
bash port/scripts/collect-phase4-legal-info.sh
```

O controlador verifica hashes dos inputs e aceita somente a diferença aditiva
de configuração descrita. Scripts antigos de build/configuração/auditoria
recusam sobrescrever o checkpoint headless quando o perfil core está ativo.
Artefatos locais em `dist/phase4/core-native/`; fontes, licenças, configuração,
manifesto de resultados e checksums acompanham o incremento, sem publicação.
Não há libmali ou outro blob gráfico nesse rootfs.

**Comparação executada após o retorno do usuário:** os mesmos pulsos passaram
em três grupos, com os executáveis/bibliotecas da imagem core original:

| Grupo | Caminho | Parâmetros efetivos | Mixer amostrado durante PCM |
| --- | --- | --- | --- |
| A | ALSA `hw:0,0`, WAV S16 | RW_INTERLEAVED, S16_LE, 2ch/48 kHz, período 6000/buffer 24000 | Playback 95,95; SPK_HP |
| B | ALSA `hw:0,0`, raw S32 | RW_INTERLEAVED, S32_LE, mesmos canais/rate/buffer | Playback 95,95; SPK_HP |
| C | PipeWire, software 100% | MMAP_INTERLEAVED, S32_LE, 2ch/48 kHz, período 512/buffer 2048 | Playback 95,95; SPK |

O S32 foi obtido deslocando os mesmos samples S16 por 16 bits, sem ganho
adicional. Os controles foram coletados antes, durante e depois de cada
reprodução. O usuário confirmou: **os três grupos tiveram volume igual,
baixo, mas audível**. Não foi observada atenuação adicional específica de
PipeWire, nem diferença audível entre os formatos/rotas desse recorte.
Isso não estabelece causalidade nem valida volume confortável dos sons reais
do menu. O default 35% continua sem alteração; a comparação usou unity apenas
na sessão privada e não corrigiu automaticamente o ganho do codec.

O [fixture comparativo](../../port/scripts/run-phase4-audio-compare.sh) gera
payload separado com os [hooks](../../port/scripts/phase4-audio-compare.py).
O ciclo completo terminou com status 0, snapshot final exatamente igual ao
inicial, serviços ativos, taint 0 e contadores Btrfs zerados. Artefatos em
`dist/phase4/core-audio-comparison/`; logs/estados em
`build/phase4/core/audio-compare.8aO0Wo/evidence/`. O pacote core anterior
permanece intacto com os scripts exatos da prova original. Próximo teste
de áudio: sons representativos do frontend compilado para o rootfs novo,
com referência auditiva e ganho medido, após resolver o provider gráfico.

**Sem acompanhamento físico:** fechar providers EGL/GLES/GBM/SDL e licenças,
preparar configuração/compilação contra o sysroot novo e auditar dependências.
O [overlay r13p0](phase4-r13-runtime.md) passou posteriormente em EGL/SDL; o [input novo](phase4-native-input.md) passou com uinput real. Repetir frontend/mapping/sons após integrar um provider ao build com os termos aplicáveis fechados. Permanecem pendentes
init/storage completos, mapping SDL/frontend do novo build, coldplug, candidata de
kernel, bootloader/DDR/BL31, DTB de U-Boot e boot em cartão separado.

**Retomada de 25/10:** o [menu com dependências próprias](phase4-menu-own-rootfs.md) passou em áudio SDL/PipeWire a volume confortável confirmado pelo usuário, no nível de codec 153,153 escolhido antes da sessão e software em unity. Os WAVs de ajuda foram controles diagnósticos. A primeira restauração divergiu para 95,95; foi reparada e a nova rotina verificou o snapshot após subir os serviços em uma regressão automática. Não se estende esse resultado a boot, volume/energia completos ou sons originais de ajuda.
