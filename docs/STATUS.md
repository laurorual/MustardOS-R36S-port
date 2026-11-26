# Project status

Current state only; update at the end of every milestone. Release plan:
[roadmap.md](roadmap.md); answered decisions: [decisions.md](decisions.md);
licences: [LICENSING.md](LICENSING.md); how-tos: [procedures.md](procedures.md);
finished milestones: [milestones.md](milestones.md) (M1–M7 in
[archive/](archive/milestones-m1-m7.md)); hardware facts:
[hardware-findings.md](hardware-findings.md); host storage:
[storage.md](storage.md).

## Current phase

Phase 5 (own-card firmware). M1–M9 done: **v1.0.0 published 2026-11-26**
(GitHub release, latest; m9k, its developer twin, is the recovery
image). **Current: M10 — experimental hardware reach** (started
2026-11-26; plan below).

## Device and bench

- **Bench (2026-11-26):** test128 in slot 1, updated through the update
  path m9k → **m10a** (p2 = m10a; main = `Image-494d1c3d5ebd` + the
  undervolt DTB `panel0-84611ef0394d.dtb`, previous = the same kernel +
  the stock DTB `panel0-c97151d0ec1a.dtb` since the model T2). p1 has
  the 22 model DTBs, `models.txt` and the selectors. original32 holds
  the public v1.0.0.
- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0), test128
  in slot 1 (mmcblk0 by DT alias), slot 2 empty. `user_init` = 0, time
  zone −03. Access, identity and card layout: procedures.md.
- **p2 = m10a** (2026-11-26, through the update path; the previous p2,
  m9k, in `MUOS/trial/p2-previous.img`). p1 `bootlogo.bmp` = the
  press-kit logo (`d6e6d189…`).
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
| `dist/firmware/MustardOS-R36S-port-v1.0.0.img.xz` (xz `a308dccd…`, raw `b762425f…`, p2 `9cf48944…`) + `.img.zst`, `.p2.img.gz`/`.sha256` | **public v1.0.0** (Build = v1.0.0); 29 checks | tag pushed; release pending (token, see "Current phase"); T3 ok 2026-11-26 |
| `dist/firmware/test128-m10a-20261126.img.zst` (raw `cc85290c…`, p2 `77ff5a87…`) | M10: Wi-Fi dongles, model DTBs + switch, developer variant | on the bench (update path from m9k); T2 below |
| **`dist/firmware/test128-m9k-20261126.img.zst`** (raw `3e487ae1…`, p2 `43779504…`) | v1.0.0 rootfs + kernel, developer variant | on the bench; T2: update rounds with progress screens, NES 59.96; **recovery since 2026-11-26** (v1.0.0 T3 ok) |
| (v1.0.0-rc2 public) | on GitHub (pre-release); local files deleted 2026-11-26 | T3 ok 2026-11-25 |
| (m9f) | the rc2 developer twin | retired 2026-11-26 (m9k recovery) |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2 | **base of every image build**; never retire |

3/5 versions in `storage-retention.json` (M2, m9k+v1.0.0, m10a; m9c,
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

- **Licences/publication:** v1.0.0 published (LICENSING.md; Hardkernel
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

- **Other test hardware (M10):** do you have, or can you borrow, any
  other USB Wi-Fi dongle (any brand; the chip doesn't matter) or another
  R36S/clone? Without one, M10's new paths ship untested, as the README
  says. Recommendation: none needed; a cheap RTL8188FTV/8188EU dongle
  would make item 1 testable.

## T3 queue

**v1.1.0 checklist** (public image on original32 in slot 1, as for
v1.0.0; full menu paths in pt-BR):
1. Update from v1.0.0: copy the release's `.p2.img.gz` + `.p2.img.sha256`
   to original32's `MUOS/update`, Aplicativos → Ferramentas de sistema →
   Instalar atualização do sistema: progress bar, restart, "Concluindo a
   atualização do sistema", restart into the menu.
2. Informações → Detalhes do dispositivo: Compilação = v1.1.0.
3. Wi-Fi at power-on (RTL8821CU, the new detection): connects by itself
   within ~30 s.
4. Configuração → Conectividade → Wi-Fi: off, then on: reconnects
   within ~20 s.
5. With Wi-Fi connected: unplug the dongle, wait 5 s, plug it back:
   reconnects within ~30 s.
6. Sleep (short Power press), wait 10 s, wake: Wi-Fi back within ~15 s.
7. Card in the PC: the boot partition has `select-model.bat`,
   `select-model.sh`, `select-model.command` and `models.txt`. Run the
   one for your PC: a list of 23 models (1 = "R36S-V12 2023-08-18
   Panel 0 (R35S, the port default)"); choose 1: "Chosen: …", a
   `model.txt` with `default` appears. Card back in slot 1, power on: no
   extra restart, the menu as always. (Don't choose another model on
   the R35S: their battery tables would upset the gauge; T2 covered the
   switch with a test DTB.)
8. Configuração → Configurações perigosas → Undervolt: the rows show the
   current state as before (not "unavailable").
After it passes: m10a becomes the recovery image.

## Current milestone: M10 — experimental hardware reach

Goal: v1.1 runs on more R36S units and with more Wi-Fi dongles, labelled
experimental (decisions 43–44; the port can't test them: feedback via
issues). Wi-Fi first (no bootloader write), then the variants.

Items:
1. Worker: any USB Wi-Fi dongle the kernel drives (modalias → wireless
   module, vendor Realtek drivers first; 8188fu is built in), interface
   by phy80211, radio off unloads it; the 8821cu-only paths (CD-ROM
   switch, warm-reboot reset, C2H watchdog, stuck-scan reset) stay
   gated on the 8821cu.
2. Hotplug rule + adapter row for any such dongle; autoload blacklist
   for the USB Wi-Fi modules (the worker loads them).
3. Firmware for the mainline drivers (mt7601u, rt2800usb, rt73usb,
   rtl8192cu, r8712u, r8723au) from linux-firmware, pinned, licences in
   LICENSING/THIRD-PARTY.
4. T1: detection against a fake sysfs; T2: the 8821cu regression set
   (radio, toggle loop, wake, hotplug, liveness).
5. Model DTBs (`dtb-survey.sh`, log `build/logs/m10/dtb-survey.tsv`):
   wave 1 = the 22 dArkOSen models on the port's board type (rg351mp
   U-Boot DTB) at 640x480 with the port's input names and key codes
   (Panel 0 keeps the port DTB: dArkOSen's Panel 0 has the glitching
   29 MHz timing). Build: dArkOSen DTB + the mmc aliases (`fdtput`),
   as `model-<sha12>.dtb` keys in dtb-variants.txt, in p1 and in p2's
   boot files. Not yet: 13 rg351v clones and R50S (other input names),
   7 soysauce (rg351p board), 1024/720 panels (frontend resolution).
6. Card-root selectors (`.bat`, `.sh`, `.command`) writing p1
   `model.txt` (a model id or `default`) from p1 `models.txt`.
7. `muos-model` (Linux, as `muos-undervolt`): early in the boot, a
   `model.txt` that main doesn't boot arms a one-shot trial with that
   DTB (same kernel) and reboots; the menu up 20 s promotes it; a
   failed trial renames `model.txt` to `.failed`. No U-Boot change, so
   v1.0 users get it through the update; boot-sync keeps the model
   across kernel updates; the undervolt rows say unavailable on a model.
8. Audio and battery come with each DTB (all wave-1 models: speaker +
   jack detection, dArkOSen `alsa_path` SPK_HP; no gamma key there).
9. Docs (README driver and model lists, hardware-findings,
   known-issues), v1.1.0 image at the end.

**Done:** items 1–4 (T2 2026-11-26: detection 15/15 fake IDs + the
real 8821cu, `t2-wifi-detect.sh`; boot ready 17.6 s; radio, 6-cycle
toggle, C2H watchdog with the new hotplug path, 2 wakes 9.3/8.9 s: all
pass).

Expected T3: the 8821cu regression (Wi-Fi on, toggle, sleep), the
selector on a PC, boot with the default and with a chosen Panel 0 DTB.

## Previous milestone: M9 — public v1.0 (done 2026-11-26)

Details in milestones.md M9.
