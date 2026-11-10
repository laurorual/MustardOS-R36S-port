# Fase 4 — boot diagnóstico da ext4 própria

**Resultado:** B01 aprovado no segundo boot, após a correção de formatação. Logs coletados, fsck offline e saúde do dArkOSen após retorno passaram. A base de 512 MiB e os checkpoints anteriores permanecem imutáveis. O teste será limitado a PID 1 diagnóstico, storage e carregamento explícito de gpio_keys, sem rcS completo, frontend ou rede.

## Implementação e evidências

O [preparador](../../port/scripts/prepare-phase4-ext4-diagnostic.py) confere o SHA256 da base `ccdb9c0a…13fc0`, copia para arquivo regular e usa debugfs no container já fixado. Altera quatro arquivos: `/etc/default/muos-ui` (`enabled=0`, `hotkeys=0`), marcador próprio, [PID 1 diagnóstico](../../port/device/rk-r35s-p0/ext4-diagnostic/init) e guarda de CID. Cria também `/boot`, ausente na base. A comparação de todos os demais arquivos regulares e links passou; binários, bibliotecas e módulos permanecem os da imagem auditada.

Fsck, leitura de features/inode, extração independente e QEMU Cortex-A35 passaram. O probe de kmod usa `-0 modprobe`, reproduzindo o argv0 da symlink real; uma tentativa anterior de chamar `kmod modprobe` foi recusada no host e corrigida antes da candidata. QEMU verifica resolução de dependências sem carregar módulos. Não demonstra sucesso do syscall de carga em hardware.

O [perfil U-Boot](../../port/device/rk-r35s-p0/uboot-ext4/board.h) seleciona `root=PARTUUID=4d554432-02 rootfstype=ext4 rootwait ro init=/sbin/muos-ext4-diag`. Não inclui initramfs neste perfil. [O carregador](../../port/device/rk-r35s-p0/uboot-linux/boot.c) conserva tamanho/SHA256 de Image/DTB, reservas, ambiente em RAM e exclusões de recovery. O executável contém `booti 0x02000000 - 0x01f00000` e não contém o nome do initramfs. O hash da raiz é conferido na imagem/releitura da mídia; não existe verificação criptográfica da raiz pelo U-Boot.

O kernel fixado tem EXT4_FS/DEVTMPFS_MOUNT/MSDOS_PARTITION built-in e parser PARTUUID em `init/do_mounts.c`. Os recursos ext4 64bit/orphan_file/metadata_csum_seed/fast_commit já estavam excluídos pela receita da base. Não foi necessário recompilar kernel ou userspace.

| Parte | Layout planejado |
| --- | --- |
| Imagem | 640 MiB |
| Boot chain | Mesmos setores 64/16384/24576 dos ensaios anteriores |
| MBR | Assinatura `0x4d554432` |
| p1 | FAT32 de 100 MiB, início 16 MiB, label MUOSDIAG |
| p2 | Ext4 de 512 MiB, início 128 MiB, PARTUUID `4d554432-02` |

## Comportamento do PID 1

O kernel monta a raiz ro. O init monta proc/sysfs e tmpfs em run/tmp, confere release/modelo/marcadores/CID e MAJ:MIN da raiz. A presença do cartão original de 32 GB recusa o teste antes de remount rw.

Em seguida pede **somente** `modprobe gpio_keys`, exige `/sys/module/gpio_keys` e `odroidgo3-keys` em proc input, remonta a raiz rw e executa start/status/stop do S90 de storage. O S90 usa os mesmos binds/identidades já exercitados em namespace na fase anterior. Depois faz sync e remount ro da raiz, salva DIAG02 no FAT e desmonta o FAT antes da tela final. Não chama rcS, S95, S96 ou S99; não valida coldplug geral. Eventos dos botões, áudio, GLES e frontend continuam fora do recorte.

Se uma etapa falhar, o probe tenta parar o storage e retornar a raiz a ro; não imprime o marcador de sucesso. Falhas anteriores ao PID 1 ou a validação de mídia podem não gerar logs. Operações de I/O não têm limite rígido se o kernel ficar bloqueado; guardar a mensagem na tela e retornar ao cartão original com o aparelho desligado. Não remover mídia energizada.

## Guardas e orçamento desta rodada

O writer mantém destino exclusivo `/dev/mmcblk1`, CID/capacidade fixos e exclusão de raiz/boot originais. B01 aceita exatamente 640 MiB; A01/monitor continuam limitados a 128 MiB. Casos de tamanho maior/menor, experimento desconhecido e ausência de autorização foram recusados no host. Após escrita: fsync, invalidação de cache e releitura integral. Não usar esse writer para tamanhos arbitrários.

O saldo informado pelo usuário é 24% do limite de 5h. Não iniciar outra sequência de firmware após este recorte: concluir a preparação/checagens e, se houver ensaio físico, reservar o fechamento para retorno, logs e checkpoint. Nenhuma licença pendente foi tratada como resolvida; todo payload proprietário continua restrito ao uso privado.

## Artefatos atuais

Raiz diagnóstica: `build/phase4/linux-diagnostic/ext4.jixtcq08`.
U-Boot: `build/phase4/uboot-sd/probe.3utahq01`, pacote `package.ou1j44x6`.
A prova U-Boot está em `dist/phase4/uboot-sd-ext4-diagnostic/`.
A imagem e os resultados de mídia/boot serão registrados abaixo após conclusão, sem sobrescrever provas históricas.


## Primeiro ensaio e correção de formatação

O primeiro boot alcançou o PID 1 da ext4, mas parou em `Root device mismatch`.
A comparação usava saída tabulada de findmnt, que acrescenta espaços a
MAJ:MIN. O guard executa antes de remount rw, modprobe e S90, portanto esse
ensaio não aprovou módulos/storage e não entrou na parte de escrita da raiz.
O usuário voltou ao dArkOSen; saúde e kernel originais foram conferidos.

A correção usa `findmnt -rn -o MAJ:MIN /`. O binário AArch64 do SDK foi
executado em QEMU e sua saída validada como dígitos:digitos sem padding.
O [patcher limitado a um arquivo](../../port/scripts/patch-phase4-ext4-init.py)
confere CIDs, PARTUUID, capacidade, ausência de mount de p2 e hashes exatos;
exige que os novos bytes sejam precisamente a troca de `-n` por `-rn` nessa
comparação. Faz substituição atômica com modo/owner/fsync, desmonta e roda
fsck read-only. Tudo passou, sem modificar U-Boot/kernel ou regravar a imagem.

O cartão atual é a imagem original de 640 MiB, SHA256
`872cc3c441628e9686b8b89309d928e481878d8b74147c39c77638ebb6779f7c`,
**mais essa correção**. O raw inicial ainda contém o guard antigo; não
regravá-lo sem aplicar o patch ou reconstruir com o manifesto corrigido.
A cópia host corrigida `linux-diagnostic/ext4.0fns3h93` passou em fsck/QEMU.
A prova `dist/phase4/ext4-init-correction/` preserva o patch, hashes e
verificação; `dist/phase4/ext4-diagnostic-media/` preserva a escrita inicial.
O segundo ensaio foi confirmado na tela e nos três arquivos de DIAG02.


## Fechamento do B01

A prova nativa está em `dist/phase4/native-ext4-boot/`; análise em
`build/phase4/uboot-sd/probe.3utahq01/native-ext4-analysis.json`.
O report amostrado em uptime 6,75 s mostra `/dev/root / ext4 ro`, módulo
`gpio_keys` carregado sem taint, dispositivo `odroidgo3-keys`, status 0 e
marcadores STORAGE_OK/GPIO_KEYS_OK. S90 concluiu start/status/stop e seus
binds foram removidos. Não havia frontend, áudio ou rede em execução.
O fsck read-only da p2 retornou 0 após a volta ao dArkOSen. A primeira
coleta não encontrou e2fsck no PATH de sudo; foi repetida com o caminho
absoluto `/usr/sbin/e2fsck`, sem instalar pacotes ou alterar os cartões.

O dArkOSen permanece com Image `31bdb671…b0577`, taint 0, cinco contadores
Btrfs zerados e ES/ogage/Fn ativos. As montagens globais de SD2 foram
preservadas; o mount da coleta era privado/read-only e foi removido.
Somente o PID 1 diagnóstico foi testado: init BusyBox, rcS completo,
coldplug geral, eventos de input e frontend no kernel próprio continuam
fora desta aprovação. O próximo recorte testa init e serviços de base
sem UI/áudio, com ordem, readiness e parada verificados.
