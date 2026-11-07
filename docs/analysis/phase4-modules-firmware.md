# Fase 4 — módulos e firmware na raiz própria, 25/10/2026

**Concluído no host:** a candidata privada agora contém os 555 módulos do
mesmo build do kernel `4.4.189-muos-r35s-p4`, índices kmod 33 e dois firmwares
Bluetooth identificados. A imagem final passou em auditoria, consulta dos
aliases via QEMU e fsck. **Nenhum módulo candidato foi carregado no dArkOSen;
o kernel candidato continua sem teste de boot.**

## Conjunto fixado

O [lock do payload](../../port/device/rk-r35s-p0/phase4-module-payload.json)
relaciona `Image`, DTB Linux Panel0, configuração e `modules.tar.gz` do
checkpoint `dist/phase4/bsp-probe/`. O
[preparador](../../port/scripts/prepare-phase4-modules.py) confere seus hashes,
extrai uma árvore nova em `build/phase4/modules/payload.*`, inspeciona os
módulos e regenera os índices com o host kmod da própria Buildroot.

| Componente | SHA256 |
| --- | --- |
| Image | `780935823cb8c86e4330c8c8157ebb4005fb5580e68e72c4b0c4e480bab42d2f` |
| DTB Linux próprio | `496bbe3591f8619f059ebc384277ecdd17fd41f956aef40de20afb46b92d5b49` |
| modules.tar.gz | `0b2946be07df09e69736c23a5a3f2cf9ccc66fe12667fd3f1dd11de1eafe9696` |
| kernel.config | `13ece0aefe7bd38eac6b3de4cd4cd9be6f064a0fc04e55fbe47134cba3b5c40e` |

São555 ELF64 little-endian, AArch64, **ET_REL**, sem program headers.
Verificado `.modinfo`, nomes únicos e fechamento das dependências declaradas,
incluindo os módulos builtin. O vermagic completo é:

```text
4.4.189-muos-r35s-p4 SMP mod_unload aarch64
```

`depmod -e -F System.map` não relatou símbolos desconhecidos. O `System.map`
tem hash fixado no lock. O kernel tem `CONFIG_MODVERSIONS` desligado; isso
não permite concluir compatibilidade com outro kernel de mesmo número.
Módulos usam o compilador Linaro do kernel, separado do GCC 13 do userspace.

O aviso preservado é `could not open modules.builtin.modinfo`: esse artefato
não foi gerado pelo build 4.4. Não se fabricou um arquivo vazio para ocultá-lo.
A listagem `modules.builtin` existente entrou na resolução. Coldplug real e
carregamento pelo novo kernel continuam pendentes.

O [verificador do rootfs](../../port/scripts/verify-phase4-rootfs.py) mantém
as regras de program headers/loader para ET_EXEC/ET_DYN. Somente `.ko` na
árvore do release esperado usa a
[auditoria ET_REL separada](../../port/scripts/verify-phase4-modules.py).
Provas negativas rejeitaram arquitetura errada, vermagic alterado e um
executável userspace apresentado como módulo.

## Dongle observado e escolha dos firmwares

Leitura SSH atual: USB **0bda:c820**, Wi-Fi ligado ao módulo `8821cu` e
`hci0` ligado a `btusb`. A presença de `rtk_btusb` em lsmod não prova que
esse seja o driver ligado ao hci0. Evidência completa sem SSID/MAC:
`build/phase4/modules/device-evidence.txt` e checkpoint em `dist/`.

| Função | Evidência no fonte Linux fixado em d8402159c04b1044106b4f27b7ed7c22ed09228f | Decisão |
| --- | --- | --- |
| Wi-Fi 8821cu | `drivers/net/wireless/rtl8821cu/include/autoconf.h:72`: `#define CONFIG_EMBEDDED_FWIMG`; `hal/rtl8821c/rtl8821c_halinit.c:140–150` seleciona `array_mp_8821c_fw_nic` | Usa array embutido no módulo; não copiar outro firmware externo por suposição |
| Bluetooth genérico | `drivers/bluetooth/btrtl.c:127–132`: caso 8821C, `rtl_bt/rtl8821c_fw.bin` e base `rtl_bt/rtl8821c_config`; a construção posterior acrescenta `.bin` | Incluir exatamente esses dois arquivos |
| Bluetooth alternativo | `drivers/bluetooth/rtk_btusb.c:115`: IDc820, nomes `rtl8821c_fw`/`rtl8821c_config`, `MAX_PATCH_SIZE_40K` | Bloquear seu autoload nesta candidata; não renomear o firmware genérico de 54.636bytes para tentar satisfazê-lo |

O overlay instala `etc/modprobe.d/r35s-bluetooth.conf` com
`blacklist rtk_btusb`. A consulta `modprobe -b --show-depends`, com raiz,
release e diretório de configuração explícitos, resolve:

- Interface Wi-Fi → `8821cu.ko`.
- Interface Bluetooth → `btintel.ko`, `btbcm.ko`, `btrtl.ko`, `btusb.ko`;
  exclui `rtk_btusb.ko`.

Essas linhas de saída começam com `insmod`, mas **foram somente impressas**
pelo modo de consulta. A regra empacotada `lib/udev/rules.d/80-drivers.rules:5`
usa `kmod load`; `eudev-3.2.14/src/udev/udev-builtin-kmod.c:51` aplica
`KMOD_PROBE_APPLY_BLACKLIST`. Isso sustenta a política proposta sem equivaler
a um ensaio de coldplug.

## Origem e termos dos dois arquivos externos

Pacote oficial Debian `firmware-realtek_20250410-2_all.deb`, obtido de
[deb.debian.org](https://deb.debian.org/debian/pool/non-free-firmware/f/firmware-nonfree/firmware-realtek_20250410-2_all.deb).
Tamanho2.859.648bytes e SHA256
`925755a9b0891c7dc39bbb73d28ab8f7193d37303b5022e8bc9d458b9b4aaa4e`,
conferidos com o registro de `trixie/non-free-firmware/binary-arm64/Packages.xz`.
O lock permite repetir a obtenção e verificar o pacote sem depender do índice
mutável. A extração usa `dpkg-deb` no container fixado, sem instalar no host.

| Arquivo sob `/lib/firmware/` | Bytes | SHA256 |
| --- | --- | --- |
| `rtl_bt/rtl8821c_fw.bin` | 54636 | `dfe7ef772d078ec09490c02190a32fcd40b3eaf3b040049d8930eb80e6d5743c` |
| `rtl_bt/rtl8821c_config.bin` | 10 | `292717b0610ce920f66b734c299d349ea59a4c4400044078d8fc65625f17e382` |

Os hashes coincidem com os arquivos instalados no console. O copyright
do **pacote exato**, `usr/share/doc/firmware-realtek/copyright:860–863,5967–6004`,
associa `rtl_bt/*` a `binary-redist-Realtek-restrictive`: distribuição binária
sem modificação, preservação dos avisos, restrições e disclaimer. O texto
inteiro acompanha os arquivos em
`/usr/share/licenses/r35s-module-payload/firmware-realtek-copyright`, sem
alterar os binários. Também entram COPYING Linux e o manifesto de fontes.
Esses dois arquivos têm termos identificados; a pendência Mali e a política
de uso privado da candidata permanecem no registro de licenças.

**Limites:** as tags `.modinfo` listam 157 pedidos distintos de firmware, mas
não são inventário completo: o próprio caso 8821C tem pedido construído no
código. Não foram incluídos firmwares de todos os periféricos compilados.
Outros dongles não estão cobertos. A raiz ainda não fornece a integração
completa de Wi-Fi/WPA/DHCP/SSH nem BlueZ. CRDA está habilitado no kernel e o
regdb interno desligado; a configuração regulatória também fica pendente.
Não houve associação Wi-Fi, transmissão Bluetooth ou validação RF na candidata.

## Imagem final e repetição

O [fragmento Buildroot](../../port/device/rk-r35s-p0/phase4-foundation.fragment)
habilita `BR2_PACKAGE_HOST_KMOD` e `BR2_PACKAGE_KMOD_TOOLS`, versão33.
O [instalador](../../port/scripts/install-phase4-foundation.py) ganhou
`--bsp-modules`, exige o lock atual e confere o payload. O modo anterior não
pode omitir silenciosamente módulos já pertencentes ao overlay.

Imagem ext4 ROOTFS de 512 MiB:
SHA256 `ccdb9c0a7d232f8dc628a86ceb911c53247d74dd0e14802e0907459bddf13fc0`.
Tem **284 ELF userspace + 555 módulos = 839 ELF AArch64**, ABI da libc 4.4.0.
Os hashes dos módulos, índices, firmware e avisos foram comparados com a
extração da **imagem finalizada**, não só com `target/`.

Passaram: carregamento/link/GBM/mapper/supervisor via QEMU Cortex-A35,
`modinfo` e resolução dos dois aliases pelo **kmod AArch64** em modo de
consulta, preservação byte a byte dos componentes UI aprovados, WAVs
originais, hotkeys e `e2fsck -fn`. Autostart continua configurado pela
aprovação dos serviços anteriores; esta imagem não foi inicializada.

Para repetir a integração já concluída, somente no host:

```sh
bash port/scripts/build-phase4-foundation.sh reconfigure
bash port/scripts/build-phase4-foundation.sh module-tools
# Aguardar container parado e module-tools.exit=0 antes de continuar.
python3 port/scripts/prepare-phase4-modules.py
python3 port/scripts/install-phase4-foundation.py --validated-runtime --init-services --enable-ui --bsp-modules
bash port/scripts/build-phase4-foundation.sh image
# Aguardar container parado e image.exit=0.
bash port/scripts/audit-phase4-foundation.sh
```

O staging aprovado está em `foundation/staging.YRRiUd`; ponteiro mutável em
`foundation/latest-staging`. `dist/phase4/modules-firmware/` preserva
manifestos, inventário, auditoria, fontes do incremento e avisos, sem Mali,
imagem completa ou tar do runtime. Os artefatos privados ficam em `build/`.

Saúde ao encerrar a coleta SSH: taint 0, cinco contadores Btrfs 0,
ES/ogage/fn ativos e hash do `Image` instalado inalterado. Não houve parada
do launcher, reboot, cópia para a instalação ou escrita de blocos. O próximo
passo é o [bootloader específico](phase4-uboot-panel.md), antes do teste
independente em mídia identificada.
