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

**Phase 5 (own-card firmware). M1–M4e.1 done (M4e.1 = recovery image).
M4f (USB watchdog, menu scripts): `test128-m4f-20261117`, T2 passed
(trial and live root), p2 written 2026-11-18; **T3 pending**. Item 3
(BOOST power cycle) dropped: the BOOST is not the port's 5 V.**
Details: milestones.md M4f, M4e.1.

## Next session — read first (2026-11-18)

- Device off the charger, on main = **M4f p2** (`46a573a0…`, written
  2026-11-18 with `write-p2`; old p2 = M4e.1 + M4f files installed,
  `d58ca5a3…`, in `MUOS/trial/p2-previous.img`).
- `t2-wifi-robust` hotplug fixed (test only): the watchdog rebinds 4–6 s
  after the software unplug ("missed plug"), so the removed state is
  sampled at 3 s and the watchdog's rebind is the re-add.
- Next: the user's M4f T3 below; if it passes, promote M4f to recovery,
  retire M4c.
- The idle discharge logger (`MUOS/init`) still runs; `t2-discharge.sh
  report` pending.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1: M4b image flashed 2026-11-14, M4d p2 written
  2026-11-16, M4e.1 p2 written 2026-11-17, M4f p2 2026-11-18 (`write-p2`). p3
  `MUOS/trial/rootfs.img` = M4f p2 (`46a573a0…`), `p2-previous.img` =
  M4e.1 p2 + M4f files (`d58ca5a3…`).
  Time zone set by the user (−03); volume 10 (user's level was 55).
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
| `dist/firmware/test128-m4f-20261117.img.zst` (raw `159d4894…`, p2 `46a573a0…`) | M4f developer image | p2 on the card (2026-11-18); T2 passed; T3 pending |
| **`dist/firmware/test128-m4e1-20261117.img.zst`** (raw `c122c7f4…`, p2 `d73646be…`) | **Recovery image since 2026-11-17 (evening).** M4e.1 (kernel 0001–0008) | T3 passed |
| `dist/firmware/test128-m4d-20261116.img.zst` (raw `619473f7…`, p2 `61f2c02f…`) + `public-m4d-20261116` | M4d (kernel 0001–0007); recovery 2026-11-17 morning | T3 items 1–3 passed |
| `dist/firmware/test128-m4c-20261114.img.zst` | M4c (kernel 0001–0005) | T3 passed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 firmware versions (`port/packaging/storage-retention.json`; retired
M1, M3a.1, M3b–M3e, M4a, M4b, M4e).

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

- **Battery:** (c) kernel 0008 (OFF_CNT cleared, register writable)
  passed warm reboots; its clear after a real power-off (no charger)
  is not yet seen in a log. (d) The BSP smoothing uses `abs(delta_cap)`.
- **USB (dwc2 misses port events):** an unplug (M4e T3) and a plug
  (M4e.1 T3, 1 in 4) left no kernel event although HPRT0 showed the
  change (connected bit set for 53 s, nothing enumerated). The dwc2 runs
  `dr_mode = "otg"` with its PHY (`otg-port`) disabled (same in
  ROCKNIX). M4f: try `dr_mode = "host"` (trial DTB), else a watchdog.
- **Missing muOS scripts:** the pinned `/opt/muos/script/mux` has only
  `audio_sink.sh` (+ `sdl_remap.sh` since M4e.1); the frontend also calls
  `tweak.sh` (Power, Theme, Custom, Danger saves), `find.sh` (search),
  `backup.sh`, `extract.sh`, `track.sh`, `bt_*.sh` (M4f audit).
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

## M4f T3 checklist (after write-p2; no flash)

1. **Audio overdrive:** Configuration → Advanced → Audio overdrive on,
   back: volume goes above 100 %; off again: max 100 %.
2. **Search:** Explore → Search "crash": CTR listed, opens.
3. **Activity:** play a game ~2 min, quit: Activity shows it with ~2 min;
   sleep during play is not counted.
4. **System details:** serial shown; integrity shows "Modified".
5. **Wi-Fi replug x4** (watchdog log `/opt/muos/log/usb-watchdog.log`):
   each plug reconnects within ~25 s even if the kernel misses one.
6. **Regression:** sleep/wake in game, Wi-Fi toggle.

## Next milestone (proposal)

**M4f:** (1) dwc2 missed plug/unplug: trial DTB with `dr_mode =
"host"`, replug series with `t2-usb-watch.sh`; fallback: a watchdog that
compares HPRT0 with usb 1-1 and rebinds dwc2. (2) Missing muOS menu
scripts (`tweak.sh` first, then search, backup, extract, playtime).
(3) Dongle power cycle via BOOST; SFTP jail (static sftp-server in Buildroot + upstream
`musftpjail`, `muos` user); then the publication checklist.
