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
layout and the heavy systems). 2026-11-20 day (user present): the night-1
T3 fixes, PSP/NDS/DC emulators and the 1 GiB p2 layout: image m8b
flashed with the host reader and p3 restored; T3 checklist below.
Recovery image: m7d (old 512 MiB p2 layout; flashing it rewrites the
whole card, so it still works); m8b becomes recovery after its T3.**

## Next session — read first

- Device = **m8b flashed whole** (2026-11-20 ~17:25, raw `fea0b63a…`,
  p2 `d1411860…`, M8 U-Boot `159e086c…`), p3 restored from
  `build/m8/p3-backup/p3.tar` (**private**: delete it once the m8b T3
  confirms the restored card). New layout: p2 1 GiB (468 MB free), p3 at
  1152 MiB. Boot records: main = `Image-331eebd4a643` +
  `panel0-c97151d0ec1a.dtb`, previous = the M2 kernel (image default).
  No live installs on top.
- Test data on p3 `MUOS/t2`: `state-v120`/`state-v112` (the user's God of
  War states for v1.20.4 / v1.12.3; v1.12 needs `T2_PSP_BYKEY=1`),
  `ppsspp-2021` (test copy, now in the image: removable), `drastic`
  (night-1 copy, removable), `m1-backup` (old flycast; removable).
- CTR test state: p3 `MUOS/port/t2/ctr-race`.
- Device volume as the user left it (T2 runs set 10 and restore).
- New-system ROMs (p3, also in `port/roms/`): 32X, 2600, 7800, GG, LYNX,
  SMS, PCE, SEGACD, PCECD, DC (Power Stone 2), PSP (God of War CoO), NDS
  (NSMB), SATURN (Sonic R); BIOS incl. `dc/dc_boot.bin`, `dc/dc_flash.bin`,
  `saturn_bios.bin`.
- The user's spare card is in slot 2 (exFAT, `ROMS/megadrive`); it never
  initialises (open problem). Slot 1 is mmcblk0 by DT alias since M8.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, the user's spare card (exFAT) in slot 2: m8b
  flashed whole 2026-11-20 (1 GiB p2 layout; p3 restored), after the M4b
  image of 2026-11-14 and p2 writes up to m8. `user_init` = 0. Time
  zone −03.
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
| `dist/firmware/test128-m8b-20261120.img.zst` (raw `fea0b63a…`, p2 `d1411860…`, U-Boot `159e086c…`) | M8 day: **1 GiB p2 layout**, instant screen-off sleep + 3 s wake hold, PSP PPSSPP v1.12.3 + FrameSkip 1 (v1.20.4 second), NDS DraStic, DC Flycast v2.7 | **on the device (flashed whole)**; trial-root T2 passed; T3 pending (the M8b checklist) |
| `dist/firmware/test128-m8-20261120.img.zst` (raw `fbd4871c…`, p2 `0f723304…`, U-Boot `159e086c…`) | M8 night 1: mmc aliases, quiet U-Boot + boot logo, Wi-Fi deferred on wake in a game, standalone PPSSPP, DC/NDS/Saturn cores | T3 2026-11-20: 1, 2, 4, 6 ok; 3 slow, 5 stutters (fixed in m8b) |
| **`dist/firmware/test128-m7d-20261119.img.zst`** (raw `67ae7da4…`, p2 `176c691a…`) | **Recovery image since 2026-11-20.** M7 final: m7c + N64 defaults to the standalone Rice (decision 22), pruned N64 core list | on the device; T3 2026-11-20: 1–8 passed |
| `dist/firmware/test128-m7c-20261119.img.zst` (raw `5878d3b3…`, p2 `701eb2a8…`) | M7c: the M7 T3-fix fixes (Danger screen, cap switch, N64 warm-up), standalone Mupen64Plus, suspend stop/continue, PipeWire stall self-heal (recovery until m7d) | T3 2026-11-19: 1–8 passed (4 partial: no level bar or screenshot feedback in the standalone N64) |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 versions in `storage-retention.json` (m8b added, m7t3 retired
2026-11-20). The next image retires m7c.

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
- **p2 space:** 1 GiB since m8b, 468 MB free. ScummVM and the CJK fonts
  (decision 17) are next (by `write-p2`, no reflash).
- **Heavy systems (M8, T2; verdicts are the m8b T3):** PSP = PPSSPP
  v1.12.3 + FrameSkip 1: God of War ~31 emulated fps (full speed) in the
  user's scene; CPU-bound and thermally held at ~1000 MHz under the 1296
  cap. NDS = DraStic, full speed (NSMB). DC = Flycast v2.7: Power Stone 2
  36–43 fps (attract loop; options not tuned). Saturn = YabaSanshiro
  libretro, Sonic R ~21 fps (dArkOSen's standalone YabaSanshiro not
  tried). Details in hardware-findings "Standalone emulators (M8)".
- **Wi-Fi toggle (m8b trial T2):** one of 7 toggles sat in SCANNING for
  150 s (no AP found), the next came back in 9 s; network code unchanged
  in m8b; two SSH drops earlier the same day under heavy load.
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
  until the game ends and the paused frame is held 3 s (m8b: no slow
  frames after it in T2); night-1 T3 still felt micro stutters (before
  the hold); m8b T3 to confirm.
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

Answered 2026-11-20 (night-1 T3): 23 the emulator with the most FPS for
every system, closed source allowed (done: PSP v1.12.3, NDS DraStic, DC
Flycast v2.7); 24 DC/Saturn BIOS provided (done); 25 layout session
(done: m8b flashed, p3 restored).

## Decisions for the user

26. **Slot-2 swap test (M8 item 4):** flash our image on the spare card
    (the former original32, now exFAT with `ROMS/megadrive`; **its
    contents are erased**), boot it in slot 1 with test128 in slot 2.
    Recommendation: yes, with you present (~10 min); copy anything you
    want from the spare card first.
27. **Public image and closed source (M9):** DraStic has no explicit
    redistribution licence. Recommendation: developer image now; for the
    public image either a licence answer or a first-run download script.

## T3 queue

**M8b checklist (image m8b, flashed 2026-11-20; pt-BR labels).** Sleep
items on battery (on the charger sleep is the fake one).

1. **Restored card:** menu in pt-BR, Wi-Fi connects (header icon); in
   Explorar conteúdo your systems and games are all there; open a game
   that had a save (e.g. Explorar conteúdo → GBA or SNES → a game you
   played) and check the save/resume is there.
2. **Sleep in the menu:** short Power → the screen goes off at once;
   Power → the menu is back.
3. **Sleep in a game (NES):** Explorar conteúdo → NES → a game, short
   Power: the screen goes off at once (no visible freeze first); wake
   after ~30 s: the paused picture for ~3 s, then game and sound come
   back together with no stutter.
4. **PSP** (Explorar conteúdo → PSP → God of War - Chains of Olympus
   (USA)): starts in PPSSPP 1.12.3; L3 loads your 1.12 state (saved
   16:02); play a few minutes: game speed close to normal (fewer frames
   on screen, frameskip 1), sound clean, controls as before; Fn opens
   PPSSPP's menu; Fn+Start back to the muOS menu.
5. **Sleep in PSP (battery):** short Power, Power: continues, sound back.
6. **NDS** (Explorar conteúdo → NDS → New Super Mario Bros. (USA)):
   starts in DraStic; d-pad and left stick, A/B/X/Y, L1/R1, Start,
   Select; right stick = touch cursor, L3 = touch; R3 swaps the screens;
   L2/R2 change the layout; Fn opens DraStic's menu (B/Back closes it).
   Save in the game, Fn+Start, open it again: the save is there.
7. **Sleep in NDS (battery):** short Power, Power: continues.
8. **Dreamcast** (Explorar conteúdo → DC → Power Stone 2 (USA)): the
   Dreamcast BIOS logo, then the game; is it playable? (T2: 36–43 fps).
9. **Saturn** (Explorar conteúdo → SATURN → Sonic R (USA, Brazil)):
   starts; slow (~21 fps) is expected.
10. **N64 regression** (Explorar conteúdo → N64 → Mario Kart 64 (USA)):
    starts; Fn+Start back to the menu.

## Current milestone: M8 — card layout and the heavy systems (decisions 16, 17, 20)

Started 2026-11-20. Night 1 (unattended, 2026-11-20 01:30–03:30): items
1 (U-Boot root by device, written), 2 (quiet boot + logo, written), 7
(PSP standalone), 10 (wake in a game) done to T2; 6/8/9 built, blocked by
decisions 23/24; 3/4 need decision 25. Day (user present): night-1 T3
fixes (sleep screen-off, 3 s wake hold), PSP v1.12.3, DraStic, Flycast
v2.7, item 3 (m8b flashed, p3 restored). Details: milestones.md M8.
**Left:** 4 (decision 26), 5 (ScummVM, CJK: by write-p2), 9 (Saturn
standalone, lowest), 11, 12; then the M8 T3 and promotion of m8b.

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
