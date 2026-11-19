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
folded into M7. M7 (polish): first image T3-tested 2026-11-19; its T3
fixes are in image `test128-m7t3-20261119` (`5e72cfa`), written to p2
2026-11-19 ~13:15; its T3 (2026-11-19) passed except the Danger screen
→ recovery image. Its T3 fixes (Danger screen, cap switch, N64 resume)
are done to T2 on the live root; the next image carries them.**

## Next session — read first

- Device on main = **M7 T3-fix p2** (`c1f45838…`, build `r35s-5e72cfa`,
  written 2026-11-19 by `write-p2`; the previous p2 = M7 `c24516fb…`,
  saved as `MUOS/trial/p2-previous.img` `01e4c0bf…` incl. its boot-time
  state); boot records: main = the M7 DTB.
- The live root (rw since `install-rootfs.sh`, until the next reboot)
  differs from p2 `c1f45838…`: frontend 0011 `libmuxmod.so` and
  `muos-governor` (min-before-max cap). The N64 warm-up is only in
  post-build (tested with a bind-mounted info copy).
- **Idle discharge log running** (`t2-discharge.sh log-start`, started
  2026-11-19 14:27 at 22 %, menu idle, backlight 60, ~412 mA at
  3.56 V; samples 14:31–14:33 are inflated by an agent grep over p3):
it ends at the low-battery poweroff; leave the device alone until then; after the user charges
  and powers on: `t2-discharge.sh report`, then `log-stop`.
- Slot 2 waits for M8 (decision 16).
- `build/m3c/cores/debug/` holds the -g mupen build matching the shipped
  core (45 MB, for gdb); delete it once N64 is T3-confirmed.
- Smoke ROMs deleted from p3 (2026-11-19); `make-smoke-roms.py` makes
  them again for T2.
- The user's spare card is in slot 2 (exFAT, `ROMS/megadrive`); it never
  initialises (open problem). `/dev/mmcblk0` is still slot 1.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, the user's spare card (exFAT) in slot 2: M4b image
  flashed 2026-11-14, then p2 written in place (`write-p2`) for M4d,
  M4e.1, M4f, M4g, M5 and M7. `user_init` = 0. Time zone −03; volume 10
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
| `dist/firmware/test128-m7-20261119.img.zst` (raw `528da83a…`, p2 `c24516fb…`) | M7 so far (contains M6): language pack + pt-BR, Wi-Fi liveness, 1512 MHz opt-in DTB, faster boot | T3 2026-11-19: N64 crash, blink, archive mark (fixed in m7t3) |
| **`dist/firmware/test128-m7t3-20261119.img.zst`** (raw `9c60175f…`, p2 `c1f45838…`) | **Recovery image since 2026-11-19.** M7 + its T3 fixes | on the device; T3 2026-11-19: 1–5 passed, 6 partial (Danger screen, fixed since) |
| `dist/firmware/test128-m5-20261118.img.zst` (raw `64e45d74…`, p2 `768942b1…`) + `public-m5-20261118` | M5 | on the card; T3 2026-11-18: item 5 broke navigation → not promoted |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

4/5 versions in `storage-retention.json` (m4g retired 2026-11-19 when
m7t3 became recovery). The image after next retires m5.

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

Answered 2026-11-19: 17 grow p2 to 1 GiB in the M8 card layout, then
ship ScummVM and the CJK fonts (recommendation accepted); 18 the user
provides game dumps: after every T3 check `port/roms/` on the PC and use
any ROM of a not yet tested system for its core's T2 (none new as of
2026-11-19: bios, gb, gba, megadrive, n64, nes, psx, snes).

## Decisions for the user

None open.

## T3 queue

M7 T3-fix checklist done 2026-11-19 (results: milestone item 13). For
the next image (every path in the menu's pt-BR labels):

1. **Configurações perigosas** (Configuração → focus on "Geral" → hold
   **Y** → confirm): Down from "Máximo do processador" reaches "Máximo
   dos gráficos", Down again wraps to "Nível do Log do Kernel"; on
   "Máximo do processador" Right raises (1368 MHz…"Máxima (1512 MHz)"),
   Left lowers.
2. **Cap back to 1296:** set "Máxima (1512 MHz)", leave with B, open the
   screen again, set 1296 MHz, leave: a PSX game (CTR) runs as before the
   overclock (no extra slowdowns).
3. **N64 resume:** start Mario Kart 64, race a little, Fn+Start; start
   it again: it resumes where you left (after ~1 s of the boot logo).
4. **Battery:** after the discharge run ends (the device powers off on
   its own), charge and power on; nothing else (the agent pulls the log).

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
    t2-sftp-jail, Wi-Fi toggle 3/3 + C2H, liveness C2H); written to p2
    2026-11-19 (read-back verified; boots to the menu, build id ok).
11. **M6 + M7 T3 (2026-11-19):** ok: pt-BR, screenshots, Wi-Fi,
    boot time, auto-assign by folder, regression. Found: (a) archive
    restore said "could not be marked as installed" (extract.sh writes
    /opt/muos/update on the read-only root); (b) one black blink at the
    end of the fade-in after a game and after a theme (bright.sh's
    forced fb0 unblank, hardware-findings); (c) CPU 1512 not found (the
    checklist gave a wrong path; the Danger screen is hold Y on
    "Geral"); (d) slot 2 still dead with the former original32 card;
    (e) N64 crashed at start (GLES2 build, hardware-findings); (f) BIOS
    Report only said "6 findings"; (g) Explore listed the empty system
    folders S91 seeds.
12. **T3 fixes — done to T2 except the image's suite:** (a) S91 binds
    p3 `MUOS/port/update`; (b) post-build skips the forced unblank
    (verified live: no FB:69 commit, backlight still set); (e) N64 core
    rebuilt for GLES3 (MK64 59.9, DK64 ~60 fps, 80–83 °C); (f) closing
    dialog + case renames; (g) `folderempty` 0 + one-shot migration.
    (d): the conclusive test (test128 in slot 2 under the port kernel)
    needs the M8 U-Boot (root by slot 1, decision 16); the user has only
    these two cards. Image `test128-m7t3-20261119` (`5e72cfa`, raw
    `9c60175f…`, p2 `c1f45838…`): trial root T2 passed (sweep 44 ok/7
    bounces, NES 59.96, sleep 2/2, t2-sdcard, t2-sftp-jail, Wi-Fi toggle
    3/3, N64 start, no FB:69 after the screen is up on game exit, p3
    update mark); written to p2.
13. **M7 T3-fix T3 (2026-11-19):** ok: fade without blink, MK64,
    archive restore, BIOS Report, empty folders, Fn+Start from N64. Found:
    (a) the Danger screen lost the focus below "Máximo do processador"
    and wrapped to the second row (upstream hides the Online Cores row,
    absent here, before grouping); (b) its Left/Right ran backwards
    (upstream lists the highest speed first); (c) switching 1512 → 1296
    kept 1512 until the next game (tweak.sh's bright.sh boost holds
    scaling_min at the old max, so the lower max write is refused);
    (d) N64 never resumed (mupen64plus-next rejects a state before its
    first frames); (e) DK64 drops frames in the intro and the first
    controllable scene (better at 1512), its camera resets (the user saw
    the same under ArkOS: emulator); a few CTR slowdowns at 1512, not
    seen at 1296. Promoted to recovery (only the Danger screen failed).
14. **Its fixes — done to T2 on the live root:** (a)+(b) frontend 0011
    (hide after grouping, as muxtweakgen; caps lowest first, "Highest"
    last): screenshots of the focus at both rows, the wrap and
    Right/Left; libmuxmod repinned. (c) `muos-governor` lowers
    scaling_min first: 1512 → 1296 through tweak.sh 3/3. (d) post-build
    appends `savestate_warmup_frames = "5"` to the mupen info: the
    user's MK64 (3 frames) and DK64 (5) autosaves restored.
Remaining for M7: DK64 frame drops (after the discharge run: perf
capture on the user's autosave, GLideN64 options vs the upstream
defaults now in use: FB emulation, copy color/depth to RDRAM, hybrid
filter, frame duping; per-folder/core overrides live in p3
`MUOS/pickles/coreopt/{directory,core}`), CTR at 1512 vs 1296 (thermal?), underrun bursts, idle
power (log running), a soak; then the image.

**Next milestone after M7:** M8 — public v1.0.
