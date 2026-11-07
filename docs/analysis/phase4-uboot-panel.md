# Fase 4 — delta de display U-Boot Panel0, 25/10/2026

**Continuação:** o [executável SD](phase4-uboot-sd.md) agora também foi
compilado/auditado e seus contêineres privados conferidos, sem teste de boot.
As declarações abaixo de executável ainda não construído descrevem o
checkpoint anterior de display. Persistem gates de memória/diagnóstico.

**Novo resultado estático:** o
[DTS U-Boot próprio](../../port/device/rk-r35s-p0/rk3326-muos-r35s-panel0-uboot.dts)
compilou e passou na comparação do contrato de display com o DTB U-Boot
instalado. Não foi compilado um executável U-Boot, empacotado loader/trust
ou executado flasher. Este resultado complementa a
[identificação anterior](phase4-boot-chain.md); não recupera o delta `dirty`
do bootloader instalado.

## Fonte, licença e diferença explícita

Checkout completo em `build/phase4/uboot-base`, fora dos refs, do commit
`5606e804ffe8f9e5427d55c8da04c638f01a9391` de
`christianhaitian/RG351MP-u-boot`. O
[lock](../../port/device/rk-r35s-p0/phase4-uboot-sources.json) fixa revisão,
container e hashes dos quatro payloads nomeados pela receita DDR/miniloader/
BL31/BL32. Isso identifica seus bytes no fonte; ainda não prova que todos
sejam os componentes instalados nem fecha seus termos por arquivo.
O item `boot-chain-payloads` do registro de licenças permanece aberto.

O DTS do port inclui `arch/arm/dts/rg351mp-uboot.dts`, GPL-2.0+,
preservando atribuição Hardkernel. A sequência 370 bytes vem do fonte Linux
fixado `rk3326-r35s-linux.dts`, Copyright 2020 Hardkernel, GPL-2.0+ OR MIT,
e coincide com o DTB U-Boot instalado. Não se copiou um subsistema inteiro
nem se tratou a decompilação binária como fonte com licença presumida.

| Propriedade | Base U-Boot | Delta específico Panel0 |
| --- | --- | --- |
| Model | RG351MP genérico | `R36S-V12 2023-08-18 Panel 0` |
| Init sequence | 928bytes | 370bytes; SHA256 `972f614858caa119329cffdafc07c3a610b92343090ee7acf65e68c21d131a91` |
| Prepare/reset | 2/1ms | 20/150ms |
| Clock | 26,4MHz | 50MHz |
| Hfront/hsync/hback | 119/2/119 | 450/70/450 |
| Vfront/vsync/vback | 13/2/5 | 17/5/13 |
| Pixelclk-active | 0 | 1 |
| PWM período/default | 25000ns/índice200 | 62745ns/índice51, tabela2…102 |

Esses valores são do **DTB U-Boot**, diferentes dos 29 MHz e demais timings
do DTB Linux. Não unificá-los. Ambos continuam sem teste no kernel/bootloader
próprios. O nome `60Hz` do nó não é uma medição de refresh efetivo.

## Verificação e limites

O [build do DTB](../../port/scripts/build-phase4-uboot-panel.sh) só executa
preprocessamento C e `dtc` 1.7.2 no container já fixado. Não chama `make.sh`
upstream ou seus utilitários binários. Repetição no host:

```sh
bash port/scripts/build-phase4-uboot-panel.sh
```

O [verificador](../../port/scripts/verify-phase4-uboot-panel.py) exige o hash
`e65ccee748de35597c3f7f5e3032ed33e8312abba886bd3dba1aa0dbf662d102`
da referência coletada. Compara37 propriedades de painel/backlight,
resolvendo referências por caminho, inclusive resetGPIO3.C0, PWM e supplies.
Também confere propriedades selecionadas dos GPIO/PWM e reguladores LDO7/8.
As provas negativas de clock e init sequence alterados foram rejeitadas.

SHA256 do DTB produzido:
`b28dd7236b407476c3dac4e0edae69ed9fab6897abd03bb8e8e8fe86fa4b9551`.
`build/phase4/uboot-panel/panel-audit.json` e
`dist/phase4/uboot-panel/` preservam a prova. O log conserva os avisos DTC
nos includes legados, incluindo endereços duplicados de crypto/rng e cif,
unit-address e graph. Não se declarou equivalência da placa inteira,
correção de todos os avisos, estabilidade elétrica ou boot aprovado.

## Contratos encontrados no fonte completo

- `cmd/hwrev.c:21–43` seleciona `dtb_uboot` pelo ADC da revisão RG351;
  o fallback é RG351P. **Fato:** esse código não identifica variantes de
  painel R35S/R36S. Ainda falta fixar explicitamente o par de DTBs do alvo.
- `arch/arm/mach-rockchip/board.c:347–408`, `init_kernel_dtb`, carrega o
  DTB de U-Boot pela FAT antes de reconstruir a árvore live e fazer scan DM.
  Tenta também SPI/resource quando a FAT falha. O nome da função não torna
  esse arquivo o DTB que o `booti` entregará ao Linux.
- `board/rockchip/odroidgoa/odroidgoa.c:185–243` chama rotinas de Wi-Fi GPIO,
  SFC, power/recovery, charge display, logo/autotest e inspeção de SD/ES.
  A presença do launcher é usada para mensagem; ausência não demonstra
  bloqueio obrigatório do boot. Não transportar essas políticas sem revisão.
- **Escritas automáticas a retirar antes de qualquer boot candidato:**
  `odroidgoa.c:216–220` chama recovery quando
  `odroidgoa_recovery.c:16–40` encontra `spi_recovery.img` e seu md5 na FAT.
  `odroidgoa_recovery.c:43–122` escreve SPI com `rksfc write` e, sem flag
  manufacture, executa `mmc erase 0x1 0x7FFF`. O checksum é comparado
  depois da escrita SPI. Essa é evidência do fonte candidato, **não prova
  de que o console atual tenha SPI nem de que seu delta dirty execute esse
  mesmo caminho**. Nenhuma dessas rotinas foi executada nesta investigação.
- `include/configs/odroidgoa.h:16–29,71–88` ainda contém ambiente persistente,
  comando SPI e defaults Debian/mmc1; `CONFIG_CMD_SAVEENV` está habilitado
  no defconfig. A candidata de teste deve remover os caminhos de escrita
  automática, evitar carregar ambiente desconhecido e definir bootargs/
  arquivos do port. Não usar `saveenv` no dispositivo para contornar isso.

## Próximo menor passo executável

**No host:** criar delta/config de U-Boot exclusivo para boot SD deste Panel0,
sem recovery SPI/erase automático, sem depender de ambiente salvo ou ADC para
escolher painel; revisar GPIO/power e fallback. Compilar primeiro só U-Boot e
auditar DTB, mapa, comandos/defaults e tamanhos. Depois empacotar DDR/trust com
payloads fixados e conferir sua estrutura. Isso ainda não escreve mídia.

Só depois preparar imagem de teste com layout/boot.ini próprios e primeiro
boot de diagnóstico. Identificar cartão separado e confirmar escrita antes
da Fase 5; retirar/preservar o dArkOSen. Planejar coleta de logs e recuperação
sem depender da UI ou Wi-Fi, que ainda não estão aprovados no boot novo.
Continuam pendentes shutdown/energia/bateria, conteúdo e o som final da ajuda.
