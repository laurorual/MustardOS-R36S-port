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

**Phase 5 (own-card firmware). M1–M5 done; M4g = recovery image (M5's T3
found a menu-navigation bug, so M5 was not promoted). M6 (systems, cores,
build from source) in progress: release frontend, 14 new cores + N64
trial, M5 T3 fixes; image `test128-m6-20261119` built, trial root and
`write-p2` next.**

## Next session — read first

- Device on main = **M5 p2** (`768942b1…`) plus files installed live
  for M6 T2 (release frontend and muxretro, the new cores, core info
  files, core-assign, S99muos-ui, Wi-Fi worker, BIOS Report task); the
  root stayed rw after `install-rootfs.sh` (busy).
- Next: trial root with `build/m3a/test128-m6-20261119.p2.img`
  (p2 `ac695c52…`), the standard T2 set + `t2-wifi-toggle-loop.sh`, then
  `write-p2`; retire m4e1 (5/5 versions) before `retention.py add`.
- The user's spare card is in slot 2 (exFAT, `ROMS/megadrive`); it never
  initialises (open problem). `/dev/mmcblk0` is still slot 1.
- p3 has smoke ROMs in `ROMS/{ATARI2600,ATARI7800,PCE,NGPC,WS,SG1000,
  POKEMINI,DOS}/smoke.*` (`make-smoke-roms.py`): delete them before the
  user's T3.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, the user's spare card (exFAT) in slot 2: M4b image
  flashed 2026-11-14, then p2 written in place (`write-p2`) for M4d,
  M4e.1, M4f, M4g and M5. `user_init` = 0. Time zone −03; volume 55.
  - Boot records: main = `Image-ea8ac0033c0e` (0001–0008) +
    `panel0-bc04b6f8e4d4.dtb`; previous = `Image-d61188f3a808` (0007).
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
| `dist/firmware/test128-m6-20261119.img.zst` (raw `d443411e…`, p2 `ac695c52…`) | M6 so far: release frontend, 14 cores + N64 trial, M5 T3 fixes | built; trial root next |
| `dist/firmware/test128-m5-20261118.img.zst` (raw `64e45d74…`, p2 `768942b1…`) + `public-m5-20261118` | M5 | on the card; T3 2026-11-18: item 5 broke navigation → not promoted |
| **`dist/firmware/test128-m4g-20261118.img.zst`** (raw `a9d7cbc4…`, p2 `371b3f23…`) | **Recovery image since 2026-11-18 (night).** M4g | T3 1, 3, 4 passed |
| `dist/firmware/test128-m4f-20261117.img.zst` (raw `159d4894…`, p2 `46a573a0…`) | M4f | T3 2–6 passed |
| `dist/firmware/test128-m4e1-20261117.img.zst` (raw `c122c7f4…`, p2 `d73646be…`) | M4e.1 | T3 passed; retire for M6 |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

The M6 image is not yet in `storage-retention.json` (6 on disk until m4e1
is retired with `retention.py retire`).

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
screenshots (menu), Date and Time.

## Open problems

- **Slot 2 does not initialise the user's spare card (M5 T3 10):** at
  boot and on hotplug the card holds DAT0 busy before the first command
  and DAT3 reads low (as if unpowered); `mmc1: error -110`. DT, kernel
  source/config, regulators (vcc_sd LDO6 3.0 V, shared with slot 1),
  pinmux/pulls and GRF IO_VSEL match stock dArkOSen, whose log shows
  test128 at SDR104 in slot 2 of this unit. Next: the user's T3 (reseat;
  the same card under stock; another card).
- **p2 space:** 488 MB root, ~113 MB free with the M6 cores (FBNeo 80 MB,
  MAME 2003-Plus 43 MB). ScummVM does not fit (decision 17).
- **Wi-Fi zombie (M5 incident):** the 8821cu firmware can enter a C2H/
  H2C error loop. While connecting it is now detected (M6: dongle reset,
  T2 with an injected error). While "ready" nothing detects it yet (M7:
  liveness check, dwc2 rebind).
- **New systems: fps verdicts are synthetic** (an idle loop per core,
  60 fps everywhere, core 4–7 ms); real games are the user's (T3,
  decision 18). FBNeo, MAME, MSX, Coleco, Lynx, Sega CD, PCE CD need
  game or BIOS files to test at all.
- **Screenshots:** menu only (X+L2+R2, now with a flash); muxretro has
  no capture. X on the Configuration tile also opens Kiosk (upstream).
- **Battery:** (d) the BSP smoothing uses `abs(delta_cap)`.
- **USB (dwc2 misses port events):** `muos-usb-watchdog` (M4f) rebinds
  dwc2 after 3 disagreeing reads (not yet triggered by a real replug).
- **Upstream gaps:** see the gap inventory in roadmap.md.
- **Translation (pt-BR, M7):** parts stay English; the SFTP help text is
  English only; our own strings are not in language files.
- **Wi-Fi dongle (RTL8821CU):** the warm-reboot H2C case (1 in 7 since
  M4c); no software power cycle; inserting the dongle during boot is
  unqualified.
- **Wake:** Wi-Fi returns ~9 s after wake with ~0.7 s of slow frames;
  felt stronger in M5 T3 (likely the slot-2 card's init retries).
- **Power:** menu idle ~420 mA; no controllable LEDs.
- **Audio:** one unexplained no-sound report (M3d); WirePlumber "no
  profile" start failure retried; 3–8 underrun bursts per game; 200 %
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
- **Licences (M8):** Mali r13p0 (Hardkernel: no answer yet), the dirty
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

## Decisions for the user

Work continues without them; the recommendation applies until answered.

17. **p2 size** (488 MB, ~113 MB free after the M6 cores). ScummVM
    (~60–100 MB) and later cores need room. Recommendation: grow p2 to
    1 GiB in the M8 card layout (a reflash anyway, user present); ship
    ScummVM from then on; until then leave it out.
18. **Games for the new systems** (one per system; your own dumps): copy
    them to `ROMS/<DIR>` (ATARI2600, ATARI7800, LYNX, PCE, PCECD, NGP,
    NGPC, WS, WSC, MSX, COLECO, SG1000, SEGACD, ARCADE, NEOGEO, DOS,
    POKEMINI, N64) and the BIOS files to `MUOS/bios` (Diagnostics → BIOS
    Report lists them), or put them in `port/roms/<dir>` on the PC.
    Recommendation: yes; it turns the synthetic fps checks into real
    verdicts (T2 then runs them automatically).

## T3 queue

M5 T3 done 2026-11-18 (results in milestones.md). M6 checklist (draft;
for the M6 p2 once written):

1. **Configuration menu:** each row opens its own screen (Power →
   power settings, Backup → backup list). Backup: back up "Capturas de
   Tela" to SD1; Aplicativos → Archive Manager lists it; restore it.
2. **No test-image marks:** no "THIS IS A TEST IMAGE" banner, no
   FPS/CPU counter in any screen.
3. **Screens between UI and game:** start and quit a game, change the
   theme: no console text flashes (black or the last frame instead).
4. **Screenshot:** X+L2+R2 in the menu (not on the Configuration tile):
   a short white flash; the file is in `MUOS/screenshot`.
5. **Wi-Fi toggle:** off/on 3–4 times in Conectividade: back each time
   within ~30 s.
6. **Slot 2 diagnosis:** (a) with the console on, pull the spare card and
   push it in firmly; (b) if nothing shows, try the same card in slot 2
   under stock dArkOSen (original32 in slot 1): does dArkOSen see it?
   (c) optionally another card. Report which.
7. **New systems:** one game each where you have one (decision 18):
   plays at full speed with sound; saves/states for one of them.
8. **BIOS:** Task Toolkit → Diagnostics → BIOS Report: the report lists
   the BIOS files per core; a Coleco game without `colecovision.rom`
   shows a "BIOS missing" message.
9. **Auto-assign by folder name:** a folder named like dArkOS's
   (`ROMS/megadrive`, `ROMS/snes`) on slot 1 with a game: Explore shows
   and starts it with the port's core.
10. **N64 trial:** one game in `ROMS/N64`: playable or not?
11. **Regression:** a game with volume keys, sleep/wake in the game.

## Current milestone: M6 — systems, cores, build from source

Plan (roadmap.md), state:
1. M5 T3 fixes — done to T2: Config rows (frontend 0008), screenshot
   flash (0007), fbcon unbound under the UI (S99), Wi-Fi C2H reset
   (worker; `t2-wifi-toggle-loop.sh`, 10 cycles + injected error).
2. Release frontend (`TEST_IMAGE=0`) of libui, libmuxcom, libmuxmod,
   libplutosvg, muxfrontend, muhotkey, mubattery, muxretro — done to T2
   (screen sweep 44 ok/7 bounces, NES 59.76 fps). Config keys reviewed:
   106 absent keys, all with built-in defaults.
3. Cores (`build-cores.sh`): stella2014, prosystem, handy, beetle pce
   fast/neopop/cygne, blueMSX, gearcoleco, gearsystem, pokemini, FBNeo,
   MAME 2003-Plus, dosbox-pure, mupen64plus-next (trial) — built, symbol
   checked, 17 folders seeded; smoke fps 60 on 2600, 7800, PCE, NGPC, WS
   (SG-1000, Pokémon mini, DOS pending). Coredb system defaults = the
   port's cores (auto-assign). ScummVM: decision 17.
4. Kernel modules from source: `build-boot.sh modules-check` 553
   identical + 2 differing only in the build date — done.
5. BIOS: upstream core info files (muxretro's BIOS prompt) + Diagnostics
   → BIOS Report — done to T2 (task not yet run on the device).
6. Image, trial T2, `write-p2` — image built; trial next.

**Next milestone after M6:** M7 — polish: language, performance, power.
