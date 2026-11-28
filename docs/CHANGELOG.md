# Changelog

MustardOS for R36S/R35S (unofficial port). Not supported by the MustardOS
team: https://github.com/laurorual/MustardOS-R36S-port/issues

## v1.1.2 (unreleased)

- **First boot:** a newly flashed card starts in MustardOS's own
  first-boot setup (Date and Time, Language, Profiles, Input Tester,
  Shutdown, Install), as on muOS.
- **Install asks how to format the card's storage:** exFAT (recommended),
  FAT32 or EXT4. With exFAT or FAT32 the card opens on Windows and macOS:
  copy games straight into `ROMS/<system>`. The storage grows to the
  whole card. exFAT and FAT32 have no journal: shut down from the menu
  and keep the battery charged (README).
- A card updated from v1.1.1 keeps its EXT4 storage, its games and its
  settings (an update does not run the first boot). To switch it to
  exFAT, copy `ROMS`, `MUOS/save` and `MUOS/pickles` off the card, flash
  v1.1.2 and copy them back.
- A model chosen on a PC (`select-model` or `model.txt`) switches a few
  seconds after power-on, before the menu starts (it used to wait for
  the menu, about a minute of black screen on another panel).
- **More PortMaster ports run:** the libraries many ports expect from
  the system are now included (zstd, Vorbis, OpenAL, ModPlug, libsndfile,
  SDL2_gfx, SDL2_net, fontconfig, mpg123, Opus, libevdev, Speex and the
  PulseAudio client, played through PipeWire): 53 of 150 ready-to-run
  ports checked needed at least one. Nonny starts again.
- GameMaker ports (gmloadernext, e.g. Dueling Dragons) and other SDL2
  OpenGL ES games without vsync no longer freeze on a black screen
  after the first frame.
- Install's "Preparing the games storage" screen stays up long enough to
  be read before the restart.

## v1.1.1 (2026-11-27)

- **PortMaster:** Applications → PortMaster installs PortMaster on its
  first start (Wi-Fi, or `muos.portmaster.zip` in `MUOS/update`) and
  runs it as on muOS; ports appear in the Ports system and quit with
  Fn+Start. Godot, Mono, Java and other runtimes work; libretro ports run
  in the system's libretro frontend. 32-bit-only ports are not supported.
- Applications from `MUOS/application` (and PortMaster's app ports) start
  from the Applications menu.
- Python 3 in the system (for PortMaster).
- **PICO-8:** carts in `ROMS/PICO-8` play with the Picante8 core (FAKE-08
  as the other choice). The official PICO-8 (your own Raspberry Pi
  download in `MUOS/bios/pico8`) adds the standalone and pixel-perfect
  choices and the Splore app.
- GNU wget with HTTPS (Splore downloads, port scripts).
- Ports, applications, the official PICO-8 and the standalone emulators
  (N64, PSP, Dreamcast, Saturn, NDS, ScummVM) show the same volume and
  brightness bar as the libretro games, in the theme's style, with the
  menu's rounded corners (in games too).
- **Updates over Wi-Fi are manual:** Task Toolkit → "Check for Online
  Update" (below "Install Firmware Update") looks for a newer release,
  shows its version and asks before downloading (with progress), then
  asks to install now or later. Nothing is downloaded in the background
  any more.
- **Fixed:** the automatic updater installed the latest GitHub release
  even when it was older than the card's (v1.1.1 went back to v1.1.0),
  and its background download and unpack slowed PortMaster and the menu.
- Icons for "Install Firmware Update", "Check for Online Update" and the
  Splore app, in the MustardOS theme's style.
- **Fixed:** Fn+Start out of an N64 game fades out again (the screen went
  black at once).
- **Fixed:** A and B were swapped in ports, PortMaster, the official
  PICO-8, PPSSPP and Flycast on a card without an Input Remap; A is now
  confirm and B back everywhere, and A is PICO-8's O button in every
  PICO-8 core (FAKE-08 too).
- **Fixed:** a mouse arrow in the top-left corner of PortMaster and of
  ports.

## v1.1.0 (2026-11-26)

- **More R36S models (experimental):** 22 models with the 640x480 screen
  from dArkOSen's device trees (list in the README). Choose yours on a PC
  with `select-model.bat`, `.command` or (Linux, in a terminal)
  `sh select-model.sh` in the card's boot partition, or a hand-written
  `model.txt`; the console restarts once to apply it. Untested by the port:
  please report whether yours works.
- **More Wi-Fi dongles (experimental):** every USB Wi-Fi chip the kernel
  has a driver for (Realtek RTL8188EU/FTV, RTL8192CU, RTL8723BU,
  RTL8812AU, RTL8822BU and others, MediaTek MT7601U, Ralink RT5370 and
  others), with their firmware. The RTL8821CU stays the tested one.

## v1.0.0 (2026-11-26)

- **Updates:** an update over Wi-Fi or from the Task Toolkit now also
  brings the new kernel and boot screen: tried once at the next start and
  kept only if the menu comes up (otherwise the old kernel stays).
- **Update screens:** unpacking and installing show a progress bar; the
  install runs on its own screen right after the restart ("do not power
  off") instead of hidden behind the menu, and restarts by itself. About
  twice as fast (no extra copy of the old system, one pass to unpack).
  Needs the charger or at least 30 % battery.
- **Task Toolkit:** task and folder names, the update texts and help
  texts in every MustardOS language; diagnostics help points to the
  port's GitHub, not the MustardOS team.
- **Device Details:** Build shows the release (v1.0.0).

## v1.0.0-rc2 (2026-11-26, pre-release)

- **Battery:** charging now ends at 100 % ("Full"); before, the gauge
  stopped at 95–98 % (kernel: the BSP's finish check compared the charge
  level in the wrong units and never ran).
- **First start:** a new card starts in English at 50 % volume, with
  debug mode off.
- **Boot screen:** MustardOS's own boot screen from its press kit, with
  "R36S / R35S" and "unofficial port" below it.

## v1.0.0-rc1 (unreleased)

First public release candidate. Based on MustardOS 2606.0 ANDROMEDA
(frontend `5e8635b`, internal `550cc58`).

- **Firmware:** a complete card image for the R35S/R36S Panel 0: Linux
  4.4 (rk351 BSP) built from source, own U-Boot with boot records and an
  automatic fallback, read-only system partition, data partition that
  grows to the card, quiet boot with a logo.
- **Menu:** the MustardOS frontend built from source with the port's
  device patches; every screen works or is hidden; six themes, profiles,
  Task Toolkit, search, activity, screenshots, date and time with NTP.
- **Languages:** every MustardOS language; Português (Brasil) complete;
  Japanese and Chinese menu labels completed by the port.
- **Hardware:** display at 60 Hz, all controls, speaker and headphones,
  volume/brightness with an in-game bar, battery gauge and low-battery
  shutdown, sleep/resume, USB Wi-Fi (RTL8821CU) with SSH/SFTP.
- **Systems:** about 30 libretro cores and standalone Mupen64Plus (N64),
  PPSSPP (PSP), DraStic (NDS, with the two-screen layout and auto save),
  Flycast (Dreamcast), YabaSanshiro (Saturn) and ScummVM, with per-system
  CPU governors and save states.
- **Power:** CPU up to 1512 MHz as an opt-in; Undervolt (CPU/GPU, 25 mV
  steps) as an opt-in in Danger Settings.
- **Updates:** "Install Firmware Update" in the Task Toolkit and
  automatic updates from GitHub releases over Wi-Fi.
- **Licences:** THIRD-PARTY.txt in the image, the complete source bundle
  with every release, MustardOS naming per muos.dev/press.
