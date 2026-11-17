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

**Phase 5 (own-card firmware). M1–M4d done (M4d T3 items 1–3 passed →
recovery image). M4e (config directories = 24-hour clock fix, rumble
probe + "Unavailable" row, Wi-Fi diagnostics and faster retry,
shellcheck) is T2-passed on a trial root (night of 2026-11-16/17,
unattended); its p2 waits in p3 for `write-p2` with the user present.
Kernel 0008 (gauge jump after warm reboots) is built, untested.**
Details: milestones.md M4e.

## Tonight (2026-11-17, unattended) — read first

- The device is **on, off the charger, discharging** with the idle
  logger (`t2-discharge.sh log-start`, p3 `MUOS/log/discharge.csv`),
  volume 10, on the main p2 (M4d + M4e files). Expected: low-battery
  poweroff at 1% (M4d) during the night.
- **Gauge jump:** the last warm reboot (00:47) moved the % from 57 to 69
  (stale OFF_CNT → stale OCV, milestones M4e item 6). The night's
  cut-off therefore starts from a % that is ~12 points high; the log
  shows where the voltage really ends.
- **Incident:** a blind button sequence in a T2 launched CTR and a sleep
  test overwrote **CTR's resume state** (`autosave.state`, 00:38). The
  memory card save should be intact (the game saves only on demand).
- `write-p2` (M4e) and any PMIC write / trial kernel were not done:
  refused by the permission check while unattended.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1: M4b image flashed 2026-11-14, M4d p2 written
  2026-11-16, M4e files installed 2026-11-17 (`install-rootfs.sh`,
  originals in `/var/lib/muos-m1-backup`). p3 `MUOS/trial/rootfs.img` =
  M4e p2 (sha `1b877d11…`, T2-passed), `p2-previous.img` = M4c p2.
  Time zone set by the user (−03); volume 10 (user's level was 55).
  - Boot records: main = `Image-d61188f3a808` (0001–0007) +
    `panel0-bc04b6f8e4d4.dtb`; previous = `Image-0c3305ad6946`.
    `build/m3b/boot` now holds `Image` `ea8ac0033c0e` (0001–0008).
  - p3: ROMs, Wi-Fi profile `Home.ini`, zone link, rumble verdict
    (`MUOS/port/rumble`: absent), discharge logger in `MUOS/init`.
- **original32 (stock dArkOSen):** the flasher station (slot 1, target
  in slot 2). Never write it.
- Device access, identity and card layout: procedures.md.

## Recovery image

The developer images are **private** (Wi-Fi PSK, SSH host key,
authorized_keys): never commit or share them. Flashing any image rewrites
the whole card, bootloader included; steps in procedures.md.

| Image | Content | State |
|---|---|---|
| `dist/firmware/test128-m4e-20261117.img.zst` (raw `ea5ca0b4…`, p2 `1b877d11…`) | M4e developer image | T2-passed (trial root); never flashed |
| **`dist/firmware/test128-m4d-20261116.img.zst`** (raw `619473f7…`, p2 `61f2c02f…`) + `public-m4d-20261116` | **Recovery image since 2026-11-17.** M4d (kernel 0001–0007) | T3 items 1–3 passed (p2 ran on the card) |
| `dist/firmware/test128-m4c-20261114.img.zst` | M4c (kernel 0001–0005) | T3 passed |
| `dist/firmware/test128-m4b-20261114.img.zst` | M4b, flashed by the user | T3 items 1–6 passed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 firmware versions (`port/packaging/storage-retention.json`; retired
M1, M3a.1, M3b–M3e, M4a). After the M4e T3: promote M4e, retire M4b.

## What works (T3-confirmed)

Display (60.0046 Hz), all controls, frontend and submenus; volume and
brightness with muxretro's in-game bar and hold-to-repeat; speaker audio;
Wi-Fi (power save, profiles, scan, connect, replug, sleep/wake ~9 s,
on/off toggle, rows dimmed without a dongle, warm reboot) + SSH/SFTP;
time zone and NTP; prefs persistence; GB, NES, SNES, GBA, MD and PSX with
saves and states; per-system governors, 408 MHz menu idle; autostart,
menu reboot/shutdown, hard power-cut recovery; Power-key sleep/resume,
shutdown timer, charging fake sleep; battery %, icons and low-battery
poweroff from the RK817 gauge; battery-empty splash; headphone path
switching; flashing with the host card reader; p3 auto-grow; `panic=10`.

## Open problems

- **Battery:** (c) OFF_CNT stays set across warm reboots → OCV
  recalibration with a stale OCV on every warm reboot (+12 points seen);
  kernel 0008 clears it (T2/T3 pending). (b) Counter lost after a
  flat-battery poweroff; 0006/0007 (T3 = tonight's flat battery). (d) The
  BSP smoothing uses `abs(delta_cap)`.
- **Wi-Fi dongle (RTL8821CU):** the warm-reboot H2C case still happens
  (1 in 7 since M4c); the dongle resets itself after ~40 s; M4e retries
  at once (Wi-Fi at ~75 s instead of ~115 s). Next: a software power
  cycle through the RK817 BOOST (0xB4, hardware-findings), attended.
  The user's slow first replug left no logs; `network-last.log` now
  keeps them. Inserting the dongle during boot is unqualified.
- **Wake:** Wi-Fi returns ~9 s after wake with ~0.7 s of slow frames.
- **Power:** menu idle ~420 mA; LEDs none controllable.
- **Audio:** one unexplained no-sound report (M3d); WirePlumber "no
  profile" start failure retried; 3–8 underrun bursts per game.
- **Headphones (hardware, deprioritized):** jack contact problem.
- **DDR devfreq** isn't synced to the display; **U-Boot log** goes to
  serial/LCD only.
- **Pinned, not rebuilt:** muxfrontend, libui/libmuxcom, the cores, the
  kernel modules, the tuned `/opt/muos` config (now completed with empty
  directories at boot); idbloader and trust (rkbin files).
- **Trial root:** p3 can't be unmounted at shutdown while it runs; any
  reboot returns to main (one-shot marker).
- **Menu:** Wi-Fi row help text English only; "Direct Link" and "Proxy
  Settings" not exercised; static addresses untested; the Rumble row's
  "present" case unverified (no motor here).
- **SFTP** runs as root with the whole filesystem (decision 6: jail
  needs a static sftp-server; M4f).
- **Licences:** Mali r13p0 (Hardkernel: no answer yet), the dirty
  U-Boot, Gambatte and BT firmware are private-only.

## Decisions

Answered by the user 2026-11-14: 1 name "muOS for R36S/R35S (unofficial
port)"; 2 Mali (a), request sent 2026-11-14, no answer as of 2026-11-17;
3 boot payloads rkbin (done, M4d); 4 GPL source on GitHub; 5 public root
password `root`; 6 SFTP jail before the final public build; 7 unported
web services hidden; 8 public p3 empty.
Answered 2026-11-17: 9 shellcheck download allowed (done); 10 the R35S
has no rumble motor; keep the option, detect the motor, show
"Unavailable" without one (done in M4e); 11 no public-image test yet.

Open: none.

## Tomorrow (user, 2026-11-17)

1. Don't charge before looking: if the device is off, it hit the
   low-battery poweroff. Then plug the charger, power on, and tell me
   (the % at power-on and later while charging = 0007's T3). If it is
   still on, leave it; it keeps logging.
2. With the user present, the agent will: `write-p2` the M4e p2, test
   kernel 0008 (one i2c write check, then a trial kernel), pull the
   discharge log (`t2-discharge.sh report`), and optionally try the
   BOOST power cycle for the Wi-Fi dongle.

## M4e T3 checklist (after the agent's write-p2; no flash)

1. **24-hour clock:** Configuration → General → Date and Time → Time
   Notation → a 24-hour option, back: the header shows 24-hour time;
   survives a reboot.
2. **Rumble row:** Configuration → Advanced: "Rumble" reads
   "Unavailable", dimmed; left/right/A give the error sound; "Rumble
   strength" is not listed.
3. **Other saves in new directories (spot check):** change one overlay
   or hotkey setting in General/Advanced, leave, re-enter: it stuck.
4. **Wi-Fi replug:** unplug/plug the dongle twice in Connectivity; note
   which one is slow, if any (the log now keeps the reason).
5. **After kernel 0008 (if tested):** reboot twice from the menu: the %
   doesn't jump.

## Next milestone (proposal)

**M4f:** kernel 0008 on hardware; dongle power cycle via BOOST (if the
attended test works: deaf-dongle recovery in seconds, maybe a shorter
settle); SFTP jail (static sftp-server in Buildroot + upstream
`musftpjail`, `muos` user); then the publication checklist.
