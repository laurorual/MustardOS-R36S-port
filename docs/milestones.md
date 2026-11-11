# Completed milestones

Results and checklists of finished Phase 5 milestones, moved out of
[STATUS.md](STATUS.md). Newest first. The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## M3a — reproducible image + e2fsck (T2 done 2026-11-11, T3 pending)

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

**What it added** (details in STATUS.md "Boot and runtime"): upstream
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
