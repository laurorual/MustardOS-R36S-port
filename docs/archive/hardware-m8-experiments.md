# M8 heavy-system experiments (archive)

Moved from [hardware-findings.md](../hardware-findings.md) on 2026-11-25;
the summaries stay there. Logs: build/logs/m8f/thermal, build/m8g.

## Thermal block, undervolt, overclock, charging

  - *M8 thermal block (`t2-thermal.sh`, DC Power Stone 2 fight with the
    user's per-game options, 8 min on battery from 55 °C, minute 1
    skipped; speed = core audio frames/s, logs build/logs/m8f/thermal):*

    | run | °C | CPU MHz | mA | speed | s < 95 % |
    |---|---|---|---|---|---|
    | stock (cap 1296) | 79.3 | 1234 | 811 | 94.7 % | 159 |
    | cap 1200 | 77.4 | 1195 | 781 | 96.5 % | 129 |
    | CPU+GPU −50 mV | 75.9 | 1296 | 758 | 97.0 % | 102 |
    | CPU+GPU −75 mV | 74.8 | 1296 | 741 | 97.2 % | 98 |
    | CPU −50 mV only | 78.9 | 1279 | 823 | 96.1 % | 122 (battery 20→9 %) |

    The DC "random frame skipping" is throttling: per second, at 1008 MHz
    the game runs 88 % (52 of 75 s below 95 %), at 1296 97 %. What stays
    below 95 % at a steady 1296 is heavy scenes. Undervolt trial DTBs
    (`make-dtb-uv.sh`: CPU OPPs ≥ 1008 MHz and GPU OPPs, target = min =
    table − N mV): the real vdd_arm at 1296 is the table −25 mV
    (`rockchip,evb-irdrop`), so stock runs 1325 mV, −50 runs 1250 mV.
    This chip: bin 0, leakage 19, pvtm-volt-sel 2. **GPU (vdd_logic)
    undervolt is unstable in PSP** (PPSSPP v1.12 God of War: −75 and −50
    mV both give Mali "GPU fault 0x4002" / job hard-stops, 6–55 faults,
    freezes of 8–17 s; DC was clean for 8 min at −75). CPU −50 mV with the
    stock GPU table: PSP 4 min clean (12.3 presented fps vs 11.6–11.9
    stock), DC clean. **CPU −50 / GPU −25 mV** (`uvc50g25.dtb`, sha
    84611ef0394d): PSP 5 min clean (12.4 fps, worst gap 170 ms vs 174–189
    stock), DC 8 min clean: the candidate for this unit. Other units may
    have less margin (do not assume; bin/leakage/pvtm differ).
  - *Overclock does not help DC on battery (M8g, CPU −50 / GPU −25 mV
    DTB, `t2-thermal.sh --cap 1512000`, logs build/logs/m8f/thermal/oc1512):*
    1512 MHz holds for ~3 min, then the SoC sits at 81–83 °C and the
    power allocator trades CPU (mean 1414 MHz, dips to 1008) against the
    GPU (400–520 MHz): 95.6 % speed, 154 s below 95 % vs 97.0 % / 102 s at
    a steady 1296. The minutes that are slow at 1296 (heavy scenes) stay
    slow. The 1296 cap with the undervolt is the DC optimum on this unit.
    Since M9 the undervolt is a menu opt-in (Danger Settings →
    Undervolt), stock voltages by default.
  - *Overclock does not help PSP either (M8g, God of War v1.12.3 state,
    300 s from 60 °C, `build/m8g/t2-psp-oc.sh`):* cap 1296: 12.6 presented
    fps, CPU mean 1065 MHz, max 84.2 °C (it throttles at the stock cap
    already); cap 1512: 12.3 fps, mean 1024 MHz, 83.8 °C. On this unit
    the heavy systems are held by heat, not by the clock cap: no game
    overclock (M8 item 18 closed). Gains for PSP need less work per
    frame (emulator, settings, a newer kernel/GPU driver), not MHz.
  - *Flycast 2022 DSP off (M8g, `reicast_enable_dsp=disabled` per game,
    1296 cap): 96.7 %, 121 s below 95 %:* no gain; the slow minutes are
    the same scenes in every run (minute 2 ~92 %, minute 7 ~95 %). The
    residual DC dips are game content beyond the RK3326 at 640x480, not
    heat (frame skipping 1 or 320x240 would hide them, both rejected).
  - *Charging during play is the biggest heat source:* the same DC run on
    the 2 A adapter (battery charging at ~1.3 A) with CPU −50/GPU −25:
    81.5 °C, CPU down to 408 MHz, 93.5 % speed, 179 s below 95 % (worse
    than stock on battery). The RK817 charge current (CHRG_CUR_SEL) and
    input limit (USB_ILIM_SEL) written at run time through a test
    module_param (dmesg confirmed the writes) changed nothing measurable:
    even 450 mA input kept the battery charging at ~1.2 A, so the path is
    not limited by those fields on this board (the patch was dropped).
    Heavy systems: play on battery.

## PSP

- **PSP performance (M8 T3 fixes, `t2-psp-fps.sh`, God of War CoO from a
  fixed state, presented frames by swapstat):** CPU-bound and thermally
  limited. At a fixed 1008 MHz: v1.20.4 11.1 fps, v1.12.3 13.0 (+17 %);
  BloomHack 3 and a 400 MHz GPU cap change nothing; resolution Auto (2x
  on 640x480) is slower than 1x. At the 1296 cap the soc zone's
  power_allocator (750 mW, the same in the stock DTB) holds the CPU at
  ~900–1150 MHz after a minute (82–83 °C). FrameSkip 1 roughly doubles
  the emulated rate: v1.12.3 15.5 presented = ~31 emulated fps (GoW's
  30 Hz, full speed) at 1146 MHz. The two versions' states are not
  compatible (each its own memory stick, SAVEDATA shared).
  M8 T3 4 (God of War "graphics problems"; screenshots by
  `t2-swapstat.sh grab`): dArkOSen's v1.12 ini has `RenderingMode = 0`
  (non-buffered): no sky and no post-processing in GoW. Buffered costs
  ~8 % at a fixed CPU clock (6.1 → 5.6 presented fps at 408 MHz); GPU
  skinning and a 222 MHz emulated CPU change nothing. Unpinned runs on
  the charger are dominated by heat (CPU averages 600–1000 MHz at
  82–84 °C), so compare settings at a fixed cap.

## Dreamcast and Saturn

- **Dreamcast:** libretro/flycast is now the parallel_dc fork: with the
  real BIOS it still never shows a frame (the CPU thread spins). Flyinghead
  Flycast v2.7 (libretro, GLES 3.2 on the Mali) boots Power Stone 2: 36–43
  fps in the attract loop (core 14–17 ms, present ~10 ms).
  M8 T3 (Power Stone 2 "not playable", `t2-dc-fps.sh`): v2.7 waits for
  the GPU (synchronous rendering), so a heavy fight runs in slow motion
  (user's mid-fight state: 38 ms frames, ~44 % game speed; dArkOSen's
  standalone emu.cfg options made it worse, 50 ms). dArkOSen's default is
  the libretro Flycast of April 2022 (libretro/parallel-dc `4c293f3`,
  dArkOS goadvance build: LOW_END/LOW_RES defaults: 320x240, per-strip
  sorting, DSP off, no synchronous rendering): attract loop core 6.5 ms vs
  11.6 ms on v2.7; game logic at full speed, rendered frames dropped when
  the GPU lags (~30 shown). Shipped as `flycast2022_libretro.so`, the DC
  default; v2.7 stays as "Flycast". Its states differ (per-core state
  directories, no cross-loading).
  M8c T3 7 (uneven speed, half resolution; user's fight state, 60 s,
  `t2-dc-fps.sh`): the core is not the limit (4–6 ms); 640x480 internal
  costs nothing over 320x240; `reicast_framerate=fullspeed` alternates
  16/33 ms pictures (felt as speed changes) with audio underruns, `normal`
  shows a steady 30 at 60 emulated fps; synchronous rendering shows ~59
  but emulates 53 (slow motion). Defaults since m8d: 640x480 + normal.
  M8d T3 4 (still fast in the BIOS and Capcom logos, slow mid-fight;
  measured with `t2-coremeter.sh`, the core's audio frames per second =
  real game speed): Flycast renders threaded, so its emulation thread is
  paced only by the audio it pushes, and muxretro's Speed Limiter (audio
  backpressure, a muxretro setting) is off by default: the queue grew to
  ~830 ms (0 backpressure waits) and the game ran 108-123 % after every
  slow patch, 100 % then 86 % in the attract loop. Speed Limiter on (core
  settings `pickles/settings/core/flycast2022.ini`, migration
  m8e-dc-limiter): queue ~30 ms, no bursts above 103 %, the user's fight
  100 % at ~52 pictures/s even at 1008 MHz; heavy attract scenes still
  ~86 % (frame skipping 1: 100 % at ~28 pictures/s, not the default).
  Threaded rendering off hangs the 2022 core (no audio, no frames).
- **Saturn:** YabaSanshiro libretro with `saturn_bios.bin` runs Sonic R at
  ~21 fps (core 44 ms per frame); in the race 18.6 of 60 emulated fps.
  Standalone (dArkOSen's retro_arena build, low-res, SH2 cache off,
  frame skip on): title 23–24 fps, intro/race 10–20 pictures/s, CPU
  thermally held at 1008 MHz (81–83 °C), main thread ~55–65 % of a core.
  Needs `-r 3`; reads an EmulationStation input list (input.cfg) and
  writes keymapv2.json once; quits on SIGTERM (~1 s).
  M8d T3 5/6 (slow, Select closed the game), our patches in
  `port/patches/yabasanshiro-sa`: (1) it never set a swap interval, so
  SDL's KMSDRM queued asynchronous page flips, which this kernel refuses
  (~30 "Could not queue pageflip: -22" a second: frames dropped or drawn
  into the scanned-out buffer); now `SDL_GL_SetSwapInterval(1)` (the
  emulator paces itself, SDL triple-buffers). (2) The menu crash
  (`glnvg__renderFill`, also the SIGSEGV on quit): nanogui compiled its own
  older nanovg (renderFill without the compositeOperation argument)
  against src/nanovg's newer nanovg.c, so every menu fill ran with shifted
  arguments; the build copies src/nanovg over nanogui's. (3) The SCSP
  "realtime" thread's Linux wait passed `ctime()` as the deadline
  (EINVAL at once): a real CLOCK_REALTIME deadline now. Speed (emulated
  fps by `MUOS_YABA_FPSLOG`, Sonic R race): 20-25 of 60 at 1008 MHz
  (81-83 °C), with frame skip on. The limit is the sound thread (68K +
  SCSP in real time, ~100 % of a core, ~21 waits/s = it never keeps real
  time; the SH2 thread ~65 %, VDP ~60 %): C68K instead of Musashi
  (`MUOS_YABA_M68K=1`, built in) is within the noise. Light 2D games are
  untested (no ROM).
