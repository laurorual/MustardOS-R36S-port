# Fase 4 — reserva de memória e monitor visual, 25/10/2026

**Primeiro boot nativo do monitor confirmado:** o buffer do DTB de controle passou a ter
reserva nos dois alocadores, e o U-Boot ganhou um monitor visual para o
teste sem UART. A imagem privada de 128 MiB foi preparada no cartão secundário
de 128 GB por autorização explícita do usuário; a releitura integral passou.
O usuário confirmou os textos, a orientação, os endereços, o desligamento
por Power longo e o retorno normal ao dArkOSen no cartão original.

O usuário informou que não tem UART ou prefere não abrir o console. O
primeiro ensaio, portanto, usa texto na tela e mantém o kernel desativado.
Não equivale ao boot do Linux, rootfs ou frontend muOS.

## Proteção do DTB nos dois mapas

O [memory.h](../../port/device/rk-r35s-p0/uboot-sd/memory.h) fixa o nome
`muos-control-fdt` e intervalo `[0x01e00000,0x01e40000)`,256KiB.
O [adaptador](../../port/device/rk-r35s-p0/uboot-sd/board.c) usa
`sysmem_alloc_base_by_name`, com identidade própria, sem consumir o
`MEMBLK_ID_FDT` reservado ao DTB Linux.

Evidência na fonte fixada U-Boot5606e804:

- `lib/sysmem.c:694–762`: o mapa é reinicializado antes e depois da
  relocação; `board_sysmem_reserve` roda antes das reservas de framework e
  stack. O hook forte do port registra a região em cada mapa.
- `lib/sysmem.c:338–364,439–513`: pedidos comuns entram na lista de
  alocações e no LMB; colisões são rejeitadas. O caminho especial
  `sysmem_fdt_reserve_alloc_base` só registra reservas do kernel e não é
  substituto para esta alocação. Por isso não foi usado para o buffer.
- [patch0007](../../port/patches/0007-uboot-r35s-sd-probe.patch): o carregador
  chama novamente a reserva idempotente **antes** de `fatload`. Sem sysmem
  inicializado, RAM suficiente ou espaço livre, retorna erro antes da leitura.
- `common/bootm.c:70–71` usa outro LMB. O hook nativo
  `arch/arm/mach-rockchip/board.c:609–649` já existia e foi **estendido**
  para chamar `muos_reserve_bootm_fdt`, preservando sua configuração de
  `bootm_low`/`bootm_mapsize`. Não foi substituído por outro símbolo forte.

A configuração exige SYSMEM/BIDRAM/LMB. O auditor confere os hooks fortes,
as chamadas na fonte compilada e os hashes. A reserva protege alocações dos
frameworks; comandos interativos de acesso bruto à RAM/disco continuam
existindo e não formam um ambiente com todas as escritas proibidas.
`fs/fs.c:395–416` também mostra que `fatload` comum não consulta o sysmem:
os destinos fixos do port precisam continuar separados e conferidos.

## Teste com os alocadores nativos

O [harness](../../port/probes/uboot-memory/allocator.c), executado pelo
[auditor de memória](../../port/scripts/audit-phase4-uboot-memory.sh), liga
**os próprios** `lib/sysmem.c`, `lib/lmb.c` e `arch/arm/mach-rockchip/memblk.c`
da revisão fixada ao adaptador do port. Não implementa outro alocador para
simular o resultado. O processo x86_64 usa páginas anônimas privadas; não
acessa `/dev/mem` ou dispositivos. UBSan terminou sem erro.

Passaram: rejeição antes de init, reserva em initf/initr, idempotência sem
duplicar registros, colisão rejeitada, região adjacente permitida, Linux FDT
separado, exclusão no LMB de boot, stack sobreposta rejeitada, falta de RAM e
lacuna entre bancos rejeitadas. Também passou com os bancos observados no
Linux instalado, incluindo as lacunas ATF/TEE.

Os testes do monitor usam chamadas de tela **mockadas**, conferindo os gates
de tamanho/endereço/geometria e os argumentos formatados em nove linhas.
Não exercitam MMIO, renderer, comandos DSI ou legibilidade física. A
descoberta BIDRAM/ATAGS e o orçamento do malloc_f de8KiB também não são
reproduzidos pelo harness; dependem do boot real.

Provas negativas em cópias temporárias rejeitaram device SD alterado dentro
do ELF, remoção de PANIC_HANG, hook de memória transformado em símbolo weak,
CRC U-Boot incorreto e hash de componente trust incorreto. Os testes de
contêiner mantiveram o checksum externo atualizado para testar a validação
interna, não somente o hash do arquivo.

## Memória observada no dArkOSen

Leitura SSH, sem alterar memória/dispositivo:

| Região disponível no DT Linux instalado | Intervalo, fim exclusivo |
| --- | --- |
| Banco0 | `0x00200000–0x08400000` |
| Banco1 | `0x0a200000–0x40000000` |

`/proc/iomem` também informou código do kernel a partir de0x02080000,
coerente com o cálculo do `booti` desta revisão. Os zeros adicionais em
`memory/reg` são slots vazios. MemTotal observado:916904kB.

O parser nativo `param_parse_optee_mem`, em
`arch/arm/mach-rockchip/param.c:97–142`, continua lendo ATAGS/estrutura
legada independentemente de OPTEE_CLIENT. Desligar o cliente RPC/RPMB não
removeu essa descoberta de reserva; BIDRAM segue habilitado. Os dois bancos
observados não são, porém, medição de `gd` da candidata nova. Os endereços
exibidos pelo monitor próprio estão registrados no ensaio físico abaixo;
o monitor não imprime a lista completa de bancos e reservas ATAGS.

As fontes de vídeo reservam antecipadamente framebuffer640×480×4 mais
pool32MiB. O monitor rejeita ranges incoerentes antes de chamar `lcd_init`;
depois confere640×480, rotação0, BPP24 e intervalo do framebuffer nativo.
O framebuffer RGB888 usado pelo helper cabe na reserva maior de32bpp.
Não foi usado mmap do framebuffer Linux, que permanece excluído por causa
das falhas históricas ainda não explicadas.

## Monitor e imagem de teste

O monitor mostra `muOS - R35S / Panel 0`, `SD monitor: U-Boot reached`,
autoboot OFF e valores de RAM top, vídeo, relocação U-Boot, stack e DTB.
Usa os helpers nativos do display; não contém emulador de UI ou frontend
alternativo. O bootcmd Linux permanece desativado por BOOTDELAY−1.

Build final deste incremento:
`build/phase4/uboot-sd/probe.xqc7am2o`, pacote `package.x5asz5qk`.
U-Boot binário859063bytes, SHA256
`18bf64186e08765f0c47d5b53dfb78497462abf3449819317cb253f3cb76b533`.
DTB externo mantém `b28dd7236b407476c3dac4e0edae69ed9fab6897abd03bb8e8e8fe86fa4b9551`.
Os checkpoints anteriores são imutáveis:
`dist/phase4/uboot-sd-memory/` e `dist/phase4/uboot-sd-monitor/`.

O [builder da imagem](../../port/scripts/build-phase4-monitor-image.py)
opera exclusivamente sobre arquivos regulares em `build/`. Usa dosfstools
4.2-1.2 e mtools4.0.48-1 em container derivado da imagem fixada, sem instalar
pacotes no Bazzite. ID do container de ferramentas:
`sha256:4d5c100835e155188d742a07aa0ae8823bed2fefa26770e23d5cea559b83a8a8`.

| Parte da imagem | Layout |
| --- | --- |
| Tamanho | 134217728bytes,128MiB |
| Tabela | DOS/MBR, assinatura de disco `0x4d553435` |
| idbloader / U-Boot / trust | setores64 /16384 /24576, sem sobreposição |
| p1 | FAT32, setor32768,204800setores,100MiB, label `MUOSMON` |
| Arquivos FAT | DTB de controle, `COPYING.TXT`, `PROBE.TXT` |
| Linux/rootfs | Não incluídos; nenhum kernel é iniciado automaticamente |

Fsck FAT, parsing pelo fdisk e releitura mtools **da imagem final** passaram.
A descompressão gzip também foi conferida contra o hash da imagem raw.
Não se declarou identidade bit a bit entre reconstruções em outros diretórios.

Imagem raw SHA256:
`6a67c21e7a00af92c785bf3d60ed81684e83b02c03c902ca80a51ec22cbfe2b7`.
Gzip SHA256:
`17ac1bd66fe22d4fd8ef1e4ef745e758032e69bdaad45adfdf42ae57fb34f5f3`.
Arquivos privados em `monitor-image.0c45_wjn/` dentro do build; os payloads
DDR/miniloader/BL31/BL32 e a imagem não entraram nos checkpoints em dist.
Termos pendentes continuam no registro para o relatório final solicitado.

## Preparação autorizada do cartão secundário

O usuário ofereceu o Steam Deck com leitor e autorizou usar SSH para
preparar o secundário se fosse mais simples. A operação foi vinculada ao
cartão já identificado de127934660608bytes, `/dev/mmcblk1`, CID SHA256
`12d2c78fbc14993fe2f8a00c413a5e3ef8d9659a3eba9a41a77b5c37029aa193`.
O sistema estava em `/dev/mmcblk0p2`, no cartão separado de32GB.

O [writer](../../port/scripts/write-phase4-monitor-card.py) tem inspeção como
default. O modo explícito confere arquitetura/kernel/modelo, raiz e boot,
identidades distintas e capacidade, saúde do kernel/Btrfs, bateria e os
hashes do programa/gzip/raw antes de parar serviços. O diretório de trabalho
remoto foi tmpfs. A bateria estava em100%.

ES/ogage/Fn foram parados e `/opt/system/Tools` e `/roms2` desmontados.
Não houve unmount forçado/lazy. O dispositivo foi aberto com O_EXCL após
checar ausência de mounts e novamente CID/capacidade. Foram escritos apenas
os134217728bytes previstos. Depois: fsync, BLKFLSBUF e releitura integral.
O hash do cartão coincidiu com a imagem, sem depender só do page cache.
Não se releu a tabela de partições durante a sessão para evitar reativar
consumidores do layout antigo.

A unidade transitória independente de SSH terminou em10,806s, status0,
`verified=true`. O `Image` instalado manteve SHA25631bdb671…b0577;
taint0 e os cinco contadores Btrfs0. Esses são indicadores do **dArkOSen
instalado**, não da candidata. Os registros foram coletados no host antes
de solicitar poweroff. A desconexão SSH após esse pedido foi registrada;
o usuário confirmou depois o monitor e o retorno ao sistema original.

Prova congelada: `dist/phase4/monitor-media-proof/`, com plano autorizado,
resultados, tabela/fsck e fontes do builder/writer. A prova registra escrita
verificada e boot ainda pendente; resultados físicos posteriores terão
registro separado, sem reescrever esse checkpoint.

## Ensaio físico e recuperação

Com o console completamente desligado: guardar o cartão dArkOSen32GB,
passar o128GB para o slot do sistema e deixar o segundo vazio. O ensaio
espera somente o monitor parado; não há Linux, menu, rede ou SSH.
Confirmar textos/orientação e, se possível, os endereços mostrados.

Para voltar ao dArkOSen, desligar antes de qualquer troca e recolocar o
cartão32GB no slot original. Deixar o secundário fora no primeiro retorno
evita que o sistema tente usar seu novo FAT como o antigo volume de ROMs.
O conteúdo anterior do secundário foi substituído conforme a autorização
e o backup já informado; sua capacidade física não foi reduzida. A partição
pequena é intencional neste ensaio e poderá ser refeita depois.

**Resultado físico aprovado pelo usuário:** “Monitor apareceu e o texto
está correto”. O teste ocorreu com o cartão de 128 GB no slot de OS e o
cartão dArkOSen guardado. Os valores foram transcritos da tela; a linha
U-Boot foi reconfirmada explicitamente com oito dígitos.

| Valor mostrado | Endereço hexadecimal |
| --- | --- |
| RAM top | `0x40000000` |
| Video | `0x3de00000–0x3fff0000` |
| U-Boot | `0x3dd08000` |
| Stack | `0x31cfd580` |
| Control DTB | `0x01e00000` |

**Conferência no host:** o ELF tem `_start=0x00200000` e
`__bss_end=0x002f7fe8`. Assim, o monitor ocupa `0x000f7fe8` antes de
alinhamento; `(0x3de00000 - 0x000f7fe8) & ~0xfff` reproduz
`0x3dd08000`. A reserva de vídeo tem espaço para framebuffer e pool; a
stack, incluindo sua guarda de 2 MiB, fica acima dos destinos planejados
do kernel e dos dois FDTs. A folga de 64 KiB até RAM top é coerente com
a reserva de tabelas MMU do fonte. Isso confirma os valores mostrados
neste build; não é uma leitura completa da RAM nem teste de estabilidade.

O Power longo desligou sem retornar ao monitor. O usuário recolocou o
cartão dArkOSen no slot original e confirmou boot normal. Esse resultado
valida a saída física deste monitor, sem implementar política de Power,
bateria ou shutdown no Linux candidato.

**Retorno conferido via SSH após reconectar o Wi-Fi:** o cartão original
mantém seu CID, `/` em `/dev/mmcblk0p2` Btrfs e `/boot` em
`/dev/mmcblk0p1` FAT. Kernel `4.4.189`, Image SHA256
`31bdb671d640863448b59f79801277fe486fa6c78c326bd4ebb51a54559b0577`,
taint 0, os cinco contadores Btrfs 0 e ES/ogage/Fn ativos. Nenhuma unidade
`muos*` permaneceu carregada. A busca no ring buffer não encontrou falha
classificada de MMC/Btrfs/Oops/panic; o padrão amplo capturou a mensagem
normal `ramoops: attached`, excluída e registrada como falso positivo.
Isso não equivale a teste prolongado ou imagem integral do cartão original
idêntica byte a byte. O secundário de 128 GB está novamente no segundo
slot, identificado por CID e sem montagem. A conferência foi somente de
leitura e não iniciou outra gravação ou sessão de frontend.

A prova física fica em `dist/phase4/native-monitor-boot/`, vinculada aos
hashes do executável, da imagem e da releitura do cartão. As provas do host
e da escrita continuam imutáveis, com os estados anteriores ao teste.
O fechamento SSH posterior está em `dist/phase4/native-monitor-return/`;
a prova física anterior mantém corretamente seu estado de SSH pendente
naquele instante.

O recorte aprovado é ROM→DDR/miniloader→trust/U-Boot→display e endereços
mostrados, neste único Panel 0. **Kernel próprio, raiz persistente, coldplug,
energia e frontend em boot novo continuam pendentes.**

## Próximo menor incremento

Preparar um boot diagnóstico do Linux próprio na mídia secundária, com
init mínimo e frontend desativado. Antes de gravar, definir como observar
o progresso sem UART: console de texto, registro persistente pelo init e
marcador inequívoco de chegada ao userspace. Falhas anteriores ao init
podem não produzir arquivo de log; tela e retorno ao cartão original
continuam necessários. Auditar o mapa final após incluir Image/DTB/raiz e
conferir identidade da mídia novamente antes de qualquer nova escrita.
Não reutilizar a aprovação do monitor como aprovação do kernel/rootfs.
