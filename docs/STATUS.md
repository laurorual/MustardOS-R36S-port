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
layout and the heavy systems), closing with the m8g round; next M9
(public v1.0). 2026-11-21: m8e (recovery until 22), then the thermal
block (undervolt CPU −50 / GPU −25 mV as this unit's main DTB), ScummVM,
Flycast standalone: m8f, T3 2/6/7/8 ok → m8f is the recovery image.
2026-11-22 night: the M8f T3 round (ScummVM one entry + both cores in
the list + virtual keyboard, CJK languages), overclock measured and
dropped (heat-bound, item 18 closed): image m8g; the M8g T3 below.**

## Next session — read first

- Device = **m8f on p2**, powered off 2026-11-22 ~01:45 **with the
  trial root armed**: the next power-on boots the final m8g (p3
  `MUOS/trial/rootfs.img`, `4ca8c058…`, short trial T2 passed: CJK menu
  screenshots, NES 59.96) as a trial root; any later reboot returns to
  m8f. The user does the M8g T3 in that boot. `write-p2` of it was
  refused by the auto-mode classifier (unattended): do it with the user
  present (re-arm on main, reboot, `muos-root-trial write-p2
  /userdata/MUOS/trial/rootfs.img 4ca8c058a3a5…751`). Old p2 copy:
  `MUOS/trial/p2-previous.img` (m8e). 1 GiB p2 layout, `user_init` 0.
  Boot records: main = `Image-be499e33d4eb` + **`panel0-84611ef0394d.dtb`
  (undervolt CPU −50 / GPU −25 mV)**, previous = the same Image +
  `panel0-c97151d0ec1a.dtb` (stock). A freeze that looks like
  instability: `muos-boot-slot` back to the stock DTB.
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
| `dist/firmware/test128-m8g-20261122.img.zst` (raw `81613024…`, p2 `4ca8c058…`, U-Boot `159e086c…`) | M8f T3 round: ScummVM games as NAME/NAME.scummvm (one entry), "ScummVM - Standalone" in the core list, virtual keyboard (Select) in both, CJK languages with their fonts | trial-root T2 passed (`build/m8g/t2-m8g.sh`); T3 pending (the M8g checklist) |
| **`dist/firmware/test128-m8f-20261121.img.zst`** (raw `fe44baad…`, p2 `15b51793…`, U-Boot `159e086c…`) | **Recovery image since 2026-11-22.** M8e T3 round + thermal block: ScummVM core + standalone, Flycast v2.7 standalone, DC synchronous rendering, one DraStic (the image's p1 DTB is the stock one; the undervolt DTB is a boot record on this card only) | T3 2026-11-21: 2, 6, 7, 8 ok; 1 DC dips as before, 3 PSP as before; 4/5 ScummVM entry, keyboard, core list (fixed in m8g) |
| `dist/firmware/test128-m8e-20261121.img.zst` (raw `2f0293a2…`, p2 `e43458ce…`, U-Boot `159e086c…`) | Recovery 2026-11-21 → 22. m8d T3 round: DC speed limiter, Saturn vblank flips + menu crash fix + SCSP wait, core lists by installed cores, NDS touch on R3, Fn+Start fade | T3 2026-11-21: 2–9 ok; 1 DC uneven |
| `dist/firmware/test128-m8d-20261120.img.zst` (raw `c7520a89…`, p2 `37d7194d…`, U-Boot `159e086c…`) | m8c T3 round: NDS quit fix + right-stick stylus, DC Flycast 2022 at 640x480, Saturn standalone YabaSanshiro | T3 2026-11-21: 1, 2, 3, 7 ok (rest fixed in m8e) |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 versions in `storage-retention.json` (m8c retired, m8g added
2026-11-22). The next image retires m8d.

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
- **p2 space:** 1 GiB since m8b; 318 MB free in m8g (ScummVM, the CJK
  fonts in).
- **Heavy systems (M8; performance first, AGENTS.md):** they are held
  by heat, not by the clock cap. Undervolt CPU −50 / GPU −25 mV on this
  unit (main DTB) keeps DC at 1296 MHz on battery (94.7 → ~97 % speed;
  the user saw no difference, M8f T3); GPU undervolt beyond −25 mV faults
  in PSP. **Overclock dropped (M8g, item 18 closed):** 1512 MHz throttles
  to 81–83 °C within ~3 min and the allocator then also cuts the GPU: DC
  95.6 % (worse), PSP 12.3 vs 12.6 fps (the CPU averages ~1050 MHz at
  either cap); DC's Flycast DSP off: no gain. The remaining DC dips are
  heavy scenes (the same minutes in every run), beyond the RK3326 at
  640x480 (frame skip 1 or 320x240 would hide them; rejected). Charging
  during play is the largest heat source (play heavy systems on
  battery). PSP = PPSSPP v1.12.3 + FrameSkip 1, buffered. DC = Flycast
  2022 at 640x480 + Speed Limiter + synchronous rendering; Flycast v2.7
  standalone selectable (~15 fps, kept by decision 30). NDS = advanced
  DraStic, full speed. Saturn = standalone YabaSanshiro (Sonic R 20–25
  fps: too heavy), libretro selectable. The user wants any future FPS
  gain for PSP: only less work per frame helps (emulator, settings, a
  newer kernel/GPU driver). Details in hardware-findings "Standalone
  emulators (M8)" and "M8 thermal block".
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
  names. Chinese (Simplified/Traditional), Japanese and Korean ship
  since m8g with upstream's fonts (decision 17).
- **Menu sleep, one missed press (M7 soak):** 1 of 15 Power presses
  (20 s after a resume) reached muos-hotkey but muos-suspend exited
  silently (its lock or the recent-wake guard); not reproduced in 5 more
  cycles. Both exits log since M8 (item 11): no "ignored:" line in the
  m8f day's logs.
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
Answered 2026-11-21 (M8f T3): 28 undervolt as an opt-in, stock voltages
by default (agreed; the row goes in Configuração → Configurações
perigosas, below "Máximo do processador", built in M9; this card keeps
the undervolt DTB); 30 keep the Flycast standalone in the DC list.
Standing rule (AGENTS.md "Heavy Systems"): heavy systems = maximum
performance first.

## Decisions for the user

29. **ScummVM default** for the SCUMMVM folder: the libretro core
    (muxretro overlay, states, volume bar) or the standalone (its own
    menus, 60 Hz). Both are now in the core list (M8g T3 3).
    Recommendation: the core, unless your T3 prefers the standalone.

## T3 queue

**M8g checklist (pt-BR labels).** The first power-on boots m8g as a
trial root: do the whole list in that boot (a restart goes back to m8f;
then just tell the agent).

1. **ScummVM list** (Explorar conteúdo → SCUMMVM): one entry "The Secret
   of Monkey Island (CD DOS VGA)" (no second one); it starts (on this
   card: the standalone, as assigned before).
2. **ScummVM standalone, typing a save name:** in the game, Start opens
   ScummVM's own menu → Save (its menus may be in English) → pick a slot: Select opens the virtual
   keyboard; move the pointer (stick/d-pad) and A on the keys, then its
   Enter/OK; save. Fn+Start quits; start again, Start → Load: your save
   is there.
3. **ScummVM core list + core:** X on the game → Opções do conteúdo →
   Núcleo do conteúdo: two entries, "ScummVM" and "ScummVM -
   Standalone"; pick "ScummVM", start: the game runs, Select opens the
   virtual keyboard, the volume/brightness bar works, saving from item 2
   is not shared (each keeps its own). Which do you prefer (decision 29)?
4. **Japanese / Korean / Chinese:** Configuração → Idioma → "Japanese"
   (the list keeps English names): the menu shows Japanese text (no
   empty boxes); the same for "Korean" and "Chinese (Simplified)"; back to
   "Portuguese (BR)".
5. **Regression:** a GBA or SNES game with a save resumes; DC Power
   Stone 2 starts as before; short Power in the menu sleeps and wakes.

DC note (M8f T3 1): the short dips are heavy scenes the RK3326 can't
hold at 60 fps; nothing measured removes them (overclock makes it worse,
see "Heavy systems"). No DC item this round.

## Current milestone: M8 — card layout and the heavy systems (decisions 16, 17, 20)

Started 2026-11-20; rounds m8b → m8g (per-round details and T3 results
in milestones.md M8, items 1–46). **State of the items:** 1 clean U-Boot
+ `root=` by device, 2 quiet boot + logo, 3 the 1 GiB p2 layout, 4 the
slot-2 swap, 5 ScummVM (core + standalone, virtual keyboard) and the CJK
fonts, 6 DC (Flycast 2022, v2.7 standalone), 7 PSP (PPSSPP v1.12.3), 8
NDS (advanced DraStic), 9 Saturn (standalone YabaSanshiro), 10 wake in a
game, 11 the sleep-exit logging: done (T3 per round). 18 overclock:
measured and dropped (heat-bound, M8g). 12 battery % after sleeping on
the charger: moved to M9 (the BSP gauge's charge-finish step, low
priority). Thermal block: undervolt on this unit (decision 28 makes it
an M9 opt-in).

**m8g round (2026-11-22 night):** M8f T3 fixes (ScummVM one entry,
"ScummVM - Standalone" key, virtual keyboard, the core's extra/theme
data), CJK languages + fonts, overclock and DSP measurements (no
change). Trial-root T2 passed (the build before the CJK language-file
fix); the device went off the network on the reboot after the batch
(Wi-Fi; the user reconnected it). The final p2's short trial T2 passed
(`build/m8g/t2-cjk.sh`: Japanese/Korean/Chinese menus render; NES
59.96). **Next:** `write-p2` with the user present (refused unattended),
then the M8g T3 results. **M8 closes
when the M8g T3 passes**; its findings are fixed inside M9.

Tests: T0 builds and shellcheck; T1 ELF/ABI checks; T2 trial root
(`build/m8g/t2-m8g.sh`: sweep, NES, sdcard, SFTP jail, ScummVM core +
standalone, Flycast standalone, DC 2022, NDS, Saturn, PSP, wake) and
`build/m8g/t2-cjk.sh` (menu screenshots in Japanese, Korean, Chinese).

## Next milestone: M9 — public v1.0

Plan in roadmap.md M9 (licences, the public variant, install guide,
rc1 → T3 on a blank card with the user present).
