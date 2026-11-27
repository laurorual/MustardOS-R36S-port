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

- **Bench (2026-11-27, M13 T2, decision 52):** **original32 in slot 1**
  with the developer `test128-m13d` (flashed as m13b, updated to m13d by
  `muos-update stage` on exFAT; p3 now ext4 after the last
  `t2-first-boot.sh install ext4`, factory_reset 0, Portuguese (BR),
  São Paulo zone; no games). Its old public v1.1.0 is gone. test128
  (off, in the drawer) keeps m12f with all the test content (PortMaster,
  PICO-8 with the user's private official PICO-8, ROMs, T2 states);
  boot records main = `Image-494d1c3d5ebd` + the undervolt DTB, previous =
  the stock DTB. Wi-Fi dongle on original32 bench runs: 0bda:c820.
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
| **`dist/firmware/test128-m12f.img.zst`** (raw `8b9df957…`, p2 `6a29a226…`, `build/m3a/test128-m12f.p2.img`) | M11 + M12 + the v1.1.1 T3 fixes + manual online update | v1.1.1 T3 round 4 ok; **recovery since 2026-11-27** (m12e retired); on the bench p2 |
| `dist/firmware/MustardOS-R36S-port-v1.1.2.*` (raw `b012fcfc…`, p2 `49ed4c87…`) | v1.1.2 candidate, public (e6462d9, the m13d rootfs), 45 checks | **T3 pending** (original32) |
| `dist/firmware/test128-m13d.img.zst` (raw `2325c3a6…`, p2 `fdae3cbc…`) | M13 developer, MUOS_FIRST_BOOT=1 | M13 T2 PASS; on original32 |
| (v1.1.1 public, m12f) | on GitHub (release, latest; raw `d5187bd2…`, p2 `4068786a…`); local images, raw p2 and source zips deleted 2026-11-27 (manifest kept) | T3 ok 2026-11-27 |
| (v1.1.0 public, m10a) | on GitHub (release); local files and m10a retired 2026-11-27 | T3 ok 2026-11-26 |
| (v1.0.0 public, m9k) | on GitHub (release); local files and m9k retired 2026-11-26 (m10a recovery) | T3 ok 2026-11-26 |
| (v1.0.0-rc2 public) | on GitHub (pre-release); local files deleted 2026-11-26 | T3 ok 2026-11-25 |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2 | **base of every image build**; never retire |

5/5 versions in `storage-retention.json` (M2, m12f, p4test, m13d,
v1.1.2-public; m13b, m13c and earlier retired). `build/release`
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

None (decision 52: the model switch stays in S89; M13 = v1.1.2;
flash tests on original32).

## T3 queue

**v1.1.2 (public candidate) on original32, blank card** (sent 2026-11-27):
1. Flash `MustardOS-R36S-port-v1.1.2.img.zst` (flash-card.sh, no
   `--grow`), slot 1, power on: logo, then the First Boot (English).
2. Idioma → Português (BR): the screens switch.
3. Data e hora: time and Fuso horário (São Paulo).
4. Perfis, Teste de botões: open, every button shows, back.
5. Desligar: off; power on: the First Boot again, language kept.
6. Instalar → exFAT: progress screen, restart, the main menu in pt-BR
   with the time set; no First Boot at the next start.
7. Configuração → Conectividade → Rede Wi-Fi: connects.
8. Aplicativos → PortMaster: installs, opens; one port installed plays.
9. Power off; the card on a PC (Windows if possible): the storage drive
   with `ROMS` and `MUOS`; copy a ROM into `ROMS/<system>`, eject.
10. Explorar conteúdo → SD1 → the system → the ROM plays and quits.
11. Restart: clock and zone right (Configuração → Data e hora).
12. Aplicativos → Ferramentas de sistema → Buscar atualização online:
    up to date (GitHub's v1.1.1 is older: not offered).

## Current milestone: M13 — First Boot and the games card format (started 2026-11-27)

Goal (decisions 50, 51): a fresh public card starts in MustardOS's own
first boot (the pin's `muxinstall` in muxfrontend: Date and Time,
Language, Profiles, Input Tester, Shutdown, Install); Install asks exFAT
(recommended) / FAT32 / EXT4 for the card, so Windows can copy ROMs. One
partition (p3) as upstream's SD1, whatever the format. Host-only for now
(the bench is off for the panel); T2 when it is on.

Design: the port keeps its state on p3 (not on a system partition as
upstream), so Install cannot format p3 under the running menu: it notes
the choice (`muos-install-storage request`) and restarts; S89 applies it
before anything else uses p3 (`apply`: the first boot's state kept in RAM,
p3 grown, formatted, state back, factory_reset 0; ext4 is only grown; a
fresh card only; a failed format falls back to ext4 and the first boot).
p3 is mounted by type in the shim (trial root), S89 and S90. Links on p3:
`muos-link-or-bind` (DraStic resources and microphone, PPSSPP 2021's
shared SAVEDATA, ScummVM's extra/theme: a bind on exFAT/FAT32, undone at
stop); the time zone is text on p3 with the link in /run/muos/localtime
(frontend patch 0004, muos-clock zone; older cards' link still read).
The README warns about exFAT/FAT32 and power loss (decision 51).
(A first p4 design, 65f7222/2f16e2d, was replaced by this one.)

Done: exfatprogs + dosfstools; public images factory_reset 1
(`MUOS_FIRST_BOOT=1` for a developer image); install request/apply +
progress task (texts in 33 languages); content paths through /mnt/mmc;
PortMaster chmod tolerant; frontend 0004 rebuilt; the early model switch
in S89 (decision 52); install guides, README, CHANGELOG, known issues;
LICENSING 65 packages (`make-source-bundle.sh check` ok).
T0 shellcheck; T1 `t1-install-storage.sh` PASS (now with the S91 pickles
seed). **T2 on original32 (2026-11-27), m13b → m13d, all PASS:**
`t2-first-boot.sh pre`, `install exfat` (fixed: S91's Flycast seeds in
MUOS/pickles were taken for a used card; pickles now kept), NES 59.97 fps,
DraStic (resources/microphone binds, state on exit), PPSSPP 2021
(SAVEDATA bind), `t2-portmaster.sh` (fixed: on exFAT/FAT32
`/userdata/roms/ports` matched ROMS/Ports and harbourmaster took
Batocera's folders; `muos-portmaster` sets HM_*), the update m13b → m13d
by `muos-update stage` with the trial image on exFAT (~16 min on this
slow card), `install vfat` (NES 59.97, PortMaster PASS), `install ext4`,
`t2-model.sh build/m10/t2/p0copy.dtb` (a Panel 0 copy with one extra
property; armed in S89, promoted 39 s later; the script now refuses a
DTB already on p1). Public v1.1.2 built (45 checks).
Left: the T3 above, then the release (procedures "Release").
Release: v1.1.2. Then M14: the MustardOS next release (decision 45).
