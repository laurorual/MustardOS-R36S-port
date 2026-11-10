# Fase 4 — userspace próprio e contrato de init

Continuação de 24/10/2026. Complementa a [base BSP](phase4-bsp-foundation.md).
Este incremento compilou e auditou um rootfs **sem gráficos** e seu sysroot.
Não é firmware completo; o muOS não inicia automaticamente neste perfil.

**Continuação posterior:** o perfil ativo agora inclui [utilitários e bootstrap limitado de áudio muOS](phase4-core-audio.md), com ensaio nativo do stack próprio. Este documento e `dist/phase4/rootfs-headless/` preservam o checkpoint anterior. Use o controlador `build-phase4-core.sh` para continuar a saída atual; os comandos antigos de reconfiguração/build/auditoria são bloqueados enquanto `core/active` existir.

**Checkpoint concluído:** download e build offline terminaram com status 0.
A imagem ext4 passou na auditoria estática e no `e2fsck -fn`; os probes QEMU
e nativo de libc passaram. O build levou cerca de 31 minutos neste host.
Não houve boot da imagem, teste do novo kernel ou integração do init muOS.

Também passaram os checks do verificador com ELF AArch64 existente, rejeição
de ELF x86_64, resolução de symlinks absolutos dentro da raiz de destino e
rejeição de loop. Reconfiguração e segundo build durante o job foram recusados.
Um teste negativo adicional rejeitou uma cópia da imagem com `orphan_file`
habilitado; a imagem original permaneceu intacta. Esses checks complementam
a auditoria, sem substituir o boot real.

## Resultados e limites

| Verificação | Resultado observado | Limite da conclusão |
| --- | --- | --- |
| Toolchain interna | GCC 13.4.0, glibc 2.41, headers BSP 4.4.189 | Independente da Linaro usada somente no kernel |
| ELF da árvore de destino | 223 ELF64 little-endian AArch64; loader `/lib/ld-linux-aarch64.so.1` presente | Não é teste funcional de todos os executáveis |
| Mínimo de kernel glibc | Nota ABI Linux 4.4.0 e config de build correspondentes | Não comprova todos os syscalls/drivers do BSP |
| Filesystem | ext4, label `ROOTFS`, 536.870.912 bytes, blocos de 4096 bytes, estado clean; fsck status 0 | Imagem de filesystem; não inclui tabela de partições ou cadeia de boot |
| Features ext4 | compat `0x3c`, incompat `0x242`, ro_compat `0x46b` | Ausentes `64bit`, `orphan_file`, `metadata_csum_seed` e `fast_commit`; montagem no BSP ainda não ensaiada |
| QEMU user-mode Cortex-A35 | Probe libc/pthread/eventfd/epoll/clock, BusyBox `true`, versões Bash/PipeWire/WirePlumber passaram | Usa o kernel do host, não simula o handheld nem seu boot |
| Probe nativo no R35S | Mesmo probe recompilado contra o sysroot novo, loader e libc próprios em tmpfs; status 0 | Sobre o kernel **dArkOSen instalado** 4.4.189, não sobre a candidata recompilada |
| Preservação do console | Temporários removidos, launcher/serviços ativos, raiz rw, taint 0, cinco contadores Btrfs zerados e scan dmesg limpo | Sessão curta; não resolve as causas antigas de mmap/MMC |

SHA256 da imagem:
`f2cec5ecaccdf98797cd47e1139e5f0dcf0d70f9f7f2f576bfd43b62700cec00`.
O kernel instalado manteve o SHA256 `31bdb671…b0577` da referência anterior.

Saída do probe, tanto em QEMU quanto no R35S:

```text
glibc=2.41 pointer_bits=64 pthread/eventfd/epoll/clock=OK
```

O programa também imprime `libc_path`. No console, o caminho correspondeu
exatamente a `/tmp/muos-r35s-phase4-abi.*/libc.so.6`, após conferir os hashes
de probe, loader e libc. Não se usou a libc Debian para aprovar esse binário.
O [runner nativo](../../port/scripts/run-phase4-abi-probe.sh) executa sem root,
com ambiente limpo, cache do loader desabilitado, timeout e trap de limpeza.
`/tmp` foi confirmado como tmpfs; os payloads ficaram em RAM. Nenhum serviço,
mixer, mount, arquivo de boot ou biblioteca do sistema foi alterado.

Evidências: `build/phase4/rootfs-audit/`, `rootfs-build.log`,
`native-abi-20261024T172023Z.txt`, `rootfs-device-before.txt`,
`rootfs-device-after.txt` e respectivos dmesg. Artefatos locais em
`dist/phase4/rootfs-headless/`, com manifestos, fontes do port, checksums,
runtime do probe e aviso `NOT-FOR-DEVICE-BOOT.txt`. Não houve publicação.

Imagem de build usada:
`sha256:ccef62bd0d6602d0f891f160e2040653df3b782976458308d8fcd6f1e99e6787`.
As referências em `refs/` permaneceram intactas; não foi necessário atualizá-las.

## Execução retomável e limite de uso

O [controlador](../../port/scripts/build-phase4-rootfs.sh) mantém downloads e
compilação em um container Podman independente da conversa. Não acessa o R35S,
dispositivos de bloco ou serviços do host. O container tem limite de 12 GiB de
memória, 8 jobs por padrão e filesystem próprio somente leitura; grava apenas
em `build/phase4/` e em `/tmp` privado. Dependências são instaladas somente na
[imagem de build](../../port/packaging/phase4-rootfs.Containerfile).

```sh
# Consultar primeiro; não iniciar uma segunda compilação concorrente.
bash port/scripts/build-phase4-rootfs.sh status

# Preparar container/config; somente antes do primeiro build ou com config igual.
bash port/scripts/build-phase4-rootfs.sh prepare

# Obter fontes com rede; aguardar running=false e rootfs-fetch.exit = 0.
bash port/scripts/build-phase4-rootfs.sh fetch

# Compilar sem rede; aguardar running=false e rootfs-build.exit = 0.
bash port/scripts/build-phase4-rootfs.sh build

# Parar somente o build local, preservando cache e saída incremental.
bash port/scripts/build-phase4-rootfs.sh stop
```

Se a conversa for interrompida, o job local pode continuar. `status` informa o
estado real; um limite da conta não determina sucesso ou falha da compilação.
Após falha, ler `build/phase4/rootfs-{fetch,build}.log` e o arquivo `.exit`
correspondente. Se faltar `.exit` e o container estiver parado, o processo pode
ter sido morto: não interpretar isso como sucesso. Reiniciar o mesmo estágio
reutiliza o cache. Mudanças de toolchain/defconfig depois de começar a compilar
exigem preservar a saída anterior e iniciar uma árvore de saída limpa.
Se um encerramento forçado interromper a gravação de um objeto, o pacote em
questão pode precisar ser reconstruído com `dirclean`; cache preservado não
equivale a garantir integridade de todo objeto intermediário.

O estágio `fetch` deve terminar antes de `build`; este usa `--network=none`.
Um download indisponível não deve ser contornado desabilitando a conferência de
hash. Os pacotes comuns são verificados pelos hashes do Buildroot fixado.
Os headers BSP usam arquivo GitHub do mesmo commit `d8402159…`, evitando buscar
todo o histórico Git. Buildroot dispensa hashes para headers customizados;
o hash desse arquivo também precisa constar da evidência local.

Arquivo observado: SHA256
`0647d3804fafeb4647af9c16a1182c98e9e45193fea377421517f795269f777e`.
O controlador passou a conferir esse hash explicitamente ao concluir `fetch`;
na primeira execução, ele também foi conferido manualmente antes do build.

## Contrato observado no muOS

Referência local: `refs/muos/internal` em
`550cc58f9cd3449a17f53ca55efcdc6c473b5a89`, GPLv3 conforme `LICENSE`.
Nenhum script upstream foi copiado para o rootfs neste incremento.

| Contrato | Evidência | Situação do perfil inicial |
| --- | --- | --- |
| PID1 → `rcS`; shutdown → `rcK` → swapoff/umount | `build/phase4/buildroot/package/busybox/inittab` | Usar o mecanismo fornecido pelo Buildroot |
| Serviços de base em ordem S??; parada inversa | `package/initscripts/init.d/rcS`, `rcK` no Buildroot | Buildroot controla os serviços neste perfil |
| `/sbin/udevd`, trigger de subsistemas/dispositivos e settle | muOS `script/init/S10udev.sh`; Buildroot `package/eudev/S10udev` | Eudev do Buildroot é o único proprietário inicial |
| D-Bus em `/run/dbus/system_bus_socket`; diretórios temporários | muOS `script/init/S30dbus.sh` | D-Bus do Buildroot; não ligar uma segunda cópia pelo muOS |
| Config/cache e diretórios próprios | muOS `script/var/base.sh`: `MUOS_VAR_BIN=/opt/muos/frontend/muvarctl`, `MUOS_RUN_DIR=/run/muos` | Payload, perfil e cache ainda ausentes |
| Áudio via `/run/pipewire-0` e ferramentas `pw-cli`, `pw-dump`, `wpctl`, `jq` | muOS `script/init/S80pipewire.sh`, `script/var/base.sh` | Pacotes PipeWire/WirePlumber selecionados; falta configurar/ligar sessão e perfil RK817; `jq` ainda não selecionado |
| PipeWire ALSA SPA e plugin PCM `pipewire` | Buildroot `package/pipewire/pipewire.mk`: `-Dalsa=enabled`, `-Dpipewire-alsa=enabled` com ALSA+udev | Gerados `usr/lib/spa-0.2/alsa/libspa-alsa.so` e `usr/lib/alsa-lib/libasound_module_{pcm,ctl}_pipewire.so`; roteamento RK817 ainda não testado |
| Storage e bind mounts próprios | muOS `script/init/async/S06mount.sh`, `script/device/storage.sh`, `bind.sh` | Layout `/run/muos/storage`, partições e conteúdo ainda não integrados |
| Inicialização completa e tarefas de manutenção | muOS `script/init/sysinit`, `S99muos.sh` | Ainda não ligar `sysinit`: requer frontend, hotkeys, storage, perfis e utilitários adicionais |
| Shutdown completo antes de desmontar | muOS `script/init/shutdown` → serviços em ordem inversa | Integração futura deve entrar antes da desmontagem do BusyBox e ter um único proprietário por serviço |

O Buildroot instala o executável e configurações de PipeWire/WirePlumber, mas
as receitas selecionadas não fornecem serviço SysV para iniciá-los. Instalar
essas bibliotecas não significa que o áudio estará funcionando no boot.
O ambiente upstream (`script/var/base.sh`) usa `XDG_RUNTIME_DIR=/run` e
`PIPEWIRE_RUNTIME_DIR=/run`. A configuração de roteamento RK817 deve ser própria
do R35S; não copiar o perfil de áudio de outro aparelho RK3326 pelo nome do SoC.

**Decisão:** validar primeiro PID1/serviços básicos do Buildroot. Na integração
muOS, adotar um único proprietário de udev/D-Bus/áudio, com start/stop coerentes,
e ligar `sysinit`/`shutdown` apenas quando os contratos acima forem atendidos.
Não criar silenciosamente dois fluxos de boot concorrentes. Não executar esses
scripts no Debian instalado para "testar" o init autônomo. O caminho
`musplash`/mmap continua excluído dos ensaios enquanto sua falha não for explicada.

## Auditoria da saída real

O [verificador](../../port/scripts/verify-phase4-rootfs.py) inspeciona a árvore
gerada e a imagem ext4 sem montá-las. Confere executáveis básicos, ELF64
AArch64, loader resolvido **dentro** do rootfs, nota GNU de ABI Linux da glibc
e features do superbloco. Rejeita as quatro features deliberadamente excluídas
e flags fora do perfil estreito inicial. A nota ABI não comprova compatibilidade
de todos os syscalls com o BSP.

O [probe de userspace](../../port/probes/phase4-rootfs-abi.c) foi compilado
com a toolchain nova e testou libc, pthread, eventfd, epoll e clock monotônico.
Uma execução em QEMU user-mode testa loader/bibliotecas no host; não testa o
kernel BSP, PID1, drivers, tela, input ou áudio. O ensaio nativo usou diretório
temporário e loader explícito, preservando `/lib` do Debian. Binários aprovados
na Fase 3 não entram automaticamente neste rootfs.

O GCC foi configurado com `--with-cpu=cortex-a35`. A glibc já gerada contém
nota `NT_GNU_ABI_TAG: Linux 4.4.0`; `build/config.h` confirma
`__LINUX_KERNEL_VERSION_STR "4.4.0"`. Os headers instalados anunciam
`LINUX_VERSION_CODE 263357` (4.4.189). Essa conferência antecipada passou também
no parser do port, sem aguardar o fim dos demais pacotes; ainda não é resultado
de boot. O QEMU da auditoria usou explicitamente `-cpu cortex-a35`, e o probe
usou loader/library-path explícitos para evitar confundir a libc nova com a
do ambiente de build ou do Debian instalado.

Depois de um build concluído com status 0, executar:

```sh
bash port/scripts/audit-phase4-rootfs.sh
```

Esse estágio verifica a imagem, recompila o probe contra o sysroot novo e
executa os ensaios QEMU com timeout. Somente após essas verificações ele gera
`dist/phase4/rootfs-headless/`, com imagem de filesystem, manifestos, fontes
do port, checksums e aviso de que não se trata de firmware gravável.
O cache contém as fontes dos pacotes. A coleta `legal-info` inicialmente
rejeitou o hash de `COPYING`: o recipe padrão espera o texto curto dos kernels
novos, enquanto o BSP 4.4 contém a GPLv2 completa com a nota de uso por syscalls.
O arquivo da árvore de headers coincide com o da fonte Linux fixada, SHA256
`af8067302947c01fd9eee72befa54c7e3ef8a48fecde7fd71277f2290b2bf0f7`.
O [arquivo de hashes próprio](../../port/device/rk-r35s-p0/phase4-linux-headers.hash)
e o [coletor offline](../../port/scripts/collect-phase4-legal-info.sh) fornecem
`LINUX_HEADERS_HASH_FILES` para essa versão. A nova coleta terminou com status 0.
Não se desabilitou a verificação nem se alterou o Buildroot de referência.
Seu aviso sobre o próprio fonte Buildroot foi preservado; foi gerado também
um arquivo Git dessa revisão. Revisão de licenças/fontes antes de release
continua necessária, especialmente quando forem incluídos os providers GPU.

```sh
bash port/scripts/collect-phase4-legal-info.sh
# Aguardar o container muos-r35s-phase4-rootfs-legal e conferir:
cat build/phase4/rootfs-legal-info.exit
```

Os manifestos registram 22 pacotes de destino. Licenças, fontes dos pacotes,
manifestos e o arquivo Git do Buildroot ficam em
`build/phase4/rootfs-output/legal-info/`. Os resumos/licenças e o fonte Buildroot
também acompanham o artefato local. As fontes completas dos demais pacotes
permanecem no cache/coleta em `build/`; o pacote experimental não é um release.

Continuam abertos os gates gráficos/licenças, payload/init muOS completo,
bootloader/DDR/BL31, DTB de U-Boot e boot real da candidata. A Fase 4 permanece
em andamento e nenhum teste desta compilação exige gravar cartões.

Próximo incremento: completar dependências e perfil RK817, reconstruir os
utilitários muOS contra este sysroot e integrar start/stop com um único
proprietário por serviço; depois fechar GPU/SDL e cadeia de boot. O `/etc/fstab`
genérico Buildroot ainda declara `/dev/root` como ext2/noauto; a configuração
final deve expressar ext4 e o layout escolhido, sem fixar cegamente nomes MMC.
