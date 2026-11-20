# Roadmap: native AArch64 muOS for the R35S (Panel 0)

The release plan from the current state to a public v1.0, and the tracks
after it. Rewritten 2026-11-18. The current state is in
[STATUS.md](STATUS.md), finished milestones in
[milestones.md](milestones.md); the Phase 0–4 history (C1–C122) is in
[archive/phase4/roadmap.md](archive/phase4/roadmap.md).

## Where we are

Phases 0–4 (inventory, first native component, display/input, the menu on
the Debian bench, the standalone firmware base) are done. Phase 5 (own
card) has delivered M1–M7 (M7 T3 passed 2026-11-20): a flashable image that
boots straight to the muOS menu in English or Português (BR), with
display, controls, audio, Wi-Fi + SSH/SFTP (jailed), battery gauge,
sleep/resume, poweroff, time zone/NTP, about 20 libretro cores plus the
standalone Mupen64Plus (the N64 default) with saves and states, search,
activity, themes, and a public build variant without the developer's
identity. Everything
listed under "What works" in STATUS is T3-confirmed.

## Gap inventory (2026-11-18)

Against upstream muOS at the pinned commit (`upstream-revisions.txt`).
Every screen is compiled into `muxfrontend`; the gaps are what the
screens call.

| Area | Upstream | Port | Milestone |
|---|---|---|---|
| Archives | `mux/extract.sh`, `mux/backup.sh` (muxarchive, muxbackup, core installs) | missing; `unzip` present, no `zip` | done (M5) |
| Packages | `package/{theme,catalogue,config,logo}.sh` (muxpicker) | missing (logo not wanted) | done (M5) |
| Themes | MustardOS, C64, Dracula, GB Dark, Orange, mubiOS | MustardOS only | done (M5), plus theme download |
| Profiles | `system/profile.sh`, `share/profile` | missing | done (M5) |
| Storage | Secondary (`/mnt/sdcard`), USB; `mux/{migrate,sync,purge}.sh` | slot 2 never mounted; scripts missing | slot 2 done (M5; a real card does not initialise yet, M7 T3; swap test in M8); migration not ported (hidden) |
| Hotkeys | `share/hotkey/*` (screenshot, brightness, overlay…) | the port's own 2 files | screenshot done (M5) |
| Share data | `share/{lookup,info/name,media,task}` | missing | done (M5) |
| Screens without a backend | Bluetooth, HDMI, USB gadget, News | shown | hidden by flags or 0008/0009 (M5) |
| Cores | 125 systems, 236 core entries (`core.json`) | 6 cores | M6: 20 cores, 28 folders (N64 trial; ScummVM waits for p2 space) |
| Build from source | — | muxfrontend, libui, cores, kernel modules pinned as binaries | M6: release frontend + muxretro and all `build-cores.sh` cores from source; modules proven identical (`modules-check`) |
| Languages | 35 language files | upstream language pack + pt-BR overlay; CJK fonts out until p2 has room | done (M7); CJK in M8 |
| Performance/power | — | 1512 MHz opt-in, underruns measured, PipeWire self-heal; wake dip in libretro games | done (M7); wake hold in M8 |
| Public release | — | licences, GPL bundle, public image T3, docs | M9 |
| Applications | PortMaster, RetroArch, PPSSPP, ScummVM, standalone emulators | Mupen64Plus standalone (M7) | ScummVM, PPSSPP and the NDS emulator in M8 (decisions 17, 20); the rest after v1.0 |
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
prerequisite for M9), as a release build: the pinned frontend is a
`TEST_IMAGE=1` build (the "THIS IS A TEST IMAGE" watermark and LVGL's
FPS/CPU monitor; the flag changes LVGL structs, so all frontend parts
change together). Core assignments regenerated from one table.

### M7 — Polish: language, performance, power

Português (Brasil) complete (inventory of English strings with pt-BR
selected, the port's own strings into the language files, review of the
existing text) and all upstream language files. Wake: the ~0.7 s of slow
frames and Wi-Fi ~9 s after wake. Audio: underrun bursts, the WirePlumber
retry, the unexplained no-sound report. CPU 1512 MHz (the stock maximum)
as an opt-in, off by default. Idle power and DDR devfreq. Wi-Fi
warm-reboot H2C, dongle inserted during boot, and liveness: the 8821cu
can sit in a firmware error loop with an address and no traffic (M5
incident): detect it and rebind dwc2. A long soak (hours of play,
sleep cycles, a discharge to empty) and boot time.

### M8 — Card layout and the heavy systems (decisions 16, 17, 20)

With the user present: a clean U-Boot build, `root=` by the slot-1
device (decision 16), p2 grown to 1 GiB (decision 17), then the slot-2
swap test (our image on the former original32 in slot 1, test128 in
slot 2) to close the slot-2 problem. With the room: ScummVM and the CJK
fonts (decision 17), and the systems the user wants in v1.0 (decision
20, 2026-11-19), each at its best playable speed on the RK3326 (dArkOSen
as the reference): Dreamcast (Flycast), PSP (PPSSPP), NDS (DraStic is
closed source: check its licence for a public image, else melonDS or
DeSmuME), then Saturn (lowest priority: YabaSanshiro or Beetle). PSP and
NDS likely standalone (exceptions to decision 14 like N64), with the
launcher pattern of `muos-mupen64plus`. Standalone emulators follow
dArkOSen's choices, versions, settings and performance profiles (the
user, 2026-11-20; dArkOS RK3326 `es_systems.cfg`: PSP standalone PPSSPP,
NDS DraStic, Saturn standalone YabaSanshiro). Out of v1.0: Atari 5200,
Virtual Boy, Jaguar, Jaguar CD, CD-i. From the M7 T3: a quiet boot with a boot logo
instead of the scrolling kernel console (needed before any public
image), and a libretro game held on wake until the bring-up settles.

### M9 — Public v1.0

Licences closed (`pending-licenses.json`): Mali r13p0 (Hardkernel's
answer or a libmali with terms), the clean U-Boot (M8), Gambatte, the BT
firmware, the M8 emulators. The GPL source bundle on GitHub and third-party notices in the
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
- **Applications:** PortMaster, the other standalone emulators (Mupen64Plus
  is in since M7, the N64 default; PPSSPP and the NDS one come in M8).
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
