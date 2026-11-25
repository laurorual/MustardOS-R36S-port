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
image (M9a T3 passed); m9c is on the bench's p2 (T3 pending).

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0), test128
  in slot 1 (mmcblk0 by DT alias), slot 2 empty. `user_init` = 0, time
  zone −03. Access, identity and card layout: procedures.md.
- **p2 = m9c** (2026-11-23, via the trial root, T2 passed; the previous p2
  in `MUOS/trial/p2-previous.img`).
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
| `dist/firmware/test128-m9c-20261123.img.zst` (p2 `6dab27a8…`) | m9b + Wi-Fi stuck-scan reset, `muos-update auto`, undervolt labels | on p2, T2 passed, T3 pending |
| `dist/firmware/test128-m9b-20261122.img.zst` (p2 `ce6694f8…`) | Traditional Chinese, CPU/GPU undervolt rows, THIRD-PARTY.txt, update task | superseded by m9c |
| **`dist/firmware/test128-m9a-20261122.img.zst`** (raw `093d64ce…`, U-Boot `159e086c…`) | ScummVM keyboard fixes, Undervolt row, JP/ZH overlays | **recovery since 2026-11-22** |
| `dist/firmware/test128-m8g-20261122.img.zst` (raw `81613024…`) | previous recovery | kept |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2 | **base of every image build**; never retire |

5/5 versions in `storage-retention.json`; the next image retires m9b
(m8f retired 2026-11-23).

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

- **Licences/publication (M9 priority):** see the plan below and
  LICENSING.md.
- **Battery % short of 100 after sleeping on the charger** (2026-11-19:
  95 % after a night; FCC learned down to 2550 mAh). M9 polish item.
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
  rkbin); Gambatte and FCEUmm are Phase 4 builds (M9 item 1 moves them
  to `build-cores.sh`).
- **Hardware:** headphone jack contact (deprioritized); slot 2 fails only
  with the spare card (closed); no controllable LEDs; DDR devfreq not
  synced to the VOP.
- **Trial root:** p3 can't be unmounted at shutdown while it runs.
- **p2 space:** 1 GiB, ~318 MB free.

## Decisions for the user

None open after 2026-11-25 (decisions 33–38). New ones from this round
go here.

## T3 queue

**M9c checklist** (m9c on p2; can be done any time):
1. Power on with the Wi-Fi dongle in, 3–4 times: Wi-Fi connects without a
   replug (worst case ~40 s).
2. Configuração → Configurações perigosas: the rows read "Undervolt do
   CPU" and "Undervolt do GPU".
3. Auto-update: only with a public release on GitHub (rc1).

## Current milestone: M9 — public v1.0

Plan in roadmap.md M9 (rewritten 2026-11-25). Done before 2026-11-25:
M8g T3 fixes, ScummVM standalone default, CJK overlays, undervolt rows,
THIRD-PARTY.txt, `make-source-bundle.sh` (first version), public variant
checks (18 pass), the update path (`muos-update`, auto-update).

**Round of 2026-11-25 (plan):**
- Docs cleanup: decisions.md, STATUS ~150 lines, M1–M7 and the M8
  experiments archived, roadmap M9 rewritten. *Done.*
- L1 LICENSING.md (single source; absorbs license-requests.md),
  pending-licenses.json and THIRD-PARTY.txt reconciled; Gambatte/FCEUmm
  into `build-cores.sh`; rtl8821c BT firmware out of the public image;
  only the 640x480 DraStic layout; community-practice reference.
- L2 MustardOS compliance: name, notice (EN/pt-BR) in README, release
  notes and the system; CC BY-NC credits.
- L3 GPL bundle covering the whole public image.
- L4 repository: history scan, README/LICENSE/NOTICE, push blockers, the
  final command; decision 33 (`/etc/muos-update.conf`).
- L5 Plan B `prepare-image.sh` (T1 against a public image without
  libmali and DraStic), procedures.md.
- L6 rc1 image + `check-public-image.sh`; T3 on a blank card with the
  user present.
- Polish: install guide EN/pt-BR, changelog, known issues, battery after
  charger sleep.

Tests: T0 shellcheck/builds; T1 ELF and image checks, prepare-image
round trip; T2 the rc1 p2 as a trial root on the bench (developer
access stays); T3 rc1 on a blank card (user present).
