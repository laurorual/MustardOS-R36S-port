# Project status

Update at the end of every milestone. See also
[hardware-findings.md](hardware-findings.md), [roadmap.md](roadmap.md),
[compatibility-matrix.md](compatibility-matrix.md) and
[storage.md](storage.md). The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## Current phase

**Phase 5 (own-card firmware) is in progress. M1 is done (2026-11-10).
M2 (power, battery, cpufreq) passed T3 on 2026-11-11 with three
failures; their fixes (M2.1) wait for a short T3 (end of this file).
M3 is planned below.**

M2 T3 results (2026-11-11, `build/t3-m2.txt`):

| # | Check | Result |
|---|---|---|
| 1–3 | Power short/long press, in menu and in game | OK |
| 4 | Shutdown timer after 10 min asleep | OK |
| 5 | Charging | PARTIAL: fake sleep OK (instant wake, dongle stayed on); no charging icon |
| 6 | Battery % | NOT TESTABLE: no battery indicator in the status bar |
| 7 | Headphones | OK polarity; **HP much quieter than the speaker** |
| 8 | NES SMB3 | OK |
| 9 | Hard power cut | OK |
| — | Observation | **No sound after the hand-over; a menu reboot didn't fix it, the hard power cut (item 9) did** |

M2.1 fixes:
- **Battery indicator:** the Phase 3 staging profile shipped
  `visual/battery=3` (hidden). The rootfs default and staging profile are
  now `2` (upstream: icon + percent), and S91 migrates an existing p3
  config once (`MUOS/port/.migrations`).
- **Headphone volume:** the RK817 HP output is a 0 dB opamp with no
  class-D amp, so the shared PipeWire level is loud on the speaker and
  quiet on HP. `muos-headphone` now does upstream's per-output volume
  (`/run/muos/headphones` flag + `SAVE/LOAD_SINK_VOLUME`): each output
  keeps its own level. If HP is still too quiet at 100%, upstream's
  Overdrive (Settings → Advanced, up to 200%) applies.
- **Silence after boot (root cause found):** on some boots WirePlumber's
  ALSA device enumerates no profile (empty `EnumProfile`, no sink) and
  upstream S80pipewire gives up after its 3 s node budget; S95 then ran
  the whole boot silent. Caught live on 2 of 13 warm reboots; two bad
  boots in a row look like "reboot didn't fix it". Not codec state: the
  RK817 playback registers and the 44.1 kHz PCM rate were identical across
  reboots and 5 sleep cycles (`port/scripts/t2-audio-state.sh`). S95 now
  retries the full audio start (prime + S80 + sink wait) up to 3 times
  within a 25 s deadline, records `/run/muos/core/audio-attempts`, keeps
  each failed attempt's `pw-dump`, and writes a codec/PCM snapshot to p3
  `MUOS/log/system/audio-codec.txt` every boot.
  Soak (15 warm reboots): audio up on 15/15; 2 needed the second attempt,
  none a third; the playback registers were identical on all samples.

M1 delivered three things:
- a flashable recovery image,
- a device that boots straight into the muOS frontend through standard
  BusyBox rcS/rcK-style init,
- the retirement of the C-step safety harness.

All checks passed at T0–T2, and **M1 T3 passed (2026-11-10)**. The first
flash attempt failed at verification (dArkOSen's sudo PATH has no sbin;
fixed in `9bf8f80`); the rerun verified the card and grew p3 to 116.6 GiB.
Results by checklist item:

| # | Check | Result |
|---|---|---|
| 1 | Flash via dArkOSen slot 2 | OK |
| 2 | Cold boot to menu | OK (menu at ~15.5 s; SSH at 192.168.15.8) |
| 3 | GB save/load/quit | OK |
| 4 | Menu reboot, persistence | OK. Relaunching the game resumed the last state without Fn+L2: muxretro's default `auto_save=3` (idle + quit) writes `autosave.state` on quit and loads it at the next launch. Expected muOS behaviour. |
| 5 | Menu shutdown, power on | OK |
| 6 | Power key / speaker | OK |

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

The device runs the M2 image plus the M2.1 fixes installed in place
(`install-rootfs.sh`; no new image, to save disk: M2 stays the recovery
image). The images are in `dist/recovery/`, each with `.sha256` and `.manifest`.
**They are private:** they contain the Wi-Fi PSK, the SSH host key and
authorized_keys. Never commit or share them.

| Image | Content | Boots on |
|---|---|---|
| `test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: + sleep, battery, headphones, NES core | any card ≥ 2 GiB |
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

**M2 additions:**
- **Power key and sleep, as upstream muOS:**
  - `share/hotkey/sleep.json` binds `POWER_SHORT`/`POWER_LONG` to
    `SLEEP_*`. The frontend loop starts `muos-hotkey`, which reads
    muhotkey's output through a FIFO (like upstream `hotkey.sh`).
  - Both presses run `muos-suspend` (like upstream `suspend.sh`):
    muxretro SIGUSR1 (auto-save + pause), backlight off, mute,
    Wi-Fi/SSH down, `mem` from `danger/state`, then everything in
    reverse plus SIGUSR2.
  - Wi-Fi: 8821cu is unloaded and the DWC2 USB host is unbound before
    sleep and rebound after it; otherwise the dongle stays dead after
    `mem`.
  - Shutdown timer (`settings/power/shutdown`, upstream default 600 s):
    a clean poweroff after 10 min asleep.
  - With the charger connected it does upstream's "fake sleep" instead:
    screen off, frontend stopped, the next Power press wakes it.
  - Events are ignored for 6 s after waking, so the waking press can't
    put it back to sleep.
- **Battery** (S97): muOS `mubattery` feeds the status bar (hidden until
  M2.1 by `visual/battery=3`, see above) from
  `device/config/battery/*` (RK817 gauge, `ac/online` as the charger).
  `muos-lowbattery` shows the warning overlay at
  `settings/power/low_battery` (25%). As a port addition, it powers off
  cleanly at ≤3% while discharging.
- **Headphones** (S97, `muos-headphone`): jack in → playback path HP,
  out → `SPK_HP` (polarity confirmed at T3). M2.1: per-output volume as
  upstream; `port/scripts/t2-headphone.sh` simulates plug/unplug by
  flipping the tmpfs `device/config/audio/jack_inverted`.
- **cpufreq:** writable. The frontend loop applies muOS per-content
  governors and restores the device default, `schedutil`. The menu
  idles at 1008 MHz.
- **No overclock.** The port U-Boot pins the size and SHA256 of `Image`
  and the DTB, so the 1512 MHz DTB stopped the boot. It was restored
  through dArkOSen. See hardware-findings and M3.

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
- NES: the C47 "51.4 fps" figure applied only to the synthetic demo ROM
  (see M2)

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

**M2, automated on the device (T2), 2026-11-11:**
- **NES fps.** Measured by `port/scripts/t2-nes-fps.sh` with muxretro's own
  frame-time capture (`MUXRETRO_PERF_CAPTURE`; muxretro's "Content
  rate" log line is audio-derived, not fps), 60 s after a 10 s warm-up:

  | Run | ROM | fps | frame / core / present ms | CPU, governor |
  |---|---|---|---|---|
  | before (cpufreq ro) | Super Mario Bros. 3 (MMC3) | 59.90 | 16.69 / 5.88 / 10.60 | 1296 MHz, performance |
  | after (writable) | Super Mario Bros. 3 | 59.89 | 16.70 / 7.09 / 9.35 | 1296 MHz, schedutil |
  | before | r35s-flight (MIT demo) | 51.61 | 19.38 / 13.47 / 5.70 | 1296 MHz, performance |
  | after | r35s-flight | 51.56 | 19.40 / 13.50 / 5.69 | 1296 MHz, performance (muxretro boost) |

  A real game runs at full speed (vsync-locked to the 59.94 Hz panel)
  with headroom. Only the synthetic demo ROM is slow. Writable cpufreq
  doesn't change fps, but the menu now idles at 1008 MHz.
- **Sleep:** 20/20 Power-key sleep/resume cycles
  (`port/scripts/t2-sleep-cycle.sh`; injected Power press, `mem`, RTC
  wake).
  - 3 of them were in game: muxretro auto-saved, paused and resumed on
    SIGUSR2.
  - Each cycle checked the backlight restored and Wi-Fi/SSH back on the
    first attempt.
- **Charging fake sleep:** screen off and frontend stopped; a second
  press wakes it.
- **Battery:** `/run/muos/battery` reports 100%, 4150 mV, charging=1.
  The low-battery logic (overlay, clean critical poweroff) passed at T1.
- **Headphones:** jack=0 → `SPK_HP`. Insertion not exercised (no hands).
  M2.1: `t2-headphone.sh` PASS (plug → HP with its own level, unplug →
  speaker level restored, replug → HP level restored).
- **Regression:** the full `t2-menu-cycle.sh` passes (9/9).

## Broken, caveated or unverified

- **Power:**
  - **Shutdown timer:** the poweroff after 10 min asleep is untested
    (powering back on needs hands).
  - **Physical Power key:** only injected presses have been tested.
  - **Not done:** LEDs (the R35S LED node is disabled in stock too;
    charge indication is presumably hardware) and rumble.
  - **No CPU overclock:** see M3.
- **Audio:**
  - half-rate PCM after reboot (root cause unknown; not seen in 13+15
    probed reboots, where hw_ptr always advanced at ≈44.1 kHz)
  - the WirePlumber "no profile" start failure itself is unexplained;
    M2.1 retries around it
  - 3–8 underrun bursts per game
  - help WAVs inaudible
  - HP loudness at 100%/overdrive unconfirmed (T3)
- **Unsupported content:** only libretro cores in `/opt/muos/share/core`
  are supported (gambatte and fceumm are installed); `ext-*` launchers
  are refused. There is no general ROM import path beyond copying files
  to p3 `ROMS/<system>` (`port/scripts/install-nes.sh` copies
  `port/roms/nes`).
- **Missing on the device: e2fsck (M2 item 8 not done).** Building
  e2fsprogs in the Buildroot output needs container access to `build/`,
  which this session's permission rules deny. The p3 journal covers
  unclean shutdowns, but no fsck runs on the device.
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

## M3 plan — real usage and a reproducible boot chain

M3 is split into sub-milestones; each ends with its own T3. Order matters:
kernel changes (`HW_RANDOM_ROCKCHIP`, anything in `Image`/DTB) need M3b,
because the port U-Boot pins the size and SHA256 of `Image` and the DTB.

**M3a — reproducible image + e2fsck** (next; needs approval: it ends with
writing p2):
1. **Inventory.** List every p2 file on the device (path, mode, size,
   sha256) and classify it: Buildroot package, port `rootfs/`, prebuilt
   input (kernel modules, Mali r13p0, Wi-Fi firmware, frontend,
   muxretro, cores), or legacy C-step leftover (dropped).
2. **One build.** `port/scripts/build-image.sh` in the existing
   `phase4-rootfs` container, reusing `build/phase4/buildroot` and its
   download cache:
   - `port/device/rk-r35s-p0/firmware.defconfig` = the phase4 rootfs
     defconfig + e2fsprogs (e2fsck, resize2fs) + i2c-tools + whatever
     the inventory shows is missing;
   - only the live BR2_EXTERNAL packages (muos-core, muxretro,
     wifi-only, ...); the legacy C-step packages (launcher-once,
     save-store, session, boot) are dropped;
   - `BR2_ROOTFS_OVERLAY` = `port/device/rk-r35s-p0/rootfs`;
   - prebuilt inputs pinned by SHA256 in
     `port/packaging/firmware-inputs.json`;
   - post-image: the full card image in the test128 layout (bootloader
     at 64/16384/24576, p1 FAT, p2 ext4 with 4.4-safe features, p3
     1 GiB) plus `.sha256` and `.manifest`, same format as
     `make-recovery-image.sh`.
3. **S89 runs `e2fsck -p` on p3** before mounting it (time-bounded;
   result logged to p3). A "needs manual fsck" result still mounts p3 so
   the UI comes up, and the problem is reported in the log.
4. **T1.** Inventory diff of the new rootfs against the live p2 (every
   difference explained), ELF/ldd resolution under qemu, fsck of the
   image.
5. **T2 without risking the card.** The shim
   (`/sbin/muos-ext4-diag`, 29 lines) gets a one-shot "trial root": if
   `/etc/muos-root-trial` exists, it consumes the marker, loop-mounts p3
   `MUOS/trial/rootfs.img` read-only and `pivot_root`s into it (BusyBox
   `switch_root` refuses a non-tmpfs root). A hang or failure → power
   cycle → normal p2, as with the trial inittab. The new branch is only
   reachable through the marker; it's tested in a container first (as the
   M1 shim was), because a broken shim can't protect itself. That boot must pass `t2-menu-cycle.sh`,
   `t2-sleep-cycle.sh`, `t2-headphone.sh` and the audio probe. Then,
   from inside the trial root (p2 unmounted), the agent writes the new
   p2, reads it back and verifies the SHA256. The old p2 image is kept on
   p3 until T3 passes.
6. **Collapse the chain.** Once `build-image.sh` is the single source,
   retire the prepare/package/compose scripts and C-step checks that it
   doesn't use (they stay in Git history), and dry-run
   `retention.py retire` for the old `build/phase4` outputs.
7. **T3:** flash the built image via dArkOSen (proves the image itself is
   a recovery image), boot, short play session, battery %/charging
   check.
- **Disk:** host at 96% (44 GiB free); `build/phase4` is 16 GiB. The build
  reuses the Buildroot tree, downloads and toolchain. Expected growth is
  about 3–6 GiB, recovered by retiring old outputs (graphics-config 3 GiB,
  physical-capture 2 GiB, offline-backup 0.9 GiB) after review.

**M3b — boot chain:** rebuild U-Boot without the `Image`/DTB pin (or
re-pinned from the build); write it from a verified image, using the
dArkOSen flasher as the recovery path. Then `HW_RANDOM_ROCKCHIP` and, if
content needs it, the 1512 MHz OPPs (`port/scripts/make-dtb-opp.sh`).

**M3c — ROM library:** a ROM copy path (sftp over the existing dropbear
first, then Samba or FAT-partition import), SRAM saves per system, more
libretro cores as needed.

**M3d — robustness:** p3 auto-grow on first boot, log rotation, the audio
half-rate/underruns, and the WirePlumber "no profile" start failure;
then a long run (1–2 h of play, 20 reboot/poweroff cycles).

## M1 T3 checklist (done 2026-11-10, results above)

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

## M2 T3 checklist (done 2026-11-11, results above)

Device: test128 in slot 1, slot 2 empty, at the menu. No reflash needed:
the device already runs M2.

1. **Power key in the menu:** short-press Power.
   - Expected: the screen goes dark within about 2 s.
   - Short-press again: the menu returns within about 3 s, buttons work,
     and Wi-Fi/SSH come back (I can confirm).
2. **Power key in a game:** start GB (or Super Mario Bros. 3 in
   Explore → NES), play, press Power, wait 20 s, press Power again.
   - Expected: the game continues exactly where it was, after a pause
     menu flash, with sound.
3. **Long press:** hold Power about 1 s.
   - Expected: the same sleep as a short press (that's upstream muOS
     behaviour).
   - Note: holding it much longer (≥ 6 s) is the PMIC's hard power cut;
     don't use that.
4. **Shutdown timer:** unplug the charger, press Power to sleep, and
   leave it for more than 10 minutes.
   - Expected: it powers off by itself (clean shutdown; the next power-on
     boots to the menu with the GB save intact).
5. **Charging:** plug the charger in.
   - Expected: the battery icon shows charging.
   - Power then gives the screen-off "fake sleep"; Power again wakes it.
6. **Battery %:** unplug the charger and play for about 10 minutes.
   - Expected: the status-bar % drops plausibly.
7. **Headphones:** plug headphones in during a game or with menu sounds.
   - Expected: sound only in the headphones. Unplug: sound back on the
     speaker.
   - Tell me if it's reversed (speaker silent with nothing plugged in),
     so I can flip the polarity.
8. **NES:** Explore → NES → Super Mario Bros. 3, play about 2 minutes.
   - Expected: smooth full speed and clean audio.
9. **Optional, data safety:** during a game, cut power the hard way
   (hold Power ≥ 6 s), then power on.
   - Expected: it boots to the menu. GB/NES load their last auto-save or
     quick save.


## M2.1 T3 checklist (for the user)

Device: test128 in slot 1, at the menu. No reflash: the fixes are
installed. If anything is silent, **don't reboot**: tell me first, so I
can inspect the live state over SSH.

1. **Battery indicator:** look at the top-right of the menu status bar.
   - Expected: a battery icon and a percentage.
2. **Charging:** plug the charger in, wait about 10 s.
   - Expected: the icon changes to charging. Unplug: back to normal.
3. **Battery %:** unplugged, play for about 10–15 minutes.
   - Expected: the % drops a few points (the gauge read 100% at
     3.95 V; tell me if it never moves).
4. **Headphones volume:** plug headphones in, raise the volume to a
   comfortable level, unplug.
   - Expected: the speaker comes back at its previous (lower) volume.
     Plug in again: the headphone level you set is back.
   - If 100% is still too quiet: Settings → Advanced → Overdrive on, and
     tell me whether that's enough.
5. **Sound after boot:** power off and on (or Reboot from the menu) 3
   times; each time, check there's sound in the menu.
   - Expected: sound on every boot.
