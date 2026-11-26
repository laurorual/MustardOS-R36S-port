# Install guide

MustardOS for R36S/R35S is an **unofficial port**: the MustardOS team
does not support it. Questions and bug reports go to
https://github.com/laurorual/MustardOS-R36S-port/issues only.

Português (Brasil): [install.pt-BR.md](install.pt-BR.md).

## What you need

- An R36S or R35S with the **Panel 0** screen (board R36S V12, device tree
  "R36S-V12 2023-08-18 Panel 0"). That is the only tested unit. Other
  panels and clones may show a black or garbled screen: nothing breaks,
  just put your old card back.
- A microSD card of 8 GB or more (a good brand; the card in slot 1 holds
  the system and your saves).
- A PC with a card reader and balenaEtcher, Rufus or Raspberry Pi Imager.
- Optional: a USB Wi-Fi adapter with the **Realtek RTL8821CU** chip (for
  SFTP, time sync and updates); a second microSD (FAT32 or exFAT) for
  ROMs in slot 2.

Keep your original card: writing this image erases the card you use.

## Write the card

1. From the [releases page](https://github.com/laurorual/MustardOS-R36S-port/releases)
   download `MustardOS-R36S-port-<version>.img.xz` and
   `MustardOS-R36S-port-<version>.img.xz.sha256`. Optional check on
   Linux/macOS: `sha256sum -c MustardOS-R36S-port-<version>.img.xz.sha256`.
2. Write the `.img.xz` file to the card with balenaEtcher, Rufus or
   Raspberry Pi Imager ("Use custom"). They decompress it themselves.
   On Linux without them:
   `xz -dc MustardOS-R36S-port-<version>.img.xz | sudo dd of=/dev/sdX bs=4M conv=fsync status=progress`
   (sdX = the card; check with `lsblk`).
3. Windows may offer to "format" the card afterwards: say **no** (its
   partitions are Linux partitions).

## First start

1. Put the card in **slot 1** (the one the handheld boots from; on most
   units the slot marked TF1/INT) and power on.
2. The first start takes a little longer: the data partition grows to the
   whole card. The boot logo shows "MustardOS R36S / R35S, unofficial
   port", then the MustardOS menu appears.
3. Language: Configuration → Language.
4. Wi-Fi (adapter plugged in): Configuration → Connectivity → Wi-Fi
   Network.

## Add games and BIOS files

No games or BIOS files are included; use only dumps of games you own.

- **Over Wi-Fi (SFTP):** Configuration → Connectivity → Web Services →
  Secure File Transfer → on. Connect with FileZilla or WinSCP: SFTP,
  the handheld's IP address, port **2022**, user **muos**, password
  **muos**. Put games in `ROMS/<system>` and BIOS files in `MUOS/bios`.
- **On a second card (slot 2):** a FAT32/exFAT card with a `ROMS` folder
  (`ROMS/<system>`); MustardOS lists it as SD2 in Explore Content.

Systems that need BIOS files: PlayStation (`scph5501.bin` or similar),
Sega CD (`bios_CD_U.bin`…), PC Engine CD (`syscard3.pce`), Dreamcast
(`dc/dc_boot.bin`, `dc/dc_flash.bin`), Saturn (`saturn_bios.bin`).

## Updates

- With Wi-Fi, a new release published on GitHub is downloaded and
  installed at the next start (only the system partition changes; games,
  saves and settings stay).
- Without Wi-Fi: copy `MustardOS-R36S-port-<version>.p2.img.gz` and its
  `.p2.img.sha256` from the release into `MUOS/update` on the card (SFTP
  or the card reader on Linux), then Applications → Task Toolkit →
  "Install Firmware Update".
- An update shows its progress, restarts the device twice and takes
  about 10 minutes: keep it on, on the charger or with at least 30 %
  battery. If the new system does not reach the menu, the next start
  returns to the previous one by itself; a new kernel is kept only after
  it reaches the menu.
- A full reflash (the steps above) erases saves: copy `MUOS/save` and
  `MUOS/pickles` off the card first.

## Good to know

- Heavy systems (PSP, Dreamcast, Saturn, N64) run best on battery: the
  charger heats the SoC and the CPU slows down.
- Configuration → Danger Settings → Undervolt can lower the heat further;
  if games crash with it on, switch it off in the same place.
- Known issues: [known-issues.md](known-issues.md).
- Root password (SSH, off by default): `root`. Change it if you enable
  SSH.
