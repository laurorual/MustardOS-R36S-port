# Fase 4 — primeiro boot diagnóstico do Linux próprio

**Resultado: primeiro boot nativo do Linux próprio aprovado no recorte
diagnóstico.** A tela final foi confirmada pelo usuário, os três logs foram
recuperados e o retorno ao dArkOSen foi conferido por SSH. Release próprio,
raiz em RAM, console e taint 0 estão registrados. A ext4 completa e o
frontend ainda não iniciaram no kernel próprio. As provas da preparação
preservam seus estados anteriores ao teste físico.
O cartão dArkOSen de 32 GB permanece a recuperação preservada.

## Recorte escolhido

O [monitor anterior](phase4-memory-monitor.md) confirmou U-Boot/display no
Panel 0. Este incremento acrescenta o Image/DTB Linux já compilados e uma
raiz mínima em RAM. Não usa a ext4 completa com autostart do frontend;
assim, a chegada ao PID 1 pode ser observada antes de integrar storage,
hotkeys, GPU userspace, áudio, rede e serviços muOS.

O usuário confirmou disponibilidade para trocar os cartões e acompanhar o
primeiro boot. A preparação via SSH reutiliza a autorização anterior para
o secundário de 128 GB e a continuação solicitada da Fase 4. O original
de 32 GB não é destino de gravação e ficará fora durante o ensaio.

## Fontes e caminhos efetivamente usados

- O [preparador](../../port/scripts/prepare-phase4-linux-diagnostic.py) usa
  o BusyBox e três bibliotecas **do sysroot próprio**, não do Debian do
  console. Inclui `lib64 -> lib`, necessário ao caminho de busca desta
  glibc. A primeira prova QEMU detectou a ausência desse link; a correção
  foi feita antes de preparar a candidata de boot. A tentativa recusada
  está preservada em `initramfs.utb12gs4/`; a aprovada é `initramfs.rtp27nen/`.
- O arquivo newc contém `/init`, `/dev/console` 5:1, `/dev/null` 1:3,
  BusyBox, loader, libc, libresolv e applets selecionados. Não contém
  módulos, firmware, frontend, Mali ou scripts rcS do produto.
- O [init diagnóstico](../../port/device/rk-r35s-p0/linux-diagnostic/init)
  exige PID 1, monta proc/sysfs/devtmpfs e mostra `INIT REACHED` em tty0.
  Exige o release próprio, AArch64 e o model Panel 0. Não executa reboot
  ou poweroff: permanece parado para observação.
- A [guarda](../../port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh)
  procura o CID do secundário com capacidade exata e recusa a presença
  do CID do cartão dArkOSen. Monta somente sua p1 FAT, primeiro read-only,
  exige `DIAG.ID=MUOS-R35S-LINUX-P4-A01` e só depois permite gravar os logs.
  Os arquivos são `DIAG01/REPORT.TXT`, `DMESG.TXT` e `RESULT.TXT`.
  O marcador final na tela só aparece após sync e umount bem-sucedidos.
- O [perfil U-Boot](../../port/device/rk-r35s-p0/uboot-linux/board.h)
  habilita autoboot em 3 segundos para o comando próprio
  `muos_linux_diag`. Mantém ambiente em RAM, exclusões de recovery/erase
  automático e panic parado do monitor. Não executa script vindo do FAT.
- O [carregador](../../port/device/rk-r35s-p0/uboot-linux/boot.c) reserva
  os três destinos no sysmem antes de fatload. Confere tamanho e SHA-256
  exatos de cada arquivo; leitura curta, excessiva ou hash divergente
  mostra STOPPED e não chama booti. O limite de leitura é tamanho+1, ainda
  dentro da reserva. O Image é o já auditado; seu header não é inferido
  a partir do nome do arquivo.

## Contrato de memória e console

| Recurso | Endereço/intervalo, fim exclusivo |
| --- | --- |
| DTB controle U-Boot | `0x01e00000–0x01e40000` |
| DTB Linux e margem | `0x01f00000–0x01f40000` |
| Image carregado + destino/BSS | `0x02000000–0x02ec0000` |
| Entry Linux após booti | `0x02080000` |
| Reserva initramfs | `0x0a200000–0x0aa00000` |

O header do Image fixa text_offset `0x80000`, image_size `0xe40000` e
flags `0xa`. `cmd/booti.c:62–83` da revisão U-Boot fixada move o Image
para `0x02080000`. O kernel ocupa até `0x02ec0000`, sem alcançar FDTs,
initrd ou as regiões altas mostradas pelo monitor anterior.

`common/image.c:1135–1164` e `common/image-fdt.c:230–270` implementam
initrd/FDT in-place quando `initrd_high`/`fdt_high` têm todos os bits em 1.
Esse perfil usa esses valores, com reservas explícitas e margem para
`CONFIG_SYS_FDT_PAD`. O LMB nativo continua reservando kernel, stack e
regiões do DTB no handoff. Os endereços altos do monitor anterior são
referência de um build diferente, não observação deste novo executável.

O kernel existente inclui BLK_DEV_INITRD, RD_GZIP, DEVTMPFS,
VT_CONSOLE, FRAMEBUFFER_CONSOLE, DRM_FBDEV_EMULATION e VFAT built-in.
A cmdline usa `rdinit=/init`, ttyFIQ0 + tty0, panic sem reset e não fixa
root em partição. O console Linux/DRM neste boot ainda depende do ensaio
real. Nenhum acesso mmap a `/dev/fb0` foi reintroduzido.

## Artefatos e provas do host

- Build U-Boot: `build/phase4/uboot-sd/probe.e1z1roxv`, pacote
  `package.z7v48cdq`, binário 860455 bytes, SHA256
  `e2f0d369d63a916a1d1cd93600ba1a41ca7d7aeaa678b42770673e7467ffedae`.
- Kernel SHA256
  `780935823cb8c86e4330c8c8157ebb4005fb5580e68e72c4b0c4e480bab42d2f`;
  DTB Linux `496bbe3591f8619f059ebc384277ecdd17fd41f956aef40de20afb46b92d5b49`.
- Imagem privada de 128 MiB em `linux-image.yu6fwzw8/`, MBR
  `0x4d554431`, p1 FAT32 de 100 MiB/setor32768/label `MUOSDIAG`.
  Raw SHA256 `85f82bff8dfc512844121e0129e4849d0f30239d1eceb58d4348d8b0f7dca848`.
- Provas separadas: `dist/phase4/uboot-sd-linux-diagnostic/` e
  `dist/phase4/linux-diagnostic-media/`. Excluem imagem raw, initramfs com
  bibliotecas e payloads proprietários. Uso privado/termos pendentes segue
  o registro do projeto; não se trata de release.

O [auditor do initramfs](../../port/scripts/audit-phase4-linux-diagnostic.py)
conferiu independentemente newc/payloads/nodes/links, ELF AArch64, applets,
syntax shell, execução BusyBox em QEMU Cortex-A35 e recusa fora de PID 1.
Seis fixtures de seleção de cartão passaram: ausente, secundário correto,
tamanho incorreto, original presente, CID duplicado e somente original.
Essas fixtures executam shell do host; QEMU não executou o init como PID 1
nem os mounts. A prova de memória liga os alocadores nativos com UBSan,
mas não executa o novo carregador/handoff em hardware.

ELF/defaults/autoboot/DTB e exclusões foram auditados no executável.
As provas negativas de devnum, panic, hook forte e contêineres passaram.
FAT/fsck, parsing de partições, releitura de todos os arquivos da imagem
final e gzip passaram. A gravação usou o writer com guards de identidade,
abertura exclusiva, fsync, invalidação de cache e releitura dos 128 MiB.
O hash releitura coincide com o raw. Antes do poweroff, Image instalado
inalterado, taint 0 e cinco contadores Btrfs 0.

## Ensaio físico e recuperação executados

Com o console desligado, guardar o cartão dArkOSen, mover o de 128 GB ao
slot OS e deixar o segundo vazio. Esperar até cerca de 60 segundos pelo
texto `Linux diagnostic: INIT REACHED` e `Logs saved: DIAG01 (FAT unmounted)`.
Sem shell por botões, rede ou frontend nesta etapa. Registrar a última
mensagem/tela se não chegar ao marcador. Não remover mídia energizada.

Depois da confirmação, desligar por Power longo, recolocar dArkOSen no
slot OS e o cartão de teste no segundo slot para coleta **read-only** dos
logs e nova conferência de saúde. A escrita dos logs durante o diagnóstico
ocorre somente no FAT do cartão de teste; não é ensaio read-only completo.

O usuário confirmou a tela prevista, incluindo `No frontend or network
started` e a instrução de Power. Depois informou “dArkOS está de volta e
conectado”. Não foi executado shutdown de software no Linux candidato.

O dArkOSen montou automaticamente o secundário em `/roms2` e fez bind de
`/tools` em `/opt/system/Tools`. A coleta inicial recusou essa condição
antes de montar/ler os arquivos. O [coletor ajustado](../../port/scripts/collect-phase4-linux-logs.py)
usa `unshare --mount --propagation private`, faz bind privado read-only e
confere `ro` via findmnt. Os arquivos foram lidos nessa visão e o bind
privado desmontado. As duas montagens globais rw do dArkOSen permaneceram
inalteradas; não foram parados serviços para a coleta. A propriedade
`secondary_unmounted_after_collection` descreve **o mount privado**, não
o cartão globalmente desmontado. O secundário continua montado pelo dArkOSen.

## Evidências nativas e pendências delimitadas

Arquivos recuperados em `build/phase4/uboot-sd/probe.e1z1roxv/`:
`report.txt`, `dmesg.txt`, `result.txt` e envelope `log-collection.json`.
O [analisador](../../port/scripts/analyze-phase4-linux-boot.py) produziu
`native-linux-analysis.json`, vinculando hashes de arquivos, imagem e kernel.
Prova final imutável: `dist/phase4/native-linux-boot/`.

Trechos do log/report, sem inferir aprovação de componentes não exercitados:

```text
Linux version 4.4.189-muos-r35s-p4 (muos@r35s-port)
Console: switching to colour frame buffer device 80x30
rockchip-drm display-subsystem: fb0:  frame buffer device
rootfs / rootfs rw,size=457560k,nr_inodes=114390 0 0
MemTotal:         916920 kB
TAINT
0
RESULT.TXT: INIT_REACHED_AND_LOGS_SAVED
```

O report foi amostrado em uptime **16,37 s**. `/proc/iomem` mostra kernel
code em `02080000–02beffff`, data em `02c70000–02ebffff` e os bancos
`00200000–083fffff`/`0a200000–3fffffff`, coerentes com o mapa analisado.
O log contém modo `640x480p60`, probe final `mali0`, registro RK817 e
`GO-Super Gamepad`. Isso valida console/display e enumeração nesse recorte;
não valida contexto EGL/GLES, reprodução de áudio ou eventos dos controles.
`/proc/modules` estava vazio, conforme o initramfs sem módulos.

Não foram encontrados Oops, BUG, panic, call trace ou erros I/O/MMC na
busca documentada dos logs coletados. Não é teste de estabilidade além
da janela capturada. Avisos de DRM/DSI `-517` foram seguidos por bind
bem-sucedido e framebuffer; `-517` corresponde a EPROBE_DEFER no BSP.
Os avisos selecionados abaixo também aparecem no log do dArkOSen restaurado:

- `drm-logo@00000000` com reserva de tamanho zero e `failed to parse loader memory`;
- trigger da IRQ170 e clock `clk_cabac`;
- rotas ASoC de MIC_IN/HPOL/HPOR sem widgets correspondentes.

Essa comparação evita classificá-los como regressões novas já comprovadas;
**não demonstra que sejam inofensivos**. Manter a investigação de logo,
IRQ, codec/rotas e demais diagnósticos antes de aprovar os recursos afetados.

O input `odroidgo3-keys` não apareceu. Fato: `.config` tem
`CONFIG_KEYBOARD_GPIO=m`; `rk3326-r35s-linux.dts:23–35` define os botões de
volume como `gpio-keys`; este initramfs não inclui/carrega `gpio_keys.ko`.
Isso explica a ausência esperada do dispositivo neste recorte. Validar
seu carregamento e os eventos no próximo rootfs antes de exigir volume/Fn.
Não há evidência deste ensaio para alterar o DTS ou renumerar event devices.

O retorno foi conferido duas vezes: kernel instalado `4.4.189`, Image
SHA256 `31bdb671…b0577` preservado, taint 0, cinco contadores Btrfs 0,
ES/ogage/Fn ativos e nenhuma unidade `muos*` carregada. As montagens globais
do secundário continuaram rw/noatime. O coletor temporário foi removido e
as sessões SSH foram encerradas. Nenhum módulo candidato foi carregado
no kernel dArkOSen. O FAT do teste agora contém os logs e diretórios
criados pelo próprio dArkOSen; não esperar que seu hash integral ainda
seja o da imagem pré-boot.

**Riscos/hipóteses:** falha anterior ao PID 1 pode não gerar log em cartão;
não há UART ou aprovação de pstore persistente entre cold boots. Mount/sync
podem bloquear em falha física de mídia e não possuem limite rígido neste
init; uma falha de gravação não deve ser interpretada como FAT desmontado.
Long Power já funcionou no monitor, mas shutdown Linux ainda não foi
implementado. Não considerar este ensaio aprovação da ext4 completa,
drivers userspace, coldplug de módulos, política de energia ou outros painéis.


## Próximo menor teste

Bootar a ext4 própria com init diagnóstico e autostart da UI bloqueado,
validando montagem/identidade, logs e módulos do release próprio antes de
iniciar a interface. O teste deve incluir carregamento de `gpio_keys` e
coldplug/input, sem forçar vermagic nem carregar esses módulos no Debian.
A imagem completa já auditada tem autostart configurado: preparar uma
cópia diagnóstica e não sobrescrever esse checkpoint. Planejar limites do
writer e coleta/parada antes de uma nova gravação maior que 128 MiB.
