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

**Phase 5 (own-card firmware). M1–M5, M7 and M8 done (M8g T3 passed
2026-11-22, m8g is the recovery image). Current: M9 (public v1.0),
first round m9a (2026-11-22, user present): M8g T3 fixes (ScummVM
keyboard), decision 29, Japanese/Chinese menu overlays, the Undervolt
row (decision 28); M9a T3 passed → m9a is the recovery image. Then
(installed on the bench, not yet in an image): Traditional Chinese
overlay (decision 31, OpenCC), the CPU/GPU undervolt rows. **Token
budget is nearly spent until 2026-11-25: plan for minimal tokens.**

## Next session — read first

- Device = **m9a on p2** (written 2026-11-22 ~13:00 with the user
  present, after its trial-root T2 `build/m9/t2-m9a.sh` passed). Old p2
  copy: `MUOS/trial/p2-previous.img` (the used m8g p2 `678e3766…`;
  m8g is the recovery image). 1 GiB p2 layout, `user_init` 0. Boot
  records: main = `Image-be499e33d4eb` + **`panel0-84611ef0394d.dtb`
  (undervolt, label `undervolt-on`)**, previous = the same Image +
  `panel0-c97151d0ec1a.dtb` (stock, `undervolt-off`); p1
  `dtb-variants.txt` (by hand on this card; the image build writes it
  since m9a). The Undervolt row switches them (or `muos-undervolt`).
- The user does the M9a T3 (below) on p2.
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
  the folder's assignment on this card is the standalone (a fresh card
  seeds the standalone too since decision 29).

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, slot 2 empty: m8b flashed whole 2026-11-20 (1 GiB
  p2 layout; p3 restored), m8c–m8f, then m8g (2026-11-22) written to
  p2. `user_init` = 0. Time zone −03.
  - Boot records: main = `Image-be499e33d4eb` + `panel0-84611ef0394d.dtb`
    (M8: mmc DT aliases, dw_mmc set_ios sleeps; CPU OPPs to 1512 MHz, cap
    1296; M8f undervolt CPU −50 / GPU −25 mV, switched by the Undervolt
    row since M9); previous = the same Image + `panel0-c97151d0ec1a.dtb`
    (stock voltages).
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
| **`dist/firmware/test128-m9a-20261122.img.zst`** (raw `093d64ce…`, p2 `ed83f5f4…`, U-Boot `159e086c…`) | M8g T3 round + M9 start: ScummVM keyboard preview + paced keys, ScummVM standalone default, Undervolt row (both DTBs on p1, stock by default), Japanese/Chinese menu overlays | **Recovery image since 2026-11-22 (afternoon).** T2 `build/m9/t2-m9a.sh`, on p2; M9a T3 1–5 ok |
| **`dist/firmware/test128-m8g-20261122.img.zst`** (raw `81613024…`, p2 `4ca8c058…`, U-Boot `159e086c…`) | Recovery 2026-11-22 (morning). M8f T3 round: ScummVM games as NAME/NAME.scummvm (one entry), "ScummVM - Standalone" in the core list, virtual keyboard (Select) in both, CJK languages with their fonts | T3 2026-11-22: 1–5 ok; keyboard preview/in-game names and CJK text completeness fixed in m9a |
| `dist/firmware/test128-m8f-20261121.img.zst` (raw `fe44baad…`, p2 `15b51793…`, U-Boot `159e086c…`) | Recovery 2026-11-22 (morning). M8e T3 round + thermal block: ScummVM core + standalone, Flycast v2.7 standalone, DC synchronous rendering, one DraStic | T3 2026-11-21: 2, 6, 7, 8 ok |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 versions in `storage-retention.json` (m8d retired when m8g became
recovery, m9a added and m8e retired 2026-11-22). The next image
retires m8f.

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
  since m8g with upstream's fonts (decision 17). Upstream's Japanese and
  Chinese texts are incomplete: since m9a the port's overlays translate
  the menu labels (Japanese, Simplified); help texts and Traditional
  Chinese stay as upstream (decision 31).
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
Answered 2026-11-22 (M8g T3): 29 the ScummVM standalone is the SCUMMVM
default (done in m9a). Answered 2026-11-22 (M9a T3): 31 OpenCC allowed
(venv `build/tools/opencc-venv`): Traditional Chinese overlay done. The
user asked for manual CPU/GPU undervolt values (other R35S/R36S units):
two rows below Undervolt, 25 mV steps, the image ships all 16 DTBs.
Standing rule (AGENTS.md "Heavy Systems"): heavy systems = maximum
performance first.

## Decisions for the user

None open.

## T3 queue

M9a T3 passed 2026-11-22 (1–5 ok). Next round (visual only, no voltage
tests, the user's call): Configuração → Configurações perigosas: below
"Undervolt" the rows "Undervolt do processador" (−25…−100 mV, default
−50) and "Undervolt dos gráficos" (0…−75 mV, default −25) look right
(checked by screenshot `build/logs/m5/shots/m9b-danger-uv.png`); the
Chinese (Traditional) menus.

## Current milestone: M9 — public v1.0 (started 2026-11-22)

M8 closed 2026-11-22: the M8g T3 passed (1–5 ok, small findings below),
m8g written to p2 with the user present and promoted to recovery (m8d
retired). Plan in roadmap.md M9. **Items:**

1. **M8g T3 fixes:** ScummVM virtual keyboard preview without brackets
   per letter; the in-game save name got only the last letter (SCUMM
   keeps one key per tick, the keyboard pushed all at once): keys now
   delivered one at a time, 60 ms apart (patch
   `port/patches/scummvm/0001`, core + standalone).
2. **Decision 29:** the ScummVM standalone is the SCUMMVM default
   (core-assign.txt, coredb runtime external; the same latent coredb
   fix for Saturn).
3. **CJK menus:** upstream's Japanese (~86 % English), Chinese
   Traditional (~80 %) and Simplified (~39 %) are incomplete even in
   the 2026-11-22 pack: a port overlay for the menu labels.
4. **Undervolt opt-in (decision 28):** Danger Settings → "Undervolt"
   (frontend patch 0012, `muos-undervolt`, the image ships both DTBs
   and p1 `dtb-variants.txt`); switching arms a trial boot and
   reboots, 20 s of menu promotes it.
5. **Licences:** close `pending-licenses.json` as far as the answers
   allow (Mali: no answer yet); third-party notices in the image.
6. **GPL source bundle** (decision 4) and the public variant's T2
   (`check-public-image.sh`, first-boot flow).
7. **Docs:** install guide (EN + pt-BR), changelog, known issues,
   SHA256.
8. **Update path for v1.x** (reflash keeping p3, or an update package).
9. **Battery % after sleeping on the charger** (moved from M8 item 12).
10. **rc1** → T3 on a blank card with the user present → v1.0.

**State:** 1–4 done (m9a, T3 passed; recovery). Added: Traditional
Chinese overlay, CPU/GPU undervolt rows (on the bench, next image).
5–10 next.

Tests: T0 builds/shellcheck; T1 ELF checks; T2 trial root (sweep, NES,
ScummVM core + standalone, the undervolt round trip on and off, CJK
screenshots); T3 the M9 checklist (keyboard names in the game, the
Undervolt row, CJK menus, rc1 on a blank card).
