# Project status

Update at the end of every milestone. Finished milestones (results,
checklists) are in [milestones.md](milestones.md). See also
[hardware-findings.md](hardware-findings.md), [roadmap.md](roadmap.md),
[compatibility-matrix.md](compatibility-matrix.md) and
[storage.md](storage.md). The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## Current phase

**Phase 5 (own-card firmware). M1, M2 and M2.1 are done (T3 passed
2026-11-10/11). M3a's T3 (2026-11-11): the built image flashes and boots,
but every boot was silent (SDL2 built without its pipewire driver).
M3a.1 fixes that and passed T0–T2 on 2026-11-11; its p2 is on the card,
and its T3 is at the end of this file.** Results: milestones.md M3a, M3a.1.

## Device and bench

- **Device:** R35S Panel 0, test128 in slot 1, flashed with the M3a image
  (p3 grown to the whole card, M2-era data). p2 is the M3a.1 build (p2
  sha256 `1b3995a2…`), written from the trial root. The previous p2 (the
  silent M3a one, as mounted) is on p3 at `MUOS/trial/p2-previous.img`
  until the M3a.1 T3 passes.
  - The DHCP IP changes between boots; it was 192.168.15.8.
  - Identify the device by its host key, not its IP:
    `SHA256:fDW+/iNaWgqPwqBtO/ESuKPSQHvYN1PSo2RHfilOxK0`.
  - Identify a boot by `/proc/sys/kernel/random/boot_id`.
- **Access:** `port/scripts/device.sh` locates the device by fingerprint:
  `find`, `id`, `run CMD`, `sh`, `push`, `pull`, `reboot` / `poweroff`
  (both through init), `capture DIR`.
- **test128 layout** (disk ID `4d554432`, 249872384 sectors):
  - Bootloader at sectors 64 / 16384 / 24576.
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
or share them. **M2 stays the known-good recovery image** until M3a.1
passes its T3 (sound on 3 boots).

| Image | Content | Boots on |
|---|---|---|
| `dist/firmware/test128-m3a1-20261111.img.zst` (raw `112db539…`) | M3a.1: M3a + SDL2 with its pipewire driver; p2 on the card, image not yet flashed | any card ≥ 2 GiB (expected) |
| `dist/firmware/test128-m3a-20261111.img.zst` (raw `2ac44673…`) | M3a: flashed once (boots, `--grow` OK) but **silent**; retire after the M3a.1 T3 | any card ≥ 2 GiB |
| `test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: + sleep, battery, headphones, NES core | any card ≥ 2 GiB |
| `test128-m1-20261110.img.zst` (raw `1c65c693…`) | M1: autostart, seedless | any card ≥ 2 GiB |
| `test128-baseline-20261110.img.zst` (raw `9c1c8a37…`) | pre-M1 C07 init, SSH only | test128 only (CID-locked bootstrap), slot 2 empty |

**Flash via dArkOSen:**
1. Power off. Put original32 in slot 1 and the target card in slot 2.
   Boot, join Wi-Fi, and enable Remote services (Options).
2. On the host:
   `port/scripts/flash-card.sh darkosen <dArkOSen-IP> dist/recovery/test128-m2-20261111.img.zst --grow`
   - Enter the `ark` SSH password once and the sudo password once.
   - The script refuses the running root and too-small cards, unmounts
     slot 2, writes, re-reads and verifies the SHA256, then grows p3.
3. Power off. Move the card to slot 1, leave slot 2 empty, power on.

**Flash with a host card reader** (once it arrives):
`port/scripts/flash-card.sh host /dev/sdX <image> --grow`. Check `/dev/sdX`
with `lsblk` first.

**Build the firmware** (M3a; about 50 min from scratch, minutes
incrementally, in `build/m3a/output`):
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
   `check-rootfs-contract.sh` on the p2 image).
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

**Risky init changes** to inittab, rc or the shim: arm a trial boot.
1. Copy the known-good inittab to `/etc/inittab.fallback`.
2. Install the change, `touch /etc/muos-boot-trial`, reboot.
3. Confirm by deleting `/etc/muos-boot-trial.used`.

If SSH never comes back, a long-press power cycle boots
`inittab.fallback` instead of needing a reflash.

## Boot and runtime

U-Boot boots `init=/sbin/muos-ext4-diag`, a shim that runs BusyBox init,
which runs `/usr/libexec/muos-rc start`:

| Step | Service | What it does |
|---|---|---|
| 1 | stock `seedrng`, syslog, sysctl, `udev`, D-Bus | standard Buildroot services |
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
  idles at 1008 MHz. No overclock: the port U-Boot pins the size and
  SHA256 of `Image` and the DTB (M3b).

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
| Never `saveenv` or dArkOSen `flash_uboot.sh`; never write original32 | Protects the bootloader and the stock card. |
| ≤ 5 firmware versions (`retention.py`) | Host disk space. |

The M1 retirements are listed in milestones.md. M3a retired 410 Phase 4
scripts (in Git at `e7d67a2`); 48 remain: the live tools, the producers
of the pinned inputs, and the kernel/U-Boot/DTB tooling for M3b.

## What works (T3-confirmed)

Display, all controls, frontend and submenus, volume and brightness,
speaker audio on every boot (M2.1; M3a regressed it, M3a.1 T3 pending),
Wi-Fi + SSH, prefs persistence; GB (Gambatte)
and NES (fceumm, SMB3 at 59.9 fps) with saves and states; autostart, menu
reboot/shutdown, hard power cut recovery; physical Power key sleep/resume
in menu and game, shutdown timer, charging fake sleep; battery icon, %,
charging icon; headphone path switching.

## Broken, caveated or unverified

- **Headphones:** per-output volume confirmed only at T2 (simulated jack);
  the T3 plug was in the undetected half-inserted position. A full
  insertion is quieter: hardware (codec registers are identical on both
  paths).
- **Battery gauge:** jumps from 84% to 100% within about 20 s of plugging
  the charger (RK817 BSP gauge estimate). After a full discharge, a boot
  with the charger in showed 91%, and the kernel said `capacity=100` at
  4.112 V / 1.4 A charge current 13 min after boot: the PMIC loses its
  coulomb-counter state when the battery dies and re-seeds SOC from the
  charge-inflated voltage. `mubattery` only displays the kernel value.
  Calibration → M3d.
- **Power:** LEDs (the R35S LED node is disabled in stock too) and rumble
  not done. No CPU overclock (M3b).
- **Audio:** half-rate PCM after reboot (not seen in 28 probed reboots);
  the WirePlumber "no profile" start failure is retried, not explained;
  3–8 underrun bursts per game; help WAVs inaudible.
- **Content:** only libretro cores in `/opt/muos/share/core` (gambatte,
  fceumm); `ext-*` launchers are refused. ROMs are copied to p3
  `ROMS/<system>` by hand (`port/scripts/install-nes.sh` for
  `port/roms/nes`).
- **M3a.1 image not yet flashed:** its p2 was written in place. The M3a
  image proved the build's prefix/p1/p3 and `--grow` path; M3a.1 differs
  only in p2.
- **Headphones (fully inserted) not re-tested:** M3a was silent.
- **Pinned, not rebuilt:** the muOS frontend binaries, muxretro, the
  cores, kernel modules and the tuned `/opt/muos` config are prebuilt
  inputs (`firmware-inputs.json`), copied byte-identical from the live
  p2's host build outputs; Buildroot rebuilds the rest. U-Boot, the
  kernel `Image` and the DTB on p1 still come from the M2 card (M3b).
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

M3 is split into sub-milestones; each ends with its own T3. Kernel
changes (`HW_RANDOM_ROCKCHIP`, anything in `Image`/DTB) need M3b, because
the port U-Boot pins the size and SHA256 of `Image` and the DTB.

**M3a — reproducible image + e2fsck** (done at T2 2026-11-11, T3 pending;
the plan as executed, see milestones.md for results):
0. **Disk first.** Review and retire old `build/phase4` outputs
   (`retention.py retire` dry run first) and check `podman system df`
   before the Buildroot build.
1. **Inventory.** List every p2 file on the device (path, mode, size,
   sha256) and classify it: Buildroot package, port `rootfs/`, prebuilt
   input (kernel modules, Mali r13p0, Wi-Fi firmware, frontend, muxretro,
   cores), or legacy C-step leftover (dropped).
2. **One build.** `port/scripts/build-image.sh` in the existing
   `phase4-rootfs` container, reusing `build/phase4/buildroot` and its
   download cache:
   - `port/device/rk-r35s-p0/firmware.defconfig` = the phase4 graphics +
     network config + e2fsprogs (e2fsck, resize2fs); i2c-tools dropped
     (BusyBox `i2cget` is used);
   - only the live BR2_EXTERNAL packages (muos-core, muxretro, wifi-only,
     ...); the legacy C-step packages (launcher-once, save-store,
     session, boot) are dropped;
   - `BR2_ROOTFS_OVERLAY` = `port/device/rk-r35s-p0/rootfs`;
   - prebuilt inputs pinned by SHA256 in
     `port/packaging/firmware-inputs.json`;
   - post-image: the full card image in the test128 layout (bootloader at
     64/16384/24576, p1 FAT, p2 ext4 with 4.4-safe features, p3 1 GiB)
     plus `.sha256` and `.manifest`, as `make-recovery-image.sh` does.
3. **S89 runs `e2fsck -p` on p3** before mounting it (time-bounded;
   result logged to p3). A "needs manual fsck" result still mounts p3 so
   the UI comes up, and the problem is reported in the log.
4. **T1.** Inventory diff of the new rootfs against the live p2 (every
   difference explained), ELF/ldd resolution under qemu, fsck of the
   image.
5. **T2 without risking the card.** The shim (`/sbin/muos-ext4-diag`)
   gets a one-shot "trial root": if `/etc/muos-root-trial` exists, it
   consumes the marker, loop-mounts p3 `MUOS/trial/rootfs.img` read-only
   and `pivot_root`s into it (BusyBox `switch_root` refuses a non-tmpfs
   root). A hang or failure → power cycle → normal p2. The branch is only
   reachable through the marker and is tested in a container first. That
   boot must pass `t2-menu-cycle.sh`, `t2-sleep-cycle.sh`,
   `t2-headphone.sh` and the audio probe. Then, from inside the trial
   root (p2 unmounted), the agent writes the new p2, reads it back and
   verifies the SHA256. The old p2 image stays on p3 until T3 passes.
6. **Collapse the chain.** Retire the prepare/package/compose scripts and
   C-step checks that `build-image.sh` doesn't use (they stay in Git).
7. **T3:** flash the built image via dArkOSen (proves it is a recovery
   image), boot, short play session, battery %/charging, and the
   per-output volume retest with the plug fully inserted.

**M3b — boot chain:** rebuild U-Boot without the `Image`/DTB pin (or
re-pinned from the build); write it from a verified image, with the
dArkOSen flasher as the recovery path. Then `HW_RANDOM_ROCKCHIP` and, if
content needs it, the 1512 MHz OPPs (`port/scripts/make-dtb-opp.sh`).

**M3c — ROM library:** a ROM copy path (sftp over the existing dropbear
first, then Samba or FAT-partition import), SRAM saves per system, more
libretro cores as needed.

**M3d — robustness:** p3 auto-grow on first boot, log rotation, battery
gauge calibration (incl. the SOC re-seed after a full discharge: e.g.
hold the displayed % while the charge current is high, or re-seed from
an IR-compensated voltage), the audio half-rate/underruns and the WirePlumber "no
profile" failure; then a long run (1–2 h of play, 20 reboot/poweroff
cycles).

## M3a.1 T3 checklist (for the user)

The card already runs the M3a.1 p2 (no reflash needed). Charger in or out
as you like.

1. **Sound on 3 boots:** power off fully (menu Shutdown), power on; repeat
   three times. Each time, in the menu, move the cursor (navigation
   sounds), then start a GB or NES game and play ~30 s.
   - Expected: menu sounds and game sound from the speaker on all 3 boots;
     the volume keys change the level.
2. **Headphones, plug fully inserted** (the M2.1 item 4 retest):
   1. Start a game, push the plug all the way in: the speaker goes silent
      and the sound is in the headphones (possibly quieter).
   2. Set a headphone volume clearly different from the speaker's, unplug.
   - Expected: the speaker comes back at its own level; plug in again:
     the headphone level is back.
   - Also tell me: with the plug only half in, does the speaker keep
     playing too?
