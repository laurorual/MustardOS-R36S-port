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
