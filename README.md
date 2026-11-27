# MustardOS for R36S/R35S (unofficial port)

A native AArch64 port of [MustardOS](https://muos.dev) (muOS) to the
RK3326-based R36S and R35S handhelds: a complete card image that boots
straight to the MustardOS menu.

> **Unofficial port. Not made, approved or supported by the MustardOS
> team.** The R36S/R35S is not on MustardOS's device list. Ask for help
> only here, in this repository's
> [issues](https://github.com/laurorual/MustardOS-R36S-port/issues),
> never on the MustardOS Discord, forum or GitHub.

*Português (Brasil): veja [abaixo](#português-brasil).*

## Supported hardware

**Tested:** one screen and one Wi-Fi dongle, the ones on the port's own
test device:

- **R35S with Panel 0** (device tree model "R36S-V12 2023-08-18 Panel 0",
  the default). R36S units with the same board and panel work the same.
- Wi-Fi: a USB dongle with the **Realtek RTL8821CU** chip (the R36S has no
  internal Wi-Fi). Since v1.1 also a TP-Link dongle with the **Realtek
  RTL8822BU** (USB ID 2357:0115, 5 GHz at 867 Mb/s). No Bluetooth.
- Slot 1 (the card slot the system boots from). An optional second card
  in slot 2 can hold ROMs.

**Experimental since v1.1 (untested by the port; feedback welcome):**

- **Other R36S models** with the same 640x480 screen and buttons, from
  dArkOSen's device trees: HL-R36H-V20 2024-05-18, HL-R36H-V21 2024-11-18,
  HL-R46H-V22 2026-03-12, R36S-V12 2023-08-18 Panel 4, R36S-V21 2024-12-18
  2503, R36S-V21 2024-12-18 2529, R36S-V21 2024-12-18 2537, R36S-V21
  2024-12-18 2544, R36S-V21 2024-12-18 2547, R36S-V21 2024-12-18 2550,
  R36S-V21 2024-12-18 2551, R36S-V21 2024-12-18 2552, R36S-V21 2024-12-18
  2604, R36S-V22 2024-12-18 2534, R36S-V22 2024-12-18 2535, R36S-V22
  2024-12-18 2545, R36S-V22 2024-12-18 2548, R36S-V22 2024-12-18, R36S-V30
  2025-18-11 2603, R36S-Y02 2024-12-18, R36XX-V21 2024-12-18, RK3326-D3.

- **Other USB Wi-Fi dongles** with these chips (the drivers come with the
  system): Realtek RTL8188EU/ETV, RTL8188FTV, RTL8188CUS/RTL8192CU,
  RTL8723BU, RTL8811AU/RTL8812AU/RTL8821AU, RTL8812BU/RTL8822BU, RTL8188SU/
  RTL8191SU/RTL8192SU, RTL8723AU, RTL8187; MediaTek MT7601U; Ralink
  RT2870/RT3070/RT5370 and RT2571W/RT73.

Choose your DTB on a PC: open the card's boot partition and run
`select-model.bat` (Windows), `select-model.command` (macOS) or, on
Linux, open a terminal there and type `sh select-model.sh`.
How to change DTB manually: create `model.txt` there with the id
of your model (the first word of its line in `models.txt`).

Then start the console: it restarts once by itself to apply it. If the screen then stays black or wrong, run the
selector again and pick another model or the default (a start that
freezes before the menu goes back to the previous model by itself: hold
Power to turn it off, then on again).

Not working yet: the G80C/G80CA and other "clone" boards, the Y3506 ("soysauce") boards, the R50S and the 720/1024
screens.

The port can't test these on real hardware, so **any feedback is
welcome**: open an [issue](https://github.com/laurorual/MustardOS-R36S-port/issues)
with your model or dongle (its chip or USB ID) and whether it worked.

## Install

Full guide: [docs/install.md](docs/install.md). In short:

1. Download `MustardOS-R36S-port-<version>.img.xz` and its `.sha256` from
   the [releases](https://github.com/laurorual/MustardOS-R36S-port/releases).
2. Write it to a microSD card (8 GB or more) with balenaEtcher, Rufus or
   Raspberry Pi Imager. This erases the card.
3. Put the card in slot 1 and power on. MustardOS's first-boot setup
   opens (date and time, language, profiles, input tester); its
   **Install** asks how to format the card's storage:
   - **exFAT** (recommended): Windows, macOS and Linux read and write it,
     so games can be copied straight to the card's `ROMS` folders.
   - **FAT32**: every computer reads it, but no file can be larger than
     4 GB.
   - **EXT4**: copes best with a sudden power loss, but Windows cannot
     read it without extra software.

   > **exFAT and FAT32 and power loss:** the settings, saves and the
   > firmware update area live on that same storage. These filesystems
   > have no journal: if the battery dies or the console is switched off
   > while it writes (saving a game, changing a setting, installing an
   > update), files can be damaged, and at worst the card needs to be
   > flashed again. Shut down from the menu, keep the battery charged, and
   > back up your saves. Choose EXT4 if you copy games over Wi-Fi anyway.
4. Add games: on a PC (exFAT/FAT32: the card's storage drive), over Wi-Fi
   with SFTP (Configuration → Connectivity → Web Services), or on a
   FAT/exFAT card in slot 2 (`ROMS/<system>`). BIOS files go to
   `MUOS/bios`. No games or BIOS files are included.

Updates: Applications → Task Toolkit → "Check for Online Update" (Wi-Fi:
shows the new version and asks before downloading and installing), or
"Install Firmware Update" for the `.p2.img.gz` + `.p2.img.sha256` of a
release copied to `MUOS/update`. Nothing is downloaded without asking.

## What is included

The MustardOS frontend and themes, about 30 libretro cores (NES, SNES,
GB/GBC/GBA, Mega Drive/32X/Sega CD, PlayStation, PC Engine/CD, Atari,
Lynx, Neo Geo Pocket, WonderSwan, MSX, arcade, DOS, ScummVM, N64, DC,
PSP, NDS, Saturn) and standalone emulators for the heavy systems
(Mupen64Plus, PPSSPP, DraStic, Flycast, YabaSanshiro, ScummVM). English,
Português (Brasil) and every MustardOS language. Known issues:
[docs/known-issues.md](docs/known-issues.md); changes:
[docs/CHANGELOG.md](docs/CHANGELOG.md).

**PortMaster (since v1.1.1):** Applications → PortMaster downloads and
plays PC game ports made for Linux handhelds. Its first start installs
PortMaster from its official release (Wi-Fi, about 25 MB; offline: copy
`muos.portmaster.zip` from
[PortMaster's releases](https://github.com/PortsMaster/PortMaster-GUI/releases)
to `MUOS/update` first). Installed ports appear in the **Ports** system;
Fn+Start quits a port. Ports for 32-bit (armhf) systems only do not run.
PortMaster is not part of this firmware: it, its runtimes and its ports
come from the PortMaster project and their authors.

**PICO-8 (since v1.1.1):** carts (`.p8`, `.p8.png`) in `ROMS/PICO-8`
play with the free Picante8 core (FAKE-08 is the other choice, in the
content options). If you own the official PICO-8, copy its Raspberry Pi
download (`pico-8_*_raspi.zip`, or `pico8_64` + `pico8.dat` from it) to
`MUOS/bios/pico8` and restart: choose the core "PICO-8 - Standalone" or
"PICO-8 - Pixel-Perfect - Standalone" for the folder or a cart, and
Applications gets **Splore** (the Lexaloffle BBS, Wi-Fi). The official PICO-8 is not included.

## Licences

- The port's own code: MIT ([LICENSE](LICENSE)). Its patches to GPL code
  follow that code's licence.
- Every third-party component, its licence and state:
  [docs/LICENSING.md](docs/LICENSING.md) (also `THIRD-PARTY.txt` in the
  image). The complete corresponding source of each release is attached
  to the release as a source bundle.
- MustardOS name, themes and assets: © the MustardOS project and the
  theme authors, CC BY-NC 4.0 (https://muos.dev/press), included with the
  MustardOS team's permission.
- Some cores are licensed for non-commercial use only: **this firmware
  must not be sold** or bundled with a commercial product.
- Closed components without published terms (the Mali GPU driver,
  DraStic, the DraStic hook and layout art) are included as other
  community firmwares do, with credit to their authors. If you are an
  author and want your work removed, open an issue: it will be removed in
  the next release.

See [NOTICE](NOTICE).

## Building

The build runs in rootless containers (Buildroot 2025.02 and the pinned
toolchains); see [docs/procedures.md](docs/procedures.md) and
[docs/roadmap.md](docs/roadmap.md). Hardware notes:
[docs/hardware-findings.md](docs/hardware-findings.md).

---

## Português (Brasil)

Um port nativo AArch64 do [MustardOS](https://muos.dev) (muOS) para os
portáteis R36S e R35S (RK3326): uma imagem completa de cartão que inicia
direto no menu do MustardOS.

> **Port não oficial. Não é feito, aprovado nem suportado pela equipe do
> MustardOS.** O R36S/R35S não está na lista de aparelhos do MustardOS.
> Peça ajuda somente aqui, nas
> [issues](https://github.com/laurorual/MustardOS-R36S-port/issues) deste
> repositório, nunca no Discord, fórum ou GitHub do MustardOS.

**Aparelhos testados:** uma tela e um adaptador Wi-Fi, os do aparelho de
testes do port: **R35S com Panel 0** (modelo "R36S-V12 2023-08-18 Panel
0", o padrão; R36S com a mesma placa e tela funcionam igual) e adaptador
USB com chip **Realtek RTL8821CU** (desde a v1.1 também um TP-Link com
**Realtek RTL8822BU**, USB ID 2357:0115, 5 GHz a 867 Mb/s); sem
Bluetooth.

**Experimental desde a v1.1 (não testado pelo port; retorno bem-vindo):**
outros modelos do R36S com a mesma tela 640x480 e botões, dos device
trees do dArkOSen (lista acima, em inglês).

Escolha o seu DTB num PC: abra a partição de boot do cartão e rode `select-model.bat` (Windows),
`select-model.command` (macOS) ou, no Linux, abra um terminal nela e
digite `sh select-model.sh`.
Como mudar o DTB manualmente: crie nela um `model.txt` com o id do seu modelo (a primeira
palavra da linha dele em `models.txt`).

Depois ligue o console, que reinicia uma vez sozinho para aplicar. Se a tela ficar
preta ou errada, rode o seletor de novo e escolha outro modelo ou o
padrão (um início que trava antes do menu volta sozinho ao modelo
anterior: segure Power para desligar e ligue de novo).

Ainda não funciona: placas "clone" G80C/G80CA e
outras, placas Y3506 ("soysauce"), R50S e telas 720/1024. Também outros
adaptadores Wi-Fi USB com os chips da lista acima (Realtek RTL8188EU/FTV,
RTL8192CU, RTL8723BU, RTL8812AU, RTL8822BU e outros; MediaTek MT7601U;
Ralink RT5370 e outros). O port não tem como testá-los em hardware real,
então **qualquer retorno é bem-vindo**: abra uma
[issue](https://github.com/laurorual/MustardOS-R36S-port/issues) com o
seu modelo ou adaptador (o chip ou o ID USB) e se funcionou.

**Instalação** (guia completo: [docs/install.pt-BR.md](docs/install.pt-BR.md)):
baixe `MustardOS-R36S-port-<versão>.img.xz` e o `.sha256` em
[releases](https://github.com/laurorual/MustardOS-R36S-port/releases),
grave num cartão microSD (8 GB ou mais) com balenaEtcher, Rufus ou
Raspberry Pi Imager (o cartão é apagado), coloque no slot 1 e ligue. Abre
a configuração inicial do MustardOS (data e hora, idioma, perfis, teste
de botões), e o **Instalar** pergunta como
formatar o armazenamento do cartão: **exFAT** (recomendado: Windows, macOS
e Linux leem e gravam, os jogos vão direto para as pastas `ROMS`),
**FAT32** (todo computador lê, mas nenhum arquivo passa de 4 GB) ou
**EXT4** (aguenta melhor uma queda de energia, mas o Windows não lê sem
programas extras).

> **exFAT, FAT32 e queda de energia:** configurações, saves e a área de
> atualização do sistema ficam nesse mesmo armazenamento. Esses sistemas
> de arquivos não têm journal: se a bateria acabar ou o console for
> desligado durante uma gravação (salvar o jogo, mudar uma configuração,
> instalar uma atualização), arquivos podem se corromper e, no pior caso,
> o cartão precisa ser gravado de novo. Desligue pelo menu, mantenha a
> bateria carregada e faça cópia dos saves. Escolha EXT4 se for copiar os
> jogos pelo Wi-Fi de qualquer jeito.

Os
jogos vão direto no PC (exFAT/FAT32: a unidade de armazenamento do
cartão), por SFTP pelo Wi-Fi ou num cartão FAT/exFAT no slot 2
(`ROMS/<sistema>`); BIOS em `MUOS/bios`. Nenhum jogo ou BIOS acompanha o
sistema. Atualizações: Aplicativos → Ferramentas de sistema → "Instalar
atualização do sistema" (arquivos `.p2.img.gz` + `.p2.img.sha256` de um
release copiados para `MUOS/update`) ou "Buscar atualização online" (com
Wi-Fi: mostra a nova versão e pergunta antes de baixar e instalar).

**PortMaster (desde a v1.1.1):** Aplicativos → PortMaster baixa e roda
ports de jogos de PC feitos para portáteis Linux. A primeira abertura
instala o PortMaster a partir do release oficial (Wi-Fi, cerca de
25 MB; sem Wi-Fi: copie antes o `muos.portmaster.zip` dos
[releases do PortMaster](https://github.com/PortsMaster/PortMaster-GUI/releases)
para `MUOS/update`). Os ports instalados aparecem no sistema **Ports**;
Fn+Start fecha um port. Ports só para sistemas 32 bits (armhf) não
rodam. O PortMaster não faz parte deste firmware: ele, as runtimes e os
ports vêm do projeto PortMaster e dos seus autores.

**PICO-8 (desde a v1.1.1):** cartuchos (`.p8`, `.p8.png`) em
`ROMS/PICO-8` rodam com o core livre Picante8 (o FAKE-08 é a outra
opção, nas opções de conteúdo). Se você tem o PICO-8 oficial, copie o
download para Raspberry Pi (`pico-8_*_raspi.zip`, ou o `pico8_64` +
`pico8.dat` dele) para `MUOS/bios/pico8` e reinicie: escolha o core
"PICO-8 - Standalone" ou "PICO-8 - Pixel-Perfect - Standalone" para a
pasta ou um cartucho, e Aplicativos ganha o **Splore** (o BBS da
Lexaloffle, Wi-Fi). O PICO-8 oficial não acompanha
o sistema.

**Licenças:** código do port em MIT; componentes de terceiros em
[docs/LICENSING.md](docs/LICENSING.md); nome e temas do MustardOS sob
CC BY-NC 4.0, com permissão da equipe do MustardOS. Alguns cores são só
para uso não comercial: **este firmware não pode ser vendido**.
Componentes fechados sem termos publicados (driver Mali, DraStic, hook e
layouts do DraStic) são incluídos como fazem outros firmwares da
comunidade, com créditos; autores que quiserem a remoção podem abrir uma
issue.
