# Completed milestones

Results and checklists of finished Phase 5 milestones, moved out of
[STATUS.md](STATUS.md). Newest first. The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## M9 — public v1.0 (in progress, started 2026-11-22)

Logs `build/logs/m9/`. Plan in STATUS. M8 closed first: **M8g T3
(2026-11-22):** 1, 3, 5 ok; 2 ok with two keyboard findings (the
preview showed every letter as `[l]`; a name typed for the game's own
save dialog arrived as its last letter only); 4 ok (fonts render, no
empty boxes) but Japanese mostly and Chinese partly in English (upstream
text). Decision 29: the standalone stays the ScummVM default. m8g
written to p2 with the user present (old p2 `0b1e8978…` kept as
`MUOS/trial/p2-previous.img`) and promoted to recovery, m8d retired.

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
