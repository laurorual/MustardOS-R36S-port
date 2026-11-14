# Completed milestones

Results and checklists of finished Phase 5 milestones, moved out of
[STATUS.md](STATUS.md). Newest first. The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## M4a — public-image foundations + Wi-Fi menu (T2 done 2026-11-14, T3 pending)

Goal: the technical half of M4 (no publication) plus Wi-Fi management
from muOS's own settings menu. Images (version `m4a-20261114` in
`storage-retention.json`): developer `dist/firmware/test128-m4a-20261114`
(raw `deef0ab2…`, p2 `d61fd490…`, private) and public
`dist/firmware/public-m4a-20261114` (raw `193c520f…`, p2 `05d01396…`,
`private=no`). Kernel and boot chain as M3e. Built autonomously in the
night of 2026-11-14.

1. **Wi-Fi from the Connectivity menu** (T2 done): `board/network=1`
   (post-build overrides the pinned 0) shows Configuration →
   Connectivity. Port adapters at upstream's script paths
   (`script/init/async/S02network.sh`, `script/web/{ssid,password,
   service}.sh`) call `usr/libexec/muos-network/worker`, which builds
   wpa_supplicant's config from muOS profiles on p3 (`MUOS/network/*.ini`,
   PSK hex as muxnetprofile saves it, priority, autoconnect, static
   address) plus the developer `network.conf`. DHCP or the static address
   runs from a `wpa_cli -a` hook; no configured network → radio off
   (`/run/muos/network/idle`, muos-suspend accepts it). Connect reports
   upstream's status file and exit codes. T2 (test128, repeatable with
   `port/scripts/t2-wifi.sh`, PASS on the final p2): connect good key
   0 (8 s), wrong key 2 INVALID_PASSWORD (10 s), absent AP 3 AP_NOT_FOUND
   (23 s), each failure back on the previous network in 1–5 s; boot
   autoconnect from the profile; UI driven by `muos-press`: launcher →
   Configuration → Connectivity → Wi-Fi (muxnetwork) → X scan
   (muxnetscan, 11 SSIDs) → profile (muxnetprofile); 3/3 sleep cycles.
   Bugs found and fixed on the way: daemons inherited the command lock
   (fd 8; an SSH session from such a dropbear kept the lock held),
   network ids keep counting across `reconfigure` (select the first
   listed id), COMPLETED must be on the selected id.
2. **SSH/SFTP toggles** (T2 done): muxwebserv's `service.sh apply` →
   dropbear on `web/sshd_port` (22, password, root) and `web/sftp_port`
   (2022, forced `sftp-server`); host key from the private store, else
   created on p3 `MUOS/port/ssh` on first use (T2 with an isolated worker
   copy). Developer images keep key-only :2222.
3. **User init scripts** (T2 done): `S98muos-user-init` runs p3
   `MUOS/init/*.sh` when `settings/advanced/user_init=1` (upstream
   `user_init.sh`; default off). Used tonight for the discharge logger.
4. **Public variant** (T0/T1 done; never booted on purpose): `build-image.sh
   image NAME --public` → no Wi-Fi config, host key or authorized key,
   root password hash (`MUOS_PUBLIC_ROOT_PASSWORD`, default `root`), a
   fresh empty p3 with the base p3's ext4 features and the data marker,
   `private=no`. `check-public-image.sh` (18 checks incl. grepping the raw
   image for the developer's Wi-Fi/SSH values): public passes; the
   developer image fails 6 checks (negative test). `t1-fresh-p3.sh`
   (PASS): the empty-p3 first boot (S90, S91 seeding, S98, worker idle)
   in a rootless qemu container on the Buildroot target.
5. **Cosmetics** (T2 partly): low-battery poweroff stops the UI, writes a
   "Battery empty" picture (`make-battery-splash.py`, raw XRGB in
   `usr/share/muos-r35s/battery-empty.fb.gz`) to `/dev/fb0` via
   `muos-splash`, waits 3 s; `muos-rc stop` redraws it. T2: fb0 holds the
   picture byte for byte after the UI stopped (visibility is T3).
   `info_open/close.wav` high-passed (`wav-highpass.py`, 400 Hz 4th
   order, peak 30000) in post-build (audibility is T3).
6. **Licence groundwork** (report, `pending-licenses.json`): DDR v1.10,
   miniloader v1.12 and BL32 v1.10 are byte-identical to rkbin commits;
   BL31 v1.14 is not. rkbin's LICENSE allows use/copy/distribution.
   libmali: rockchip-linux/libmali is gone; the mirror has only
   bifrost-g31 g24p0 (needs a newer kbase than the 4.4 BSP's r13p0) under
   ARM's Mali EULA (redistribution allowed with the EULA). No
   redistributable userspace for our kbase found.
7. **On test128:** the M4a developer p2 was booted as trial root (T2:
   2/2 in-game sleep cycles, audio PASS), then written to p2 (read-back
   verified; the previous p2 is in p3 `MUOS/trial/p2-previous.img`);
   `t2-menu-cycle.sh` all PASS on it.
8. **Idle discharge run** (2026-11-14 06:21–12:06 UTC, log in
   `build/logs/discharge/`, `t2-discharge.sh log-start`): menu idle,
   backlight 40, mean 389 mA, 94% → 3% in 345 min, survived 6 reboots
   (logger as p3 user init). Clean `critical battery (3%, 3364 mV):
   power off`. Coulomb counter 3172 → 963 mAh = 2209 mAh, host-integrated
   current 2234 mAh (1% apart: the counter is trustworthy). dsoc tracked
   rsoc down to ~3.82 V, then the zero algorithm pulled it ahead (rsoc
   28.5% at the 3% poweroff). **Real capacity ~2530 mAh** (OCV via the
   DT table, start ~88–92%, end ~1–5% for bat_res 100–200 mΩ: 87 points
   = 2209 mAh, ±10% since the table isn't measured for this cell); the
   DT/PMIC FCC 3380 is ~33% too large. Next charge boot: patch 0005's
   lost-counter branch fired (`coulomb counter lost (now=0): dsoc 33000
   cap 1115 from the voltage`, charging at 1.6 A), first sighting with
   the 0005 kernel: **wrong**, real ~3–5% (the user plugged in and
   powered on at once; 7 min later 36% shown vs ~10% real). Cause:
   bat_res 100 mΩ vs ~200 mΩ effective at charge onset, and the stored
   dsoc 2999 was ignored. Bug found: `log-stop`'s `pkill -f` killed its own
   remote shell (the command line named the init script), so the script
   stayed installed; fixed (pkill in its own call), cleanup done by hand.

## M3e — daily-use polish (done 2026-11-14, T3 passed)

Goal: close the M3 items that need no user decision and ship the M3e
image. Image `dist/firmware/test128-m3e-20261113` (raw `7b7c4a66…`, p2
`fd547220…`, rootfs `e7c12aa1…`, kernel `Image-b486b7126df2` = patches
0001–0005), the recovery image since 2026-11-14 (M3b retired; M2 kept as
the image-build base).

1. **Hold-to-repeat** (T2 done): post-build sets `handle_hold` on the
   level combos (as upstream). A 2 s hold moves the level ~10 steps;
   brightness 0 blanks the screen as upstream (the next brightness-up
   restores it). In game: 60.0 fps, 0 missed vsyncs (`t2-level-fps.sh`
   vol-hold / bright-hold).
2. **Menu idle power** (T2 done): Wi-Fi power save (`rtw_power_mgnt=1
   rtw_ips_mode=1`, `etc/modprobe.d/8821cu-power.conf`) 546 → 454 mA;
   ping avg 12 ms / max 92 ms, 20 MB push 3.5 s. The BSP's 408 MHz
   CPU OPP (0.95 V; the vendor DTS deleted it) 454 → 409 mA, 88% of
   menu idle at 408 MHz; games stay ≥ 1008 MHz. T2: NES gate 60.0 fps /
   0 missed; SNES, GBA, MD ~1 missed vsync per minute (as M3d); 2/2
   in-game sleep cycles.
3. **Battery full discharge** (passed 2026-11-14, logs in
   `build/m3e/discharge-20261114`): NES test game, then CTR from 60%
   (`t2-discharge.sh switch`), volume 10. 64% → 4% in 95 min, ~1150 mAh
   (mean 721 mA), no % jumps; 25% at 3441 mV, 10% at 3368 mV; clean
   `critical battery (3%, 3335 mV): power off` (muos-lowbattery).
4. **Image hygiene** (done): p1 without `DIAGnn` / `PROBE.TXT` /
   `tools`; muxretro's provenance and `payload.sha256` describe the
   source build.
5. **M3e image** (T2 done on the trial root): audio before/after PASS,
   level-fps PASS on rerun (see "Frame pacing"), 2/2 in-game sleep
   cycles, long play 2 min each NES/SNES/GBA/MD/PSX PASS (2–3 missed
   vsyncs per game, fps ≥ 59.77, PSX 77 °C).
6. **Gauge after a dead battery** (T2 done, 2026-11-14): after ~7 h of
   charging while off, the boot showed 0% on a full battery: the
   counter came back invalid (0 vs 974 mAh), which the BSP took for a
   halt. The PMIC's OCV sample (3751 mV, from the charger plug-in) was
   stale, and the off timer stays set, so warm reboots recalibrated to
   48%. Kernel patch 0005 adds a current-corrected voltage estimate
   (V − I·bat_res). With it, a lost counter starts from the estimate, and
   an OCV more than 30 points away from it is skipped. Boot sanity resets
   to the estimate when dsoc and the counter are both more than 40 points
   away. T2: the trial boot went 49% → 97% (4.16 V, tail charge), stable
   over 2 reboots on main; audio PASS. Image rebuilt (same rootfs).

**T3 (2026-11-14, all passed).**
- A. Discharge run: clean low-battery poweroff at 3%. The screen just
  goes black, because `muos-lowbattery` calls `poweroff` without the
  frontend's shutdown message (cosmetic).
- B. Boot after the recharge: 0% on a full battery with the old kernel;
  fixed by patch 0005 (step 6).
- C. Flashed without `--grow`: p3 grew on the first boot (116.6 GiB,
  resize2fs rc 0 at 7.1 s), so M3d item 9 is fixed. BIOS, ROMs and saves
  were restored and are checksum-identical. The gauge kept 97% across the
  flash.
- D. Menu at 408 MHz idle as smooth as before; hold-to-repeat in the menu
  and in game; Wi-Fi + SFTP; sleep/wake in game; sound on every boot;
  battery % stable over a power-off and cold boot.

## M3d — smoothness + robustness (done 2026-11-13, T3 passed)

Goal: no visible slowdowns in normal play (the user's bar for the final
build), then robustness for long use. Steps 1–2 are below; steps 3–6 ran
autonomously on the night of 2026-11-13. Image
`dist/firmware/test128-m3d-20261113` (raw `f2692bfa…`, p2 `fd78705a…`),
the recovery image since 2026-11-13.

**Step 3 — volume/brightness judder.** muxretro built from source
(`build-muxretro.sh`: Phase 4 provider source + `port/patches/muxretro/`,
byte-reproducible, pinned from `build/m3d/muxretro/tree`): patch 0001
(per-frame `slow_frames` stage trace), 0002 (in-game level bar drawn by
muxretro: plain panel, bar and recoloured theme glyph; the pause menu keeps
upstream's LVGL bar). WirePlumber `state.restore-props = false` on the sink
(`core-wireplumber.conf`); volume steps through `muos-volume-step` +
`muos-volumed` (resident `pw-cli`, started on the first press; the first
press after boot uses upstream `audio.sh`). T2 gate `t2-level-fps.sh
--max-slow 6 --max-missed 0`: 0 frames > 25 ms per 14 s of presses on
NES/schedutil (was 46–53 vol / 10–35 bright).

**Step 4 — remaining stalls.** Wake: the 8821cu's association busy-waits
in the kernel (PREEMPT_VOLUNTARY) and froze a frame for 80–130 ms; the
Wi-Fi side now runs on CPU3 (network worker, its daemons, `RTW_CMD_THREAD`;
`muos-cpu-pin`, BusyBox `taskset`) and a resumed game on CPU0–2: worst
frame after wake 129 → 33 ms. PSX: pcsx_rearmed on muxretro's core thread,
overlapped with presenting (muxretro patch 0003): CTR attract 8–12 missed
vsyncs per 75 s and 60.0 fps per 5 s window (was 35–108, 53–58 fps); about
one frame more input latency. 2/2 PSX in-game sleep cycles
(`T2_GAME_DIR`/`T2_GAME_ROM` for `t2-sleep-cycle.sh`).

**Step 5 — robustness.** p3 auto-grow on first boot (`muos-grow-p3`, S89:
MBR p3 end before the mount, online `resize2fs` after it, log p3
`MUOS/log/grow-p3.log`; only for disk ID 4d554432 with three partitions);
log size cap (`muos-logcap`, S97: a log over 4 MiB keeps its last 1 MiB as
`NAME.1`). T2 of the grow on a loop-device copy of the layout only (see
item 9 below for what that missed).

**Step 6 — long run.** 51 warm reboots (`t2-audio-state.sh --reboots`:
audio 51/51, slot main, gauge `force0`), 30 of them on kernel 0004, which
held the % every time; one boot read the unsampled OCV (18 mV) and the
guard kept dsoc. An RK817 RTC alarm doesn't power the device on, so cold
boots are T3-only. `t2-long-play.sh --minutes 12` on NES, SNES, GBA, MD and
PSX: all PASS, ~1 missed vsync per minute (capture dump a likely cause),
fps ≥ 59.7, RSS +0–1 MiB, SoC 62–68 °C (PSX 78 °C), PCM throughout.
Battery: patch 0004 (skip OCV calibrations outside 3.0–4.5 V; an
unsampled OCV register read 18 mV on 5/20 warm reboots and became 0%).

**T3 (user, 2026-11-13), items 1–8 on the card before the flash:**
1 cold boot after ≥ 5 and ≥ 30 min off OK; 2 charging reboot OK; 3 drain
OK (gauge logs of the last 4 boots: no correction, dsoc kept, e.g. 81%
after ~50 min off with the counter at 72%, 87% on the charging reboot with
vsoc 99%; saved in `build/m3d/p3-preflash-20261113`); 4 bar OK, but
holding a key changes one step only (upstream repeats; the port's hotkey
JSON lacks `handle_hold` → M3e); 5 volume OK; 6 CTR smooth over 3–4 races,
input OK; 7 wake OK, one small dip left (remove late in the project if
possible); 8 sound on every boot. Decisions: overclock deferred to the end
as an optional user toggle; M3d is the recovery image; M3a.1 retired; from
now on a milestone whose T3 shows no or only small problems becomes the
recovery image without asking.

**T3 item 9 — first flash, p3 auto-grow (2026-11-13): failed, fixed at
T2.** Flashed without `--grow` (raw SHA verified). The first boot wrote
the MBR but the kernel kept p3 at 1 GiB: BusyBox `partprobe` (BLKRRPART)
gets EBUSY while p2 is mounted, which the loop-device test (nothing
mounted) couldn't show. It also broke p3's fsck: udev re-probed p3 after
the MBR write, and blkid found no table entry matching p3's old kernel
size, so `/dev/disk/by-partuuid/4d554432-03` disappeared between S89's
check and `e2fsck` (rc 8; S89 mounted anyway by `/dev/mmcblk0p3`). sfdisk
2.40 only knows BLKRRPART too. Fix: Buildroot `UTIL_LINUX_PARTX`
(`resizepart`, BLKPG_RESIZE_PARTITION, p3 only) after the MBR write, then
`udevadm settle`. T2 on test128 (MBR p3 set back to the flashed 2097152
sectors, ext4 untouched): partition 248561664 sectors at 6.8 s, ext4 online
resize done at 7.6 s, link present, fsck rc 0, 118.5 GiB; the next boot
was a no-op with a clean fsck. The M3d image itself still has the old
script (a fresh card should reach full size on its second boot, not tested; `--grow` avoids
it); the fix ships in the next image.

## M3d step 2 — battery % from the fuel gauge, per-system governors (done 2026-11-13)

**Delivered:** kernel patches 0001 (capacity = RK817 fuel-gauge dsoc),
0002 (boot sanity check dsoc vs coulomb, `muos-gauge:` log), 0003 (BSP
unit fix in the boot calibration); per-system governors (PSX/32X
performance, the rest schedutil); `muos-boost` for volume/brightness keys;
`muos-lowbattery` voltage guard (< 3.5 V). Commits 91c7ff5, 5386632 and
the 0003 commit.

**T3 (user, 2026-11-13, first run):** items 4–6 OK; battery failed (0%
after a reboot, low-battery poweroff) → 0002 + guard.
**Re-test (user, 2026-11-13 night):** 3 (done first) cold boot raised the
% from ~75 to ~80; 2 > 1 h idle in the menu 100% → 81% (~19%/h, matches
the ~560 mA menu draw); 1 (after 3) reboot kept the %; 4 charged to 85%,
rebooted with the charger in → ~95%; 5 sound OK the whole time. Cause of
both jumps: the BSP's force calibration fired on every boot (unit mix,
hardware-findings "Battery %"); fixed by 0003 (T2: a charging reboot keeps
dsoc 99010 with `force=0`; the counter persists). Cold boot is T3-only.

## M3d step 1 — game governor, wake order, panel timing, PSX BIOS (done 2026-11-12, T3 passed)

**Delivered:** `muos-governor` (CPU governor + GPU floor, deep idle, DDR
follow it, as upstream `governor.sh`), games at `performance`; wake resumes
the game after the Wi-Fi radio is up; panel timing 60.0046 Hz (stock
vertical porches) fixed the bottom-rows glitch; the user's PSX BIOS on p3.
T2: NES 59.97, GB 60.00, PSX 58.76–59.8 fps; wake 2–6 missed vsyncs (was
41); sleep-cycle 3/3; boot-slot fallbacks PASS. Commit 638d39a.

**T3 (user, 2026-11-12):** 1 screen OK (no strip ever, incl. cold boot);
2 PSX OK, a little slowdown at the start and end of a race only; 3 wake OK,
"way better than before"; 4 volume/brightness OK (unchanged); 5 battery
PARTIAL: ~15 min of play seemed to take it to ~70%, and a cold boot showed
100% again. Cause: the kernel's voltage-only `capacity` (hardware-findings
"Battery %"), fixed in step 2. The user asked for per-core CPU/GPU profiles
(PSX full speed, NES not) → step 2.

## M3c — ROM library: SFTP, 4 cores, ROM folders (done 2026-11-12, T3 passed)

**Delivered:** Buildroot `gesftpserver` as `/usr/libexec/sftp-server`
(dropbear SFTP; OpenSSH `scp` works without `-O`), `rom-push.sh`; S91
seeds ROM folders (NES GB GBC GBA SNES MD SMS GG 32X PSX) and core
assignments from `core-assign.txt` only where a folder has none;
`build-cores.sh` builds snes9x2005_plus, gpsp, picodrive and
pcsx_rearmed from pinned commits (offline, `-mcpu=cortex-a35`).
Image `test128-m3c-20261112` (raw `64811ce2…`).

**T2:** `t2-sftp.sh` PASS (8–9 MiB/s), regression suite PASS, fps NES
59.90, GB 59.90, SNES 59.92, GBA 59.91, MD 59.93, PSX 59.09 (see M3d:
schedutil). `t2-menu-cycle` no longer touches the user's GB states.

**T3 (2026-11-12, user):** all four items OK:
1. GBA, SNES, MD and PSX start from Explore with sound; the empty GBC, SMS,
   GG and 32X folders show.
2. Pokemon Yellow's battery save survives quit, sleep and poweroff.
3. A ROM copied by SFTP shows up in Explore.
4. Cold boot, NES/GB game and brightness keys: OK.

Observations, all taken into M3d:
- PSX (CTR) had severe slowdowns in its menu and intro cutscene on the
  first run, milder after a restart (cause: schedutil at the 1008 MHz floor,
  plus a CPU-heavy cutscene).
- Slight slowdowns right after waking from sleep, in every game (cause:
  the game resumed during the USB/Wi-Fi bring-up).
- Volume/brightness judder: the user rules it out for a final build.
- During the M3d T2 session: a bottom strip of the screen showing the top
  rows, persisting across a warm reboot (cause: the rk351 panel timing; M3d
  DTB).

**Recovery image:** M3c since 2026-11-12, M3b kept as the previous one.
M1 retired (its content is all in M2).

## M3b — boot chain from source, boot records, trial kernel, TRNG (done 2026-11-11, T3 passed)

Image `dist/firmware/test128-m3b-20261111.img.zst` (raw `2a8fec32…`).

**Reproduced first:** `build-boot.sh kernel-ref` (from scratch, Linaro
6.3.1, read-only linux-base, DTB built outside the tree) and `uboot-ref`
(`uboot-tree.py ref`) rebuild the M2 card's `Image` (`78093582…`), DTB
(`496bbe35…`) and `uboot.img` (`98c62e0b…`) byte for byte. The only
assembly drift was a docs path in a U-Boot DTS comment.

**Boot records instead of compiled-in pins:** the M2 U-Boot pinned the
size and SHA256 of `Image`/DTB, so every kernel change meant a bootloader
write, and its 0xec0000 kernel window had zero headroom (text_offset +
image_size of the M2 kernel = 0xec0000; the M3b kernel needs 0xed0000).
The M3b U-Boot (`muos_boot`) reads records at sectors 32/33/34 (main,
previous, trial; shared `bootrec.c`, CRC32), consumes an armed trial on
the card before trying it, verifies every file, falls through
trial → main → previous, and appends `muos_slot=` (trial: `panic=10`).
Kernel window 32 MiB at 0x02000000, the old window as fallback. Same
U-Boot config as M2 (diffed); `install-dtb.sh` retired.

**TRNG:** the DTB already enables `rockchip,cryptov2-rng`;
`HW_RANDOM_ROCKCHIP=y` alone left `tpm-rng` (no TPM; EIO) as the current
hwrng, because the 4.4 core keeps the first registered one, so
`HW_RANDOM_TPM` is off too. RNG ready at 2.58 s (was 7–11 s), no
"uninitialized urandom read" warnings. `Module.symvers` unchanged: the
pinned modules stay valid. Time to the UI is unchanged (~16 s).

**T0/T1:** `t0-boot.sh`: 19 U-Boot scenarios against mock U-Boot APIs
(ASan/UBSan: trial once and consumed before booti, bad/stale/oversized
files, corrupt records, window fallback, booti returning, no records);
record codec: C and Python encoders byte-identical, cross-decoding, all
512 single-byte corruptions rejected. ASan caught two harness bugs, none
in `boot.c`. Image stage: p1 `fsck.fat`, records and U-Boot read back.

**T2 (device):** new p2 via the trial root (audio, 3 sleep cycles); M2
records written; U-Boot written and read back (old region saved on p3);
first boot `muos_slot=main`. Trial kernel boots once with `panic=10`; the
next boot is main again; after the TPM fix the TRNG is current and
survives 5 sleep cycles; promoted. On hardware: corrupt main record →
previous; bad-SHA trial → consumed → main (`t2-boot-slot.sh` 4/4). Suite
on the M3b kernel: `t2-menu-cycle` 11/11, `t2-sleep-cycle --game` 3/3 and
5/5, `t2-headphone` PASS, NES 59.89 fps, audio soak 6/6 boots (one second
S95 attempt).

**T3 (2026-11-11, user):** 3 cold boots with sound, games, brightness
and in-game sleep/wake: OK. The M3b image was flashed with the host USB
card reader (`flash-card.sh host /dev/sdb … --grow`, its first real use):
`verified raw_sha256=2a8fec32…`, `p3 grown and clean`, cold boot to the
menu with sound. M3b became the recovery image; the reader is the primary
flash method (dArkOSen stays the fallback). Afterwards: the pre-flash
`pickles` restored byte-identical; `flash-card.sh host` now accepts only a
USB/removable/MMC whole disk and asks before writing (the host also has an
internal SATA `sda`).

**T3 observation: fps drops while changing volume/brightness in game.**
Measured with the new `t2-level-fps.sh` (keys injected through
`muos-press volup|voldown|fn+vol*`, i.e. the real muhotkey path); see
hardware-findings.md "Level-change judder". Upstream behaviour, not
fixed. The investigation found and fixed two test hazards: a T2 game run
autosaves on exit and replaced the user's state (`t2-game.lib.sh` now
snapshots and restores the ROM's pickles), and replacing
`MUOS/pickles` by rename leaves the `/run/muos/storage/pickles` bind on
the deleted directory (copy in place instead; `device.sh push` no longer
keeps the host uid).

## M3a.1 — audio regression fix (done 2026-11-11, T3 passed)

**M3a T3 (2026-11-11):** the built image flashed via dArkOSen (`verified
raw_sha256=2ac44673…`, `p3 grown and clean`) and boots: it is a working
recovery image for boot. Games, brightness and sleep/wake OK. **No sound
on any boot**, speaker or headphones, before and after the flash; the
headphone retest could not be judged. Battery showed 91% after a full
discharge with the charger in (→ M3d, see STATUS).

**Root cause:** muOS runs every SDL client with `SDL_AUDIODRIVER=pipewire`,
and the Buildroot-built SDL2 had only `alsa dsp disk dummy`, so
`SDL_Init(AUDIO)` failed ("Audio target 'pipewire' not available") and
nothing opened the PCM. Buildroot's pipewire depends on sdl2 (examples),
so a clean build configures SDL2 before PipeWire is in staging, and
SDL2's configure silently drops the driver. The Phase 4 tree had
PipeWire installed when SDL2 was built. Two traps on the way:
- `sdl2-reconfigure` is not enough: with `--disable-dependency-tracking`
  `SDL_pipewire.o` is built but the driver table in `SDL_audio.o` stays
  stale. `sdl2-dirclean` + `all` works.
- String checks on the library (`libpipewire-0.3.so.0`) pass on that
  stale build; only asking SDL for its registered drivers is reliable.

**Fix:** `build-image.sh build` runs the new
`/usr/libexec/muos-sdl-audio-probe --require pipewire` (package
`muos-sdl-audio-probe`) under qemu against the target, rebuilds SDL2 if
needed and fails if it still lacks the driver; `image` repeats the qemu
check and `check-rootfs-contract.sh` checks the p2 image. SDL2 is back to
M2's size (1412240 bytes). The same ordering cost ffmpeg's SDL2 output
device (libavdevice −8 KB); nothing uses it. Lesson for inventory diffs:
a "rebuilt" ELF that shrank is a lost feature until explained.

**T2 probe:** M3a's probe printed `pcm=closed rate=0` and passed by eye.
`t2-audio-state.sh` now prints a verdict and exits non-zero unless the
PCM is RUNNING at 40–50 k frames/s, a PipeWire output stream exists, this
boot's audio log has an `SDL Init Success` and no failure, and a fresh SDL
client opens `pipewire@44100`. `t2-menu-cycle.sh` runs it in the menu
and in the game. Negative proof on the live silent M3a boot: `FAIL audio:
pcm=closed rate=0 no-stream sdl=fail15`.

**T2:** trial root: audio PASS, `t2-sleep-cycle` 5/5 (audio PASS after),
`t2-headphone` PASS, `t2-menu-cycle` 11/11 (menu 44.1 kHz, game 48 kHz).
p2 written from the trial root, read back `1b3995a2…`. New p2: audio
soak 6/6 boots PASS (one second S95 attempt), `t2-menu-cycle` 11/11,
`t2-sleep-cycle --game` 3/3, `t2-headphone` PASS, NES SMB3 59.90 fps.
Image `dist/firmware/test128-m3a1-20261111.img.zst` (raw `112db539…`).

**T3 (2026-11-11):** sound on 3 boots, speaker and headphones; the volume
keys work. Headphones: fully inserted is not detected (the speaker keeps
playing) and only some frequencies drop: hardware, see STATUS. Per-output
volume is shared at T3 (no jack event); the user deprioritized it.

## M3a — reproducible image + e2fsck (T2 done 2026-11-11; T3: flashes and boots, silent → M3a.1)

Commits `e7d67a2` (build, trial root, e2fsck), `76d9aec` (script
retirement). Image `dist/firmware/test128-m3a-20261111.img.zst`.

**Disk first:** retired the synthetic capture fixtures and the unused
Mali SDK libs, then (user decision) the Phase 4 raw card captures and all
non-project podman images: host free space 61 → 68 GiB before the build,
62 GiB after it (`build/m3a/output` 9.8 G); podman images 15.0 → 4.6 GB.

**Inventory** (3462 p2 paths, sha256 per file, via a bind mount of `/` so
S90/S91 binds don't hide p2 content): all but 6 files were in the port
overlay or byte-identical to a host build output. Final diff of the
built target against the live p2: 3204 identical, 57 overlay, 90 rebuilt
ELFs (plus the user tables, completed at image time), 9 symlink/file
swaps (e2fsprogs replaces BusyBox links; proper library symlinks), 73
new (e2fsprogs, libs, jimtcl), 12 removed (Buildroot's S50dropbear, the
usb_modeswitch udev dispatcher, ifupdown/wpa defaults, hwdb sources,
PipeWire raop/ffmpeg plugins) and 101 dropped (C-step probes, legacy
session/save-store packages, the M1 backups, trial and seed state).
Seven tuned files under `/opt/muos` and `/etc/default` (audio path
`SPK_HP`, the C30 WirePlumber settings, input on, the saved
`asound.state`, ...) differ from the package defaults; the live content
is pinned.

**Build:** the cross toolchain and all packages from scratch in about
50 min (16 jobs). One fix: the container exported `TARGET=all`, which
muinput's Makefile (`TARGET ?= muinput`) picked up; variables are now
`M3A_*`.

**T1:** `t1-shim.sh` (no marker, trial, failure at each of 8 steps
before `pivot_root` → p2, marker consumed); `t1-elf-deps.sh`: 320
dynamic ELFs resolve with the target ld.so under qemu; e2fsck 1.47.2,
jq, dropbear, wpa_supplicant run. Image: fsck clean, label ROOTFS,
4.4-safe features, dbus/pipewire users, BusyBox 04755, identity copied
(byte-compared).

**T2 on the trial root:** boot to menu (rc done 16.6 s, all services
rc=0), `t2-sleep-cycle` 5/5, `t2-headphone` PASS, audio probe healthy,
NES SMB3 59.91 fps; `t2-menu-cycle` 7/8: the only failure was "p3 needed
journal recovery", expected because the trial root runs from p3.
**p2 written** from the trial root in 2 m 43 s, read back
`a21a4186…`; old p2 saved (`d5d9a5b6…`).

**T2 on the new p2:** `t2-menu-cycle` 9/9 (p3 clean after the reboot),
`t2-sleep-cycle` 10/10, `t2-headphone` PASS, NES 59.90 fps; 6-reboot
soak: audio up on 6/6 (one second attempt), `e2fsck -p rc=0` every boot;
the first boot after the trial replayed p3's journal in 0.16 s.

## M2.1 — battery indicator, per-output volume, audio start retry

Done 2026-11-11 (`8114513`, installed in place on the M2 card).

**Fixes:**
- **Battery indicator:** the Phase 3 staging profile shipped
  `visual/battery=3` (hidden). The rootfs default and the staging profile
  are now `2` (upstream: icon + percent). S91 migrates an existing p3
  config once (`MUOS/port/.migrations`).
- **Per-output volume:** `muos-headphone` does upstream's
  `SWITCH_OUTPUT_VOLUME` (`/run/muos/headphones` flag +
  `SAVE/LOAD_SINK_VOLUME`), so each output keeps its own level.
- **Silence after boot (root cause found):** on some boots WirePlumber's
  ALSA device enumerates no profile (empty `EnumProfile`, no sink).
  Upstream S80pipewire gives up after its 3 s node budget, and S95 then
  ran the whole boot silent. Caught live on 2 of 13 warm reboots; two bad
  boots in a row look like "reboot didn't fix it". It's not codec state:
  the RK817 playback registers and the 44.1 kHz PCM rate were identical
  across reboots and 5 sleep cycles (`port/scripts/t2-audio-state.sh`).
  - S95 now retries the full audio start (prime + S80 + sink wait) up to
    3 times within 25 s, records `/run/muos/core/audio-attempts`, keeps
    each failed attempt's `pw-dump`, and writes a codec/PCM snapshot to
    p3 `MUOS/log/system/audio-codec.txt` every boot.
  - Soak (15 warm reboots): audio up on 15/15; 2 needed the second
    attempt, none a third.

**T2:** `t2-headphone.sh` PASS (plug → HP with its own level, unplug →
speaker level restored, replug → HP level restored); 15-reboot audio soak.

**T3 (2026-11-11, `build/t3-m21.txt`):**

| # | Check | Result |
|---|---|---|
| 1 | Battery icon + % | OK |
| 2 | Charging icon | OK |
| 3 | % drops while playing | OK. Observation: 84% → 100% within about 20 s of plugging the charger |
| 4 | Per-output volume | FAIL as seen: speaker and headphones shared one level |
| 5 | Sound on 3 boots | OK |

**Analysis of the observations** (done after T3 over SSH):
- **Item 4 is a jack detection problem, not a volume logic problem.**
  muOS writes an output's level file on every volume key press. The
  headphone slot (`share/volume/48dc3513`) was last written at 02:31 UTC,
  during the T2 run and before the M2.1 commit at 02:46. During the T3
  session only the speaker slot changed (03:08). So the jack never
  reported "inserted" while the volume was being changed. The user found
  that the plug sounds right only when partly inserted; in that position
  the detect contact is open, the path stays `SPK_HP`, and both outputs
  share one level. A full insertion is detected (M2 T3 item 7). It gets
  retested at full insertion in the next T3.
- **Headphones quieter when fully inserted: hardware**, as the user
  suspected (same on ArkOS). The RK817 registers 0x12–0x4f under the
  `HP` and `SPK_HP` paths differ only in `ADAC_CFG1` bit 2 (class-D DAC
  power). The HP opamp setup and the digital level (`DDAC_VOL` 0x0a) are
  identical: this kernel is built with `ARCH_ROCKCHIP_ODROIDGOA`, so the
  path switch doesn't apply the DT `hp-volume`. The M2 "HP much quieter"
  report has the same cause.
- **Battery jump on charge:** the % is the RK817 BSP fuel gauge's
  `capacity` (mubattery passes it through: sysfs 88 = `/run/muos/battery`
  88). The gauge re-estimates when charging starts. Calibration (DT OCV
  table, or muOS's voltage-curve mode) is deferred to M3d.
- **Lost evidence:** the per-boot logs of the plug test were overwritten
  by item 5's reboots (S91 kept one previous boot). S91 now keeps three
  (`MUOS/log/system.prev`, `.prev2`, `.prev3`).

**M2.1 T3 checklist (done):**
1. Battery indicator top-right: icon and %.
2. Charger in, about 10 s: charging icon; out: normal.
3. Unplugged, play 10–15 min: % drops a few points.
4. Headphones in, raise the volume, unplug: speaker back at its own
   level; replug: the HP level is back. If 100% is too quiet, try
   Overdrive.
5. Power cycle or Reboot 3 times: sound in the menu every time.

## M2 — power, battery, cpufreq

Done 2026-11-11 (`03aa053`, `925c7bd`, `0154772`, `af33e99`). Image:
`test128-m2-20261111.img.zst`.

**What it added** (details in procedures.md "Boot and runtime"): upstream
Power-key sleep/resume, the shutdown timer, charging fake sleep, the
battery service and low-battery poweroff, the headphone path follower,
writable cpufreq with per-content governors. The 1512 MHz DTB was tried
and reverted: the port U-Boot pins `Image` and the DTB.

**T2 (2026-11-11):**
- **NES fps.** Measured by `port/scripts/t2-nes-fps.sh` with muxretro's
  own frame-time capture (`MUXRETRO_PERF_CAPTURE`; the "Content rate" log
  line is audio-derived, not fps), 60 s after a 10 s warm-up:

  | Run | ROM | fps | frame / core / present ms | CPU, governor |
  |---|---|---|---|---|
  | before (cpufreq ro) | Super Mario Bros. 3 (MMC3) | 59.90 | 16.69 / 5.88 / 10.60 | 1296 MHz, performance |
  | after (writable) | Super Mario Bros. 3 | 59.89 | 16.70 / 7.09 / 9.35 | 1296 MHz, schedutil |
  | before | r35s-flight (MIT demo) | 51.61 | 19.38 / 13.47 / 5.70 | 1296 MHz, performance |
  | after | r35s-flight | 51.56 | 19.40 / 13.50 / 5.69 | 1296 MHz, performance (muxretro boost) |

  A real game runs at full speed (vsync-locked to the 59.94 Hz panel).
  Only the synthetic demo ROM is slow; the old C47 "51.4 fps" figure was
  that ROM. Writable cpufreq doesn't change fps; the menu now idles at
  1008 MHz.
- **Sleep:** 20/20 Power-key cycles (`port/scripts/t2-sleep-cycle.sh`;
  injected press, `mem`, RTC wake), 3 in game (auto-save, pause, resume
  on SIGUSR2). Each cycle: backlight restored, Wi-Fi/SSH back first try.
- **Charging fake sleep:** screen off, frontend stopped; a second press
  wakes it.
- **Battery:** `/run/muos/battery` 100%, 4150 mV, charging=1. The
  low-battery logic (overlay, clean critical poweroff) passed at T1.
- **Regression:** `t2-menu-cycle.sh` 9/9.

**T3 (2026-11-11, `build/t3-m2.txt`):**

| # | Check | Result |
|---|---|---|
| 1–3 | Physical Power short/long press, in menu and in game | OK |
| 4 | Shutdown timer after 10 min asleep | OK |
| 5 | Charging | PARTIAL: fake sleep OK (instant wake, dongle stayed on); no charging icon → M2.1 |
| 6 | Battery % | NOT TESTABLE: no indicator in the status bar → M2.1 |
| 7 | Headphones | OK polarity; HP much quieter than the speaker (hardware, see M2.1) |
| 8 | NES SMB3 | OK |
| 9 | Hard power cut | OK |
| — | Observation | No sound after the hand-over; a menu reboot didn't fix it, a hard power cut did → M2.1 |

**M2 T3 checklist (done):**
1. Short Power in the menu: dark within 2 s; again: menu back within 3 s,
   Wi-Fi/SSH back.
2. Power in a game, wait 20 s, Power: the game continues with sound.
3. Hold Power about 1 s: same sleep (upstream behaviour). ≥ 6 s is the
   PMIC hard cut.
4. Unplugged, sleep for more than 10 min: clean poweroff; next boot has
   the GB save.
5. Charger in: charging icon; Power gives fake sleep, Power wakes.
6. Unplugged, play 10 min: % drops plausibly.
7. Headphones in: sound only there; out: back on the speaker.
8. NES SMB3 for 2 min: full speed, clean audio.
9. Optional: hard power cut in game, boot: the menu and the last save.

## M1 — recovery image, autostart, seedless init

Done 2026-11-10. Image: `test128-m1-20261110.img.zst`.

**Delivered:** a flashable recovery image; boot straight into the muOS
frontend through standard BusyBox rcS/rcK-style init; retirement of the
C-step safety harness.

**T2:**
- Autostart to the menu on more than 15 boots of the new init, one of
  them seedless; rcS done at about 15 s.
- `port/scripts/t2-menu-cycle.sh` passed 4 times in full, driving the
  real buttons by evdev injection (`/usr/libexec/muos-press`): menu →
  Explore → GB → private.gb at 59.73 Hz; Fn+R2 quick save (to p3) and
  Fn+L2 quick load; Fn+Start → Explore; launcher Reboot → ordered rcK →
  p3 clean → state persisted → menu.
- Prefs: 55/70 imported into the persistent config.
- Degraded audio: if audio fails to start, the menu still works.
- Panel timing measured (hardware-findings).
- T0/T1: shellcheck on all new scripts; container tests for the
  installer, the trial boot, the frontend loop and the file-target flash;
  fsck and content checks of both images; a p3 grow test; AST import
  check of all 425 kept Python files.

**T3 (2026-11-10).** The first flash attempt failed at verification
(dArkOSen's sudo PATH has no sbin; fixed in `9bf8f80`); the rerun
verified the card and grew p3 to 116.6 GiB.

| # | Check | Result |
|---|---|---|
| 1 | Flash via dArkOSen slot 2 | OK |
| 2 | Cold boot to menu | OK (menu at ~15.5 s) |
| 3 | GB save/load/quit | OK |
| 4 | Menu reboot, persistence | OK. Relaunching resumed the last state without Fn+L2: muxretro's default `auto_save=3` (idle + quit) writes `autosave.state` on quit and loads it at the next launch. Expected muOS behaviour. |
| 5 | Menu shutdown, power on | OK |
| 6 | Power key / speaker | OK |

**M1 T3 checklist (done):**
1. Flash the M1 image via dArkOSen: `verified raw_sha256=1c65c693…`,
   `p3 grown and clean`.
2. Cold boot: the menu without any SSH step in 15–25 s.
3. GB: play, Fn+R2, move on, Fn+L2 → back at the save; Fn+Start → list.
4. Menu Reboot: volume/brightness unchanged; the state still loads.
5. Menu Shutdown: screen off within 5 s; power on → menu.
6. Optional: Power key (nothing yet), speaker sound.

**Seed investigation.** The "seed" was the SeedRNG entropy file
(`/var/lib/muos-seedrng/seed.*`), created by Buildroot's seedrng through
the C05 `S05muos-entropy` wrapper. Only the network script's "RNG ready"
gate depended on it (so dropbear's host key was generated with a ready
RNG; readiness takes 7–11 s on 4.4 with no HW RNG). The "never replay"
rule protected RNG freshness across p2 restores, which doesn't matter on
a dev card. Decision: retire the gate and the wrapper; stock seedrng
still runs; images ship without `seed.*`; the dropbear host key stays in
the image so the fingerprint survives a reflash.

**Retired in M1:**
- Card/CID guards: the C01/C07 bootstrap and `card-guard.sh` (they broke
  every flashed copy and halted with original32 in slot 2).
- Marker files: `/etc/muos-*-diagnostic`, `/etc/muos-private-foundation`,
  `DIAG.ID` checks.
- The boot-seq counter and `.once` tokens (`/var/lib/muos-diagnostic`).
- Consumed claims (host-only).
- Hash guards: foundation-89, "guard 200", the resident/batch manifests,
  the hash-pinned retention dependency trace.
- Seed/counter anti-replay and "never write test128".
- Device payloads: the C01–C25 dispatchers, capsules, caller, batch and
  resident packages, the UI supervisor, MUOSSAV1 `muos-save-store`,
  `S05muos-entropy`, `S98muos-session`. A tar is on p3 at
  `MUOS/port-legacy-c07.tar`; the baseline image keeps them all.
- Host: 223 one-off C-step scripts and fixtures; they stay in Git at
  `ea2f7d8`.

**Contradictions resolved in M1:**
- Panel timing: the port DTB is 29 MHz / 732×661 / 59.94 Hz (measured
  three ways); the stock dArkOSen DTB is 50 MHz / ≈61.2 Hz. The two docs
  described different DTBs.
- The roadmap marks Phase 4 done and Phase 5 in progress.
- Warm Wi-Fi: fixed since C18; the "replug needed" archive notes are
  historical.
- The C123 guard is obsolete (guards retired).
