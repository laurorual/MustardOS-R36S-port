# Changelog

MustardOS for R36S/R35S (unofficial port). Not supported by the MustardOS
team: https://github.com/laurorual/MustardOS-R36S-port/issues

## v1.2.0 (unreleased)

- **PortMaster:** Applications → PortMaster installs PortMaster on its
  first start (Wi-Fi, or `muos.portmaster.zip` in `MUOS/update`) and
  runs it as on muOS; ports appear in the Ports system and quit with
  Fn+Start. Godot, Mono, Java and other runtimes work; libretro ports run
  in the system's libretro frontend. 32-bit-only ports are not supported.
- Applications from `MUOS/application` (and PortMaster's app ports) start
  from the Applications menu.
- Python 3 in the system (for PortMaster).

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
