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

**Phase 5 (own-card firmware). M1–M5 done; M4g = recovery image. M6
(systems, cores) done to T2 and folded into M7. M7 (polish) first part
done to T2: image `test128-m7-20261119` passed T2 as the trial root
(2026-11-19 ~03:00). `write-p2` is waiting for the user: the Claude Code
permission check refuses it while the user is away (also on 2026-11-17),
although AGENTS.md pre-authorizes it.**

## Next session — read first

- Device on main = **M5 p2** (`768942b1…`) plus files installed live for
  M6/M7 T2 (frontend, cores, language pack, watchdog, governor, muos-rc,
  S91); boot records: main = the M7 DTB (promoted after its trial boot).
  It was powered off at the end of the session (on the charger).
- Next, **with the user present** (or a permission rule for it):
  `write-p2` of `MUOS/trial/rootfs.img` = M7 p2 `c24516fb…` (on p3 with
  its `.sha256`): arm `/etc/muos-root-trial` on main, reboot,
  `/usr/libexec/muos-root-trial write-p2 /userdata/MUOS/trial/rootfs.img
  c24516fbf2431fd395d52cc8ae14b83271ee57e19d5146ca3b18ef938422d5f0`,
  reboot. Then hand over the T3 list below.
- Smoke ROMs deleted from p3 (2026-11-19); `make-smoke-roms.py` makes
  them again for T2.
- The user's spare card is in slot 2 (exFAT, `ROMS/megadrive`); it never
  initialises (open problem). `/dev/mmcblk0` is still slot 1.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, the user's spare card (exFAT) in slot 2: M4b image
  flashed 2026-11-14, then p2 written in place (`write-p2`) for M4d,
  M4e.1, M4f, M4g and M5. `user_init` = 0. Time zone −03; volume 10
  (lowered for the night T2).
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
| `dist/firmware/test128-m7-20261119.img.zst` (raw `528da83a…`, p2 `c24516fb…`) | M7 so far (contains M6): language pack + pt-BR, Wi-Fi liveness, 1512 MHz opt-in DTB, faster boot | trial root T2 passed; `write-p2` waits for the user |
| `dist/firmware/test128-m6-20261119.img.zst` (raw `d443411e…`, p2 `ac695c52…`) | M6 | trial T2 passed; never written (superseded) |
| `dist/firmware/test128-m5-20261118.img.zst` (raw `64e45d74…`, p2 `768942b1…`) + `public-m5-20261118` | M5 | on the card; T3 2026-11-18: item 5 broke navigation → not promoted |
| **`dist/firmware/test128-m4g-20261118.img.zst`** (raw `a9d7cbc4…`, p2 `371b3f23…`) | **Recovery image since 2026-11-18 (night).** M4g | T3 1, 3, 4 passed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 versions in `storage-retention.json` (m4e1 and m4f retired
2026-11-19). The next image retires m5 (keep m4g while it is recovery).

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
- **Wi-Fi zombie (M5 incident):** handled since M7: while connecting by
  the worker (dongle reset), while "ready" by `muos-usb-watchdog` (C2H
  errors or a silent gateway → dwc2 rebind; T2 with injected errors and
  test hooks). A real occurrence is unverified.
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
- **Translation (pt-BR):** every frontend string has pt-BR text since M7
  (upstream language pack + the port's overlay). Still English, as
  upstream: task names (file names), sort tags, time zone and language
  names. Chinese, Japanese and Korean are not shipped until p2 has room
  for their fonts (decision 17).
- **Wi-Fi dongle (RTL8821CU):** the warm-reboot H2C case (1 in 7 since
  M4c); no software power cycle; inserting the dongle during boot is
  unqualified.
- **Wake:** Wi-Fi returns ~9.3–10.2 s after wake (M7 timeline in
  hardware-findings: the 4 s CD-ROM settle dominates); ~0.7 s of slow
  frames in a game; felt stronger in M5 T3 (likely the slot-2 card).
- **Power:** menu idle ~420 mA (not re-measured in M7: the device was on
  the charger); no controllable LEDs.
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
    ScummVM and the CJK fonts (Noto Sans SC/TC/JP/KR, 29 MiB: Chinese,
    Japanese, Korean menus) from then on; until then leave them out.
18. **Games for the new systems** (one per system; your own dumps): copy
    them to `ROMS/<DIR>` (ATARI2600, ATARI7800, LYNX, PCE, PCECD, NGP,
    NGPC, WS, WSC, MSX, COLECO, SG1000, SEGACD, ARCADE, NEOGEO, DOS,
    POKEMINI, N64) and the BIOS files to `MUOS/bios` (Diagnostics → BIOS
    Report lists them), or put them in `port/roms/<dir>` on the PC.
    Recommendation: yes; it turns the synthetic fps checks into real
    verdicts (T2 then runs them automatically).

19. **`write-p2` while you are away:** the Claude Code permission check
    refuses it unattended (2026-11-17 and 2026-11-19), so each milestone's
    p2 waits for you. Recommendation: add a permission rule for
    `muos-root-trial write-p2` (it only runs after a T2-passed trial root,
    and the previous p2 is saved for a rollback), or tell me in the
    morning to run it with you nearby.

## T3 queue

M5 T3 done 2026-11-18 (results in milestones.md). **M6 + M7 checklist**
(on the M7 p2, after `write-p2`):

1. **pt-BR everywhere:** browse Configuração, Conectividade, Serviços
   web (SSH/"Arquivos via SFTP" and their help with Menu/Fn), Energia,
   Aparência: no English except task names, tags and time zones. System
   details → Compilação shows `r35s-a868092`.
2. **Configuration menu:** each row opens its own screen (Power → power
   settings, Backup → backup list). Backup "Capturas de Tela" to SD1;
   Aplicativos → Archive Manager lists it; restore it.
3. **No test-image marks; no console text** between UI and game: start
   and quit a game, change the theme: black or the last frame only.
4. **Screenshot:** X+L2+R2 in the menu (not on the Configuration tile):
   a short white flash; the file is in `MUOS/screenshot`.
5. **Wi-Fi:** off/on 3–4 times in Conectividade (back within ~30 s
   each); then leave the console idle in the menu for 10+ minutes and
   check SSH/Wi-Fi still answer (the new liveness watchdog must not
   reset a healthy connection: `MUOS/log/...usb-watchdog.log` has no
   "Wi-Fi dead" line).
6. **CPU 1512 MHz (opt-in):** Configurações perigosas → Máximo do
   processador lists up to "Máxima (1512 MHz)" with 1296 MHz selected. Choose Máxima, play a
   heavy game (PSX) 10 min: no freeze; then set 1296 again.
7. **Boot:** two cold boots: the menu appears ~3 s sooner on the
   second (core assignments cached); everything still assigned.
8. **Slot 2 diagnosis:** (a) with the console on, pull the spare card
   and push it in firmly; (b) if nothing shows, the same card in slot 2
   under stock dArkOSen (original32 in slot 1); (c) another card.
9. **New systems:** one game each where you have one (decision 18):
   full speed with sound; saves/states for one of them; N64 playable?
10. **BIOS:** Task Toolkit → Diagnostics → BIOS Report lists the BIOS
    files per core; a Coleco game without `colecovision.rom` shows a
    "BIOS missing" message.
11. **Auto-assign by folder name:** `ROMS/megadrive` (or `snes`) on slot
    1 with a game: Explore shows and starts it with the port's core.
12. **Regression:** a game with volume keys, sleep/wake in the game.

## Current milestone: M7 — polish: language, performance, power (started 2026-11-19)

Goal (roadmap.md): pt-BR complete, wake/audio/Wi-Fi robustness, the
1512 MHz opt-in, idle power, a soak. State (logs `build/logs/m7/`):
1. **Languages — done to T2:** the pinned upstream language pack
   (MustardOS/language `3db301a`, `muos-language.txt`) replaces
   internal's stale `share/language` (2679 of 3318 strings had no pt-BR
   text); the port overlay (`port/packaging/language/`) adds the 32
   newer strings, the Wi-Fi radio help (frontend 0001 now translates it)
   and a jail-accurate SFTP help; CJK out (decision 17), Arabic font in.
   Screen sweep: 44 ok; pt-BR complete except upstream file-name texts.
2. **Wi-Fi liveness — done to T2** (`t2-wifi-liveness.sh` c2h + silent).
3. **CPU 1512 MHz opt-in — done to T2:** DTS OPPs, `muos-governor` caps
   (`danger/cpu_max` default 1296000), `muos-rc` early cap; trial boot,
   3 min 4-core load at 1512 MHz/1.35 V (max 73.8 °C), sleep/wake;
   promoted to main.
4. **Wake — measured, unchanged** (timeline in hardware-findings).
5. **Audio:** the WirePlumber retry stays (15/15 in M5); underruns not
   worked on yet.
6. **Idle power / DDR devfreq:** not measurable on the charger; open.
7. **Wi-Fi warm-reboot H2C / dongle at boot:** covered by the worker
   retries and the liveness watchdog; the plug-during-boot case needs
   hands (T3 later).
8. **Boot time:** UI at ~17 s uptime; S99 now skips upstream assign.sh
   when core.json and the script are unchanged (−3 s from the second
   boot). Soak: not yet.
9. M6 T3: folded into the checklist above.
10. **Image `test128-m7-20261119`** (`a868092`): trial root T2 passed
    (NES 60.00, DOS 60.02, sleep 2/2 + 1/1 in game, t2-sdcard,
    t2-sftp-jail, Wi-Fi toggle 3/3 + C2H, liveness C2H); `write-p2`
    waits for the user (decision 19).
Remaining for M7 after the T3: underrun bursts, idle power (off the
charger), a soak (hours of play, discharge), the T3 fixes.

**Next milestone after M7:** M8 — public v1.0.
