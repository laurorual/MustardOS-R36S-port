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
layout and the heavy systems). 2026-11-21 night (unattended): the m8d
T3 round (DC speed limiter, Saturn page flips + menu crash, core lists,
NDS touch on R3, Fn+Start fade): image m8e; M8e T3 2–9 ok → m8e is the
recovery image. 2026-11-21 day: the thermal block (undervolt CPU −50 /
GPU −25 mV promoted as the main DTB on this unit), ScummVM (core +
standalone), dArkOSen's standalone Flycast: image m8f, trial-root T2
passed, p2 written; the M8f T3 checklist below.**

## Next session — read first

- Device = **m8f on p2** (written 2026-11-21 ~15:30 after its trial-root
  T2, `build/m8f/t2-m8f.sh`, logs `build/logs/m8f/trial-m8f/`; old p2 =
  m8e as run, sha 141504d3, in p3 `MUOS/trial/p2-previous.img`), on the
  1 GiB p2 card layout. `user_init` 0. Boot records: main =
  `Image-be499e33d4eb` + **`panel0-84611ef0394d.dtb` (undervolt CPU −50 /
  GPU −25 mV, `make-dtb-uv.sh`; trial-boot T2 `build/logs/m8f/trial-uv`)**,
  previous = the same Image + `panel0-c97151d0ec1a.dtb` (stock
  voltages). A crash or freeze that looks like instability: `muos-boot-slot`
  back to the stock DTB (previous). No live installs on top.
- T2 left on p3: `pickles/settings/core/flycast{,2022}.ini`
  (speed_limiter=1, as the migration writes them); YabaSanshiro's per-game
  `Sonic R ... .cue.config` and `save/backup.bin` (race tests).
- Test data on p3 `MUOS/t2`: `state-v120`/`state-v112` (the user's God of
  War states for v1.20.4 / v1.12.3; v1.12 needs `T2_PSP_BYKEY=1`),
  `ppsspp-2021` (test copy, now in the image: removable), `drastic`
  (night-1 copy, removable), `m1-backup` (old flycast; removable),
  `dc-fight` (the user's Power Stone 2 mid-fight state, Flycast v2.7
  only), `dc-fight-2022` (the user's fight on Flycast 2022, M8c T3), `emu` (advanced DraStic trial copy, removable),
  `drastic-config-m8b` (the plain DraStic config before the switch).
- CTR test state: p3 `MUOS/port/t2/ctr-race`.
- Device volume as the user left it (T2 runs set 10 and restore).
- New-system ROMs (p3, also in `port/roms/`): 32X, 2600, 7800, GG, LYNX,
  SMS, PCE, SEGACD, PCECD, DC (Power Stone 2), PSP (God of War CoO), NDS
  (NSMB), SATURN (Sonic R); BIOS incl. `dc/dc_boot.bin`, `dc/dc_flash.bin`,
  `saturn_bios.bin`.
- Slot 2 is empty (the spare card now holds m8c, flashed for the swap
  test; the user keeps it). Slot 1 is mmcblk0 by DT alias since M8.
- `refs/darkosen` at upstream `28f5427` (2026-11-14). The user copied
  the lean clone's files in, but its `.git` is still the 361 MB one (an
  aborted `ls-tree -l` fetched blobs); replacing `refs/darkosen/.git` by a
  fresh `--filter=blob:none --sparse` clone's would free ~340 MB (the
  user's call; refs/ is read-only to the agent). Its repo binaries are
  unusable: `opt/flycastsa/flycast` is damaged by the repo's
  `* text eol=lf` (42 CRLF→LF), `opt/scummvm/scummvm` is Git LFS (media
  URL) and needs ~20 Debian libraries.
- ScummVM test game: p3 `ROMS/SCUMMVM/The Secret of Monkey Island (CD
  DOS VGA)/` + `….scummvm` (id `monkey`, also in `port/roms/ScummVM`);
  the folder's assignment on this card is the standalone (muOS
  auto-assigned it during the tests; a fresh card seeds the core).

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, slot 2 empty: m8b flashed whole 2026-11-20 (1 GiB
  p2 layout; p3 restored), m8c, m8d, m8e, then m8f (2026-11-21) written to p2. `user_init` = 0. Time zone −03.
  - Boot records: main = `Image-be499e33d4eb` + `panel0-84611ef0394d.dtb`
    (M8: mmc DT aliases, dw_mmc set_ios sleeps; CPU OPPs to 1512 MHz, cap
    1296; M8f undervolt CPU −50 / GPU −25 mV); previous = the same Image
    + `panel0-c97151d0ec1a.dtb` (stock voltages).
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
| `dist/firmware/test128-m8f-20261121.img.zst` (raw `fe44baad…`, p2 `15b51793…`, U-Boot `159e086c…`) | M8e T3 round + thermal block: ScummVM v2026.4.0 core + standalone, Flycast v2.7 standalone, DC synchronous rendering default, one DraStic, sleep stops YabaSanshiro/ScummVM/Flycast (the image's p1 DTB is the stock one; the undervolt DTB is a boot record on this card only) | **on the device (p2 written 2026-11-21)**; trial-root T2 passed; T3 pending (the M8f checklist) |
| **`dist/firmware/test128-m8e-20261121.img.zst`** (raw `2f0293a2…`, p2 `e43458ce…`, U-Boot `159e086c…`) | **Recovery image since 2026-11-21 (1 GiB p2 layout).** m8d T3 round: DC Flycast speed limiter, Saturn vblank flips + menu crash fix + SCSP wait, core lists by installed cores, NDS touch on R3, Fn+Start fade | T3 2026-11-21: 2–9 ok; 1 DC uneven (frame-skip feel) |
| `dist/firmware/test128-m8d-20261120.img.zst` (raw `c7520a89…`, p2 `37d7194d…`, U-Boot `159e086c…`) | m8c T3 round: NDS Fn+Start quit fix + right-stick stylus, quit dimming, DC Flycast 2022 at 640x480 + framerate normal, Saturn standalone YabaSanshiro default | T3 2026-11-21: 1, 2, 3, 7 ok; 4 DC uneven, 5 Saturn slow + Select crash, 6 core list (fixed in m8e) |
| `dist/firmware/test128-m8c-20261120.img.zst` (raw `b0ca0ac9…`, p2 `51788316…`, U-Boot `159e086c…`) | Recovery 2026-11-20 → 21. m8b T3 round: advanced DraStic (two-screen layout, auto save state), DC Flycast 2022 (dArkOSen), PSP buffered rendering, wake without hold (kernel 0010 + CPU1-3), libmucursor | T3 2026-11-20: 1, 2, 3, 6, 8 ok; 4 stylus stick, 5 NDS resume/quit freeze, 7 DC uneven/half resolution (fixed in m8d); also boots the spare card in slot 1 |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 versions in `storage-retention.json` (m8f added 2026-11-21). The
next image retires m8c (or m8d).

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
3 menu sleeps in a row (M7 T3); m8b (2026-11-20): the 1 GiB p2 card
restored with saves, instant screen-off sleep in the menu, PSP and NDS
sleep on battery, God of War playable with frameskip 1, NDS DraStic
controls and saves.

## Open problems

- **Slot 2 (closed 2026-11-20, swap test):** with our image, test128
  runs in slot 2 at SDR104 (150 MHz, ~62 MB/s read, no errors) and the
  spare card (former original32) boots in slot 1 (SDR50): the failure is
  that card in slot 2 (contact or card), not the port. Slot 2 is left
  empty on the bench. muOS automounts a slot-2 card's first partition
  rw at `/mnt/sdcard` and creates `ARCHIVE`, `ROMS`, `ports` there (as
  upstream; it did so on test128's FAT p1).
- **Battery % short of 100 after sleeping on the charger (user,
  2026-11-19):** sleep with the charger in overnight, wake: 95 %, not
  100 %. The next boot logged dsoc 93.9 %, rsoc 92.9 %, OCV 4149 mV,
  remain 2368 of FCC 2550 mAh (FCC learned down from 3380). Likely the BSP
  gauge's charge-finish step (dsoc → 100 on charge done) doesn't run
  while suspended, and/or the low learned FCC. Low priority; look at it
  with the M7 power items.
- **p2 space:** 1 GiB since m8b, 468 MB free. ScummVM and the CJK fonts
  (decision 17) are next (by `write-p2`, no reflash).
- **Heavy systems (M8; performance first, AGENTS.md):** M8f thermal
  block: the DC "random frame skipping" was throttling to 1008 MHz (88 %
  game speed there); undervolt CPU −50 / GPU −25 mV on this unit (main
  DTB) keeps 1296 MHz on battery; GPU undervolt beyond −25 mV faults in
  PSP; charging during play is the largest heat source and the RK817
  limits do not act (play heavy systems on battery). PSP = PPSSPP
  v1.12.3 + FrameSkip 1, buffered since m8c (~8 % slower, accepted by the
  user); CPU-bound and thermally held at ~1000 MHz (78–84 °C) on the
  charger. Flycast v2.7 standalone (dArkOSen, M8f) is CPU-bound at ~15
  presented fps (emulation thread 100 % of a core) vs ~51 for Flycast
  2022: selectable, not the default. NDS = advanced DraStic, full speed. DC = Flycast 2022 at
  640x480 + framerate normal + muxretro's Speed Limiter since m8e (the
  user's fight 100 %, ~52 pictures/s; heavy attract scenes ~86 %); v2.7
  selectable. Saturn = standalone YabaSanshiro (Sonic R race 20-25 of 60
  emulated fps: the sound thread is the limit, too heavy for the RK3326;
  2D games untested), libretro selectable. The user wants any future FPS gain
  (other settings, emulator versions, a newer kernel with Vulkan) for
  PSP. Details in hardware-findings "Standalone emulators (M8)".
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
  until the game ends. The post-wake stutters were the slot-2 card's
  resume rescan spinning on CPU0 (m8c: kernel 0010, game on CPU1-3, no
  hold: 2–4 frames of 21–27 ms per wake in T2; m8c T3: fine). The
  slot-2 rescan cost ~3 s of CPU at boot and on every wake while the
  spare card was in slot 2 (now empty).
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
Answered 2026-11-20 (m8b T3): 26 slot-2 swap test: yes, the spare card
(former original32) may be erased (T3 queue item, needs the user's
hands); 27 DraStic and every other closed component stay in the
developer and the public image; the public image is published only
after explicit licence answers (pending-licenses.json `nds-drastic-m8`).
Standing rule (AGENTS.md "Heavy Systems"): heavy systems = maximum
performance first.

## Decisions for the user

28. **Undervolt in the public image.** It is per-chip: CPU −50 / GPU −25
    mV is stable on this unit (bin 0, leakage 19), others may freeze.
    Recommendation: stock voltages by default, undervolt as an opt-in
    (a menu toggle that switches the boot DTB, with the stock one as the
    fallback record), built in M9; this card keeps it.
29. **ScummVM default** for the SCUMMVM folder: the libretro core
    (muxretro overlay, states, volume bar) or the standalone (its own
    menus, 60 Hz). Recommendation: the core, after your T3.
30. **Flycast standalone:** keep it in the DC core list or drop it
    (~15 fps vs ~51 for Flycast 2022 in T2). Recommendation: drop it
    unless your T3 finds a game it runs better.

## T3 queue

**M8f checklist (image m8f, undervolt DTB; pt-BR labels).** Heavy games
on battery (the charger heats the console more than the game).

1. **Dreamcast** (Explorar conteúdo → DC → Power Stone 2 (USA)), on
   battery, 10 min of fights: no more "frame-skipping" spells (they were
   the CPU throttling to 1008 MHz; with the undervolt it stays at 1296).
   Synchronous Rendering is on by default now.
2. **Dreamcast standalone:** on Power Stone 2 press X → Opções do
   conteúdo → Núcleo do conteúdo → "Flycast - Standalone (dArkOSen)";
   start it: compare speed and controls with Flycast 2022 (T2: much
   slower). Fn+Start quits; the next start resumes where you left (auto
   state). Set the core back to "Flycast 2022 (dArkOSen)".
3. **PSP** (God of War), on battery, 10 min: no freezes or graphics
   glitches (the GPU undervolt is the risky part: PSP is where too deep a
   GPU undervolt froze it).
4. **ScummVM standalone** (Explorar conteúdo → SCUMMVM → The Secret of
   Monkey Island (CD DOS VGA)): it starts the game (this card's folder
   is on the standalone); music and voices from the CD tracks; move the
   pointer and click (note which buttons do what); save in the game
   menu; Fn+Start quits back to the list.
5. **ScummVM core:** X → Opções do conteúdo → Núcleo do conteúdo →
   "ScummVM" (libretro); start the game: the same checks; Start opens
   ScummVM's menu; the volume/brightness bar works; your save from item
   4 may not be shared (each keeps its own saves). Which do you prefer
   (decision 29)?
6. **NDS core list:** X → Opções do conteúdo → Núcleo do conteúdo on
   NSMB: only one "DraStic (Advanced)" entry.
7. **Saturn sleep:** in Sonic R, a short Power press sleeps and the next
   wakes into the game (sleep now stops YabaSanshiro, ScummVM and
   Flycast like the other standalones).
8. **Regression:** GBA or SNES game with a save: resume and save still
   there; short Power in the menu sleeps and wakes.

## Current milestone: M8 — card layout and the heavy systems (decisions 16, 17, 20)

Started 2026-11-20. Night 1 (unattended, 2026-11-20 01:30–03:30): items
1 (U-Boot root by device, written), 2 (quiet boot + logo, written), 7
(PSP standalone), 10 (wake in a game) done to T2; 6/8/9 built, blocked by
decisions 23/24; 3/4 need decision 25. Day (user present): night-1 T3
fixes (sleep screen-off, 3 s wake hold), PSP v1.12.3, DraStic, Flycast
v2.7, item 3 (m8b flashed, p3 restored). Details: milestones.md M8.
**Left:** see the m8c T3 round below.

**m8b T3 round (2026-11-20 evening; heavy systems = performance first,
AGENTS.md):** done to T2 and in m8c: 13 PSP buffered rendering (GoW
graphics), 14 advanced DraStic (layout vh_s0, auto save/load state, no
cursor), 15 DC Flycast 2022 (dArkOSen's default), 16 wake stutter root
cause (kernel 0010 + CPU1-3, no hold).

**m8c T3 round (2026-11-20 night):** done to T2 and in m8d (milestones.md
M8 26–30): NDS Fn+Start quit/save-state fix, right-stick stylus, quit
dimming, DC 2022 at 640x480 + framerate normal, 17 Saturn standalone
YabaSanshiro (Boost static, not in the rootfs); item 4 (slot-2 swap)
closed.

**m8d T3 round (2026-11-21 night, unattended):** done to T2 and in m8e
(milestones.md M8 33-36): DC speed limiter, Saturn vblank flips + menu
crash + SCSP wait, core lists by installed cores, NDS touch on R3,
Fn+Start fade, `t2-coremeter`; M8e T3 2–9 ok, m8e recovery.

**Thermal block + M8e T3 round (2026-11-21 day; milestones.md M8 38–44):**
dArkOSen manages heat as the port does; measured with `t2-thermal.sh`
(hardware-findings "M8 thermal block"): T1 harness done; T2 cap 1200
(−1.9 °C, small gain); T6 undervolt: CPU −50 / GPU −25 mV stable here,
promoted as the main DTB (GPU −50/−75 fault in PSP); T5 charger heat
measured, the RK817 limits do nothing (dropped); T3/T4 (GPU cap, IPA
tuning) not needed after the undervolt (no throttling on battery); T7 DC
synchronous rendering default (m8f-dc-sync); T8 one DraStic; T9 Flycast
standalone built from source, slower than 2022 (selectable); item 5
ScummVM core (pthreads; libco deadlocks under muxretro's worker thread)
+ standalone. **Left:** 18 overclock (now with thermal headroom: ~75 °C
at 1296 on battery), CJK fonts, 11, 12, the M8f T3, decisions 28–30.

**Older notes:** 18 overclock only where heat allows (on the charger
DC/Saturn/PSP hit 81-84 °C).

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
