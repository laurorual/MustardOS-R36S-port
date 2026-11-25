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

- Tested on one **R35S with Panel 0** (device tree model
  "R36S-V12 2023-08-18 Panel 0"). R36S units with the same board and
  panel should work. Other panels, board revisions and clones are not
  supported: the screen may stay black or show garbage.
- Slot 1 (the card slot the system boots from). An optional second card
  in slot 2 can hold ROMs.
- Wi-Fi needs a USB dongle with the Realtek RTL8821CU chip (the R36S has
  no internal Wi-Fi). Bluetooth is not supported.

## Install

Full guide: [docs/install.md](docs/install.md). In short:

1. Download `MustardOS-R36S-port-<version>.img.xz` and its `.sha256` from
   the [releases](https://github.com/laurorual/MustardOS-R36S-port/releases).
2. Write it to a microSD card (8 GB or more) with balenaEtcher, Rufus or
   Raspberry Pi Imager. This erases the card.
3. Put the card in slot 1 and power on. The first boot grows the data
   partition to the whole card.
4. Add games: over Wi-Fi with SFTP (Configuration → Connectivity → Web Services), or on
   a FAT/exFAT card in slot 2 (`ROMS/<system>`). BIOS files go to
   `MUOS/bios`. No games or BIOS files are included.

Updates: Applications → Task Toolkit → "Install Firmware Update", or
automatic with Wi-Fi when a new release is published here.

## What is included

The MustardOS frontend and themes, about 30 libretro cores (NES, SNES,
GB/GBC/GBA, Mega Drive/32X/Sega CD, PlayStation, PC Engine/CD, Atari,
Lynx, Neo Geo Pocket, WonderSwan, MSX, arcade, DOS, ScummVM, N64, DC,
PSP, NDS, Saturn) and standalone emulators for the heavy systems
(Mupen64Plus, PPSSPP, DraStic, Flycast, YabaSanshiro, ScummVM). English,
Português (Brasil) and every MustardOS language. Known issues:
[docs/known-issues.md](docs/known-issues.md); changes:
[docs/CHANGELOG.md](docs/CHANGELOG.md).

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

**Aparelhos:** testado em um **R35S com Panel 0** (modelo "R36S-V12
2023-08-18 Panel 0"); R36S com a mesma placa e tela devem funcionar.
Outras telas, revisões e clones não são suportados. Wi-Fi requer um
adaptador USB com chip Realtek RTL8821CU; sem Bluetooth.

**Instalação** (guia completo: [docs/install.pt-BR.md](docs/install.pt-BR.md)):
baixe `MustardOS-R36S-port-<versão>.img.xz` e o `.sha256` em
[releases](https://github.com/laurorual/MustardOS-R36S-port/releases),
grave num cartão microSD (8 GB ou mais) com balenaEtcher, Rufus ou
Raspberry Pi Imager (o cartão é apagado), coloque no slot 1 e ligue. Os
jogos vão por SFTP pelo Wi-Fi ou num cartão FAT/exFAT no slot 2
(`ROMS/<sistema>`); BIOS em `MUOS/bios`. Nenhum jogo ou BIOS acompanha o
sistema. Atualizações: Aplicativos → Task Toolkit → "Install Firmware
Update", ou automáticas com Wi-Fi.

**Licenças:** código do port em MIT; componentes de terceiros em
[docs/LICENSING.md](docs/LICENSING.md); nome e temas do MustardOS sob
CC BY-NC 4.0, com permissão da equipe do MustardOS. Alguns cores são só
para uso não comercial: **este firmware não pode ser vendido**.
Componentes fechados sem termos publicados (driver Mali, DraStic, hook e
layouts do DraStic) são incluídos como fazem outros firmwares da
comunidade, com créditos; autores que quiserem a remoção podem abrir uma
issue.
