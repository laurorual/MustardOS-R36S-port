# Project status

Current state only; update at the end of every milestone. Release plan:
[roadmap.md](roadmap.md); answered decisions: [decisions.md](decisions.md);
licences: [LICENSING.md](LICENSING.md); how-tos: [procedures.md](procedures.md);
finished milestones: [milestones.md](milestones.md) (M1–M7 in
[archive/](archive/milestones-m1-m7.md)); hardware facts:
[hardware-findings.md](hardware-findings.md); host storage:
[storage.md](storage.md).

## Current phase

Phase 5 (own-card firmware). M1–M8 done. **Current: M9 — public v1.0**
(started 2026-11-22). Since 2026-11-25 licences and publication come
first in every session, polish after (decision 37). m9a is the recovery
image until 2026-11-25, then m9d, then m9f; **m9k** (the developer twin
of **v1.0.0**, whose T3 passed 2026-11-26) is the recovery image now.
v1.0.0 is tagged at `452e465` and pushed (by the user, 2026-11-26); the
GitHub release is **not created yet**: the API answered 403 "Resource
not accessible by personal access token" (the token reads the repository
but lacks Contents: write; `git push` works through the user's SSH key).
After the user fixes the token, `build/release/publish-v1.0.0.sh`
(re-runnable: reuses the tag, an existing release and uploaded assets)
creates the release with the notes and the 8 assets and pushes main.

## Device and bench

- **Bench (2026-11-26):** test128 back in slot 1 (flashed with m9f by the
  user, p3 restored from `build/m8/p3-backup/p3.tar`), then updated
  through the update path to **m9k** (p2 = m9k; main = `Image-494d1c3d5ebd`
  + the undervolt DTB `panel0-84611ef0394d.dtb`). original32 holds the
  public pre-final v1.0.0 build (same release name as the published one:
  auto-update sees it as current). Slot 2 with ext4 tested ok on rc2.
- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0), test128
  in slot 1 (mmcblk0 by DT alias), slot 2 empty. `user_init` = 0, time
  zone −03. Access, identity and card layout: procedures.md.
- **p2 = m9k** (2026-11-26, through the update path). p1 `bootlogo.bmp`
  = the press-kit logo (`d6e6d189…`).
- Charge log of 2026-11-25 stopped (`build/logs/discharge/discharge.csv`).
- **Boot records:** main = `Image-494d1c3d5ebd` (patch 0011) +
  `panel0-84611ef0394d.dtb` (undervolt CPU −50 / GPU −25 mV); previous =
  `Image-be499e33d4eb` + the same DTB (promoted 2026-11-25 after the
  trial-boot T2; `t2-boot-slot.sh` 4/4). p1 has all 16 undervolt DTBs
  and `dtb-variants.txt`.
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
| `dist/firmware/MustardOS-R36S-port-v1.0.0.img.xz` (xz `a308dccd…`, raw `b762425f…`, p2 `9cf48944…`) + `.img.zst`, `.p2.img.gz`/`.sha256` | **public v1.0.0** (Build = v1.0.0); 29 checks | tag pushed; release pending (token, see "Current phase"); T3 ok 2026-11-26 |
| **`dist/firmware/test128-m9k-20261126.img.zst`** (raw `3e487ae1…`, p2 `43779504…`) | v1.0.0 rootfs + kernel, developer variant | on the bench; T2: update rounds with progress screens, NES 59.96; **recovery since 2026-11-26** (v1.0.0 T3 ok) |
| (v1.0.0-rc2 public) | on GitHub (pre-release); local files deleted 2026-11-26 | T3 ok 2026-11-25 |
| (m9f) | the rc2 developer twin | retired 2026-11-26 (m9k recovery) |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2 | **base of every image build**; never retire |

2/5 versions in `storage-retention.json` (M2, m9k+v1.0.0; m9c,
m9d+rc1, m9f, m9g, m9h, m9i retired and the p3 backup tar deleted 2026-11-26).

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

- **Licences/publication (M9 priority):** closed to T2 (LICENSING.md);
  repository public since 2026-11-25 (pushed by the user); open: rc1
  T3, the source bundle and the GitHub release (decisions 40–41).
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
- **Standalone N64:** no volume/brightness bar; screenshots give no
  feedback. muxretro has no capture.
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

None open (43–46 answered 2026-11-25: variants and dongles after v1.0,
MustardOS 2606.0 for v1.0, the bench change).

## T3 queue

Empty: the v1.0.0 checklist (update screens, Build = v1.0.0, Task Toolkit
in Português, Wi-Fi at power-on) passed 2026-11-26.

## Current milestone: M9 — public v1.0

Plan in roadmap.md M9 (rewritten 2026-11-25). Done before 2026-11-25:
M8g T3 fixes, ScummVM standalone default, CJK overlays, undervolt rows,
THIRD-PARTY.txt, `make-source-bundle.sh` (first version), public variant
checks (18 pass), the update path (`muos-update`, auto-update).

History of the M9 rounds (licences, rc1, rc2, kernel updates, v1.0.0):
milestones.md M9. v1.0.0 T3 ok 2026-11-26. **Left:** the GitHub release
(token fix, then the publish script). README states that only Panel 0
and the RTL8821CU are implemented and tested, other DTBs and dongles
planned, feedback welcome.

**Next: M10 — experimental hardware reach** (roadmap "After v1.0",
decisions 43–44): other Wi-Fi dongles (USB-ID → module table, firmware
with licences, worker for any wireless driver) first, as it needs no
bootloader write; then the R36S variant DTBs (dArkOSen 640x480 set with
the port's DT deltas, card-root selectors, U-Boot `variant.dtb` rule:
bench U-Boot write with the user present). The next MustardOS release
(decision 45) follows as M11.
