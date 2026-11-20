# Project status

Current state only; update at the end of every milestone. The release
plan is in [roadmap.md](roadmap.md); how-tos (flash, build, trial root,
trial kernel, boot sequence) in [procedures.md](procedures.md); finished
milestones with their results and T3 checklists in
[milestones.md](milestones.md); hardware facts and the support summary in
[hardware-findings.md](hardware-findings.md); host storage in
[storage.md](storage.md). The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## Current phase

**Phase 5 (own-card firmware). M1–M5 and M7 done. Current: M8 (card
layout and the heavy systems), first night done 2026-11-20 (unattended):
image m8 on p2 and the new U-Boot (root by device, quiet boot, boot
logo) on the card, both T2-passed; T3 checklist below. Recovery image:
m7d (its U-Boot is the old one; the m8 image carries the new one).**

## Next session — read first

- Device on main = **M8 p2** (`0f723304…`, written 2026-11-20 ~03:05 by
  `write-p2`; previous p2 `50a5c24d…` in `MUOS/trial/p2-previous.img`)
  and the **M8 U-Boot** (`159e086c…`, written ~03:10 with read-back; the
  M7 one `65fb3dcd…` in `MUOS/trial/uboot-previous.img` and
  `build/m8/uboot-previous.img`). p1 has `bootlogo.bmp`. Boot records:
  main = `Image-331eebd4a643` + `panel0-c97151d0ec1a.dtb` (mmc aliases),
  previous = the M7 kernel/DTB. No live installs on top.
- If the U-Boot ever fails: write `build/m8/uboot-previous.img` to
  sectors 16384–24575 of the card from the host reader (p3 untouched):
  `dd if=build/m8/uboot-previous.img of=/dev/sdX bs=512 seek=16384
  conv=fsync`.
- CTR test state (the user's scene, mid-race, unpaused): p3
  `MUOS/port/t2/ctr-race` (`t2-long-play.sh --state`, `t2-soak.sh`).
- Idle discharge run done (report in hardware-findings, logger stopped).
- Device volume 35 at the end of the M8 night (40 before; T2 runs set
  10 and restore what they read).
- The standalone N64 SRAM of DK64 and MK64 was migrated from the
  libretro .srm on 2026-11-19 (`MUOS/t2-bak` deleted after the M7c T3).
- New-system ROMs from `port/roms/` on p3 (2026-11-19): 32X, ATARI2600,
  ATARI7800, GG, LYNX, SMS, PCE, SEGACD (Sonic CD), PCECD (Dracula X);
  BIOS `bios_CD_U.bin`, `syscard3.pce` in p3 `MUOS/bios`. M8
  (2026-11-20): DC (Power Stone 2), PSP (God of War CoO), NDS (NSMB),
  SATURN (Sonic R); core options: `melonds_threaded_renderer=enabled`.
- DraStic test copy (dArkOS binary + RG351MP cfg) in p3 `MUOS/t2/drastic`.
- Smoke ROMs deleted from p3 (2026-11-19); `make-smoke-roms.py` makes
  them again for T2.
- The user's spare card is in slot 2 (exFAT, `ROMS/megadrive`); it never
  initialises (open problem). Slot 1 is mmcblk0 by DT alias since M8.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, the user's spare card (exFAT) in slot 2: M4b image
  flashed 2026-11-14, then p2 written in place (`write-p2`) for M4d,
  M4e.1, M4f, M4g, M5, M7 (m7, m7t3, m7c, m7d) and M8 (m8); U-Boot
  rewritten in place for M8. `user_init` = 0. Time zone −03.
  - Boot records: main = `Image-331eebd4a643` + `panel0-c97151d0ec1a.dtb`
    (M8: mmc DT aliases; CPU OPPs to 1512 MHz, cap 1296); previous =
    `Image-ea8ac0033c0e` + `panel0-0475265be8ac.dtb` (M7).
  - p3: ROMs, Wi-Fi profile `Home.ini`, zone link, rumble verdict
    (absent), the six seeded themes, PSX BIOS (`SCPH550x.bin`, upper case).
- **original32 (stock dArkOSen):** the flasher station (slot 1, target
  in slot 2). Never write it.
- Device access, identity and card layout: procedures.md.

## Recovery image

The developer images are **private** (Wi-Fi PSK, SSH host key,
authorized_keys): never commit or share them. Flashing any image rewrites
the whole card, bootloader included; steps in procedures.md.

| Image | Content | State |
|---|---|---|
| `dist/firmware/test128-m8-20261120.img.zst` (raw `fbd4871c…`, p2 `0f723304…`, U-Boot `159e086c…`) | M8 night 1: mmc aliases, quiet U-Boot + boot logo, Wi-Fi deferred on wake in a game, standalone PPSSPP, DC/NDS/Saturn cores | on the device (p2 + U-Boot); T3 pending (the M8 checklist) |
| **`dist/firmware/test128-m7d-20261119.img.zst`** (raw `67ae7da4…`, p2 `176c691a…`) | **Recovery image since 2026-11-20.** M7 final: m7c + N64 defaults to the standalone Rice (decision 22), pruned N64 core list | on the device; T3 2026-11-20: 1–8 passed |
| `dist/firmware/test128-m7c-20261119.img.zst` (raw `5878d3b3…`, p2 `701eb2a8…`) | M7c: the M7 T3-fix fixes (Danger screen, cap switch, N64 warm-up), standalone Mupen64Plus, suspend stop/continue, PipeWire stall self-heal (recovery until m7d) | T3 2026-11-19: 1–8 passed (4 partial: no level bar or screenshot feedback in the standalone N64) |
| `dist/firmware/test128-m7t3-20261119.img.zst` (raw `9c60175f…`, p2 `c1f45838…`) | M7 + its T3 fixes (recovery until m7c) | T3 2026-11-19: 1–5 passed, 6 partial (Danger screen, fixed in m7c) |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 versions in `storage-retention.json` (m8 added 2026-11-20). The next
image retires m7t3.

## What works (T3-confirmed)

Display (60.0046 Hz), all controls, frontend and submenus; volume and
brightness with muxretro's in-game bar, hold-to-repeat and overdrive to
200 %; speaker audio; Wi-Fi (power save, profiles, scan, connect, replug,
sleep/wake ~9 s, on/off toggle, rows dimmed without a dongle, warm
reboot) + SSH/SFTP (developer and the menu's jailed SFTP with FileZilla);
time zone and NTP; prefs persistence; GB, NES, SNES, GBA, MD and PSX with
saves and states; per-system governors, 408 MHz menu idle; autostart,
menu reboot/shutdown, hard power-cut recovery; Power-key sleep/resume,
shutdown timer, charging fake sleep; Search, Activity (sleep excluded),
System details; battery %, icons and low-battery poweroff from the RK817
gauge, % kept across a power-off; battery-empty splash; headphone path
switching; flashing with the host card reader; p3 auto-grow; `panic=10`;
themes (six bundled, download, switching), profiles, Task Toolkit,
screenshots (menu), Date and Time; N64 with the standalone Mupen64Plus
Rice (saves, resume, sleep, levels; GLideN64 works but slow, the
default since M7); 32X, 2600, 7800, GG, Lynx, SMS, PCE, Sega CD and PCE
CD; Wi-Fi dongle plugged during boot; 15 min of CTR/MK64 without cuts;
3 menu sleeps in a row (M7 T3).

## Open problems

- **Slot 2 does not initialise the card (M5 T3 10; M7 T3: reseated,
  same):** the card is the former original32 (SDHC, worked in slot 1
  under stock at 1.8 V SDR50); test128 worked in slot 2 under stock.
  Port side: at
  boot and on hotplug the card holds DAT0 busy before the first command
  and DAT3 reads low (as if unpowered); `mmc1: error -110`. DT, kernel
  source/config, regulators (vcc_sd LDO6 3.0 V, shared with slot 1),
  pinmux/pulls and GRF IO_VSEL match stock dArkOSen, whose log shows
  test128 at SDR104 in slot 2 of this unit. Next (M8, after the U-Boot
  root-by-slot change): our image on the former original32 in slot 1,
  test128 in slot 2.
- **Battery % short of 100 after sleeping on the charger (user,
  2026-11-19):** sleep with the charger in overnight, wake: 95 %, not
  100 %. The next boot logged dsoc 93.9 %, rsoc 92.9 %, OCV 4149 mV,
  remain 2368 of FCC 2550 mAh (FCC learned down from 3380). Likely the BSP
  gauge's charge-finish step (dsoc → 100 on charge done) doesn't run
  while suspended, and/or the low learned FCC. Low priority; look at it
  with the M7 power items.
- **p2 space:** 488 MB root, ~85 MB free in m8 (PPSSPP 48 MB, parallel-dc
  32 MB added). ScummVM, CJK fonts and DraStic wait for the 1 GiB p2
  (decision 17; layout session with the user).
- **Heavy systems (M8):** PSP standalone runs (God of War: 30 Hz content,
  mostly 7–8 presented frames/s after the menus with auto frameskip; the
  heaviest PSP game, verdict is T3); DC and Saturn need BIOS (decision
  24: parallel-dc's HLE hangs on Power Stone 2, YabaSanshiro refuses
  without BIOS); NDS: melonDS 22–23 fps, DraStic not integrated
  (decision 23). The coredb PSP default key `ppsspp` also names the
  unshipped libretro entry (folders assigned by name may pick it).
- **Wi-Fi zombie (M5 incident):** handled since M7: while connecting by
  the worker (dongle reset), while "ready" by `muos-usb-watchdog` (C2H
  errors or a silent gateway → dwc2 rebind; T2 with injected errors and
  test hooks). A real occurrence is unverified.
- **New systems: fps verdicts are synthetic** (an idle loop per core,
  60 fps everywhere, core 4–7 ms); real games are the user's (T3,
  decision 18). FBNeo, MAME, MSX, Coleco, Lynx, Sega CD, PCE CD need
  game or BIOS files to test at all.
- **Screenshots:** menu (X+L2+R2, with a flash) and the standalone N64
  (Fn+X, saved but no feedback: the M7c T3 missed it); muxretro has no
  capture.
- **Standalone N64:** no volume/brightness bar (muxretro draws it; the
  keys work). Low priority. X on the Configuration tile also opens Kiosk (upstream).
- **Battery:** (d) the BSP smoothing uses `abs(delta_cap)`.
- **USB (dwc2 misses port events):** `muos-usb-watchdog` (M4f) rebinds
  dwc2 after 3 disagreeing reads (not yet triggered by a real replug).
- **Upstream gaps:** see the gap inventory in roadmap.md.
- **Translation (pt-BR):** every frontend string has pt-BR text since M7
  (upstream language pack + the port's overlay). Still English, as
  upstream: task names (file names), sort tags, time zone and language
  names. Chinese, Japanese and Korean are not shipped until p2 has room
  for their fonts (decision 17).
- **Menu sleep, one missed press (M7 soak):** 1 of 15 Power presses
  (20 s after a resume) reached muos-hotkey but muos-suspend exited
  silently (its lock or the recent-wake guard); not reproduced in 5 more
  cycles. Both exits log from the next image on.
- **Wi-Fi dongle (RTL8821CU):** the warm-reboot H2C case (1 in 7 since
  M4c); no software power cycle.
- **Wake:** in the menu Wi-Fi returns ~9.3–10.2 s after wake (M7
  timeline in hardware-findings). Woken in a game (M8), Wi-Fi stays down
  until the game ends (no stutter: T2 peak 40 ms); T3 to confirm.
- **Boot logo (M8):** U-Boot shows p1 `bootlogo.bmp` (own art), the
  kernel console is serial-only and quiet, muos-rc shows the same logo
  until the menu. The gap between the kernel taking the display (~4 s,
  fbcon) and muos-rc (~5 s) may be black; T3.
- **Power:** menu idle 407–425 mA (M7 discharge run, backlight 60,
  Wi-Fi up); no controllable LEDs.
- **Audio:** PipeWire sink stall now and then (no sound, standalone
  N64 frozen until a PipeWire restart; hardware-findings): self-healed
  before each game since M7, root cause open; WirePlumber "no
  profile" start failure retried; underruns only at game start (launch +
state load) or when a core runs short of CPU (M7); 200 %
  overdrive distorts (as upstream).
- **Headphones (hardware, deprioritized):** jack contact problem.
- **DDR devfreq** isn't synced to the display; **U-Boot log** goes to
  serial/LCD only.
- **Pinned, not rebuilt:** idbloader and trust (rkbin files); fceumm and
  gambatte are Phase 4 source builds outside `build-cores.sh`.
- **Trial root:** p3 can't be unmounted at shutdown while it runs; any
  reboot returns to main (one-shot marker).
- **Menu:** "Direct Link" and "Proxy Settings" not exercised; static
  addresses untested; the Rumble row's "present" case unverified.
- **Licences (M9):** Mali r13p0 (Hardkernel: no answer yet), the dirty
  U-Boot, Gambatte and BT firmware are private-only; FBNeo and MAME
  2003-Plus are non-commercial (pending-licenses.json).

## Decisions

Answered by the user 2026-11-14: 1 name "muOS for R36S/R35S (unofficial
port)"; 2 Mali (a), request sent 2026-11-14, no answer as of 2026-11-19;
3 boot payloads rkbin (done, M4d); 4 GPL source on GitHub; 5 public root
password `root`; 6 SFTP jail before the final public build (done, M4g);
7 unported web services hidden; 8 public p3 empty.
Answered 2026-11-17: 9 shellcheck download allowed (done); 10 the R35S
has no rumble motor; keep the option, detect the motor, show
"Unavailable" without one (done); 11 no public-image test yet.
Answered 2026-11-18 (recommendations accepted): 12 upstream themes in the
developer image now, in the public image after the MustardOS team
answers (M8); 13 CPU 1512 MHz as an opt-in, off by default (M7);
14 Bluetooth, PortMaster, standalone emulators after v1.0; 15 spare card
in slot 2 (inserted; fails, see open problems); 16 `root=` by the slot-1
device with the clean U-Boot in M8 (user present); until then no image
copies in slot 2.

Answered 2026-11-19: 17 grow p2 to 1 GiB in the M8 card layout, then
ship ScummVM and the CJK fonts (recommendation accepted); 18 the user
provides game dumps: after every T3 check `port/roms/` on the PC and use
any ROM of a not yet tested system for its core's T2 (none new as of
2026-11-19: bios, gb, gba, megadrive, n64, nes, psx, snes); 19 exception
to decision 14: standalone Mupen64Plus for N64 now (M7), the other
standalone emulators stay after v1.0. The user is providing ROMs for the
new systems (first batch 2026-11-19: 32X, 2600, 5200, 7800, CD-i, DC,
GG, Jaguar, Jaguar CD, Lynx, NDS, PSP, Saturn, SMS, TG16, TG-CD, VB).
Answered 2026-11-19: 20 Dreamcast, PSP, NDS and Saturn (lowest
priority) in v1.0 (M8, after the 1 GiB p2; popular, and some games are
playable under dArkOSen); Atari 5200, Virtual Boy, Jaguar, Jaguar CD
and CD-i out of v1.0. 21 Sega CD and PC Engine CD BIOS provided in
`port/roms/bios` (bios_CD_U.bin, syscard3.pce).

Answered 2026-11-19 (M7c T3): 22 N64 defaults to "Mupen64Plus -
Standalone - Rice" (done to T2: seed, migration, coredb default; the
assignment list offers only Rice and Glide, the "- Full" entries equal
4:3 on this panel and GlideMk2 isn't built).

## Decisions for the user

23. **NDS emulator.** dArkOSen uses DraStic (closed source, free to use;
    its binary is in the dArkOS repo; no explicit redistribution licence).
    melonDS (GPL) is 22–23 fps here. Recommendation: DraStic in the
    developer image now (needs the 1 GiB p2 or ~5 MB of the 85 MB left,
    plus a launcher with remapped controls), public image only after
    the licence check (pending-licenses, M9); melonDS stays as the
    fallback core.
24. **BIOS for DC and Saturn.** Please add to `port/roms/bios`: DC
    `dc_boot.bin` (+ `dc_flash.bin`), Saturn `saturn_bios.bin` (or
    `sega_101.bin` / `mpr-17933.bin`). Without them DC hangs at boot
    (HLE) and Saturn does not start; dArkOSen's DC also uses the BIOS.
25. **Card layout session (M8 items 1–4 left):** p2 1 GiB means moving
    p3 (ROMs, saves, Wi-Fi profile): recommendation: with you present,
    back up p3 on the PC, flash the 1 GiB-layout image with the host
    reader, restore p3 (one session, ~30 min of your time), then the
    slot-2 swap test with the two cards.

## T3 queue

**M8 checklist, night 1 (image m8 + new U-Boot, on the device; pt-BR
labels).** Items 4 and 5 on battery (on the charger sleep is the fake
one).

1. **Boot logo:** Desligar, power on: from the first light to the menu a
   black screen with "muOS / R36S / R35S / unofficial port" and no
   scrolling text; note any black gap or flicker and the seconds from
   power-on to the menu (M7: ~15 s).
2. **Regression after boot:** menu in pt-BR, Wi-Fi connects (header
   icon), Configuração → Conectividade unchanged.
3. **PSP** (Explorar conteúdo → PSP → God of War - Chains of Olympus
   (USA)): starts in PPSSPP; Cross = B, Circle = A, Square = Y,
   Triangle = X, L1/R1 = L/R, Start/Select, d-pad and stick; play a few
   minutes: is it playable? Fn opens PPSSPP's menu (B or Fn closes it);
   Fn+Start returns to the muOS menu.
4. **Sleep in PSP (battery):** short Power → screen off; Power → the game
   continues where it was, sound back.
5. **Sleep in a libretro game (battery):** NES (Explorar conteúdo → NES),
   short Power, wake after ~30 s: the game continues at once with no
   stutter; the Wi-Fi icon stays off while in the game; Fn+Start to the
   menu: Wi-Fi icon back within ~15 s.
6. **N64 regression** (Explorar conteúdo → N64 → Mario Kart 64 (USA)):
   starts, Fn+Start back to the menu.
7. **NDS / DC / Saturn (known):** NDS (Explorar conteúdo → NDS) starts
   in melonDS but slow (~22 fps); DC and Saturn need BIOS (decision 24):
   no need to test.

## Current milestone: M8 — card layout and the heavy systems (decisions 16, 17, 20)

Started 2026-11-20. Night 1 (unattended, 2026-11-20 01:30–03:30): items
1 (U-Boot root by device, written), 2 (quiet boot + logo, written), 7
(PSP standalone), 10 (wake in a game) done to T2; 6/8/9 built, blocked by
decisions 23/24; 3/4 need decision 25. Details: milestones.md M8.
The bootloader and partition-table writes need the user present, except
the night-1 exception.

Items:
1. Clean U-Boot build (from source, no dirty tree), `root=` by the
   slot-1 device (decision 16). T0–T2 through the trial boot path; the
   bootloader write with the user there.
2. Quiet boot and a boot logo (M7 T3): no kernel console on the LCD
   (`console=tty0`/`loglevel` out of the bootargs), a logo from U-Boot or
   early userspace until the frontend; the developer image keeps the log
   on serial and in a file.
3. Card layout with p2 at 1 GiB (decision 17) and a matching recovery
   image.
4. Slot-2 swap test (our image on the former original32 in slot 1,
   test128 in slot 2) to close the slot-2 problem.
5. ScummVM and the CJK fonts (decision 17).
6. Dreamcast (Flycast).
7. PSP (PPSSPP, standalone, `muos-mupen64plus` launcher pattern).
8. NDS (DraStic licence check for a public image, else melonDS or
   DeSmuME; standalone like PSP).
9. Saturn last (YabaSanshiro or Beetle), lowest priority.
10. Wake in a libretro game: hold the game until the wake bring-up
    settles, like the standalone N64 (M7 T3 note), instead of resuming
    into slow frames.
11. The sleep-exit logging (M7 item 26) in the image; follow the missed
    menu press if it shows again.
12. Battery % short of 100 after sleeping on the charger (low priority).

Tests: T0 builds and shellcheck; T1 the new emulators under qemu-user
and ELF/ABI checks; T2 trial root (sweep, fps per new system with the
user's ROMs, sleep, wake frame times), trial boot for the U-Boot and
bootargs change. Expected T3: the boot logo, the U-Boot/layout flash
with the user present, the slot-2 swap, a game each in DC, PSP, NDS
(and Saturn), ScummVM, a CJK language, wake in NES.

## Next milestone: M9 — public v1.0

Plan in roadmap.md M9 (licences, the public variant, install guide,
rc1 → T3 on a blank card with the user present).
