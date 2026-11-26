# Release notes template

Copy into the GitHub release text; replace `<version>`.

---

## MustardOS for R36S/R35S <version> (unofficial port)

> **Unofficial port. Not made, approved or supported by the MustardOS
> team.** Ask for help only in this repository's issues, never on the
> MustardOS Discord, forum or GitHub.

Tested on the R35S/R36S **Panel 0** (R36S-V12 board) only.

### ⬇ Download: [MustardOS-R36S-port-<version>.img.xz](https://github.com/laurorual/MustardOS-R36S-port/releases/download/<version>/MustardOS-R36S-port-<version>.img.xz)

This is the only file you need to flash. Its SHA256 is in
`MustardOS-R36S-port-<version>.img.xz.sha256`; every other asset is the
update package or the GPL source.

**Install:** write `MustardOS-R36S-port-<version>.img.xz` to a microSD
card (balenaEtcher, Rufus or Raspberry Pi Imager), put it in slot 1,
power on. Guide: [English](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/install.md) ·
[Português (BR)](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/install.pt-BR.md). Known issues:
[docs/known-issues.md](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/known-issues.md).

**Update from an earlier version:** automatic over Wi-Fi, or copy the
`.p2.img.gz` and `.p2.img.sha256` assets to `MUOS/update` and run
Applications → Task Toolkit → Install Firmware Update.

**What changed:** see [docs/CHANGELOG.md](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/CHANGELOG.md).

**Assets**

| File | What |
|---|---|
| `MustardOS-R36S-port-<version>.img.xz` (+ `.sha256`) | the card image to flash |
| `MustardOS-R36S-port-<version>.p2.img.gz` + `.p2.img.sha256` | the update package (system partition) |
| `MustardOS-R36S-port-*.tar.zst`, `linux-*`, `u-boot-*`, `cores/*`, `buildroot-legal-info.tar.zst`, … + `SHA256SUMS` | the complete corresponding source (GPL) |

**Licences:** the port's code is MIT; every component's licence is in
[docs/LICENSING.md](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/LICENSING.md) and `THIRD-PARTY.txt` in the image.
MustardOS name, themes and assets: CC BY-NC 4.0, used with the MustardOS
team's permission. Some cores are non-commercial: **do not sell this
firmware**. Closed components without published terms (Mali GPU driver,
DraStic, the DraStic hook and layout art) are included as other
community firmwares do, with credit; authors who want a component
removed can open an issue. No games or BIOS files are included.

---

### Português (Brasil)

> **Port não oficial. Não é feito, aprovado nem suportado pela equipe do
> MustardOS.** Peça ajuda somente nas issues deste repositório, nunca no
> Discord, fórum ou GitHub do MustardOS.

**⬇ Baixar a imagem: [MustardOS-R36S-port-<version>.img.xz](https://github.com/laurorual/MustardOS-R36S-port/releases/download/<version>/MustardOS-R36S-port-<version>.img.xz)** (o único
arquivo para gravar no cartão; os outros são o pacote de atualização e o
código-fonte GPL).

Testado somente no R35S/R36S **Panel 0**. Grave o
`MustardOS-R36S-port-<versão>.img.xz` num microSD (balenaEtcher, Rufus ou
Raspberry Pi Imager), coloque no slot 1 e ligue. Guia:
[docs/install.pt-BR.md](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/install.pt-BR.md). Este firmware não pode
ser vendido (licenças não comerciais de alguns cores).
