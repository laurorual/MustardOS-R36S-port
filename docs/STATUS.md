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

**Phase 5 (own-card firmware). M1–M3e are done. M4a (public-image
foundations + Wi-Fi from the settings menu) was built autonomously in
the night of 2026-11-14: T0–T2 passed, T3 pending (checklist below).
M4 publication waits for the "Decisions for the user".**

## Night of 2026-11-14 (summary)

- **Discharge run (optional battery measurement):** started 06:21 UTC at
  94% (gauge counter 3172 mAh), idle menu, ~360 mA, volume 10 (the
  user's 25 is saved). At 07:30 UTC: 84%, 2797 mAh. The logger is a p3
  user-init script, so it survived the 8 reboots of the night. Expected
  to end with the low-battery poweroff (3%) around 13:00–15:00 UTC; the
  device was left on. **After recharging and powering on:**
  `port/scripts/t2-discharge.sh report` (pulls `MUOS/log/discharge.csv`
  to `build/logs/discharge/`, restores volume 25), then
  `t2-discharge.sh log-stop`. Columns `cc_mah` (coulomb counter),
  `rsoc`, `dsoc`, `fcc` give the real capacity: counter at 94% minus the
  counter at 3%, plus the integrated current.
- **M4a done (commits `a3d80de`…):** Wi-Fi menu + SSH/SFTP toggles,
  user init scripts, public build variant + leak check, battery-empty
  splash, high-passed info sounds, licence survey. Details:
  [milestones.md](milestones.md#m4a--public-image-foundations--wi-fi-menu-t2-done-2026-11-14-t3-pending).
- **test128 now runs the M4a developer p2** (trial-root boot, then
  `write-p2`, read-back verified). Rollback without reflash: p3
  `MUOS/trial/p2-previous.img` (the M3e p2 + tonight's installs, sha
  `c053c985…`) through the trial-root procedure.
- The public image was never booted (as instructed): T0/T1 only.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1. Flashed with the M3e image on 2026-11-14; p2 is the
  M4a developer p2 since 2026-11-14 07:20 UTC (`write-p2`).
  - Boot records: main = `Image-b486b7126df2` (kernel patches
    0001–0005) + `panel0-c7b3551ce101.dtb` (408 MHz OPP); previous = the
    M2 kernel.
  - p3: ROMs from `port/roms`, the user's PSX BIOS, saves; Wi-Fi profile
    `MUOS/network/Home.ini` (made from the private `network.conf` for
    T2: private like the image); `MUOS/init/zz-discharge-log.sh` and
    `settings/advanced/user_init=1` until `log-stop`;
    `MUOS/trial/p2-previous.img`.
  - Volume 10 during the run (the user's 25 restored by `report`).
- **original32 (stock dArkOSen):** the flasher station (slot 1, target
  in slot 2). Never write it.
- Device access, identity and card layout: procedures.md.

## Recovery image

The images are **private** (Wi-Fi PSK, SSH host key, authorized_keys):
never commit or share them. Flashing any image rewrites the whole card,
bootloader included; steps in procedures.md.

| Image | Content | State |
|---|---|---|
| `dist/firmware/test128-m4a-20261114.img.zst` (raw `deef0ab2…`, p2 `d61fd490…`) | M4a developer image (Wi-Fi menu, user init, splash, info sounds) | p2 T2-passed on test128 (trial root, then written); never flashed as a whole |
| `dist/firmware/public-m4a-20261114.img.zst` (raw `193c520f…`, p2 `05d01396…`) | M4a **public** variant: no identity, SSH off, root password `root`, empty p3 | T0/T1 only (`check-public-image.sh` 18/18); not private, but not for publication yet |
| **`dist/firmware/test128-m3e-20261113.img.zst`** (raw `7b7c4a66…`, p2 `fd547220…`) | **Recovery image since 2026-11-14.** M3e: kernel 0001–0005, p3 grow fix, hold-to-repeat, Wi-Fi power save, 408 MHz CPU OPP | Flashed and T3-passed (p3 grows on the first boot) |
| `dist/firmware/test128-m3d-20261113.img.zst` (raw `f2692bfa…`) | M3d: kernel 0001–0004, muxretro from source, p3 auto-grow (second boot) | Previous recovery image; flashed and T3-passed |
| `dist/firmware/test128-m3c-20261112.img.zst` (raw `64811ce2…`) | M3c: M3b boot chain + sftp-server, 4 cores, ROM folders | p2 T3-passed, image never flashed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build** (`build-image.sh`): bootloader blobs, M2 kernel, identity; never retire while used |

5/5 firmware versions kept (`port/packaging/storage-retention.json`;
M4a = one version with both variants; retired: M1, M3a.1, M3b
2026-11-14). After the M4a T3: promote the developer M4a image, retire
M3c. If M3e fails to boot, flash M3d the
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
  speed up later. The 94% → 3% run of 2026-11-14 measures it (see the
  night summary).
  (b) Patch 0005's lost-counter branch is verified by review only (seen
  once, with the old kernel); its stale-OCV and sanity branches were
  T2-tested. (c) M4a adds a "Battery empty" splash (its visibility is
  unverified: T3 item 8). The BSP's `off=` underreports the time off (47 min for
  ~7 h) and stays set across warm reboots.
- **Power:** menu idle ~409 mA (M3e: Wi-Fi power save 546 → 454 mA, the
  408 MHz CPU OPP → 409 mA; Wi-Fi off would be 397 − 45 mA; brightness
  70 → 35 saves ~38 mA). LEDs (the R35S LED node is disabled in stock too)
  and rumble not done.
- **Audio:** one unexplained no-sound report (M3d step 2, cleared by a
  reboot); the WirePlumber "no profile" start failure is retried, not
  explained; 3–8 underrun bursts per game; `info_open.wav` /
  `info_close.wav` high-passed in M4a (audibility: T3 item 7).
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
  is blacklisted. M4a: the menu's connect/scan were T2-tested through the
  scripts and button injection, not by eye; the on-screen keyboard and a
  network other than the bench's are T3. A scan leaves the radio on
  until the next boot or sleep if no network gets configured. Static
  addresses are implemented but untested. Web services other than SSH
  and SFTP (dashboard, mDNS, NTP, Syncthing, virtual terminal) are not
  ported: their toggles do nothing.
- **SFTP (M4a)** runs as root with the whole filesystem (upstream jails
  user `muos` to the storage with `musftpjail`, which the pinned
  frontend lacks).
- **Licences:** Mali r13p0, DDR/miniloader/BL31/BL32, the dirty U-Boot,
  Gambatte and BT firmware are private-only
  (`port/packaging/pending-licenses.json`, M4a survey added there:
  DDR/miniloader/BL32 = rkbin files under rkbin's LICENSE; BL31 differs
  from rkbin's v1.14; no redistributable libmali for the r13p0 kbase).

## Decisions for the user

Collected in the night of 2026-11-14; nothing below was decided or
contacted on the user's behalf. M4 publication waits for 1–4.
1. **Name and identity of a public image:** what to call it (e.g.
   "muOS for R35S — unofficial port"), and whether to ask the MustardOS
   team before using the muOS name and the MustardOS theme assets in a
   published image (roadmap M4 step 3). Contacting them is the user's call.
2. **Mali GPU userspace (the blocker):** the Hardkernel r13p0 blob has
   no terms; Rockchip's libmali repo is gone and the surviving mirror
   only has g24p0 builds (ARM EULA allows redistribution with the EULA,
   but they need a newer kbase than the 4.4 BSP). Options: (a) send the
   drafted request to Hardkernel for r13p0 terms
   (`docs/archive/phase4/hardkernel-r13-license-request.md`); (b) port a
   g24p0 kbase to the 4.4 kernel (large, uncertain); (c) mainline +
   Panfrost (M5, months; ROCKNIX as reference). Pick one.
3. **Boot payloads:** DDR v1.10, miniloader v1.12 and BL32 v1.10 match
   rkbin byte for byte (rkbin LICENSE: use, copy, distribute; it was added
   after these 2018 files: is that acceptable?). BL31 v1.14 does not
   match rkbin: approve replacing it with rkbin's BL31 (a trust-image
   rebuild = bootloader write, needs a T3 cycle), or open TF-A later.
4. **GPL source offer:** where to host the pinned source bundle (kernel,
   U-Boot, Buildroot packages, GPLv3 muOS frontend, cores) that must
   accompany a published image.
5. **Default root password of the public image:** `root`, as upstream
   muOS documents (only reachable after the user enables SSH/SFTP in the
   menu). Alternatives: no password login at all, or a forced change.
6. **SFTP scope:** keep root + whole filesystem (simple, now) or port
   upstream's jailed `muos` user (needs `musftpjail`, a frontend rebuild).
7. **Unported web services** (dashboard, mDNS, NTP, Syncthing, virtual
   terminal): hide their toggles (needs a frontend change) or port some
   of them later. NTP would give the clock a source (no RTC battery?).
8. **Public p3 content:** the public image ships an empty p3 (no test
   ROM, no BIOS). OK, or add the port's own NES test game?

Still open from before:
- **Kernel base:** keep the rk351 4.4 BSP (reassessed 2026-11-12,
  roadmap.md); a mainline/Panfrost port is the licence-clean path (M5
  candidate) — ties in with decision 2.

Taken:
- **CPU overclock** (1512 MHz DTB via `make-dtb-opp.sh`): deferred to
  the end of the project, as an optional toggle for the user (2026-11-13).
- **Recovery image promotion** after a passed T3: automatic (2026-11-13).

## M4a T3 checklist (user)

0. **Before anything else:** charge test128 (it may have powered itself
   off at 3% — expected) and power it on; ask the agent to run
   `t2-discharge.sh report` and `log-stop`: flashing wipes p3 and the
   log with it. Expected: a clean low-battery poweroff logged, and
   (item 8) whether you saw the splash if you were there.
1. **Flash the public image** `dist/firmware/public-m4a-20261114.img.zst`
   on test128 with the host card reader (procedures.md); recovery =
   `test128-m4a-20261114` (or M3e). Boot: menu in ~15–20 s (first boot
   grows p3), no Wi-Fi icon in the header.
2. **Join Wi-Fi from the menu:** Configuration → Connectivity → Wi-Fi
   Network → X (scan) → pick your network → Password (on-screen
   keyboard) → Connect. Expected: status goes Associating/Authenticating
   → Connected with an IP within ~15 s; Wi-Fi icon in the header.
   A wrong password shows "invalid password" (optional).
3. **Reboot:** reconnects by itself (icon back within ~30 s of the menu).
4. **Enable SSH:** Connectivity → Web Services → SSH on. From the PC:
   `ssh root@<ip>` with password `root` works. The developer key is
   refused: `port/scripts/device.sh find <ip>` fails (no :2222, other
   host key).
5. **Enable SFTP:** `sftp -P 2022 root@<ip>` (password `root`) lists
   `/`; a file copy works. Turn SSH/SFTP off again: the ports close.
6. **Sleep/wake with Wi-Fi on:** Power short press, wake: Wi-Fi back.
7. **Info sounds:** open a help box (the menu's info/help key) and close
   it: both sounds audible now (were inaudible before).
8. **Battery-empty splash** (any image ≥ M4a): seen at the end of a full
   discharge, or ask the agent to show it (`S99muos-ui stop;
   muos-splash`): "Battery empty" picture, readable, not rotated.
9. **Back to the developer image:** flash `test128-m4a-20261114`, check
   SSH via `device.sh` and Wi-Fi as before. If 1–9 pass: the developer
   M4a image becomes the recovery image, M3c is retired.

## Next milestone (proposal)

Depends on the decisions above. Without them, **M4b — daily-use and
power**: Wi-Fi radio off when unused (menu toggle), the real FCC from
tonight's discharge in the DT (if the run confirms it), LEDs/rumble,
NTP for the clock, and the hidden web-service toggles if decision 7
says so. With decision 2 = (c), M5 (mainline + Panfrost) planning
replaces it.
