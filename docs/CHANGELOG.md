# Changelog

MustardOS for R36S/R35S (unofficial port). Not supported by the MustardOS
team: https://github.com/laurorual/MustardOS-R36S-port/issues

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
