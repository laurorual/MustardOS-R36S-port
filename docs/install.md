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
   units the slot marked TF1/INT) and power on. The boot logo shows
   "MustardOS R36S / R35S, unofficial port", then MustardOS's first-boot
   setup opens.
2. Set **Date and Time** and **Language**; **Profiles** and **Input
   Tester** (checks every button) are optional. **Shutdown** turns the
   handheld off without installing: the setup opens again at the next
   start.
3. **Install** asks how to format the card's storage (games, saves,
   settings):
   - **exFAT** (recommended): Windows, macOS and Linux read and write it,
     so games can be copied straight to the card's `ROMS` folders.
   - **FAT32**: every computer reads it, but no file can be larger than
     4 GB.
   - **EXT4**: copes best with a sudden power loss, but Windows cannot
     read it without extra software.

   The handheld restarts, the storage grows to the whole card and is
   formatted (a few seconds), and the MustardOS menu appears with the
   date, language and profile you chose.

   > **exFAT and FAT32 and power loss:** the settings, saves and the
   > firmware update area live on that same storage. These filesystems
   > have no journal: if the battery dies or the console is switched off
   > while it writes (saving a game, changing a setting, installing an
   > update), files can be damaged, and at worst the card needs to be
   > flashed again. Shut down from the menu, keep the battery charged, and
   > back up your saves.
4. Wi-Fi (adapter plugged in): Configuration → Connectivity → Wi-Fi
   Network.

## Add games and BIOS files

No games or BIOS files are included; use only dumps of games you own.

- **On a PC (exFAT or FAT32):** power the handheld off, put the card in
  the PC's reader and copy games into `ROMS/<system>` and BIOS files
  into `MUOS/bios` on its storage drive (the large one; leave the small
  boot drive alone). Eject the card before taking it out.
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

Only the system partition changes; games, saves and settings stay.
Nothing is downloaded without asking.

- With Wi-Fi: Applications → Task Toolkit → "Check for Online Update"
  shows a newer release and asks before downloading it and before
  installing it.
- Without Wi-Fi: copy `MustardOS-R36S-port-<version>.p2.img.gz` and its
  `.p2.img.sha256` from the release into `MUOS/update` on the card (on a
  PC with an exFAT/FAT32 card, or over SFTP), then Applications → Task
  Toolkit → "Install Firmware Update".
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
