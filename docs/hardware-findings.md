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
- **⚠ Conflict (panel timing):**
  - compatibility-matrix.md quotes the stock Linux Panel 0 DTB
    (`rk3326-r36s-linux.dtb`, SHA256 `5634eb3e…`) as 50 MHz,
    h 450/**46**/450, v 17/5/13.
  - phase4-uboot-panel.md says the Linux DTB is 29 MHz, which matches the
    measured mode.
  - Which DTB or mode the 50 MHz/hsync-46 figure describes is unresolved.
- **Framebuffer:**
  - `/dev/fb0` is 640×480, 32 bpp XRGB, stride 2560, with an empty `fix.id`.
  - **mmap returns EINVAL**, so muOS musplash needed a pread/pwrite fallback
    (patch0001).
  - musplash/mmap also triggered `Bad page map` / `Bad rss-counter` on the
    stock kernel, so that path stays excluded.
  - muxretro leaves its last frame on the framebuffer after exit.
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
- **Boot command and root check:**
  - Kernel cmdline: `root=PARTUUID=4d554432-02 rootfstype=ext4 rootwait ro`,
    no initramfs, `booti 0x02000000 - 0x01f00000`. The C79 image uses
    `init=/sbin/muos-ext4-diag`.
  - Compare root MAJ:MIN using `findmnt -rn`; padded output once caused a
    false "Root device mismatch".
  - (phase4-ext4-diagnostic.md, phase4-card-image.md)
- **Init:**
  - BusyBox 1.37.0 init runs its SHUTDOWN actions, then `kill(-1)`. A
    failing script **does not cancel** the shutdown, so every stop check must
    finish before the reboot/poweroff request reaches PID 1.
  - Service order: eudev → D-Bus → S90 storage → S95 core/audio/muinput →
    S96 input/mapping → S99 UI.
  - `muxfrontend` SIGTERMs itself if its parent is PID 1, which is why it
    needs `muos-ui-supervisor`.
  - (phase4-boot-coordinator.md, phase4-init-services.md)
- **Entropy:**
  - HW_RANDOM=y, but HW_RANDOM_ROCKCHIP and CRYPTO_DEV_ROCKCHIP_V2 are off,
    so the RNG becomes ready only after about 7–11 s. The deadline was raised
    from 5 s to 60 s (S05 capped at 90 s).
  - The seed lives in `/var/lib/muos-seedrng` (directory 0700, file 0400,
    256 B). Credit it once per boot only.
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
- **Write and data rules:**
  - The only routine write target is p2, at byte offset 134217728 with
    length 536870912. The ranges 0–128 MiB and 640 MiB–end are protected.
  - The 640 MiB factory images (C70/C79) contain only p1/p2. Writing one
    whole would destroy p3.
  - p3 holds `MUOS/preferences`, `MUOS/port-saves-v1` and
    `MUOS/port-roms-v1`.
  - (phase4-root-migration.md, phase4-p2-write-core.md)
- **ext4 feature flags:**
  - Root and data ext4 are created **without** 64bit, metadata_csum(_seed),
    orphan_file or fast_commit, to stay compatible with kernel 4.4.
  - The resulting images report compat 0x3c / incompat 0x242 / ro_compat
    0x46b.
  - (phase4-rootfs.md, phase4-gambatte-image.md)
- **Private state on p2:**
  - Network config and host key: 0600.
  - `seed.credit`: 0400.
  - Boot counter `var/lib/muos-diagnostic/boot-seq`: 0600, and must stay
    0600. C07 sets umask 077 itself.
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
  - LAN only, no DNS.
  - (phase4-network-ssh.md)
- **SSH:**
  - Port 2222, root, key only. The host key is generated on the device after
    the RNG is ready.
  - Command:
    `ssh -p 2222 -i build/phase4/private/c07-client -oIdentitiesOnly=yes
    -oStrictHostKeyChecking=yes
    -oUserKnownHostsFile=build/phase4/private/c07-known_hosts root@<IP>`
  - Host key fingerprint
    `SHA256:fDW+/iNaWgqPwqBtO/ESuKPSQHvYN1PSo2RHfilOxK0`.
  - (phase4-network-ssh.md, phase4-resume-checkpoint.md)
- **Bounded runs:** `muos-run-bounded` rejects limits over 120 s with rc 125.
  (phase4-network-ssh.md)

## Power and battery

- **Battery:** RK817 fuel gauge, design_capacity 3140, qmax 3454. Not
  validated. (compatibility-matrix.md)
- **LEDs and rumble:** GPIO77 is the battery LED. LEDs and rumble are
  untested. (compatibility-matrix.md)
- **Power key:**
  - A long press powers off from the U-Boot monitor. This is the only Power
    behaviour confirmed so far.
  - The Linux Power key is `rk8xx_pwrkey` (event0) and is untested.
  - (phase4-memory-monitor.md)
- **CPU:**
  - The port caps the CPU at 1296 MHz (stock allows 1512).
  - Under load the governor read performance at 1296000 kHz.
  - (phase4-bsp-foundation.md, phase4-nes-performance.md)
- **Reboot:** a controlled reboot through the C12 preflight works. Physical
  poweroff and suspend are untested. (phase4-boot-power.md)

## Emulation stack facts

- **Host:** the native host is muOS `muxretro`, not RetroArch. Port patches
  0003, 0006–0012 and 0015 are in the lineage; 0013 and 0014 are
  experimental. (phase4-muxretro-integration.md, phase4-nes-performance.md)
- **NES (FCEUmm):**
  - About 51.4 fps against 60.0998 nominal. A frame takes 19.4 ms: 13.5 ms
    core plus 5.6 ms present.
  - O3/LTO reaches 53.57 fps. Software pacing gives no gain.
  - (phase4-nes-performance.md)
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
  - The stock dArkOSen card is the independent recovery and must never be
    written.
  - Power off before swapping cards.
  - When booting dArkOSen, keep the test card out of slot 2. Otherwise it
    automounts its FAT as `/roms2`.
  - (phase4-memory-monitor.md, phase4-linux-diagnostic.md)
- **Black screen:** wait 2 minutes before powering off.
  (phase4-native-graphics.md)
- **Card writer guard:** the writer is locked by CID and exact capacity,
  refuses to run if the dArkOSen CID is present, and verifies writes by
  re-reading. (phase4-linux-diagnostic.md)
- **p2-only repair flow (C89):**
  - Steps, run in the Deck reader:
    1. Seal a fence.
    2. Capture p2.
    3. Compose a 512 MiB ext4 from the C82 root, with a fresh unclaimed seed,
       counter+1 and root 0755.
    4. Write exactly p2, then re-read.
    5. Compare MBR/p1/p3.
  - Evidence: `dist/phase4/p2-recovery-native`.
  - The flow needs the retired Deck workflow.
  - (phase4-p2-recovery.md, phase4-recovery-image.md)
- **Backups:**
  - `build/phase4/offline-backup` (C82) holds a 640 MiB prefix plus a USTAR
    of prefs and saves. It contains root, seed and credentials, so it is
    **host-only** and never goes into `dist/`.
  - Never restore old counters, seeds or keys from it.
  - (phase4-offline-backup.md, phase4-userdata-offline.md)
- **No documented full-card image recovery:** there are no `dd`/`bmaptool`
  steps for a full-card recovery image anywhere in the reports. See STATUS
  open decision 1.
- **Untested:** power loss or SIGKILL during any write.
