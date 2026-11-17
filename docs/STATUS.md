# Project status

Current state only; update at the end of every milestone. How-tos
(flash, build, trial root, trial kernel, boot sequence) are in
[procedures.md](procedures.md); finished milestones with their results and
T3 checklists in [milestones.md](milestones.md). See also
[hardware-findings.md](hardware-findings.md), [roadmap.md](roadmap.md),
[compatibility-matrix.md](compatibility-matrix.md) and
[storage.md](storage.md). The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## Current phase

**Phase 5 (own-card firmware). M1–M4c done (M4c T3 passed 2026-11-16 →
recovery image). M4d part 1 (Wi-Fi Network closed without an adapter,
battery cut-off at 1% on the current-corrected voltage, battery history,
clock: NTP + time zones, boot payloads all rkbin) is T2-passed and its p2
is written to the card (2026-11-16 night); its T3 is next (user).**
Details: milestones.md M4d.

## Today, 2026-11-16

- M4c T3: items 1–7 OK. Item 2 remark (Wi-Fi Network stayed enabled
  without a dongle) fixed in M4d. M4c promoted, M3e retired.
- Battery: 100% after the charge finish and days off was plausible; the
  card stored 85% after the T3 session (~50 min of Wi-Fi), voltage
  estimate 87–92%: consistent. From now on `MUOS/log/battery-history.log`
  records % and RTC date at every stop and boot.
- Decision 3 closed without a bootloader write: the trust image built
  from rkbin's BL31 is byte-identical to the card's (`rkbin-trust.sh`).

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1: M4b image flashed 2026-11-14 + M4d p2 written
  2026-11-16 (`write-p2`; the M4c p2 is in p3 `MUOS/trial/p2-previous.img`,
  sha `59991e2d…`). The M4c files installed with `install-rootfs.sh`
  are superseded by the new p2 (their backups in `/var/lib/muos-m1-backup`
  were on the old p2). Off the charger, ~76%; **volume 10** (lowered for
  the night tests; the user's level was 55); no logger, no test hooks.
  - Boot records: main = `Image-d61188f3a808` (patches 0001–0007) +
    `panel0-bc04b6f8e4d4.dtb` (capacity 2500/2550); previous =
    `Image-0c3305ad6946` (0001–0006). The M4d image has the same main.
  - p3: ROMs from `port/roms` (incl. CTR + PSX BIOS), Wi-Fi profile
    `MUOS/network/Home.ini`, zone link `MUOS/port/config/localtime` (UTC).
- **original32 (stock dArkOSen):** the flasher station (slot 1, target
  in slot 2). Never write it.
- Device access, identity and card layout: procedures.md.

## Recovery image

The developer images are **private** (Wi-Fi PSK, SSH host key,
authorized_keys): never commit or share them. Flashing any image rewrites
the whole card, bootloader included; steps in procedures.md.

| Image | Content | State |
|---|---|---|
| `dist/firmware/test128-m4d-20261116.img.zst` (raw `619473f7…`, p2 `61f2c02f…`) + `public-m4d-20261116` (raw `6b715293…`) | M4d developer + public variant | T2-passed; its p2 runs on the card; never flashed |
| **`dist/firmware/test128-m4c-20261114.img.zst`** (raw `ab60ef13…`, p2 `70f7ae82…`) | **Recovery image since 2026-11-16.** M4c (its kernel is `4f866b8b` = 0001–0005: flashing it drops 0006/0007) | T3 passed (files installed on the card) |
| `dist/firmware/test128-m4b-20261114.img.zst` (raw `3737c893…`) | M4b, flashed by the user | T3 items 1–6 passed |
| `dist/firmware/test128-m4a-20261114.img.zst` + `public-m4a-20261114` | M4a developer + public | T3 passed (developer) |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 firmware versions (`port/packaging/storage-retention.json`; retired
M1, M3a.1, M3b, M3c, M3d, M3e). After the M4d T3: promote M4d, retire
M4a (rule, user 2026-11-13).

## What works (T3-confirmed)

Display (60.0046 Hz), all controls, frontend and submenus; volume and
brightness with muxretro's in-game bar and hold-to-repeat; speaker audio;
Wi-Fi (power save, profiles, scan, connect, replug, sleep/wake ~9 s,
on/off toggle, warm reboot) + SSH/SFTP; prefs persistence; GB, NES, SNES,
GBA, MD and PSX (CTR smooth, user's BIOS) with saves and states;
per-system governors, 408 MHz menu idle; autostart, menu reboot/shutdown,
hard power-cut recovery; Power-key sleep/resume in menu and game,
shutdown timer, charging fake sleep; battery %, icons and low-battery
poweroff from the RK817 gauge (charger boot after a flat battery keeps
the stored %); battery-empty splash; headphone path switching; flashing
with the host card reader; p3 auto-grow; `panic=10` reboots after a
kernel panic.

## Open problems

- **Battery:** (b) the counter is lost after a flat-battery poweroff (why
  it ends near -3260 mAh is unknown); 0006 keeps the stored %, 0007 loads
  the seed (T3 at the next flat battery). (c) The BSP's `off=`
  underreports the time off and stays set across warm reboots (the
  battery history now has the real dates). (d) The BSP smoothing uses
  `abs(delta_cap)`: a counter jump while charging raises the % (only seen
  in 0007's T2; not patched).
- **Wi-Fi dongle (RTL8821CU):** a deaf dongle has no software recovery
  except another sleep (power cut). Inserting the dongle during boot is
  unqualified; Bluetooth blacklisted.
- **Wake:** a game resumes 0.6 s after wake; Wi-Fi returns ~9 s later
  with ~0.7 s of slow frames. The user wants dips gone late in the project.
- **Power:** menu idle ~409 mA; Wi-Fi off saves ~76 mA (CTR). LEDs: none
  controllable (the R35S LED node is disabled in stock too). Rumble:
  `board/rumble` empty (decision 10).
- **Audio:** one unexplained no-sound report (M3d); WirePlumber "no
  profile" start failure retried; 3–8 underrun bursts per game.
- **Frame pacing:** one M3e run had one 29 ms frame; reruns clean.
- **Headphones (hardware, deprioritized):** jack not detected with the
  plug fully in (contact problem).
- **DDR devfreq** isn't synced to the display; **U-Boot log** goes to
  serial/LCD only.
- **Pinned, not rebuilt:** muxfrontend, libui/libmuxcom (lang/config
  structs), the cores, the kernel modules, the tuned `/opt/muos` config;
  idbloader and trust from the M2 image (all rkbin files since M4d).
- **Trial root:** p3 can't be unmounted at shutdown while it runs; any
  reboot during a trial-root T2 returns to main (one-shot marker).
- **Menu:** the Wi-Fi row's help text is English only; "Direct Link" and
  "Proxy Settings" are upstream screens not exercised on the port; static
  addresses untested; the Timezone screen not yet driven on the device.
- **SFTP** runs as root with the whole filesystem (decision 6: port
  upstream's jail before the public build; needs a static sftp-server,
  M4e).
- **Tooling:** no shellcheck on the host (decision 9).
- **Licences:** Mali r13p0 (decision 2 (a): request sent 2026-11-14,
  awaiting the answer), the dirty U-Boot, Gambatte and BT firmware are
  private-only (`port/packaging/pending-licenses.json`); boot payloads
  resolved (rkbin LICENSE ships with the public image).

## Decisions

Answered by the user 2026-11-14 (evening):
1. **Name:** "muOS for R36S/R35S (unofficial port)"; the user contacts
   the MustardOS team before publication.
2. **Mali:** (a), request r13p0 terms from Hardkernel (sent 2026-11-14).
3. **Boot payloads:** rkbin files: done in M4d (trust identical).
4. **GPL source offer:** on GitHub.
5. **Public root password:** as upstream (`root`).
6. **SFTP:** port upstream's jailed `muos` user before the final public
   build.
7. **Unported web services:** hidden now (M4c); port some before the
   final public build.
8. **Public p3:** empty.

Open (2026-11-16):
9. **shellcheck:** downloading the static binary into `build/tools/` was
   blocked by the permission check; allow it, install it in the
   `fedora-dev` toolbox, or stay with `sh -n`.
10. **Rumble:** does the R35S have a vibration motor? If yes, enable
    `board/rumble` and test it (M4e).
11. **Public M4d image on hardware (optional, M4b item 7):** flash
    `public-m4d-20261116` on test128, check, then reflash M4d developer
    (or M4c recovery) and `rom-push.sh`; or leave it for the final build.

Earlier: kernel base stays the rk351 4.4 BSP (mainline/Panfrost = M5
candidate); CPU overclock deferred to the end as an optional toggle;
recovery promotion after a passed T3 is automatic.

## M4d T3 checklist (user; the card already runs M4d, no flash needed)

1. **Clock and time zone:** the header clock shows UTC (3 h ahead of
   Brasília). Configuration → General → Date and Time → Timezone → your
   region and city (e.g. America → Sao Paulo): back on the menu the
   header shows local time; Date and Time shows the zone. Reboot: still
   local time, right to the minute.
2. **Wi-Fi Network without a dongle:** Configuration → Connectivity,
   unplug the dongle: within ~3 s "Wi-Fi" reads "Unavailable" and "Wi-Fi
   Network" is dimmed too; A on either gives the error sound. Plug back:
   both normal within ~5 s.
3. **Regression (short):** boot to menu, a game with sound, sleep/wake
   once in the game (Wi-Fi back ~9 s), menu shutdown.
4. **Next flat battery (whenever it happens, e.g. a long game):** low
   warning at 25%; play on: the "battery empty" splash and a clean
   poweroff at 1% (not earlier than ~2–3 min after 3%). Later charger +
   power on: the % starts near the stored value and rises (0007 T3).
   Tell me the date; `MUOS/log/battery-history.log` has the rest.
5. Optional: decision 11 (public image).

## Next milestone (proposal)

**M4e — public-build prerequisites, part 2:** SFTP jail (static
sftp-server in Buildroot + upstream `musftpjail` adapted, `muos` user,
decision 6), rumble if decision 10 says yes, the Timezone screen driven
on the device, then the publication checklist (name, GPL bundle on
GitHub with rkbin's LICENSE, Mali answer).
