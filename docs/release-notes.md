# Release notes template

Copy into the GitHub release text; replace `<version>`. One line per paragraph (no hard wraps): the GitHub page wraps it. Keep the download links at the top. For a release candidate, replace the "Update" paragraph with: "**Release candidate** (pre-release): flash the card image; updates over Wi-Fi only offer normal releases."

---

## MustardOS for R36S/R35S <version> (unofficial port)

> **Unofficial port. Not made, approved or supported by the MustardOS
> team.** Ask for help only in this repository's issues, never on the
> MustardOS Discord, forum or GitHub.

Tested on the R35S/R36S **Panel 0** (R36S-V12 board) only.

### ⬇ New install: [MustardOS-R36S-port-<version>.img.xz](https://github.com/laurorual/MustardOS-R36S-port/releases/download/<version>/MustardOS-R36S-port-<version>.img.xz)

### ⬇ Update: [MustardOS-R36S-port-<version>.p2.img.gz](https://github.com/laurorual/MustardOS-R36S-port/releases/download/<version>/MustardOS-R36S-port-<version>.p2.img.gz) + [.p2.img.sha256](https://github.com/laurorual/MustardOS-R36S-port/releases/download/<version>/MustardOS-R36S-port-<version>.p2.img.sha256)

**Install:** write `MustardOS-R36S-port-<version>.img.xz` to a microSD card (balenaEtcher, Rufus or Raspberry Pi Imager), put it in slot 1, power on. Its SHA256 is in `MustardOS-R36S-port-<version>.img.xz.sha256`. Guide: [English](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/install.md) · [Português (BR)](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/install.pt-BR.md).
Known issues: [docs/known-issues.md](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/known-issues.md).

**Update** (games, saves and settings stay): with Wi-Fi on, the device downloads it by itself and installs it at the next start. Without Wi-Fi, copy both update files to `MUOS/update` on the card and run Applications → Task Toolkit → Install Firmware Update. The update shows its progress and restarts the device twice (about 10 minutes): keep it on, on the charger or with at least 30 % battery.

**What changed:** see [docs/CHANGELOG.md](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/CHANGELOG.md).

**Assets**

| File | What |
|---|---|
| `MustardOS-R36S-port-<version>.img.xz` (+ `.sha256`) | the card image to flash |
| `MustardOS-R36S-port-<version>.p2.img.gz` + `.p2.img.sha256` | the update package (system partition, kernel included) |
| `MustardOS-R36S-port-<version>-source-1.zip`, `-source-2.zip` (+ `.sha256`) | the complete corresponding source (GPL): unzip both into one folder, `SHA256SUMS` inside |

**Licences:** the port's code is MIT; every component's licence is in [docs/LICENSING.md](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/LICENSING.md) and `THIRD-PARTY.txt` in the image.
MustardOS name, themes and assets: CC BY-NC 4.0, used with the MustardOS team's permission. Some cores are non-commercial: **do not sell this firmware**. Closed components without published terms (Mali GPU driver, DraStic, the DraStic hook and layout art) are included as other community firmwares do, with credit; authors who want a component removed can open an issue. No games or BIOS files are included.

---

### Português (Brasil)

> **Port não oficial. Não é feito, aprovado nem suportado pela equipe do
> MustardOS.** Peça ajuda somente nas issues deste repositório, nunca no
> Discord, fórum ou GitHub do MustardOS.

**⬇ Instalação nova: [MustardOS-R36S-port-<version>.img.xz](https://github.com/laurorual/MustardOS-R36S-port/releases/download/<version>/MustardOS-R36S-port-<version>.img.xz)** (o arquivo para gravar no cartão).

**⬇ Atualização: [MustardOS-R36S-port-<version>.p2.img.gz](https://github.com/laurorual/MustardOS-R36S-port/releases/download/<version>/MustardOS-R36S-port-<version>.p2.img.gz) + [.p2.img.sha256](https://github.com/laurorual/MustardOS-R36S-port/releases/download/<version>/MustardOS-R36S-port-<version>.p2.img.sha256)** (jogos, saves e configurações ficam).

Testado somente no R35S/R36S **Panel 0**. Grave o `MustardOS-R36S-port-<version>.img.xz` num microSD (balenaEtcher, Rufus ou Raspberry Pi Imager), coloque no slot 1 e ligue. Guia: [docs/install.pt-BR.md](https://github.com/laurorual/MustardOS-R36S-port/blob/<version>/docs/install.pt-BR.md).
Para atualizar: com Wi-Fi, o aparelho baixa sozinho e instala no próximo início; sem Wi-Fi, copie os dois arquivos de atualização para `MUOS/update` no cartão e rode Aplicativos → Ferramentas de sistema → Install Firmware Update. A atualização mostra o progresso e reinicia o aparelho duas vezes (cerca de 10 minutos): deixe ligado, no carregador ou com pelo menos 30 % de bateria.
Este firmware não pode ser vendido (licenças não comerciais de alguns cores).
