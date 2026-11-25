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
image (M9a T3 passed); m9d (= the rc1 rootfs, developer variant) is on
the bench's p2; the public **v1.0.0-rc1** is built and awaits its T3.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0), test128
  in slot 1 (mmcblk0 by DT alias), slot 2 empty. `user_init` = 0, time
  zone −03. Access, identity and card layout: procedures.md.
- **p2 = m9d** (2026-11-25 15:40, via the trial root after its T2; the
  previous p2, m9c, in `MUOS/trial/p2-previous.img`).
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
| `dist/firmware/MustardOS-R36S-port-v1.0.0-rc1.img.xz` (raw `da27f90b…`, p2 `abd16601…`) + `.img.zst`, `.p2.img.gz`/`.sha256` | **public rc1**: complete image (decision 35), 24 `check-public-image.sh` checks pass | T3 pending (blank card, user present) |
| `dist/firmware/test128-m9d-20261125.img.zst` (raw `6dad53f3…`, p2 `14859cdb…`) | the rc1 rootfs, developer variant: unmodified libmali, Gambatte/FCEUmm from source, no BT firmware, MustardOS logo, support notice | on p2 2026-11-25, T2 passed (10/10) |
| `dist/firmware/test128-m9c-20261123.img.zst` (p2 `6dab27a8…`) | m9b + Wi-Fi stuck-scan reset, `muos-update auto`, undervolt labels | previous p2 |
| **`dist/firmware/test128-m9a-20261122.img.zst`** (raw `093d64ce…`, U-Boot `159e086c…`) | ScummVM keyboard fixes, Undervolt row, JP/ZH overlays | **recovery since 2026-11-22** |
| `dist/firmware/test128-m8g-20261122.img.zst` (raw `81613024…`) | previous recovery | kept |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2 | **base of every image build**; never retire |

5/5 versions in `storage-retention.json` (m9d and rc1 are one entry;
m9b retired 2026-11-25); the next image retires m8g.

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

39. ~~Commit e-mail~~ closed: the user pushed the repository on
    2026-11-25 (`origin/main` = `a62c25b`) with the history as it was.
40. **Agent files in the public repository:** AGENTS.md/CLAUDE.md hold the
    workflow rules (and the Telegram section). Recommendation: keep
    them (they document how the port is built and tested).
41. **rc1 on GitHub:** recommendation: publish rc1 as a *pre-release*
    after its T3 (auto-update ignores pre-releases: it reads
    `releases/latest`), v1.0.0 as a normal release.

## T3 queue

**M9 rc1 checklist** (user present; a blank or spare microSD; pt-BR
paths):
1. PC: write `dist/firmware/MustardOS-R36S-port-v1.0.0-rc1.img.xz` with
   balenaEtcher/Rufus (or `flash-card.sh`) to the blank card; put it in
   slot 1 (test128 out), power on. Expected: logo "MustardOS / R36S /
   R35S / unofficial port", then the menu in English (first boot a bit
   longer: p3 grows).
2. Configuração → Idioma → Português (BR): menus in pt-BR.
3. Informações → Detalhes do dispositivo → down to "Versão", Fn: the help
   says it is an unofficial port and points to the GitHub page.
4. Configuração → Conectividade → Rede Wi-Fi (dongle in): connect to
   your network.
5. Configuração → Conectividade → Serviços web → Arquivos via SFTP → on;
   FileZilla: SFTP, the IP, port 2022, muos/muos; copy one NES and one
   NDS ROM into `ROMS/NES` and `ROMS/NDS`; play both (NDS: DraStic with
   the two-screen layout, Fn+Start quits).
6. Bench device (test128 back in slot 1, m9d): before a night on the
   charger tell me (I start `t2-discharge.sh log-start`), sleep it with
   the charger in, next morning wake it and tell me the battery %.
7. Same device, M9c leftovers: power on with the Wi-Fi dongle in 3 times
   (connects without a replug, worst case ~40 s); Configuração →
   Configurações perigosas: rows "Undervolt do CPU"/"Undervolt do GPU".

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

**Next:** rc1 T3 (above) → fold findings → the GitHub release:
`make-source-bundle.sh bundle`, assets, notes (decisions 40–41). The
repository is public (pushed by the user 2026-11-25, `a62c25b`); later
commits are pushed by the user too. Polish meanwhile:
battery after charger sleep (data first), Wi-Fi power-on T3.
