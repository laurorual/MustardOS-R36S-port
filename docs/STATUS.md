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
image until 2026-11-25, then m9d; **m9f** (the developer twin of
**v1.0.0-rc2**, whose T3 passed 2026-11-25) is the recovery image now.
rc2 is a GitHub pre-release; **v1.0.0** (developer twin m9k) published
2026-11-26 by the agent with the user's token; its T3 is pending.

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
- **p2 = m9e** (2026-11-25 ~17:00, via the trial root after its T2; the
  previous p2, m9d, in `MUOS/trial/p2-previous.img`); m9f's p2 has the
  same files (only the release name differs). p1 `bootlogo.bmp` =
  the press-kit logo (`d6e6d189…`; the old one in
  `MUOS/trial/bootlogo.bmp.before`).
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
| `dist/firmware/MustardOS-R36S-port-v1.0.0.img.xz` (xz `a308dccd…`, raw `b762425f…`, p2 `9cf48944…`) + `.img.zst`, `.p2.img.gz`/`.sha256` | **public v1.0.0** (Build = v1.0.0); 29 checks | published 2026-11-26; T3 pending |
| `dist/firmware/test128-m9k-20261126.img.zst` (raw `3e487ae1…`, p2 `43779504…`) | v1.0.0 rootfs, developer variant | on the bench; T2: update rounds with progress screens, NES 59.96 |
| `dist/firmware/MustardOS-R36S-port-v1.0.0-rc2.img.xz` (xz `fa935564…`, raw `2c2e33e8…`, p2 `2ffa8678…`) + `.img.zst`, `.p2.img.gz`/`.sha256` | **public rc2**: rc1 + English/50 % first boot, press-kit boot logo, `/etc/issue`, kernel patch 0011; 29 checks pass | T3 ok 2026-11-25 |
| **`dist/firmware/test128-m9f-20261125.img.zst`** (raw `78973074…`, p2 `252f1cf0…`) | the rc2 rootfs + kernel, developer variant (m9e + patch 0011; m9e retired) | rootfs T2 as m9e (sweep, NES 59.98, DC); kernel T2 on the bench (sweep, 3 sleeps, NES 59.96, DC 59.99, boot slots); **recovery since 2026-11-25** (rc2 T3 ok) |
| `dist/firmware/MustardOS-R36S-port-v1.0.0-rc1.img.xz` (raw `da27f90b…`, p2 `abd16601…`) | public rc1 | T3 2026-11-25: 1–7 ok, findings fixed in rc2 |
| `dist/firmware/test128-m9d-20261125.img.zst` (raw `6dad53f3…`, p2 `14859cdb…`, U-Boot `159e086c…`) | the rc1 rootfs, developer variant | previous recovery |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2 | **base of every image build**; never retire |

4/5 versions in `storage-retention.json` (M2, m9d+rc1, m9f+rc2,
m9k+v1.0.0; m9c, m9g, m9h, m9i retired 2026-11-26).

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
  T3 pending); warm-reboot H2C (1 in 7); a real zombie occurrence is
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

**v1.0.0 checklist** (the published release; full menu paths in pt-BR):
1. Update screens: copy the release's `.p2.img.gz` + `.p2.img.sha256` to
   original32's `MUOS/update` (sudo cp, as on 2026-11-26), card in slot 1,
   Aplicativos → Ferramentas de sistema → Instalar atualização do
   sistema: a progress bar while unpacking; after the restart a screen
   "Concluindo a atualização do sistema" with a progress bar (~3 min on a
   public image), then it restarts by itself into the menu.
2. Informações → Detalhes do dispositivo: Compilação = v1.0.0.
3. Ferramentas de sistema: task and folder names in Português; Menu on
   "Instalar atualização do sistema": the help in Português.
4. Wi-Fi at power-on (open since m9c): power on with the dongle in; Wi-Fi
   connects by itself within ~30 s.
After it passes: m9k becomes the recovery image.

## Current milestone: M9 — public v1.0

Plan in roadmap.md M9 (rewritten 2026-11-25). Done before 2026-11-25:
M8g T3 fixes, ScummVM standalone default, CJK overlays, undervolt rows,
THIRD-PARTY.txt, `make-source-bundle.sh` (first version), public variant
checks (18 pass), the update path (`muos-update`, auto-update).

History of the M9 rounds (licences, rc1, rc2, kernel updates, v1.0.0):
milestones.md M9. **Next:** v1.0.0 T3 (T3 queue); then post-v1.0
(roadmap: other variants, dongles, the next MustardOS release).
