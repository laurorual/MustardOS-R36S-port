# Procedures

How to flash, build and update the firmware, and how the running system is
put together. Current state and the recovery image are in
[STATUS.md](STATUS.md); results of each milestone in
[milestones.md](milestones.md).

## Device access and card layout

- **Access:** `port/scripts/device.sh` locates the device by fingerprint:
  `find`, `id`, `run CMD`, `sh`, `sftp`, `scp` (device paths as
  `dev:/path`), `push`, `pull`, `reboot` / `poweroff` (both through init),
  `capture DIR`.
  - Identify the device by its host key, not its IP (DHCP, changes between
    boots): `SHA256:fDW+/iNaWgqPwqBtO/ESuKPSQHvYN1PSo2RHfilOxK0`.
  - Identify a boot by `/proc/sys/kernel/random/boot_id`.
- **test128 layout** (disk ID `4d554432`, 249872384 sectors):
  - Bootloader at sectors 64 / 16384 / 24576; boot records at sectors
    32 (main), 33 (previous), 34 (trial).
  - p1: FAT `MUOSDIAG`, 16 MiB+100 MiB, ro at `/boot`.
  - p2: ext4 root, 128 MiB+512 MiB, ro at runtime.
  - p3: ext4 `MUOSDATA`, 640 MiB to the end, rw at `/userdata`. 1 GiB in
    images; `flash-card.sh --grow` or the first boot (`muos-grow-p3`, since
    M3d) extends it.
- **original32 (stock dArkOSen):** the flasher station, in slot 1 with
  the target card in slot 2. Never write original32 itself.

## Flash with the host card reader (primary, since 2026-11-11)

The commands name the M3d image; use the recovery image named in
STATUS.md, and if it ever fails to boot, the previous one the same way.

1. Power the device off and put its card in the USB reader on the host.
2. `lsblk -dno NAME,TRAN,SIZE,MODEL` (the reader shows `usb`, about 119 GiB
   for test128).
3. `port/scripts/flash-card.sh host /dev/sdX dist/firmware/test128-m3d-20261113.img.zst --grow`
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
   `port/scripts/flash-card.sh darkosen <dArkOSen-IP> dist/firmware/test128-m3d-20261113.img.zst --grow`
   - Enter the `ark` SSH password once and the sudo password once.
   - Same checks as above; the target is always slot 2 (`/dev/mmcblk1`).
3. Power off. Move the card to slot 1, leave slot 2 empty, power on.

## Build the firmware

(about 50 min from scratch, minutes
incrementally; rootfs in `build/m3a/output`, boot chain in `build/m3b`):
0. Boot chain: `port/scripts/build-boot.sh all` (kernel incremental in
   `build/m3b/kernel-output`, U-Boot in `build/m3b/uboot-boot`; outputs
   and `SHA256SUMS` in `build/m3b/boot`). `kernel-ref` / `uboot-ref`
   rebuild the M2 card's `Image`/DTB/`uboot.img` and must match byte for
   byte (done once in M3b). `kernel` fails if `Module.symvers` changes
   (the modules are pinned inputs). Host tests: `port/scripts/t0-boot.sh`
   (U-Boot logic against mocks, record codec).
   The idbloader (DDR + miniloader) and the trust image (BL31 + BL32) come
   from the M2 base image; all four payloads are rkbin files.
   `port/scripts/rkbin-trust.sh [IMAGE]` rebuilds the trust image from
   rkbin's BL31/BL32 and checks it equals sector 24576 (M4d: identical).
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
   - `image <name> --public` (M4a): the public variant, no developer
     identity (no Wi-Fi config, host key, authorized key; root password
     `MUOS_PUBLIC_ROOT_PASSWORD`, default `root`; empty p3). It runs
     `check-public-image.sh` against the base p2's secrets and refuses to
     finish if anything leaks. Never boot it on the bench device unless
     the user can reflash: it has no SSH until enabled in the menu.
3. `port/scripts/retention.py add <name> "<reason>" <files>`

Prebuilt inputs are pinned in `port/packaging/firmware-inputs.json` and
stored in `build/m3a/inputs/<sha256>` (`build-image.sh inputs`). To
re-derive them from a device: inventory p2 (`find` + sha256, see
milestones.md M3a), then `firmware-inputs.py generate`; it reports every
difference against the build. A device capture
(`device.sh capture` + `make-recovery-image.sh`) still works for
snapshots.

## Update p2 in place via the trial root

(no reflash):
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
- Unattended: re-arming must happen on the main root (on the trial root
  `/` is the read-only loop image). A p3 user-init guard
  (`MUOS/init/zz-trial-guard.sh`, `user_init=1`) reboots a trial root or
  trial kernel that has no Wi-Fi after 6 min (both fall back).
- Robustness T2 for Wi-Fi: `port/scripts/t2-wifi-robust.sh` (menu SSH
  vs UI kill, simulated unplug/replug); sleep: `t2-sleep-cycle.sh`;
  wake timing: `t2-wake-wifi.sh [CYCLES] [SETTLE_MS]` (timeline from
  wake to address; a deaf dongle is power-cycled by another sleep);
  the menu's Wi-Fi toggle backend: `t2-wifi-radio.sh` (M4c).
  Connectivity rows without an adapter (button injection, software
  unplug): `t2-wifi-network-row.sh` (M4d).
  Button injection (`muos-press`) in list screens: the launcher is a 2×4
  grid (Configuration = down, right from Explore) and keeps its focus
  across screens; `comm` of `muxfrontend` names the current module. Don't
  drive Configuration → General blind: on 2026-11-16 it saved
  `settings/general/startup = resume` through its save dialog (reverted).

## Update the kernel or DTB via a trial kernel

(no bootloader write):
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

## Risky init changes

to inittab, rc or the shim: arm a trial boot.
1. Copy the known-good inittab to `/etc/inittab.fallback`.
2. Install the change, `touch /etc/muos-boot-trial`, reboot.
3. Confirm by deleting `/etc/muos-boot-trial.used`.

If SSH never comes back, a long-press power cycle boots
`inittab.fallback` instead of needing a reflash.

## Boot and runtime (reference)

U-Boot (`muos_boot`: armed trial once, then main, then previous; each
file size- and SHA256-checked, see hardware-findings.md) boots
`init=/sbin/muos-ext4-diag` with `muos_slot=<slot>`; the shim runs BusyBox
init, which runs `/usr/libexec/muos-rc start`:

| Step | Service | What it does |
|---|---|---|
| 1 | stock `seedrng`, syslog, sysctl, `udev`, D-Bus | standard Buildroot services; the TRNG has the RNG ready at 2.6 s |
| 2 | S41muos-network | Wi-Fi and SSH in the background (waits for p3's profiles); up at about 20 s |
| 3 | S85 | root ro |
| 4 | S89 | `e2fsck -p` on p3 (≤ 100 s; log p3 `MUOS/log/fsck-p3.log`), p3 rw at `/userdata`, p1 ro at `/boot` |
| 5 | S90 | muOS storage binds |
| 6 | S91 | persistent muOS config, core assignments and per-output volume on p3 (`MUOS/port`); tmpfs views for other muOS paths; logs on p3 `MUOS/log/system` (three previous boots in `system.prev*`) |
| 7 | S95 | audio (retried up to 3× within 25 s) + muinput; audio failure is non-fatal |
| 8 | S96 | input mapping |
| 9 | S97 | battery (`mubattery`, `muos-lowbattery`), headphones (`muos-headphone`) |
| 10 | S98 | user init scripts (p3 `MUOS/init`, only with `user_init=1`) |
| 11 | S99 | UI frontend loop (+ `muos-hotkey`) |

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
  warning at 25%, clean poweroff at ≤1% while discharging (M4d; only if
  the current-corrected voltage V + I·200 mΩ is below 3550 mV), with a
  "Battery empty" splash on the framebuffer (`muos-splash`) for 3 s. The
  kernel powers off by itself below 3300 mV. One line per boot and per
  clean stop (RTC date, %, mV, mA, the kernel's boot decision) in p3
  `MUOS/log/battery-history.log`. T1: `t1-lowbattery.sh`.
- **Clock (M4d):** the RK817 RTC keeps UTC while off; the kernel sets the
  clock from it at boot. After each DHCP/static address, `muos-clock sync`
  runs one `ntpd -q` (pool from config `clock/pool`, at most every 6 h of
  uptime) and writes the RTC (log `MUOS/log/system/clock.log`).
  `/etc/localtime` → p3 `MUOS/port/config/localtime` (created as UTC by
  S91), which the menu's Timezone screen rewrites (frontend 0004); full
  tzdata in `/usr/share/zoneinfo`.
- **Headphones:** jack in → path `HP`, out → `SPK_HP`; each output keeps
  its own volume (upstream `SWITCH_OUTPUT_VOLUME`).
- **cpufreq:** muOS per-content governors through `muos-governor` (GPU
  floor, deep idle and DDR follow the CPU governor, as upstream). Menu:
  `schedutil` (idles at 1008 MHz), dmc_ondemand. Games: `performance`
  (M3d default; SoC ~82 °C after minutes of PSX, throttling starts near
  85 °C). Per system from `core-assign.txt` (PSX/32X `performance`, the
  rest `schedutil`); per folder or game: muOS Content Options → Governor.
  Volume/brightness keys boost CPU/GPU floors for 2 s (`muos-boost`). No
  overclock (deferred to the end of the project as a user toggle; a
  1512 MHz DTB from `make-dtb-opp.sh` would go in as a trial kernel).
- **Wi-Fi and SSH (M4a):** muOS's Connectivity menu (Wi-Fi Network:
  X scans, a profile connects; Web Services: SSH/SFTP) drives
  `usr/libexec/muos-network/worker` through adapters at upstream's script
  paths. Profiles: p3 `MUOS/network/<name>.ini`. Developer images also
  load the private `network.conf` and run key-only dropbear on :2222.
  No network configured → the radio stays off. `worker status` shows
  radio, wpa state, address, active profile and SSH services; logs in
  `/run/muos/network/private/` (never print `network.conf`).
- **User init scripts:** p3 `MUOS/init/*.sh` run at boot (S98) when
  `settings/advanced/user_init` is 1 (upstream feature, default off).
- **Unattended discharge log:** `t2-discharge.sh log-start` (idle, no
  game) installs `MUOS/init/zz-discharge-log.sh` and sets `user_init=1`,
  so the log (`MUOS/log/discharge.csv`, one line a minute incl. the
  gauge's coulomb counter `cc_mah`) survives reboots; `status`, `report`
  (after recharging), `log-stop`.
- **T2 hygiene:** `t2-sleep-cycle.sh --game` uses the NES test game with a
  pickles snapshot (never the user's saves); keep the volume at 10 during
  T2 runs at night.

Source lives in `port/device/rk-r35s-p0/rootfs/`; the init scripts are
symlinks to the files Buildroot also uses. Deploy with
`port/scripts/install-rootfs.sh [paths]` (atomic; keeps the first original
in `/var/lib/muos-m1-backup`; `--restore` undoes). Build outputs:
`--tree DIR path` (e.g. `build/m4c/frontend-libs/tree`,
`build/m3d/muxretro/tree`). A path with a bind mount on it fails with
EBUSY (unmount test binds first); for frontend files stop the UI first,
and restart `S97muos-battery` (mubattery maps `libmuxmod.so`), or `/`
stays rw until the next boot.

**Frontend libraries (M4c):** `port/scripts/build-frontend-libs.sh`
builds `libmuxmod.so` from the C65 source + `port/patches/frontend/`
(`check`: an unpatched build equals the pinned one; `mkpatch NAME FILE…`
as in `build-muxretro.sh`). Patches touch module code only. Pin a new
build in `firmware-inputs.json` (sha256 + origin) and run
`firmware-inputs.py store port/packaging/firmware-inputs.json
build/m3a/inputs` before `build-image.sh build`.

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

