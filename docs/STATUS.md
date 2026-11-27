# Project status

Current state only; update at the end of every milestone. Release plan:
[roadmap.md](roadmap.md); answered decisions: [decisions.md](decisions.md);
licences: [LICENSING.md](LICENSING.md); how-tos: [procedures.md](procedures.md);
finished milestones: [milestones.md](milestones.md) (M1–M7 in
[archive/](archive/milestones-m1-m7.md)); hardware facts:
[hardware-findings.md](hardware-findings.md); host storage:
[storage.md](storage.md).

## Current phase

Phase 5 (own-card firmware). M1–M12 done: **v1.1.1 published 2026-11-27**
(GitHub release, latest; M11 PortMaster + M12 PICO-8, decision 48; v1.1.0
and v1.0.0 before it). v1.1.1 T3 round 4 passed; m12f is the recovery
image. **Next: M13**, First Boot and the games card format (decision 50).

## Device and bench

- **Bench (2026-11-27):** test128 in slot 1, **p2 = m12f**, installed
  through the new Task Toolkit "Check for Online Update" (the m12f p2
  served as a local "v9.9.9" by `t2-online-update.sh serve`: download,
  unpack, trial boot, finishing screen, write-p2; the previous p2, m12e,
  in `MUOS/trial/p2-previous.img`). m12e before it (`t2-levelbar.sh` +
  `t2-quit-fade.sh` + `t2-pico8.sh` + `t2-portmaster.sh` PASS). PortMaster reinstalled
  on p3 2026-11-26 (a trial reboot during its source update corrupted
  `config/020_portmaster.source.json`); the user's Doukutsu-rs kept. p3 test
  content: PortMaster with sdlsopwith, turbotabletennis, 2048; ROMS/PICO-8
  `ld45.p8`, `cartparsetest.p8.png`; the user's official PICO-8 0.2.7 in
  `MUOS/bios/pico8` (private: never in an image) and the Splore app. Before:
  the update path m9k → m10a (boot records: main = `Image-494d1c3d5ebd` + the
  undervolt DTB `panel0-84611ef0394d.dtb`, previous = the same kernel +
  the stock DTB `panel0-c97151d0ec1a.dtb` since the model T2). p1 has
  the 22 model DTBs, `models.txt` and the selectors. original32 holds
  the public v1.1.0 (updated from v1.0.0 in the T3; `model.txt` =
  `default`; password SSH on port 22, root/`root`, used read-only for
  the RTL8822BU dongle info) with a TP-Link RTL8822BU dongle (2357:0115).
- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0), test128
  in slot 1 (mmcblk0 by DT alias), slot 2 empty. `user_init` = 0, time
  zone −03. Access, identity and card layout: procedures.md.
- p2 = m12f (see "Bench"). p1 `bootlogo.bmp` = the press-kit logo
  (`d6e6d189…`).
- Charge log of 2026-11-25 stopped (`build/logs/discharge/discharge.csv`).
- **Boot records:** see "Bench". p1 has all 16 undervolt DTBs, the 21
  distinct model DTBs and `dtb-variants.txt` (22 `m-` keys).
- **p3:** ROMs (also in `port/roms/`; systems listed in milestones M8),
  Wi-Fi profile `Home.ini`, the six themes, BIOS (PSX, DC, Saturn, Sega
  CD, PCE CD). T2 data in `MUOS/t2` (God of War states `state-v120` /
  `state-v112`, DC fight states `dc-fight` / `dc-fight-2022`; `ppsspp-2021`,
  `drastic`, `m1-backup`, `emu` are removable), CTR state in
  `MUOS/port/t2/ctr-race`, ScummVM test game (Monkey Island).
- **original32 (stock dArkOSen):** the flasher station only. Never write it.
- `refs/darkosen` at `28f5427`; its `.git` is 361 MB (a fresh blobless
  clone would free ~340 MB: the user's call, refs/ is read-only).

## Recovery image

Developer images are **private** (Wi-Fi PSK, SSH host key,
authorized_keys): never commit or share them. Flashing rewrites the whole
card, bootloader included (procedures.md).

| Image | Content | State |
|---|---|---|
| **`dist/firmware/test128-m12f.img.zst`** (raw `8b9df957…`, p2 `6a29a226…`, `build/m3a/test128-m12f.p2.img`) | M11 + M12 + the v1.1.1 T3 fixes + manual online update | v1.1.1 T3 round 4 ok; **recovery since 2026-11-27** (m12e retired); on the bench p2 |
| (v1.1.1 public, m12f) | on GitHub (release, latest; raw `d5187bd2…`, p2 `4068786a…`); local images, raw p2 and source zips deleted 2026-11-27 (manifest kept) | T3 ok 2026-11-27 |
| (v1.1.0 public, m10a) | on GitHub (release); local files and m10a retired 2026-11-27 | T3 ok 2026-11-26 |
| (v1.0.0 public, m9k) | on GitHub (release); local files and m9k retired 2026-11-26 (m10a recovery) | T3 ok 2026-11-26 |
| (v1.0.0-rc2 public) | on GitHub (pre-release); local files deleted 2026-11-26 | T3 ok 2026-11-25 |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2 | **base of every image build**; never retire |

2/5 versions in `storage-retention.json` (M2, m12f; m12e, m10a+v1.1.0,
m12b–m12d, m9k+v1.0.0 and earlier retired 2026-11-26/27). `build/release`
keeps only the v1.1.1 publish script and notes (the template).

## What works (T3-confirmed)

Display, controls, frontend and submenus; volume/brightness with the
in-game bar; speaker audio and headphone switching; Wi-Fi (profiles,
scan, sleep/wake, toggle, replug) + SSH/SFTP (jailed); time zone/NTP;
battery %, icons, low-battery poweroff, empty splash; sleep/resume,
shutdown timer, charging fake sleep; themes, profiles, Task Toolkit,
search, activity, screenshots (menu); GB, NES, SNES, GBA, MD, PSX, 32X,
2600, 7800, GG, Lynx, SMS, PCE, Sega CD, PCE CD; N64 (standalone Rice);
PSP (v1.12.3, frameskip 1), NDS (advanced DraStic), DC (Flycast 2022),
Saturn (standalone YabaSanshiro, slow); ScummVM core + standalone with
the virtual keyboard; pt-BR and CJK menus; the Undervolt rows; the
firmware update task; flashing with a host card reader; p3 auto-grow;
power-cut recovery. Full list per milestone in milestones.md.

## Open problems

- **Licences/publication:** v1.0.0 and v1.1.0 published (LICENSING.md; Hardkernel
  answered without a position, decision 47; Exophase and steward-fu
  still silent).
- **Battery % short of 100 on the charger — fixed (patch 0011, rc2 T3
  ok)** (2026-11-19:
  95 % after a night; FCC learned down to 2550 mAh). The driver's finish
  step (dsoc +1 % per ~92 s, only in MODE_FINISH) never ran: the next
  boot read rsoc 92.9 %, OCV 4149 mV, so the charge itself stopped
  short. **Cause found (charge log 2026-11-25, 23 → 98 % in 2 h):** the
  coulomb counter reaches FCC (rsoc 100.000 %) while dsoc sits at 98 %,
  taper still at 140–240 mA. `rk817_bat_fake_finish_mode()` tests
  `rsoc == 100`, but rsoc is in thousandths (other checks use
  `100 * 1000`), so fake finish never fires and dsoc only reaches 100
  on the PMIC's own CHARGE_FINISH (CHG_STS even read "off" in the
  taper; `update_info` also reset the finish timer). Patch 0011:
  98 → 100 % "Full" 2 min after boot (hardware-findings "End of charge").
- **Wi-Fi:** stuck scans at power-on (dongle reset at 20 s since m9c,
  T3 ok 2026-11-26); warm-reboot H2C (1 in 7); a real zombie occurrence is
  unverified (watchdog tested with injected errors only).
- **Heavy systems:** held by heat, not by the clock cap (hardware-findings
  "M8 thermal block"); play them on battery. Saturn too heavy for Sonic R.
- **Audio:** occasional PipeWire sink stall (self-healed before each
  game, root cause open); 200 % overdrive distorts (as upstream).
- **User report (2026-11-26, another user, DTB "R36S-V12 2023-08-18
  Panel 4"):** a black screen while changing settings, and the B/back
  button also lowered the volume. No `MUOS/log` (muOS already removed).
  The user's own dArkOSen DTB (`build/rk3326-r36s-linux.dtb`, sha256
  `ebf08da5…`, 2026-11-27) is dArkOSen's own Panel 4 DTB of 2026-08-31
  (commit 7b30ae7, blob 2176862b; the user runs that dArkOSen). dArkOSen
  then dropped the GPU 600 MHz OPP (09-18) and, in its final update
  (11-14, our pin), set the native 60Hz mode's **vfront-porch 16 → 165**
  (~77 Hz → 59.94 Hz), CPU max-volt 1.40 → 1.35 V (the kernel drops the
  OPPs above it: no instability; Panel 0 has the same cap), the battery
  table 3140 → 3380 mAh, slot 2 to 3.3 V and compatible odroidgo3 →
  r36s. arkos4clone's "origin panel4 type1" keeps vfp 16. Inputs
  (joypad, gpio-keys, ADC, GPIOs and codes) are identical in all of them:
  B + volume is not the DTB. The timing is the only display change
  between his working DTB and ours: the black-screen suspect. Cheap
  cross-check for him: dArkOSen's final (11-14) release.
  **Test build for that user (2026-11-27):**
  `dist/firmware/MustardOS-R36S-port-v1.1.1-p4test.img.xz` (sha256
  `4344ae80…`, raw `9805db59…`; 0f5bff9, all public checks ok) = v1.1.1 +
  the selector entry "R36S-V12 2023-08-18 Panel 4 (vfp 16, test)"
  (`models.txt` "+BASE" line). T2: that DTB with the port battery node
  boots the bench at 640x480p77 (V 480/496/498/512), menu up, same input
  names, NES 60.16 fps. Waiting for the user's result; then keep the entry
  (or make it Panel 4's default) or drop it, and retire `p4test`.
- **Menu:** "Direct Link", "Proxy Settings" and static addresses
  untested; one missed Power press in a 15-cycle soak (logged since M8).
- **Pinned, not rebuilt:** idbloader/trust (rkbin files, identical to
  rkbin).
- **Hardware:** headphone jack contact (deprioritized); slot 2 fails only
  with the spare card (closed); no controllable LEDs; DDR devfreq not
  synced to the VOP.
- **Trial root:** p3 can't be unmounted at shutdown while it runs.
- **p2 space:** 1 GiB, ~318 MB free.

## Decisions for the user

None open.

## T3 queue

Empty (v1.1.1 round 4 passed 2026-11-27; results in milestones.md).

## Current milestone: M13 — First Boot and the games card format (started 2026-11-27)

Goal (decision 50): a fresh public card starts in MustardOS's own first
boot (the pin's `muxinstall` in muxfrontend: Date and Time, Language,
Profiles, Input Tester, Shutdown, Install); Install asks exFAT
(recommended) / FAT32 / EXT4 for the games storage, so Windows can copy
ROMs. Host-only for now (the bench is off for the panel); T2 when it is on.

Design (the port keeps its state on p3, unlike upstream's system
partition): EXT4 = today's layout (p3 grown to the card). exFAT/FAT32 = p3
ext4 kept at 4–6 GiB for the port's state (MUOS/port config, logs,
update and trial root, preferences) and a new **p4** in the chosen format
for the content (ROMS and the MUOS folders upstream keeps on SD1: bios,
save, pickles, theme, network, screenshot, PortMaster, ...), mounted at
/mnt/content and bound at /mnt/mmc. Robust to power loss where the system
needs it, nothing the trial root or the shim reads moves. Existing cards
(factory_reset 0 in their p3 config) keep one ext4 p3 through updates.

Items:
1. Rootfs: exfatprogs, dosfstools (mkfs/fsck/label), so the installer
   offers all three formats.
2. Public image: `boot/factory_reset` 1 (developer 0); S89 leaves p3
   ungrown on a factory rootfs (Install sizes it).
3. Install (`muos-install-storage`, progress screen via task_autorun):
   ext4 → grow p3; exFAT/FAT32 → p3 to 4–6 GiB + p4 (type 07/0c) to the
   end, mkfs, factory_reset 0, restart. Idempotent after a power cut.
4. S89 mounts p4 (fsck.exfat -p / fsck.fat -a / e2fsck -p, then exfat
   module + mount); S90 binds the content root (p4 or p3) at /mnt/mmc.
5. Content paths to /mnt/mmc (S91 ROMS folders, PICO-8, Splore, ScummVM,
   BIOS paths, screenshots, saves); port state stays on /userdata;
   muos-update also reads updates dropped in the content's MUOS/update.
6. Content-fs limits: no symlinks/chmod on exFAT/FAT32 (ScummVM links,
   PortMaster chmod) handled.
7. Texts in 33 languages (task-texts), check-public-image checks, docs
   (README first boot + Windows, procedures card layout, findings,
   LICENSING for exfatprogs GPL-2.0 / dosfstools GPL-3.0).
Tests: T0 shellcheck, task-texts check; T1 the install script against
disk image files under qemu (sfdisk, mkfs.exfat/fat, fsck), public-image
checks. T2 (bench on): a fresh public-variant p3 in a trial (dev access),
each format, PortMaster, update from the content MUOS/update. Expected
T3: the six screens on a blank card, Windows sees the games drive, copy a
ROM, play it, an online update keeps everything.
**Progress (2026-11-27, host only):** items 1–7 implemented
(65f7222 + the S89 retry fix): T0 shellcheck clean, task-texts current;
T1 `t1-install-storage.sh` PASS (exfat 32 GiB → p3 6 GiB + p4 type 7,
repeated; vfat on that table, type c; ext4 removes p4; 12 GiB → p3
4 GiB; 6 GiB refused before any write; foreign disk id refused),
`t1-fresh-p3.sh` PASS. Public images also check factory_reset 1, the mkfs
and fsck tools, the install files and /mnt/content. Left for the release:
README / install guides (first boot, the games drive on Windows), known
issues, release notes, the LICENSING package count.
**T2 when the bench is on (user present: flash):** `card-p3.sh backup`;
flash `test128-m13a` (developer, MUOS_FIRST_BOOT=1) without `--grow`;
`t2-first-boot.sh pre`, `install exfat`, `install vfat`, `install ext4`;
then NES fps, PortMaster install, an update copied to p4 MUOS/update;
reflash the recovery image + `card-p3.sh restore`.

Then M14: the MustardOS next release (decision 45).
