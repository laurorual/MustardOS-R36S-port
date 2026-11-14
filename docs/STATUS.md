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

**Phase 5 (own-card firmware). M1–M3e are done (M3e T3 passed
2026-11-14; results in milestones.md). M4a in progress (autonomous night
2026-11-14, see "M4a progress" below).**

## M4a progress (night of 2026-11-14, checkpoint)

- Discharge run started 06:21 UTC at 94% (idle menu, ~360 mA):
  `t2-discharge.sh log-start`, logger restarted on every boot through
  the new user init scripts (S98, p3 `MUOS/init`). Status:
  `t2-discharge.sh status`; after recharging: `t2-discharge.sh report`
  then `log-stop`.
- Done + T2: Wi-Fi from muOS's Connectivity menu (profiles, scan,
  SSH/SFTP toggles), installed on test128 with `install-rootfs.sh`.
  A guard (`MUOS/init/aa-net-guard.sh`, backup in `MUOS/m4a-guard`)
  restores the M3e worker if the network isn't ready 4 min after boot.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1. Flashed with the M3e image on 2026-11-14 (without
  `--grow`; p3 grown on the first boot, 116.6 GiB, resize2fs rc 0).
  - Boot records (from the image): main = `Image-b486b7126df2`
    (kernel patches 0001–0005) + `panel0-c7b3551ce101.dtb` (408 MHz
    OPP); previous = the M2 kernel.
  - p2 = the M3e image's p2; no trial root on p3.
  - p3: ROMs from `port/roms` (GB, NES, SNES, GBA, MD, PSX CTR) plus the
    image's `private.gb` and NES test game; the user's PSX BIOS
    (`MUOS/bios`, backup in `port/roms/bios`); saves (`MUOS/pickles`)
    restored from `build/m3e/p3-backup-20261114`, checksums identical.
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
| **`dist/firmware/test128-m3e-20261113.img.zst`** (raw `7b7c4a66…`, p2 `fd547220…`) | **Recovery image since 2026-11-14.** M3e: kernel 0001–0005, p3 grow fix, hold-to-repeat, Wi-Fi power save, 408 MHz CPU OPP | Flashed and T3-passed (p3 grows on the first boot) |
| `dist/firmware/test128-m3d-20261113.img.zst` (raw `f2692bfa…`) | M3d: kernel 0001–0004, muxretro from source, p3 auto-grow (second boot) | Previous recovery image; flashed and T3-passed |
| `dist/firmware/test128-m3c-20261112.img.zst` (raw `64811ce2…`) | M3c: M3b boot chain + sftp-server, 4 cores, ROM folders | p2 T3-passed, image never flashed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build** (`build-image.sh`): bootloader blobs, M2 kernel, identity; never retire while used |

4/5 firmware versions kept (`port/packaging/storage-retention.json`;
retired: M1, M3a.1, M3b 2026-11-14). If M3e fails to boot, flash M3d the
same way. Rule (user, 2026-11-13): a milestone whose T0–T3 show no or
only small problems becomes the recovery image, and the oldest kept
version except the M2 base is retired.

## What works (T3-confirmed)

Display (panel timing 60.0046 Hz), all controls, frontend and submenus;
volume and brightness with muxretro's in-game bar and hold-to-repeat;
speaker audio on every boot; Wi-Fi (power save) + SSH/SFTP; prefs
persistence; GB, NES, SNES, GBA, MD and PSX (CTR smooth over full races,
user's BIOS) with saves and states; per-system governors, 408 MHz menu
idle; autostart, menu reboot/shutdown, hard power-cut recovery;
Power-key sleep/resume in menu and game (one small dip on wake),
shutdown timer, charging fake sleep; battery %, icon and charging icon
from the RK817 fuel gauge (cold boots, charging reboot, a full discharge
with a clean low-battery poweroff at 3%, and the boot after a dead
battery hold a plausible %); headphone path switching; flashing with the
host card reader; p3 auto-grow on the first boot.

## Open problems

- **Battery:** (a) the FCC (3380 mAh, DT value) is probably too large:
  the counter still held 974 mAh at 3%; below 3.85 V the % follows the
  voltage (BSP zero algorithm), so above it the % may fall too slowly and
  speed up later. A 100% → 0% `t2-discharge.sh` run would measure it.
  (b) Patch 0005's lost-counter branch is verified by review only (seen
  once, with the old kernel); its stale-OCV and sanity branches were
  T2-tested. (c) The low-battery poweroff shows no shutdown screen
  (cosmetic). The BSP's `off=` underreports the time off (47 min for
  ~7 h) and stays set across warm reboots.
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
- **Frame pacing:** one level-fps run (M3e) had one 29 ms frame (a late
  page flip); the rerun and four other runs had 0 missed vsyncs.
- **Headphones (hardware, deprioritized by the user):** the jack isn't
  detected with the plug fully in, so the speaker keeps playing; a
  contact problem, not software (hardware-findings).
- **Wake:** one small dip remains (Wi-Fi association on CPU3, game on
  CPU0–2; worst frame ~30–50 ms). The user wants it gone late in the
  project if possible.
- **DDR devfreq** isn't synced to the display (no `vop-bw-dmc-freq` in
  the DT); schedutil games may switch DDR mid-game (no flash seen).
- **U-Boot log:** messages go to serial/LCD only (no log on the card).
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

## Next milestone (proposal): M4a — public-image foundations

M4 (roadmap.md) needs the user for naming and the licence position, but
its technical half doesn't. M4a builds that half; nothing is published.
1. **Public build variant** (`build-image.sh image --public`): no Wi-Fi
   PSK, no authorized_keys, no host key (generated on first boot),
   dropbear off by default; a check refuses a public image holding keys,
   `network.conf` or seeds. The developer image stays as it is.
2. **First-boot Wi-Fi:** upstream muxnetwork (scan, on-screen keyboard)
   writes `config/network/*`; the port's network worker generates the
   wpa_supplicant config from it. SSH/SFTP follow muOS's web-services
   toggles.
3. **Cosmetics:** a "battery empty" splash before the low-battery
   poweroff; high-passed `info_open/close.wav`.
4. **Licence groundwork:** match the pinned boot blobs to rkbin and
   survey libmali bifrost-g31 builds with redistribution terms (report
   only).
T3: flash the public image on test128 (developer image as recovery),
join Wi-Fi from the menu, enable SSH from the menu, the developer key
is refused. Optional, whenever the device can sit idle: a 100% → 0%
discharge to measure the real battery capacity.
