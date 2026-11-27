# Roadmap: native AArch64 muOS for the R35S (Panel 0)

The release plan from the current state to a public v1.0, and the tracks
after it. Rewritten 2026-11-18. The current state is in
[STATUS.md](STATUS.md), finished milestones in
[milestones.md](milestones.md); the Phase 0–4 history (C1–C122) is in
[archive/phase4/roadmap.md](archive/phase4/roadmap.md).

## Where we are

Phases 0–4 (inventory, first native component, display/input, the menu on
the Debian bench, the standalone firmware base) are done. Phase 5 (own
card) has delivered M1–M10 (v1.0.0 and v1.1.0 published 2026-11-26): a flashable image that
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
| Cores | 125 systems, 236 core entries (`core.json`) | 6 cores | M6: 20 cores, 28 folders; M8: the heavy systems, ScummVM (core + standalone) |
| Build from source | — | muxfrontend, libui, cores, kernel modules pinned as binaries | M6: release frontend + muxretro and all `build-cores.sh` cores from source; modules proven identical (`modules-check`) |
| Languages | 35 language files | upstream language pack + pt-BR overlay, CJK with their fonts (M8) | done (M7, CJK M8) |
| Performance/power | — | 1512 MHz opt-in, underruns measured, PipeWire self-heal; wake dip in libretro games | done (M7); wake hold in M8 |
| Public release | — | licences, GPL bundle, repository, public image T3, docs | M9 |
| Applications | PortMaster, RetroArch, PPSSPP, ScummVM, standalone emulators | Mupen64Plus (M7); PPSSPP, DraStic, YabaSanshiro, Flycast, ScummVM core + standalone (M8) | the rest after v1.0 |
| Bluetooth | `bt_*.sh`, bluez | none (no bluez; dongle only) | after v1.0 |
| Web services | ttyd, Syncthing, mDNS, landing page | hidden (decision 7) | after v1.0 |

Not wanted: `system/prepare.sh` and `logo.sh` (one card, p1 boot),
`init/async/S08sunrise.sh` (no LEDs to drive).

## Release plan to v1.0

Each milestone is large (several sessions, 6–15 items) and ends with one
consolidated T3 checklist; the next one starts while the user tests.

Done (details in [milestones.md](milestones.md) and
[archive/milestones-m1-m7.md](archive/milestones-m1-m7.md)): M5
daily-driver completeness (every menu screen works or is hidden), M6
systems, cores and the build from source, M7 language, performance and
power, M8 card layout (clean U-Boot, `root=` by slot, 1 GiB p2), the
heavy systems (DC, PSP, NDS, Saturn), ScummVM, the CJK fonts and the boot
logo.

### M9 — Public v1.0 (licences and publication first)

From 2026-11-25 (decision 37) every session first advances licences and
publication, then polish. Decisions 33–38 in [decisions.md](decisions.md).

Licences and publication (priority):

1. [LICENSING.md](LICENSING.md) as the single source: one row per
   distributed component (version/sha, licence, state "open",
   "permitted", "community practice" or "removed") and the request log;
   `pending-licenses.json` and `THIRD-PARTY.txt` agree with it. Gambatte
   and FCEUmm built by `build-cores.sh` at pinned commits; the Bluetooth
   firmware out of the public image; how dArkOS/ArkOS ship libmali and
   DraStic recorded as the community-practice reference.
2. MustardOS compliance (decision 34): the name "MustardOS for
   R36S/R35S (unofficial port)" per muos.dev/press in the README, release
   notes, image, boot logo and Information → Device Details; the "not supported by the
   MustardOS team, support on the port's GitHub" notice in the README,
   the release notes and in the system itself (EN and pt-BR); credits and
   the CC BY-NC 4.0 licence of the assets used.
3. The GPL source bundle (`make-source-bundle.sh`) covering everything
   the public image contains, attached to every release.
4. The repository (decision 33): history scan for secrets, blobs, ROMs
   and third-party binaries; README (EN with pt-BR), LICENSE, NOTICE; the
   push blockers and the final command for the user (the agent never
   publishes).
5. Plan B (decision 36): `prepare-image.sh` ready and T1-tested against a
   public image without libmali and DraStic.
6. rc1: the complete public image (decision 35), `check-public-image.sh`,
   T3 on a blank card with the user present → v1.0.

Polish (after each licence block): install guide (EN and pt-BR),
changelog, known issues, battery % after sleeping on the charger, the
open T3 rounds, and whatever else matters most for v1.0. Done in M9 so
far: the M8g T3 fixes, the ScummVM standalone default, CJK menu overlays,
the undervolt opt-in with manual CPU/GPU values, THIRD-PARTY.txt, the
update path (`muos-update`, Task Toolkit "Install Firmware Update",
GitHub auto-update in public images).

Before v1.0.0 (found 2026-11-25, done 2026-11-26 with `muos-boot-sync`): the update path carried only p2, so
a kernel/DTB fix (like patch 0011) never reaches an updated card. Plan:
the p2 image carries the boot files (`Image`, DTBs, `dtb-variants.txt`)
and, after the update's first good boot, installs changed ones with the
existing trial path (`muos-boot-slot install-trial`, reboot, promote
after the menu is up; a bad kernel falls back to main). T2 on the bench
with an update from rc2 to the next build.

Scope of v1.0: R35S/R36S **Panel 0** only (DT model R36S-V12 2023-08-18
Panel 0), the DTB choice documented like dArkOSen's. No claims for other
panels or clones.

## After v1.0 (tracks)

- **Mainline/Panfrost (only if community practice stops being
  viable,** e.g. Arm or Hardkernel object to the bundled libmali):
  ROCKNIX's 6.x kernel as the reference; removes the Mali blob and the
  vendor TF-A; full re-qualification (see "Kernel base").
- **Other R36S variants and Wi-Fi dongles (decisions 43–44): M10**
  (done, v1.1.0). Wave 1: 22 dArkOSen models on the port's board at 640x480,
  switched by Linux (`muos-model`, a one-shot trial like the undervolt
  rows) instead of a U-Boot rule, so the update path delivers it; every
  USB Wi-Fi driver the kernel has. Later waves: the rg351v clones and R50S
  (other input device names: a frontend input profile), the Y3506 boards
  (rg351p), the 720/1024 panels (a frontend resolution port).
- **PortMaster: M11** and **Pico-8: M12**: done, v1.1.1 (2026-11-27;
  milestones.md).
- **First Boot and the games card format (decision 50): M13.** the
  upstream first-boot sequence (Date and Time, Language, Profiles, Input
  Tester, Shutdown, Install; muxinstall and the prepare/storage scripts
  of the pin) with Install formatting p3 as exFAT (default), FAT32 or
  EXT4, so Windows can copy ROMs.
- **MustardOS next release (decision 45): M14.** port the frontend/internal
  pin to the next official release after 2606.0 Andromeda (main on
  2026-11-25: Pickles/Wasabi content, Chutney reader, muaudio daemon,
  performance levels instead of governors, JSON theme layouts and main
  menu styles, lower idle/sleep power); rebase the port's patches, the
  theme format update comes with it.
- **Overclock beyond stock** (CPU above 1512 MHz, GPU above 520 MHz) as an
  explicit, labelled option.
- **Bluetooth** through a combo dongle (bluez, `bt_*.sh`).
- **Applications:** PortMaster (M11), the other standalone emulators (Mupen64Plus
  is in since M7; PPSSPP, DraStic, Flycast, YabaSanshiro and ScummVM since M8).
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
- **Licences:** [LICENSING.md](LICENSING.md) is the single source (M9);
  `port/packaging/pending-licenses.json` is its machine-readable mirror.

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
be resolved, v1.0 still ships it as community practice (decision 35);
the mainline/Panfrost track replaces it only if that stops being viable.
