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
2026-11-18 (night). Current milestone: M5 (daily-driver completeness),
first of the release plan to v1.0 (M5–M8, roadmap.md).**

## Next session — read first

- Device on main = **M4g p2** (`371b3f23…`); `MUOS/trial/p2-previous.img`
  = M4f p2 + the M4g frontend files (`38b383fa…`). Web SSH and SFTP on
  (the user's setting).
- The idle discharge logger (`MUOS/init`) still runs; `t2-discharge.sh
  report` is M5 item 2 (its `report` restores a saved volume: check first).

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1, slot 2 empty: M4b image flashed 2026-11-14, then p2
  written in place (`write-p2`) for M4d, M4e.1, M4f and M4g. p3
  `MUOS/trial/rootfs.img` = M4g p2.
  Time zone set by the user (−03); volume 55 (the user's level).
  - Boot records: main = `Image-ea8ac0033c0e` (0001–0008) +
    `panel0-bc04b6f8e4d4.dtb`; previous = `Image-d61188f3a808` (0007).
  - p3: ROMs, Wi-Fi profile `Home.ini`, zone link, rumble verdict
    (`MUOS/port/rumble`: absent), discharge logger in `MUOS/init`.
- **original32 (stock dArkOSen):** the flasher station (slot 1, target
  in slot 2). Never write it.
- Device access, identity and card layout: procedures.md.

## Recovery image

The developer images are **private** (Wi-Fi PSK, SSH host key,
authorized_keys): never commit or share them. Flashing any image rewrites
the whole card, bootloader included; steps in procedures.md.

| Image | Content | State |
|---|---|---|
| **`dist/firmware/test128-m4g-20261118.img.zst`** (raw `a9d7cbc4…`, p2 `371b3f23…`) | **Recovery image since 2026-11-18 (night).** M4g (SFTP jail, overdrive bar) | p2 on the card; T3 1, 3, 4 passed |
| `dist/firmware/test128-m4f-20261117.img.zst` (raw `159d4894…`, p2 `46a573a0…`) | M4f (kernel 0001–0008, USB watchdog, menu scripts) | T3 2–6 passed |
| `dist/firmware/test128-m4e1-20261117.img.zst` (raw `c122c7f4…`, p2 `d73646be…`) | M4e.1 | T3 passed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

4/5 firmware versions (`port/packaging/storage-retention.json`). No
public image is kept (public-m4d retired with M4d; the next one is built
in M5/M8).

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

- **SFTP jail with a FileZilla saved site (M4g T3 2):** `SSH_FX_NO_SUCH_FILE`
  at connect; OpenSSH lists the jail root (Catalogue, Collections,
  History, Internal, Primary Storage). Likely the site's remote directory
  from the old root SFTP. "Internal" is the read-only p2 view of
  `/opt/muos` (non-recursive bind, as upstream). M5 item 1.
- **Battery:** (d) the BSP smoothing uses `abs(delta_cap)`.
- **USB (dwc2 misses port events):** an unplug and a plug (1 in 4) left
  no kernel event although HPRT0 showed the change. `muos-usb-watchdog`
  (M4f) rebinds dwc2 after 3 disagreeing reads (not yet triggered by a
  real replug).
- **Upstream gaps:** see the gap inventory in roadmap.md (M5: archives,
  packages, themes, profiles, slot 2, hotkeys, share data).
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
15. **A spare microSD for slot-2 tests** (FAT32 or exFAT, a few ROMs).
    Recommendation: optional; without it slot 2 ships T2-tested only.

## T3 queue

Items waiting for the user's hands or eyes, newest milestone last. Each
item is folded into the milestone's checklist at hand-over.

- (M4g 2) FileZilla: SFTP retry with the saved site's remote directory
  cleared (or a new site), then the M5 checklist item.

## Current milestone: M5 — daily-driver completeness

Goal: every menu screen either works or is hidden. Plan (2026-11-18):

1. SFTP follow-up: reproduce the FileZilla saved-site case; the Web
   Services screen shows the SFTP login (user, password, port).
2. `t2-discharge.sh report`, then stop the idle logger.
3. Archives: `zip`, upstream `mux/extract.sh` + `mux/backup.sh`
   (muxarchive, muxbackup); T2 round trip.
4. Themes: upstream `package/*.sh` (muxpicker) and the upstream themes;
   T2 switch + framebuffer screenshot.
5. Profiles: `system/profile.sh` + `share/profile`.
6. Secondary storage (slot 2): mount at `/mnt/sdcard`, hotplug, muxstorage
   migrate/sync/purge, the SFTP jail's Secondary Storage.
7. Hotkeys and screenshots (upstream hotkey files that apply).
8. Share data: lookup/name tables, sounds, fonts, a Task Toolkit subset.
9. Clock screens: muxrtc and muxtimezone T2.
10. Screen sweep: a T2 script opening every screen; screens without a
    backend (Bluetooth, HDMI, News, USB gadget) hidden.
11. Image, trial root T2, `write-p2`, docs, report.

Tests: T0 shellcheck/contract/public check; T1 ELF deps; T2 per item +
the standard set (sftp-jail, sftp, menu-cycle, sleep-cycle, wifi).
Expected T3: FileZilla, Web Services login, backup/restore, archive
install, theme switch, profile, screenshot, time zone/RTC, slot-2 card
(optional), regression.

**Next milestone:** M6 — systems, cores, build from source (roadmap.md).
