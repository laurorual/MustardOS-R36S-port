# Roadmap: native AArch64 muOS for the R35S (Panel 0)

The release plan from the current state to a public v1.0, and the tracks
after it. Rewritten 2026-11-18. The current state is in
[STATUS.md](STATUS.md), finished milestones in
[milestones.md](milestones.md); the Phase 0–4 history (C1–C122) is in
[archive/phase4/roadmap.md](archive/phase4/roadmap.md).

## Where we are

Phases 0–4 (inventory, first native component, display/input, the menu on
the Debian bench, the standalone firmware base) are done. Phase 5 (own
card) has delivered M1–M4g: a flashable image that boots straight to the
muOS menu, with display, controls, audio, Wi-Fi + SSH/SFTP (jailed),
battery gauge, sleep/resume, poweroff, time zone/NTP, six cores (NES, GB/GBC,
GBA, SNES, MD/SMS/GG/32X, PSX) with saves and states, search, activity,
and a public build variant without the developer's identity. Everything
listed under "What works" in STATUS is T3-confirmed.

## Gap inventory (2026-11-18)

Against upstream muOS at the pinned commit (`upstream-revisions.txt`).
Every screen is compiled into `muxfrontend`; the gaps are what the
screens call.

| Area | Upstream | Port | Milestone |
|---|---|---|---|
| Archives | `mux/extract.sh`, `mux/backup.sh` (muxarchive, muxbackup, core installs) | missing; `unzip` present, no `zip` | M5 |
| Packages | `package/{theme,catalogue,config,logo}.sh` (muxpicker) | missing | M5 |
| Themes | MustardOS, C64, Dracula, GB Dark, Orange, mubiOS | MustardOS only | M5 |
| Profiles | `system/profile.sh`, `share/profile` | missing | M5 |
| Storage | Secondary (`/mnt/sdcard`), USB; `mux/{migrate,sync,purge}.sh` | slot 2 never mounted; scripts missing | M5 |
| Hotkeys | `share/hotkey/*` (screenshot, brightness, overlay…) | the port's own 2 files | M5 |
| Share data | `share/{lookup,info/name,media,task}` | missing | M5 |
| Screens without a backend | Bluetooth, HDMI, USB gadget, News | shown | M5 (hide) |
| Cores | 125 systems, 236 core entries (`core.json`) | 6 cores | M6 |
| Build from source | — | muxfrontend, libui, cores, kernel modules pinned as binaries | M6 |
| Languages | 35 language files | English + Português (BR) (incomplete) | M7 |
| Performance/power | — | wake dip, audio underruns, CPU capped at 1296 MHz | M7 |
| Public release | — | licences, GPL bundle, public image T3, docs | M8 |
| Applications | PortMaster, RetroArch, PPSSPP, ScummVM, standalone emulators | none | after v1.0 |
| Bluetooth | `bt_*.sh`, bluez | none (no bluez; dongle only) | after v1.0 |
| Web services | ttyd, Syncthing, mDNS, landing page | hidden (decision 7) | after v1.0 |

Not wanted: `system/prepare.sh` and `logo.sh` (one card, p1 boot),
`init/async/S08sunrise.sh` (no LEDs to drive).

## Release plan to v1.0

Each milestone is large (several sessions, 6–15 items) and ends with one
consolidated T3 checklist; the next one starts while the user tests.

### M5 — Daily-driver completeness (menu side)

Every menu screen either works or is hidden. M4g follow-ups (SFTP with
saved FileZilla sites, the SFTP login on the Web Services screen, the
discharge report); zip + extract/backup (muxarchive, muxbackup); package
scripts and the upstream themes (muxpicker, theme switching); profiles;
secondary storage in slot 2 (mount, hotplug, muxstorage scripts, SFTP
jail); hotkeys and screenshots; share data (lookup/name tables, sounds,
Task Toolkit subset); RTC and time zone screens; an automated screen
sweep; screens without a backend hidden.

### M6 — Systems, cores, build from source

The systems the A35/Mali-G31 runs well, each with a fps verdict and a
governor: Atari 2600/7800/Lynx, PC Engine/CD, Neo Geo Pocket, WonderSwan,
MSX/ColecoVision/SG-1000, Sega CD, arcade and Neo Geo (FBNeo,
MAME 2003-Plus), DOS (DOSBox-Pure), ScummVM, Pokémon mini, and an N64
trial (ship only if playable). BIOS folder checks. Rebuild muxfrontend,
libui, libmuxmod, all cores and the kernel modules from pinned source,
so every shipped binary has its corresponding source (the GPL
prerequisite for M8). Core assignments regenerated from one table.

### M7 — Polish: language, performance, power

Português (Brasil) complete (inventory of English strings with pt-BR
selected, the port's own strings into the language files, review of the
existing text) and all upstream language files. Wake: the ~0.7 s of slow
frames and Wi-Fi ~9 s after wake. Audio: underrun bursts, the WirePlumber
retry, the unexplained no-sound report. CPU 1512 MHz (the stock maximum)
as an opt-in, off by default. Idle power and DDR devfreq. Wi-Fi
warm-reboot H2C, dongle inserted during boot. A long soak (hours of play,
sleep cycles, a discharge to empty) and boot time.

### M8 — Public v1.0

Licences closed (`pending-licenses.json`): Mali r13p0 (Hardkernel's
answer or a libmali with terms), a clean U-Boot build, Gambatte, the BT
firmware. The GPL source bundle on GitHub and third-party notices in the
image. The public variant: T2 checks, first-boot flow (Wi-Fi from the
menu, SSH/SFTP toggles, empty p3 populated). The MustardOS team's answer on
the name and theme assets. Install guide (English and pt-BR), changelog,
known issues, SHA256. The update path for v1.x (reflash keeping p3, or a
muxarchive update package). rc1 → T3 on a blank card with the user present
→ v1.0.

Scope of v1.0: R35S/R36S **Panel 0** only (DT model R36S-V12 2023-08-18
Panel 0), the DTB choice documented like dArkOSen's. No claims for other
panels or clones.

## After v1.0 (tracks)

- **Mainline/Panfrost:** ROCKNIX's 6.x kernel as the reference; removes
  the Mali blob and the vendor TF-A; full re-qualification (see "Kernel
  base").
- **Other panels and R36S revisions:** only with evidence and a physical
  test; DTB chosen like dArkOSen, never autodetected from the SoC name.
- **Overclock beyond stock** (CPU above 1512 MHz, GPU above 520 MHz) as an
  explicit, labelled option.
- **Bluetooth** through a combo dongle (bluez, `bt_*.sh`).
- **Applications:** PortMaster, standalone emulators (PPSSPP, Mupen64Plus).
- **Web services:** ttyd, Syncthing, mDNS, the landing page.
- **Automated builds and update packages.**

## Approach

- **What we keep from muOS:** the frontend, muinput, and the config/service
  contracts.
- **Device profile:** our own R35S profile (`rk-r35s-p0`) with small patches
  under `port/`. G350 and Pixel 2 profiles are references only, never
  drop-in implementations.
- **Reference repos:** use dArkOSen to learn how the hardware already works,
  and ROCKNIX to compare DTS, drivers and panels.
- **Input:** use the portable evdev backend, not userspace GPIO/ADC.
- **Kernel base:** the dArkOSen/rk351 4.4 BSP. ROCKNIX is the fallback if
  provenance, licences or stability can't be closed.
  - Never copy the BSP DTB into mainline.
  - A ROCKNIX panel overlay is a migration option, not a universal DTB.
- **Image format:** ext4 root plus FAT boot, built with Buildroot
  2025.02.19. The stock Btrfs card is data to preserve, not a conversion
  target.
- **Sysroots:** keep two, one for Debian bench tests and one for the
  standalone firmware. An approval in one does not carry over to the other
  without loader, symbol, kernel and GPU proof.
- **Build hygiene:** builds happen only in `build/`, never in `refs/`. Use a
  rootless, pinned container.
- **Licences:** private use only during development. Track pending items in
  `port/packaging/pending-licenses.json` and resolve them in M8.

## Kernel base, reassessed 2026-11-12

| Option | For | Against |
|---|---|---|
| **rk351 4.4.189 BSP (current)** | Everything qualified (sleep, audio, battery, Wi-Fi, panel); reproducible build | Mali r13p0 blob with unclear terms; vendor boot payloads; ext4 feature limits; no uclamp; DWC2 must be unbound around suspend; DDR devfreq not synced to the VOP (no `vop-bw-dmc-freq`) |
| **dArkOSen 5.10 (announced, not released)** | Newer drivers, uclamp, ext4, likely better USB suspend | Still a Mali blob (newer g-series) and vendor boot chain; no RK3326 5.10 source published yet (christianhaitian/linux has only 4.4 rg351 branches; dArkOS's 5.10.226 is RK3566-only); dArkOSen itself warns it "may break clone devices" |
| **ROCKNIX mainline (6.x)** | Panfrost + Mesa removes the Mali licence blocker; open TF-A for PX30; rtw88 8821cu in-tree; maintained R36S panel mode | Full re-qualification (rk817 audio/charger, joypad, sleep, panel, battery); DDR init blob stays; months of work |

**Decision:** keep 4.4 for v1.0. Don't chase 5.10: it keeps both licence
problems and adds risk, and its source isn't public. Re-check when
dArkOSen publishes the RK3326 5.10 source and DTBs; the trial kernel +
trial root path can test it without a reflash. If the Mali licence can't
be resolved in M8, the public release waits for the mainline/Panfrost
track, not for 5.10.
