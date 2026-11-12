# Project status

Update at the end of every milestone. Finished milestones (results,
checklists) are in [milestones.md](milestones.md). See also
[hardware-findings.md](hardware-findings.md), [roadmap.md](roadmap.md),
[compatibility-matrix.md](compatibility-matrix.md) and
[storage.md](storage.md). The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## Current phase

**Phase 5 (own-card firmware). M1–M3b are done. M3b (boot chain built
from source, boot-record U-Boot with a one-shot trial kernel, TRNG)
passed T3 on 2026-11-11: 3 cold boots, then a flash of the M3b image
with the host card reader. The M3b image is the recovery image. Next:
M3c (ROM library), plan at the end of this file.** Results: milestones.md.

## Device and bench

- **Device:** R35S Panel 0, test128 in slot 1, flashed with the M3b
  image on 2026-11-11 (host card reader, p3 grown to the whole card).
  Boot records: main = M3b kernel (`Image-ab18bba307f8`,
  `panel0-496bbe3591f8.dtb`), previous = M2 kernel (`Image`,
  `rk3326-muos-r35s-panel0.dtb`).
  - p2 differs from the image only by `/usr/libexec/muos-press` (test
    helper with volume keys; `install-rootfs.sh`, original kept).
  - Saves: the pre-flash `pickles` were restored from
    `build/m3b/p3-backup` (byte-identical); the post-flash ones are kept
    in `build/m3b/p3-postflash`.
  - The DHCP IP changes between boots; it was 192.168.15.8.
  - Identify the device by its host key, not its IP:
    `SHA256:fDW+/iNaWgqPwqBtO/ESuKPSQHvYN1PSo2RHfilOxK0`.
  - Identify a boot by `/proc/sys/kernel/random/boot_id`.
- **Access:** `port/scripts/device.sh` locates the device by fingerprint:
  `find`, `id`, `run CMD`, `sh`, `push`, `pull`, `reboot` / `poweroff`
  (both through init), `capture DIR`.
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
or share them. **Recovery image: M3b** (flashed and T3-passed
2026-11-11). M3a.1 and M2 stay as fallbacks with the M2 U-Boot. Flashing
any image rewrites the whole card, bootloader included.

| Image | Content | Boots on |
|---|---|---|
| **`dist/firmware/test128-m3b-20261111.img.zst`** (raw `2a8fec32…`) | **Recovery image.** M3b: boot-record U-Boot, M3b kernel (main) + M2 kernel (previous), M3b p2 | any card ≥ 2 GiB |
| `dist/firmware/test128-m3a1-20261111.img.zst` (raw `112db539…`) | M3a.1: M2 U-Boot and kernel, SDL2 with its pipewire driver; p2 T3-passed, image never flashed | any card ≥ 2 GiB (expected) |
| `test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: + sleep, battery, headphones, NES core | any card ≥ 2 GiB |
| `test128-m1-20261110.img.zst` (raw `1c65c693…`) | M1: autostart, seedless | any card ≥ 2 GiB |
| `test128-baseline-20261110.img.zst` (raw `9c1c8a37…`) | pre-M1 C07 init, SSH only | test128 only (CID-locked bootstrap), slot 2 empty |

**Flash with the host card reader (primary, since 2026-11-11):**
1. Power the device off and put its card in the USB reader on the host.
2. `lsblk -dno NAME,TRAN,SIZE,MODEL` (the reader shows `usb`, about 119 GiB
   for test128).
3. `port/scripts/flash-card.sh host /dev/sdX dist/firmware/test128-m3b-20261111.img.zst --grow`
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
   `port/scripts/flash-card.sh darkosen <dArkOSen-IP> dist/firmware/test128-m3b-20261111.img.zst --grow`
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
- **cpufreq:** muOS per-content governors; default `schedutil`, the menu
  idles at 1008 MHz. No overclock (deferred by the user 2026-11-11; a
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
- **Battery gauge:** jumps from 84% to 100% within about 20 s of plugging
  the charger (RK817 BSP gauge estimate). After a full discharge, a boot
  with the charger in showed 91%, and the kernel said `capacity=100` at
  4.112 V / 1.4 A charge current 13 min after boot: the PMIC loses its
  coulomb-counter state when the battery dies and re-seeds SOC from the
  charge-inflated voltage. `mubattery` only displays the kernel value.
  Calibration → M3d.
- **Power:** LEDs (the R35S LED node is disabled in stock too) and rumble
  not done. No CPU overclock (deferred).
- **Audio:** half-rate PCM after reboot (not seen in 28 probed reboots);
  the WirePlumber "no profile" start failure is retried, not explained;
  3–8 underrun bursts per game; help WAVs inaudible.
- **Content:** only libretro cores in `/opt/muos/share/core` (gambatte,
  fceumm); `ext-*` launchers are refused. ROMs are copied to p3
  `ROMS/<system>` by hand (`port/scripts/install-nes.sh` for
  `port/roms/nes`).
- **In-game volume/brightness change:** 2–5 dropped frames per second
  while the keys are pressed (59.9 → 58.5–59.7 fps), none at rest.
  Upstream behaviour on this SoC, not a port defect (hardware-findings.md,
  "Level-change judder"); not fixed.
- **U-Boot messages** (which record failed and why) go to the serial
  console and the LCD only; there is no log on the card.
- **p1** still holds the Phase 4 `DIAG*` folders (about 1 MiB).
- **Pinned, not rebuilt:** the muOS frontend binaries, muxretro, the
  cores, kernel modules and the tuned `/opt/muos` config are prebuilt
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

1. **Licences / redistribution:** unchanged.
2. **Kernel base:** rk351 4.4 BSP vs a ROCKNIX fallback. Not revisited.
3. **Public image identity:** drop the host key and Wi-Fi config from a
   shareable image, and add first-boot Wi-Fi setup.

## M3 plan — real usage and a reproducible boot chain

M3 is split into sub-milestones; each ends with its own T3.

**M3a** (reproducible image + e2fsck), **M3a.1** (audio fix) and **M3b**
(boot chain) are done; plans and results in milestones.md.

**M3c — ROM library** (planned 2026-11-11; in progress). Goal: the user
adds games from the PC without the agent, and more systems play.
1. **File transfer:** Buildroot `gesftpserver` → `/usr/libexec/sftp-server`,
   so dropbear serves SFTP (GUI clients, `sftp`, and OpenSSH `scp`, which
   speaks SFTP by default; today only legacy `scp -O` works). Host helper
   `port/scripts/rom-push.sh SYSTEM FILE...` (mkdir `ROMS/<dir>`, copy,
   sha256 check, refresh). Login stays key-only root on :2222.
2. **ROM folders:** create `ROMS/<dir>` for every system with a core at
   boot (S90), so the PC client shows where files go.
3. **More cores** (built in the container like fceumm/gambatte, pinned as
   inputs, core assignment + `core.gov` per system), each with a T2 fps
   check: proposed SNES (snes9x2005_plus), GBA (gpsp), Mega Drive/SMS/GG
   (picodrive), PS1 (pcsx_rearmed). Needs a user decision on the list and
   test ROMs the user owns.
4. **SRAM saves:** prove battery saves (`.srm`) land on p3 per system and
   survive quit, sleep, poweroff and a power cut (T2 with a battery ROM).
5. Deferred to after M3c: Samba, a FAT import partition (repartitioning).

T0: shellcheck, defconfig diff; T1: `sftp-server` ELF/deps, cores' ELF
and `retro_api_version` under qemu; T2: sftp/scp round trip from the
host, `rom-push.sh`, per-core fps (`t2-nes-fps.sh`-style), SRAM cycle.
p2 changes go in via the trial root; a firmware image at the end.

**M3d — robustness:** p3 auto-grow on first boot, log rotation, battery
gauge calibration (incl. the SOC re-seed after a full discharge: e.g.
hold the displayed % while the charge current is high, or re-seed from
an IR-compensated voltage), the audio half-rate/underruns and the WirePlumber "no
profile" failure; then a long run (1–2 h of play, 20 reboot/poweroff
cycles).
