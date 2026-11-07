# Fase 4 — identificação da região de boot instalada

**Executável posterior:** o [monitor SD próprio](phase4-uboot-sd.md)
compilou e foi auditado; trust foi reproduzido a partir dos payloads
fixados e ferramentas compiladas do fonte. Nenhum boot ou escrita de mídia.
O delta dirty instalado continua desconhecido; a prova é da candidata do port.

**Continuação de 25/10:** o [delta Panel0](phase4-uboot-panel.md) agora tem
DTS próprio compilado e comparação estática de display aprovada. O checkout
completo fixou os quatro payloads de receita e revelou caminhos automáticos
de SPI/erase a retirar da candidata. Ainda não há executável U-Boot próprio
ou teste de boot; as comparações históricas abaixo permanecem válidas.

Leitura em 24/10/2026, enquanto a candidata gráfica compilava no host.
**Não houve escrita de setores, execução de flasher, reboot ou teste de outro
bootloader.** O [leitor](../../port/scripts/read-phase4-boot-prefix.py) abriu
`/dev/mmcblk0` com `O_RDONLY` e coletou somente os primeiros 16 MiB, após
verificar modelo Panel 0, raiz em mmcblk0p2, taint e início de p1. O payload
binário ficou em `build/phase4/boot-chain/`, para análise local.

## Correspondência com dArkOSen

Em `refs/darkosen`, commit `1501b7195e0ab0b51614112de84147d914080b28`,
`UBOOT/flash_uboot.sh` declara os seguintes setores de 512 bytes. O script
foi **lido**, nunca executado. Sua sequência desmonta partições, escreve os
três componentes e reinicia; não é ferramenta de inspeção.

| Componente de referência | Setor / offset | Tamanho da referência | Comparação com a janela instalada do mesmo tamanho |
| --- | --- | --- | --- |
| idbloader.img | 64 / 32.768 bytes | 145.154 bytes | Diferente: 126.784 bytes divergem |
| uboot.img | 16.384 / 8 MiB | 4.194.288 bytes | Diferente: 3.532.551 bytes divergem |
| trust.img | 24.576 / 12 MiB | 4.194.304 bytes | **Idêntico** |

SHA256 do trust observado e da referência:
`3531668a2f08d4f8583ae9e256177f3404e04f9888d6e2a677613c8dfd4da138`.
Hashes completos das outras janelas, blobs Git e offsets estão em
`build/phase4/boot-chain/comparison.json`. Essas janelas não determinam
automaticamente o comprimento real dos componentes instalados divergentes.
O hash do prefixo inteiro inclui MBR e espaço reservado; não é hash de U-Boot.

Os banners encontrados **tanto na referência quanto no cartão** foram:

```text
DDR Version 1.10 20181114
U-Boot 2017.09-g5606e804ff-dirty (Jul 17 2026 - 00:57:49 -0600)
```

Isso demonstra por que nome, banner e data não bastam: os bytes são diferentes
apesar dessas strings iguais. `dirty` registra alterações locais, sem informar
quais. Não há evidência para atribuir toda a diferença ao ajuste de logo.

## Fonte candidata localizada

`UBOOT/DOCUMENTATION.md` do dArkOSen aponta para
`christianhaitian/RG351MP-u-boot`, branch `odroidgoA-v2017.09`, e documenta
ajustes no tamanho/endereço do buffer de logo. Os aparelhos listados como
verificados nesse documento não são este Panel 0.

O prefixo do banner foi resolvido no repositório indicado para o commit
[`5606e804ffe8f9e5427d55c8da04c638f01a9391`](https://github.com/christianhaitian/RG351MP-u-boot/commit/5606e804ffe8f9e5427d55c8da04c638f01a9391),
cuja mensagem trata de DTS para a10mini/G350. A identidade do commit base foi
confirmada; **o delta dirty instalado não foi recuperado**. Não se tomou o HEAD
atual da branch como fonte exata do cartão.

Arquivos dessa revisão foram consultados/guardados em `build/`, sem modificar
refs ou compilar/executar seus scripts:

| Arquivo | Evidência e consequência |
| --- | --- |
| [`Licenses/README`](https://github.com/christianhaitian/RG351MP-u-boot/blob/5606e804ffe8f9e5427d55c8da04c638f01a9391/Licenses/README) | Declara GPLv2 e condições por arquivo; não basta para atribuir licença aos firmwares binários agregados |
| [`configs/odroidgoa_defconfig`](https://github.com/christianhaitian/RG351MP-u-boot/blob/5606e804ffe8f9e5427d55c8da04c638f01a9391/configs/odroidgoa_defconfig) | RK3326, SD_BOOT, target/default DTS odroidgoa, U-Boot no setor 0x4000 |
| [`include/configs/odroidgoa.h`](https://github.com/christianhaitian/RG351MP-u-boot/blob/5606e804ffe8f9e5427d55c8da04c638f01a9391/include/configs/odroidgoa.h) | Sobrescreve tamanho/offset do ambiente e bootcommand; usa mmc 1 no U-Boot, cfgload, Image e dtb_name |
| [`make.sh`](https://github.com/christianhaitian/RG351MP-u-boot/blob/5606e804ffe8f9e5427d55c8da04c638f01a9391/make.sh) | Usa Linaro 6.3.1 e tools/rk_tools no alvo; empacota DDR 333MHz v1.10 + miniloader v1.12 |
| [`tools/rk_tools/RKTRUST/RK3326TRUST.ini`](https://github.com/christianhaitian/RG351MP-u-boot/blob/5606e804ffe8f9e5427d55c8da04c638f01a9391/tools/rk_tools/RKTRUST/RK3326TRUST.ini) | Declara BL31 v1.14 em 0x10000 e BL32 v1.10 em 0x08400000 |
| [`cmd/cfgload.c`](https://github.com/christianhaitian/RG351MP-u-boot/blob/5606e804ffe8f9e5427d55c8da04c638f01a9391/cmd/cfgload.c), [`cmd/source.c`](https://github.com/christianhaitian/RG351MP-u-boot/blob/5606e804ffe8f9e5427d55c8da04c638f01a9391/cmd/source.c) | Procura boot.ini/boot.scr em mmc 1 e executa via source; aceita a assinatura textual do board no caminho ODROID |

Os nomes e versões da receita são fatos do fonte candidato, **não identificação
completa do DDR/miniloader/BL31/BL32 instalados**. Ainda falta relacionar cada
payload do trust e do idbloader aos arquivos e licenças efetivos. A igualdade
do trust com o dArkOSen fecha uma comparação de bytes, não toda sua proveniência.

Também há uma armadilha concreta de configuração: o defconfig anuncia ENV
offset `0x3f8000`, mas o header do board com SD_BOOT redefine-o para 1 MiB.
A checagem de CRC do ambiente de 32 KiB nos dois offsets não encontrou um
ambiente válido no prefixo coletado. **Hipótese:** o aparelho usa defaults
compilados; o layout ou delta dirty podem ser outros. Não foi usado `saveenv`.
O header contém comandos de recuperação SPI; não foram acionados e não devem
entrar implicitamente em um ensaio de boot do port.

O número mmc 1 no U-Boot e mmcblk0 no Linux são de espaços de enumeração
diferentes. Não substituir um pelo outro por coincidência numérica.
O `boot.ini` Panel 0 começa com `odroidgoa-uboot-config`, compatível com esse
caminho de source; não é INI convencional nem prova de suporte extlinux.

O DTS [`arch/arm/dts/rg351mp-uboot.dts`](https://github.com/christianhaitian/RG351MP-u-boot/blob/5606e804ffe8f9e5427d55c8da04c638f01a9391/arch/arm/dts/rg351mp-uboot.dts)
também foi localizado, com licença GPL-2.0+. **Ele não descreve o Panel 0
instalado:** seu array de inicialização tem 928 bytes, contra 370 na referência,
e usa 26,4 MHz/hsync 2, contra 50 MHz/hsync 70 no DTB U-Boot coletado.
O nome de arquivo/modelo não torna esses payloads intercambiáveis. A comparação
está em `panel-source-comparison.json`; não compilou nem aprovou esse DTS.
Será necessário um delta próprio e comparação estática específica do DTB de
U-Boot, além daquela já realizada para o DTB Linux do port.

## Layout observado, sem proposta de alteração

O MBR coletado tem assinatura 0x55aa e três entradas:

| Partição | Tipo MBR | Início (setores) | Comprimento (setores) |
| --- | --- | --- | --- |
| 1 | 0x0c | 32.768 | 204.800 |
| 2 | 0x83 | 237.568 | 20.955.977 |
| 3 | 0x07 | 21.193.545 | 41.140.407 |

p1 começa em 16 MiB e ocupa 100 MiB. Os tipos MBR não provam por si os
filesystems; FAT/Btrfs foram identificados por mounts nos ensaios anteriores.
Esse é o layout atual, não o layout aprovado da imagem muOS. Não reutilizar
o prefixo inteiro como molde de uma imagem: ele contém partições e binários
ainda sem proveniência completa.

## Estado ao encerrar e próximo passo

Após a leitura: taint 0, cinco contadores Btrfs zerados, dmesg sem os
marcadores antigos de erro e ES/ogage/fn-menu-watcher ativos. A conexão SSH
foi fechada. Nenhum artefato de boot foi instalado no console ou incluído em
release; o prefixo bruto não foi levado a `dist/`.

O próximo passo local é fechar fontes/licenças dos payloads nomeados e obter
uma compilação própria rastreável de U-Boot, com delta Panel 0 explícito.
Reprodução exata do binário instalado e alternativa própria são caminhos
distintos: uma candidata própria exige validação de boot e painel, mesmo
se seu fonte for conhecido. O DTB de U-Boot separado e o caminho cfgload/
boot.ini continuam sendo contratos a verificar antes da imagem da Fase 5.
