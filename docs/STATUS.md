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

**Phase 5 (own-card firmware). M1–M4a done (M4a T3 2026-11-14: items
0–5 and 7–9 OK, 6 = sleep/wake with Wi-Fi partial, fixed in M4b). M4b
(Wi-Fi robustness, public boot −30 s, crash capture, quiet console,
battery capacity) was built and T2-passed on the trial root in the
afternoon of 2026-11-14, unattended. It is not on the card yet: writing
p2 and installing the kernel/DTB were refused by the agent's permission
check and need the user. The device has been unreachable since the last
test (a forced kernel panic, 14:47 local).** M4 publication waits for the
"Decisions for the user".

## When you're back (user)

1. **Device unreachable** since 14:47 (forced panic to test `panic=10`;
   it didn't come back within 15 min, no ARP reply). Nothing on p1 or
   the main p2 was written: the main p2 is still M4a and the trial-root
   marker was consumed, so the next boot is plain M4a. Look at the screen,
   tell the agent what it showed, then power-cycle (hold Power ~8 s,
   press again):
   - **menu visible:** it rebooted, but the dongle stayed deaf after the
     panic's warm reboot (like case (d) below) → `panic=10` works;
   - **frozen / black / kernel text:** the panic did not reboot →
     `panic=10` doesn't help on this BSP (photo if there is text).
   Expected afterwards: M4a boots, `device.sh` finds it. If it doesn't
   boot: flash the recovery image `dist/firmware/test128-m4a-20261114`
   (procedures.md).
2. **Approve the M4b install** (pick one): (a) the agent writes p2 from
   the trial root (`write-p2`, old p2 saved to p3) and installs the
   kernel + DTB as a trial kernel, then promotes it (both have automatic
   fallbacks); (b) you flash `dist/firmware/test128-m4b-20261114.img.zst`
   (raw `3737c893…`, p2 `a45a3c4a…`) with the card reader (wipes p3).
   For (a) while you are away, allow those commands in the agent's
   permission settings; otherwise do it while you're there.
3. Answers to the "Decisions for the user".
4. The M4b T3 checklist (below), after the install.

## Afternoon of 2026-11-14 (M4b, unattended)

- **Fixes** (details: milestones.md M4b): settle a freshly powered dongle
  ≥ 10 s before the CD-ROM switch (`connected_duration`); udev hotplug
  hook (`usr/libexec/muos-network/hotplug`); stale-interface reset;
  retries reset the dongle; every network daemon in its own session
  (`setsid`); `muos-suspend` resumes a game at once while the dongle
  settles; S85 waits for a host key only on developer images; sysctl
  `kernel.panic=10`, console printk 4; S89 saves ramoops oops dumps to
  p3 `MUOS/log/pstore/`; gauge estimate with 200 mΩ (patch 0005); DT
  `design_capacity` 2500 / `design_qmax` 2550.
- **T2 on the trial root, all PASS:** `t2-wifi-robust.sh` (menu SSH
  survives a UI kill; simulated unplug/replug, Wi-Fi back in 18 s),
  sleep cycles 6/6 (bind-mounted) + 4/4 menu + 2/2 + 3/3 + 2/2 in game,
  `t2-wifi.sh`, `t2-audio-state.sh`, `t2-menu-cycle.sh`; boot to menu
  16.5 s. The dongle returns in CD-ROM mode after every "mem" sleep, also
  on the charger; no H2C error with the settle. A DWC2 unbind/bind does
  **not** power-cycle the dongle (no software power cycle exists).
- **Not tested on the device:** the new kernel/DTB (T1 only: DTB values,
  `Module.symvers` = reference); a real replug (T3); `panic=10` (see 1.).
- M4a developer image promoted to recovery; M3c retired.
- Device-side leftovers: p3 `MUOS/trial/rootfs.img` (M4b p2),
  `MUOS/init/zz-trial-guard.sh` with `user_init=1` (reboots a trial root or
  trial kernel without Wi-Fi after 6 min; inert on main; remove after the
  install, `MUOS/trial/user_init.before` = 0). The user's volume 55 is set
  to 10 for the tests (restore after).

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, reflashed by the user with the M4a developer image
  on 2026-11-14 (after the public-image T3); on the charger.
  - Boot records: main = `Image-b486b7126df2` (kernel patches 0001–0005)
    + `panel0-c7b3551ce101.dtb` (408 MHz OPP); previous = the M2 kernel.
  - p3: ROMs from `port/roms`, Wi-Fi profile `MUOS/network/Home.ini`;
    the M4b leftovers above.
- **original32 (stock dArkOSen):** the flasher station (slot 1, target
  in slot 2). Never write it.
- Device access, identity and card layout: procedures.md.

## Recovery image

The developer images are **private** (Wi-Fi PSK, SSH host key,
authorized_keys): never commit or share them. The public variant holds
none of that but isn't cleared for publication (decisions 1–4). Flashing
any image rewrites the whole card, bootloader included; steps in
procedures.md.

| Image | Content | State |
|---|---|---|
| `dist/firmware/test128-m4b-20261114.img.zst` (raw `3737c893…`, p2 `a45a3c4a…`) | M4b developer image: M4a + Wi-Fi robustness, crash capture, kernel `4f866b8b` (0005 at 200 mΩ) + DTB `bc04b6f8` (capacity 2500/2550) | p2 T2-passed on the trial root; kernel/DTB T1 only; never flashed |
| **`dist/firmware/test128-m4a-20261114.img.zst`** (raw `deef0ab2…`, p2 `d61fd490…`) | **Recovery image since 2026-11-14 (afternoon).** M4a developer image (Wi-Fi menu, user init, splash, info sounds) | Flashed and T3-passed (with the public variant) |
| `dist/firmware/public-m4a-20261114.img.zst` (raw `193c520f…`, p2 `05d01396…`) | M4a **public** variant: no identity, SSH off, root password `root`, empty p3 | T3 by the user 2026-11-14 (items 1–8); not for publication yet |
| `dist/firmware/test128-m3e-20261113.img.zst` (raw `7b7c4a66…`, p2 `fd547220…`) | M3e: kernel 0001–0005, p3 grow fix, hold-to-repeat, Wi-Fi power save, 408 MHz CPU OPP | Previous recovery image; flashed and T3-passed |
| `dist/firmware/test128-m3d-20261113.img.zst` (raw `f2692bfa…`) | M3d: kernel 0001–0004, muxretro from source, p3 auto-grow | Flashed and T3-passed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build** (`build-image.sh`); never retire while used |

5/5 firmware versions kept (`port/packaging/storage-retention.json`;
M4a = one version with both variants; retired: M1, M3a.1, M3b, M3c
2026-11-14). After the M4b T3: promote M4b, retire M3d. Rule (user,
2026-11-13): a milestone whose T0–T3 show no or only small problems
becomes the recovery image, and the oldest kept version except the M2
base is retired.

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

- **Battery:** (a) FCC 3380 mAh vs ~2530 measured (2026-11-14): M4b sets
  DT `design_capacity` 2500 / `design_qmax` 2550, so the BSP clamps the
  stored FCC to 2550 at the next boot (it never learns FCC). Expect one
  % jump on that boot; consistent after a full charge (T3 + a discharge
  run). (b) Patch 0005's lost-counter estimate read 33% on a ~4% battery
  while charging at 1.6 A (V − I·100 mΩ); M4b uses 200 mΩ (measured),
  not tested on the device yet. (c) The BSP's `off=` underreports the
  time off (47 min for ~7 h) and stays set across warm reboots.
- **Wi-Fi dongle (RTL8821CU, M4a T3 2026-11-14; logs
  `build/logs/wifi-m4a/`, M4b T2 `build/logs/m4b/`):** a "mem" sleep cuts
  the dongle's power; switched out of CD-ROM mode 0.27 s after power-up
  its firmware failed the BT-coex H2C and stayed deaf until a power
  cycle. M4b: ≥ 10 s settle (T2 17/17 wakes), udev hotplug, stale-state
  reset. Open: (d) one warm reboot after a deaf dongle stayed deaf until
  a cold boot (cause unknown); a deaf dongle has no software recovery
  (replug or cold boot); (e) the "bootloop with hex" (an oops) was never
  reproduced; M4b reboots on panic (if `panic=10` works, see "When
  you're back") and saves the dump to p3.
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
- **Wake:** M4b resumes a game 0.6 s after wake (was 6 s); the Wi-Fi
  bring-up ~13 s later costs ~0.7 s of slow frames (worst 52 ms,
  `build/logs/m4b/stall-wake.log`). The user wants dips gone late in the
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
- **Public image first boot** (M4a): the empty-p3 path (S90, S91
  seeding, S98, worker idle) passes in a qemu container
  (`t1-fresh-p3.sh`); S89's real mount, p3 growth and the UI on an empty
  p3 are T3 item 1.
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

## M4b T3 checklist (user, after the install)

1. **Boot:** menu in ~17 s; no driver text scrolls over the screen.
2. **Battery % on the first M4b boot:** note the % before the install
   and after the first boot (one jump expected, FCC 3380 → 2550); then
   charge to full: 100% when the charge ends, not earlier.
3. **Sleep/wake with Wi-Fi, 3 times** (menu and in a game): Wi-Fi icon
   back ~15 s after waking; in a game: back in the game within ~1 s,
   maybe one short hitch ~13 s later.
4. **Replug the dongle** with Wi-Fi on: unplug, 10 s, plug back: Wi-Fi
   back within ~30 s, no reboot needed. Then scan in Wi-Fi settings:
   networks listed.
5. **Unplug the dongle and scan:** no networks (no hang); plug back in:
   item 4 again.
6. **Charger boot after a flat battery** (when convenient): plug in and
   power on at once: a low % (not ~33%).
7. **Public image (optional, flash the M4b public variant later):** boot
   in ~17 s instead of 46 s; SSH survives the splash demo.

## Next milestone (proposal)

After the M4b install and T3: **M4c — daily-use and power**: Wi-Fi
radio off when unused (menu toggle), LEDs/rumble, NTP for the clock, the
hidden web-service toggles if decision 7 says so, and an overnight
discharge run to validate the new capacity. With decision 2 = (c), M5
(mainline + Panfrost) planning replaces it.
