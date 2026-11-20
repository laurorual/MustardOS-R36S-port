# Completed milestones

Results and checklists of finished Phase 5 milestones, moved out of
[STATUS.md](STATUS.md). Newest first. The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## M8 — card layout and the heavy systems (in progress; night 1 and day 2026-11-20)

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

## M7 — polish: language, performance, power (done 2026-11-20, T3 passed; m7d is recovery)

Logs `build/logs/m7/`. Images m7 → m7t3 → m7c → m7d (recovery).

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
15. **Standalone Mupen64Plus (decision 19) — built, T1 passed, not on
    the device yet:** `build-mupen64plus-sa.sh` (2.6.0 core with the
    aarch64 new dynarec, ui-console, audio/input-sdl, rsp-hle, Rice,
    GLideN64 GLES3+EGL at `a04081a`; 5.0 MB, pinned inputs), core patch
    `port/patches/mupen64plus/0001` (MUPEN_AUTOSAVE: Stop saves a state
    first), launcher `/usr/libexec/muos-mupen64plus` (N64's upstream
    `ext-mupen64plus-*` assignments; Rice or GLideN64; Fn+Start quit +
    autosave, resume with --savestate; Fn+R1/L1 state; libretro-like
    controls; config in p3 `MUOS/port/mupen64plus`, saves per game in
    pickles `mupen64plus_sa`; a mupen64plus-next .srm is split into
    .eep/.mpk/.sra/.fla on the first start, header names tested in z64,
    v64, n64 order on the host). T2 after the discharge run: assignment
    list, start, input, quit/resume, DK64 fps (Rice vs GLideN64 vs the
    libretro core), sleep while it runs.
16. **Idle power — measured:** discharge run 22 % → low-battery
    poweroff in 91 min at 407–425 mA (hardware-findings).
17. **Standalone Mupen64Plus — done to T2:** fixed on the device:
    nothing shown (SDL's async page flips are refused by the 4.4 kernel:
    vsync forced on), Input-SDL section version, no forced
    ThreadedVideo; Fn+X screenshot; muos-suspend stops/continues it
    (fake sleep verified on the charger; real "mem" sleep is T3). T2:
    start through the frontend handoff, DK64 .srm migration, Fn+Start
    autosave + resume (DK Rap further along after restart), autosave on
    UI stop (poweroff path), audio stream in PipeWire, fps with
    `t2-swapstat.sh`: DK64 intro Rice 58 VI/s vs libretro 30.6 fps;
    MK64 Rice 61; standalone GLideN64 20–27 (GPU-bound, any options).
    The N64 folder's default stays the libretro core (MK64 59.9, more
    accurate); DK64 → Standalone Rice per game (T3 item 4). The
    assignment list's ext entries come from core.json (not yet opened
    in the menu at T2).
18. **New systems — T2 (decision 18):** real games at 59.8–60.0 fps on
    title/attract screens: 32X Chaotix (core 8.9 ms), 2600 Pac-Man,
    7800 Ms. Pac-Man, GG Sonic Triple Trouble, Lynx Blue Lightning
    (handy's built-in boot, no BIOS), SMS Sonic, PCE Splatterhouse.
    With the user's BIOS (decision 21): Sega CD Sonic CD (picodrive,
    bios_CD_U.bin, 35 tracks) and PCE CD Dracula X (pce_fast,
    syscard3.pce) 60.0 fps. Atari 5200, VB, Jaguar, Jaguar CD, CD-i out
    of v1.0; Dreamcast, PSP, NDS, Saturn in M8 (decision 20).
19. **PipeWire sink stall — found and self-healed:** the first trial
    root of image m7c had no game audio (muxretro discarded it all; the
    standalone N64 froze in audio-sdl's sync): PipeWire's ALSA sink had
    stopped writing (appl_ptr frozen, PCM running). Reproduced 3× in ~10
    full screen sweeps, never per screen; a PipeWire restart cures it.
    `muos-frontend` now checks the PCM for 0.1 s before each game and
    restarts PipeWire when stuck (T2: frozen PipeWire → detected (XRUN)
    → restart → NES audio flowing). Root cause open.
20. **M7c T3 (2026-11-19):** 1–3, 5–8 ok; 4 partial: save, controls,
    steady frame rate, resume, sleep, levels and the camera ok (the
    camera reset was the libretro core), Fn+X saved two shots but showed
    nothing, no level bar. Glide much slower than Rice (expected). Small
    slowdowns felt in the new systems. Promoted to recovery (m5 retired).
21. **Its follow-ups — done to T2 on the live root:** decision 22 (N64 →
    standalone Rice: core-assign row with an ext- core, S91 installs it
    when `emulator/mupen64plus` exists, one-shot `n64-standalone`
    migration of the folder and per-game cfgs equal to the old seed;
    `coredb-governors.py` sets an external default and drops N64's
    unbuilt external entries). T2: migration on busybox, MK64 from the
    folder assignment → Rice under performance, Fn+Start autosave, .srm
    split.
22. **New systems, frame pacing (`t2-newsys-fps.sh`, 75 s each,
    attract):** all 7 at 60.00 Hz, p95 16.9–18.2 ms; the only frames over
    25 ms (one per 17 s window, always 2.1 s into it) are muxretro's own
    15 s capture dump, so no hitch from the cores. 2600 Pac-Man has the
    most 18.5–25 ms frames (62 per 75 s, still no repeats). The user's
    slowdowns are likely the games' own (Chaotix and 2600 Pac-Man slow
    down and flicker on real hardware) or level changes (~1 frame each,
    M3b); ask which game if they persist.
23. **CTR at the 1296 vs 1512 cap** (`t2-long-play.sh --cap`, mid-race
    from the fixed test state p3 `MUOS/port/t2/ctr-race`, the user's
    scene): 1512 is thermally counterproductive under a long load (CPU
    held at 1008–1200 MHz, min fps 59.31, 433 underrun events) vs 1296
    (59.88, 25): the 1296 default stays (decision 13; hardware-findings).
24. **Underruns — measured:** the "bursts" are the game start (launch +
    state load); a steady game underruns only when the core runs short of
    CPU (hardware-findings, Audio).
25. **Image `test128-m7d-20261119`** (`1ed3ce6`, raw `67ae7da4…`, p2
    `176c691a…`): trial root T2 passed (build id `r35s-1ed3ce6`, sweep 44
    ok/9 bounces as before, NES 59.96, sleep 2/2, t2-sdcard,
    t2-sftp-jail, Wi-Fi toggle 3/3, MK64 Rice start/quit); written to p2
    2026-11-19 (previous p2 `21fbc43b…` saved).
26. **Soak (`t2-soak.sh`, m7d on main, 10 min per game, ~1 h 40):** NES,
    GBA, 32X, PCE, Mega Drive (UMK3, from `megadrive`; SNES and MD empty
    on p3) 59.79–59.95 min fps, 0–2 underruns, RSS flat, 68–83 °C, CPU
    1296 MHz throughout; CTR mid-race 59.89, 43 underruns, 83 °C; MK64
    (standalone Rice, folder default) 10 min alive, 61.9 VI/s, 78–82 °C,
    Fn+Start autosave written; sleep in a game 5/5. Menu sleep 1 of 5
    missed: the press reached muos-hotkey (SLEEP_SHORT logged 20 s after
    the previous resume) but muos-suspend exited without a trace (its
    lock or the recent-wake guard); rerun 5/5. Both silent exits now log
    (next image).
27. **M7 T3 (2026-11-20, image m7d):** 1–8 ok (N64 default and core
    list, DK64, dongle during boot, long play, menu sleep 3/3, game
    sleep, regression). Notes: (a) there is no boot logo: the kernel
    console scrolls on the LCD (U-Boot env `console=tty0 loglevel=7`) →
    M8 with the clean U-Boot; (b) on wake a libretro game (NES) is back
    almost at once but stutters briefly before it settles (the known
    ~0.7 s of slow frames), while the standalone N64 holds its last frame
    ~1 s and then runs smoothly → M8. m7d promoted to recovery, m7
    retired.

## M6 — systems, cores, build from source (done to T2 2026-11-19; p2 never written, superseded by M7)

Image `dist/firmware/test128-m6-20261119`. Its `write-p2` was refused by
the Claude Code permission check while the user slept (unattended); M7's
image contains all of M6.

Plan (roadmap.md), state:
1. M5 T3 fixes — done to T2: Config rows (frontend 0008), screenshot
   flash (0007), fbcon unbound under the UI (S99), Wi-Fi C2H reset
   (worker; `t2-wifi-toggle-loop.sh`, 10 cycles + injected error).
2. Release frontend (`TEST_IMAGE=0`) of libui, libmuxcom, libmuxmod,
   libplutosvg, muxfrontend, muhotkey, mubattery, muxretro — done to T2
   (screen sweep 44 ok/7 bounces, NES 59.76 fps). Config keys reviewed:
   106 absent keys, all with built-in defaults.
3. Cores (`build-cores.sh`): stella2014, prosystem, handy, beetle pce
   fast/neopop/cygne, blueMSX, gearcoleco, gearsystem, pokemini, FBNeo,
   MAME 2003-Plus, dosbox-pure, mupen64plus-next (trial) — built, symbol
   checked, 18 folders seeded; smoke fps 60 on 2600, 7800, PCE, NGPC, WS,
   SG-1000, Pokémon mini, DOS. Coredb system defaults = the
   port's cores (auto-assign). ScummVM: decision 17.
4. Kernel modules from source: `build-boot.sh modules-check` 553
   identical + 2 differing only in the build date — done.
5. BIOS: upstream core info files (muxretro's BIOS prompt) + Diagnostics
   → BIOS Report — done to T2 (on the device: 3 required files missing
   for MSX/Coleco; the PSX BIOS names need lower case).
6. Image `test128-m6-20261119` (raw `d443411e…`, p2 `ac695c52…`): trial
   root T2 passed (sweep 44 ok, NES 59.98, DOS smoke 60.01, Wi-Fi toggle
   3/3 + injected C2H, sleep 2/2 in game, t2-sdcard, t2-sftp-jail 8;
   logs `build/logs/m6/trial/`). T3 folded into M7's checklist.


## M5 — daily-driver completeness (done 2026-11-18, p2 written, T3 2026-11-18: not promoted)

First milestone of the release plan (roadmap.md). Image
`dist/firmware/test128-m5-20261118` (raw `64e45d74…`, p2 `768942b1…`)
+ `public-m5-20261118` (T0 only); logs `build/logs/m5/`.
1. **SFTP follow-up:** FileZilla's error is a remembered path outside the
   jail (`ls /mnt/mmc/ROMS` → "not found"). The Web Services help for SFTP
   already gives port 2022 and `muos`/`muos` (upstream default English
   text; the pinned pt-BR file predates it).
2. **Discharge report:** findings in hardware-findings (displayed % lags
   rsoc; % kept across power-off). `report` restored a stale volume (40)
   and resume.ini from a 14 Nov run: now it restores and removes only
   what the current run saved; `log-start` drops stale files.
3. **Archives:** Info-ZIP `zip`/`unzip` (BusyBox unzip lacks `-Z`);
   upstream `mux/extract.sh`, `mux/backup.sh`, `package/{theme,catalogue,
   config}.sh`, `system/{profile,catalogue}.sh`, `var/{ui,zip,theme,diag,
   runtime,boot}.sh`, `script/archive/*` unchanged (hash list). T2 in
   native task mode: backup of the screenshot section → `.muxbak` →
   restore.
4. **Upstream share data:** `refs/muos/internal` is a `blob:none` sparse
   clone (reading `share/` blobs fetched 19 MiB into refs once, by
   accident); `fetch-upstream-share.sh` keeps a sparse clone in
   `build/upstream/internal` (640x480 only, 28 MiB): six themes, profiles,
   lookup/name tables, media, tasks (14 unported ones excluded),
   languages, Latin fonts, by git tree id. `muos-seed-share` (S90) copies
   the themes and name files to p3 like upstream's factory reset. The
   pinned launcher had no `image/grid` (blank tiles); the 2606 themes were
   rejected because `config/system/version` was missing ("Edge"): shipped
   as `2606.0_ANDROMEDA`, refreshed by S91 every boot.
5. **Profiles:** `profile.sh` state on p3 (`share/profile/state` link);
   apply Large Print / undo T2 (undo materialises default-valued files).
6. **Slot 2:** port `script/device/storage.sh` (controller ff380000,
   exFAT/FAT32/ext4 at `/mnt/sdcard`, ROMS/ARCHIVE/ports), udev
   `91-muos-sdcard.rules`, S90 at boot; `t2-sdcard.sh` with loop devices
   (vfat, exFAT, unformatted, UTF-8 names, jail's Secondary Storage).
   Safety: cards are numbered in detection order, so `muos-root-trial`,
   `muos-boot-slot`, `muos-grow-p3`, `muos-ext4-diag` and S89 find the
   slot-1 card by controller (`muos-boot-disk`). Frontend 0008 hides the
   Storage migration screen (no bind.sh) and muxspace's card preparation.
7. **Screenshots:** the panel is a KMS plane `/dev/fb0` doesn't show;
   frontend 0007 serves screenshot requests on every output; port
   `screenshot.sh`; X+L2+R2 (upstream hotkey file). Menu only.
8. **Frontend fixes:** 0008 also hides "Cores" (upstream downloads);
   0009 hides colour temperature (no colour node on the RK3326); 0010
   moves the theme catalogue and Explore's forward history to p3 (both
   were on `/opt`, read-only). CA certificates for libcurl; the upstream
   theme download/filter and hotkey config keys; `share/news` link to p3.
   Theme download and the community catalogue work.
9. **Clock:** RTC stays UTC through muxrtc/muxtimezone's `hwclock -w`
   (`/var/lib/hwclock/adjtime`, FHS path).
10. **Screen sweep** (`t2-screen-sweep.sh`, `t2-ui.sh`): 54 context-free
    screens opened by `/run/muos/action`, none crashed; contact sheet
    `build/logs/m5/shots/sweep-sheet.png`.
11. **Tests:** T0 shellcheck, contract, public leak check; T1 338 ELFs.
    Trial root: `t2-sdcard`, `t2-sftp-jail 8`, `t2-sftp 16`, `t2-wifi`,
    `t2-sleep-cycle --game 2`, `t2-menu-cycle` (its Explore path now goes
    down to Nintendo Game Boy: friendly names sort the root); p2 written,
    `t2-sftp-jail 4` and `t2-sdcard` on it. Incident on the first trial:
    the 8821cu firmware error loop with Wi-Fi "up" (STATUS, M7).

**T3 2026-11-18** (the user; fixes in M6, so M4g stays the recovery image:
item 5 broke menu navigation):
1. FileZilla ok (new site): Catalogue, Collections, History, Internal,
   Primary Storage; ROM copy works; help shows the login and port.
2. Ok. Noted: a console flash when a game starts or ends and a blink when
   returning to the list or changing theme. Cause of the flash: fbcon
   repainted the kernel log on fb0 whenever the UI dropped the display
   (M6: unbound). The blink is upstream's black fade-in (Customisation).
3. Ok. MustardOS launcher icons look dimmer than the theme's preview:
   the theme's own 640x480 scheme sets icon alpha/recolour 225 and tile
   alpha 192; its preview.png matches the global scheme (255). As upstream.
4. Ok (theme download, apply, back to MustardOS).
5. **Configuration → Backup opened Power, Power opened Core ("No cores
   found")**: 0008 hid the Core row but its A-handler entry stayed visible
   (M6 fix).
6. "Nothing happens" on X+L2+R2: eight screenshots of that session are
   in MUOS/screenshot; there was no feedback (no rumble motor). M6: a
   white flash. In-game screenshots remain unsupported.
7, 8. Ok.
9. The minute changed; after a reboot NTP set the correct time again
   (as designed: the RTC is written, then synced when Wi-Fi is up).
10. **Slot 2 failed** (FAT32 and exFAT card, `ROMS/megadrive`): the
    kernel never initialised the card: data line busy before the first
    command, DAT3 low (looks unpowered), at boot and on hotplug. DT, kernel
    source, config, regulators, pins and GRF match stock dArkOSen, whose
    log shows slot 2 at SDR104 on this unit. Open (T3 in M6).
11. Mostly ok. One Wi-Fi off/on stayed in "connecting" (8821cu C2H error
    loop after the module load, 95 s) until a second toggle; M6: the
    worker resets the dongle on those errors. The wake hitch felt
    stronger; likely the slot-2 card init retries on resume (~3 s of mmc
    errors at each wake in that log).

## M4g — SFTP jail, overdrive volume bar (done 2026-11-18, p2 written, T3 2026-11-18 → recovery image)

Image `dist/firmware/test128-m4g-20261118` (raw `a9d7cbc4…`, p2
`371b3f23…`); logs `build/logs/m4g/`.
1. **Overdrive bar.** The frontend's `device.c` clamps `device.audio.max`
   to 0–100, the bar handlers drop saved volumes above it, and
   `volume_to_percent` divides by 200 with overdrive: the bar stopped at
   50 % while the sink went on (T2: saved 123, gain 1.86). muxretro
   patch 0002 and frontend patch 0006 (`common/ui/common.c`) take 200
   with overdrive. 0006 is in libmuxcom, so `build-frontend-libs.sh` now
   ships `libmuxcom.so` when a patch touches `frontend/common/`; an
   unpatched rebuild has the pinned symbol table (names, types, sizes;
   only `.data`/`.bss` padding from link order differs), the patched one
   differs only in `ui_common_progress_tick`'s size. libmuxmod unchanged.
2. **SFTP jail (decision 6)** as upstream `web/service.sh`: dropbear
   `-G muos -c /opt/muos/frontend/musftpjail -W 1048576 -T 5` on
   web/sftp_port. `musftpjail` built unchanged from the pinned frontend
   source (upstream tool flags); Buildroot package `muos-sftp-static`:
   gesftpserver linked `-static` at `/opt/muos/bin/aarch64/sftp-server`,
   account `muos` (1000, upstream's hash = "muos"; mkusers wants home
   `-`), `musftpjail` root:muos 4750, `/opt/muos/browse`. The worker
   refuses to start SFTP without the jail. The developer SFTP (2222,
   root, `/usr/libexec/sftp-server`) is unchanged.
3. **T0–T2:** shellcheck; frontend 0 warnings, muxretro only the 13
   upstream ones; `check` passed; T1 333 ELFs resolved, the server static,
   modes and accounts read from the ext4 image. Trial root:
   `t2-sftp-jail` (login shows only Catalogue, Collections, History,
   Internal, Primary Storage; 8 MiB put 9.8 MiB/s; `/..`, /etc, /usr not
   reachable; root and a wrong password refused; Internal read-only),
   `t2-sftp 16`, `t2-wifi`, `t2-wifi-robust`, `t2-menu-cycle`,
   `t2-sleep-cycle --game 2`; live root before the image: `t2-menu-cycle`,
   `t2-sleep-cycle --game 2` with the new libmuxcom/muxretro. p2 written
   and verified; `t2-sftp-jail 4` on the written p2. `sftp -b` turns
   BatchMode on (no passwords): the test passes `-oBatchMode=no` first.
4. **T3 (2026-11-18):** 1 overdrive bar OK; 2 FileZilla with a saved site
   failed at connect with `SSH_FX_NO_SUCH_FILE` (OpenSSH lists the jail
   fine: the site's remote directory is outside the jail; M5 item 1);
   3 battery 55 % before a power-off off the charger, 55 % after: closes
   battery problem (c) (kernel 0008); 4 regression OK. Promoted to recovery,
   M4d retired.

## M4f — USB watchdog, menu scripts (done 2026-11-17, p2 written and T3 2026-11-18 → recovery image)

Logs `build/logs/m4f/`.
1. **dwc2 missed plug/unplug.** Trial DTB `dr_mode = "host"` (only change,
   `panel0-09073fe29464.dtb`, trial boot): 4 manual cycles, 8/8 events
   seen; not conclusive against the ~1 in 6 miss rate (23 % chance), so
   the DT stays `otg`. Automating replugs through the RK817 BOOST failed:
   with 0xB4 = 0x00 the dongle stayed powered (on battery and on the
   charger), so the BOOST is not the port's 5 V and item 3 (BOOST power
   cycle) is dropped. A dwc2 unbind/bind re-detects the port (Wi-Fi back
   17 s later) → `muos-usb-watchdog` (S97): HPRT0 bit 0 vs usb 1-1 every
   2 s, 3 disagreeing reads → rebind, 30 s pause; idle while
   `suspend.lock` is held (muos-suspend unbinds dwc2 itself); binds a dwc2
   left unbound 10 s; a stop mid-rebind still binds. T2: simulated missed
   plug (test hook) → rebind, Wi-Fi ready 15 s after detection; the
   robustness test's software unplug is healed the same way; no trigger
   over 9 wakes. Incident: an earlier test killed the watchdog between
   unbind and bind → no USB until the user rebooted (nothing written).
2. **Menu scripts.** The pinned set lacks 9 scripts the menu modules run
   (`libmuxmod.so`): shipped now: own `tweak.sh` (audio/max from Audio
   overdrive, also at boot: it never applied before; brightness; default
   governor without content), upstream `find.sh` (Search) with an own
   `/opt/muos/bin/rg` (busybox subset), `track.sh` (Activity; hooks in
   muos-frontend start/stop and muos-suspend suspend/resume/poweroff),
   `serial.sh`, `tegridy.sh` (all "Modified": no verifier, honest for an
   unofficial port), `var/service.sh`; copied from refs/muos/internal
   (pinned 550cc58f, identical to the pinned var/*.sh) by
   `stage_overlay` against `port/packaging/muos-internal-extra.txt`.
   Not shipped: `prepare.sh` (formats a card: one-slot device), `logo.sh`
   (writes p1), `backup.sh` (needs zip), `profile.sh`, Bluetooth; no
   `share/lookup` name tables (search by file name).
   T2: tweak overdrive 0/1/0 → audio/max 100/200/100; search "crash" →
   CTR in 0.35 s; track start/suspend/resume/stop on tmpfs → 5 s of 7;
   `t2-sleep-cycle --game 2` with tracking on tmpfs → 56 s of 99 (two
   sleeps excluded); `t2-sleep-cycle`, `t2-wifi-robust`, `t2-wake-wifi`.
3. **Trial T2 and write-p2 (2026-11-18).** The trial root's
   `t2-wifi-robust` hotplug FAIL was the test: the watchdog's rebind
   (4–6 s after the software unplug, logged as "missed plug") had the
   dongle back before the 8 s "removed" sample. The test now samples at
   3 s (usb-done may still be set), waits for the watchdog's rebind and
   rebinds itself only without a watchdog. Trial root: `t2-wifi`,
   `t2-wifi-radio`, `t2-wifi-robust`, `t2-sleep-cycle --game 2`,
   `t2-wake-wifi 2` (9.1 s) passed, no watchdog trigger over the sleeps;
   p2 written and verified (`46a573a0…`), live: watchdog, frontend,
   audio/max 100, one sleep cycle.
4. **T3** (user, 2026-11-18): 2 Search, 3 Activity, 5 Wi-Fi replug ×4
   (all four seen by the kernel, watchdog idle), 6 sleep/wake in game and
   Wi-Fi toggle passed; 4 serial shown, the integrity result is the
   "Modifications" tab of Device Details (items "Modificado"), as
   designed. 1 overdrive: the volume rises (T2: saved 123, gain 1.86),
   but the bar stops at 50 % (frontend clamps `device.audio.max` to 100,
   upstream; STATUS open problems). No regression against M4e.1 (overdrive
   never applied before) → recovery image; M4c retired.

## M4e.1 — Input Remap saves, dongle re-plug, kernel 0008 (done 2026-11-17, T3 passed → recovery image)

Image `dist/firmware/test128-m4e1-20261117` (raw `c122c7f4…`, p2
`d73646be…`, kernel `ea8ac003` = 0001–0008); p2 written with `write-p2`
from the trial root (old p2 `5b621944…` in `MUOS/trial/p2-previous.img`).
Logs `build/logs/m4e-t3/`.
1. **M4e T3** (user, 2026-11-17 afternoon): 1 24-hour clock OK, 2 Rumble
   row OK, 3 Input Remap never stuck, 4 second replug failed, 5 (after
   0008) 19 → 19 → 19 % over a power-off on the charger and a reboot.
2. **Input Remap:** muxremap saves through `script/mux/sdl_remap.sh`,
   absent from the pinned script set (only `audio_sink.sh` of 28), and the
   DB `share/info/gamecontrollerdb` is on the read-only root. Own MIT
   `sdl_remap.sh` (upstream contract: replace the GUID's line, set
   `settings/remap/layout`, drop display.sh's `/tmp/sdl_gc_*` cache); S91
   seeds p3 `MUOS/port/gamecontrollerdb` once and binds it. The frontend
   adds that file on top of the board map, so the menu follows a remap.
3. **Second replug (timeline from dmesg/hotplug/worker logs):** the
   unplug produced no kernel event; turning Wi-Fi off/on made the worker
   reset the stale port (`usb_modeswitch -R`) and only then "USB
   disconnect" (590 s). The re-plugged dongle came back in CD-ROM mode at
   the same path while the worker waited 30 s for 0bda:c820 (add ignored:
   worker running). Attempt 2 associated, the AP sent deauth reason 2 (it
   still held the old association), the driver ignored it (`ignore=1`),
   no lease for 170 s, and the worker reported "ready" without an address.
   Worker now: a 1a2b with a new devnum during the wait → switch again
   (2 times max); no address at 20 s and 50 s → `disconnect` +
   `reassociate`. The missed disconnect itself: `t2-usb-watch.sh`
   (dev-only logger of HPRT0/GINTSTS, usb 1-1, wlan0, wpa_state).
4. **Kernel 0008:** OFF_CNT read 74 min after the flat-battery power-up;
   `i2cset` 0 sticks. Trial boot: off count 0, `ocv=0`, dsoc kept;
   promoted (previous = 0007).
5. **Flat battery (0006/0007 T3):** clean low-battery poweroff 04:05 at
   2 % / 3352 mV; at power-on "stored dsoc=2049 … ocv stale, kept": the
   counter survived.
7. **T3** (user, 2026-11-17 16:40): 1 Input Remap stuck, the menu
   followed it, restored; 3 a game's buttons right (CTR). 2 replug: plugs
   1, 2 and 4 reconnected in ~10 s; plug 3 (16:37, uptime 1264 s) had no
   kernel event at all: HPRT0 read 0x00021401 (connected, D+ high, port
   not enabled) for 53 s and nothing enumerated; the unplug (1317 s) and
   plug 4 (1328 s) were seen. Same class as the M4e missed unplug: the
   dwc2 driver misses port interrupts (GINTSTS without PrtInt).
6. **T2:** `t2-wifi`, `t2-wifi-radio`, `t2-wifi-robust`,
   `t2-sleep-cycle` 5/5, `t2-wake-wifi 2` (8.8–9.1 s) PASS on the live
   root and the trial root; `sdl_remap.sh` host test (scratch paths) and
   device test (board mapping, then removed).

## M4e — config directories, rumble probe, Wi-Fi diagnostics (done 2026-11-17 night, T2 passed; superseded by M4e.1)

Built unattended while the user slept. Image `dist/firmware/test128-m4e-20261117`
(raw `ea5ca0b4…`, p2 `1b877d11…`, kernel `d61188f3` = 0001–0007). Its p2 is
in p3 `MUOS/trial/rootfs.img` (T2 passed there); `write-p2` was refused by
the permission check while unattended. The card's main p2 is M4d + the
M4e files installed with `install-rootfs.sh` (all functional changes; not
the worker's cosmetic stderr fix). Logs `build/logs/m4d/*m4e*`.
1. **M4d T3** (user, 2026-11-16 night): 1 time zone OK (24-hour notation
   did not stick), 2 Wi-Fi Network row OK (the first replug was slower
   than the second), 3 regression OK, 4 flat battery in progress (the
   discharge logger runs tonight). M4d promoted to recovery, M4a retired.
2. **Config directories:** the pinned `/opt/muos/config` lacked 15
   directories the frontend writes (`clock`, `backup`, `sort`, `terminal`,
   `settings/{overlay,hotkey,colour,font,hdmi,rgb,theme}`, ...): every save
   there failed ("Failed to open file for writing: .../clock/notation" =
   the 24-hour bug). `usr/share/muos-r35s/config-dirs.txt` (from the
   pinned config.c and module paths) + S91 creates the missing ones on p3
   (reads default when a file is missing). T2: all present after a boot.
3. **Rumble** (the R35S has no motor; some R36S do; every R36S-family DT
   declares the PWM): `muos-rumble` (C, Buildroot package) plays FF_RUMBLE
   on the gamepad (private node: muinput hides it) and probes the motor
   from the RK817 averaging current (0x7A/0x7B over i2c, ~0.7 s update):
   4 × (off 1.2 s / on 1.2 s), present if median delta ≥ 35 mA. R35S: 4
   runs, deltas −2…+3 mA (noise ±3 mA at menu idle): absent. The FF write
   reaches the PWM although muinput grabs the pad (PWM registers change
   during a pulse). `muos-rumble-setup`: verdict cached per SoC serial in
   p3 `MUOS/port/rumble`, probed in the background on a new device,
   `board/rumble` = `ff` or empty; startup/shutdown/sleep pulses per
   `settings/advanced/rumble`. Frontend 0005: Advanced → Rumble reads
   "Unavailable", dimmed and locked without a motor (keeps the saved
   value); Rumble strength was already hidden. Positive case unverified
   (no motor here).
4. **Wi-Fi diagnosis:** the 2026-11-17 warm reboot hit the H2C case
   again (1 in 7 since M4c): firmware deaf from 13 s, the dongle reset
   itself at 53 s and returned in CD-ROM mode at 72 s, but the worker
   waited its full 90 s for an address, so Wi-Fi came at ~115 s. Now: the
   worker logs uptime stamps, retries as soon as the interface vanishes,
   waits 30 s (not 10) for the dongle to come back, and S89 keeps the
   boot's worker/hotplug logs and the dongle's kernel lines in p3
   `MUOS/log/network-last.log`. The user's slow first replug left no logs
   (only /run then); likely the same deaf-firmware case (4 s settle after
   power-up passed 3/3 per value in M4c, not 100%).
5. **shellcheck 0.10.0** (`build/tools/shellcheck`, user-approved
   download): all port scripts and shipped init scripts warning-clean
   (false positives annotated; `muos-headphone` empty assignment).
6. **Gauge jump after warm reboots (found tonight):** 57% → 69% on a
   reboot. OFF_CNT (0x6F) keeps 141 min across warm reboots, so the BSP
   recalibrated to the stale power-up OCV (3880 mV); 0005's stale check
   (30 points against the voltage estimate) let it through and 0002 moved
   the display. Kernel patch 0008 clears OFF_CNT after reading it
   (`Image-ea8ac0033c0e`, T0 only: needs the i2c write check and a trial
   kernel with the user present).
7. **T2 (trial root, M4e p2):** `t2-wifi.sh`, `t2-wifi-radio.sh`,
   `t2-wifi-network-row.sh`, `t2-wake-wifi.sh 3` (8.6–9.1 s),
   `t2-sleep-cycle.sh` 5/5 PASS; rumble probe absent; config dirs; network
   log at shutdown. Incident: a blind "up, left" before the network-row
   test (focus was already on Explore) made its A presses launch CTR; the
   sleep test then autosaved it: **CTR's resume state
   (`autosave.state`) was overwritten at 00:38** (memory card `.srm`
   rewritten at 00:33, content presumably unchanged: CTR saves only on
   demand). The test now aborts on the first unexpected screen.

## M4d — public-build prerequisites, part 1 (done 2026-11-16, T3 items 1–3 passed 2026-11-16)

Image `dist/firmware/test128-m4d-20261116` (raw `619473f7…`, p2
`61f2c02f…`, kernel `d61188f3` = 0001–0007, DTB `bc04b6f8`) + public
variant `public-m4d-20261116` (raw `6b715293…`). The card runs the same
p2 (`muos-root-trial write-p2`, old p2 in p3 `MUOS/trial/p2-previous.img`)
and kernel; bootloader and p1 unchanged. Logs `build/logs/m4d/`.
1. **Wi-Fi Network without an adapter** (M4c T3 item 2 remark, frontend
   0001): dimmed and closed while the toggle reads "Unavailable".
   `t2-wifi-network-row.sh` (button injection, software unplug/rebind):
   PASS on the M4c files and on the M4d trial root.
2. **Battery cut-off** (`muos-lowbattery`): critical 3 → 1%, guard on the
   current-corrected voltage (V + I·200 mΩ < 3550 mV) instead of the
   loaded 3500 mV. Analysis (hardware-findings, Power): the ~470 mAh left
   at the CTR cut-off are not reachable at 730 mA (loaded 3352 mV vs the
   BSP's own 3300 mV poweroff); 1% gains ~2–3 min. `t1-lowbattery.sh` 8/8
   on the host and under the device's busybox.
3. **Battery history** (S97): one line per boot and per clean stop in p3
   `MUOS/log/battery-history.log` (RTC date, %, mV, mA, the kernel's boot
   decision); the M4b log only kept 3 boots. Verified: stop + boot lines
   across the trial reboots.
4. **Clock:** the RK817 RTC already kept UTC (40 s off after days).
   busybox `ntpd` (`muos-clock sync` after each address, ≤ every 6 h of
   uptime, RTC written in UTC via `/var/lib/hwclock/adjtime`): first boot
   stepped 40 s, the next 0 s. Time zones: Buildroot tzdata 2026e (3.1
   MB), `/etc/localtime` → p3 `MUOS/port/config/localtime` (S91 creates it
   as UTC), frontend 0004 makes the Timezone screen rewrite that link (the
   root is read-only). T1 (`t1-fresh-p3.sh`): UTC on a new card, −03 after
   a São Paulo link; T2: `date` follows a link change at once. The
   Timezone screen itself was not driven (T3).
5. **Boot payloads (decision 3):** rkbin's BL31 (efff42ab) has the same
   LOAD segments as the pinned one; the trust image built from it is
   byte-identical to the card's (`rkbin-trust.sh`). No bootloader write;
   all four payloads are rkbin files (LICENSE in `build/m4d/rkbin`).
6. **Not done:** SFTP jail (upstream's `musftpjail` chroots and then
   `fexecve`s a static sftp-server; the port's gesftpserver is dynamic →
   M4e), LEDs (none controllable), rumble (`board/rumble` empty; motor
   unknown: question for the user).
7. **T0–T2:** frontend from a clean tree (patches 0001–0004 apply,
   libmuxmod `165afdfa…` reproducible; no warnings in the patched code);
   `check-public-image.sh`, `t1-fresh-p3.sh`, `t1-elf-deps.sh` PASS. On
   the trial root: `t2-wifi.sh`, `t2-wifi-radio.sh`,
   `t2-wifi-network-row.sh`, `t2-menu-cycle.sh` PASS; on the written p2:
   `t2-wake-wifi.sh 3` (wake → address 8.8–9.1 s) and
   `t2-sleep-cycle.sh` 5/5 PASS, NTP step 0 s after the reboot. A blind button run in Configuration → General saved
   `startup = resume` through the save dialog: reverted (file removed,
   config diff empty). shellcheck is not available on the host (download
   blocked): `sh -n`/`bash -n` only.

## M4c — Wi-Fi toggle, faster Wi-Fi after wake, warm-reboot fix (done 2026-11-14, T3 passed 2026-11-16)

**T3 (user, 2026-11-16, files installed on the card, kernel 0007):**
items 1–7 all OK (toggle, no dongle, off stays off, wake 3×, Web
Services, back navigation, warm reboot 2×). Item 2 remark: "Wi-Fi
Network" stayed enabled while the toggle read "Unavailable"; no reason
to, so it is now dimmed and closed without an adapter too (frontend
0001, M4d; `t2-wifi-network-row.sh` PASS). M4c promoted to recovery
image, M3e retired. Battery: 100% after the charge finish and a few days
off (plausible: off-state drain is small), 85% stored after the T3
session (~50 min of Wi-Fi use), voltage estimate 87–92%: consistent.

Built in the evening of 2026-11-14 while the user ran the M4b discharge.
Image `dist/firmware/test128-m4c-20261114` (raw `ab60ef13…`, p2
`70f7ae82…`; kernel/DTB = M4b); the same files are on the card
(`install-rootfs.sh`, p3 kept). Logs `build/logs/m4c/`.
1. **Frontend from source** (`port/scripts/build-frontend-libs.sh`): the
   C65 frontend source (`build/phase4/frontend-libs/source`) + patches in
   `port/patches/frontend/`, built with the Phase 4 graphics toolchain at
   the C65 path; an unpatched build reproduces the pinned `libmuxmod.so`
   byte for byte (`check`). Only `libmuxmod.so` is taken (module code;
   the lang/config structs in libmuxcom stay pinned).
2. **Wi-Fi toggle** (frontend 0001, worker `radio on|off`,
   `S02network.sh radio`, `settings/network/radio`, missing = on): a
   "Wi-Fi" row first in Connectivity (Enabled/Disabled, left/right/A).
   Without a dongle it reads "Unavailable", dimmed, and can't change
   (`/run/muos/network/adapter`, kept by the worker and the udev hook;
   polled every second). Off: worker down, 8821cu unloaded, Wi-Fi Network
   dimmed and closed; boot, wake and hotplug leave the radio down. CTR:
   737 → 661 mA with Wi-Fi off. Frontend 0003: back from Wi-Fi Network
   lands on its row (not on the toggle).
3. **Web Services** (frontend 0002): only SSH and SFTP are listed
   (decision 7: hide the unported dashboard, mDNS, terminal, Syncthing).
4. **Wi-Fi after wake 18 → 9 s:** CD-ROM settle 10 → 4 s (5, 3 and 2 s
   passed 3/3 wakes each, no H2C error; 4 s = twice the shortest passing
   value; the recorder in `t2-wake-wifi.sh` power-cycles a deaf dongle with
   another sleep); the first scan after a wake covers only the last
   association's channel (`freq_list`, lifted with `set freq_list 0`
   after the association or 5 s; scan 3.9 → 0.5 s). 6/6 wakes in CTR at
   8.5–9.2 s from wake to address.
5. **Warm reboot** (`etc/modprobe.d/8821cu-no-autoload.conf`): after a
   warm reboot the dongle is still `c820`; udev bound 8821cu at ~6 s,
   before the worker's USB reset, and the reset under the bound driver left
   the firmware failing H2C (no AP, recovered by the second attempt after
   90 s; likely the open case (d)). Blacklisted (the worker's explicit
   `modprobe` still loads it): 5/5 warm reboots with Wi-Fi on the first
   attempt, driver at 10.2 s, address at ~20 s uptime, no H2C error.
6. **Boot order:** the worker also waits for S91 (`runtime/ready`):
   before its bind `/opt/muos/config` is p2's default, so the toggle (and
   `network/boot`) read "on" (seen at the first off-at-boot test).
7. **In-game Wi-Fi glyph** (muxretro 0004, M4b T3 item 3): the pause
   menu redraws it each time it opens (it was drawn once at game start).
8. **T2 (all PASS on the card):** `t2-wifi-radio.sh` (off, wake while
   off, unplug/replug while off, on: back in 7 s), menu toggle through
   button injection (left off / A on dimmed Wi-Fi Network blocked / right
   on in 10 s / no adapter: no change), Web Services rows (SFTP toggled
   from the menu), radio off across a reboot (then on: 10 s),
   `t2-wake-wifi.sh` 6/6, 5 warm reboots, `t2-wifi.sh`,
   `t2-wifi-robust.sh`. Shellcheck clean; libmuxmod ELF imports and
   NEEDED as before.

## M4b — Wi-Fi robustness, crash capture, battery capacity (done 2026-11-14, flashed by the user, T3 items 1–5 passed)

**T3 (user, 2026-11-14 evening, after flashing the image):** 1 boot OK;
2 battery 100% before and after the flash (no jump visible at full
charge; FCC reads 2550 on the device); 3 sleep/wake with Wi-Fi OK (the
in-game Wi-Fi glyph stayed "connected" across the reconnect → M4c item
7); 4 replug OK; 5 unplug + scan OK; 6 (charger boot after a flat
battery) and 7 (public image) pending, during the M4b discharge run
(`t2-discharge.sh log-start` + CTR from 96%). The forced panic of the
afternoon: the menu was showing (rebooted by `panic=10`, the dongle deaf
after the warm reboot → M4c item 5).
Item 6 (2026-11-14 night): the CTR discharge ended in a clean
low-battery poweroff at 3% / 3354 mV (dsoc tracked down to the cut-off,
no early cut); the charger boot ~2 h later showed **20%** (fail). The
coulomb counter read 0 (lost), so patch 0005 took the voltage estimate
(3900 mV at +1.6 A → 20%) over the correct stored 3%. Fixed by kernel
patch 0006 (M4d): a lost counter keeps a stored dsoc within 30 points of
the estimate and seeds the counter from it (counter-lost T3 at the next
flat battery). Capacity under CTR load (~750 mA): 1895 mAh counted for
95 → 3% (~2050 mAh usable from full vs ~2450 at menu idle); the counter
still held 470 mAh (18%) at the cut-off: IR drop, not a gauge error.
Retest (kernel 0006, same night): CTR from 24%, clean poweroff at 3%
after 31 min (362 mAh, 701 mA mean); plugged in and powered on at once:
**3%** (pass). But the counter was not lost this time (`now_cap=363`
vs stored 362, `off=0min`): the 0005 tie-breaker (`coulomb 14191 ->
dsoc 2995`, estimate 6%) set it, so 0006's branch is still unexercised.
The counter was lost after ~2 h off the first time: retest = power off
at the cut-off, wait hours, then charger + power on.
Overnight retest (2026-11-15, 4% at 23:59, off ~15 h, charger + power
on): **7%** (pass by the 0–5% / 15–25% bar). The 0006 branch ran this
time (`coulomb counter lost (now=0): kept dsoc 4059 (voltage says
16000), cap 103`), but the 103 mAh seed never reached the counter: Q_PRESS
stayed at about -3260 mAh (bit 31 = "invalid", read as 0), so no charge
was counted, and the first smoothing step booked the 0 → 103 mAh step
as charge (linek 750 × 40/10 = +3000 → dsoc 7059). Cause: the RK817
loads Q_INIT into Q_PRESS on a write to Q_INIT_L0 (0x73), and the BSP's
`regmap_field_write` skips unchanged bytes. Fixed by kernel patch 0007
(M4d): all four bytes written, Q_PRESS checked. T2: counter invalidated
by hand, trial boot logged `seed 793 mAh: q_press fc0283ff -> 00fd4008
(1 write)`, the % then tracked the charge; promoted to main (`d61188f3`).
Side effect of that test: invalidating the counter while charging made
the smoothing count the drop as charge too (18 → 31%, ~8 points high
until the charge finishes).

Built unattended in the afternoon of 2026-11-14 from the M4a T3 findings.
Image `dist/firmware/test128-m4b-20261114` (raw `3737c893…`, p2
`a45a3c4a…`; kernel `4f866b8b`, DTB `bc04b6f8`). Logs `build/logs/m4b/`.
1. **Dongle settle** (worker `usb_mode`): a dongle in CD-ROM mode that was
   powered < 10 s ago (`power/connected_duration`) waits before
   `usb_modeswitch -K`. "mem" sleep cuts its power (it returns as
   `0bda:1a2b` after every wake, also on the charger); a DWC2 unbind/bind
   does not (returns as `c820`). T2: 17/17 wakes with Wi-Fi back, no H2C
   error.
2. **Hotplug** (`usr/libexec/muos-network/hotplug`, udev
   `90-muos-wifi-dongle.rules`): add of `1a2b`/`c820` restarts S41, a
   removal with no dongle back 2 s later stops it and clears the radio
   state; ignored while sleep/resume (suspend.lock), `worker up` or a menu
   command (worker lock) owns the dongle. The worker also resets a radio
   whose interface vanished; retries reset the dongle (rmmod, USB reset).
   T2 `t2-wifi-robust.sh hotplug` (software unplug via `1-1/remove`,
   re-add via DWC2 rebind): stopped, then Wi-Fi back in 18 s.
3. **Own sessions:** wpa_supplicant, wpa_cli, udhcpc and dropbear start
   under `setsid`, so `S99muos-ui stop` (kills the UI's process group)
   no longer takes menu-started SSH/SFTP down. T2 `t2-wifi-robust.sh
   services`.
4. **Wake in a game:** `muos-suspend` resumes the game at once while the
   dongle settles (0.6 s instead of 6 s); the later bring-up costs ~0.7 s
   of slow frames (`t2-stall.sh --wake`, worst 52 ms).
5. **Boot/crash:** S85 waits for a host key only on developer images
   (public boots −30 s); `etc/sysctl.d/90-muos.conf`: `kernel.panic=10`,
   `kernel.printk = 4 4 1 7` (no driver dumps on the screen); S89 mounts
   pstore and moves `dmesg-ramoops-*` to p3 `MUOS/log/pstore/<time>/`;
   S41 appends to `worker.log`.
6. **Battery:** patch 0005's estimate uses 200 mΩ (measured) instead of
   DT `bat_res` 100; DTS `design_capacity` 2500, `design_qmax` 2550 (the
   BSP clamps the stored FCC 3380 to qmax at boot). T1 only.
7. **T2 on the trial root** (all PASS): `t2-wifi-robust.sh`,
   `t2-sleep-cycle.sh 4` and `--game 2`, `t2-wifi.sh`,
   `t2-audio-state.sh`, `t2-menu-cycle.sh`; menu at 16.5 s. Unattended
   guard: p3 user init `zz-trial-guard.sh` (trial root/kernel without
   Wi-Fi for 6 min → reboot = fallback).
8. **Not done:** `write-p2` and the trial kernel were refused by the
   agent's permission check (boot/root writes need the user). A forced
   panic (`sysrq c`, 14:47) to test `panic=10` + pstore left the device
   unreachable: either no reboot on panic or a deaf dongle after the
   warm reboot (STATUS "When you're back").

## M4a — public-image foundations + Wi-Fi menu (done 2026-11-14, T3 passed, item 6 partial → M4b)

Goal: the technical half of M4 (no publication) plus Wi-Fi management
from muOS's own settings menu. Images (version `m4a-20261114` in
`storage-retention.json`): developer `dist/firmware/test128-m4a-20261114`
(raw `deef0ab2…`, p2 `d61fd490…`, private) and public
`dist/firmware/public-m4a-20261114` (raw `193c520f…`, p2 `05d01396…`,
`private=no`). Kernel and boot chain as M3e. Built autonomously in the
night of 2026-11-14.

1. **Wi-Fi from the Connectivity menu** (T2 done): `board/network=1`
   (post-build overrides the pinned 0) shows Configuration →
   Connectivity. Port adapters at upstream's script paths
   (`script/init/async/S02network.sh`, `script/web/{ssid,password,
   service}.sh`) call `usr/libexec/muos-network/worker`, which builds
   wpa_supplicant's config from muOS profiles on p3 (`MUOS/network/*.ini`,
   PSK hex as muxnetprofile saves it, priority, autoconnect, static
   address) plus the developer `network.conf`. DHCP or the static address
   runs from a `wpa_cli -a` hook; no configured network → radio off
   (`/run/muos/network/idle`, muos-suspend accepts it). Connect reports
   upstream's status file and exit codes. T2 (test128, repeatable with
   `port/scripts/t2-wifi.sh`, PASS on the final p2): connect good key
   0 (8 s), wrong key 2 INVALID_PASSWORD (10 s), absent AP 3 AP_NOT_FOUND
   (23 s), each failure back on the previous network in 1–5 s; boot
   autoconnect from the profile; UI driven by `muos-press`: launcher →
   Configuration → Connectivity → Wi-Fi (muxnetwork) → X scan
   (muxnetscan, 11 SSIDs) → profile (muxnetprofile); 3/3 sleep cycles.
   Bugs found and fixed on the way: daemons inherited the command lock
   (fd 8; an SSH session from such a dropbear kept the lock held),
   network ids keep counting across `reconfigure` (select the first
   listed id), COMPLETED must be on the selected id.
2. **SSH/SFTP toggles** (T2 done): muxwebserv's `service.sh apply` →
   dropbear on `web/sshd_port` (22, password, root) and `web/sftp_port`
   (2022, forced `sftp-server`); host key from the private store, else
   created on p3 `MUOS/port/ssh` on first use (T2 with an isolated worker
   copy). Developer images keep key-only :2222.
3. **User init scripts** (T2 done): `S98muos-user-init` runs p3
   `MUOS/init/*.sh` when `settings/advanced/user_init=1` (upstream
   `user_init.sh`; default off). Used tonight for the discharge logger.
4. **Public variant** (T0/T1 done; never booted on purpose): `build-image.sh
   image NAME --public` → no Wi-Fi config, host key or authorized key,
   root password hash (`MUOS_PUBLIC_ROOT_PASSWORD`, default `root`), a
   fresh empty p3 with the base p3's ext4 features and the data marker,
   `private=no`. `check-public-image.sh` (18 checks incl. grepping the raw
   image for the developer's Wi-Fi/SSH values): public passes; the
   developer image fails 6 checks (negative test). `t1-fresh-p3.sh`
   (PASS): the empty-p3 first boot (S90, S91 seeding, S98, worker idle)
   in a rootless qemu container on the Buildroot target.
5. **Cosmetics** (T2 partly): low-battery poweroff stops the UI, writes a
   "Battery empty" picture (`make-battery-splash.py`, raw XRGB in
   `usr/share/muos-r35s/battery-empty.fb.gz`) to `/dev/fb0` via
   `muos-splash`, waits 3 s; `muos-rc stop` redraws it. T2: fb0 holds the
   picture byte for byte after the UI stopped (visibility is T3).
   `info_open/close.wav` high-passed (`wav-highpass.py`, 400 Hz 4th
   order, peak 30000) in post-build (audibility is T3).
6. **Licence groundwork** (report, `pending-licenses.json`): DDR v1.10,
   miniloader v1.12 and BL32 v1.10 are byte-identical to rkbin commits;
   BL31 v1.14 is not. rkbin's LICENSE allows use/copy/distribution.
   libmali: rockchip-linux/libmali is gone; the mirror has only
   bifrost-g31 g24p0 (needs a newer kbase than the 4.4 BSP's r13p0) under
   ARM's Mali EULA (redistribution allowed with the EULA). No
   redistributable userspace for our kbase found.
7. **On test128:** the M4a developer p2 was booted as trial root (T2:
   2/2 in-game sleep cycles, audio PASS), then written to p2 (read-back
   verified; the previous p2 is in p3 `MUOS/trial/p2-previous.img`);
   `t2-menu-cycle.sh` all PASS on it.
8. **Idle discharge run** (2026-11-14 06:21–12:06 UTC, log in
   `build/logs/discharge/`, `t2-discharge.sh log-start`): menu idle,
   backlight 40, mean 389 mA, 94% → 3% in 345 min, survived 6 reboots
   (logger as p3 user init). Clean `critical battery (3%, 3364 mV):
   power off`. Coulomb counter 3172 → 963 mAh = 2209 mAh, host-integrated
   current 2234 mAh (1% apart: the counter is trustworthy). dsoc tracked
   rsoc down to ~3.82 V, then the zero algorithm pulled it ahead (rsoc
   28.5% at the 3% poweroff). **Real capacity ~2530 mAh** (OCV via the
   DT table, start ~88–92%, end ~1–5% for bat_res 100–200 mΩ: 87 points
   = 2209 mAh, ±10% since the table isn't measured for this cell); the
   DT/PMIC FCC 3380 is ~33% too large. Next charge boot: patch 0005's
   lost-counter branch fired (`coulomb counter lost (now=0): dsoc 33000
   cap 1115 from the voltage`, charging at 1.6 A), first sighting with
   the 0005 kernel: **wrong**, real ~3–5% (the user plugged in and
   powered on at once; 7 min later 36% shown vs ~10% real). Cause:
   bat_res 100 mΩ vs ~200 mΩ effective at charge onset, and the stored
   dsoc 2999 was ignored.
9. **T3 (user, 2026-11-14, public image):** items 0–5, 7, 8 OK; 6
   (sleep/wake with Wi-Fi) PARTIAL (→ M4b); 9 OK (developer image
   reflashed, SSH and Wi-Fi checked by the agent). M4a developer image
   promoted to recovery, M3c retired. Wi-Fi dongle findings
   and the +30 s public boot: STATUS "Open problems". Debug aids used
   (temporary, /run only): `wifi-rec.sh` recorder (kernel lines + network
   state to p3 every 2 s; copy in `build/logs/wifi-m4a/`), `panic=10`,
   a worker with a 10 s settle bind-mounted over the original. Bug found: `log-stop`'s `pkill -f` killed its own
   remote shell (the command line named the init script), so the script
   stayed installed; fixed (pkill in its own call), cleanup done by hand.

## M3e — daily-use polish (done 2026-11-14, T3 passed)

Goal: close the M3 items that need no user decision and ship the M3e
image. Image `dist/firmware/test128-m3e-20261113` (raw `7b7c4a66…`, p2
`fd547220…`, rootfs `e7c12aa1…`, kernel `Image-b486b7126df2` = patches
0001–0005), the recovery image since 2026-11-14 (M3b retired; M2 kept as
the image-build base).

1. **Hold-to-repeat** (T2 done): post-build sets `handle_hold` on the
   level combos (as upstream). A 2 s hold moves the level ~10 steps;
   brightness 0 blanks the screen as upstream (the next brightness-up
   restores it). In game: 60.0 fps, 0 missed vsyncs (`t2-level-fps.sh`
   vol-hold / bright-hold).
2. **Menu idle power** (T2 done): Wi-Fi power save (`rtw_power_mgnt=1
   rtw_ips_mode=1`, `etc/modprobe.d/8821cu-power.conf`) 546 → 454 mA;
   ping avg 12 ms / max 92 ms, 20 MB push 3.5 s. The BSP's 408 MHz
   CPU OPP (0.95 V; the vendor DTS deleted it) 454 → 409 mA, 88% of
   menu idle at 408 MHz; games stay ≥ 1008 MHz. T2: NES gate 60.0 fps /
   0 missed; SNES, GBA, MD ~1 missed vsync per minute (as M3d); 2/2
   in-game sleep cycles.
3. **Battery full discharge** (passed 2026-11-14, logs in
   `build/m3e/discharge-20261114`): NES test game, then CTR from 60%
   (`t2-discharge.sh switch`), volume 10. 64% → 4% in 95 min, ~1150 mAh
   (mean 721 mA), no % jumps; 25% at 3441 mV, 10% at 3368 mV; clean
   `critical battery (3%, 3335 mV): power off` (muos-lowbattery).
4. **Image hygiene** (done): p1 without `DIAGnn` / `PROBE.TXT` /
   `tools`; muxretro's provenance and `payload.sha256` describe the
   source build.
5. **M3e image** (T2 done on the trial root): audio before/after PASS,
   level-fps PASS on rerun (see "Frame pacing"), 2/2 in-game sleep
   cycles, long play 2 min each NES/SNES/GBA/MD/PSX PASS (2–3 missed
   vsyncs per game, fps ≥ 59.77, PSX 77 °C).
6. **Gauge after a dead battery** (T2 done, 2026-11-14): after ~7 h of
   charging while off, the boot showed 0% on a full battery: the
   counter came back invalid (0 vs 974 mAh), which the BSP took for a
   halt. The PMIC's OCV sample (3751 mV, from the charger plug-in) was
   stale, and the off timer stays set, so warm reboots recalibrated to
   48%. Kernel patch 0005 adds a current-corrected voltage estimate
   (V − I·bat_res). With it, a lost counter starts from the estimate, and
   an OCV more than 30 points away from it is skipped. Boot sanity resets
   to the estimate when dsoc and the counter are both more than 40 points
   away. T2: the trial boot went 49% → 97% (4.16 V, tail charge), stable
   over 2 reboots on main; audio PASS. Image rebuilt (same rootfs).

**T3 (2026-11-14, all passed).**
- A. Discharge run: clean low-battery poweroff at 3%. The screen just
  goes black, because `muos-lowbattery` calls `poweroff` without the
  frontend's shutdown message (cosmetic).
- B. Boot after the recharge: 0% on a full battery with the old kernel;
  fixed by patch 0005 (step 6).
- C. Flashed without `--grow`: p3 grew on the first boot (116.6 GiB,
  resize2fs rc 0 at 7.1 s), so M3d item 9 is fixed. BIOS, ROMs and saves
  were restored and are checksum-identical. The gauge kept 97% across the
  flash.
- D. Menu at 408 MHz idle as smooth as before; hold-to-repeat in the menu
  and in game; Wi-Fi + SFTP; sleep/wake in game; sound on every boot;
  battery % stable over a power-off and cold boot.

## M3d — smoothness + robustness (done 2026-11-13, T3 passed)

Goal: no visible slowdowns in normal play (the user's bar for the final
build), then robustness for long use. Steps 1–2 are below; steps 3–6 ran
autonomously on the night of 2026-11-13. Image
`dist/firmware/test128-m3d-20261113` (raw `f2692bfa…`, p2 `fd78705a…`),
the recovery image since 2026-11-13.

**Step 3 — volume/brightness judder.** muxretro built from source
(`build-muxretro.sh`: Phase 4 provider source + `port/patches/muxretro/`,
byte-reproducible, pinned from `build/m3d/muxretro/tree`): patch 0001
(per-frame `slow_frames` stage trace), 0002 (in-game level bar drawn by
muxretro: plain panel, bar and recoloured theme glyph; the pause menu keeps
upstream's LVGL bar). WirePlumber `state.restore-props = false` on the sink
(`core-wireplumber.conf`); volume steps through `muos-volume-step` +
`muos-volumed` (resident `pw-cli`, started on the first press; the first
press after boot uses upstream `audio.sh`). T2 gate `t2-level-fps.sh
--max-slow 6 --max-missed 0`: 0 frames > 25 ms per 14 s of presses on
NES/schedutil (was 46–53 vol / 10–35 bright).

**Step 4 — remaining stalls.** Wake: the 8821cu's association busy-waits
in the kernel (PREEMPT_VOLUNTARY) and froze a frame for 80–130 ms; the
Wi-Fi side now runs on CPU3 (network worker, its daemons, `RTW_CMD_THREAD`;
`muos-cpu-pin`, BusyBox `taskset`) and a resumed game on CPU0–2: worst
frame after wake 129 → 33 ms. PSX: pcsx_rearmed on muxretro's core thread,
overlapped with presenting (muxretro patch 0003): CTR attract 8–12 missed
vsyncs per 75 s and 60.0 fps per 5 s window (was 35–108, 53–58 fps); about
one frame more input latency. 2/2 PSX in-game sleep cycles
(`T2_GAME_DIR`/`T2_GAME_ROM` for `t2-sleep-cycle.sh`).

**Step 5 — robustness.** p3 auto-grow on first boot (`muos-grow-p3`, S89:
MBR p3 end before the mount, online `resize2fs` after it, log p3
`MUOS/log/grow-p3.log`; only for disk ID 4d554432 with three partitions);
log size cap (`muos-logcap`, S97: a log over 4 MiB keeps its last 1 MiB as
`NAME.1`). T2 of the grow on a loop-device copy of the layout only (see
item 9 below for what that missed).

**Step 6 — long run.** 51 warm reboots (`t2-audio-state.sh --reboots`:
audio 51/51, slot main, gauge `force0`), 30 of them on kernel 0004, which
held the % every time; one boot read the unsampled OCV (18 mV) and the
guard kept dsoc. An RK817 RTC alarm doesn't power the device on, so cold
boots are T3-only. `t2-long-play.sh --minutes 12` on NES, SNES, GBA, MD and
PSX: all PASS, ~1 missed vsync per minute (capture dump a likely cause),
fps ≥ 59.7, RSS +0–1 MiB, SoC 62–68 °C (PSX 78 °C), PCM throughout.
Battery: patch 0004 (skip OCV calibrations outside 3.0–4.5 V; an
unsampled OCV register read 18 mV on 5/20 warm reboots and became 0%).

**T3 (user, 2026-11-13), items 1–8 on the card before the flash:**
1 cold boot after ≥ 5 and ≥ 30 min off OK; 2 charging reboot OK; 3 drain
OK (gauge logs of the last 4 boots: no correction, dsoc kept, e.g. 81%
after ~50 min off with the counter at 72%, 87% on the charging reboot with
vsoc 99%; saved in `build/m3d/p3-preflash-20261113`); 4 bar OK, but
holding a key changes one step only (upstream repeats; the port's hotkey
JSON lacks `handle_hold` → M3e); 5 volume OK; 6 CTR smooth over 3–4 races,
input OK; 7 wake OK, one small dip left (remove late in the project if
possible); 8 sound on every boot. Decisions: overclock deferred to the end
as an optional user toggle; M3d is the recovery image; M3a.1 retired; from
now on a milestone whose T3 shows no or only small problems becomes the
recovery image without asking.

**T3 item 9 — first flash, p3 auto-grow (2026-11-13): failed, fixed at
T2.** Flashed without `--grow` (raw SHA verified). The first boot wrote
the MBR but the kernel kept p3 at 1 GiB: BusyBox `partprobe` (BLKRRPART)
gets EBUSY while p2 is mounted, which the loop-device test (nothing
mounted) couldn't show. It also broke p3's fsck: udev re-probed p3 after
the MBR write, and blkid found no table entry matching p3's old kernel
size, so `/dev/disk/by-partuuid/4d554432-03` disappeared between S89's
check and `e2fsck` (rc 8; S89 mounted anyway by `/dev/mmcblk0p3`). sfdisk
2.40 only knows BLKRRPART too. Fix: Buildroot `UTIL_LINUX_PARTX`
(`resizepart`, BLKPG_RESIZE_PARTITION, p3 only) after the MBR write, then
`udevadm settle`. T2 on test128 (MBR p3 set back to the flashed 2097152
sectors, ext4 untouched): partition 248561664 sectors at 6.8 s, ext4 online
resize done at 7.6 s, link present, fsck rc 0, 118.5 GiB; the next boot
was a no-op with a clean fsck. The M3d image itself still has the old
script (a fresh card should reach full size on its second boot, not tested; `--grow` avoids
it); the fix ships in the next image.

## M3d step 2 — battery % from the fuel gauge, per-system governors (done 2026-11-13)

**Delivered:** kernel patches 0001 (capacity = RK817 fuel-gauge dsoc),
0002 (boot sanity check dsoc vs coulomb, `muos-gauge:` log), 0003 (BSP
unit fix in the boot calibration); per-system governors (PSX/32X
performance, the rest schedutil); `muos-boost` for volume/brightness keys;
`muos-lowbattery` voltage guard (< 3.5 V). Commits 91c7ff5, 5386632 and
the 0003 commit.

**T3 (user, 2026-11-13, first run):** items 4–6 OK; battery failed (0%
after a reboot, low-battery poweroff) → 0002 + guard.
**Re-test (user, 2026-11-13 night):** 3 (done first) cold boot raised the
% from ~75 to ~80; 2 > 1 h idle in the menu 100% → 81% (~19%/h, matches
the ~560 mA menu draw); 1 (after 3) reboot kept the %; 4 charged to 85%,
rebooted with the charger in → ~95%; 5 sound OK the whole time. Cause of
both jumps: the BSP's force calibration fired on every boot (unit mix,
hardware-findings "Battery %"); fixed by 0003 (T2: a charging reboot keeps
dsoc 99010 with `force=0`; the counter persists). Cold boot is T3-only.

## M3d step 1 — game governor, wake order, panel timing, PSX BIOS (done 2026-11-12, T3 passed)

**Delivered:** `muos-governor` (CPU governor + GPU floor, deep idle, DDR
follow it, as upstream `governor.sh`), games at `performance`; wake resumes
the game after the Wi-Fi radio is up; panel timing 60.0046 Hz (stock
vertical porches) fixed the bottom-rows glitch; the user's PSX BIOS on p3.
T2: NES 59.97, GB 60.00, PSX 58.76–59.8 fps; wake 2–6 missed vsyncs (was
41); sleep-cycle 3/3; boot-slot fallbacks PASS. Commit 638d39a.

**T3 (user, 2026-11-12):** 1 screen OK (no strip ever, incl. cold boot);
2 PSX OK, a little slowdown at the start and end of a race only; 3 wake OK,
"way better than before"; 4 volume/brightness OK (unchanged); 5 battery
PARTIAL: ~15 min of play seemed to take it to ~70%, and a cold boot showed
100% again. Cause: the kernel's voltage-only `capacity` (hardware-findings
"Battery %"), fixed in step 2. The user asked for per-core CPU/GPU profiles
(PSX full speed, NES not) → step 2.

## M3c — ROM library: SFTP, 4 cores, ROM folders (done 2026-11-12, T3 passed)

**Delivered:** Buildroot `gesftpserver` as `/usr/libexec/sftp-server`
(dropbear SFTP; OpenSSH `scp` works without `-O`), `rom-push.sh`; S91
seeds ROM folders (NES GB GBC GBA SNES MD SMS GG 32X PSX) and core
assignments from `core-assign.txt` only where a folder has none;
`build-cores.sh` builds snes9x2005_plus, gpsp, picodrive and
pcsx_rearmed from pinned commits (offline, `-mcpu=cortex-a35`).
Image `test128-m3c-20261112` (raw `64811ce2…`).

**T2:** `t2-sftp.sh` PASS (8–9 MiB/s), regression suite PASS, fps NES
59.90, GB 59.90, SNES 59.92, GBA 59.91, MD 59.93, PSX 59.09 (see M3d:
schedutil). `t2-menu-cycle` no longer touches the user's GB states.

**T3 (2026-11-12, user):** all four items OK:
1. GBA, SNES, MD and PSX start from Explore with sound; the empty GBC, SMS,
   GG and 32X folders show.
2. Pokemon Yellow's battery save survives quit, sleep and poweroff.
3. A ROM copied by SFTP shows up in Explore.
4. Cold boot, NES/GB game and brightness keys: OK.

Observations, all taken into M3d:
- PSX (CTR) had severe slowdowns in its menu and intro cutscene on the
  first run, milder after a restart (cause: schedutil at the 1008 MHz floor,
  plus a CPU-heavy cutscene).
- Slight slowdowns right after waking from sleep, in every game (cause:
  the game resumed during the USB/Wi-Fi bring-up).
- Volume/brightness judder: the user rules it out for a final build.
- During the M3d T2 session: a bottom strip of the screen showing the top
  rows, persisting across a warm reboot (cause: the rk351 panel timing; M3d
  DTB).

**Recovery image:** M3c since 2026-11-12, M3b kept as the previous one.
M1 retired (its content is all in M2).

## M3b — boot chain from source, boot records, trial kernel, TRNG (done 2026-11-11, T3 passed)

Image `dist/firmware/test128-m3b-20261111.img.zst` (raw `2a8fec32…`).

**Reproduced first:** `build-boot.sh kernel-ref` (from scratch, Linaro
6.3.1, read-only linux-base, DTB built outside the tree) and `uboot-ref`
(`uboot-tree.py ref`) rebuild the M2 card's `Image` (`78093582…`), DTB
(`496bbe35…`) and `uboot.img` (`98c62e0b…`) byte for byte. The only
assembly drift was a docs path in a U-Boot DTS comment.

**Boot records instead of compiled-in pins:** the M2 U-Boot pinned the
size and SHA256 of `Image`/DTB, so every kernel change meant a bootloader
write, and its 0xec0000 kernel window had zero headroom (text_offset +
image_size of the M2 kernel = 0xec0000; the M3b kernel needs 0xed0000).
The M3b U-Boot (`muos_boot`) reads records at sectors 32/33/34 (main,
previous, trial; shared `bootrec.c`, CRC32), consumes an armed trial on
the card before trying it, verifies every file, falls through
trial → main → previous, and appends `muos_slot=` (trial: `panic=10`).
Kernel window 32 MiB at 0x02000000, the old window as fallback. Same
U-Boot config as M2 (diffed); `install-dtb.sh` retired.

**TRNG:** the DTB already enables `rockchip,cryptov2-rng`;
`HW_RANDOM_ROCKCHIP=y` alone left `tpm-rng` (no TPM; EIO) as the current
hwrng, because the 4.4 core keeps the first registered one, so
`HW_RANDOM_TPM` is off too. RNG ready at 2.58 s (was 7–11 s), no
"uninitialized urandom read" warnings. `Module.symvers` unchanged: the
pinned modules stay valid. Time to the UI is unchanged (~16 s).

**T0/T1:** `t0-boot.sh`: 19 U-Boot scenarios against mock U-Boot APIs
(ASan/UBSan: trial once and consumed before booti, bad/stale/oversized
files, corrupt records, window fallback, booti returning, no records);
record codec: C and Python encoders byte-identical, cross-decoding, all
512 single-byte corruptions rejected. ASan caught two harness bugs, none
in `boot.c`. Image stage: p1 `fsck.fat`, records and U-Boot read back.

**T2 (device):** new p2 via the trial root (audio, 3 sleep cycles); M2
records written; U-Boot written and read back (old region saved on p3);
first boot `muos_slot=main`. Trial kernel boots once with `panic=10`; the
next boot is main again; after the TPM fix the TRNG is current and
survives 5 sleep cycles; promoted. On hardware: corrupt main record →
previous; bad-SHA trial → consumed → main (`t2-boot-slot.sh` 4/4). Suite
on the M3b kernel: `t2-menu-cycle` 11/11, `t2-sleep-cycle --game` 3/3 and
5/5, `t2-headphone` PASS, NES 59.89 fps, audio soak 6/6 boots (one second
S95 attempt).

**T3 (2026-11-11, user):** 3 cold boots with sound, games, brightness
and in-game sleep/wake: OK. The M3b image was flashed with the host USB
card reader (`flash-card.sh host /dev/sdb … --grow`, its first real use):
`verified raw_sha256=2a8fec32…`, `p3 grown and clean`, cold boot to the
menu with sound. M3b became the recovery image; the reader is the primary
flash method (dArkOSen stays the fallback). Afterwards: the pre-flash
`pickles` restored byte-identical; `flash-card.sh host` now accepts only a
USB/removable/MMC whole disk and asks before writing (the host also has an
internal SATA `sda`).

**T3 observation: fps drops while changing volume/brightness in game.**
Measured with the new `t2-level-fps.sh` (keys injected through
`muos-press volup|voldown|fn+vol*`, i.e. the real muhotkey path); see
hardware-findings.md "Level-change judder". Upstream behaviour, not
fixed. The investigation found and fixed two test hazards: a T2 game run
autosaves on exit and replaced the user's state (`t2-game.lib.sh` now
snapshots and restores the ROM's pickles), and replacing
`MUOS/pickles` by rename leaves the `/run/muos/storage/pickles` bind on
the deleted directory (copy in place instead; `device.sh push` no longer
keeps the host uid).

## M3a.1 — audio regression fix (done 2026-11-11, T3 passed)

**M3a T3 (2026-11-11):** the built image flashed via dArkOSen (`verified
raw_sha256=2ac44673…`, `p3 grown and clean`) and boots: it is a working
recovery image for boot. Games, brightness and sleep/wake OK. **No sound
on any boot**, speaker or headphones, before and after the flash; the
headphone retest could not be judged. Battery showed 91% after a full
discharge with the charger in (→ M3d, see STATUS).

**Root cause:** muOS runs every SDL client with `SDL_AUDIODRIVER=pipewire`,
and the Buildroot-built SDL2 had only `alsa dsp disk dummy`, so
`SDL_Init(AUDIO)` failed ("Audio target 'pipewire' not available") and
nothing opened the PCM. Buildroot's pipewire depends on sdl2 (examples),
so a clean build configures SDL2 before PipeWire is in staging, and
SDL2's configure silently drops the driver. The Phase 4 tree had
PipeWire installed when SDL2 was built. Two traps on the way:
- `sdl2-reconfigure` is not enough: with `--disable-dependency-tracking`
  `SDL_pipewire.o` is built but the driver table in `SDL_audio.o` stays
  stale. `sdl2-dirclean` + `all` works.
- String checks on the library (`libpipewire-0.3.so.0`) pass on that
  stale build; only asking SDL for its registered drivers is reliable.

**Fix:** `build-image.sh build` runs the new
`/usr/libexec/muos-sdl-audio-probe --require pipewire` (package
`muos-sdl-audio-probe`) under qemu against the target, rebuilds SDL2 if
needed and fails if it still lacks the driver; `image` repeats the qemu
check and `check-rootfs-contract.sh` checks the p2 image. SDL2 is back to
M2's size (1412240 bytes). The same ordering cost ffmpeg's SDL2 output
device (libavdevice −8 KB); nothing uses it. Lesson for inventory diffs:
a "rebuilt" ELF that shrank is a lost feature until explained.

**T2 probe:** M3a's probe printed `pcm=closed rate=0` and passed by eye.
`t2-audio-state.sh` now prints a verdict and exits non-zero unless the
PCM is RUNNING at 40–50 k frames/s, a PipeWire output stream exists, this
boot's audio log has an `SDL Init Success` and no failure, and a fresh SDL
client opens `pipewire@44100`. `t2-menu-cycle.sh` runs it in the menu
and in the game. Negative proof on the live silent M3a boot: `FAIL audio:
pcm=closed rate=0 no-stream sdl=fail15`.

**T2:** trial root: audio PASS, `t2-sleep-cycle` 5/5 (audio PASS after),
`t2-headphone` PASS, `t2-menu-cycle` 11/11 (menu 44.1 kHz, game 48 kHz).
p2 written from the trial root, read back `1b3995a2…`. New p2: audio
soak 6/6 boots PASS (one second S95 attempt), `t2-menu-cycle` 11/11,
`t2-sleep-cycle --game` 3/3, `t2-headphone` PASS, NES SMB3 59.90 fps.
Image `dist/firmware/test128-m3a1-20261111.img.zst` (raw `112db539…`).

**T3 (2026-11-11):** sound on 3 boots, speaker and headphones; the volume
keys work. Headphones: fully inserted is not detected (the speaker keeps
playing) and only some frequencies drop: hardware, see STATUS. Per-output
volume is shared at T3 (no jack event); the user deprioritized it.

## M3a — reproducible image + e2fsck (T2 done 2026-11-11; T3: flashes and boots, silent → M3a.1)

Commits `e7d67a2` (build, trial root, e2fsck), `76d9aec` (script
retirement). Image `dist/firmware/test128-m3a-20261111.img.zst`.

**Disk first:** retired the synthetic capture fixtures and the unused
Mali SDK libs, then (user decision) the Phase 4 raw card captures and all
non-project podman images: host free space 61 → 68 GiB before the build,
62 GiB after it (`build/m3a/output` 9.8 G); podman images 15.0 → 4.6 GB.

**Inventory** (3462 p2 paths, sha256 per file, via a bind mount of `/` so
S90/S91 binds don't hide p2 content): all but 6 files were in the port
overlay or byte-identical to a host build output. Final diff of the
built target against the live p2: 3204 identical, 57 overlay, 90 rebuilt
ELFs (plus the user tables, completed at image time), 9 symlink/file
swaps (e2fsprogs replaces BusyBox links; proper library symlinks), 73
new (e2fsprogs, libs, jimtcl), 12 removed (Buildroot's S50dropbear, the
usb_modeswitch udev dispatcher, ifupdown/wpa defaults, hwdb sources,
PipeWire raop/ffmpeg plugins) and 101 dropped (C-step probes, legacy
session/save-store packages, the M1 backups, trial and seed state).
Seven tuned files under `/opt/muos` and `/etc/default` (audio path
`SPK_HP`, the C30 WirePlumber settings, input on, the saved
`asound.state`, ...) differ from the package defaults; the live content
is pinned.

**Build:** the cross toolchain and all packages from scratch in about
50 min (16 jobs). One fix: the container exported `TARGET=all`, which
muinput's Makefile (`TARGET ?= muinput`) picked up; variables are now
`M3A_*`.

**T1:** `t1-shim.sh` (no marker, trial, failure at each of 8 steps
before `pivot_root` → p2, marker consumed); `t1-elf-deps.sh`: 320
dynamic ELFs resolve with the target ld.so under qemu; e2fsck 1.47.2,
jq, dropbear, wpa_supplicant run. Image: fsck clean, label ROOTFS,
4.4-safe features, dbus/pipewire users, BusyBox 04755, identity copied
(byte-compared).

**T2 on the trial root:** boot to menu (rc done 16.6 s, all services
rc=0), `t2-sleep-cycle` 5/5, `t2-headphone` PASS, audio probe healthy,
NES SMB3 59.91 fps; `t2-menu-cycle` 7/8: the only failure was "p3 needed
journal recovery", expected because the trial root runs from p3.
**p2 written** from the trial root in 2 m 43 s, read back
`a21a4186…`; old p2 saved (`d5d9a5b6…`).

**T2 on the new p2:** `t2-menu-cycle` 9/9 (p3 clean after the reboot),
`t2-sleep-cycle` 10/10, `t2-headphone` PASS, NES 59.90 fps; 6-reboot
soak: audio up on 6/6 (one second attempt), `e2fsck -p rc=0` every boot;
the first boot after the trial replayed p3's journal in 0.16 s.

## M2.1 — battery indicator, per-output volume, audio start retry

Done 2026-11-11 (`8114513`, installed in place on the M2 card).

**Fixes:**
- **Battery indicator:** the Phase 3 staging profile shipped
  `visual/battery=3` (hidden). The rootfs default and the staging profile
  are now `2` (upstream: icon + percent). S91 migrates an existing p3
  config once (`MUOS/port/.migrations`).
- **Per-output volume:** `muos-headphone` does upstream's
  `SWITCH_OUTPUT_VOLUME` (`/run/muos/headphones` flag +
  `SAVE/LOAD_SINK_VOLUME`), so each output keeps its own level.
- **Silence after boot (root cause found):** on some boots WirePlumber's
  ALSA device enumerates no profile (empty `EnumProfile`, no sink).
  Upstream S80pipewire gives up after its 3 s node budget, and S95 then
  ran the whole boot silent. Caught live on 2 of 13 warm reboots; two bad
  boots in a row look like "reboot didn't fix it". It's not codec state:
  the RK817 playback registers and the 44.1 kHz PCM rate were identical
  across reboots and 5 sleep cycles (`port/scripts/t2-audio-state.sh`).
  - S95 now retries the full audio start (prime + S80 + sink wait) up to
    3 times within 25 s, records `/run/muos/core/audio-attempts`, keeps
    each failed attempt's `pw-dump`, and writes a codec/PCM snapshot to
    p3 `MUOS/log/system/audio-codec.txt` every boot.
  - Soak (15 warm reboots): audio up on 15/15; 2 needed the second
    attempt, none a third.

**T2:** `t2-headphone.sh` PASS (plug → HP with its own level, unplug →
speaker level restored, replug → HP level restored); 15-reboot audio soak.

**T3 (2026-11-11, `build/t3-m21.txt`):**

| # | Check | Result |
|---|---|---|
| 1 | Battery icon + % | OK |
| 2 | Charging icon | OK |
| 3 | % drops while playing | OK. Observation: 84% → 100% within about 20 s of plugging the charger |
| 4 | Per-output volume | FAIL as seen: speaker and headphones shared one level |
| 5 | Sound on 3 boots | OK |

**Analysis of the observations** (done after T3 over SSH):
- **Item 4 is a jack detection problem, not a volume logic problem.**
  muOS writes an output's level file on every volume key press. The
  headphone slot (`share/volume/48dc3513`) was last written at 02:31 UTC,
  during the T2 run and before the M2.1 commit at 02:46. During the T3
  session only the speaker slot changed (03:08). So the jack never
  reported "inserted" while the volume was being changed. The user found
  that the plug sounds right only when partly inserted; in that position
  the detect contact is open, the path stays `SPK_HP`, and both outputs
  share one level. A full insertion is detected (M2 T3 item 7). It gets
  retested at full insertion in the next T3.
- **Headphones quieter when fully inserted: hardware**, as the user
  suspected (same on ArkOS). The RK817 registers 0x12–0x4f under the
  `HP` and `SPK_HP` paths differ only in `ADAC_CFG1` bit 2 (class-D DAC
  power). The HP opamp setup and the digital level (`DDAC_VOL` 0x0a) are
  identical: this kernel is built with `ARCH_ROCKCHIP_ODROIDGOA`, so the
  path switch doesn't apply the DT `hp-volume`. The M2 "HP much quieter"
  report has the same cause.
- **Battery jump on charge:** the % is the RK817 BSP fuel gauge's
  `capacity` (mubattery passes it through: sysfs 88 = `/run/muos/battery`
  88). The gauge re-estimates when charging starts. Calibration (DT OCV
  table, or muOS's voltage-curve mode) is deferred to M3d.
- **Lost evidence:** the per-boot logs of the plug test were overwritten
  by item 5's reboots (S91 kept one previous boot). S91 now keeps three
  (`MUOS/log/system.prev`, `.prev2`, `.prev3`).

**M2.1 T3 checklist (done):**
1. Battery indicator top-right: icon and %.
2. Charger in, about 10 s: charging icon; out: normal.
3. Unplugged, play 10–15 min: % drops a few points.
4. Headphones in, raise the volume, unplug: speaker back at its own
   level; replug: the HP level is back. If 100% is too quiet, try
   Overdrive.
5. Power cycle or Reboot 3 times: sound in the menu every time.

## M2 — power, battery, cpufreq

Done 2026-11-11 (`03aa053`, `925c7bd`, `0154772`, `af33e99`). Image:
`test128-m2-20261111.img.zst`.

**What it added** (details in procedures.md "Boot and runtime"): upstream
Power-key sleep/resume, the shutdown timer, charging fake sleep, the
battery service and low-battery poweroff, the headphone path follower,
writable cpufreq with per-content governors. The 1512 MHz DTB was tried
and reverted: the port U-Boot pins `Image` and the DTB.

**T2 (2026-11-11):**
- **NES fps.** Measured by `port/scripts/t2-nes-fps.sh` with muxretro's
  own frame-time capture (`MUXRETRO_PERF_CAPTURE`; the "Content rate" log
  line is audio-derived, not fps), 60 s after a 10 s warm-up:

  | Run | ROM | fps | frame / core / present ms | CPU, governor |
  |---|---|---|---|---|
  | before (cpufreq ro) | Super Mario Bros. 3 (MMC3) | 59.90 | 16.69 / 5.88 / 10.60 | 1296 MHz, performance |
  | after (writable) | Super Mario Bros. 3 | 59.89 | 16.70 / 7.09 / 9.35 | 1296 MHz, schedutil |
  | before | r35s-flight (MIT demo) | 51.61 | 19.38 / 13.47 / 5.70 | 1296 MHz, performance |
  | after | r35s-flight | 51.56 | 19.40 / 13.50 / 5.69 | 1296 MHz, performance (muxretro boost) |

  A real game runs at full speed (vsync-locked to the 59.94 Hz panel).
  Only the synthetic demo ROM is slow; the old C47 "51.4 fps" figure was
  that ROM. Writable cpufreq doesn't change fps; the menu now idles at
  1008 MHz.
- **Sleep:** 20/20 Power-key cycles (`port/scripts/t2-sleep-cycle.sh`;
  injected press, `mem`, RTC wake), 3 in game (auto-save, pause, resume
  on SIGUSR2). Each cycle: backlight restored, Wi-Fi/SSH back first try.
- **Charging fake sleep:** screen off, frontend stopped; a second press
  wakes it.
- **Battery:** `/run/muos/battery` 100%, 4150 mV, charging=1. The
  low-battery logic (overlay, clean critical poweroff) passed at T1.
- **Regression:** `t2-menu-cycle.sh` 9/9.

**T3 (2026-11-11, `build/t3-m2.txt`):**

| # | Check | Result |
|---|---|---|
| 1–3 | Physical Power short/long press, in menu and in game | OK |
| 4 | Shutdown timer after 10 min asleep | OK |
| 5 | Charging | PARTIAL: fake sleep OK (instant wake, dongle stayed on); no charging icon → M2.1 |
| 6 | Battery % | NOT TESTABLE: no indicator in the status bar → M2.1 |
| 7 | Headphones | OK polarity; HP much quieter than the speaker (hardware, see M2.1) |
| 8 | NES SMB3 | OK |
| 9 | Hard power cut | OK |
| — | Observation | No sound after the hand-over; a menu reboot didn't fix it, a hard power cut did → M2.1 |

**M2 T3 checklist (done):**
1. Short Power in the menu: dark within 2 s; again: menu back within 3 s,
   Wi-Fi/SSH back.
2. Power in a game, wait 20 s, Power: the game continues with sound.
3. Hold Power about 1 s: same sleep (upstream behaviour). ≥ 6 s is the
   PMIC hard cut.
4. Unplugged, sleep for more than 10 min: clean poweroff; next boot has
   the GB save.
5. Charger in: charging icon; Power gives fake sleep, Power wakes.
6. Unplugged, play 10 min: % drops plausibly.
7. Headphones in: sound only there; out: back on the speaker.
8. NES SMB3 for 2 min: full speed, clean audio.
9. Optional: hard power cut in game, boot: the menu and the last save.

## M1 — recovery image, autostart, seedless init

Done 2026-11-10. Image: `test128-m1-20261110.img.zst`.

**Delivered:** a flashable recovery image; boot straight into the muOS
frontend through standard BusyBox rcS/rcK-style init; retirement of the
C-step safety harness.

**T2:**
- Autostart to the menu on more than 15 boots of the new init, one of
  them seedless; rcS done at about 15 s.
- `port/scripts/t2-menu-cycle.sh` passed 4 times in full, driving the
  real buttons by evdev injection (`/usr/libexec/muos-press`): menu →
  Explore → GB → private.gb at 59.73 Hz; Fn+R2 quick save (to p3) and
  Fn+L2 quick load; Fn+Start → Explore; launcher Reboot → ordered rcK →
  p3 clean → state persisted → menu.
- Prefs: 55/70 imported into the persistent config.
- Degraded audio: if audio fails to start, the menu still works.
- Panel timing measured (hardware-findings).
- T0/T1: shellcheck on all new scripts; container tests for the
  installer, the trial boot, the frontend loop and the file-target flash;
  fsck and content checks of both images; a p3 grow test; AST import
  check of all 425 kept Python files.

**T3 (2026-11-10).** The first flash attempt failed at verification
(dArkOSen's sudo PATH has no sbin; fixed in `9bf8f80`); the rerun
verified the card and grew p3 to 116.6 GiB.

| # | Check | Result |
|---|---|---|
| 1 | Flash via dArkOSen slot 2 | OK |
| 2 | Cold boot to menu | OK (menu at ~15.5 s) |
| 3 | GB save/load/quit | OK |
| 4 | Menu reboot, persistence | OK. Relaunching resumed the last state without Fn+L2: muxretro's default `auto_save=3` (idle + quit) writes `autosave.state` on quit and loads it at the next launch. Expected muOS behaviour. |
| 5 | Menu shutdown, power on | OK |
| 6 | Power key / speaker | OK |

**M1 T3 checklist (done):**
1. Flash the M1 image via dArkOSen: `verified raw_sha256=1c65c693…`,
   `p3 grown and clean`.
2. Cold boot: the menu without any SSH step in 15–25 s.
3. GB: play, Fn+R2, move on, Fn+L2 → back at the save; Fn+Start → list.
4. Menu Reboot: volume/brightness unchanged; the state still loads.
5. Menu Shutdown: screen off within 5 s; power on → menu.
6. Optional: Power key (nothing yet), speaker sound.

**Seed investigation.** The "seed" was the SeedRNG entropy file
(`/var/lib/muos-seedrng/seed.*`), created by Buildroot's seedrng through
the C05 `S05muos-entropy` wrapper. Only the network script's "RNG ready"
gate depended on it (so dropbear's host key was generated with a ready
RNG; readiness takes 7–11 s on 4.4 with no HW RNG). The "never replay"
rule protected RNG freshness across p2 restores, which doesn't matter on
a dev card. Decision: retire the gate and the wrapper; stock seedrng
still runs; images ship without `seed.*`; the dropbear host key stays in
the image so the fingerprint survives a reflash.

**Retired in M1:**
- Card/CID guards: the C01/C07 bootstrap and `card-guard.sh` (they broke
  every flashed copy and halted with original32 in slot 2).
- Marker files: `/etc/muos-*-diagnostic`, `/etc/muos-private-foundation`,
  `DIAG.ID` checks.
- The boot-seq counter and `.once` tokens (`/var/lib/muos-diagnostic`).
- Consumed claims (host-only).
- Hash guards: foundation-89, "guard 200", the resident/batch manifests,
  the hash-pinned retention dependency trace.
- Seed/counter anti-replay and "never write test128".
- Device payloads: the C01–C25 dispatchers, capsules, caller, batch and
  resident packages, the UI supervisor, MUOSSAV1 `muos-save-store`,
  `S05muos-entropy`, `S98muos-session`. A tar is on p3 at
  `MUOS/port-legacy-c07.tar`; the baseline image keeps them all.
- Host: 223 one-off C-step scripts and fixtures; they stay in Git at
  `ea2f7d8`.

**Contradictions resolved in M1:**
- Panel timing: the port DTB is 29 MHz / 732×661 / 59.94 Hz (measured
  three ways); the stock dArkOSen DTB is 50 MHz / ≈61.2 Hz. The two docs
  described different DTBs.
- The roadmap marks Phase 4 done and Phase 5 in progress.
- Warm Wi-Fi: fixed since C18; the "replug needed" archive notes are
  historical.
- The C123 guard is obsolete (guards retired).
