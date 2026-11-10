# Fase 1: execução AArch64 de muinput no R35S

**Resultado em 23/10/2026: aprovado para `--list-devices`.** O binário upstream foi compilado em container no Bazzite e executado como `ark` no R35S, usando as bibliotecas já instaladas. A execução nativa terminou com status 0. Não foi iniciado o daemon nem implementado um backend R35S.

## Escopo autorizado e fonte

Esta etapa sucede a auditoria estática. O usuário solicitou começar a Fase 1 e autorizou conexão SSH. Foram permitidos somente o levantamento de ABI e o teste temporário descrito no roadmap; nenhum serviço, bootloader, kernel, DTB ou configuração persistente foi alterado. Credenciais não foram gravadas em scripts, relatórios ou comandos de build.

Fonte compilada: `refs/muos/frontend`, commit `5e8635b3b485eec9ad2ace141c415fd2df47d8f1`, somente subdiretório `input/`. A cópia veio de `git archive` para `build/phase1/source/`; o repositório de referência permaneceu intacto. Não houve patch nas fontes muOS. O `LICENSE` GPLv3 e as fontes correspondentes acompanham o artefato local.

O caminho de listagem em `input/main.c:146–151,268–295` termina antes de criar runtime/uinput ou selecionar/inicializar hardware. A leitura opcional de intensidade em `/opt/muos/device/config/board/strength` precede o parser, mas não escreve nesse caminho.

## Ambiente efetivamente observado

O retorno fornecido pelo usuário na Fase 0 foi complementado e conferido por SSH:

| Item | Resultado |
| --- | --- |
| Modelo DT | `R36S-V12 2023-08-18 Panel 0` |
| Arquitetura/userspace | `aarch64`, `getconf LONG_BIT=64` |
| Kernel | `4.4.189 #1 SMP Thu Oct 1 02:03:12 UTC 2026` |
| Distribuição | Debian GNU/Linux 13, trixie, `DEBIAN_VERSION_FULL=13.7` |
| libc instalada | `glibc 2.41`; `libc6:arm64 2.41-12+deb13u4` |
| Multiarch | `libc6` e `libc6-dev` instalados para arm64 e armhf; este teste utiliza somente arm64 |
| Interpreter | `/lib/ld-linux-aarch64.so.1` → `/usr/lib/aarch64-linux-gnu/ld-linux-aarch64.so.1` |
| Raiz | `/dev/mmcblk0p2`, Btrfs, subvolume `/` |
| Boot | `/dev/mmcblk0p1`, vfat |
| `/tmp` | tmpfs, `rw,nosuid,nodev`, sem `noexec` |
| Input power | `rk8xx_pwrkey`, event0 |
| Fone | `rockchip,rk817-codec Headphones`, event1 |
| Gamepad | `GO-Super Gamepad`, js0/event2 |
| Teclas separadas | `odroidgo3-keys`, event3; não houve captura de pressões nesta fase |

O cmdline fornecido inclui `max_cpufreq=1512 boot_cpufreq=1296`. Nenhuma frequência foi alterada. A existência de armhf não altera o objetivo AArch64 e não comprova compatibilidade de qualquer binário de outro firmware.

## Build reproduzível e ABI

Receita: [phase1-toolchain.Containerfile](../../port/packaging/phase1-toolchain.Containerfile). Driver de build: [build-phase1-muinput.sh](../../port/scripts/build-phase1-muinput.sh).

- Base amd64 Debian fixada em `docker.io/library/debian@sha256:4876fdea29cac1a33a3195f1eb1952feb1fca7dd6dd00be3e2f1879cf20d34d2`.
- APT em snapshots Debian/debian-security `20261023T000000Z`, com verificação de assinatura preservada. Apenas a validade temporal dos índices históricos foi desativada.
- GCC AArch64 `14.2.0-19cross1`, binutils `2.44-3`, libc cross e headers `2.41-11cross1`. A lista completa de pacotes acompanha o artefato.
- Container rootless; nenhuma dependência instalada no host ou aparelho. A compilação ocorre sem rede, sem capabilities e com root do container somente leitura; apenas `build/phase1/` é montado para escrita.
- Makefile próprio de input, C11, `-O2`, LTO, `-march=armv8-a`, FORTIFY 3, stack protector, PIE e RELRO/BIND_NOW. Sem `-mcpu=cortex-a53`, `-march=native` ou extensões crypto presumidas. `-D_GNU_SOURCE` acompanha a política do Makefile global upstream.
- `SOURCE_DATE_EPOCH=1792704399` e mapeamento de paths de build; reconstruções completas produziram bytes idênticos. Não foi usado `make check`, que executaria o alvo AArch64 no host.

O sysroot é o fornecido pelos pacotes cross arm64 do Debian trixie, **não uma cópia exata do rootfs do aparelho**. A versão de pacote libc difere da instalada; por isso a decisão não se baseou somente no nome Debian 13. Foram conferidos os símbolos versionados, o baseline de kernel, o carregamento pelo loader real e a execução no dispositivo. Isso vale para este binário e este caminho de execução.

| Propriedade do artefato | Resultado |
| --- | --- |
| Arquivo | `dist/phase1/muinput`, 154120 bytes |
| SHA256 | `e823ac36d83240c31b7adf859e60c63602cd61a2cbf6e218880c9595ef6229d7` |
| ELF | ELF64 little endian, AArch64, executável PIE |
| Interpreter | `/lib/ld-linux-aarch64.so.1` |
| DT_NEEDED | `libm.so.6`, `libc.so.6`, `ld-linux-aarch64.so.1` |
| Versões requeridas | GLIBC_2.17, GLIBC_2.33, GLIBC_2.34, GLIBC_2.38 |
| Símbolos externos fortes | 95; todos encontrados nas bibliotecas reais do aparelho |
| Baseline GNU ABI tag | Linux 3.7.0 no ELF, na libc cross e em libc/libm do alvo; inferior ao kernel 4.4.189 |
| Loader real | `--verify` e `--list` passaram, resolvendo as bibliotecas do sistema |

Não foi necessário copiar libc, libm ou loader para o R35S. A auditoria não usou `ldd` do host para deduzir dependências AArch64.

## Execução e limpeza

O [run-phase1-probe.sh](../../port/scripts/run-phase1-probe.sh) verifica checksums locais, modelo, arquitetura, glibc e flags de montagem antes de criar um diretório aleatório em `/tmp`. Transfere somente o binário, confere SHA256 e usa ambiente limpo. O comando de execução foi equivalente a:

```sh
env -i PATH=/usr/bin:/bin LC_ALL=C MUOS_RUMBLE_STRENGTH=0 \
    /tmp/muos-r35s-phase1.XXXXXX/muinput --list-devices
```

Trecho da saída real, em 23/10/2026 às 18:05 de São Paulo (21:05 UTC):

```text
MODEL=R36S-V12 2023-08-18 Panel 0
KERNEL=4.4.189
LIBC=glibc 2.41
...
rk-g350-v    G350 V
rk-pixel-2   GKD PIXEL 2
rg-vita-pro  ANBERNIC RG VITA PRO
LIST_DEVICES_EXIT_STATUS=0
```

Foram listados os 21 backends upstream, sem perfil R35S/R36S, como esperado. A listagem não tenta detectar o handheld.

A limpeza por trap foi confirmada por uma segunda leitura: nenhum diretório `muos-r35s-phase1.*` em `/tmp`, nenhum processo `muinput` restante e ausência de `/opt/muos`, `/run/muos` e `/run/muinput`. EmulationStation permaneceu `active`, e os quatro dispositivos input originais continuaram presentes. Não houve modeset, grab, injeção de eventos, instalação, mudança de mixer, GPIO ou serviço.

Evidências locais, ignoradas pelo Git:

- `build/phase1/toolchain-build.log`, `compile.log`: instalação isolada e comandos de compilação.
- `build/phase1/target-inventory.txt`, `target-libraries.txt`, `target-symbols.txt`, `target-symbol-check.txt`: inventário e conferência dos 95 símbolos.
- `build/phase1/device-test-20261023T210529Z.txt`: saída integral do teste nativo.
- `dist/phase1/`: binário, licença, `upstream-source.tar`, versões, manifesto, inspeção ELF e `SHA256SUMS`. O campo de runtime do manifesto de build não substitui este relatório de execução.

## Repetição e limites

No host, a reprodução usa a base já baixada por digest; em máquina nova é necessário obtê-la primeiro. Não executar esses comandos dentro dos refs:

```sh
podman pull docker.io/library/debian@sha256:4876fdea29cac1a33a3195f1eb1952feb1fca7dd6dd00be3e2f1879cf20d34d2
bash port/scripts/build-phase1-muinput.sh
# A linha seguinte repete o ensaio temporário no alvo informado.
bash port/scripts/run-phase1-probe.sh ark@ENDERECO_DO_R35S
```

O runner exige host key já conhecida e glibc 2.41; divergências param o teste para revisão. Ele não contém senha. Uma sessão SSH multiplexada pode ser indicada por `MUOS_SSH_CONTROL`; a conexão criada nesta execução foi encerrada ao concluir, preservando o terminal SSH que já estava aberto.

**Concluído:** toolchain isolada, build sem patch, inspeção de ABI, comparação de símbolos, carregamento e caminho CLI nativo, limpeza e documentação.

**Não validado:** leitura de botões/sticks, criação de uinput, rumble, GPU/SDL/GLES, framebuffer, áudio, bateria, power/suspend, frontend e boot autônomo. Também não foi provada execução de todos os caminhos internos do daemon. O próximo passo do roadmap é a Fase 2, começando pelo inventário gráfico e um teste de tela separado; nenhum teste dessa fase foi iniciado automaticamente.
