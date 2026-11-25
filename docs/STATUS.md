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
image until 2026-11-25; **m9d** (the developer twin of rc1, whose T3
passed with two small findings) is the recovery image now. m9e (the rc2
rootfs) is on the bench's p2; the public **v1.0.0-rc2** awaits its short
T3.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0), test128
  in slot 1 (mmcblk0 by DT alias), slot 2 empty. `user_init` = 0, time
  zone −03. Access, identity and card layout: procedures.md.
- **p2 = m9e** (2026-11-25 ~17:00, via the trial root after its T2; the
  previous p2, m9d, in `MUOS/trial/p2-previous.img`). p1 `bootlogo.bmp` =
  the press-kit logo (`d6e6d189…`; the old one in
  `MUOS/trial/bootlogo.bmp.before`).
- **Charge log running** (`T2_CHARGING=1 t2-discharge.sh log-start`,
  p3 `MUOS/log/discharge.csv`, user_init = 1): the overnight sleep on the
  charger; `t2-discharge.sh report` then `log-stop` in the morning.
- **Boot records:** main = `Image-be499e33d4eb` + `panel0-84611ef0394d.dtb`
  (undervolt CPU −50 / GPU −25 mV, `undervolt-on`); previous = the same
  Image + stock `panel0-c97151d0ec1a.dtb`. p1 has all 16 undervolt DTBs
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
| `dist/firmware/MustardOS-R36S-port-v1.0.0-rc2.img.xz` (raw `5554dc47…`, p2 `cfa7df4d…`) + `.img.zst`, `.p2.img.gz`/`.sha256` | **public rc2**: rc1 + English/50 % first boot, press-kit boot logo, `/etc/issue`; 29 checks pass | short T3 pending |
| `dist/firmware/test128-m9e-20261125.img.zst` (raw `21bec4ad…`, p2 `cb74b78c…`) | the rc2 rootfs, developer variant | on p2, T2 passed (sweep, NES 59.98, DC 59.08 Hz at 6 % battery) |
| `dist/firmware/MustardOS-R36S-port-v1.0.0-rc1.img.xz` (raw `da27f90b…`, p2 `abd16601…`) | public rc1 | T3 2026-11-25: 1–7 ok, findings fixed in rc2 |
| **`dist/firmware/test128-m9d-20261125.img.zst`** (raw `6dad53f3…`, p2 `14859cdb…`, U-Boot `159e086c…`) | the rc1 rootfs, developer variant | **recovery since 2026-11-25** (rc1 T3 passed) |
| `dist/firmware/test128-m9c-20261123.img.zst` (p2 `6dab27a8…`) | m9b + Wi-Fi stuck-scan reset, auto-update | kept |
| `dist/firmware/test128-m9a-20261122.img.zst` (raw `093d64ce…`) | previous recovery | kept |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2 | **base of every image build**; never retire |

5/5 versions in `storage-retention.json` (M2, m9a, m9c, m9d+rc1,
m9e+rc2; m9b and m8g retired 2026-11-25); the next image retires m9a.

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
- **Battery % short of 100 after sleeping on the charger** (2026-11-19:
  95 % after a night; FCC learned down to 2550 mAh). The driver's finish
  step (dsoc +1 % per ~92 s, only in MODE_FINISH) never ran: the next
  boot read rsoc 92.9 %, OCV 4149 mV, so the charge itself stopped
  short. Needs a logged night on the charger (T3 item 6) before a fix.
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

None open (39–42 answered 2026-11-25, decisions.md). The user
force-pushes the rewritten history (no-reply e-mail).

## T3 queue

rc1 T3 (2026-11-25): 1–5, 7 ok; findings: first boot at 100 % volume and
in Português (both from the bench's config pinned into the image; fixed
in rc2); boot screen as the press kit (done in rc2).
**rc2 checklist** (short):
1. Bench device, tonight (item 6 of rc1): the charge log is running; put
   it to sleep (short Power press) on the charger overnight; in the
   morning wake it and tell me the battery %.
2. Bench device, any reboot (main menu → Reiniciar): the
   boot shows the MustardOS badge (yellow, not blue/cyan) with "R36S /
   R35S" and "unofficial port" below, from U-Boot until the menu.
3. Spare card: write `dist/firmware/MustardOS-R36S-port-v1.0.0-rc2.img.xz`,
   first start: same boot screen, menu in **English**; press Vol+ once:
   the volume bar shows **55 %** (50 % + one 5 % step).

## Current milestone: M9 — public v1.0

Plan in roadmap.md M9 (rewritten 2026-11-25). Done before 2026-11-25:
M8g T3 fixes, ScummVM standalone default, CJK overlays, undervolt rows,
THIRD-PARTY.txt, `make-source-bundle.sh` (first version), public variant
checks (18 pass), the update path (`muos-update`, auto-update).

**Round of 2026-11-25 — done to T2:** docs cleanup; L1 LICENSING.md
(Gambatte/FCEUmm in `build-cores.sh`, BT firmware out, unmodified
libmali); L2 MustardOS name and support notice (logo, README, NOTICE,
THIRD-PARTY, Device Details help, EN/pt-BR); L3 source bundle covers the
public image (`make-source-bundle.sh check` passes); L4 history scan
clean, README/LICENSE/NOTICE, updater repo; L5 Plan B `prepare-image.sh`
(T1 on m9c and rc1); L6 rc1 built (24 checks) + m9d trial-root T2 10/10
(sweep, NES 59.97, GB 59.98, slot 2, SFTP jail, DC 59.99 Hz, DraStic,
N64, PSP 15.5 swaps/s), m9d written to p2. Polish: install guide EN/pt-BR,
CHANGELOG, known issues, release notes template.

**rc1 T3 round (2026-11-25):** fresh-card defaults (English, 50 %,
startup volume "previous", debug_mode 0), `/etc/issue`, boot logo from
the press-kit boot screen; check-public-image 29 checks; m9e T2, on p2;
history rewritten to the no-reply e-mail; m9d promoted to recovery.

**Next:** rc2 T3 (above) → the GitHub pre-release of rc2:
`make-source-bundle.sh bundle`, assets, notes (decisions 40–41). The
repository is public (pushed by the user 2026-11-25, `a62c25b`); later
commits are pushed by the user too. Polish meanwhile:
battery after charger sleep (data first), Wi-Fi power-on T3.
