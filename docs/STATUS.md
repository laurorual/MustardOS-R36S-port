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

**Phase 5 (own-card firmware). M1–M5 done; M6 folded into M7. M7
(polish) done to T2 2026-11-19: image `test128-m7d-20261119` on p2, its
T3 (the M7 checklist below) pending. Recovery image: m7c. Next: M8 (needs
the user present).**

## Next session — read first

- Device on main = **M7d p2** (`176c691a…`, build `r35s-1ed3ce6`;
  written 2026-11-19 ~22:00 by `write-p2` from the trial root; the
  previous p2 saved as `MUOS/trial/p2-previous.img` `21fbc43b…`), no
  live installs on top. The muos-suspend/muos-hotkey logging of silent
  sleep exits (M7 item 26) is in the repo only (next image). Boot
  records: main = the M7 DTB.
- CTR test state (the user's scene, mid-race, unpaused): p3
  `MUOS/port/t2/ctr-race` (`t2-long-play.sh --state`, `t2-soak.sh`).
- Idle discharge run done (report in hardware-findings, logger stopped).
- Device volume 40 (the user's).
- The standalone N64 SRAM of DK64 and MK64 was migrated from the
  libretro .srm on 2026-11-19 (`MUOS/t2-bak` deleted after the M7c T3).
- New-system ROMs from `port/roms/` on p3 (2026-11-19): 32X, ATARI2600,
  ATARI7800, GG, LYNX, SMS, PCE, SEGACD (Sonic CD), PCECD (Dracula X);
  BIOS `bios_CD_U.bin`, `syscard3.pce` in p3 `MUOS/bios`.
- Slot 2 waits for M8 (decision 16).
- Smoke ROMs deleted from p3 (2026-11-19); `make-smoke-roms.py` makes
  them again for T2.
- The user's spare card is in slot 2 (exFAT, `ROMS/megadrive`); it never
  initialises (open problem). `/dev/mmcblk0` is still slot 1.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, the user's spare card (exFAT) in slot 2: M4b image
  flashed 2026-11-14, then p2 written in place (`write-p2`) for M4d,
  M4e.1, M4f, M4g, M5 and M7 (m7, m7t3, m7c, m7d). `user_init` = 0. Time
  zone −03; volume 40 (the user's; T2 runs use 10 and restore it).
  - Boot records: main = `Image-ea8ac0033c0e` + `panel0-0475265be8ac.dtb`
    (M7: CPU OPPs to 1512 MHz, capped at 1296 by `danger/cpu_max`);
    previous = `Image-ea8ac0033c0e` + `panel0-bc04b6f8e4d4.dtb` (M4f–M6).
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
| `dist/firmware/test128-m7d-20261119.img.zst` (raw `67ae7da4…`, p2 `176c691a…`) | M7 final: m7c + N64 defaults to the standalone Rice (decision 22), pruned N64 core list | on the device; T3 pending (the M7 checklist); promote on pass |
| `dist/firmware/test128-m7-20261119.img.zst` (raw `528da83a…`, p2 `c24516fb…`) | M7 so far (contains M6): language pack + pt-BR, Wi-Fi liveness, 1512 MHz opt-in DTB, faster boot | T3 2026-11-19: N64 crash, blink, archive mark (fixed in m7t3) |
| **`dist/firmware/test128-m7c-20261119.img.zst`** (raw `5878d3b3…`, p2 `701eb2a8…`) | **Recovery image since 2026-11-19.** M7c: the M7 T3-fix fixes (Danger screen, cap switch, N64 warm-up), standalone Mupen64Plus, suspend stop/continue, PipeWire stall self-heal | T3 2026-11-19: 1–8 passed (4 partial: no level bar or screenshot feedback in the standalone N64) |
| `dist/firmware/test128-m7t3-20261119.img.zst` (raw `9c60175f…`, p2 `c1f45838…`) | M7 + its T3 fixes (recovery until m7c) | T3 2026-11-19: 1–5 passed, 6 partial (Danger screen, fixed in m7c) |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 versions in `storage-retention.json` (m5 retired 2026-11-19 when
m7c became recovery, 530 MiB). The next image (or m7d's promotion)
retires m7.

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
Rice (saves, resume, sleep, levels; GLideN64 works but slow); 32X, 2600,
7800, GG, Lynx, SMS, PCE, Sega CD and PCE CD.

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
- **p2 space:** 488 MB root, ~113 MB free with the M6 cores (FBNeo 80 MB,
  MAME 2003-Plus 43 MB). ScummVM does not fit (decision 17).
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
  M4c); no software power cycle; inserting the dongle during boot is
  unqualified.
- **Wake:** Wi-Fi returns ~9.3–10.2 s after wake (M7 timeline in
  hardware-findings: the 4 s CD-ROM settle dominates); ~0.7 s of slow
  frames in a game; felt stronger in M5 T3 (likely the slot-2 card).
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

None open.

## T3 queue

**M7 checklist (image m7d, on the device; pt-BR menu labels).** The
M6/M7, M7 T3-fix and M7c checklists are done (milestones.md M7 items 11,
13, 20). CPU stays at the default 1296 MHz for all of it.

1. **N64 default** (Explorar conteúdo → N64 → Mario Kart 64 (USA)): it
   starts in the standalone Mupen64Plus without choosing a core; your
   time-trial save is there; Fn+Start quits; start it again: it resumes.
2. **N64 core list** (Explorar conteúdo → N64 → focus a game → Select →
   OPÇÕES DO CONTEÚDO → Núcleo do conteúdo → "Nintendo N64"): among the
   standalone entries only "Mupen64Plus - Standalone - Glide" and
   "- Rice" (no "Full", no "GlideMk2").
3. **DK64** (Explorar conteúdo → N64 → Donkey Kong 64): still Rice, save
   and resume as in the M7c T3.
4. **Dongle inserted during boot:** main menu → Desligar; take the Wi-Fi
   dongle out; power on; plug it in while the boot logo shows. In the
   menu: Configuração → Conectividade → Rede Wi-Fi: it connects (network
   icon in the header within ~30 s).
5. **Long play (~15 min):** CTR (Explorar conteúdo → PSX) or MK64,
   really playing: no slowdowns beyond the game's own, no sound cuts; the
   console gets warm (~80 °C is normal).
6. **Sleep in the menu, 3× in a row:** short Power → screen off; Power
   again → menu back; repeat about 20 s after each wake. Every press must
   sleep (note any press that does nothing).
7. **Sleep in a game:** one libretro game (e.g. NES) and MK64: short
   Power, wake after ~1 min: the game continues where it was, sound back.
8. **Regression:** Desligar, power on: menu in pt-BR; in a libretro game
   volume and brightness show the bar; Wi-Fi connects; Fn+Start from
   N64 back to the menu.

Not for this checklist (known limitations): the standalone N64 has no
level bar and no screenshot feedback (Fn+X still saves); 1512 MHz is not
recommended for long sessions (thermal, M7 item 23).

## Current milestone: M7 — done to T2 2026-11-19, T3 pending

Items 1–26 and their results: [milestones.md](milestones.md) (M7). All
work items are done to T0–T2; only the T3 checklist above remains. On a
pass: m7d → recovery, m7 retired (rule 2026-11-13).

## Next milestone: M8 — card layout and the heavy systems (decisions 16, 17, 20)

Plan (roadmap.md M8), **needs the user present** for the bootloader and
partition-table writes:
1. Clean U-Boot build, `root=` by the slot-1 device (decision 16): T0–T2
   on the trial path first; the bootloader write with the user there.
2. Card layout with p2 at 1 GiB (decision 17), a matching recovery image.
3. Slot-2 swap test (our image on the former original32 in slot 1,
   test128 in slot 2).
4. ScummVM and the CJK fonts (decision 17).
5. Dreamcast (Flycast), PSP (PPSSPP), NDS (licence check for DraStic,
   else melonDS/DeSmuME), Saturn last (decision 20); PSP/NDS standalone
   with the `muos-mupen64plus` launcher pattern.
6. The M7 T3 results and the sleep-exit logging (item 26) folded in.
Work that needs no user (emulator builds, T1, launchers) can start
before the bootloader session.
