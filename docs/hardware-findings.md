# Hardware findings — R35S, Panel 0

These are durable technical facts consolidated from the Phase 1–4 reports.
Sources are given as `(file)` and refer to [archive/phase4/](archive/phase4/).
Current state and progress are in [STATUS.md](STATUS.md).

Where two documents disagree, the entry is marked **⚠ Conflict** and left
unresolved.

Everything below was measured on **one unit**, so it does not prove anything
about other R35S/R36S panels or revisions.

## Device identity

- **SoC and model:**
  - Genuine RK3326 (Cortex-A35, AArch64).
  - DT model `R36S-V12 2023-08-18 Panel 0`, compatible
    `rockchip,rk3326-odroidgo3-linux`.
  - (phase1-muinput.md, compatibility-matrix.md)
- **Stock bench system:**
  - dArkOSen Debian 13.7 (trixie), glibc 2.41.
  - Kernel `4.4.189 #1 SMP`, Image SHA256 `31bdb671…b0577`.
  - Boot cmdline includes `max_cpufreq=1512 boot_cpufreq=1296`.
  - (phase1-muinput.md)
- **Memory:**
  - MemTotal is about 916.9 MB: 916920 kB on the diagnostic kernel and
    916904 kB on the monitor.
  - RAM banks are 0x00200000–0x08400000 and 0x0a200000–0x40000000.
  - (phase4-linux-diagnostic.md, phase4-memory-monitor.md)

## Display

- **Panel:**
  - Panel `elida,kd35t133`: DSI with 4 lanes, RGB888, 640×480, mode flags
    0xa03.
  - The 370-byte init sequence (SHA256 `972f6148…1a91`) is shared by the
    U-Boot and Linux DTBs.
  - (compatibility-matrix.md, phase4-uboot-panel.md)
- **Linux DRM mode (measured):**
  - CRTC 60, 640×480, pixel clock 29000 kHz, htotal 732, vtotal 661,
    59.935683 Hz.
  - That clock and totals imply h 46/2/44 and v 165/2/14.
  - The mode is identical before and after each test, because SDL restores
    the CRTC.
  - Connector DSI-1, `/dev/dri/card0`.
  - (phase4-native-graphics.md, phase2-display-input.md)
- **U-Boot DTB timing:**
  - 50 MHz, h 450/70/450, v 17/5/13, prepare/reset 20/150 ms, PWM period
    62745 ns, default index 51.
  - **Do not unify it with the Linux DTB timing.**
  - The node named "60Hz" is not a refresh-rate measurement.
  - (phase4-uboot-panel.md)
- **Panel timing, resolved (M1, measured):** the two figures describe
  different DTBs.
  - Port DTB (`rk3326-muos-r35s-panel0.dts`, from the rk351
    `rk3326-r35s-linux.dts`): single node "60Hz", 29 MHz, h 46/2/44,
    v 165/2/14, htotal 732 / vtotal 661 = 59.9357 Hz. Measured on the device:
    live DT, DRM CRTC 60 (`muos-drm-mode-probe`: 29000 kHz, 732×661,
    59.935683 Hz), and muxretro reports the display locked at 59.94 Hz.
  - Stock dArkOSen Linux DTB (`rk3326-r36s-linux.dtb`, `5634eb3e…`):
    native-mode "60Hz" is 50 MHz, h 450/46/450, v 17/5/13 (1586×515,
    ≈61.2 Hz), plus unused "50Hz" (25.5 MHz) and "75Hz" (30.6 MHz) nodes.
- **Bottom-rows glitch → M3d timing (2026-11-12):** with the rk351 timing
  (v 165/2/14) the bottom rows intermittently showed the top rows; once
  started it persisted in game and menu and across a warm reboot (panel
  power stays on). The DRM plane/CRTC state was correct (win1 640×480 at
  0,0, XR24), so it is panel-side: the ST7703 init (`b3 10 10 28 28 03 ff`,
  SETRGBIF) is set up for short porches, as on stock and ROCKNIX (both
  50 MHz, v 17/5/13). M3d DTB `d2cef0b6…`: 50 MHz, h 466/46/466,
  v 17/5/13, htotal 1618 × vtotal 515 = **60.0046 Hz** (`device/config/screen/refresh` 60.004560, moved from the pinned inputs to the overlay) (stock h 450/46/450
  is 61.2 Hz, ROCKNIX 450/70/450 60.3 Hz). Measured: real_clk 50000,
  DSI link 330 × 4 Mbps; the glitch was gone in the menu right after the
  trial boot (user-checked). The trigger was never identified, so the
  long-run check stays a T3 item.
    compatibility-matrix.md quoted this one.
  - The U-Boot DTB is 50 MHz h 450/70/450 (see above). Keep all three
    separate.
- **Framebuffer:**
  - `/dev/fb0` is 640×480, 32 bpp XRGB, stride 2560, with an empty `fix.id`.
  - **mmap returns EINVAL**, so muOS musplash needed a pread/pwrite fallback
    (patch0001).
  - musplash/mmap also triggered `Bad page map` / `Bad rss-counter` on the
    stock kernel, so that path stays excluded.
  - muxretro leaves its last frame on the framebuffer after exit.
  - M4a: once the UI has stopped, a raw 640×480 BGRX write to `/dev/fb0`
    (plain `write`, no mmap) lands byte for byte (`muos-splash`); fbcon
    is on `tty0` (`console=tty0`), so the cursor is hidden first.
  - (phase2-display-input.md, phase3-storage-stop.md,
    phase4-launcher-retro-cycle.md)
- **Backlight:**
  - `/sys/class/backlight/backlight` is pwm-backlight with period 40000 and
    levels 0–160; the default is 80.
  - The muOS default is 255, so values must be mapped. The UI's integer
    percentage turns 80/160 into "50", and it moves several points per
    step of 5.
  - The prefs store keeps brightness as 40..160 in panel units.
  - Blank/unblank is untested.
  - (compatibility-matrix.md, phase4-network-controls.md,
    phase4-preferences-preparation.md)

## Graphics (GPU)

- **Kernel driver:** Mali-G31 with the kernel kbase `bifrost_for_linux`,
  ioctl UK **11.7**. Device nodes are `/dev/mali0`, `/dev/dri/card0` and
  `renderD128`. (phase4-graphics.md, phase4-bsp-foundation.md)
- **Working userspace blob:**
  - The **Hardkernel r13p0** ZIP (`ef1a18fa…`) contains an AArch64 member
    `2a067ea3…` (40,867,064 B), with SONAME set to `libmali.so.1`.
  - It reports EGL 1.4 and "OpenGL ES 3.2 v1.r13p0-01rel0".
  - (phase4-r13-runtime.md, phase4-private-foundation.md)
- **Rejected blob:**
  - Buildroot's rockchip-mali `libmali-bifrost-g31-rxp0-gbm.so`
    (38,901,128 B) fails with "user 10.6, kernel 11.7".
  - Earlier notes blamed a "UK 10.6" kernel; that was later corrected (it
    came from an unused legacy header).
  - The dArkOSen library with the *same file name* works on the stock bench,
    so the two are different binaries.
  - The ROCKNIX rxp0 blob is untested.
  - (phase4-graphics.md, phase2-display-input.md)
- **SDL:**
  - SDL2 2.30.12 runs KMSDRM with the opengles2 renderer at 640×480:
    59.63 fps average, frame median 16.687 ms, p95 16.904 ms.
  - With the GBM provider it needed 3 local patches.
  - (phase4-native-graphics.md, phase4-graphics.md)

## Input

- **Physical sources:**

  | Node | Device | Notes |
  |---|---|---|
  | event0 | `rk8xx_pwrkey` | KEY_POWER 116 |
  | event1 | RK817 headphone jack | |
  | event2 / js0 | `GO-Super Gamepad` (`odroidgo3-joypad`, 0019:484b:1100) | |
  | event3 | `odroidgo3-keys` | volume 114/115 |

  (phase1-muinput.md, phase2-display-input.md)
- **Pad codes:**
  - D-pad: BTN_DPAD 0x220–0x223.
  - Face buttons: A=0x131 EAST, B=0x130 SOUTH, X=0x133 NORTH, Y=0x134
    WEST. There is **no G350 A/B swap**.
  - L1/R1/L2/R2: 310–313.
  - TRIGGER_HAPPY1–5: Select, Start, L3, R3, **Fn = HAPPY5**.
  - Physical sticks report −1800…1800, fuzz/flat 32.
  - (phase2-display-input.md, compatibility-matrix.md)
- **Volume keys need a module:** the volume keys come from `gpio-keys`,
  built as a **module** (`CONFIG_KEYBOARD_GPIO=m`). Without `gpio_keys.ko`,
  `odroidgo3-keys` does not appear, so coldplug must load it.
  (phase4-linux-diagnostic.md, phase4-service-diagnostic.md)
- **Virtual pad (muinput backend `rk-r35s-p0`):**
  - `muOS-Keys`: bus 0x06, vendor 0x756d, product 0x3504, version 0x736f.
  - Sticks are normalised to ±32767 on ABS 0/1/3/4. The D-pad becomes
    HAT0X/HAT0Y.
  - The 4.4 headers lack `UI_DEV_SETUP`, so the legacy uinput setup is used
    (patch0004).
  - (phase4-native-input.md, phase2-display-input.md)
- **SDL mapping:**
  - GUID `06004ca66d750000043500006f730000`. It contains a CRC, so do not
    hand-build it.
  - Buttons: a:b1, b:b0, x:b2, y:b3, shoulders/triggers b4–b7, back b8,
    start b9, guide b10, L3/R3 b11/b12, vol−/+ b13/b14.
  - SDL sees 15 buttons and joydev sees 13. The BSP's `JSIOCG*MAP` returns
    a byte count, not 0.
  - (phase3-native-menu.md, phase4-full-frontend.md)
- **Hotkeys:**
  - Fn maps HAPPY5 → BTN_MODE (SDL GUIDE).
  - Fn+Start exits a game, Fn+R2 quicksaves, Fn+L2 quickloads. Fn must be
    pressed first.
  - (phase4-gb-hotkey-exit.md, phase4-gb-state.md)
- **Double volume steps:** reading both the physical and the virtual volume
  caused double steps; patch0006 fixed this. (phase4-full-frontend.md)
- **Known glitch:** L3 fired twice once in Phase 2. It was accepted as
  margin of error and should be re-investigated if it recurs.
  (phase2-display-input.md)

## Audio

- **Codec:**
  - RK817 codec (`rockchip,rk817-codec`), card0 `rockchiprk817co`, driver
    asoc-simple-card, PCM `ff070000.i2s-rk817-hifi`, mclk-fs 256.
  - I2S MCLK is 12.288 MHz at 48 kHz.
  - (phase4-core-audio.md, phase4-native-audio.md)
- **Mixer:**
  - `Playback` is 0..237 with no dB mapping.
  - `Playback Path` options include SPK and SPK_HP (=3).
  - `Headphone Jack`.
  - G350's `digital volume` control does not exist here.
  - (phase4-core-audio.md, phase3-native-menu.md)
- **Speaker route:**
  - **SPK is inaudible on this unit and SPK_HP is audible.** SPK_HP also
    enables the HP/charge-pump stages (rk817_codec.c:558–585, 620–647). This
    is similar to ROCKNIX's HP/SPK inversion quirk.
  - The DTB has hp-volume 20 and spk-volume 3, and no hp-ctl/spk-ctl GPIO.
  - The SPK_HP cause is a hypothesis for this unit only.
  - (phase4-native-audio.md, compatibility-matrix.md)
- **Gain history:**
  - 95 (stock) → 157 (C05) → 195 (C26) → **215 (C27, current, approved)**.
    The calibration record is
    `port/device/rk-r35s-p0/speaker-calibration.json`.
  - Mixer numbers are not comparable across drivers: stock 95 gives DAC
    0x70, while the candidate driver at 157 gives DAC 0x62.
  - (phase4-image-volume-calibration.md, phase4-native-audio.md)
- **PipeWire:**
  - Sink `alsa_output.platform-rk817-sound.playback.0.0`; ACP/UCM disabled.
  - The WirePlumber rule limits output to 2 channels (FL/FR). Without it,
    enumeration asks for 64 and gets 8.
  - **`clock.force-quantum=1024`** removes the idle hiss and the "out of
    buffers" errors (the default quantum of 256 caused them).
  - `api.alsa.disable-tsched=true` (IRQ mode) gives period 1024 / buffer
    4096.
  - Do not add RT_PROCESS to SDL 2.30.12.
  - (phase4-core-audio.md, phase4-audio-buffers.md,
    phase4-irq-rate-negotiation.md)
- **udev root cause (C05):**
  - eudev rule 78 exits early for platform devices, so card0 had no
    `ID_PATH`, ACP stayed on and no sink appeared.
  - Fix: a custom rule 79 does `IMPORT{builtin}=path_id` for
    `platform/rk817-sound` cards.
  - (phase4-native-audio.md)
- **Shutdown root cause (C05):** the mulog logger held a writable FD on a
  `/opt/muos/log` file, so the read-only remount failed. Fix: SIGTERM the
  logger after its clients stop. (phase4-native-audio.md)
- **Half-rate fault after reboot (open):**
  - The PCM counter advanced at ~22050 fps for a declared 44100. This was
    seen on boots 54–57 and on the first stream of boot 60. Forcing 48 kHz
    gave 23999.7.
  - A direct `aplay` never reproduced it.
  - The driver showed I2S at 11.2896 MHz, CKR 0x00033f3f.
  - **Workaround (C36):** S95 plays 44100 frames of zeros through `aplay`
    (S32_LE, stereo, MMAP, 1024/4096) before PipeWire starts. The PCM must
    be closed before and after, with a 45 s cap. The sink is in RW mode.
  - The root cause is unknown. The planned next experiment is to reproduce
    PipeWire's sw_params with libasound, one variable at a time.
  - (phase4-calibrated-boot-audio-clock.md, phase4-rw-audio-startup.md,
    phase4-irq-rate-negotiation.md)
- **Formats seen:**

  | Path | Format | Rate | Period / buffer |
  |---|---|---|---|
  | PipeWire | S32_LE stereo | — | 512 / 2048 |
  | SDL frontend | F32LE | 44100 | 2048 samples |
  | GB core | 32768 Hz | 48000 at ALSA | 1024 / 4096 |
  | Stock dArkOSen | S16_LE | 44.1 kHz | — |

  The GB core's rate is converted by PipeWire.
  (phase4-native-frontend-audio.md, phase4-gb-content.md)
- **Volume curves and policy:**
  - wpctl volume is cubic: 0.55 → 0.166375, about −15.6 dB.
  - The muOS policy `settings/advanced/volume=2` forces 35%. Policy 3 gives
    100.
  - (phase4-core-audio.md, phase4-native-frontend-audio.md)
- **muOS help sounds:**
  - `info_open.wav` / `info_close.wav` are bass-heavy and inaudible on the
    speaker.
  - `navigate.wav` was boosted +8.80 dB to peak 30000 (SHA `adac7879…`).
  - (phase3-audio-resume.md, phase4-native-frontend-audio.md)

## Boot chain

- **Trust image = rkbin (M4d, 2026-11-16):** the BL31 in the U-Boot tree
  (`rk3326_bl31_v1.14.elf`, 800 KB) and rkbin efff42ab's (210 KB) have
  identical LOAD segments (0x10000, 78704 B; 0xff0e0000, 12288 B; same
  `v1.3(debug):1b8f3f9` build); the extra bytes are debug sections.
  trust_merger output with either is the same `3531668a…` = sector 24576
  of the card and of every image (`rkbin-trust.sh`).
- **Stock raw layout** (from dArkOSen `flash_uboot.sh`; read it only, **never
  run it**):

  | Component | Sector | Offset |
  |---|---|---|
  | idbloader | 64 | — |
  | uboot.img | 16384 | 8 MiB |
  | trust.img | 24576 | 12 MiB |

  - trust.img matches the reference (`3531668a…`).
  - The installed idbloader and U-Boot differ from the reference even
    though the banners match: `DDR Version 1.10 20181114`,
    `U-Boot 2017.09-g5606e804ff-dirty`.
  - No valid saved environment was found.
  - (phase4-boot-chain.md)
- **Own U-Boot:**
  - Source `christianhaitian/RG351MP-u-boot` @`5606e804` (GPLv2).
  - Payloads: DDR 333 MHz v1.10, miniloader v1.12, BL31 v1.14, BL32 v1.10.
  - The stock odroidgoa config has **destructive automatic paths**:
    `spi_recovery.img` → `rksfc write` + `mmc erase 0x1 0x7FFF`, `saveenv`,
    and RG351-only `hwrev` ADC DTB selection. The port removes them
    (ENV_IS_NOWHERE, PANIC_HANG, no CMD_GO/rbrom; patch0007). **Never use
    `saveenv`.**
  - (phase4-boot-chain.md, phase4-uboot-sd.md, phase4-uboot-panel.md)
- **Device numbering:** U-Boot sees the SD card as `mmc 1`; Linux sees it as
  `mmcblk0`. These are separate enumerations, so do not swap them.
  (phase4-uboot-sd.md)
- **Memory map:**
  - U-Boot entry 0x200000; control FDT reserved at [0x01e00000, 0x01e40000).
  - Linux DTB at 0x01f00000; Image at 0x02000000, effective entry
    0x02080000, end 0x02ec0000. Initramfs area at 0x0a200000.
  - U-Boot relocates to 0x3dd08000; video 0x3de00000–0x3fff0000; RAM top
    0x40000000.
  - (phase4-linux-diagnostic.md, phase4-memory-monitor.md)
- **Port kernel:**
  - `christianhaitian/linux` rg351 @`d8402159`, `rg351p_tweaked_defconfig`,
    Linaro GCC 6.3.1.
  - Release `4.4.189-muos-r35s-p4`, 555 modules.
  - DTB `rk3326-muos-r35s-panel0.dtb`, based on `rk3326-r35s-linux.dts`
    (GPL-2.0+ OR MIT). OPPs capped at CPU 1296 MHz / 1.35 V and GPU 520 MHz.
  - The stock config, recovered from the hidden `/boot`, differs from the
    public defconfig only in 2 Wi-Fi symbols.
  - (phase4-bsp-foundation.md, phase4-modules-firmware.md)
- **U-Boot boot records (M3b; replaced the M2 compiled-in asset pins):**
  the port U-Boot (`uboot-boot/boot.c`, command `muos_boot`) reads three
  512-byte records in the unused MBR gap: sector 32 main, 33 previous, 34
  trial (`bootrec/bootrec.h`; CRC32, file names, sizes, SHA256). An armed
  trial is rewritten to "consumed" on the card *before* it is tried, so a
  bad trial kernel costs one power cycle; then main, then previous. Each
  file is size- and SHA256-checked; a failure falls through to the next
  record. U-Boot appends `muos_slot=<slot>` (trial also `panic=10`). Kernel
  window: 0x02000000 + 32 MiB (fallback 0xec0000, which the M2 kernel
  filled exactly; the M3b kernel ends at 0xed0000). Kernel/DTB updates no
  longer touch the bootloader: `muos-boot-slot install-trial`, reboot,
  `promote`. Never overwrite a p1 file a record points to (new files go
  under content names, `Image-<sha12>`, `panel0-<sha12>.dtb`).
- **TRNG (M3b):** `rockchip,cryptov2-rng` at 0xff0b0000 is already "okay"
  in the port DTB; `CONFIG_HW_RANDOM_ROCKCHIP=y` drives it. The 4.4 hwrng
  core keeps the *first* registered RNG as current, and `tpm-rng` (no TPM
  on this board; reads fail with EIO) registered first, so
  `HW_RANDOM_TPM` is off. Result: the RNG is ready at 2.6 s instead of
  7–11 s.
- **Boot command and root check:**
  - Kernel cmdline: `root=PARTUUID=4d554432-02 rootfstype=ext4 rootwait ro`,
    no initramfs, `booti 0x02000000 - 0x01f00000`. The C79 image uses
    `init=/sbin/muos-ext4-diag`.
  - Compare root MAJ:MIN using `findmnt -rn`; padded output once caused a
    false "Root device mismatch".
  - (phase4-ext4-diagnostic.md, phase4-card-image.md)
- **Init (M1):**
  - U-Boot passes `init=/sbin/muos-ext4-diag` (env never rewritten). Since
    M1 it is a guard-free shim: mount proc/sys, optional trial-boot
    fallback, `exec /sbin/init`. Any check that fails in it halts PID 1
    before SSH exists, so keep it trivial.
  - BusyBox 1.37.0 init runs its SHUTDOWN actions, then `kill(-1)`. A
    failing script **does not cancel** the shutdown; `muos-rc stop` bounds
    each service stop instead.
  - `muos-rc` order: seedrng/syslog/sysctl → udev → D-Bus → S41 network
    (background) → S85 root ro → S89 p3 rw + p1 ro → S90 storage binds →
    S91 runtime views → S95 core/audio/muinput → S96 input mapping → S99 UI.
    Menu at ~15 s uptime; the stop sequence takes ~2 s.
  - Services need the muOS environment (HOME=/root, XDG_RUNTIME_DIR,
    PIPEWIRE_RUNTIME_DIR, D-Bus address, frontend LD_LIBRARY_PATH);
    without it S95 audio fails.
  - `muxfrontend` SIGTERMs itself if its parent is PID 1; the
    `muos-frontend` loop owns it. `start-stop-daemon -b` double-forks, so
    signal the process group read from `/proc/PID/stat`, not `-PID`.
  - The frontend leaves per-launch request files in `/run/muos`
    (`governor`, `controller`, ...). If they are not removed, the next
    start opens an "option" screen.
  - muOS writes `/opt/muos/config`, `/opt/muos/share/info/{content,config}`,
    `/opt/muos/share/volume`, `/opt/muos/device/config`, `/opt/muos/log`,
    `/root`, `/usr/share/wireplumber`, `/etc/asound.conf` and
    `/usr/share/alsa/alsa.conf`. With root ro these are p3 or tmpfs binds
    (S91). BusyBox `cp -f` unlinks first, so it cannot replace a
    bind-mounted file: seed the ALSA copies from muOS's own templates.
  - (phase4-boot-coordinator.md, phase4-init-services.md)
- **Entropy:**
  - Up to M3a, HW_RANDOM_ROCKCHIP was off and the RNG became ready only
    after about 7–11 s. Since M3b the TRNG makes it ready at 2.6 s (see
    "TRNG (M3b)" above).
  - Buildroot's stock S01seedrng (`-d /var/lib/muos-seedrng`) runs while
    root is still rw. Nothing waits for RNG readiness any more: the dropbear
    host key is persisted, and a missing one is generated in the background
    network worker. Images ship without `seed.*` (M1 retired the C05
    entropy gate and the "never replay the seed" rule).
  - Buildroot's S01seedrng hides failures with `|| true`.
  - (phase4-entropy-diagnostic.md, phase4-service-diagnostic.md)
- **Userspace:**
  - Buildroot 2025.02.19, GCC 13.4 (`--with-cpu=cortex-a35`), glibc 2.41,
    SDL 2.30.12; 308 ELF files as of C78.
  - BusyBox quirks: no `stat -f` (use `findmnt`), `dirname //` loops, `tar`
    has no `-z`.
  - Tools missing on the device: `pw-top`, `unshare` (use
    `/usr/libexec/muos-session/mount-namespace`), and the `jq` `test`
    function.
  - (phase4-rootfs.md, phase4-save-store-installed.md,
    phase4-irq-rate-negotiation.md)

## Storage

- **Stock card (original32):**

  | Partition | Type | Start sector | Size |
  |---|---|---|---|
  | p1 | vfat (0x0c), BOOT | 32768 | 204800 sectors |
  | p2 | Btrfs root | 237568 | — |
  | p3 | exFAT EASYROMS (0x07) | 21193545 | — |

  - The stock fstab's `compress=zlib:1` is not supported on 4.4, where zlib
    levels do not exist yet; it was changed to `compress=zlib`.
  - (phase1-muinput.md, storage-recovery.md)
- **Test card (test128):**
  - 249872384 sectors, disk ID `4d554432`.

  | Region | Contents |
  |---|---|
  | sector 64 / 16384 / 24576 | idbloader / U-Boot / trust |
  | p1 (16 MiB, 100 MiB) | FAT32 `MUOSDIAG`, boot flag |
  | p2 (128 MiB, 512 MiB) | ext4 `ROOTFS`, PARTUUID `4d554432-02`, mounted RO |
  | p3 (640 MiB to end, ~118 GiB) | ext4 `MUOSDATA`, PARTUUID `4d554432-03`, UUID `6d756f73-c020-4000-8000-000000000001` |

  - (phase4-userdata-offline.md, phase4-card-image.md)
- **Write and data rules (M1):** the whole card is disposable and is
  rewritten with the images in `dist/recovery` (STATUS). These hold
  0–640 MiB (bootloader, p1, p2) plus a 1 GiB p3. `flash-card.sh --grow`
  extends p3 to the end of the card.
  - p3 holds `ROMS/<system>` (`ROMS/GB/private.gb`), the muOS storage tree
    `MUOS/*` (saves and states in `MUOS/pickles`), `MUOS/port`
    (persistent config and assignments), `MUOS/log`, and the older C21
    `MUOS/preferences` and `MUOS/port-saves-v1` stores (imported once,
    no longer written).
  - (phase4-root-migration.md, phase4-p2-write-core.md)
- **ext4 feature flags:**
  - Root and data ext4 are created **without** 64bit, metadata_csum(_seed),
    orphan_file or fast_commit, to stay compatible with kernel 4.4.
  - The resulting images report compat 0x3c / incompat 0x242 / ro_compat
    0x46b.
  - (phase4-rootfs.md, phase4-gambatte-image.md)
- **Private state on p2:**
  - Network config and host key: 0600.
  - SeedRNG seed: created per card at first boot; never in images.
  - The C07 boot counter (`boot-seq`) was retired in M1. Boots are
    identified by `/proc/sys/kernel/random/boot_id`.
  - Root directory: 0755.
  - (phase4-root-migration.md, phase4-candidate-update.md)
- **Card-handling quirks:**
  - `blkid` exits 0 on bare PART_ENTRY tags.
  - Whole-disk and partition page caches are separate, so flush each alias
    (BLKFLSBUF).
  - e2fsprogs 1.47.2 leaks external EA blocks when an inode is removed.
  - (phase4-userdata-offline.md, phase4-recovery-image.md)
- **Steam Deck reader quirks:**
  - SteamOS automount runs `chmod 777` on the mount root
    (`steamos-automount.sh:99`). This turned the p2/p3 roots into 0777
    twice.
  - Mitigation: a UDISKS_IGNORE udev rule for the card CID plus BLKROSET.
    Neither survives a Deck reboot.
  - The Deck's reader reports a different last CID byte.
  - (phase4-backup-native.md, phase4-root-permissions.md)
- **MMC timeouts (Phase 3, stock image):**
  - `mmcblk0: error -110` and an I/O error at sector 17400328 aborted Btrfs
    and forced the root read-only.
  - The cause is unknown: card, contact, controller, power or kernel.
  - `statvfs` did not report read-only, so check `/proc/mounts`.
  - (phase3-storage-stop.md)

## Network and USB

- **Controller:** the only USB controller is DWC2 at `ff300000.usb`.
  (phase4-network-warm.md)
- **Dongle:**
  - Realtek, starts in storage mode `0bda:1a2b`.
  - `usb_modeswitch -K -v 0bda -p 1a2b` (StandardEject) switches it to
    `0bda:c820`. The generic D-Link entry does not apply.
  - Interfaces 1.0/1.1 are Bluetooth (btusb, btrtl, `rtl_bt/rtl8821c_fw.bin`
    + config); 1.2 is Wi-Fi (`8821cu`, firmware embedded).
  - `8821cu.ko` is built for `4.4.189-muos-r35s-p4`. **Never load it on the
    stock kernel.**
  - (phase4-network-ssh.md, phase4-modules-firmware.md)
- **Warm-reboot failure, root cause and fix:**
  - On warm reboot, EP0 control transfers time out (−110), including the
    vendor read of SYS_CFG2/0xfc. HALMAC then reports status 54 "chip id
    undefined", which is a side effect of the timeout, not an
    incompatibility.
  - Trigger: btusb probe → `hci_power_on` sends HCI commands even with no
    bluetoothd running.
  - **Fix:** `/etc/modprobe.d/90-muos-r35s-wifi-only.conf` blocks btusb
    autoload (recipe `muos-r35s-wifi-only`). A manual modprobe still works.
  - **Dead ends — do not retry:** USB reset (-R), drivers_probe, unloading
    8821cu, ordered network/udev stop, SET_CONFIGURATION 0→1, and DWC2
    unbind/bind both after the failure (C15) and before reboot (C17).
  - `rtw_drv_log_level=3` hides RTW_INFO, so "zero failures" proves nothing.
  - (phase4-network-warm.md, phase4-usb-control.md)
- **Network stack:**
  - Dropbear 2026.93, wpa_supplicant 2.12, libnl 3.11.0, usb_modeswitch
    2.6.1, BusyBox udhcpc, all from the pinned Buildroot SDK.
  - LAN only until M4a; since M4a the DHCP hook writes the resolver
    (`/etc/resolv.conf` → `/tmp/resolv.conf`).
  - wpa_supplicant 2.12 keeps counting network ids across `reconfigure`
    (ids 11+ after a few), so "the first network in the file" is the
    first id in `list_networks`, not id 0 (M4a).
  - Daemons started by a script that holds a `flock` fd inherit it: an
    SSH session from such a dropbear kept the worker's lock held (M4a);
    the worker closes fds 7/8 for every daemon.
  - (phase4-network-ssh.md)
- **SSH:**
  - Developer images: port 2222, root, key only. M4a adds muOS's web
    services: password SSH on `web/sshd_port` (22) and SFTP-only on
    `web/sftp_port` (2022), both off by default. The host key is generated on the device after
    the RNG is ready.
  - Use `port/scripts/device.sh` (find/run/sh/push/pull/reboot/capture).
    It finds the device by the pinned fingerprint below, because DHCP
    changes the IP, and logs to `build/logs/device.log`.
  - Host key fingerprint
    `SHA256:fDW+/iNaWgqPwqBtO/ESuKPSQHvYN1PSo2RHfilOxK0`.
  - (phase4-network-ssh.md, phase4-resume-checkpoint.md)
- **Bounded runs:** `muos-run-bounded` rejects limits over 120 s with rc 125.
  (phase4-network-ssh.md)

## Power and battery

- **RTC and cut-off (M4d, 2026-11-16):** the RK817 RTC (`rk808-rtc`,
  rtc0) kept UTC to within 40 s over days off (set earlier by dArkOSen);
  the kernel sets the clock from it at boot. DT: `power_off_thresd` 3300
  mV (VSYS), `zero_algorithm_vol` 3850, `bat_res` 100 mΩ; with
  `CONFIG_ARCH_ROCKCHIP_ODROIDGOA` the BSP itself powers off after 1 min
  below 3300 mV (or at once ≤ 3250). The zero algorithm aims dsoc at 0
  where the loaded voltage reaches that threshold at the present load, so
  the ~10–18% left at a game's cut-off (OCV ≈ 3.50 V at 730 mA) is not
  reachable at that load: the CTR run hit 3% at 3352 mV loaded, falling
  ~5 mV/min, ~1%/min. Cutting at 1% instead of 3% gains ~2–3 min.
- **Rumble (M4e):** the R35S has no motor (user, 2026-11-17); some R36S
  do, and every R36S-family DT (dArkOSen, ROCKNIX) declares the joypad's
  PWM anyway. FF_RUMBLE through the gamepad's evdev node reaches the PWM
  even while muinput grabs the pad. Probe: RK817 averaging current
  (0x7A/0x7B, raw × 172 / 1000 mA, ~0.7 s update) read over i2c without
  forks is steady to ±3 mA at menu idle; with the motor driven the R35S
  shows −2…+3 mA (no motor).
- **OFF_CNT (0x6F) is stale after warm reboots (M4e):** it read 141 min
  on every boot of 2026-11-16/17 (also earlier: 15 min across M4b boots),
  so the BSP's OCV calibration ran on warm reboots with the power-up OCV
  register (3880 mV): +12 points (57 → 69%). Kernel 0008 clears it after
  reading: the register is writable (`i2cset -f -y 0 0x20 0x6f 0` sticks;
  RK817 at i2c-0 0x20, ID 0x8174); a power-up on the charger read 0.
- **Missed USB disconnect (M4e T3):** a dongle unplugged while Wi-Fi ran
  produced no "USB disconnect" (dwc2, otg port 1-1, runtime PM off) until
  a port reset 15 s later; the first unplug of the same session was
  seen. The AP then kept the stale association (deauth reason 2 on the
  next connect, ignored by the 8821cu driver).
  M4e.1 T3: a plug was missed too: HPRT0 (0xff300440) 0x00021401 =
  connected, line state D+, not enabled, for 53 s with no enumeration
  and no PrtInt in GINTSTS; a normal attach reads 0x1005 once enabled.
  dwc2 `dr_mode = "otg"`, its PHY node `otg-port` disabled (no PHY
  driver, rockchip_usb2phy irq count 0); ROCKNIX's R3xS DT is the same.
- **RK817 BOOST** is `RK817_POWER_EN_REG(3)` = 0xB4, enable bit 1 with
  write mask bit 5 (0x20 off, 0x22 on). It is **not** the USB port's 5 V
  (M4f): with it off (0xB4 read 0x00) the dongle stayed connected, on
  battery and on the charger. The port's supply is not in the DT.
- **dwc2 rebind** (`/sys/bus/platform/drivers/dwc2/{unbind,bind}`
  `ff300000.usb`) re-detects the port and re-enumerates the dongle in
  < 1 s (M4f; muos-usb-watchdog uses it).
- **Wi-Fi dongle self-reset (2026-11-17):** with the firmware deaf (H2C
  errors every 2 s from 13 s), the dongle disconnected by itself at 53 s
  and re-enumerated in CD-ROM mode (1a2b) at 72 s: a real chip reset.
- **Battery (M2):** RK817 fuel gauge, design_capacity 3140, qmax 3454.
  `/sys/class/power_supply/battery/{capacity,voltage_now,status,health}`.
  The charger is `ac/online` (1 when plugged in; `usb/online` stays 0), the
  same as the RK817 G350 config upstream. Charge LED: the DTB
  `blue:heartbeat` gpio-led (GPIO0_C1) is disabled in stock too.
- **Battery % (M3d step 2):** the rk351 BSP's `capacity` was not the fuel
  gauge but an rg351p hack, `rk817_battery_rg351p_capacity_get()`: linear
  3.3–3.9 V, 100% at ≥ 3.9 V, only allowed to fall while discharging. A
  rested battery (cold boot) or the charger lifts the voltage above 3.9 V
  → 100% (the M2 "84→100% on plugging" and the M3d T3 "back to 100% after
  a cold boot"). dArkOSen reads the same kernel value. The driver's own
  Rockchip gauge ran all along (`dbg_level` 1 prints it: `dsoc`, `rsoc`,
  `remain_cap`, FCC 3380 mAh from the PMIC). `port/patches/kernel/0001`
  reports `dsoc` (kept in PMIC registers across reboots, OCV-corrected
  after ≥ 30 min off). Below `zero_algorithm_vol` (3850 mV) under load it
  pulls dsoc toward the OCV table (seen: 66 → 58% at 3.73 V / 0.7 A, OCV
  ≈ 3.80 V ≈ 57%), so it should reach 0 at the 3.3 V cut-off; FCC learns on
  a full charge.
  Step 2 T3 (2026-11-13): after a reboot right after unplugging at ~90%,
  dsoc came up ~0 with the coulomb counter at 99% (remain_cap 3354 of 3380
  mAh); the smoothing then raised dsoc only at the charge rate. No BSP
  init message logged on the following boot; patch 0002 cross-checks dsoc
  against the coulomb SOC at boot (`muos-gauge:` lines). Related: in
  the BSP zero algorithm dsoc drops 1% per 15 s (`WAIT_DSOC_DROP_SEC`) and
  is zeroed after 30 s below `power_off_thresd` − 70 mV.
  **Root cause of the boot jumps (2026-11-13, patch 0003):**
  `rk817_bat_not_first_pwron()` compares `ocv_soc` (%) with the stored
  dsoc (1/1000 %): `abs(ocv_soc - pre_soc) >= 80` is true on every boot
  with `pwroff_min > 0` (a reboot counts ~2 min), so the counted SOC was
  replaced by the power-on OCV estimate (`dsoc force calib: 85020 -> 98`
  with the charger in; 75 → 81 after a 1-min rest) and dsoc was set to a
  % value read as 1/1000 % (the 0% boot). The max_soc_offset test (≥ 30
  min off) mixes units the same way. 0003 compares in 1/1000 %; a short
  power-off now keeps the counter (`now_cap` matches the stored cap:
  the coulomb counter persists across a reboot).
  **Unsampled OCV (2026-11-13, patch 0004):** on 5 of 20 warm reboots the
  OCV register read 18 mV (`muos-gauge: stored ... ocv_v=18`), the OCV SOC
  0%, so the forced calibration set dsoc and the counter to 0; the next
  boot looked like a halt (counter 1 vs stored 3333 mAh) and a later boot
  with a valid OCV jumped back. 0004 treats an OCV outside 3.0–4.5 V as no
  sample and keeps the stored SOC. Likely the cause of the first step 2
  T3 failure (0% after a reboot) too.
  Confirmed on hardware in step 6: boot 2341d3cf read 18 mV and kept dsoc
  100000 (`ocv 18 mV not sampled`).
  **Real capacity (2026-11-14, idle run 94% → 3%, milestones.md M4a
  item 8):** ~2530 mAh (±10%), not the 3380 mAh FCC: 2209 mAh counted
  (host-integrated current agrees within 1%) over ~87 OCV-table points.
  Usable from full to the 3% / 3.36 V cut-off ≈ 2450 mAh, ~6.3 h at
  menu idle (389 mA). With FCC 3380, rsoc still reads 28% at the
  cut-off; the zero algorithm (< 3850 mV) makes dsoc fall ~45% faster
  below ~3.82 V (0.20 → 0.29 %/min at constant load). Loaded-step
  resistance ~200 mΩ (1-min samples, includes polarisation).
- **Wi-Fi dongle power (M4a T3 / M4b, 2026-11-14):** the RTL8821CU
  (`0bda:1a2b` CD-ROM mode → `0bda:c820`) loses power in "mem" sleep,
  also on the charger, and returns in CD-ROM mode; a DWC2 unbind/bind
  keeps it powered (no software power cycle). Switched 0.27 s after
  power-up its firmware failed `_btmpoper_cmd: Didn't get H2C Rsp
  Event!` and scans stayed empty until a power cycle; ≥ 10 s worked in
  19/19 wakes, and in M4c 5, 3 and 2 s passed 3/3 each (default now 4 s,
  6/6). `power/connected_duration` (ms) gives the powered time. A deaf
  dongle recovers with the next "mem" sleep (power cut, CD-ROM mode
  again), not with a warm reboot or a USB reset.
- **Wi-Fi dongle after a warm reboot (M4c, 2026-11-14):** it stays in
  `c820` mode, so udev autoloaded 8821cu at ~6 s; the worker's USB reset
  under the bound driver made the firmware fail H2C (45 errors, no AP).
  With autoload blacklisted (reset first, then `modprobe`): 5/5 clean.
  Wi-Fi off (driver unloaded) saves ~76 mA in CTR (737 → 661 mA).
- **Battery under game load (2026-11-14, CTR ~750 mA):** the 3.35 V
  cut-off comes with ~470 mAh (18%) still in the counter: ~2050 mAh
  usable from full vs ~2450 at menu idle; the zero algorithm brought dsoc
  to 3% at the cut-off. The coulomb counter also reads 0 after a plain
  low-battery poweroff (not only after charging while off).
- **Coulomb counter seeding (2026-11-15, i2cset on the R35S):** the
  RK817 copies Q_INIT (0x70–0x73) into Q_PRESS (0x74–0x77) when
  Q_INIT_L0 (0x73) is written, even with an unchanged value; H3 or L1
  writes alone load nothing. Q_PRESS is a signed counter (bit 31 = the
  BSP's CAP_INVALID) at ~20.93k raw/mAh (CAPACITY_TO_ADC, res_div 1).
  After the flat-battery poweroff it read about -3260 mAh and counted
  normally from there. Raw registers: `/sys/kernel/debug/regmap/0-0020/
  registers` (mount debugfs); BusyBox i2cset needs hex register numbers.
- **Battery effective resistance (2026-11-14):** ~197 mΩ from 1-min load
  steps, ~217 mΩ at charge start (DT `bat_res` says 100).
- **RTC wake from power-off:** an alarm in `/sys/class/rtc/rtc0/wakealarm`
  (rk808-rtc on the RK817) set before `poweroff` doesn't power the R35S
  back on (2026-11-13). Unattended power-off cycles need another way
  (or hands).
- **Battery current (M3d step 2, `build/logs/power-m3d`, on battery,
  volume 10, backlight as set):** menu idle 559 mA (1008 MHz); per game
  performance / schedutil: NES 759/645, GB –/625, GBA 759/633, SNES 803/664,
  MD 779/666, PSX 821/718 mA. Missed vsyncs per 45 s with schedutil: 0–1
  for NES/GB/GBA/SNES/MD, ~420 for PSX (performance: ~30–45). The menu's
  559 mA idle is high (backlight, Wi-Fi, redraws: not yet split).
- **LEDs and rumble:** GPIO77 is the battery LED. LEDs and rumble are
  untested. (compatibility-matrix.md)
- **Power key:** `rk8xx_pwrkey`, event0, `KEY_POWER`. The port board entry
  gives muhotkey ev0 for power (ev3 for volume). muhotkey emits
  `POWER_SHORT`/`POWER_LONG` (400 ms) combos; `share/hotkey/sleep.json` maps
  both to sleep, as upstream. Evdev writes to a private `/dev` node inject
  real presses (`/run` is `nodev`). A long press also powers off from the
  U-Boot monitor.
- **Suspend (M2):** `/sys/power/state` offers `freeze mem disk`; no
  `mem_sleep`. The RK817 RTC (`rk808-rtc`, `/sys/class/rtc/rtc0/wakealarm`)
  and the power key wake from `mem`.
  - After `mem` the DWC2 USB host (`ff300000.usb`) does not recover: the
    dongle's LED stays off, and replugging doesn't help.
  - Fix: unload `8821cu` and unbind DWC2 before suspend, rebind after
    resume and restart the network. The dongle re-enumerates as 1a2b and
    is mode-switched again. 20/20 cycles passed.
  - `pm_test=devices` alone does not reproduce the failure.
  - Each fd a sleep script holds is inherited by the daemons it restarts.
    Close lock fds (`9>&-`), or the next sleep finds the lock taken.
- **CPU:**
  - The port caps the CPU at 1296 MHz (stock allows 1512).
  - Under load the governor read performance at 1296000 kHz.
  - (phase4-bsp-foundation.md, phase4-nes-performance.md)
- **Reboot (M1):** `reboot` through init and the launcher's Reboot entry both
  run the ordered rcK (UI → input → core → runtime → storage → p3 unmount)
  and come back cleanly; p3 needs no journal recovery afterwards. Poweroff
  uses the same path but is untested by hand, and suspend is untested.
  `/sys/power` is bound ro until M2.

## Emulation stack facts

- **Host:** the native host is muOS `muxretro`, not RetroArch. Port patches
  0003, 0006–0012 and 0015 are in the lineage; 0013 and 0014 are
  experimental. (phase4-muxretro-integration.md, phase4-nes-performance.md)
- **NES (FCEUmm), M2 measurement:**
  - Real game, Super Mario Bros. 3 (MMC3): 59.9 fps, vsync-locked to the
    59.94 Hz panel. Core 5.9–7.1 ms per frame at 1296 MHz, under
    performance or schedutil.
  - The C47 figure (51.4 fps; 13.5 ms core + 5.6 ms present; O3/LTO
    53.6 fps) is specific to the synthetic `r35s-flight` demo ROM and
    reproduced exactly (51.6). It is not a general NES limit.
- **Measuring fps:** `MUXRETRO_PERF_CAPTURE=1` makes muxretro write
  `pickles/performance.csv` every 15 s (last 1024 frame intervals; frame,
  core and present means). Use `port/scripts/t2-nes-fps.sh`. The muxretro
  log line "Content rate window X Hz" is derived from audio and frame
  counts, not from wall time; it reads 60.10 even when slow.
- **M3c cores (1296 MHz, schedutil):** all vsync-locked at 59.9 except
  PSX (59.1). Core time per frame: GB 2.9 ms, PSX 3.6 ms (ari64 dynarec),
  GBA 4.2 ms (gpsp arm64 dynarec), MD 4.9 ms, NES 7.0 ms, SNES 9.4 ms
  (snes9x2005_plus, the tightest). pcsx_rearmed needs
  `HAVE_PHYSICAL_CDROM=0` (otherwise `cdrom.c` links without `dir_list.c`
  → `undefined symbol: dir_list_new` at load). gpsp needs `platform=arm64`
  for its dynarec (`unix` picks x86 from the host's uname). Changing the
  volume during a game drops frames (see below), so measure without
  touching the keys.
- **Level-change judder (M3b T3, `t2-level-fps.sh`):** SMB3 has no frame
  over 20 ms at rest. Changing volume or brightness in game drops frames
  (each about 33 ms, one missed vsync) for as long as the keys are
  pressed; average fps falls only 0.3–2 %.
  - Per 13.5 s of changes (about 1.5 per s): volume keys 30–70 slow
    frames, brightness keys about 33, the overlay alone (config value
    written, no script) 20–25, `bright.sh` without the overlay 0–3,
    `audio.sh`'s `wpctl` calls alone 0, `audio.sh` from a shell 9–46
    (large run-to-run variance).
  - Not the cause: GPU clock (pinned 520 MHz), `debug_mode` 2 vs 0, the
    SVG glyph decode (tiny glyphs), DDR devfreq (10 transitions per
    uptime), muhotkey's environment; nice 19, SCHED_BATCH and SCHED_IDLE
    for `audio.sh` gave no consistent gain.
  - Mechanism: while any HUD element is visible, muxretro leaves its
    video fast path and runs `lv_refr_now()` + composite every frame, and
    each value change redraws the bar. NES leaves about 6–8 ms of slack
    per frame (core 7 ms, upload 2 ms, present 9 ms incl. the vsync wait),
    so small stalls miss vsync. The scripts, `muxretro` and the overlay
    are upstream code (same on upstream's RK3326 GKD Pixel 2); not a port
    defect. A fix would be an upstream muxretro change.
  - *Fixed in M3d step 3* (muxretro patch 0001 `slow_frames` stage trace
    + `slow-frames.py`): per change, the LVGL bar cost one 22–30 ms frame
    in `present` (glyph + bar redraw through the UI render target); the
    level steps' cost was not the wpctl clients but WirePlumber's
    `node/store-stream-props` hook reacting to the sink's Props change (12
    slow frames per 14 s of `pw-cli` sets, 1 with WirePlumber stopped).
    Fixes: muxretro draws the in-game bar itself (patch 0002, video
    overlay hook, the LVGL layer stays hidden), `state.restore-props =
    false` on the sink, and `muos-volume-step`/`muos-volumed` (one Props
    write through a resident `pw-cli`). Result on NES (schedutil): vol 3–6
    frames of 20–23 ms and 0 > 25 ms per 14 s (was 46–53 up to 33 ms),
    bright 0–2 (was 10–35).
  - Port differences seen on the way, left as they are: `system/debug_mode`
    is 2 (upstream default 0; debug lines from every module go to p3), and
    the port's `r35s-bringup.json` volume/brightness combos lack
    upstream's `handle_hold` (holding a key does not repeat).
- **Frame stalls (M3d, `t2-stall.sh` + `stall-report.py`):** per-frame
  timeline from muxretro's capture against a 10 Hz sampler (CPU/DDR/GPU
  clocks, per-thread CPU, IRQs, card reads). ">25 ms" = a missed vsync;
  20–25 ms frames pair with ~13 ms ones and mostly don't show.
  - *schedutil was the main PSX cause:* the CPU sat at its 1008 MHz floor
    (scaling_min) through per-frame bursts (PELT averages them away); CTR's
    intro ran a 20/13/17/17 ms pattern, and `t2-nes-fps` read 59.09 fps
    (= 1000/16.92 ms). With `performance` (1296 MHz) the intro is clean:
    PSX cold run 540 → 152 slow frames, missed vsyncs 89 → 46.
  - *muxretro's own governor boost* (prebuilt muxretro, frontend.log
    "Governor boost"): `scaling_governor` → performance on content startup,
    on "sustained frame misses" and on state save, restored afterwards; it
    doesn't touch GPU, DDR or idle. With schedutil, volume/brightness
    presses trigger it; `muos-boost` (2 s CPU/GPU floor + idle off) acts
    sooner.
  - *DDR devfreq:* `dmc_ondemand` switches 528↔786 MHz without VOP sync
    (`failed to get vop bandwidth to dmc rate`, `rockchip-drm: devfreq is
    not set`); muOS upstream pins DDR to performance with the
    `performance` governor (`governor.sh` SYNC_*), as dArkOSen's `perfmax`
    does. The port now does the same (`muos-governor`).
  - *Card reads (cold page cache) are not the PSX cause:* the remaining
    CTR dip (~27–47 s after start, 52–58 fps with HLE) is identical warm
    and cold. With the real BIOS (scph5501) the deep dips are gone (worst
    5 s 58.5 fps, 21 missed vsyncs per 75 s vs 45 with HLE) but 20–24 ms
    jitter frames remain; core p95 17.6 ms, emulation thread only ~37%
    busy, so it waits on the GPU thread (`pcsxr-gpu`).
  - *BIOS vs HLE* (same kernel, `performance`, `t2-nes-fps` PSX 60 s,
    alternating runs): HLE 59.44 / 59.83, BIOS 59.79 / 59.85 fps, core
    6.1–6.2 ms either way: no measurable speed difference. CTR's attract loop
    dips to 54–56 fps for 5–10 s every 60–75 s (4.5 min run), with ~20
    missed vsyncs each: scene load, not system noise.
  - *Thermal:* sustained PSX at 1296 MHz levels off at 82–83 °C (M3c,
    schedutil: 64 °C). The soc zone uses `power_allocator` (trips 70/85 °C
    passive, 115 °C critical); no cooling device engaged in 4.5 min
    (CPU stayed at 1296 MHz). The margin to 85 °C is small in a warm room.
  - *Wake:* muxretro was resumed before the USB/Wi-Fi bring-up: DWC2 up to
    32k IRQ/s, udevd, kworkers and the 8821cu firmware load stalled frames
    for ~3 s (max 89 ms). All device IRQs land on CPU0. With the game
    resumed after the radio is up: 5–10 slow frames, 2–6 missed vsyncs per
    wake; what's left is one 80–95 ms frame ~4 s after resume while the
    8821cu associates (`RTW_CMD_THREAD`). Moving the dwc2 IRQ to CPU3
    doesn't change it (`taskset` isn't in the image, so muxretro pinning
    was not tried). M3d step 4: pinning the Wi-Fi side (worker, wpa,
    udhcpc, `RTW_CMD_THREAD`) to CPU3 and the game to CPU0–2 removes the
    long frame (129 → 33 ms max); the dwc2 IRQ on CPU3 too adds nothing.
    The kernel is PREEMPT_VOLUNTARY: a driver busy-wait owns its CPU.
  - *Volume/brightness (still open):* unchanged by the governor (vol 44–48,
    bright 22 slow frames per 14 s) and by priority (renice −10 of every
    muxretro thread, SCHED_RR 5 of the main thread: no gain or worse).
    Parts: the overlay alone ~20; `wpctl set-volume` alone 13 (2/s),
    `wpctl get-volume` 4 (4/s); during changes the audio queue drains
    (mean 45 → 24 ms, minimum 0). WirePlumber applies the volume in
    software (the ALSA `Playback Volume` doesn't change). Fixing the overlay part
    needs a muxretro source build (M3d step 2).
  - *Test artefact:* the capture writes performance.csv to p3 on muxretro's
    main thread every 15 s (one 35–45 ms frame); the report drops frames
    within 0.4 s of a dump.
- **muxretro signals:** SIGUSR1 → auto-save, then pause and write
  `/run/muos/muxretro_save_ready` (pid). SIGUSR2 → resume. Auto-save
  default `auto_save=3` (idle + quit) resumes the last state on launch.
- **Headphone jack:** ASoC control `Headphone Jack` (`amixer -c 0 cget
  iface=CARD,name='Headphone Jack'`) reads `off` with nothing plugged in.
  RK817 `Playback Path` items: OFF/SPK/HP/SPK_HP. Polarity is
  unconfirmed until headphones are inserted.
- **GB (Gambatte):**
  - 59.8 fps measured against 59.7275 nominal.
  - The green palette in C77 comes from `gambatte_gb_colorization=internal`,
    which is keyed on the core name `gambatte`.
  - (phase4-gb-content.md, phase4-installed-core-session.md)
- **Save state and store:**
  - Runtime state goes to `/run/muos/storage/pickles/state/<core>/…`.
  - The durable store is on p3 at `MUOS/port-saves-v1`. It holds immutable
    MUOSSAV1 bundles; HEAD holds CURRENT/PREVIOUS/NEXT, with a 32-commit
    limit and no GC.
  - (phase4-gb-state.md, phase4-save-store.md)
- **Library load order:** libmuxmod must load before libui, because
  `mux_tick` won't resolve otherwise. (phase4-frontend-libs.md)

## Recovery facts

- **original32:**
  - The stock dArkOSen card. Since M1 it is the flasher station: boot it
    in slot 1 with the target card in slot 2 (`/dev/mmcblk1`) and run
    `flash-card.sh darkosen` (it gets our key as root once). Never write
    original32 itself.
  - Power off before swapping cards.
  - When booting dArkOSen, keep the test card out of slot 2. Otherwise it
    automounts its FAT as `/roms2`.
  - (phase4-memory-monitor.md, phase4-linux-diagnostic.md)
- **Black screen:** wait 2 minutes before powering off.
  (phase4-native-graphics.md)
- **Card guards (retired in M1):** the C01/C07 bootstrap and harness were
  locked to the test128 CID and exact capacity, and halted with
  "STOPPED - media guard" on any other card or with original32 in slot 2.
  The M1 init has no card guard. (The pre-M1 baseline image that still
  carried it was retired on 2026-11-12.)
- **Full-card images (M1):** `make-recovery-image.sh` composes them
  rootless on the host from a `device.sh capture` (consistent read:
  services quiesced, root ro, p3 unmounted, prefix hash re-checked). It
  runs e2fsck on p2 and p3 and rebuilds p3 with the same label, UUID and
  4.4-safe features (`has_journal ext_attr resize_inode dir_index filetype
  extent sparse_super large_file uninit_bg dir_nlink extra_isize`).
  The images are private: Wi-Fi PSK, SSH host key, authorized_keys.
- **Superseded:** the C89 p2-only Deck repair flow and the C82 offline
  backup (`build/phase4/offline-backup`, still kept, private).
- **Untested:** power loss or SIGKILL during any write.
