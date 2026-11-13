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

**Phase 5 (own-card firmware). M1–M3d are done (M3d T3 passed
2026-11-13). M3e (below): steps 1–4 done at T2, the M3e image
`dist/firmware/test128-m3e-20261113` built and T2-passed on the trial
root; the battery full-discharge run (step 3) started 2026-11-13; then
the M3e T3 (checklist at the end).**

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1. Flashed with the M3d image on 2026-11-13 (without
  `--grow`; p3 grown on boot, 118.5 GiB).
  - Boot records (since 2026-11-13, M3e): main = `Image-3a3521e5cfb1`
    (kernel patches 0001–0004) + `panel0-c7b3551ce101.dtb` (408 MHz
    OPP); previous = the same Image + the M3d DTB `panel0-d2cef0b6bd98.dtb`.
  - p2 = the M3d image's p2 plus (`install-rootfs.sh`; originals in
    `/var/lib/muos-m1-backup`): `usr/sbin/resizepart` and the fixed
    `usr/libexec/muos-grow-p3` (M3d item 9); M3e so far: the hotkey map
    with hold (`opt/muos/share/hotkey/r35s-bringup.json`, staged in
    `build/m3e/tree`), `usr/libexec/muos-press` (hold:KEY) and
    `etc/modprobe.d/8821cu-power.conf`: functionally the M3e p2 (only
    muxretro's provenance metadata differs).
  - p3 `MUOS/trial/rootfs.img` = the M3e p2 (`6554ac33…`), T2-passed as
    the trial root.
  - p3: ROMs from `port/roms` (GB, NES, SNES, GBA, MD, PSX CTR) plus the
    image's `private.gb` and NES test game; the user's PSX BIOS
    (`MUOS/bios`, backup in `port/roms/bios`); saves restored from
    `build/m3b/p3-backup` (2026-11-11; later saves were not kept, by the
    user's choice). Pre-flash logs of the old p3:
    `build/m3d/p3-preflash-20261113`.
  - Volume 55 (the user's). Keep it at 10 during T2 runs at night.
- **original32 (stock dArkOSen):** the flasher station (slot 1, target
  in slot 2). Never write it.
- Device access, identity and card layout: procedures.md.

## Recovery image

The images are **private** (Wi-Fi PSK, SSH host key, authorized_keys):
never commit or share them. Flashing any image rewrites the whole card,
bootloader included; steps in procedures.md.

| Image | Content | State |
|---|---|---|
| `dist/firmware/test128-m3e-20261113.img.zst` (raw `08f03da8…`, p2 `6554ac33…`) | **M3e candidate:** M3d + p3 grow fix (`resizepart`), hold-to-repeat, Wi-Fi power save, 408 MHz CPU OPP, p1 without the Phase 4 `DIAGnn` folders, muxretro provenance | T2-passed on the trial root; never flashed (T3 below) |
| **`dist/firmware/test128-m3d-20261113.img.zst`** (raw `f2692bfa…`, p2 `fd78705a…`) | **Recovery image since 2026-11-13.** M3d: kernel 0001–0004, muxretro from source, volume fast path, Wi-Fi on CPU3, p3 auto-grow, log cap | Flashed and T3-passed. Its grow script lacks the item 9 fix: without `--grow` p3 reaches full size only on the second boot (expected; first-boot fsck may log rc 8) |
| `dist/firmware/test128-m3c-20261112.img.zst` (raw `64811ce2…`) | M3c: M3b boot chain + sftp-server, 4 cores, ROM folders | Previous recovery image; p2 T3-passed, image never flashed |
| `dist/firmware/test128-m3b-20261111.img.zst` (raw `2a8fec32…`) | M3b: boot-record U-Boot, M3b kernel + M2 kernel | Flashed and T3-passed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | Fallback |

5/5 firmware versions kept (`port/packaging/storage-retention.json`; M1
retired 2026-11-12, M3a.1 2026-11-13; retire M2 when M3e passes T3). If M3d fails to boot, flash M3c
the same way. Rule (user, 2026-11-13): a milestone whose T0–T3 show no
or only small problems becomes the recovery image, and the oldest kept
version is retired.

## What works (T3-confirmed)

Display (panel timing 60.0046 Hz), all controls, frontend and submenus;
volume and brightness with muxretro's in-game bar; speaker audio on every
boot; Wi-Fi + SSH/SFTP; prefs persistence; GB, NES, SNES, GBA, MD and PSX
(CTR smooth over full races, user's BIOS) with saves and states;
per-system governors; autostart, menu reboot/shutdown, hard power-cut
recovery; Power-key sleep/resume in menu and game (one small dip on
wake), shutdown timer, charging fake sleep; battery %, icon and charging
icon from the RK817 fuel gauge (cold boots, charging reboot and drain
hold the %); headphone path switching; flashing with the host card
reader. p3 auto-grow on first boot: fixed version T2-passed on test128
(T3 with the M3e image).

## Open problems

- **Battery, unverified:** accuracy over a full discharge (FCC 3380 mAh
  is the DT value until a full charge teaches it), the low-battery
  poweroff on real hardware (`muos-lowbattery`: ≤ 3% and < 3.5 V), and
  the reading after a dead battery. The BSP's `off=` (pwroff_min)
  underreports the time off (5 min for ~50); informational only.
- **Power:** menu idle ~409 mA (M3e: Wi-Fi power save 546 → 454 mA, the
  408 MHz CPU OPP → 409 mA; Wi-Fi off would be 397 − 45 mA; brightness
  70 → 35 saves ~38 mA). LEDs (the R35S LED node is disabled in stock too)
  and rumble not done.
- **Audio:** one unexplained no-sound report (M3d step 2, cleared by a
  reboot); the WirePlumber "no profile" start failure is retried, not
  explained; 3–8 underrun bursts per game; `info_open.wav` /
  `info_close.wav` are bass-heavy and inaudible on the speaker
  (hardware-findings; a high-passed copy as for `navigate.wav` would fix
  it, cosmetic).
- **Frame pacing:** one level-fps run on the M3e trial root had one
  29 ms frame (a late page flip) in a volume phase; the rerun and four
  other runs that day had 0 missed vsyncs.
- **Headphones (hardware, deprioritized by the user):** the jack isn't
  detected with the plug fully in, so the speaker keeps playing; a
  contact problem, not software (hardware-findings).
- **Wake:** one small dip remains (Wi-Fi association on CPU3, game on
  CPU0–2; worst frame ~30–50 ms). The user wants it gone late in the
  project if possible.
- **DDR devfreq** isn't synced to the display (no `vop-bw-dmc-freq` in
  the DT); schedutil games may switch DDR mid-game (no flash seen).
- **Image hygiene:** p1 still holds the Phase 4 `DIAG*` folders (about
  1 MiB); muxretro's `provenance.json` still describes the Phase 4
  binary; U-Boot messages go to serial/LCD only (no log on the card).
- **Pinned, not rebuilt:** the muOS frontend binaries, the cores, the
  kernel modules and the tuned `/opt/muos` config (`firmware-inputs.json`);
  idbloader and trust come from the M2 image (vendor blobs).
- **Trial root:** p3 can't be unmounted at shutdown while the trial root
  runs from it; the next boot replays p3's journal.
- **Wi-Fi:** inserting the dongle during boot is unqualified; Bluetooth
  is blacklisted.
- **Licences:** Mali r13p0, DDR/miniloader/BL31/BL32, the dirty U-Boot,
  Gambatte and BT firmware are private-only
  (`port/packaging/pending-licenses.json`).

## Decisions

Open:
1. **Licences / redistribution and public image identity:** proposed as
   M4 in [roadmap.md](roadmap.md#m4-proposal-first-public-image-2026-11-12-not-started);
   the Mali r13p0 userspace is the blocker. Needs the user (naming,
   contacting the MustardOS team).
2. **Kernel base:** keep the rk351 4.4 BSP (reassessed 2026-11-12,
   roadmap.md); a mainline/Panfrost port is the licence-clean path (M5
   candidate).

Taken:
- **CPU overclock** (1512 MHz DTB via `make-dtb-opp.sh`): deferred to
  the end of the project, as an optional toggle for the user (2026-11-13).
- **Recovery image promotion** after a passed T3: automatic (2026-11-13).

## Current milestone: M3e — daily-use polish

Goal: close the remaining M3 items that need no user decision and ship
the M3e image. Started 2026-11-13.

1. **Hold-to-repeat** (T2 done): post-build sets `handle_hold` on the
   level combos (as upstream). A 2 s hold moves the level ~10 steps;
   brightness 0 blanks the screen as upstream (the next brightness-up
   restores it). In game: 60.0 fps, 0 missed vsyncs (`t2-level-fps.sh`
   vol-hold / bright-hold).
2. **Menu idle power** (T2 done): Wi-Fi power save (`rtw_power_mgnt=1
   rtw_ips_mode=1`, `etc/modprobe.d/8821cu-power.conf`) 546 → 454 mA;
   ping avg 12 ms / max 92 ms, 20 MB push 3.5 s. The BSP's 408 MHz
   CPU OPP (0.95 V; the vendor DTS deleted it) 454 → 409 mA, 88% of
   menu idle at 408 MHz; games stay ≥ 1008 MHz. T2: NES gate 60.0 fps /
   0 missed; SNES, GBA, MD ~1 missed vsync per minute (as M3d); 2/2
   in-game sleep cycles.
3. **Battery full discharge** (running since 2026-11-13):
   `t2-discharge.sh start` plays the NES test game at volume 10 and logs
   a line a minute to p3 `MUOS/log/discharge.csv`; `report` after the
   recharge.
4. **Image hygiene** (done): p1 without `DIAGnn` / `PROBE.TXT` /
   `tools`; muxretro's provenance and `payload.sha256` describe the
   source build.
5. **M3e image** (T2 done on the trial root): audio before/after PASS,
   level-fps PASS on rerun (see "Frame pacing"), 2/2 in-game sleep
   cycles, long play 2 min each NES/SNES/GBA/MD/PSX PASS (2–3 missed
   vsyncs per game, fps ≥ 59.77, PSX 77 °C).

## M3e T3 checklist (user)

A. **Discharge run** (now): keep the charger unplugged and don't touch
   the device; the NES test game plays at volume 10 for ~3–4 h. Expected:
   at 25% the low-battery warning appears; at ≤ 3% (below 3.5 V) the
   device powers itself off cleanly. If the screen just goes black
   without the shutdown screen, say so (power was cut instead).
B. **After the poweroff:** plug the charger in with the device off and
   charge to full (several hours; overnight is fine), then power on.
   Expected: boots normally; the % is plausible for a full charge (about
   95–100%, not 0% and not a jump later); sound on. Tell me, and I run
   `t2-discharge.sh report`, back up the saves and restore your volume.
C. **Flash M3e** (after B): `flash-card.sh host /dev/sdX
   dist/firmware/test128-m3e-20261113.img.zst` *without* `--grow`.
   Expected: the first boot fills the card (I check `df` and
   `grow-p3.log`), I restore BIOS, ROMs and saves.
D. **On the flashed M3e:** menu navigation feels as smooth as before
   (the CPU now idles at 408 MHz); holding Vol+/Vol− and Menu+Vol
   changes the level continuously, in the menu and in a game, without
   stutter or crackle; Wi-Fi and SFTP work (slightly higher latency is
   expected); sleep/wake in a game OK; sound on every boot.
