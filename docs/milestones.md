# Completed milestones

Results and checklists of finished Phase 5 milestones, moved out of
[STATUS.md](STATUS.md). Newest first. The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## M11 + M12 — PortMaster and PICO-8 (done 2026-11-27, v1.1.1 published; m12f is recovery)

Released together as v1.1.1 (decision 48). v1.1.1 T3 round 4 (2026-11-27,
m12f on test128, the v1.1.1 update on original32): items 1–5 OK; the user
published v1.1.1 (GitHub latest); m12f promoted to recovery, m12e retired.

### v1.1.1 T3 round 4 (moved from STATUS)

**v1.1.1 checklist, round 4** (rounds 1–3: A/B, cursor, one rounded
bar, N64 fade, all OK on m12e; round 3 item 4: an update copied to
`MUOS/update` on original32 (old v1.1.1) showed no finishing screen, a
flashed v1.1.1 opened PortMaster slowly and then installed v1.1.0 by
itself at the next start. Cause: the background updater took GitHub's
latest (v1.1.0) whenever it differed from the card's, and its download +
unpack ran while the menu and PortMaster were used; the missing
finishing screen fits its unpack racing the manual one into the same
`rootfs.img.tmp` (the sha256 is taken from the stream, so a corrupt file
passed, and the trial boot fell back). Fixed in m12f: no background
updater, a lock on stage/fetch, newer versions only).
On **test128** (m12f, already installed through the new task):
1. Aplicativos → Ferramentas de sistema: "Buscar atualização online"
   right below "Instalar atualização do sistema", each with its new icon
   (tray with an arrow; cloud with an arrow); Aplicativos: Splore with
   its icon (cartridge + magnifier). Switch the language once (e.g.
   English: "Check for Online Update" right below "Install Firmware
   Update"), then back.
2. "Buscar atualização online" with Wi-Fi: "Você já tem a versão mais
   recente" or v1.1.0 offered (a developer image counts every release as
   newer): choose Cancelar; nothing is downloaded. Without Wi-Fi:
   "Conecte ao Wi-Fi primeiro".
On **original32** (now v1.1.0 after the automatic install):
3. Copy `MustardOS-R36S-port-v1.1.1.p2.img.gz` + `.p2.img.sha256` (the
   new build) to `MUOS/update`; Wi-Fi may stay on (v1.1.0's updater sees
   v1.1.0 = latest and does nothing); Aplicativos → Ferramentas de sistema
   → Instalar atualização do sistema: progress, restart, "Concluindo a
   atualização do sistema", restart; Informações → Detalhes do
   dispositivo: Compilação v1.1.1.
4. There: Ferramentas de sistema → Buscar atualização online with Wi-Fi:
   "Você já tem a versão mais recente (v1.1.1)" (GitHub's latest is
   v1.1.0, not offered); restart with Wi-Fi on and use PortMaster for a
   few minutes: nothing is downloaded (`MUOS/update` stays empty) and
   PortMaster opens and closes at its usual speed.
5. There: volume/brightness bar in the menu, a game and a port (same
   rounded bar), PortMaster A/B and no arrow, a PICO-8 cart (A = O).
After it passes: the user runs `build/release/publish-v1.1.1.sh` (it
tags the final commit; the image was built at e0f9e01 + docs, same
`port/device` tree).

### M12 — PICO-8

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
6. **Round 3 item 4 (m12f, 2026-11-27):** updates over Wi-Fi are manual:
   Task Toolkit "Check for Online Update" (`SORT_AFTER: Install Firmware
   Update`, frontend patch 0013) offers a release only when its version
   is newer, asks before downloading (progress) and before installing;
   `muos-update auto` removed; `flock` on stage/fetch; `update-task.sh`
   helper; texts in all 31 languages; the port's glyphs `muxtask/update`,
   `muxtask/cloud`, `muxapp/splore` in the MustardOS theme (the internal
   theme: every theme falls back to it). T2: `t2-online-update.sh unit`
   PASS (GitHub's v1.1.0 not offered to v1.1.1; latest; Cancel; Download
   + Later with progress), menu run (order, icons, pt-BR, "latest"
   dialog), and the full install of m12f from the menu (download, unpack,
   trial boot with the finishing screen, write-p2 verified).
6. **One bar (round 2 request, m12d):** `muxretro --level-assets`
   (patch 0005) exports the in-game bar of the active theme;
   `muos-levelbar.so` draws it (GLES2 / SDL textures, muxretro's hold and
   fade) in ports, applications, PICO-8 and the standalone emulators
   (launchers preload it; DraStic after its hook). T2 on the bench:
   t2-levelbar.sh PASS with the theme's bar in PortMaster's GUI,
   TurboTableTennis, PICO-8, Mupen64Plus (60.1 VI/s), PPSSPP 2021,
   Flycast, DraStic (A/B: no cost beyond scene noise). YabaSanshiro and
   ScummVM standalone unverified (no test content).
7. **Round 3 (m12e):** the bar rounded as the menu's in muxretro and
   muos-levelbar.so (panel, track, indicator in slices; checked in
   muxretro's own frame with the grab-only mode, PICO-8 and the GL path);
   N64 Fn+Start: Mupen64Plus's own Stop mapping off, fade then SIGTERM
   (`t2-quit-fade.sh` PASS, autosave written). t2-levelbar, t2-pico8,
   t2-portmaster, NES 60.00 fps PASS.

### M11 — PortMaster (and muOS applications)

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


## M10 — experimental hardware reach (done 2026-11-26, v1.1.0 published; m10a is recovery)

Plan, items and T2 results (moved from STATUS):

Goal: v1.1 runs on more R36S units and with more Wi-Fi dongles, labelled
experimental (decisions 43–44; the port can't test them: feedback via
issues). Wi-Fi first (no bootloader write), then the variants.

Items:
1. Worker: any USB Wi-Fi dongle the kernel drives (modalias → wireless
   module, vendor Realtek drivers first; 8188fu is built in), interface
   by phy80211, radio off unloads it; the 8821cu-only paths (CD-ROM
   switch, warm-reboot reset, C2H watchdog, stuck-scan reset) stay
   gated on the 8821cu.
2. Hotplug rule + adapter row for any such dongle; autoload blacklist
   for the USB Wi-Fi modules (the worker loads them).
3. Firmware for the mainline drivers (mt7601u, rt2800usb, rt73usb,
   rtl8192cu, r8712u, r8723au) from linux-firmware, pinned, licences in
   LICENSING/THIRD-PARTY.
4. T1: detection against a fake sysfs; T2: the 8821cu regression set
   (radio, toggle loop, wake, hotplug, liveness).
5. Model DTBs (`dtb-survey.sh`, log `build/logs/m10/dtb-survey.tsv`):
   wave 1 = the 22 dArkOSen models on the port's board type (rg351mp
   U-Boot DTB) at 640x480 with the port's input names and key codes
   (Panel 0 keeps the port DTB: dArkOSen's Panel 0 has the glitching
   29 MHz timing). Build: dArkOSen DTB + the mmc aliases (`fdtput`),
   as `model-<sha12>.dtb` keys in dtb-variants.txt, in p1 and in p2's
   boot files. Not yet: 13 rg351v clones and R50S (other input names),
   7 soysauce (rg351p board), 1024/720 panels (frontend resolution).
6. Card-root selectors (`.bat`, `.sh`, `.command`) writing p1
   `model.txt` (a model id or `default`) from p1 `models.txt`.
7. `muos-model` (Linux, as `muos-undervolt`): early in the boot, a
   `model.txt` that main doesn't boot arms a one-shot trial with that
   DTB (same kernel) and reboots; the menu up 20 s promotes it; a
   failed trial renames `model.txt` to `.failed`. No U-Boot change, so
   v1.0 users get it through the update; boot-sync keeps the model
   across kernel updates; the undervolt rows say unavailable on a model.
8. Audio and battery come with each DTB (all wave-1 models: speaker +
   jack detection, dArkOSen `alsa_path` SPK_HP; no gamma key there).
9. Docs (README driver and model lists, hardware-findings,
   known-issues), v1.1.0 image at the end.

**Done to T2 (2026-11-26):** all 9 items.
- Wi-Fi (1–4): detection 15/15 fake IDs + the real 8821cu
  (`t2-wifi-detect.sh`); radio, toggle loop, C2H watchdog with the new
  hotplug path, wakes 9.3/8.9 s.
- Models (5–8): 22 model DTBs (exact deltas); `muos-model` both ways +
  give-up path on the bench with a Panel 4 test DTB (input names, root,
  Wi-Fi under it; `t2-model.sh`); selector T1.
- m10a through the update path from m9k: p2 written, boot-sync put the
  model files and selectors on p1, undervolt kept; detection, radio,
  4-cycle toggle, NES 59.97, wake 9.0 s: all pass.
- **v1.1.0** public built at `ce15e0f` (raw `8378de0c…`, p2 `8bedd242…`,
  32 checks), source zips packed (`build/release`), notes
  `build/release/v1.1.0-notes.md`; publishing after the T3:
  `build/release/publish-v1.1.0.sh` (the user runs it).
 **T3 (v1.1.0 public on original32,
2026-11-26):** 8/8 ok — update from v1.0.0 with progress screens, Build =
v1.1.0, Wi-Fi at power-on, toggle, replug, wake, the selector (item 7
first failed: `./select-model.sh` is "permission denied" on the FAT p1,
which udisks mounts `showexec`; the docs now say `sh select-model.sh`
and give a hand-written `model.txt` as fallback; scripts unchanged),
Undervolt rows. Extra: the user's TP-Link 2357:0115 (RTL8822BU)
hot-plugged in place of the 8821cu: 88x2bu, 5 GHz at 867 Mb/s, RSSI
-38 (hardware-findings "USB Wi-Fi drivers"). m10a promoted to recovery,
m9k + v1.0.0 local files retired.

## M9 — public v1.0 (done 2026-11-26, v1.0.0 published; m9k is recovery)

**Close (2026-11-26):** v1.0.0 T3 ok (update screens, Build = v1.0.0,
Task Toolkit in Português, Wi-Fi at power-on); m9k recovery, m9f retired.
The user's first publish run pushed main + tag but the release API gave
403 (token read-only on Contents); after the token fix the re-runnable
script created the release (latest) with the 8 assets. README: only
Panel 0 and RTL8821CU tested, others planned, feedback welcome.
Hardkernel's forum answer: ask Rockchip; strategy unchanged (decision 47).

Logs `build/logs/m9/`. Plan in STATUS. M8 closed first: **M8g T3
(2026-11-22):** 1, 3, 5 ok; 2 ok with two keyboard findings (the
preview showed every letter as `[l]`; a name typed for the game's own
save dialog arrived as its last letter only); 4 ok (fonts render, no
empty boxes) but Japanese mostly and Chinese partly in English (upstream
text). Decision 29: the standalone stays the ScummVM default. m8g
written to p2 with the user present (old p2 `0b1e8978…` kept as
`MUOS/trial/p2-previous.img`) and promoted to recovery, m8d retired.

**Licences and publication round (2026-11-25, decisions 33–38):**
docs cleanup (decisions.md, STATUS trimmed, M1–M7 and the M8
experiments archived, roadmap M9 rewritten). L1 `docs/LICENSING.md`
(single source, request log, community-practice reference; absorbs
license-requests.md); pending-licenses.json and THIRD-PARTY.txt
reconciled; Gambatte/FCEUmm into `build-cores.sh` (T2 NES 59.98, GB
59.99); rtl8821c BT firmware out (firmware-inputs remove list; a stale
copy in the Buildroot target was caught by the new public check); the
U-Boot "dirty" banner closed (patched source tree). The libmali ships
unmodified (post-build copies the Hardkernel binary over the patchelf'd
one; T2 DC 59.9 Hz with it bind-mounted). L2 MustardOS compliance: boot
logo "MustardOS", THIRD-PARTY/NOTICE/README unofficial-port and support
notice, Information → Device Details help texts (EN, pt-BR), credits + CC BY-NC.
L3 `make-source-bundle.sh check` covers the whole public image (frontend
and muxretro trees, submodules, YabaSanshiro deps, dArkOS patches,
legal-info: fixed for the 4.4 headers' COPYING). L4 history scan: no
secrets (device Wi-Fi/SSH values searched in all 2936 blobs: 0), no
ROMs or third-party binaries; README, NOTICE, LICENSE; updates from
laurorual/MustardOS-R36S-port. L5 `prepare-image.sh` (Plan B; T1 strip →
inject → present on m9c and on the public rc1; dn.odroid.com blocks
scripts: manual browser download into the cache). L6
`MustardOS-R36S-port-v1.0.0-rc1` built (public: 24 checks pass, `.img.xz`
+ p2 update assets) with the developer twin m9d (same rootfs) for the
trial-root T2. Polish: install guide EN/pt-BR, CHANGELOG, known issues,
release notes template.

1. **ScummVM virtual keyboard — done to T2:** `port/patches/scummvm/0001`
   (both builds; `build-scummvm.sh` applies `port/patches/scummvm/*` to
   the standalone's archive and once to the tree for the core): a plain
   character shows as itself, named keys keep brackets; the submitted
   keys go through a paced event source (one event per 60 ms: key down,
   up, next key) instead of all at once, because SCUMM keeps one key per
   game tick (`_keyPressed`). T2: core 100 % audio, standalone starts;
   the typing itself is T3.
2. **Decision 29 — done to T2:** core-assign.txt `SCUMMVM|ext-scummvm-sa`;
   `coredb-governors.py` now sets the system's `runtime` from the
   default's section (external → `"runtime": "external"`, libretro →
   none). Saturn had the same latent gap (external default, no runtime;
   only the S91 seed made it work).
3. **CJK menus — done to T2:** upstream's pack (also the 2026-11-22
   release `cc36ab2`) leaves Japanese ~86 %, Chinese Traditional ~80 %
   and Simplified ~39 % in English. Port overlays
   `port/packaging/language/{Japanese,Chinese (Simplified)}.json`: the
   1552 short labels (≤ 60 characters, one line) still in English, from
   every visible screen (not muweb, Bluetooth, HDMI, USB link, terminal,
   media), translated by the agent; format specifiers checked against
   the frontend's `translation_safe` rule. Help texts stay English;
   Traditional Chinese unchanged (an OpenCC conversion was blocked: pip
   install denied). T2 screenshots `build/logs/m5/shots/m9-*.png`.
4. **Undervolt opt-in (decision 28) — done to T2:** frontend patch 0012
   adds "Undervolt" below "Processor Maximum" (label and help through
   `translate_specific`, no lang-struct change; pt-BR, ja, zh in the
   overlays); `muos-undervolt` (sync, arm, promote, status); the image
   build generates the undervolted DTB (`make-dtb-uv.sh … 50 25`, the
   same `84611ef0394d` as this unit's) and writes p1 `dtb-variants.txt`.
   T2 on the device: off via the script (trial boot, promoted after 20 s
   of menu), then on through the UI (Right, B: arms, reboots, promoted):
   main = undervolt, previous = stock again. Fixed after: the booted DTB
   is cached per boot (arm rewrites the trial record a trial boot came
   from), the row reuses the overclock glyph.
5. **Image m9a** (raw `093d64ce…`, p2 `ed83f5f4…`): T1 373 ELFs, 0
   missing; trial-root T2 `build/m9/t2-m9a.sh` (logs
   `build/logs/m9/trial-m9a/`): checks (undervolt available, coredb
   default/runtime), sweep 44 ok, NES 59.96, sdcard, SFTP jail, ScummVM
   core + standalone, Flycast standalone, wake (1 slow frame): all pass.
   Written to p2 2026-11-22 with the user present (old p2 `678e3766…`).
   **M9a T3 (2026-11-22): 1–5 ok** → m9a recovery, m8e retired.
6. **Decision 31 — done to T2:** Traditional Chinese overlay converted
   from the Simplified texts (upstream + port) with OpenCC `s2twp`
   (`build/tools/opencc-venv`): 2062 strings; English left only where
   Simplified has none.
7. **Manual undervolt values (the user, M9a T3) — done to T2:** rows
   "Processor Undervolt" (−25…−100 mV) and "Graphics Undervolt"
   (0…−75 mV) below Undervolt (patch 0012, `danger/uv_cpu|uv_gpu`, mV),
   default −50/−25; the image build writes all 16 DTBs and `uv-C-G=`
   lines to `dtb-variants.txt` (the bench p1 got the same set); `sync`
   reads the values back from the booted DTB. Screenshot
   `m9b-danger-uv.png`; voltages beyond the default are untested (user's
   choice: visual check only).
8. **Items 5–6 (licences, source):** `third-party.sh` →
   `THIRD-PARTY.txt` in the image (every pinned component, licence,
   source offer); `docs/license-requests.md` (drafts for Hardkernel,
   Exophase, trngaje, steward-fu, MustardOS); `make-source-bundle.sh
   check|bundle` + `build-image.sh legal-info`; public variant: 18/18
   `check-public-image.sh` checks pass.
9. **Item 8, update path — done to T2:** `muos-update stage|resume` +
   Task Toolkit "Install Firmware Update": NAME.p2.img.gz + sha256 in
   `MUOS/update`, unpacked to the trial root, armed, reboot; after 30 s
   of menu `write-p2`, reboot (a failed trial falls back and is marked
   failed). Image m9b (raw `dcd4276e…`, p2 `ce6694f8…`, T1 0 missing)
   installed on the bench this way (stage → trial → write → main m9b).

### M9 rounds 2026-11-25/26 (moved from STATUS)

**Round of 2026-11-25 — done to T2:** docs cleanup; L1 LICENSING.md
(Gambatte/FCEUmm in `build-cores.sh`, BT firmware out, unmodified
libmali); L2 MustardOS name and support notice (logo, README, NOTICE,
THIRD-PARTY, Device Details help, EN/pt-BR); L3 source bundle covers the
public image (`make-source-bundle.sh check` passes); L4 history scan
clean, README/LICENSE/NOTICE, updater repo; L5 Plan B `prepare-image.sh`
(T1 on m9c and rc1); L6 rc1 built (24 checks) + m9d trial-root T2 10/10
(sweep, NES 59.97, GB 59.98, slot 2, SFTP jail, DC 59.99 Hz, DraStic,
N64, PSP 15.5 swaps/s), m9d written to p2. Polish: install guide EN/pt-BR,
CHANGELOG, known issues, release notes template.

**rc1 T3 round (2026-11-25):** fresh-card defaults (English, 50 %,
startup volume "previous", debug_mode 0), `/etc/issue`, boot logo from
the press-kit boot screen; check-public-image 29 checks; m9e T2, on p2;
history rewritten to the no-reply e-mail; m9d promoted to recovery.

**rc2 published** as a GitHub pre-release by the user (2026-11-26).
**Next (was):** the GitHub pre-release of rc2 (T3 ok):
`make-source-bundle.sh bundle`, assets, notes (decisions 40–41). The
repository is public (pushed by the user 2026-11-25, `a62c25b`); later
commits are pushed by the user too. **Done 2026-11-26:** kernel/DTB
updates through the update path (`muos-boot-sync`, procedures.md; m9g
T2: two failed tries → given up, success path, the full stage → trial
root → write-p2 → arm → trial → promote with the undervolt DTB mapped,
boot-slot 4/4, NES 59.96); bench back on test128 (m9f, p3 restored), now
p2 = m9g. v1.0.0 built (29 checks); source zips via `make-source-bundle.sh
pack`. **Next:** v1.0.0 T3 (above) → the user publishes v1.0.0 as a normal
release (bundle + pack at that commit). **Done 2026-11-26 (night,
autonomous):** update progress screens (frontend patch 0013 + `muos-update
finish`), faster write, battery guard, Task Toolkit texts in 31 languages
(`task-texts.py`), Build = release; m9k + v1.0.0 built, v1.0.0 tagged,
source zips packed; publishing left to the user (the push was refused to the agent). **Next:** v1.0.0 T3 (above); then
post-v1.0 (roadmap: variants, dongles, next MustardOS release). Done 2026-11-25 evening: kernel patch 0011 (battery finish), trial
boot T2, promoted; rc2 rebuilt with it.

## M8 — card layout and the heavy systems (done 2026-11-22, M8g T3 passed; m8g is recovery)

Logs `build/logs/m8/`. Image `test128-m8-20261120` (raw `fbd4871c…`, p2
`0f723304…`) on p2 since 2026-11-20 ~03:05; U-Boot `159e086c…` written
the same night (user's exception for that night: U-Boot, partition table
and p2 writes allowed while away, avoiding writes likely to lose SSH).

1. **Slot 1 = mmcblk0 (decision 16) — done to T2:** kernel patch 0009
   (host and mmcblk index from the `mmcN` DT alias, upstream v5.9/v5.10
   behaviour) + DTS aliases mmc0 = sdmmc (slot 1), mmc1 = sdio. Trial
   kernel T2 (mmc0/mmcblk0 = ff370000, t2-sdcard, NES 59.97), promoted
   (main `Image-331eebd4a643` + `panel0-c97151d0ec1a.dtb`).
2. **U-Boot: root by device, quiet boot, boot logo — written, T2 passed:**
   bootargs `root=/dev/mmcblk0p2`, `console=ttyFIQ0` only, `quiet
   loglevel=3`; no autoboot delay (stock odroidgoa value, was 3 s); no
   diagnostic LCD text (probe-quiet.patch, boot profile only:
   `uboot-ref` still byte-identical to the M2 card); `muos_boot` shows p1
   `bootlogo.bmp` after validating it (640x480, 24 bpp, uncompressed,
   pixels inside the file: the decoder has no bounds checks); text only
   on failures. T0 37/37 (ASan/UBSan, 10 new logo cases). Written from
   main with read-back (previous U-Boot `65fb3dcd…` saved: p3
   `MUOS/trial/uboot-previous.img`, host `build/m8/`). First boot: cmdline
   as above, frontend loop at 10.9 s uptime (12.7 s before) plus ~3 s
   less in U-Boot; `t2-boot-slot.sh` 4/4 (main, corrupt main -> previous,
   bad trial consumed, main again).
3. **Boot logo:** `make-boot-logo.py` (greys only, Noto Sans; own art, no
   MustardOS assets): p1 `bootlogo.bmp` for U-Boot and the same picture
   from muos-rc start (`muos-splash bootlogo.fb.gz`) until the frontend.
   Visual result is T3.
4. **p2 1 GiB, slot-2 swap — not done:** the card's p3 holds the Wi-Fi
   profile and the trial root, so moving it remotely risks SSH; needs
   the user (host reflash + p3 restore, or a planned migration).
5. **Wake in a game (M7 T3 note) — done to T2:** woken in a game, Wi-Fi
   stays down until the game ends (watcher, network/deferred quiets the
   USB watchdog; T2 hook `wifi-wake-in-game`). T2 (real mem sleep, RTC
   wake, NES): 40 s in game after the wake with Wi-Fi down, dwc2 unbound,
   no watchdog rebind; Wi-Fi up 9 s after the game quit; 3161 frames
   after the wake: 10 at 18.5-25 ms, 8 at 25-50, 2 over 50 (peak 40 ms
   in the steady window).
6. **Cores (decision 20) — built, T1:** parallel-dc (libretro/flycast,
   installed as `flycast_libretro.so`, `arm64_cortex_a53_gles2`), melonDS
   (`odroidgoa`), YabaSanshiro (`arm64_cortex_a53_gles3`), PPSSPP libretro
   (built, not shipped). coredb post-build: unshipped externals dropped,
   "extra" unmarked on the defaults.
7. **dArkOSen's choices (the user, 2026-11-20):** dArkOS RK3326
   `es_systems.cfg`: PSP standalone PPSSPP (v1.20.4 + its patches,
   `ppsspp.ini`/`controls.ini` RG351MP), NDS DraStic, DC flycast (32-bit
   default; 64-bit flycast here), Saturn YabaSanshiro standalone (HLE).
   Clone `build/darkos-src` (tree only, blobs on demand).
8. **PSP — standalone PPSSPP, done to T2:** `build-ppsspp-sa.sh` (SDK gcc,
   dArkOS flags; no SDL2_ttf, as dArkOS: atlas fonts), `muos-ppsspp`
   (memstick p3 `MUOS/port/ppsspp`, dArkOS defaults copied once, OpenGL
   forced, muOS-Keys label mapping), `muos-frontend` dispatches
   `ext-ppsspp`, sleep stops/continues it, Fn+Start quits
   (`QUIT_STANDALONE` hotkey -> `muos-standalone-quit`, SIGTERM). T2:
   God of War starts, 30 Hz content, after menus mostly 7-8 presented
   frames/s with auto frameskip (heaviest PSP game; verdict is T3);
   Fn+Start quits PSP and N64 from the frontend. libretro PPSSPP: GoW at
   15 of 30 Hz (960x544 muxretro default).
9. **NDS:** melonDS 22-23 fps (JIT on, threaded renderer ~23):
   unplayable. DraStic r2.5.2.2 (dArkOS binary) runs on this rootfs
   (all libraries present) once SDL renders with vsync
   (`SDL_RENDER_VSYNC=1`; without it KMSDRM pageflip -22, black screen);
   ~70% of one core in NSMB. Not integrated: licence (decision 23) and
   its controls need remapping to muOS-Keys (select 8, start 9, hat).
10. **DC and Saturn need BIOS:** parallel-dc's HLE (REIOS) hangs at boot
    on Power Stone 2 (no frame in 75 s, also without threaded rendering);
    YabaSanshiro refuses to start without the real BIOS (HLE only by a
    debug option). Decision 24.
11. **Trial root T2 (m8):** sweep 44 ok / 10 bounces (same set as M7),
    NES 59.96, t2-sdcard, t2-sftp-jail, Wi-Fi toggle 3/3, PSP and MK64
    start/quit; written to p2 (previous p2 `50a5c24d…` saved).
12. `trial-guard.sh` (p3 user init, unattended trial boots) is in the
    repo now; removed from the card at the end (user_init back to 0).
13. **Night-1 T3 (2026-11-20, the user):** 1, 2, 4, 6 ok; 3 PSP runs but
    slow (asked: dArkOSen's PPSSPP settings, or its other PSP emulator);
    5 micro stutters after a wake, and the Power press felt slow (game
    froze late, screen off later); 7 after the new emulator. Decisions:
    23 the fastest emulator for every system, closed source allowed; 24
    BIOS provided (`dc_boot.bin`, `dc_flash.bin`, `saturn_bios.bin`); 25
    layout session accepted (user present).
14. **Sleep/wake (T3 5) — done to T2:** muos-suspend turns the screen off,
    stops a standalone emulator and mutes first (muxretro's ~1.3 s
    auto-save now runs behind a black screen; dArkOSen's sleep hook also
    blanks first). Woken in a game, the paused frame shows for 3 s
    (`settings/power/wake_hold`, ms), then sound and game resume:
    `t2-wake-frames.sh` (NES, 2 wakes) 10-11 slow frames up to 238 ms in
    the first 2.8 s (page flip) -> none. dArkOSen does nothing special on
    wake (kernel thaw, then its post hook).
15. **PSP (T3 3) — done to T2:** dArkOSen runs `ppsspp.ini.sdl` (copied
    over ppsspp.ini each start; not the file we had seeded) and offers
    `standalone-2021` (v1.12.3). `t2-psp-fps.sh` (the user's states; v1.12
    loads its state with L3): see hardware-findings "PSP performance".
    Default now `ext-ppsspp-2021` (`build-ppsspp-sa.sh build 2021`: dArkOS
    2021 patches, `-include` fixes for GCC 13, `-no-pie` for its
    non-PIC bundled FFmpeg; own memory stick p3
    `MUOS/port/ppsspp-2021/ppsspp`, SAVEDATA linked to the 1.20 one;
    defaults from dArkOS 2021 sdl ini with InternalResolution 1 and
    FrameSkip 1). v1.20.4 stays as `ext-ppsspp`. God of War ~31 emulated
    fps (full speed) in the user's scene.
16. **NDS — DraStic, done to T2:** `build-drastic.sh stage` (dArkOS
    binary r2.5.2.2 + BIOS replacements, database, logos; no usrcheat.dat),
    `muos-drastic` (working dir p3 `MUOS/port/drastic`, binary copied in),
    drastic.cfg = dArkOS RG351MP with the controls moved to muOS-Keys;
    `ext-drastic` added to the coredb (upstream has no NDS external).
    NSMB full speed; sleep/wake ok; Fn+Start quits (SIGKILL after 2 s).
17. **DC — Flycast v2.7 (flyinghead), done to T2:** `build-cores.sh`
    row `flycast2` (CMake, LIBRETRO, GLES3), installed as
    `flycast_libretro.so`; Power Stone 2 with the BIOS 36-43 fps.
    Saturn with the BIOS ~21 fps (Sonic R).
18. **One-shot migration `m8-heavy-defaults` (S91):** folder seeds and
    per-game assignments equal to the old defaults move (PSP ext-ppsspp
    -> ext-ppsspp-2021, NDS melonDS -> DraStic).
19. **Image `test128-m8b-20261120` — p2 1 GiB (items 3):** firmware.defconfig
    1G; firmware-image.sh moves the M2 base p3 behind the new p2 and
    rewrites the MBR (same disk id); `firmware-inputs.py pin-tree/pin-file`.
    Trial root T2: sweep 44 ok / 10 bounces, NES 59.98, t2-sdcard,
    t2-sftp-jail, Wi-Fi toggle 2/3 then 4/4 (one cycle SCANNING 150 s),
    PSP/NDS/DC start and quit, wake frames 2/2. Flashed with the user
    present (2026-11-20 ~17:25, host reader): `card-p3.sh backup`,
    `flash-card.sh host ... --grow`, `card-p3.sh restore` (6539 entries);
    first boot: p2 1 GiB (468 MB free), p3 116 GiB, migration ran, NES
    59.98, menu sleep 1/1. `make-recovery-image.sh`/`device.sh capture`
    now take the 1152 MiB prefix.
20. **m8b T3 (2026-11-20 evening, the user):** 1, 2, 5, 7, 10 ok; 3 sleep
    good but the 3 s wake hold felt slow; 4 GoW playable with frameskip 1
    but with graphics problems; 6 NDS ok, a small black cursor at the top
    left, no auto load of the state, wants dArkOSen's two-screen layout;
    8 DC not playable; 9 Saturn slow (try dArkOSen's standalone). New
    rule (AGENTS.md "Heavy Systems"): heavy systems = maximum performance
    first (closed source, standalone, R36S settings, overclock), dArkOSen
    first reference; native touches second. Decisions 26 (slot-2 swap,
    the spare card may be erased) and 27 (DraStic and other closed parts in
    the developer and the public image; publication only after the
    licence answers).
21. **PSP graphics — done to T2:** screenshots of GL emulators
    (`t2-swapstat.sh grab`, `t2-psp-fps.sh` T2_PSP_GRAB): dArkOSen's
    v1.12 ini renders non-buffered (`RenderingMode = 0`): no sky, no
    post-processing. Buffered: ~8 % slower at a fixed clock; default now,
    applied once to a seeded ini (`.muos-buffered`).
22. **NDS — advanced DraStic, done to T2:** `build-drastic.sh stage-adv`
    (trngaje advanced_drastic `d445a56` dArkOS lib, drastic_layout
    `e8dc3eb` 640x480 art, upstream muOS's drastic-trngaje drastic.cfg with
    the muOS-Keys controls and dArkOS's performance settings), installed at
    the m8b path `/opt/muos/share/emulator/drastic`; `muos-drastic` keeps
    p3 `MUOS/port/drastic` (saves kept; the m8b drastic.cfg becomes
    drastic.cfg.plain once). Layout vh_s0 by default, auto save state on
    exit/SIGTERM (slot 10, ~0.5 s) and auto load; no cursor plane. NSMB 60
    fps. `libmucursor.so` (upstream cursor shim) built and shipped.
23. **DC — Flycast 2022, done to T2:** `build-cores.sh` row `flycast2022`
    (libretro/parallel-dc `4c293f3` + dArkOS's makefile/per-pixel patches
    from `port/patches/cores/`, goadvance platform tuned for the A35, no
    OpenMP), coredb "Flycast 2022 (dArkOSen)" default, migration
    `m8c-dc-2022`. `t2-dc-fps.sh` (user's fight state on v2.7: 38 ms
    frames; attract: core 6.5 ms vs 11.6 ms).
24. **Wake stutter — root cause, done to T2:** the slot-2 card's resume
    rescan spins on CPU0 (hardware-findings "Wake in a game"). Kernel patch
    0010 (dw_mmc set_ios waits sleep; trial boot, t2-sdcard, NES 59.94,
    promoted: main `Image-be499e33d4eb`), muos-suspend resumes the game on
    CPU1-3 while Wi-Fi is deferred, wake hold default 0.
25. **Saturn:** dArkOSen runs YabaSanshiro standalone (christianhaitian
    `pi4-1-9-0`, retro_arena port, low-res mode, SH2 cache off); it needs
    Boost (system, filesystem, date_time, locale), not in the SDK/rootfs.
    The libretro core runs with threads off (only the sound thread).
    Done in the M8c T3 round (item 30).

**M8c T3 (2026-11-20 night, image m8c):** 1 wake in NES, 2 PSP buffered
(a little slower, kept), 3 NDS layout, 6 NDS sleep, 8 regression ok;
4 stylus on the left stick (wanted right), 5 NDS resume loads an old
state and Fn+Start freezes for seconds, 7 DC better but uneven speed and
half resolution; 9 slot-2 swap: spare card flashed with m8c.

26. **NDS quit — done to T2:** Fn+Start reached DraStic twice: the hook's
    own HOT_QUIT started the auto save state, muos-standalone-quit's
    SIGTERM arrived during it ("busy saving old one", deadlock), SIGKILL
    5 s later left an empty `_savestate_temp.dss`, so the next start loaded
    the old slot 10. muos-standalone-quit now only waits for DraStic
    (SIGTERM after 8 s, SIGKILL 5 s later); muos-drastic drops an empty
    temp state. T2: quit in ~1 s, slot 10 rewritten, the next start loads
    it.
27. **Quit indicator — done to T2:** muos-standalone-quit drops the
    backlight to a sixth while a standalone emulator saves and quits and
    restores it after (65 → 11 → 65).
28. **NDS stylus on the right stick — done to T2:** touch cursor on a2/a3,
    the vertical d-pad on the left stick (build-drastic.sh, the shipped
    drastic.cfg and a one-time migration of the user's, marker
    `.muos-rstick`).
29. **DC Flycast 2022 options — done to T2** (`t2-dc-fps.sh`, now per the
    DC folder's core, test state `MUOS/t2/dc-fight-2022` = the user's
    fight): base (320x240) 25 ms mean frame, 16/33 ms alternating, 81
    underruns; 640x480 costs nothing (23 ms); + `reicast_framerate=normal`
    a steady 33 ms (30 shown), 60 emulated fps, 4 underruns; synchronous
    rendering 59 shown but 53 emulated (slow motion) and 0.5 s audio
    missing. Default by migration `m8d-dc-2022-opts` (640x480 + normal).
30. **Saturn standalone YabaSanshiro — done to T2:**
    `build-yabasanshiro-sa.sh` (static Boost 1.83.0, offline deps
    zlib/json/libchdr/libpng pinned, GLES3 by EGL without a desktop
    libGL), `muos-yabasanshiro` (p3 `MUOS/port/yabasanshiro`, ES-style
    input.cfg for muOS-Keys), Fn+Start SIGTERM (quit ~1 s), default by
    migration `m8d-saturn-sa` (libretro selectable). Sonic R: title 23-24
    fps, intro/race 10-20 swaps/s at 1008 MHz (thermal, 81-83 °C); the
    libretro core in the race 18.6 of 60 emulated fps (31 %). Game speed
    of the standalone not measured (frame skip): T3 compares both.
31. **Image m8d** (raw `c7520a89…`, p2 `37d7194d…`): trial-root T2
    (`build/m8/t2-m8d.sh`): sweep 44 ok, NES 59.96, sdcard, SFTP jail,
    Wi-Fi toggle, DC 640x480 steady 33 ms frames (75 °C), NDS quit ~1 s
    with the state written, Saturn start/quit, PSP 11.9 presented (m8c
    11.7), wake 3 slow frames ≤ 25 ms: all pass; written to p2
    2026-11-20 ~23:50. m8c promoted to recovery, m7d retired.
32. **Slot-2 swap (decision 26):** the spare card flashed with m8c boots in
    slot 1 (SDR50); test128 in slot 2 runs at SDR104, ~62 MB/s, no errors:
    the slot-2 problem was that card in slot 2. Slot 2 stays empty.

**M8d T3 (2026-11-21 night, image m8d, the user):** 1 stylus, 2 NDS
resume/quit, 3 PSP closing, 7 regression ok; 4 DC still fast in the BIOS
and Capcom logos and slow mid-fight; 5 Saturn standalone slow (sound
fine), Select closed the game or left a black screen; 6 the only other
Saturn core offered was Yabadabadoo, which fails. Notes: NDS touch on R3
(the user's choice, default from now on); Fn+Start should fade, not jump
to dark. The rest of the night unattended.

33. **DC speed — done to T2:** `t2-coremeter.c/.sh` (dlsym hook entered by
    a tail jump, so RTLD_NEXT callers keep working) measures the core's
    audio frames per second. Flycast threaded + muxretro's Speed Limiter
    off by default: ~830 ms audio queue, 108-123 % catch-up bursts.
    Migration m8e-dc-limiter turns it on in both Flycasts' core settings:
    queue ~30 ms, the user's fight at 100 % (~52 pictures/s at 1008 MHz),
    heavy attract scenes ~86 % (frame skipping 1: 100 % at ~28/s, left
    off). Threaded rendering off hangs the 2022 core.
34. **Saturn — done to T2:** our YabaSanshiro patches (vblank page
    flips: the ~30/s refused async flips; the SCSP realtime wait's broken
    deadline; MUOS_YABA_FPSLOG; a crash stack handler) and the menu crash
    root cause (nanogui's older nanovg ABI; build copies src/nanovg):
    Select opens the menu 4 of 4, Fn+Start quits without the SIGSEGV.
    Sonic R race 20-25 of 60 emulated fps (the sound thread is the limit;
    C68K no better): the game is too heavy for the RK3326 (T3 note).
35. **Core lists — done to T2:** `coredb-governors.py` marks libretro
    entries extra by installed cores (151 hidden, YabaSanshiro and melonDS
    shown).
36. **NDS touch on R3, Fn+Start fade — done to T2:** build-drastic.sh and
    the shipped drastic.cfg (touch 1036, fake microphone 1035 = L3), a
    one-time migration of the user's config (`.muos-r3touch`; their R3
    touch kept, the microphone moved off R3); muos-standalone-quit fades
    the backlight to black in ~0.35 s over the game picture before the
    signal, keeps it dark until the emulator is gone, fades back in ~0.3 s.
37. **Image m8e** (raw `2f0293a2…`, p2 `e43458ce…`): trial-root T2
    (`build/m8e/t2-m8e.sh`, logs `build/logs/m8e/trial-m8e/`): migrations
    (both Flycast limiters, DraStic R3/L3), coredb (Yabadabadoo hidden,
    YabaSanshiro shown), sweep, NES 59.97, sdcard, SFTP jail, Wi-Fi
    toggle, DC 98.8 % speed, NDS quit ~1 s with the state written, Saturn
    race + Select menu + quit without SIGSEGV, quit fade, PSP 11.6
    presented (thermal), wake: all pass; written to p2 2026-11-21 ~03:50
    (unattended, pre-authorized). m8 retired. Not done tonight: ScummVM
    (no game data to test; a full scummvm build), CJK fonts, overclock.
    **M8e T3 (user, 2026-11-21): 2–9 ok** (Saturn picture, menu, save
    and load state also across a restart, quit, core lists, NDS R3/L3,
    fade, regression). 1 DC: no longer accelerated, but the fight felt
    like heavy frame skipping at 60 fps shown; the user turned on the
    core option Synchronous Rendering and off Anisotropic Filtering:
    smooth at 60, with random returns of the skipping feel (thermal?).
    6: two DraStic entries for NDS: keep only the advanced one. m8e
    promoted to recovery (better than m8c everywhere); m8b retired.
38. **Thermal research (2026-11-21):** dArkOSen ref updated to 28f5427;
    its DTB thermal zones, CPU voltages, caps and game governors equal the
    port's (hardware-findings). `t2-thermal.sh` (per-second temperature,
    clocks, cooling states, battery mA joined with the core's real speed):
    DC baseline 79.3 °C, 94.7 %, 159 s below 95 %; throttling to 1008 MHz
    is the "frame-skip feel" (88 % there). Cap 1200: 77.4 °C, 96.5 %.
39. **Undervolt (T6, the user asked to include it):** `make-dtb-uv.sh`
    trial DTBs. CPU+GPU −50: 75.9 °C, 97.0 %, 102 s; −75: 74.8 °C but Mali
    GPU faults in PSP (also at GPU −50). CPU −50 / GPU −25
    (`84611ef0394d`): PSP 5 min and DC 8 min clean; trial-boot T2 (NES,
    DC, PSP, `build/logs/m8f/trial-uv`), **promoted as the main DTB**
    (previous = the stock DTB). Charger: +5 °C and throttling to 408 MHz;
    a test kernel patch for the RK817 charge/input limits (0011) wrote the
    fields but changed nothing measurable: dropped, kernel back to
    be499e33.
40. **DC defaults (M8e T3 1):** migration m8f-dc-sync: Synchronous
    Rendering on, Anisotropic Filtering off (the 2022 core's LOW_END
    default drops a frame whenever the GPU is late).
41. **NDS (M8e T3 6):** upstream's "Drastic - Standalone" coredb row
    dropped; one "DraStic (Advanced)".
42. **Flycast standalone (T9):** dArkOSen's binary is damaged in their
    repo (eol=lf), so `build-flycast-sa.sh` builds v2.7 as dArkOS does
    (system SDL2), `muos-flycast` (dArkOSen's emu.cfg + auto save/load
    state), coredb "Flycast - Standalone (dArkOSen)". T2: runs, quits in
    ~4 s, state saved; ~15 presented fps, CPU-bound (Flycast 2022: ~51).
43. **ScummVM (item 5):** v2026.4.0 (dArkOSen's version; their binary
    needs Debian libs), `build-scummvm.sh` builds the standalone and the
    libretro core from one tree with the 34 "lite" engines, FLAC/Vorbis,
    MT-32. The core deadlocked under muxretro (libco context created on
    the main thread, retro_run on muxretro's worker): built with
    USE_LIBCO=0 (pthreads). Content as upstream: NAME.scummvm next to the
    game folder (S91 creates it; the standalone detects and writes the
    id). T2 (Monkey Island CD): core 100 % speed, 14.5 ms/frame, 50
    frames/s (the core's own thread pacing); standalone ~24 % CPU, quits
    in ~1 s. `muos-suspend` now also stops YabaSanshiro (missing since
    M8), ScummVM and Flycast.
44. **Image m8f** (raw `fe44baad…`, p2 `15b51793…`): trial-root T2
    (`build/m8f/t2-m8f.sh`, logs `build/logs/m8f/trial-m8f/`): sweep, NES
    59.97, sdcard, SFTP jail, ScummVM core + standalone, Flycast
    standalone, DC 2022 97.8 %, NDS, Saturn, PSP, wake: all pass; p2
    written 2026-11-21 ~15:30.
    **M8f T3 (user, 2026-11-21): 2, 6, 7, 8 ok**; 3 PSP as before the
    undervolt (no faults); 1 DC: the short "frame-skip" spells remain
    (more often, shorter); 4 two Monkey Island entries, the first fails;
    no way to type a save name; 5 only one ScummVM entry in the core
    list. No visible change from the undervolt (expected: DC 94.7 → 97 %).
    Decisions: 28 agreed (opt-in toggle), 30 keep Flycast standalone.
45. **ScummVM (M8f T3 4, 5) — done to T2:** the core launcher's copy of
    NAME.scummvm into the folder made the folder a second explorer entry
    (muxshare `folder_has_launch_file`: NAME/NAME.scummvm), which handed
    the inner file to muos-scummvm (no NAME/NAME folder: exit 1). Layout
    now upstream's self-contained one: NAME/NAME.scummvm, the folder is
    the one entry (S91 moves the outer file in; hidden .NAME/_NAME keep
    the outer one); both launchers take it. Upstream's coredb gives the
    libretro and external ScummVM the same key "scummvm" and muxassign
    lists one row per key: the external is "scummvm-sa" / "ScummVM -
    Standalone" (`coredb-governors.py`), the system's runtime preference
    dropped (fresh folders get the core), migration m8g-scummvm-sa moves
    old assignments. Virtual keyboard: the standalone built with
    `--enable-vkeybd` + vkeybd_default/small packs, the core finds them
    (and the engine data) through BIOS/scummvm/extra → the standalone's
    data directory (S91); Select opens it in both.
46. **CJK (decision 17):** Chinese (Simplified/Traditional), Japanese and
    Korean ship with upstream's fonts (share/font/internal/<Language>,
    ~33 MB); their language files were also in firmware-inputs.json
    "remove" (the M7 exclusion), dropped from it.
47. **Overclock (item 18) — measured, dropped:** 1512 MHz on battery is
    heat-bound for DC (95.6 % vs 97.0 % at 1296) and PSP (12.3 vs 12.6
    fps); Flycast DSP off: no gain (hardware-findings "M8 thermal block").
48. **Image m8g** (raw `81613024…`, p2 `4ca8c058…`): trial-root T2 of the
    same build before the CJK language fix (p2 `ff031e2f…`,
    `build/m8g/t2-m8g.sh`, logs `build/logs/m8g/trial-m8g/`): sweep 44 ok,
    NES 59.96, sdcard, SFTP jail, ScummVM core 100 % (vkeybd pack
    loaded) + standalone from NAME/NAME.scummvm (VirtualKeyboard), the
    S91 move and migration, Flycast standalone, DC 2022 98.1 %, NDS,
    Saturn (race, menu, quit), PSP 12.5, wake: all pass. m8c retired.
    The reboot back to main after the batch (2026-11-22 01:12) left the
    device off the network (Wi-Fi; the user reconnected it). The final
    p2's short trial T2: CJK menus render (`build/m8g/t2-cjk.sh`), NES
    59.96. `write-p2` refused by the auto-mode classifier (user leaving):
    the trial root re-armed from it (`/media/etc/muos-root-trial`) and the
    device powered off, so the T3 runs on m8g as a trial root.


M1–M7 (2026-11-10 to 2026-11-20): [archive/milestones-m1-m7.md](archive/milestones-m1-m7.md).
