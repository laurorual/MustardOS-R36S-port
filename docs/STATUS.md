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

**Phase 5 (own-card firmware). M1–M4f done (M4f = recovery image since
2026-11-18). M4g (SFTP jail, overdrive volume bar): `test128-m4g-20261118`,
T2 passed, p2 written 2026-11-18; **T3 pending** (checklist below).**
Details: milestones.md M4f, M4e.1.

## Next session — read first (2026-11-18 evening)

- Device off the charger, on main = **M4g p2** (`371b3f23…`); old p2 =
  M4f p2 + the M4g libmuxcom/muxretro installed (`38b383fa…`) in
  `MUOS/trial/p2-previous.img`. Web SSH and SFTP on (the user's setting).
- Next: the user's M4g T3 below; if it passes, promote M4g, retire M4d
  (5/5 now).
- The idle discharge logger (`MUOS/init`) still runs; `t2-discharge.sh
  report` pending (its `report` restores a saved volume: check first).

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1: M4b image flashed 2026-11-14, M4d p2 written
  2026-11-16, M4e.1 p2 written 2026-11-17, M4f and M4g p2 2026-11-18 (`write-p2`). p3
  `MUOS/trial/rootfs.img` = M4g p2 (`371b3f23…`), `p2-previous.img` =
  M4f p2 + M4g frontend files (`38b383fa…`).
  Time zone set by the user (−03); volume 55 (the user's level).
  - Boot records: main = `Image-ea8ac0033c0e` (0001–0008) +
    `panel0-bc04b6f8e4d4.dtb`; previous = `Image-d61188f3a808` (0007).
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
| `dist/firmware/test128-m4g-20261118.img.zst` (raw `a9d7cbc4…`, p2 `371b3f23…`) | M4g developer image (SFTP jail, overdrive bar) | p2 on the card; T2 passed; T3 pending |
| **`dist/firmware/test128-m4f-20261117.img.zst`** (raw `159d4894…`, p2 `46a573a0…`) | **Recovery image since 2026-11-18.** M4f (kernel 0001–0008, USB watchdog, menu scripts) | T3 2–6 passed, 1 bar only |
| `dist/firmware/test128-m4e1-20261117.img.zst` (raw `c122c7f4…`, p2 `d73646be…`) | M4e.1; recovery 2026-11-17 evening | T3 passed |
| `dist/firmware/test128-m4d-20261116.img.zst` (raw `619473f7…`, p2 `61f2c02f…`) + `public-m4d-20261116` | M4d (kernel 0001–0007); recovery 2026-11-17 morning | T3 items 1–3 passed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 firmware versions (`port/packaging/storage-retention.json`; retired
M1, M3a.1, M3b–M3e, M4a–M4c, M4e).

## What works (T3-confirmed)

Display (60.0046 Hz), all controls, frontend and submenus; volume and
brightness with muxretro's in-game bar and hold-to-repeat; speaker audio;
Wi-Fi (power save, profiles, scan, connect, replug, sleep/wake ~9 s,
on/off toggle, rows dimmed without a dongle, warm reboot) + SSH/SFTP;
time zone and NTP; prefs persistence; GB, NES, SNES, GBA, MD and PSX with
saves and states; per-system governors, 408 MHz menu idle; autostart,
menu reboot/shutdown, hard power-cut recovery; Power-key sleep/resume,
shutdown timer, charging fake sleep; Search, Activity (sleep excluded),
System details; battery %, icons and low-battery
poweroff from the RK817 gauge; battery-empty splash; headphone path
switching; flashing with the host card reader; p3 auto-grow; `panic=10`.

## Open problems

- **Battery:** (c) kernel 0008 (OFF_CNT cleared, register writable)
  passed warm reboots; its clear after a real power-off (no charger)
  is not yet seen in a log. (d) The BSP smoothing uses `abs(delta_cap)`.
- **USB (dwc2 misses port events):** an unplug (M4e T3) and a plug
  (M4e.1 T3, 1 in 4) left no kernel event although HPRT0 showed the
  change (connected bit set for 53 s, nothing enumerated). The dwc2 runs
  `dr_mode = "otg"` with its PHY (`otg-port`) disabled (same in
  ROCKNIX). `dr_mode = "host"` inconclusive (M4f); `muos-usb-watchdog`
  (M4f) rebinds dwc2 after 3 disagreeing reads (not yet triggered by a
  real replug: none missed in 4 at T3).
- **Missing muOS scripts:** still absent (M4f): `backup.sh` (needs zip),
  `extract.sh`, `profile.sh`, `bt_*.sh`; `prepare.sh`/`logo.sh` not
  wanted (one card, p1); no `share/lookup` name tables.
- **Audio overdrive bar (M4f T3 1):** fixed in M4g (T3 pending): the
  frontend clamps `device.audio.max` to 0–100 and ignored saved volumes
  above it while the bar scales by 200; now both bars accept up to 200
  with overdrive (`patches/muxretro/0002`, `patches/frontend/0006` in a
  rebuilt libmuxcom). 200 % = gain 8 (cubic): distorts, as upstream.
- **Translation (pt-BR, before the public build):** parts of the system
  stay English with Português (Brasil) selected, and the existing pt-BR
  text needs a review (user, 2026-11-18). Includes our own strings
  (Wi-Fi row help, Rumble "Unavailable").
- **Wi-Fi dongle (RTL8821CU):** the warm-reboot H2C case still happens
  (1 in 7 since M4c); the dongle resets itself after ~40 s; M4e retries
  at once (Wi-Fi at ~75 s instead of ~115 s). No software power cycle:
  the RK817 BOOST is not the port's 5 V (M4f).
  The user's slow first replug left no logs; `network-last.log` now
  keeps them. Inserting the dongle during boot is unqualified.
- **Wake:** Wi-Fi returns ~9 s after wake with ~0.7 s of slow frames.
- **Power:** menu idle ~420 mA; LEDs none controllable.
- **Audio:** one unexplained no-sound report (M3d); WirePlumber "no
  profile" start failure retried; 3–8 underrun bursts per game.
- **Headphones (hardware, deprioritized):** jack contact problem.
- **DDR devfreq** isn't synced to the display; **U-Boot log** goes to
  serial/LCD only.
- **Pinned, not rebuilt:** muxfrontend, libui, the cores, the
  kernel modules, the tuned `/opt/muos` config (now completed with empty
  directories at boot); idbloader and trust (rkbin files).
- **Trial root:** p3 can't be unmounted at shutdown while it runs; any
  reboot returns to main (one-shot marker).
- **Menu:** "Direct Link" and "Proxy
  Settings" not exercised; static addresses untested; the Rumble row's
  "present" case unverified (no motor here).
- **SFTP (M4g):** the menu's SFTP is jailed (muos/muos, port 2022);
  "Internal" is the read-only p2 view of `/opt/muos` (upstream binds it
  non-recursively: config/log show empty). Whether the Web Services
  screen shows the login is unverified.
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

## M4g T3 checklist (p2 written; no flash)

1. **Overdrive bar:** Configuration → Advanced → Audio overdrive on;
   in the menu and in a game, volume up to the top: the bar reaches the
   end (no stop at the middle). Overdrive off: the bar also reaches the
   end at 100 %, volume back to your level.
2. **SFTP from the PC** (FileZilla/WinSCP: SFTP, the console's IP, port
   2022, user `muos`, password `muos`): you see "Primary Storage"
   (MUOS, ROMS) and "Internal"; copy a ROM into `Primary Storage/ROMS/<system>`:
   it shows in Explore. User `root`/`root` on 2022 is refused.
3. **Battery (c):** off the charger, note the %, power off from the menu,
   wait ≥ 10 min, power on: the % is the same (±1). Tell me both values.
4. **Regression:** volume keys in a game (overdrive off), sleep/wake in
   game, Wi-Fi on/off.

## Next milestone (proposal)

**M4h:** `t2-discharge.sh report`; Web Services screen with the SFTP login
(check what the menu shows); then the publication checklist (roadmap M4:
public variant T2, licences, source bundle). **Before the final public
build:** a pt-BR milestone (inventory of English strings with pt-BR
selected, our own strings into the language files, review of the existing
pt-BR text).
