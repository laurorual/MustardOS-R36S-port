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
  - p2: ext4 root, 128 MiB+1 GiB (M8 image m8b on; 512 MiB before, the
    m7d recovery image and older still have that layout), ro at runtime.
  - p3: ext4 `MUOSDATA`, 1152 MiB (640 MiB in the old layout) to the end,
    rw at `/userdata`. 1 GiB in images; `flash-card.sh --grow` or the
    first boot (`muos-grow-p3`, since M3d) extends it.
- **original32 (stock dArkOSen):** the flasher station, in slot 1 with
  the target card in slot 2. Never write original32 itself.

## Flash with the host card reader (primary, since 2026-11-11)

`RECOVERY.img.zst` stands for the recovery image named in STATUS.md
(`dist/firmware/<name>.img.zst`); if it ever fails to boot, flash the
previous kept image the same way.

1. Power the device off and put its card in the USB reader on the host.
2. `lsblk -dno NAME,TRAN,SIZE,MODEL` (the reader shows `usb`, about 119 GiB
   for test128).
3. `port/scripts/flash-card.sh host /dev/sdX RECOVERY.img.zst --grow`
   - It accepts only a whole USB/removable/MMC disk (it refuses the
     internal `sda` and `nvme0n1`, partitions, an empty reader and a
     too-small card), shows model and size, asks `y`, then asks for sudo.
   - It unmounts the card, writes, re-reads with caches dropped, checks
     the SHA256 (`verified raw_sha256=…`), then grows p3 (`p3 grown and
     clean`).
4. Put the card in slot 1 (slot 2 empty), power on.

**Keep p3 across a reflash (M8, layout change):** a flash rewrites p3
(ROMs, saves, states, BIOS, Wi-Fi profile). With the card in the reader:
`port/scripts/card-p3.sh backup /dev/sdX` (p3 read-only → private
`build/m8/p3-backup/p3.tar`, MUOS/trial left out), the flash above with
`--grow`, then `port/scripts/card-p3.sh restore /dev/sdX` (file-count
check). Both use sudo. Delete the tar once the restored card is
T3-checked. (M8: 6539 entries, 5.5 GiB, ~15 min for all three steps.)

**Flash via dArkOSen (fallback, no reader):**
1. Power off. Put original32 in slot 1 and the target card in slot 2.
   Boot, join Wi-Fi, and enable Remote services (Options).
2. On the host:
   `port/scripts/flash-card.sh darkosen <dArkOSen-IP> RECOVERY.img.zst --grow`
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
   Lint (T0): `build/tools/shellcheck -S warning` (static 0.10.0, M4e) on
   `port/scripts/*.sh` and the shipped shell scripts: warning-clean.
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

Languages (M7): `fetch-upstream-share.sh fetch` also fetches the pinned
upstream language pack (`port/packaging/muos-language.txt`); `stage`
writes it merged with `port/packaging/language/<Language>.json` (the
port's translations: section → English text → translation). New
language files that a Buildroot package leaves behind go into
`firmware-inputs.json` "remove".

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
  the menu's Wi-Fi toggle backend: `t2-wifi-radio.sh` (M4c); repeated
  off/on: `t2-wifi-toggle-loop.sh [--inject-c2h] [N]` (M6).
  Liveness while connected (M7, `muos-usb-watchdog`):
  `t2-wifi-liveness.sh c2h|silent`.
  Connectivity rows without an adapter (button injection, software
  unplug): `t2-wifi-network-row.sh` (M4d).
  Menu SFTP (M4g, jailed as upstream: port 2022, user `muos`, password
  `muos`, storage folders only): `t2-sftp-jail.sh [MiB]`; the developer
  SFTP (`device.sh sftp`, port 2222, root, whole filesystem) is
  `t2-sftp.sh` and exists only on developer images.
  Button injection (`muos-press`) in list screens: the launcher is a 2×4
  grid (Configuration = down, right from Explore) and keeps its focus
  across screens; `comm` of `muxfrontend` names the current module. Don't
  drive Configuration → General blind: on 2026-11-16 it saved
  `settings/general/startup = resume` through its save dialog (reverted).
  Never move the launcher focus without checking it first (A on Explore
  must open `muxplore`): on 2026-11-17 a wrong guess launched CTR and a
  sleep test overwrote its resume state.
- Rumble: `muos-rumble pulse MS [PCT]`, `muos-rumble-setup probe` (M4e;
  verdict in p3 `MUOS/port/rumble`, log `MUOS/log/system/rumble.log`).
- USB replug diagnosis (dev only): `t2-usb-watch.sh start` before the
  user replugs (SSH is gone meanwhile), `report` afterwards (HPRT0 bit 0
  = connected; one line a second in `/run`, copied to p3).
- USB watchdog: `/opt/muos/log/usb-watchdog.log`; test a missed plug
  with `MUOS_USB_WATCH_DEV=/nonexistent MUOS_USB_WATCH_ONCE=1
  /usr/libexec/muos-usb-watchdog` (detached: SSH drops; never kill a
  watchdog mid-rebind from a test).
- Activity tests: mount a tmpfs over `/run/muos/storage/info/track` so
  test sessions stay out of the user's history.
- Upstream muOS scripts: add `sha256  path` to
  `port/packaging/muos-internal-extra.txt` (from refs/muos/internal).
- Upstream `share/` data (M5): refs/muos/internal is a `blob:none` sparse
  clone without `share/` (reading its blobs fetches them into refs), so
  `port/scripts/fetch-upstream-share.sh` keeps a sparse clone in
  `build/upstream/internal` (640x480 only, no music/videos; CJK fonts since M8);
  trees by git tree id in `port/packaging/muos-internal-share.txt`,
  removals in `muos-internal-share-exclude.txt`; `stage DIR` builds an
  install tree (`stage_overlay` uses it). The pinned inputs win where
  paths coincide; on the live root install only new paths (an
  `install-rootfs.sh --tree` of the whole tree overwrites pinned files).
- Screens (M5): `t2-ui.sh open MODULE` restarts muxfrontend straight
  into a module (`/run/muos/action`), `go NAME KEYS…` presses and takes a
  screenshot (`script/mux/screenshot.sh FILE`, frontend patch 0007:
  the menu only, not muxretro), `home`; `t2-screen-sweep.sh` opens every
  context-free screen and makes a contact sheet.
- Slot 2 (M5): `script/device/storage.sh sdcard mount|eject|status`
  (udev `91-muos-sdcard.rules`, S90 at boot, log `/run/muos/sdcard.log`);
  `t2-sdcard.sh` with loop devices (`MUOS_SD2_TEST_DISK`). Disk writers
  find the slot-1 card with `/usr/libexec/muos-boot-disk`; the host-side
  T2 scripts that `dd` to `/dev/mmcblk0` (t2-boot-slot.sh, device.sh
  capture) assume slot 2 is empty on the bench.
- Backups/archives (M5): native task mode for T2 is `MUOS_TASK_UI=1
  /opt/muos/script/mux/backup.sh 0` with `/tmp/muxbackup_manifest.txt`
  (`INDIVIDUAL SD1` + `SD1 screenshot`), then `extract.sh FILE archive`.
- Input Remap: `/opt/muos/script/mux/sdl_remap.sh` writes p3
  `MUOS/port/gamecontrollerdb/{retro,modern}.txt`; a broken remap is
  undone by deleting its GUID line there.
- Wi-Fi after the fact: p3 `MUOS/log/network-last.log` (worker with
  uptime stamps, hotplug, dongle kernel lines; written at each clean stop).

## Update U-Boot in place (M8)

No fallback: a U-Boot that does not boot costs a host-reader rewrite of
sectors 16384–24575 (p3 is untouched). Only with the user's consent (or
present), after T0 (`t0-boot.sh`) and `build-boot.sh uboot-ref` still
byte-identical.
1. Back up the current one: `dd if=$(muos-boot-disk) bs=512 skip=16384
   count=8192 of=/userdata/MUOS/trial/uboot-previous.img`, pull it to
   `build/`.
2. Push `build/m3b/boot/uboot.img` (4 MiB) to `/run`, check its SHA256
   against the build; `dd ... seek=16384 conv=fsync`, drop caches, read
   back and `cmp`.
3. Reboot; check `/proc/cmdline`; `t2-boot-slot.sh` (4 cases).
- The boot logo is p1 `bootlogo.bmp` (`make-boot-logo.py --bmp
  bootlogo.fb.gz OUT`; remount `/boot` rw to replace it).
- Unattended trial boots: `port/scripts/trial-guard.sh` as p3
  `MUOS/init/zz-trial-guard.sh` with `user_init` = 1 (remove after).

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
- The label is short (about 20 characters; longer ones: "bad argument").
- Undervolt DTBs (M8f): `port/scripts/make-dtb-uv.sh MAIN.dtb OUT.dtb CPU_MV
  GPU_MV` from the main DTB (pull `/boot/<fdt>`), then a DTB-only trial
  with the main `Image`. Stability T2: PSP God of War for 5 min (GPU
  faults show as "GPU fault 0x4002" in dmesg) and the DC thermal run.
- Undervolt opt-in (M9, decision 28): the image ships the stock DTB and
  16 undervolted ones (CPU 25…100 × GPU 0…75 mV, `uv-C-G=` in p1
  `dtb-variants.txt`; values in `danger/uv_cpu`, `uv_gpu`).
  Configuration → Danger Settings → Undervolt (or `muos-undervolt`:
  write 0/1 to `/opt/muos/config/danger/undervolt`, `muos-undervolt arm`,
  reboot) arms the other DTB as a trial (label `undervolt-on|off`);
  `muos-frontend` promotes it after 20 s of menu (`muos-undervolt
  promote`) and `sync` sets the row from the booted DTB. A card from an
  older image needs `dtb-variants.txt` on p1 (both DTBs already there).
- ScummVM patches: `port/patches/scummvm/*.patch` (`build-scummvm.sh`
  applies them to the standalone's archive and once to the tree).

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
  M7: the port DTS carries the stock OPPs to 1512 MHz; the CPU stays at
  1296 MHz unless config `danger/cpu_max` (menu: Danger → Processor
  Maximum; 0 = highest) says otherwise (`muos-governor`, `muos-rc`).
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
(`check`: an unpatched build equals the pinned libmuxmod and has the
pinned libmuxcom's symbols; `mkpatch NAME FILE…` as in
`build-muxretro.sh`), `libmuxcom.so` too once a patch touches
`frontend/common/` (function bodies only: muxfrontend and muxretro share
its structs), and the upstream tool `musftpjail` (M4g). Pin a new
build in `firmware-inputs.json` (sha256 + origin) and run
`firmware-inputs.py store port/packaging/firmware-inputs.json
build/m3a/inputs` before `build-image.sh build`.

**Release frontend (M6):** the image ships the `TEST_IMAGE=0` build:
`build-frontend-libs.sh release` (libraries + muxfrontend, muhotkey,
mubattery → `build/m4c/frontend-libs/release`), then
`build-muxretro.sh release` (own tree, links the release libraries →
`build/m3d/muxretro/release`). Both use every frontend/muxretro patch;
`build` (test build) stays for `check` and quick tests. Re-pin with
`pin-input.py PATH…`; a new input file: `pin-input.py --origin PATH
ORIGIN` (then `build-image.sh inputs`).

**Cores (M3c, M6):** `build-cores.sh fetch|build NAME…` (table: repo,
commit, tarball SHA256, output, licence; a new row has `-` until its
first fetch prints the SHA256). Folder, core, coredb system, launcher
key and governor per system: `rootfs/usr/share/muos-r35s/core-assign.txt`
(S91 seeds folders; the post-build sets coredb governors and default
cores). Smoke content without game dumps: `make-smoke-roms.py DIR` then
`t2-nes-fps.sh --dir DIR --rom smoke.EXT`. A core crash: `prlimit --pid
<frontend sh> --core=unlimited` and a core_pattern on p3, pull the dump,
`CORE_DEBUG=1 build-cores.sh build NAME` (-g; the stripped result must
equal the shipped .so) and gdb with a sysroot whose core path points at
`build/m3c/cores/debug/<so>`. Kernel modules:
`build-boot.sh modules-check` after a kernel build.
Core patches (M8): `port/patches/cores/<row>/*.patch` (git apply, see its
README). Standalone emulators (M8): `build-ppsspp-sa.sh`,
`build-drastic.sh stage-adv` (advanced DraStic tree + config),
`build-yabasanshiro-sa.sh build` (static Boost; its offline inputs:
`build/m8/dl` tarballs and `build/yabasanshiro-sa-deps` clones, pinned
in the script), then
`firmware-inputs.py pin-tree`/`pin-file`. Screenshots of a GL emulator
for T2 (M8): `t2-swapstat.sh arm`, launch, `t2-swapstat.sh grab FILE.png`
(the next frame's default framebuffer; PPSSPP, DraStic, Mupen64Plus);
`t2-psp-fps.sh` takes `T2_PSP_GRAB=1`. Heavy-system speed: compare
settings at a fixed CPU cap (`T2_CAP`), not under thermal throttling;
DC: `t2-dc-fps.sh` (variants, `T2_DC_SO`, `T2_DC_STATE=none`,
`T2_COREMETER=1`). Real game speed of any libretro core (M8e):
`t2-coremeter.sh build|arm|mark|report` (preloaded into muxretro by
muos-frontend while armed; audio frames per second of the core as % of
44100, independent of threaded rendering). YabaSanshiro: emulated fps on
stderr with `/run/muos/perf-capture` (`yabafps 22/60 skip=11`; the
frontend log); `build-yabasanshiro-sa.sh` keeps an unstripped
`build/m8/yabasanshiro/yabasanshiro.debug` for its crash stacks
(`addr2line` from the SDK). Wake
diagnosis: `t2-wake-frames.sh` with `T2_WAKE_SAMPLE` / `T2_WAKE_STACKS`
(sysrq-l backtraces, symbols from `build/m3b/kernel-output/System.map`).

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

