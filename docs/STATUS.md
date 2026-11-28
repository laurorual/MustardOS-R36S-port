# Project status

Current state only; update at the end of every milestone. Release plan:
[roadmap.md](roadmap.md); answered decisions: [decisions.md](decisions.md);
licences: [LICENSING.md](LICENSING.md); how-tos: [procedures.md](procedures.md);
finished milestones: [milestones.md](milestones.md) (M1–M7 in
[archive/](archive/milestones-m1-m7.md)); hardware facts:
[hardware-findings.md](hardware-findings.md); host storage:
[storage.md](storage.md).

## Current phase

Phase 5 (own-card firmware). M1–M13 done: **v1.1.2 ready to publish
2026-11-28** (M13 First Boot + games card format, port libraries; T3
round 2 ok; the user runs `build/release/publish-v1.1.2.sh`); v1.1.1
(2026-11-27) is GitHub's latest until then. m13e is the recovery image.
**Next: M14**, heavy-system emulators for v1.1.3 (decision 53).

## Device and bench

- **Bench (2026-11-28, v1.1.2 T3):** **test128 in slot 1**, p2 = the
  developer `test128-m13e` (trial-root T2 passed, written by write-p2;
  p2-previous = m12f in `MUOS/trial`, the only m12f copy left), p3 ext4 with all the test content
  (PortMaster with the T2 ports incl. Nonny, Dueling Dragons, Rockdodger,
  Cosmosmash, Jump'n'Bump; PICO-8 with the user's private official
  PICO-8, ROMs, T2 states); boot records main = `Image-494d1c3d5ebd` +
  the undervolt DTB, previous = the stock DTB. original32 (out) holds the
  public v1.1.2 candidate 2 on exFAT from T3 round 2. Wi-Fi dongle
  0bda:c820.
- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0), the
  bench card in slot 1 (mmcblk0 by DT alias), slot 2 empty. `user_init` = 0, time
  zone −03. Access, identity and card layout: procedures.md.
- p1 `bootlogo.bmp` = the press-kit logo (`d6e6d189…`).
- Charge log of 2026-11-25 stopped (`build/logs/discharge/discharge.csv`).
- **Boot records** (both cards): main = `Image-494d1c3d5ebd` + a Panel 0
  DTB; p1 has all 16 undervolt DTBs, the 21 distinct model DTBs and
  `dtb-variants.txt` (22 `m-` keys).
- **test128 p3:** ROMs (also in `port/roms/`; systems listed in milestones M8),
  Wi-Fi profile `Home.ini`, the six themes, BIOS (PSX, DC, Saturn, Sega
  CD, PCE CD). T2 data in `MUOS/t2` (God of War states `state-v120` /
  `state-v112`, DC fight states `dc-fight` / `dc-fight-2022`; `ppsspp-2021`,
  `drastic`, `m1-backup`, `emu` are removable), CTR state in
  `MUOS/port/t2/ctr-race`, ScummVM test game (Monkey Island).
- **original32:** the user's flash-test card (decision 52); flashed
  with the host reader like test128.
- `refs/darkosen` at `28f5427`; its `.git` is 361 MB (a fresh blobless
  clone would free ~340 MB: the user's call, refs/ is read-only).

## Recovery image

Developer images are **private** (Wi-Fi PSK, SSH host key,
authorized_keys): never commit or share them. Flashing rewrites the whole
card, bootloader included (procedures.md).

| Image | Content | State |
|---|---|---|
| **`dist/firmware/test128-m13e.img.zst`** (raw `011bcc4f…`, p2 `e80f5be2…`, `build/m3a/test128-m13e.p2.img`) | M13 + the v1.1.2 T3 round 1 fixes | **recovery since 2026-11-28** (m12f retired); on the test128 p2 |
| `dist/firmware/MustardOS-R36S-port-v1.1.2.*` (raw `166bccec…`, p2 `87992779…`) + `build/release/MustardOS-R36S-port-v1.1.2-source-{1,2}.zip` | v1.1.2 public (83976bf, the m13e rootfs), 45 checks | T3 round 2 ok 2026-11-28; **to publish** (delete the local files after) |
| (v1.1.1 public, m12f) | on GitHub (release, latest; raw `d5187bd2…`, p2 `4068786a…`); local files and m12f retired | T3 ok 2026-11-27 |
| (v1.1.0 public, m10a) | on GitHub (release); local files and m10a retired 2026-11-27 | T3 ok 2026-11-26 |
| (v1.0.0 public, m9k) | on GitHub (release); local files and m9k retired 2026-11-26 (m10a recovery) | T3 ok 2026-11-26 |
| (v1.0.0-rc2 public) | on GitHub (pre-release); local files deleted 2026-11-26 | T3 ok 2026-11-25 |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2 | **base of every image build**; never retire |

4/5 versions in `storage-retention.json` (M2, p4test, m13e,
v1.1.2-public; m12f, m13b–m13d and earlier retired). `build/release`:
the v1.1.2 source zips, notes and publish script (v1.1.1's as the
template).

## What works (T3-confirmed)

Display, controls, frontend and submenus; volume/brightness with the
in-game bar; speaker audio and headphone switching; Wi-Fi (profiles,
scan, sleep/wake, toggle, replug) + SSH/SFTP (jailed); time zone/NTP;
battery %, icons, low-battery poweroff, empty splash; sleep/resume,
shutdown timer, charging fake sleep; themes, profiles, Task Toolkit,
search, activity, screenshots (menu); GB, NES, SNES, GBA, MD, PSX, 32X,
2600, 7800, GG, Lynx, SMS, PCE, Sega CD, PCE CD; N64 (standalone Rice);
PSP (v1.12.3, frameskip 1), NDS (advanced DraStic), DC (Flycast 2022),
Saturn (standalone YabaSanshiro, slow); First Boot with Install as
exFAT/FAT32/EXT4; PortMaster ports needing the added libraries; ScummVM core + standalone with
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
  names, NES 60.16 fps. **Result (2026-11-27): no picture on his
  console.** Unknown yet: whether he chose the vfp-16 entry in the
  selector, waited through the first start (Panel 0 DTB first, black on
  Panel 4, then the model trial restart), and whether the regular Panel 4
  entry of the same build shows a picture; BOOT `model.txt` /
  `model.txt.failed` tell whether the trial reached the menu (logs are on
  the ext4 p3, unreadable on Windows).
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

None (decision 53: pirry's YabaSanshiro in v1.1.3; the rest of
[emulator-survey.md](emulator-survey.md) to analyse together).

## T3 queue

Empty (v1.1.2 T3 round 2 ok, 2026-11-28). After the publish: none.

## Current milestone: M14 — heavy-system emulators, v1.1.3 (decision 53)

Goal: pirry's YabaSanshiro as the Saturn default, built from source
(github.com/pirrypirrypirry/yabasanshiro-pirry, GPL-2.0; ROCKNIX's
`yabasanshiro-pirry-sa` recipe as a reference), then the survey items
the user picks (docs/emulator-survey.md).
Items (plan):
1. `build-yabasanshiro-pirry.sh` in the container (GLES3, our GCC 13
   sysroot), the port's patches carried over: muOS-Keys input map,
   SIGTERM quit (Fn+Start), the fps log for T2, state on exit if the
   other standalones do it; its per-game menu and settings kept.
2. `muos-yabasanshiro` picks it (`ext-yabasanshiro-pirry` default, the
   current one selectable); a migration moves Saturn folders that still
   carry the old default.
3. T2: Sonic R and two more games (fps log, presented frames, heat),
   quit, sleep/resume, BIOS and HLE.
4. Survey A/Bs the user approves (DSperate, Flycast 2021, ...).
Expected T3: Saturn games feel, the menu (Select), quit, states.
