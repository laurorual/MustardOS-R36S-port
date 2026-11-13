# Project status

Update at the end of every milestone. Finished milestones (results,
checklists) are in [milestones.md](milestones.md). See also
[hardware-findings.md](hardware-findings.md), [roadmap.md](roadmap.md),
[compatibility-matrix.md](compatibility-matrix.md) and
[storage.md](storage.md). The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## Current phase

**Phase 5 (own-card firmware). M1–M3c are done; M3c's image is the
recovery image. M3d (smoothness + robustness): step 1 (game governor, wake
order, panel timing, PSX BIOS) passed T3 on 2026-11-12; step 2 (battery %
from the fuel gauge, per-system governor profiles) is done: the re-test's
boot jumps were a BSP unit bug, fixed by kernel patch 0003 (T2-passed,
main on the card). Steps 3–6 run autonomously on the night of
2026-11-13; the T3 checklist is at the end of this file.** Results:
milestones.md.

## Device and bench

- **Device:** R35S Panel 0, test128 in slot 1, flashed with the M3b
  image on 2026-11-11 (host card reader, p3 grown to the whole card).
  Boot records (since 2026-11-13 night): main = `Image-0563896506e7`
  (kernel patches 0001–0003) + M3d DTB `panel0-d2cef0b6bd98.dtb`;
  previous = `Image-84112f93c3dc` (0001+0002) + the same DTB.
  Unreferenced on p1: `Image-48b6fc61382f` (0001), the M3b kernel
  `Image-ab18bba307f8`, the M2 kernel, the M3b DTB `panel0-496bbe3591f8.dtb`.
  - p2: the M3c build `313d6a44…` (content-identical to the p2 of
    `test128-m3c-20261112`; ext4 metadata differs), written via the trial
    root on 2026-11-12, plus the M3d step 1–2 files installed with
    `install-rootfs.sh` (originals in `/var/lib/muos-m1-backup`). The previous p2 (M3c step 1, `30e0f57c…`) is on p3
    at `MUOS/trial/p2-previous.img`.
  - ROMs on p3: GB (private, Pokemon Yellow, Super Mario Land), NES (SMB3),
    GBA, SNES, MD, PSX (CTR) from `port/roms`; PSX BIOS (user's) in
    `MUOS/bios`; volume left at 10.
  - Saves: the pre-flash `pickles` were restored from
    `build/m3b/p3-backup` (byte-identical); the post-flash ones are kept
    in `build/m3b/p3-postflash`.
  - The DHCP IP changes between boots; it was 192.168.15.8.
  - Identify the device by its host key, not its IP:
    `SHA256:fDW+/iNaWgqPwqBtO/ESuKPSQHvYN1PSo2RHfilOxK0`.
  - Identify a boot by `/proc/sys/kernel/random/boot_id`.
- **Access:** `port/scripts/device.sh` locates the device by fingerprint:
  `find`, `id`, `run CMD`, `sh`, `sftp`, `scp` (device paths as
  `dev:/path`), `push`, `pull`, `reboot` / `poweroff` (both through init),
  `capture DIR`.
- **test128 layout** (disk ID `4d554432`, 249872384 sectors):
  - Bootloader at sectors 64 / 16384 / 24576; boot records at sectors
    32 (main), 33 (previous), 34 (trial).
  - p1: FAT `MUOSDIAG`, 16 MiB+100 MiB, ro at `/boot`.
  - p2: ext4 root, 128 MiB+512 MiB, ro at runtime.
  - p3: ext4 `MUOSDATA`, 640 MiB to the end, rw at `/userdata`. 1 GiB in
    images; `--grow` extends it.
- **original32 (stock dArkOSen):** the flasher station, in slot 1 with
  the target card in slot 2. Never write original32 itself.

## Recovery images and flashing

The images are in `dist/recovery/` (captures) and `dist/firmware/`
(built), each with `.sha256` and `.manifest`. **They are private:** they
contain the Wi-Fi PSK, the SSH host key and authorized_keys. Never commit
or share them. **Recovery image: M3c** (p2 T3-passed 2026-11-12, raw
SHA256 re-verified from the `.zst`), M3b (flashed, T3-passed) as the
previous one; M3a.1 and M2 stay as fallbacks with the M2 U-Boot. Flashing
any image rewrites the whole card, bootloader included. A recovery image
restores the M3c panel timing (old DTB): the M3d DTB is only on p1 of the
card until the M3d image exists.

| Image | Content | Boots on |
|---|---|---|
| **`dist/firmware/test128-m3c-20261112.img.zst`** (raw `64811ce2…`) | **Recovery image since 2026-11-12.** M3c: M3b boot chain + sftp-server, 4 cores, ROM folders; p2 T3-passed on the card (content-identical); the image itself not yet flashed | any card ≥ 2 GiB (expected) |
| `dist/firmware/test128-m3b-20261111.img.zst` (raw `2a8fec32…`) | Previous recovery image. M3b: boot-record U-Boot, M3b kernel (main) + M2 kernel (previous); flashed and T3-passed | any card ≥ 2 GiB |
| `dist/firmware/test128-m3a1-20261111.img.zst` (raw `112db539…`) | M3a.1: M2 U-Boot and kernel, SDL2 with its pipewire driver; p2 T3-passed, image never flashed | any card ≥ 2 GiB (expected) |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: + sleep, battery, headphones, NES core; the last flashed image with the M2 U-Boot | any card ≥ 2 GiB |

M1 was retired on 2026-11-12 (everything in it is in M2); 4/5 versions
kept, leaving room for the M3d image. Flash commands below name M3c; if it
ever fails to boot, flash M3b the same way.

**Flash with the host card reader (primary, since 2026-11-11):**
1. Power the device off and put its card in the USB reader on the host.
2. `lsblk -dno NAME,TRAN,SIZE,MODEL` (the reader shows `usb`, about 119 GiB
   for test128).
3. `port/scripts/flash-card.sh host /dev/sdX dist/firmware/test128-m3c-20261112.img.zst --grow`
   - It accepts only a whole USB/removable/MMC disk (it refuses the
     internal `sda` and `nvme0n1`, partitions, an empty reader and a
     too-small card), shows model and size, asks `y`, then asks for sudo.
   - It unmounts the card, writes, re-reads with caches dropped, checks
     the SHA256 (`verified raw_sha256=…`), then grows p3 (`p3 grown and
     clean`).
4. Put the card in slot 1 (slot 2 empty), power on.

**Flash via dArkOSen (fallback, no reader):**
1. Power off. Put original32 in slot 1 and the target card in slot 2.
   Boot, join Wi-Fi, and enable Remote services (Options).
2. On the host:
   `port/scripts/flash-card.sh darkosen <dArkOSen-IP> dist/firmware/test128-m3c-20261112.img.zst --grow`
   - Enter the `ark` SSH password once and the sudo password once.
   - Same checks as above; the target is always slot 2 (`/dev/mmcblk1`).
3. Power off. Move the card to slot 1, leave slot 2 empty, power on.

**Build the firmware** (about 50 min from scratch, minutes
incrementally; rootfs in `build/m3a/output`, boot chain in `build/m3b`):
0. Boot chain: `port/scripts/build-boot.sh all` (kernel incremental in
   `build/m3b/kernel-output`, U-Boot in `build/m3b/uboot-boot`; outputs
   and `SHA256SUMS` in `build/m3b/boot`). `kernel-ref` / `uboot-ref`
   rebuild the M2 card's `Image`/DTB/`uboot.img` and must match byte for
   byte (done once in M3b). `kernel` fails if `Module.symvers` changes
   (the modules are pinned inputs). Host tests: `port/scripts/t0-boot.sh`
   (U-Boot logic against mocks, record codec).
1. `port/scripts/build-image.sh prepare`, then `source` (network, only
   fetches what the cache lacks), then `build` (offline, detached;
   follow with `build-image.sh status` or
   `tail -f build/m3a/logs/build.log | grep --line-buffered '^>>>'`).
   - `build` checks that SDL2 registers its pipewire driver (the target's
     `/usr/libexec/muos-sdl-audio-probe --require pipewire` under qemu);
     on a clean tree it isn't (pipewire depends on sdl2), so it runs
     `sdl2-dirclean` + `all` and checks again (+~2 min).
2. `port/scripts/build-image.sh image <name>` → `dist/firmware/<name>.img.zst`
   plus `build/m3a/<name>.p2.img` (raw p2 for the trial root). It refuses
   an image whose SDL2 lacks the pipewire driver (qemu check, then
   `check-rootfs-contract.sh` on the p2 image). The boot chain comes from
   `build/m3b/boot`: U-Boot at 16384, the kernel on p1 under content
   names, records main = it, previous = the M2 kernel.
3. `port/scripts/retention.py add <name> "<reason>" <files>`

Prebuilt inputs are pinned in `port/packaging/firmware-inputs.json` and
stored in `build/m3a/inputs/<sha256>` (`build-image.sh inputs`). To
re-derive them from a device: inventory p2 (`find` + sha256, see
milestones.md M3a), then `firmware-inputs.py generate`; it reports every
difference against the build. A device capture
(`device.sh capture` + `make-recovery-image.sh`) still works for
snapshots.

**Update p2 in place via the trial root** (no reflash):
1. Copy the raw p2 to p3 `MUOS/trial/rootfs.img` (`device.sh push` a
   gzip, `gunzip` on the device) and check its sha256.
2. `mount -o remount,rw / && touch /etc/muos-root-trial && mount -o remount,ro /`,
   then `device.sh reboot`. `muos-root-trial status` must say
   `trial-root yes`. Run the T2 suite there.
3. Re-arm (the marker is one-shot), reboot, then
   `/usr/libexec/muos-root-trial write-p2 /userdata/MUOS/trial/rootfs.img <sha256>`:
   it saves the old p2 to `MUOS/trial/p2-previous.img`, writes and reads
   back. Reboot into the new p2.
4. To go back: the same with `p2-previous.img` and its `.sha256`.

**Update the kernel or DTB via a trial kernel** (no bootloader write):
1. `device.sh push` the `Image` and DTB to `/run` (tmpfs: gone after a
   reboot), then `/usr/libexec/muos-boot-slot install-trial /run/Image
   /run/<dtb> "<label>"`: copies them to p1 as `Image-<sha12>` /
   `panel0-<sha12>.dtb` and arms the trial record.
2. `device.sh reboot`; `/proc/cmdline` must say `muos_slot=trial`. U-Boot
   consumed the record before booting it: a hang → power cycle → main; a
   panic reboots by itself (`panic=10` on trial boots only). Run T2.
3. `muos-boot-slot promote` (previous = old main, main = trial), reboot.
   `muos-boot-slot status` shows the records; `t2-boot-slot.sh` checks
   the fallbacks (3 reboots).
- Never overwrite or delete a p1 file that main or previous points to.

**Risky init changes** to inittab, rc or the shim: arm a trial boot.
1. Copy the known-good inittab to `/etc/inittab.fallback`.
2. Install the change, `touch /etc/muos-boot-trial`, reboot.
3. Confirm by deleting `/etc/muos-boot-trial.used`.

If SSH never comes back, a long-press power cycle boots
`inittab.fallback` instead of needing a reflash.

## Boot and runtime

U-Boot (`muos_boot`: armed trial once, then main, then previous; each
file size- and SHA256-checked, see hardware-findings.md) boots
`init=/sbin/muos-ext4-diag` with `muos_slot=<slot>`; the shim runs BusyBox
init, which runs `/usr/libexec/muos-rc start`:

| Step | Service | What it does |
|---|---|---|
| 1 | stock `seedrng`, syslog, sysctl, `udev`, D-Bus | standard Buildroot services; the TRNG has the RNG ready at 2.6 s |
| 2 | S41muos-network | Wi-Fi and dropbear on :2222 in the background; up at about 20 s |
| 3 | S85 | root ro |
| 4 | S89 | `e2fsck -p` on p3 (≤ 100 s; log p3 `MUOS/log/fsck-p3.log`), p3 rw at `/userdata`, p1 ro at `/boot` |
| 5 | S90 | muOS storage binds |
| 6 | S91 | persistent muOS config, core assignments and per-output volume on p3 (`MUOS/port`); tmpfs views for other muOS paths; logs on p3 `MUOS/log/system` (three previous boots in `system.prev*`) |
| 7 | S95 | audio (retried up to 3× within 25 s) + muinput; audio failure is non-fatal |
| 8 | S96 | input mapping |
| 9 | S97 | battery (`mubattery`, `muos-lowbattery`), headphones (`muos-headphone`) |
| 10 | S99 | UI frontend loop (+ `muos-hotkey`) |

The menu is on screen about 15 s after power-on.

- **Content** runs in muxretro: Explore → `ROMS/<system>` → libretro core
  (gambatte, fceumm). Saves and states go to p3 `MUOS/pickles`.
- **Shutdown/reboot** (launcher or `device.sh`) runs `muos-rc stop`: UI →
  input → core → runtime → storage → p3 in about 2 s. Log in
  `/run/muos-rc.log`; the last shutdown's copy is p3 `MUOS/log/rc-last.log`.
- **Power key** (upstream muOS): short and long press both sleep
  (`muos-suspend`: muxretro auto-save + pause, backlight off, mute,
  Wi-Fi/SSH down, `mem`; the 8821cu is unloaded and DWC2 unbound around
  `mem`). Shutdown timer: clean poweroff after 10 min asleep. With the
  charger in: fake sleep (screen off). Presses are ignored 6 s after
  waking.
- **Battery:** the RK817 gauge's `capacity` drives the status bar; a
  warning at 25%, clean poweroff at ≤3% while discharging.
- **Headphones:** jack in → path `HP`, out → `SPK_HP`; each output keeps
  its own volume (upstream `SWITCH_OUTPUT_VOLUME`).
- **cpufreq:** muOS per-content governors through `muos-governor` (GPU
  floor, deep idle and DDR follow the CPU governor, as upstream). Menu:
  `schedutil` (idles at 1008 MHz), dmc_ondemand. Games: `performance`
  (M3d default; SoC ~82 °C after minutes of PSX, throttling starts near
  85 °C). No overclock (deferred by the user 2026-11-11; a
  1512 MHz DTB from `make-dtb-opp.sh` would now go in as a trial kernel).

Source lives in `port/device/rk-r35s-p0/rootfs/`; the init scripts are
symlinks to the files Buildroot also uses. Deploy with
`port/scripts/install-rootfs.sh [paths]` (atomic; keeps the first original
in `/var/lib/muos-m1-backup`; `--restore` undoes).

**Safe mode:** create `/boot/muos-noui` on the FAT partition; the UI is
skipped, SSH still comes up.

**Seed:** stock seedrng only; images ship without `seed.*`; the dropbear
host key is the only persistent identity (M1 decision, see milestones.md).

## Safety mechanisms kept

| Mechanism | Why it stays |
|---|---|
| Flashable images + `flash-card.sh` (verify by re-read) | The recovery path. |
| Trial-boot fallback in the init shim | Turns a broken init into a power cycle instead of a reflash. |
| Root ro at runtime; p3 journal; ordered, bounded `muos-rc stop`; `umount -a -r` | Power-loss and shutdown safety. |
| 4.4-safe ext4 features (no 64bit, metadata_csum_seed, orphan_file or fast_commit) | Kernel 4.4 compatibility. |
| btusb blacklist (Wi-Fi-only) | The warm-reboot dongle fix. |
| `muos-run-bounded` | Time limits for services. |
| Boot records + one-shot trial kernel; previous = the M2 kernel | Kernel/DTB changes never touch the bootloader; a bad kernel costs a power cycle. |
| Never `saveenv` or dArkOSen `flash_uboot.sh`; never write original32 | Protects the bootloader and the stock card. |
| ≤ 5 firmware versions (`retention.py`) | Host disk space. |

The M1 retirements are listed in milestones.md. M3a retired 410 Phase 4
scripts (in Git at `e7d67a2`). M3b retired `install-dtb.sh` (it overwrote
the DTB the previous record pins); the Phase 4 U-Boot/kernel probe
scripts remain only as the producers of the Phase 4 references.

## What works (T3-confirmed)

Display, all controls, frontend and submenus, volume and brightness,
speaker and headphone audio on every boot (M3a.1),
Wi-Fi + SSH, prefs persistence; GB (Gambatte)
and NES (fceumm, SMB3 at 59.9 fps) with saves and states; autostart, menu
reboot/shutdown, hard power cut recovery; physical Power key sleep/resume
in menu and game, shutdown timer, charging fake sleep; battery icon, %,
charging icon; headphone path switching.

## Broken, caveated or unverified

- **Headphones (hardware, deprioritized by the user 2026-11-11):** with
  the plug fully in, the speaker keeps playing (no jack detection) and
  only some frequencies drop in the headphones while others stay normal:
  a jack contact problem, not software (codec registers are identical on
  both paths; a center-cancel pattern suggests the sleeve/ground
  contact). Only a slightly-off insertion is detected and mutes the
  speaker. Per-output volume passes at T2 (simulated jack) but at T3 both
  outputs share one level, as expected when the jack is never detected.
- **Battery %:** since M3d step 2 the kernel reports the RK817 fuel
  gauge (coulomb counter) instead of the BSP's voltage-only estimate that
  jumped to 100% on charging or after a cold boot (hardware-findings
  "Battery %"). Step 2 T3: one reboot (charger just removed, ~90%) came up
  at 0% with the coulomb counter full; the port's low-battery service
  powered off. The boot path is unknown (that boot's dmesg was lost);
  the re-test then showed +5–13% jumps on a cold boot and a charging
  reboot: the BSP's boot calibration compared % with 1/1000 % and reset
  the gauge to the OCV estimate on every boot (also the 0% cause). Patch
  0003 fixes the units; patch 0002 still corrects dsoc vs coulomb
  disagreements > 10% at boot and logs every boot's inputs (`muos-gauge:` lines, copied to
  `/opt/muos/log/battery-port.log` by S97), and `muos-lowbattery` powers
  off only below 3.5 V. Unverified: accuracy over a full discharge (FCC
  3380 mAh is the DT value until a full charge teaches it), the reading
  after a dead battery, and the no-sound report (below).
- **Power:** LEDs (the R35S LED node is disabled in stock too) and rumble
  not done. No CPU overclock (deferred).
- **Audio:** step 2 T3: no sound at the end of an agent session (charging,
  sink at muOS volume 10), back after a reboot; logs gone, cause unknown
  (quiet volume 10 vs the known start failure). Half-rate PCM after reboot (not seen in 28 probed reboots);
  the WirePlumber "no profile" start failure is retried, not explained;
  3–8 underrun bursts per game; help WAVs inaudible.
- **Content:** only libretro cores in `/opt/muos/share/core` (fceumm,
  gambatte, gpsp, pcsx_rearmed, picodrive, snes9x2005_plus); `ext-*`
  launchers are refused. PSX uses the user's BIOS (p3 `MUOS/bios`,
  `scph550{0,1,2}.bin`; private, never in an image). ROMs go to p3
  `ROMS/<DIR>` by SFTP or `rom-push.sh`.
- **Frame pacing (M3d steps 1–2):** per-system governor from
  `core-assign.txt` (folder `core.gov` seed + coredb system governor):
  PSX and 32X `performance` (CPU 1296 MHz, GPU floor 520 MHz, DDR
  performance, deep idle off), the 8/16-bit systems and GBA `schedutil`
  (same smoothness at T2, ~17% less current); the menu keeps schedutil.
  Per folder or game: muOS Content Options → Governor. Volume/brightness
  keys boost for 2 s (`muos-boost`). Waking resumes the game only after
  the Wi-Fi radio is up (~3 s paused). Remaining:
  - *Volume/brightness in game* (fixed in M3d step 3, T2): 0 frames
    > 25 ms per 14 s of presses on NES/schedutil (vol 3–6 at 20–23 ms,
    bright 0–2); was 46–53 / 10–35. In game muxretro draws its own level
    bar (plain panel, bar and recoloured theme glyph; the pause menu keeps
    upstream's LVGL bar); volume steps go through `muos-volumed` (resident
    `pw-cli`, started on the first press; the first press after boot uses
    upstream `audio.sh`).
  - *Wake:* one 80–95 ms frame ~4 s after resume while the 8821cu associates
    (`RTW_CMD_THREAD`).
  - *PSX (CTR intro cutscene):* 56–59 fps for ~20 s, CPU/GPU-thread bound,
    not I/O.
  - The DDR devfreq isn't synced to the display (no `vop-bw-dmc-freq` in the
    DT): with performance DDR switches only at game start/exit; schedutil
    games keep `dmc_ondemand`, so DDR may switch mid-game (no flash seen
    at T2; 0–1 missed vsyncs per 45 s).
- **U-Boot messages** (which record failed and why) go to the serial
  console and the LCD only; there is no log on the card.
- **p1** still holds the Phase 4 `DIAG*` folders (about 1 MiB).
- **muxretro** is built from source since M3d step 3
  (`port/scripts/build-muxretro.sh`: the Phase 4 provider source +
  `port/patches/muxretro/*.patch`, against the M3a sysroot; reproducible
  byte for byte) and pinned as an input from `build/m3d/muxretro/tree`.
  The provider's `provenance.json` in the image still describes the
  Phase 4 binary.
- **Pinned, not rebuilt:** the muOS frontend binaries (libui, libmuxcom
  and the modules), the cores, kernel modules and the tuned `/opt/muos` config are prebuilt
  inputs (`firmware-inputs.json`), copied byte-identical from the live
  p2's host build outputs; Buildroot rebuilds the rest. The kernel
  modules are pinned too; `build-boot.sh kernel` proves them valid
  (`Module.symvers` unchanged). The idbloader and trust come from the M2
  image (vendor blobs).
- **Trial root:** p3 can't be unmounted at shutdown while the trial root
  runs from it, so the next boot replays p3's journal (S89 e2fsck handles
  it).
- **Wi-Fi:** inserting the dongle during boot is unqualified. Bluetooth is
  blacklisted.
- **Licences:** Mali r13p0, DDR/miniloader/BL31/BL32, the dirty U-Boot,
  Gambatte and BT firmware are private-only
  (`port/packaging/pending-licenses.json`).

## Open decisions

1. **Licences / redistribution** and **3. public image identity:** proposed
   as M4 in [roadmap.md](roadmap.md#m4-proposal-first-public-image-2026-11-12-not-started)
   (the Mali r13p0 userspace is the blocker).
2. **Kernel base:** reassessed 2026-11-12 (roadmap.md): keep the rk351 4.4
   BSP; dArkOSen's announced 5.10 keeps the same blobs and has no public
   RK3326 source yet; a mainline/Panfrost port is the licence-clean path
   (M5 candidate).
4. **CPU overclock** (1512 MHz DTB via `make-dtb-opp.sh`, deferred by the
   user 2026-11-11): the remaining PSX cutscene dip is CPU-bound; the user
   decides whether to try it as a trial kernel.

## M3 plan — real usage and a reproducible boot chain

M3 is split into sub-milestones; each ends with its own T3.

**M3a** (reproducible image + e2fsck), **M3a.1** (audio fix), **M3b**
(boot chain) and **M3c** (ROM library) are done; plans and results in
milestones.md.

**M3d — smoothness + robustness** (planned and started 2026-11-12). Goal: no
visible slowdowns in normal play (the user's bar for the final build), then
robustness for long use.
1. **Stalls found in M3c T3** (done, T3 passed 2026-11-12; milestones.md):
   `muos-governor` (CPU governor + GPU floor, deep idle, DDR), wake after
   the radio is up, panel timing 60.0046 Hz, the user's PSX BIOS.
2. **Battery % + per-system profiles** (done 2026-11-13: 4–6 OK; battery
   re-test: boot jumps → patch 0003, T2-passed; cold boot left for T3):
   - Kernel `port/patches/kernel/0001` (applied by `build-boot.sh kernel`
     to a reflinked `build/m3b/linux-src`): `capacity` = the RK817 fuel
     gauge instead of the voltage-only hack (hardware-findings "Battery %").
     Main kernel `Image-48b6fc61382f`.
   - Governor per system (`core-assign.txt` 5th column → folder `core.gov`
     seed, S91 one-shot migration `system-governor`, coredb system
     governor at image post-build): PSX/32X performance, the rest
     schedutil (current per system: hardware-findings "Battery current").
   - `muos-boost`: volume/brightness keys raise CPU and GPU floors and turn
     deep idle off for 2 s under schedutil (post-build wraps the pinned
     `audio.sh`/`bright.sh`). Level test on NES (schedutil): vol 58.1 →
     59.0–59.3 fps, bright 58.8 → 59.8–59.9 (performance: 59.8 / 59.9).
   - Fix after T3: kernel patch 0002 (boot sanity check: dsoc vs coulomb
     SOC, tie-break by voltage; `muos-gauge:` boot log) and the
     `muos-lowbattery` voltage guard. T2: the card's broken state (dsoc 5%,
     counter 100%) was corrected on the trial boot (`dsoc 5017 -> coulomb
     100034`); a normal boot logs no correction; 2 in-game sleep cycles;
     the guard ignores 0% at 4.1 V and powers off at 3.4 V (host test).
   - muxretro has its own governor boost (content startup, "sustained
     frame misses", state save: `scaling_governor` → performance for a
     while); `muos-governor` records the port profile in
     `/run/muos/governor.active` so `muos-boost` isn't confused by it.
3. **Volume/brightness judder** (done 2026-11-13, T2; T3: the bar's look):
   muxretro from source (`build-muxretro.sh`), patches 0001 (per-frame
   `slow_frames` stage trace) and 0002 (in-game level bar drawn by
   muxretro), WirePlumber `state.restore-props = false` on the sink
   (post-build installs `core-wireplumber.conf`), `muos-volume-step` +
   `muos-volumed`. Gate: `t2-level-fps.sh --max-slow 6 --max-missed 0`
   (vol 3, bright 1, 0 missed); 2/2 in-game sleep cycles.
4. **Remaining stalls:** the wake hitch during 8821cu association, CTR's
   race start/end (T3) and cutscene dips (pcsx_rearmed GPU-thread mode,
   muxretro threaded run; the overclock is the user's call).
5. **Robustness (the original M3d):** p3 auto-grow on first boot, log
   rotation, the battery gauge over a full discharge (low-battery
   shutdown, re-seed after a dead battery), the 559 mA menu idle
   (backlight, Wi-Fi power save), audio half-rate/underruns, the
   WirePlumber "no profile" failure.
6. **Long run:** 1–2 h of play, 20 reboot/poweroff cycles; M3d image
   (includes the step 2 kernel and post-build); recovery image → M3d.

T2 hygiene: `t2-sleep-cycle.sh --game` now uses the NES test game with
the pickles snapshot (it used to rewrite the user's `private.gb` autosave).
