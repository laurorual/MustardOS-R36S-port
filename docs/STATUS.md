# Project status

Current state only; update at the end of every milestone. Release plan:
[roadmap.md](roadmap.md); answered decisions: [decisions.md](decisions.md);
licences: [LICENSING.md](LICENSING.md); how-tos: [procedures.md](procedures.md);
finished milestones: [milestones.md](milestones.md) (M1–M7 in
[archive/](archive/milestones-m1-m7.md)); hardware facts:
[hardware-findings.md](hardware-findings.md); host storage:
[storage.md](storage.md).

## Current phase

Phase 5 (own-card firmware). M1–M10 done: **v1.1.0 published 2026-11-26**
(GitHub release, latest; v1.0.0 before it; m10a, the v1.1.0 developer
twin, is the recovery image). **Current: M11 — PortMaster + M12 — PICO-8**
(2026-11-26, one release, decision 48): both done to T2; the first
v1.1.1 T3 passed with small findings (A/B, cursor, no bar in ports),
fixed and T2-checked in m12c; **v1.1.1 rebuilt**. The user repeats the
T3 on test128, then on original32, then publishes v1.1.1. Next: M13,
the MustardOS next release.

## Device and bench

- **Bench (2026-11-26):** test128 in slot 1, **p2 = m12d** (written
  with `write-p2` after `t2-levelbar.sh` + `t2-pico8.sh` +
  `t2-portmaster.sh` PASS; m12c, m12b before it). PortMaster reinstalled
  on p3 2026-11-26 (a trial reboot during its source update corrupted
  `config/020_portmaster.source.json`); the user's Doukutsu-rs kept. p3 test
  content: PortMaster with sdlsopwith, turbotabletennis, 2048; ROMS/PICO-8
  `ld45.p8`, `cartparsetest.p8.png`; the user's official PICO-8 0.2.7 in
  `MUOS/bios/pico8` (private: never in an image) and the Splore app. Before:
  the update path m9k → m10a (boot records: main = `Image-494d1c3d5ebd` + the
  undervolt DTB `panel0-84611ef0394d.dtb`, previous = the same kernel +
  the stock DTB `panel0-c97151d0ec1a.dtb` since the model T2). p1 has
  the 22 model DTBs, `models.txt` and the selectors. original32 holds
  the public v1.1.0 (updated from v1.0.0 in the T3; `model.txt` =
  `default`; password SSH on port 22, root/`root`, used read-only for
  the RTL8822BU dongle info) with a TP-Link RTL8822BU dongle (2357:0115).
- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0), test128
  in slot 1 (mmcblk0 by DT alias), slot 2 empty. `user_init` = 0, time
  zone −03. Access, identity and card layout: procedures.md.
- **p2 = m10a** (2026-11-26, through the update path; the previous p2,
  m9k, in `MUOS/trial/p2-previous.img`). p1 `bootlogo.bmp` = the
  press-kit logo (`d6e6d189…`).
- Charge log of 2026-11-25 stopped (`build/logs/discharge/discharge.csv`).
- **Boot records:** see "Bench". p1 has all 16 undervolt DTBs, the 21
  distinct model DTBs and `dtb-variants.txt` (22 `m-` keys).
- **p3:** ROMs (also in `port/roms/`; systems listed in milestones M8),
  Wi-Fi profile `Home.ini`, the six themes, BIOS (PSX, DC, Saturn, Sega
  CD, PCE CD). T2 data in `MUOS/t2` (God of War states `state-v120` /
  `state-v112`, DC fight states `dc-fight` / `dc-fight-2022`; `ppsspp-2021`,
  `drastic`, `m1-backup`, `emu` are removable), CTR state in
  `MUOS/port/t2/ctr-race`, ScummVM test game (Monkey Island).
- **original32 (stock dArkOSen):** the flasher station only. Never write it.
- `refs/darkosen` at `28f5427`; its `.git` is 361 MB (a fresh blobless
  clone would free ~340 MB: the user's call, refs/ is read-only).

## Recovery image

Developer images are **private** (Wi-Fi PSK, SSH host key,
authorized_keys): never commit or share them. Flashing rewrites the whole
card, bootloader included (procedures.md).

| Image | Content | State |
|---|---|---|
| **`dist/firmware/test128-m10a-20261126.img.zst`** (raw `cc85290c…`, p2 `77ff5a87…`) + `MustardOS-R36S-port-v1.1.0.*` (public, raw `8378de0c…`, p2 `8bedd242…`, 32 checks) | M10: Wi-Fi dongles, model DTBs + switch | m10a on the bench (update path from m9k); v1.1.0 T3 ok and **published 2026-11-26**; **m10a recovery since 2026-11-26** |
| `dist/firmware/test128-m12d.img.zst` (raw `efb340ec…`, p2 `bd514532…`) + `MustardOS-R36S-port-v1.1.1.*` (public, raw `53fe5b14…`, p2 `8d9920cc…`, 38 checks; source zips in `build/release`) | M11 + M12 + the v1.1.1 T3 fixes + one bar | m12d on the bench p2; v1.1.1 T3 round 3 pending, then publish |
| (v1.0.0 public, m9k) | on GitHub (release); local files and m9k retired 2026-11-26 (m10a recovery) | T3 ok 2026-11-26 |
| (v1.0.0-rc2 public) | on GitHub (pre-release); local files deleted 2026-11-26 | T3 ok 2026-11-25 |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2 | **base of every image build**; never retire |

3/5 versions in `storage-retention.json` (M2, m10a+v1.1.0,
m12d+v1.1.1; m12c, m12b and m9k+v1.0.0 and earlier retired 2026-11-26). The v1.0.0 and v1.1.0 source zips in
`build/release` (2.6 GB each, also on GitHub) are outside retention.

## What works (T3-confirmed)

Display, controls, frontend and submenus; volume/brightness with the
in-game bar; speaker audio and headphone switching; Wi-Fi (profiles,
scan, sleep/wake, toggle, replug) + SSH/SFTP (jailed); time zone/NTP;
battery %, icons, low-battery poweroff, empty splash; sleep/resume,
shutdown timer, charging fake sleep; themes, profiles, Task Toolkit,
search, activity, screenshots (menu); GB, NES, SNES, GBA, MD, PSX, 32X,
2600, 7800, GG, Lynx, SMS, PCE, Sega CD, PCE CD; N64 (standalone Rice);
PSP (v1.12.3, frameskip 1), NDS (advanced DraStic), DC (Flycast 2022),
Saturn (standalone YabaSanshiro, slow); ScummVM core + standalone with
the virtual keyboard; pt-BR and CJK menus; the Undervolt rows; the
firmware update task; flashing with a host card reader; p3 auto-grow;
power-cut recovery. Full list per milestone in milestones.md.

## Open problems

- **Licences/publication:** v1.0.0 and v1.1.0 published (LICENSING.md; Hardkernel
  answered without a position, decision 47; Exophase and steward-fu
  still silent).
- **Battery % short of 100 on the charger — fixed (patch 0011, rc2 T3
  ok)** (2026-11-19:
  95 % after a night; FCC learned down to 2550 mAh). The driver's finish
  step (dsoc +1 % per ~92 s, only in MODE_FINISH) never ran: the next
  boot read rsoc 92.9 %, OCV 4149 mV, so the charge itself stopped
  short. **Cause found (charge log 2026-11-25, 23 → 98 % in 2 h):** the
  coulomb counter reaches FCC (rsoc 100.000 %) while dsoc sits at 98 %,
  taper still at 140–240 mA. `rk817_bat_fake_finish_mode()` tests
  `rsoc == 100`, but rsoc is in thousandths (other checks use
  `100 * 1000`), so fake finish never fires and dsoc only reaches 100
  on the PMIC's own CHARGE_FINISH (CHG_STS even read "off" in the
  taper; `update_info` also reset the finish timer). Patch 0011:
  98 → 100 % "Full" 2 min after boot (hardware-findings "End of charge").
- **Wi-Fi:** stuck scans at power-on (dongle reset at 20 s since m9c,
  T3 ok 2026-11-26); warm-reboot H2C (1 in 7); a real zombie occurrence is
  unverified (watchdog tested with injected errors only).
- **Heavy systems:** held by heat, not by the clock cap (hardware-findings
  "M8 thermal block"); play them on battery. Saturn too heavy for Sonic R.
- **Audio:** occasional PipeWire sink stall (self-healed before each
  game, root cause open); 200 % overdrive distorts (as upstream).
- **N64 Fn+Start fade (v1.1.1 T3 round 2):** the user saw no fade, an
  abrupt black screen; on the bench (m12c, MK64, Rice) the backlight fades
  55 → 0 in 0.3 s while Mupen64Plus still runs and it exits 1.1 s later
  (sampled every ~70 ms): not reproduced. Waiting for the game, the video
  plugin and whether it happens every time. N64 screenshots give no
  feedback.
- **Bars:** in games (libretro, ports, standalone emulators) one bar,
  muxretro's (square corners); the menu's LVGL bar has the theme's rounded
  corners (BAR_RADIUS / BAR_PROGRESS_RADIUS): unify them later if wanted.
- **User report (2026-11-26, another user, DTB "R36S-V12 2023-08-18
  Panel 4"):** a black screen while changing settings, and the B/back
  button also lowered the volume. Our Panel 4 DTB is dArkOSen's (plus the
  mmc aliases, minus the GPU 600 MHz OPP): joypad and keys use the same
  GPIOs and key codes as Panel 0 (phandles resolved), so the DTB does not
  explain B + volume; differences: panel init sequence, backlight PWM
  period 62.7 µs (Panel 0 40 µs), default brightness 51 (80). Suspects: a
  board that is not a genuine V12 Panel 4 (clone wiring), the backlight at
  low levels. Asked the user: dArkOSen with the same DTB fine? which
  setting, does the picture come back, B → volume everywhere?, Input
  Tester, `MUOS/log` + `model.txt`.
- **Menu:** "Direct Link", "Proxy Settings" and static addresses
  untested; one missed Power press in a 15-cycle soak (logged since M8).
- **Pinned, not rebuilt:** idbloader/trust (rkbin files, identical to
  rkbin).
- **Hardware:** headphone jack contact (deprioritized); slot 2 fails only
  with the spare card (closed); no controllable LEDs; DDR devfreq not
  synced to the VOP.
- **Trial root:** p3 can't be unmounted at shutdown while it runs.
- **p2 space:** 1 GiB, ~318 MB free.

## Decisions for the user

None open. (M10's test-hardware question answered by the T3: the user
tested a TP-Link RTL8822BU dongle, 2357:0115: it works.)

## T3 queue

**v1.1.1 checklist, round 3** (round 1 2026-11-26: all OK with A/B,
cursor and bar findings; round 2 on m12c: 1–3 OK, 4 not tellable (Splore
has no button labels), Doukutsu-rs confirms dialogs with its jump button,
"East" = the physical B (the port's own default, changeable in its
Options → Controls), 5: no fade on N64 Fn+Start, not reproduced on the
bench). On **test128** (m12d), then **original32** (public v1.1.1):
1. Volume −/+ and Fn+Volume −/+ in each: a libretro game (e.g. NES), a
   port (Doukutsu-rs or TurboTableTennis), the official PICO-8, Splore,
   and the standalone N64, PSP, Dreamcast (Flycast standalone core),
   NDS: the **same bar** (icon, colours, place, ~1.5 s then a fade) in
   all of them, no slowdown while it shows.
2. Explorar conteúdo → N64 → a game, Fn+Start: does the screen fade out
   now? If not: which game and which N64 core (Y → Núcleo), every time?
3. Aplicativos → PortMaster: no arrow, A confirms, B back (round 2 item 1,
   again on the new image).
4. original32: copy the new `MustardOS-R36S-port-v1.1.1.p2.img.gz` +
   `.p2.img.sha256` to `MUOS/update`, Aplicativos → Ferramentas de
   sistema → Instalar atualização do sistema; Informações → Detalhes do
   dispositivo: Compilação v1.1.1; then items 1 and 3 there and a PICO-8
   cart with each core (A = O in all three).
After it passes: m12d becomes the recovery image (m10a retired) and the
user runs `build/release/publish-v1.1.1.sh` (tags the final commit;
the public image was built at 0ee2786, same `port/device` tree as
m12d's e341b73).

## Current milestone: M12 — PICO-8 (done to T2 2026-11-26)

The user's focus after PortMaster, released with it as v1.1.1
(decision 48). Done:
1. Cores: Picante8 (MustardOS, GPL-3.0, muOS's default) and FAKE-08
   (MIT) built by `build-cores.sh`, pinned; `ROMS/PICO-8` assigned to
   Picante8 (schedutil). T2: both 60.0 fps on `ld45.p8` and a `.p8.png`.
2. Official PICO-8 (the user's own Raspberry Pi build, as dArkOSen and
   muOS): `muos-pico8` for muOS's ext-pico8-scale / -pixel cores
   (`-home MUOS/save/pico8`, `-root_path`, `-joystick 0`,
   `sdl_controllers.txt`); S91 unpacks `pico-8_*_raspi.zip` in
   `MUOS/bios/pico8` and shows the Splore app while PICO-8 is there; Fn+Start
   quits it. T2 with the user's 0.2.7: both modes and Splore run (640x480
   GLES2, PipeWire, muOS-Keys) and quit in ~1 s.
3. GNU wget with OpenSSL (BusyBox wget has no HTTPS).
4. Docs (README, CHANGELOG, known issues, findings, LICENSING: the
   official PICO-8 is never distributed); `t2-pico8.sh`; public checks.
Splore's BBS downloads: T3 round 1 OK.
5. **v1.1.1 T3 fixes (m12c, done to T2 2026-11-26):** `sdl_map_line`
   falls back to `board/sdl_map` (fresh cards had A/B swapped in SDL
   programs: ports, PortMaster, official PICO-8, PPSSPP, Flycast); SDL2
   patch 0004 (no default KMSDRM cursor); `muos-levelbar.so` preloaded
   into ports, applications and PICO-8 (GL, EGL, SDL renderer; dlsym
   wrappers for frt and pysdl2); FAKE-08 patched to A = O.
   `t2-levelbar.sh` PASS (board mapping on a fresh store, bar in
   PortMaster's GUI / TurboTableTennis / PICO-8, cursor plane off);
   t2-pico8 (both cores 60.0 fps), t2-portmaster and NES 59.99 fps PASS.
6. **One bar (round 2 request, m12d):** `muxretro --level-assets`
   (patch 0005) exports the in-game bar of the active theme;
   `muos-levelbar.so` draws it (GLES2 / SDL textures, muxretro's hold and
   fade) in ports, applications, PICO-8 and the standalone emulators
   (launchers preload it; DraStic after its hook). T2 on the bench:
   t2-levelbar.sh PASS with the theme's bar in PortMaster's GUI,
   TurboTableTennis, PICO-8, Mupen64Plus (60.1 VI/s), PPSSPP 2021,
   Flycast, DraStic (A/B: no cost beyond scene noise). YabaSanshiro and
   ScummVM standalone unverified (no test content).

## Milestone M11 — PortMaster (and muOS applications) (done to T2 2026-11-26)

Goal: Aplicativos → PortMaster installs and runs ports as on muOS
(PortMaster's own muOS variant, `muos.portmaster.zip`, unmodified), and
ports start from the Ports system with saves, the volume bar and a quit
chord. Survey (2026-11-26): PortMaster 2026.11.17-0700; 1518 ports, 933
aarch64-only, 204 armhf-only (no 32-bit userland: unsupported); all
runtimes checked (mono, weston_pkg, frt, gmtoolkit, dotnet, godot, zulu,
renpy, pyxel) are zlib squashfs, which the kernel mounts (loop + squashfs
zlib built in): no kernel change.

Items:
1. Python 3 in the rootfs (Buildroot: ctypes/libffi, ssl, zlib, json,
   sqlite as harbourmaster needs; pyc only) for harbourmaster/pugwash
   with pySDL2 on the system SDL2.
2. Applications in the frontend loop: action `app` (muxapp writes
   `/run/muos/application`) runs `mux_launch.sh` as upstream frontend.sh
   (governor, foreground, requests cleared, back to the app menu); app
   folders from `/opt/muos/share/application` and `MUOS/application`;
   `/run/muos/storage/application` for PortMaster's app ports.
3. muOS shims PortMaster and its ports use (port-own, MIT):
   `/opt/muos/script/var/func.sh` (GET_VAR/SET_VAR/LOG_*),
   `/usr/lib/gamecontrollerdb.txt` (muOS-Keys under PortMaster's
   "Deeplay-keys" name, as upstream gamecontrollerdb.sh),
   `/roms/ports/PortMaster` → `MUOS/PortMaster`.
4. Install on first launch: the PortMaster app downloads the pinned
   release zip (sha256-checked) or takes `MUOS/update/muos.portmaster.zip`
   offline, unzips it to p3 (`MUOS/PortMaster`, `ROMS/Ports`), then
   PortMaster updates itself. Not in the image: gptokeyb is GPL and 7zzs
   LGPL (no source duty for the port; LICENSING records it).
5. Ports launch: core `external` content (`ROMS/Ports/*.sh`) runs under
   bash with the SDL/audio environment, governor, Activity tracking;
   Fn+Start quits (muhotkey, as the standalones); the Ports system
   assignment and catalogue (`External - Ports`).
6. Graphics for ports: SDL2 KMSDRM on libmali, PortMaster's gl4es
   (`libgl_muOS.txt`), weston_pkg; T2 with free ready-to-run ports (one
   SDL2, one GL/gl4es, one runtime squashfs such as frt or love).
7. Native touches (as for the heavy systems): volume/brightness bar in
   ports, sleep/resume while a port runs, the low-battery guard.
8. Docs and licences (README, known issues: armhf ports unsupported;
   LICENSING; procedures), image v1.1.1 at the end.

**Progress (2026-11-26):** items 1–5 and 8 implemented; item 6 by T2
with real ports; item 7: the volume/brightness keys work in ports, no
on-screen bar (as the standalones; known issue), libretro ports get
muxretro's bar through the `/usr/bin/retroarch` shim. T1: Python 3.12.15
imports harbourmaster and its deps under qemu. T2 on m11a (trial root):
network install 6 s; harbourmaster CLI installed sdlsopwith,
turbotabletennis (+ frt_3.5.2 runtime), 2048; Sopwith and the Godot port
ran and quit in 1–4 s; the install task ran on the progress screen.
Fixed on the way: the quit chord waits for the whole process group
(Sopwith ignores SIGTERM), leftover groups and runtime mounts are cleaned
after a session, the installed check (harbourmaster deletes
pylibs.zip), SDL2_image JPEG (the GUI crashed on `no-image.jpg`), busybox
tar `.tar.xz` (Noto fonts) and `timeout`. m11b (p2 `bd535fda…`) carries
the fixes; `t2-portmaster.sh` is the repeatable T2.

T2 tests: Python T1 (qemu imports of harbourmaster deps), app launch
loop, PortMaster install from the zip and from the network, port
launch/quit/return × 3, sleep in a port. Expected T3: PortMaster UI
navigation and a port download; a played port with sound; quit chord;
volume bar; one GL port.
