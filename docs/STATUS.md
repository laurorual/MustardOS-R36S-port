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

**Phase 5 (own-card firmware). M1–M4g done; M4g = recovery image since
2026-11-18 (night). M5 (daily-driver completeness, first milestone of the
release plan, roadmap.md) done to T2, p2 written 2026-11-18 (21:10);
**T3 pending** (T3 queue). Next: M6.**

## Next session — read first

- Device on main = **M5 p2** (`768942b1…`); `MUOS/trial/p2-previous.img`
  = M4g p2 + the M5 files installed live during development
  (`b121c62f…`); `MUOS/trial/rootfs.img` = M5 p2.
- Incident 2026-11-18 19:10–20:38: on the M5 trial root the RTL8821CU
  went into a firmware error loop (C2H/H2C errors, kernel warnings in
  the 8821cu module) during `t2-sftp.sh 16`; the worker kept "ready",
  so Wi-Fi stayed dead until the user rebooted (open problem "Wi-Fi
  zombie"). Logs: `build/logs/m5/incident/`. The repeat of the same T2
  set passed twice.

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, slot 2 empty: M4b image flashed 2026-11-14, then p2
  written in place (`write-p2`) for M4d, M4e.1, M4f, M4g and M5. The
  discharge logger is stopped; `user_init` = 0.
  Time zone set by the user (−03); volume 55 (the user's level).
  - Boot records: main = `Image-ea8ac0033c0e` (0001–0008) +
    `panel0-bc04b6f8e4d4.dtb`; previous = `Image-d61188f3a808` (0007).
  - p3: ROMs, Wi-Fi profile `Home.ini`, zone link, rumble verdict
    (`MUOS/port/rumble`: absent), the six seeded themes (M5).
- **original32 (stock dArkOSen):** the flasher station (slot 1, target
  in slot 2). Never write it.
- Device access, identity and card layout: procedures.md.

## Recovery image

The developer images are **private** (Wi-Fi PSK, SSH host key,
authorized_keys): never commit or share them. Flashing any image rewrites
the whole card, bootloader included; steps in procedures.md.

| Image | Content | State |
|---|---|---|
| `dist/firmware/test128-m5-20261118.img.zst` (raw `64e45d74…`, p2 `768942b1…`) + `public-m5-20261118` | M5: slot 2, archives, themes, profiles, screenshots, theme download, CA bundle | p2 on the card; T2 passed; T3 pending |
| **`dist/firmware/test128-m4g-20261118.img.zst`** (raw `a9d7cbc4…`, p2 `371b3f23…`) | **Recovery image since 2026-11-18 (night).** M4g (SFTP jail, overdrive bar) | T3 1, 3, 4 passed |
| `dist/firmware/test128-m4f-20261117.img.zst` (raw `159d4894…`, p2 `46a573a0…`) | M4f (kernel 0001–0008, USB watchdog, menu scripts) | T3 2–6 passed |
| `dist/firmware/test128-m4e1-20261117.img.zst` (raw `c122c7f4…`, p2 `d73646be…`) | M4e.1 | T3 passed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 firmware versions (`port/packaging/storage-retention.json`). The
public variant of M5 is kept for its T0 check only (never booted here).

## What works (T3-confirmed)

Display (60.0046 Hz), all controls, frontend and submenus; volume and
brightness with muxretro's in-game bar, hold-to-repeat and overdrive to
200 %; speaker audio; Wi-Fi (power save, profiles, scan, connect, replug,
sleep/wake ~9 s, on/off toggle, rows dimmed without a dongle, warm
reboot) + SSH/SFTP; time zone and NTP; prefs persistence; GB, NES, SNES,
GBA, MD and PSX with saves and states; per-system governors, 408 MHz menu
idle; autostart, menu reboot/shutdown, hard power-cut recovery; Power-key
sleep/resume, shutdown timer, charging fake sleep; Search, Activity
(sleep excluded), System details; battery %, icons and low-battery
poweroff from the RK817 gauge, % kept across a power-off; battery-empty
splash; headphone path switching; flashing with the host card reader; p3
auto-grow; `panic=10`.

## Open problems

- **Wi-Fi zombie (M5 incident):** the 8821cu firmware can enter a C2H/
  H2C error loop with the interface up and an address, passing no
  traffic; nothing detects it (worker "ready", no USB event). Seen once
  (trial root, heavy SFTP, third warm boot in 15 min). Fix in M7: a
  liveness check while ready (gateway ARP/ping, a few failures → the
  watchdog's dwc2 rebind, which restores Wi-Fi in ~17 s).
- **SFTP jail with a FileZilla saved site (M4g T3 2):** confirmed cause:
  a remembered path outside the jail (`ls /mnt/mmc/ROMS` in the jail →
  "not found" = `SSH_FX_NO_SUCH_FILE`). Fix on the PC side: clear the
  site's default remote directory. "Internal" is the read-only p2 view of
  `/opt/muos` (non-recursive bind, as upstream). The SFTP help text shows
  the login in English only (pinned pt-BR file is older; M7).
- **Slot 2 (M5):** T2 with loop devices only; real insertion, the udev
  rule, Explore listing SD2 content and a pulled card are T3. A card in
  slot 2 that is a **copy of this image** shares its PARTUUID: the
  kernel's `root=PARTUUID=4d554432-02` could pick it (U-Boot change,
  needs the user present); the port's own disk writers are safe
  (`muos-boot-disk`). Storage migration (muxstorage) and card
  preparation (muxspace) are hidden (frontend 0008).
- **Frontend is a TEST_IMAGE build:** "THIS IS A TEST IMAGE" banner and
  the FPS/CPU counter (M6, release build from source).
- **Screenshots:** menu only (X+L2+R2); muxretro has no capture.
- **Pinned config lacks ~270 upstream keys** (the frontend's built-in
  defaults apply); M5 added the theme download, theme filter and hotkey
  ones. Review the rest with the M6 frontend rebuild.
- **Battery:** (d) the BSP smoothing uses `abs(delta_cap)`.
- **USB (dwc2 misses port events):** an unplug and a plug (1 in 4) left
  no kernel event although HPRT0 showed the change. `muos-usb-watchdog`
  (M4f) rebinds dwc2 after 3 disagreeing reads (not yet triggered by a
  real replug).
- **Upstream gaps:** see the gap inventory in roadmap.md.
- **Translation (pt-BR, M7):** parts stay English with Português (Brasil)
  selected; the existing pt-BR text needs a review; our own strings
  (Wi-Fi row help, Rumble "Unavailable") are not in language files.
- **Wi-Fi dongle (RTL8821CU):** the warm-reboot H2C case (1 in 7 since
  M4c); the dongle resets itself after ~40 s; Wi-Fi at ~75 s instead of
  ~115 s. No software power cycle. Inserting the dongle during boot is
  unqualified.
- **Wake:** Wi-Fi returns ~9 s after wake with ~0.7 s of slow frames.
- **Power:** menu idle ~420 mA; no controllable LEDs.
- **Audio:** one unexplained no-sound report (M3d); WirePlumber "no
  profile" start failure retried; 3–8 underrun bursts per game; 200 %
  overdrive distorts (as upstream).
- **Headphones (hardware, deprioritized):** jack contact problem.
- **DDR devfreq** isn't synced to the display; **U-Boot log** goes to
  serial/LCD only.
- **Pinned, not rebuilt (M6):** muxfrontend, libui, the cores, the
  kernel modules, the tuned `/opt/muos` config; idbloader and trust
  (rkbin files).
- **Trial root:** p3 can't be unmounted at shutdown while it runs; any
  reboot returns to main (one-shot marker).
- **Menu:** "Direct Link" and "Proxy Settings" not exercised; static
  addresses untested; the Rumble row's "present" case unverified.
- **Licences (M8):** Mali r13p0 (Hardkernel: no answer yet), the dirty
  U-Boot, Gambatte and BT firmware are private-only.

## Decisions

Answered by the user 2026-11-14: 1 name "muOS for R36S/R35S (unofficial
port)"; 2 Mali (a), request sent 2026-11-14, no answer as of 2026-11-18;
3 boot payloads rkbin (done, M4d); 4 GPL source on GitHub; 5 public root
password `root`; 6 SFTP jail before the final public build (done, M4g);
7 unported web services hidden; 8 public p3 empty.
Answered 2026-11-17: 9 shellcheck download allowed (done); 10 the R35S
has no rumble motor; keep the option, detect the motor, show
"Unavailable" without one (done); 11 no public-image test yet.

## Decisions for the user

Work continues without them; the recommendation applies until answered.

12. **Upstream themes in the public image** (C64, Dracula, GB Dark,
    Orange, mubiOS; MustardOS's assets). Recommendation: ship them in the
    developer image now; in the public image only after the MustardOS
    team answers (same question as the name, M8).
13. **CPU 1512 MHz in v1.0** (the stock dArkOSen maximum; the port caps
    at 1296). Recommendation: yes, as an opt-in, off by default (M7).
14. **Bluetooth, PortMaster, standalone emulators** after v1.0.
    Recommendation: yes, after v1.0.
15. **A spare microSD for slot-2 tests** (FAT32 or exFAT, a few ROMs;
    never a copy of this image). Recommendation: optional; without it
    slot 2 ships T2-tested only.
16. **The `root=` of the kernel command line** (U-Boot env): PARTUUID
    today, ambiguous with a cloned card in slot 2. Recommendation: in M8
    (with the clean U-Boot build, user present) boot by the slot-1
    device; until then document "no image copies in slot 2".

## T3 queue

M5 checklist (p2 written; no flash). Includes M4g item 2.

1. **FileZilla:** in the saved site clear "Default remote directory"
   (Advanced tab) or make a new site: SFTP, the console's IP, port 2022,
   `muos`/`muos`. Expected: Primary Storage, Internal…; copy a ROM into
   `Primary Storage/ROMS/<system>`: it shows in Explore. Web Services →
   Secure File Transfer, help button: port 2022, `muos`/`muos` (English).
2. **Launcher and Explore:** the tiles have icons and a mustard highlight
   (upstream's full MustardOS theme); Explore lists systems by name
   (Nintendo Entertainment System, Nintendo Game Boy, Sony PlayStation).
   Anything broken or odd?
3. **Theme:** Configuration → Personalização → theme list (C64, Dracula,
   GB Dark, mubiOS, MustardOS, Orange): pick one, the menu changes; pick
   MustardOS again.
4. **Theme download:** in the theme list, Theme Download → X (refresh):
   the community list with previews; A on a small theme installs it.
5. **Backup:** Configuration → Backup: back up "Capturas de Tela" (or
   Saves) to SD1; Aplicativos → Archive Manager lists the `.muxbak`;
   restore it.
6. **Screenshot:** in the menu press X+L2+R2: a file appears in
   `MUOS/screenshot` (see it over SFTP).
7. **Profiles:** Configuration → Profiles → Accessibility → Large Print:
   bigger text; then "Restore Previous Profile" undoes it.
8. **Tasks:** Aplicativos → Task Toolkit (if listed) → Diagnostics →
   Battery Report: a report is written.
9. **Clock:** Date and Time: change the minute, reboot: the time is right.
10. **Slot 2 (optional; a spare FAT32/exFAT card with ROMS/<system>/…,
    never a copy of this image):** insert it with the console on;
    Explore shows its ROMs; SFTP shows Secondary Storage; remove it:
    nothing breaks.
11. **Regression:** a game with volume keys, sleep/wake in the game,
    Wi-Fi on/off. If Wi-Fi ever stays dead with the icon on, tell me
    the time.

## Current milestone: M6 — systems, cores, build from source

M5 is handed over (results in milestones.md). M6 plan (roadmap.md):
1. Frontend from source as a release build (muxfrontend, libui,
   libmuxcom, libmuxmod; `TEST_IMAGE=0`): no watermark/FPS counter;
   review the ~270 missing config keys against the built-in defaults.
2. Cores, each with a fps verdict and a governor: Atari 2600/7800/Lynx,
   PC Engine/CD, Neo Geo Pocket, WonderSwan, MSX/Coleco/SG-1000, Sega CD,
   FBNeo + MAME 2003-Plus (arcade, Neo Geo), DOSBox-Pure, ScummVM,
   Pokémon mini; N64 trial (ship only if playable).
3. All cores and the kernel modules rebuilt from pinned source; one core
   table generating core-assign and the coredb governors.
4. BIOS checks (folder, names, hashes) for the systems that need them.
5. Image, trial T2 (fps per system, the standard set), `write-p2`.
Expected T3: one game per new system, BIOS-dependent systems, the
menu without the watermark.

**Next milestone after M6:** M7 — polish: language, performance, power.
