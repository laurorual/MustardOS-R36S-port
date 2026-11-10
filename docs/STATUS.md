# Project status

Update at the end of every milestone. See also
[hardware-findings.md](hardware-findings.md), [roadmap.md](roadmap.md),
[compatibility-matrix.md](compatibility-matrix.md) and
[storage.md](storage.md). The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## Current phase

**Phase 5 (own-card firmware) is in progress. M1 is done (2026-11-10).**

M1 delivered three things:
- a flashable recovery image,
- a device that boots straight into the muOS frontend through standard
  BusyBox rcS/rcK-style init,
- the retirement of the C-step safety harness.

All checks passed at T0–T2. The M1 T3 checklist is pending; see the end of
this file.

## Device and bench

- **Device:** R35S Panel 0, test128 in slot 1, running the M1 init.
  - The DHCP IP changes between boots; it was 192.168.15.8.
  - Identify the device by its host key, not by its IP:
    `SHA256:fDW+/iNaWgqPwqBtO/ESuKPSQHvYN1PSo2RHfilOxK0`.
  - Identify a boot by `/proc/sys/kernel/random/boot_id`.
- **Access:** use `port/scripts/device.sh`. It locates the device by
  fingerprint, so no IP is needed:
  - `find`, `id`, `run CMD`, `sh`, `push`, `pull`
  - `reboot` / `poweroff`, both through init
  - `capture DIR`
- **test128 layout** (disk ID `4d554432`, 249872384 sectors):
  - Bootloader at sectors 64 / 16384 / 24576.
  - p1: FAT `MUOSDIAG`, 16 MiB+100 MiB, mounted ro at `/boot`.
  - p2: ext4 root, 128 MiB+512 MiB, ro at runtime.
  - p3: ext4 `MUOSDATA`, from 640 MiB to the end, rw at `/userdata`. In
    images it is 1 GiB; `--grow` extends it.
- **original32 (stock dArkOSen):** the flasher station, used in slot 1
  with the target card in slot 2. Never write original32 itself.

## Recovery images and flashing

Both images are in `dist/recovery/`, each with `.sha256` and `.manifest`.
**They are private:** they contain the Wi-Fi PSK, the SSH host key and
authorized_keys. Never commit or share them.

| Image | Content | Boots on |
|---|---|---|
| `test128-m1-20261110.img.zst` (raw `1c65c693…`) | M1: autostart, seedless | any card ≥ 2 GiB |
| `test128-baseline-20261110.img.zst` (raw `9c1c8a37…`) | pre-M1 C07 init, SSH only | test128 only (CID-locked bootstrap), slot 2 empty |

**Flash via dArkOSen**, the current method:
1. Power off. Put original32 in slot 1 and the target card in slot 2.
   Boot, join Wi-Fi, and enable Remote services (Options).
2. On the host, run:
   `port/scripts/flash-card.sh darkosen <dArkOSen-IP> dist/recovery/test128-m1-20261110.img.zst --grow`
   - Enter the `ark` SSH password once and the sudo password once.
   - The script refuses the running root and too-small cards, unmounts
     slot 2, writes the card, re-reads it and verifies the SHA256, then
     grows p3.
3. Power off. Move the card to slot 1, leave slot 2 empty, and power on.

**Flash with a host card reader**, once it arrives:
`port/scripts/flash-card.sh host /dev/sdX <image> --grow`. Check `/dev/sdX`
with `lsblk` first.

**Build a new image:**
1. `device.sh capture build/recovery/capture-<name>`. It quiesces the UI
   and p3 first; reboot afterwards.
2. `port/scripts/make-recovery-image.sh --strip-seed build/recovery/capture-<name> dist/recovery/<name>.img.zst`
3. `port/scripts/retention.py add <name> "<reason>" <files>`

**Risky init changes** to inittab, rc or the shim: arm a trial boot first.
1. Copy the known-good inittab to `/etc/inittab.fallback`.
2. Install the change, then `touch /etc/muos-boot-trial`, then reboot.
3. Confirm by deleting `/etc/muos-boot-trial.used`.

If SSH never comes back, a long-press power cycle boots
`inittab.fallback` instead of needing a reflash.

## Boot and runtime (M1)

U-Boot boots `init=/sbin/muos-ext4-diag`. That is now a shim that runs
BusyBox init, which runs `/usr/libexec/muos-rc start`. The service order
is:

| Step | Service | What it does |
|---|---|---|
| 1 | stock `seedrng`, syslog, sysctl, `udev`, D-Bus | standard Buildroot services |
| 2 | **S41muos-network** | Wi-Fi and dropbear on :2222, in the background; up at about 20 s |
| 3 | **S85** | root ro |
| 4 | **S89** | p3 rw at `/userdata`, p1 ro at `/boot` |
| 5 | S90 | muOS storage binds |
| 6 | **S91** | persistent muOS config and core assignments on p3 (`MUOS/port`); tmpfs views for the other paths muOS writes |
| 7 | S95 | audio + muinput (audio failure stays non-fatal for input) |
| 8 | S96 | input mapping |
| 9 | **S99** | UI frontend loop |

The menu is on screen about 15 s after power-on.

Content runs in muxretro: Explore → `ROMS/GB` → gambatte. Saves and states
are written to p3 `MUOS/pickles`. The launcher's Reboot/Shutdown actions
and `device.sh reboot` run `muos-rc stop`, which stops UI → input → core →
runtime → storage → p3 in about 2 s. The log is in `/run/muos-rc.log`,
and the last shutdown's copy is in p3 `MUOS/log/rc-last.log`.

Source lives in `port/device/rk-r35s-p0/rootfs/`; the init scripts are
symlinks to the files Buildroot also uses. To deploy:
`port/scripts/install-rootfs.sh [paths]`. It installs atomically and
keeps the first original in `/var/lib/muos-m1-backup`. `--restore` undoes
the changes.

**Safe mode:** create `/boot/muos-noui` on the FAT partition and the UI
is skipped; SSH still comes up.

## The seed (investigated in M1)

The "seed" was the SeedRNG entropy file (`/var/lib/muos-seedrng/seed.*`).
It was created by Buildroot's seedrng through the C05 `S05muos-entropy`
wrapper.

- **What depended on it:** only the "RNG ready" gate. The network script
  refused to start until it was set, so that the dropbear host key would
  be generated with a ready RNG. Readiness takes about 7–11 s, because the
  4.4 kernel has no HW RNG.
- **What the "never replay" rule protected:** RNG freshness across p2
  restores. That doesn't matter on a dev card.
- **Decision:** retire the gate and the wrapper.
  - Stock seedrng still runs.
  - Images ship without `seed.*`, so each card creates its own at first
    boot (tested in M1).
  - The dropbear host key is the only persistent identity. It stays in
    the image so the fingerprint survives a reflash.
  - For a public image, drop the key; the worker then generates one on
    first boot. Enabling `HW_RANDOM_ROCKCHIP` (M3) would make seedrng
    unnecessary.

## Safety mechanisms: kept or retired

**Kept, because they still protect something:**

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

**Retired in M1:**
- **Card/CID guards:** the C01/C07 bootstrap and `card-guard.sh`. They
  broke every flashed copy, and halted when original32 was in slot 2.
- **Marker files:** `/etc/muos-*-diagnostic`, `/etc/muos-private-foundation`,
  `DIAG.ID` checks.
- **boot-seq counter and `.once` tokens:** `/var/lib/muos-diagnostic`.
- **Consumed claims:** these were host-only.
- **Hash guards:** foundation-89, "guard 200", the resident/batch
  manifests, and the hash-pinned retention dependency trace.
- **Seed/counter anti-replay and "never write test128".**
- **Device payloads removed:** the C01–C25 dispatchers, capsules,
  caller, batch and resident packages, the UI supervisor, MUOSSAV1
  `muos-save-store`, `S05muos-entropy` and `S98muos-session`. A tar is on
  p3 at `MUOS/port-legacy-c07.tar`, and the baseline image keeps them all.
- **Host:** 223 one-off C-step scripts and fixtures (analyze, audit,
  check, collect, finish, run, ...). They stay in Git at `ea2f7d8`.

The other ~480 scripts in `port/scripts` remain. They are the
prepare/package/compose chain that stages the Buildroot package sources,
and the C-step checks that chain still references. Collapsing them is
part of M3.

## What works

**Confirmed by the user (T3) before M1:**
- display, all controls, frontend and submenus, volume and brightness
- speaker audio
- Wi-Fi + SSH
- prefs persistence
- Game Boy (Gambatte) with save states
- NES, but slow (51.4 fps)

**M1, automated on the device (T2):**
- **Boot:** autostart to the menu on more than 15 boots of the new init,
  one of them seedless, with rcS done at about 15 s.
- **Game cycle:** `port/scripts/t2-menu-cycle.sh` passed 4 times in full. It drives
  the real buttons by evdev injection (`/usr/libexec/muos-press`):
  - menu → Explore → GB → private.gb running at 59.73 Hz
  - Fn+R2 quick save (to p3) and Fn+L2 quick load
  - Fn+Start → back to Explore
  - launcher Reboot → ordered rcK → p3 clean → state persisted → menu
- **Prefs:** 55/70 imported into the persistent config.
- **Degraded audio:** if audio fails to start, the menu still works
  without sound.
- **Panel timing:** measured; see hardware-findings.
- **T0/T1:**
  - shellcheck on all new scripts
  - container tests for the installer, the trial boot, the frontend loop
    and the file-target flash
  - fsck and content checks of both images
  - a p3 grow test
  - AST import check of all 425 kept Python files

## Broken, caveated or unverified

- **Not exercised by hand yet (T3 pending):**
  - flashing an image
  - a true cold boot from power-off
  - physical poweroff
  - the menu Shutdown entry. It uses the same path as Reboot, but
    nothing powered the device back on to check it.
- **Power:** Power key, suspend (`/sys/power` is bound ro), battery and
  charging, LEDs and rumble are untested. The muOS battery device config
  files are missing.
- **Audio:**
  - half-rate PCM after reboot (root cause unknown)
  - 3–8 underrun bursts per game
  - help WAVs inaudible
  - headphones untested
- **CPU governor:** frontend and muxretro writes to the cpufreq governor
  fail, because the cpufreq tree is bound ro. The DTB caps the CPU at
  1296 MHz.
- **Unsupported content:** only libretro cores in `/opt/muos/share/core`
  are supported (only gambatte is installed); `ext-*` launchers are
  refused. The NES core is not installed. There is no general ROM import
  path beyond copying files to p3 `ROMS/<system>`.
- **Missing on the device:** e2fsck. The p3 journal covers unclean
  shutdowns, but no fsck ever runs on the device.
- **Rebuild:** the rootfs on the card is the C94 composition patched in
  place by M1. The M1 changes are in Git (`rootfs/` plus install), but a
  from-scratch Buildroot image hasn't been rebuilt or booted.
- **Wi-Fi:** inserting the dongle during boot is still unqualified.
  Bluetooth is blacklisted.
- **Licences:** Mali r13p0, DDR/miniloader/BL31/BL32, the dirty U-Boot,
  Gambatte and BT firmware are still private-only
  (`port/packaging/pending-licenses.json`).

## Open decisions

1. **Licences / redistribution:** unchanged.
2. **Kernel base:** rk351 4.4 BSP vs a ROCKNIX fallback. Not revisited.
3. **Public image identity:** drop the host key and Wi-Fi config from a
   shareable image, and add first-boot Wi-Fi setup.

## Contradictions resolved in M1

- **Panel timing:** the port DTB is 29 MHz / 732×661 / 59.94 Hz
  (measured three ways). The stock dArkOSen DTB is 50 MHz / ≈61.2 Hz.
  The two docs described different DTBs.
- **Phase 5:** the roadmap now marks Phase 4 done and Phase 5 in progress.
- **Warm Wi-Fi:** fixed since C18. The "replug needed" notes in the
  archive are historical.
- **C123 guard:** obsolete, because the guards were retired.

## Proposed next milestones

**M2 — Power and battery:**
- **Power key** (`rk8xx_pwrkey`, event0): short press → suspend (or
  screen off), long press → clean poweroff through init.
- **Suspend/resume:** unbind `/sys/power`, then qualify suspend and
  resume, including Wi-Fi and SSH recovery and audio after resume.
- **Battery:** RK817 gauge → muOS battery config (`capacity`, `charger`,
  `voltage`). Charging indication, low-battery warning and auto-poweroff,
  and the charge LED (GPIO77).
- **Headphones:** jack switching and volume (event1).
- **Power-loss test:** pull the battery or power during a save, then check
  p3 recovery. Add e2fsck to the rootfs and run it on p3 at boot.
- **T3:** Power key behaviour, suspend/resume, battery % against the
  charger, headphones.

**M3 — Real usage:**
- **ROM library:** browse ROMs in `ROMS/<system>` with SRAM saves, and
  install the NES core with O3/LTO (target 60 fps). Optionally add a
  simple ROM copy path: Samba/sftp over Wi-Fi, or the FAT partition.
- **Reproducible image:** build the full image from Buildroot plus
  `rootfs/`, with no in-place patching, then boot and flash it.
  Collapse the prepare/package chain and retire the remaining C-step
  scripts.
- **Robustness:** auto-grow p3 on first boot, log rotation, and
  `HW_RANDOM_ROCKCHIP`. Fix the audio half-rate and underruns.
- **Long run:** 1–2 h of play, plus 20 reboot/poweroff cycles.
- **T3:** a real play session, ROM import, and long-run stability.

## M1 T3 checklist (for the user)

1. **Flash the M1 image** using the dArkOSen steps above, on test128.
   - Expected: `verified raw_sha256=1c65c693…` and `p3 grown and clean`.
2. **Cold boot:** power off for more than 10 s, then power on.
   - Expected: the muOS menu appears without any SSH step, in about
     15–25 s.
   - Then tell me, and I confirm Wi-Fi/SSH with `device.sh find`.
3. **Game round:** Explore → GB → private, then:
   1. Play a bit.
   2. Fn+R2 to save.
   3. Move on in the game, then Fn+L2 to load.
   - Expected: it returns to the saved point.
   - Fn+Start → back to the list. B → menu.
4. **Reboot from the menu:** Reboot → Yes.
   - Expected: back in the menu, the volume and brightness are unchanged.
   - Load the GB state again (Fn+L2 in-game). It should still be there.
5. **Shutdown from the menu:** Shutdown → Yes.
   - Expected: the screen goes off within about 5 s.
   - Power on again: the menu comes back.
6. **Optional:** Power key presses (expected: nothing happens yet), and
   speaker sound in the menu and in the game.
