# Fase 4 — executável U-Boot SD e contêineres privados, 25/10/2026

**Continuação posterior:** [reserva de memória e monitor visual](phase4-memory-monitor.md)
fechou a proteção do DTB e realizou o primeiro boot nativo aprovado no
cartão secundário. O relatório abaixo preserva o checkpoint anterior,
que ainda não incluía esse teste físico.

**Novo marco no host:** U-Boot AArch64 compilado com adaptador exclusivo do
R35S Panel 0, ambiente somente em RAM e autoboot desativado. O ELF, os
defaults efetivamente compilados e a tabela de comandos foram auditados.
DDR/miniloader, U-Boot e trust foram empacotados localmente com ferramentas
compiladas de fontes GPL; verificações independentes de formato passaram.
O trust gerado reproduz exatamente a referência instalada. **Não houve
SSH, gravação de cartão, execução ARM do bootloader ou teste de boot.**

Isso não encerra a Fase 4 nem constitui imagem pronta para cartão. Os
checkpoints anteriores de kernel/rootfs e
[display U-Boot](phase4-uboot-panel.md) continuam preservados.

## Implementação e contratos

Fonte base `christianhaitian/RG351MP-u-boot`, commit
`5606e804ffe8f9e5427d55c8da04c638f01a9391`, GPLv2 com termos por arquivo.
O preparador materializa uma cópia nova sob `build/phase4/uboot-sd/probe.*`.
Não modifica `uboot-base` nem os refs. O patch mantém os avisos do fonte e
o código novo usa GPL-2.0+.

| Arquivo do port | Mudança e motivo |
| --- | --- |
| [board.c](../../port/device/rk-r35s-p0/uboot-sd/board.c) | Adaptador pequeno com seletor fixo de compatibilidade do display e boot device SD. Substitui as políticas automáticas do board legado. Erros ficam no console, sem arquivo FAT ou GPIOs de LEDs não validados |
| [board.h](../../port/device/rk-r35s-p0/uboot-sd/board.h) | Defaults próprios, endereços separados e comandos condicionados ao sucesso das leituras; sem scripts de recovery ou boot.ini arbitrário |
| [config.fragment](../../port/device/rk-r35s-p0/uboot-sd/config.fragment) | ENV_IS_NOWHERE, BOOTDELAY=-1, PANIC_HANG; desliga SPI/RKFLASH, saveenv, RockUSB, OP-TEE client/RPMB, vendor storage, charge display, GO/atalho BROM e testes de fábrica |
| [patch0007](../../port/patches/0007-uboot-r35s-sd-probe.patch) | Makefile deixa de ligar `odroidgoa{,_power,_status,_recovery}.o`. O carregador do DTB de display passa a usar somente a FAT/arquivo Panel0 fixado, sem ADC, SPI ou fallback resource. Falha interrompe por panic |

A compatibilidade RG351MP retornada por `get_rg351_rev` é usada pelo código
de rotação herdado. **Não é autodetecção do console ou aprovação de RG351MP.**
O `boot_devtype_init` do adaptador define somente `mmc/1`: o recurso nativo
que ainda o referencia não pode procurar outra mídia pelo boot-mode register.

Mantém-se a arquitetura nativa de duas árvores do BSP: um DTB mínimo
`odroidgoa` embutido permite a inicialização inicial; a árvore completa de
display Panel0 é carregada separadamente e integrada ao driver model pela
rotina nativa de fixup de phandles. O DTB Linux será outro arquivo.

| Uso | Endereço / limite de leitura |
| --- | --- |
| Entrada do executável U-Boot | `0x00200000`, com relocação nativa posterior |
| DTB de controle/display U-Boot | `0x01e00000`, até 256 KiB, `rk3326-muos-r35s-panel0-uboot.dtb` |
| DTB Linux | `0x01f00000`, até 256 KiB, `rk3326-muos-r35s-panel0.dtb` |
| Linux Image | `0x02000000`, até 64 MiB |

O controle de tamanho do DTB U-Boot confere bytes lidos, `fdt_check_header`
e `fdt_totalsize` antes do scan. Essa separação evita que o carregamento do
DTB Linux sobrescreva diretamente a árvore de controle U-Boot, como poderia
ocorrer ao reutilizar o mesmo endereço. **A auditoria completa dos ranges
de RAM, relocação, sysmem, DRM e reservas ainda precisa ser concluída.**

O monitor não executa o kernel automaticamente. O `bootcmd` compilado,
inspecionado no ELF, contém somente a sequência condicionada de SD→Image→
DTB Linux→`booti`, sem initramfs. Seus bootargs são diagnósticos:

```text
console=ttyFIQ0,115200n8 console=tty0 root=/dev/mmcblk0p2 rootfstype=ext4 rootwait ro init=/bin/sh loglevel=7 consoleblank=0
```

`mmc1` é enumeração U-Boot; `mmcblk0p2` é a escolha provisória Linux do
aparelho observado. A imagem futura precisa conferir esse mapeamento e
preferir identidade de partição fixada no layout. `/bin/sh` em raiz ro não
inicia a UI/S99 da imagem; não se validou o boot do init completo por isso.

## Auditoria do executável

Container do kernel já fixado no lock, Linaro 6.3.1 no commit
`46d00ad5a58edae59b2bc16f4694510b93d51889`, sem instalar dependências no
Bazzite. Epoch vem do commit U-Boot; `.scmversion` evita herdar o Git do
workspace. `LOCALVERSION` identifica a candidata, sem fingir reproduzir o
delta `dirty` instalado. O build solicita somente U-Boot, DTBs e metadados;
não executa `make.sh`, flasher, SPL/TPL ou binários do fornecedor.

O [auditor](../../port/scripts/verify-phase4-uboot-sd.py) passou em:

- ELF64 little-endian, AArch64 ET_EXEC, entrada 0x200000, sem PT_INTERP ou
  linker dinâmico. Isso é firmware bare-metal, não um programa Linux/QEMU user.
- Configuração Kconfig **e** macros efetivas: ambiente nowhere, bootdelay −1,
  panic sem reset automático e ausência dos providers persistentes selecionados.
- Extração do símbolo global `default_environment` do ELF: bootcmd completo,
  bootargs, SD, rotação e endereços. Sem preboot, altbootcmd ou scripts SPI.
  Os dois DTBs também não substituem bootdelay por propriedade `/config`.
- Tabela de comandos e mapa: não liga recovery/power/status antigos nem
  env/mmc; não contém saveenv, rksfc, hwrev, odroidtest, cfgload e outros
  comandos desabilitados. Strings dos caminhos destrutivos identificados
  anteriormente estão ausentes do binário.
- `u-boot.bin` é exatamente nodtb+DTB mínimo; cabe no slot de 1 MiB − 2 KiB
  do empacotador. DTB externo recompilado passou nas 37 propriedades de
  display e providers selecionados, com o hash `b28dd723…4b9551` anterior.

Build final: `probe.yjv58qmi`; executável binário de 857.887 bytes, SHA256
`c2ebd0892a5f4588fd83d894a4cc36a0f0d9d0e1ba0c8fafab47756a31ed251b`.
Contêiner `uboot.img` final:
`b422d77871b78e40143ff57d79411eb1f974ef9bb65dbaa81e268ccabcc53d04`.
Provas negativas adicionais rejeitaram alteração de `devnum` dentro do ELF
e remoção de PANIC_HANG. Com boot-mode register 0, o atalho `rbrom` herdado
escreveria no endereço 0 se acionado; CMD_GO foi desligado para retirar esse
caminho, e TEST_ROCKCHIP foi desligado para excluir `rktest`. A função
genérica `rockchip_get_boot_mode`, que também acessa esse registro, não está
no executável ligado. Isso não é prova sobre todos os comandos interativos.

## Leitura estática inicial da memória

O `Image` BSP fixado tem 13.096.968 bytes no arquivo, `text_offset=0x80000`,
`image_size=0xe40000` e flags 0xa. Aplicando **o código desta revisão**,
`cmd/booti.c:70–92`, o bit 3 faz a rotina partir do endereço de carga, mas
o alinhamento 2 MiB desloca a entrada de 0x02000000 para **0x02080000**.
O fim exclusivo da região de imagem fica em 0x02ec0000. Não confundir o
endereço de leitura com a entrada efetiva do kernel.

Isso não colide com os dois buffers FDT em 0x01e00000/0x01f00000 nem com o
BL32 em 0x08400000. O binário inicial U-Boot e seu BSS terminam abaixo da
stack inicial 0x00400000; o ELF final informa `__bss_end=0x002f7b28`.
Essas relações são cálculos estáticos, não um mapa completo da RAM disponível.

`drivers/video/video-uclass.c:75–99` reserva antecipadamente framebuffer
640×480×4 e pool 32 MiB, mesmo antes de ligar a árvore completa; a posição
vem do topo dinâmico da RAM. `common/board_f.c:465–480` reserva/reloca o DTB
mínimo, e `lib/sysmem.c:694–762` registra U-Boot/heap/stack no LMB.
O heap configurado é 192 MiB e a stack reservada 2 MiB. O valor real de
`gd->ram_top`, bases de video/heap e exclusões de ATF/TEE exige diagnóstico
da candidata; não foi presumido um tamanho físico de RAM para fechá-lo.

**Pendência concreta antes do boot:**
`boot_fdt_add_sysmem_rsv_regions`, `common/image-fdt.c:136–190`, registra
as entradas de reserva e `/reserved-memory`, mas não reserva automaticamente
o buffer que contém o DTB de controle. A nova função carregadora ainda não
registra explicitamente seu próprio intervalo 0x01e00000+256KiB no sysmem.
Completar essa proteção e auditar o percurso de vídeo/realocação antes de
habilitar um boot candidato. O resultado atual fica como monitor de prova
no host, com autoboot desligado e sem aprovação de mídia.

**Limites:** comandos interativos como `mmc` ainda permitem write/erase;
não é um monitor com todas as escritas impossibilitadas. Não se provou todo
o grafo de chamadas ou inicialização elétrica. Não há política de bateria,
charger, LEDs ou shutdown final neste adaptador. Antes de qualquer boot,
revisar também esses pontos, os ranges de memória e o meio de diagnóstico.

Ocorreram duas correções de build: comentário do header incompatível com o
preprocessamento C90 do linker script; e cliente OP-TEE ligado a referências
RPMB após retirar eMMC. Foram corrigidas sem reativar provisionamento. O
helper de boot device ausente com boot-mode register 0 ganhou implementação
SD fixa. O primeiro build aprovado ainda herdava reset no panic; o build
final adiciona PANIC_HANG e repete auditoria/empacotamento.

Avisos preservados: GNU make reclama de peer targets em regras antigas;
`tools/rockchip/boot_merger.c:895` gera `-Wstringop-overflow`. **boot_merger
não foi executado.** Os avisos DTC nos includes herdados permanecem no log.
Não há erro de compilação/link na candidata final aprovada. A receita
tem entradas fixadas, mas não se demonstrou identidade bit a bit entre
builds em diretórios diferentes.

## Empacotamento e proveniência

`tools/Makefile:63–70` compila `mkimage`, `loaderimage` e `trust_merger` de
fontes GPL-2.0+ verificadas em `tools/rkcommon.c`, `rksd.c` e
`tools/rockchip/{loaderimage,trust_merger,crc32_rk}.c`. Foram usados esses
executáveis locais, sem executar os packers precompilados de `tools/rk_tools`.

O [empacotador do port](../../port/scripts/package-phase4-uboot-sd.py) cria
diretório novo e copia os quatro payloads de hashes fixados no lock. Usa:
RKSD/px30 para DDR 333 MHz v1.10, concatenação do miniloader v1.12,
loaderimage em 0x200000 com 4 cópias de 1 MiB, e trust_merger SHA 3/RSA 3 com
duas cópias de 2 MiB. O flag RSA 3 descreve o formato esperado; **não é prova
de assinatura criptográfica, secure boot ou autenticação destes arquivos**.

O [verificador independente](../../port/scripts/verify-phase4-boot-package.py)
inspeciona somente os formatos públicos e bytes, sem executar/desmontar os
payloads. Passaram:

- Cabeçalho RKSD, offsets e alinhamento; DDR e miniloader byte a byte.
- Cabeçalho LOADER, endereço/tamanho, CRC Rockchip, SHA256 e 4 cópias iguais.
- Cabeçalho BL3X, flags 0x33, tabelas, segmentos PT_LOAD do ELF BL31 e BL32,
  endereços, padding, hashes e duas cópias iguais.
- Não sobreposição no layout **provisório** dos setores 64/16384/24576 e
  primeiro filesystem após 32768. Nenhum MBR/imagem de mídia foi produzido.
- Provas negativas rejeitaram CRC e hash de componente corrompidos, mesmo
  com o checksum externo do arquivo deliberadamente atualizado.

| Arquivo local | Bytes | Resultado |
| --- | --- | --- |
| idbloader.img | 145156 | DDR/miniloader selecionados conferidos; reprodução do idbloader instalado não declarada |
| uboot.img | 4194304 | Executável novo do port,4 cópias; difere da referência instalada |
| trust.img | 4194304 | **SHA256 idêntico à referência instalada** |

Trust SHA256:
`3531668a2f08d4f8583ae9e256177f3404e04f9888d6e2a677613c8dfd4da138`.
São dois segmentos BL31 em 0x10000/0xff0e0000 e BL32 em 0x08400000.
Isso relaciona os payloads fixados e a receita fonte aos bytes instalados do
trust, fechando essa proveniência de conteúdo. Não resolve sua licença ou
aprova executar o conjunto no aparelho.

A consulta opcional `mkimage -l idb-ddr.img` falhou com Bus error no host
durante a primeira tentativa de empacotamento. A causa não foi fechada;
essa consulta saiu da receita e não é critério de aprovação. A geração
RKSD passou e seu resultado foi conferido pelo parser independente acima.

## Repetição e próximo checkpoint

Somente host, sem acesso a dispositivo:

```sh
bash port/scripts/build-phase4-uboot-sd.sh prepare
bash port/scripts/build-phase4-uboot-sd.sh build
bash port/scripts/build-phase4-uboot-sd.sh status
# Aguardar running=false e build.exit=0 no diretório apontado por latest-build.
bash port/scripts/audit-phase4-uboot-sd.sh
python3 port/scripts/package-phase4-uboot-sd.py
# Executar o verificador com o caminho indicado por latest-package:
python3 port/scripts/verify-phase4-boot-package.py CAMINHO_DO_PACKAGE
```

Os caminhos/hashes finais estão em `build/phase4/uboot-sd/latest-build`,
`latest-package` dentro desse build e `dist/phase4/uboot-sd-probe/`.
O checkpoint em dist contém prova, executável/DTBs GPL e fontes do delta;
exclui DDR/miniloader/BL31/BL32 e seus contêineres, conservados privados em
build. Seus termos pendentes estão no registro, conforme a decisão do
usuário; o Markdown consolidado será gerado somente ao fim do projeto.

**Próximo menor passo:** auditar ranges de RAM, reservas/DRM, relocação e
continuação do driver model com as duas árvores. Definir como coletar logs
do primeiro monitor/boot — a candidata atual privilegia serial e não abre
um shell acessível pelos botões. Depois fechar layout/FAT e raiz diagnóstica
com identificação de mídia. Fase 5 ainda exige cartão separado identificado
e confirmação da gravação concreta. Rootfs persistente, coldplug, kernel
candidato, energia e frontend em boot próprio continuam não validados.
