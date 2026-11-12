# Roadmap: native AArch64 muOS for the R35S (Panel 0)

This is the condensed version written on 2026-11-10. The original roadmap and
its full milestone changelog (C1–C122) are in
[archive/phase4/roadmap.md](archive/phase4/roadmap.md). The current state is
in [STATUS.md](STATUS.md).

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
  `port/packaging/pending-licenses.json` and resolve them at the end.

## Phases

| Phase | Goal | State |
|---|---|---|
| 0 | Read-only baseline inventory | Done in practice. The original text never closed it; the remaining items were gathered during Phases 1–4. |
| 1 | Run one native muOS C component (`muinput --list-devices`) | **Done** (23/10) |
| 2 | Display and input separately (fb, SDL/GLES, all controls) | **Done** (23/10). Brightness and blank tests never run. |
| 3 | First muOS menu on the Debian bench | **Done with caveats** (24/10). Help WAVs are inaudible. |
| 4 | Standalone firmware base: own boot chain, kernel, rootfs, init, frontend, cores, persistence | **Done** (C1–C122, closed by M1 on 10/11). |
| 5 | Separate-card image and native bring-up | **In progress.** M1 (10/11): flashable image, boot straight to the menu, persistent saves. |
| 6 | Consolidation and compatibility (board/panel/kernel matrix, automated builds) | Not started |

**Phase 4 exit criteria:**
- A reproducible manifest of sources, patches and licences.
- A pinned toolchain and sysroot.
- Complete init.
- Kernel, DTB and modules from a single build.
- A bootable rootfs.
- No blob without resolved provenance or licence.

**Phase 4 milestone arc** (details in the archive):
- B01: ext4 boot.
- C01: init.
- C02: entropy.
- C03: GL.
- C04: frontend.
- C05–C06: audio.
- C07–C08: Wi-Fi and SSH.
- C09–C12: controls, profile, session, power coordinator.
- C13–C18: warm Wi-Fi.
- C19–C21: preferences.
- C22–C27: rootfs install and calibration.
- C28–C39: post-reboot audio rate.
- C40–C68: libretro/muxretro, NES/GB, save store, frontend-lib provider.
- C69–C79: offline images.
- C80–C97: p2 migration and recovery, first C79 boot.
- C99–C106: layout and installed caller.
- C107–C122: resident assets and ROM, launch latency, batch caller.

**Phase 4 remaining work:**
- **Init and boot:** full rcS/sysinit/shutdown integration; permanent UI
  autostart (C12 is inactive); a general ROM browser.
- **Power:** Power key, physical poweroff, suspend.
- **Qualification:** cold boot, long-duration runs, headphones.
- **Hardware:** battery and charging, LEDs, Bluetooth.
- **Audio:** the original help sounds.
- **Performance:** NES speed, audio underruns, launch latency.
- **Provenance:** reproduce the installed boot chain; resolve the
  redistribution licences.

**Phase 5 order (from the original plan):**
1. Boot to a shell.
2. Panel, brightness and input.
3. Frontend and storage.
4. Audio, battery, LEDs and power.
5. One AArch64 core.
6. Shutdown, suspend/resume, long cycles.

Exit: the separate card boots muOS AArch64, runs the Panel 0 basics and shuts
down correctly without dArkOSen. Do not claim general R35S/R36S support.

Steps 1–3 and 5 ran as Phase 4 milestones; M1 added the flashable image,
autostart and clean reboot/shutdown through init. Step 4 (battery, LEDs,
power) and step 6 (suspend, long cycles) remain: milestones M2 and M3 in
STATUS.

**Phase 6:** extend to other boards and panels only with evidence and a
physical test. Never autodetect a panel from the SoC name. Add update
automation only after boot and recovery are proven.

## M4 proposal: first public image (2026-11-12, not started)

Goal: an image anyone with an R35S/R36S **Panel 0** can flash, with none of
the developer's identity in it, and with a clear licence position. Prerequisites:
M3d done (p3 auto-grow on first boot, log rotation, smoothness).

1. **Identity-free image.** Build a `public` variant: no Wi-Fi PSK, no
   `authorized_keys`, no host key (the worker already creates one on first
   boot), dropbear off until the user enables SSH. A T2 check refuses an
   image that contains `network.conf`, keys or `seed.*`. The developer image
   stays a separate, private build.
2. **First-boot Wi-Fi.** Don't write a wizard: route upstream muOS's own
   network screen (muxnetwork: SSID scan, on-screen keyboard, writes
   `config/network/*`) to the port worker, which generates the
   wpa_supplicant config from those values instead of the private file.
   SSH/SFTP follow muOS's "web services" toggles (password set in muOS).
3. **Licences** (`pending-licenses.json`), in order of risk:
   - *Mali r13p0 userspace (Hardkernel zip, no terms): the blocker.* Find a
     libmali build with redistribution terms that matches our kbase
     (rockchip-linux/libmali bifrost-g31 packages), or ship without it,
     which isn't viable for the GLES frontend.
   - *Boot payloads* (DDR, miniloader, BL31, BL32): match each pinned file to
     its rkbin counterpart and carry rkbin's licence notice.
   - *GPL obligations* (kernel, U-Boot, BusyBox, Buildroot packages, the
     GPLv3 muOS frontend, gpsp/pcsx_rearmed/gambatte): publish the pinned
     source bundle next to the image (the build is already reproducible from
     pinned inputs).
   - *Non-commercial cores* (snes9x2005_plus, picodrive): fine in a free
     image. Never in a paid bundle.
   - *muOS name and assets:* label the image as an unofficial port and ask
     the MustardOS team about naming and theme asset terms before publishing.
4. **Scope statement:** Panel 0 only, with the DTB selection documented like
   dArkOSen's. No other-panel claims without Phase 6 evidence.
5. **Release artifacts:** image + SHA256 + source bundle + changelog;
   flashing with any imager (the image already boots on any card ≥ 2 GiB).

T3: flash the public image on a blank card, first-boot Wi-Fi from the menu,
enable SSH from the menu, no developer key accepted.

## Kernel base, reassessed 2026-11-12

| Option | For | Against |
|---|---|---|
| **rk351 4.4.189 BSP (current)** | Everything qualified (sleep, audio, battery, Wi-Fi, panel); reproducible build | Mali r13p0 blob with unclear terms; vendor boot payloads; ext4 feature limits; no uclamp; DWC2 must be unbound around suspend; DDR devfreq not synced to the VOP (no `vop-bw-dmc-freq`) |
| **dArkOSen 5.10 (announced, not released)** | Newer drivers, uclamp, ext4, likely better USB suspend | Still a Mali blob (newer g-series) and vendor boot chain; no RK3326 5.10 source published yet (christianhaitian/linux has only 4.4 rg351 branches; dArkOS's 5.10.226 is RK3566-only); dArkOSen itself warns it "may break clone devices" |
| **ROCKNIX mainline (6.x)** | Panfrost + Mesa removes the Mali licence blocker; open TF-A for PX30; rtw88 8821cu in-tree; maintained R36S panel mode | Full re-qualification (rk817 audio/charger, joypad, sleep, panel, battery); DDR init blob stays; months of work |

**Decision proposal:** keep 4.4 for M3d/M4-private. Don't chase 5.10: it
keeps both licence problems and adds risk, and its source isn't public.
Re-check when dArkOSen publishes the RK3326 5.10 source and DTBs; the trial
kernel + trial root path can test it without a reflash. If the Mali
licence can't be resolved in M4 step 3, the public release depends on a
mainline/Panfrost port (an M5 candidate, ROCKNIX as the reference), not on 5.10.
