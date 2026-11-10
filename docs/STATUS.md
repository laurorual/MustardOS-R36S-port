# Project status

Consolidated 2026-11-10 from the C1–C122 reports (now in
[archive/phase4/](archive/phase4/README.md)). Update at the end of every
milestone. See also [hardware-findings.md](hardware-findings.md),
[roadmap.md](roadmap.md), [compatibility-matrix.md](compatibility-matrix.md)
and [storage.md](storage.md).

## Current phase

**Phase 4 (standalone firmware base) is in progress.** The latest milestone
is **C122** (2026-11-09). It installed the resident batch contract and
validated zero-upload adoption over SSH. There was no new GUI cycle.

The roadmap still calls Phase 5 "not started". In practice, its first
bring-up steps (own U-Boot, kernel and ext4 root on the test card) have
already run; see [Contradictions](#contradictions).

## Device and bench state (last recorded 2026-11-09)

- **Device:** R35S Panel 0 at `192.168.15.15:2222`, boot counter **84**,
  running the **C07** base init (inittab → network, SSH, root ext4 RO). No
  reboot was requested after C122.
- **IP:** assigned by DHCP and changes between boots. Identify the boot by
  its counter and UUID, not by the IP.
- **test128 (128 GB):** in the console. p1 FAT `MUOSDIAG`, p2 ext4 root
  512 MiB RO, p3 ext4 `MUOSDATA` (prefs, saves, private ROM).
- **original32 (32 GB, stock dArkOSen):** stored away. It is the recovery
  card and must never be written.
- **Steam Deck:** retired. It was the offline card reader for C82–C97; the
  user removed its helpers and key in C101.
- **SSH:** key-only, keys in `build/phase4/private/c07-*`. The command is in
  [hardware-findings.md](hardware-findings.md#network-and-usb).

## What works on the device

**Confirmed by the user (T3):**
- **Display:** 640×480 via SDL2 KMSDRM + Mali r13p0 GLES at ~59.6–59.9 fps
  (C03).
- **Controls and frontend:** all controls via muinput `rk-r35s-p0`. The full
  muOS frontend works, including submenus, volume and brightness (C08–C11).
- **Speaker audio:** works in menu and games at codec gain 215, prefs 55/70.
  It is clean after reboot thanks to the C36 prime (C39).
- **Wi-Fi + SSH:** works from cold boot (C08) and across 3 warm reboots with
  no replug (C18, Wi-Fi-only policy).
- **Preferences:** persist across reboot (C20/C21).
- **Game Boy:** `muxretro` + Gambatte with the private ROM.
  - Image, sound and D-pad work.
  - Fn+Start exits; Fn+R2 / Fn+L2 save and load state.
  - Durable p3 saves survive reboot (C49–C54).
  - Runs through the installed caller (C104–C106) and the resident ROM
    (C116).
  - The batch host runs menu→GB→menu (C121), 4.27 s from selection to first
    frame.
- **NES:** FCEUmm runs with an MIT test ROM, but too slowly (C47/C48).

**Automated only (T2):** C122 install and validation (guard 200); C105–C120
caller, capsules and resident installs; C57/C62/C72/C76 package installs;
controlled reboot via the C12 preflight.

## Broken, caveated or unverified

- **No flashable recovery image exists.** The `build/` images are audit-only.
- **Audio after reboot:** the PCM can run at half rate. The cause is unknown;
  the C36 zero-prime only masks it.
- **Audio in general:** every game session has 3–8 underrun bursts, the help
  WAVs are inaudible, and headphones are untested.
- **NES speed:** about 51.4 of 60.1 fps.
- **Launch latency:** unattributed, and the timing is too coarse for speed-up
  percentages.
- **Wi-Fi:** fails if the dongle is inserted *during* boot (boot 80); the
  user deferred this. Bluetooth is blacklisted and unqualified.
- **Never tested:**
  - Power key, physical poweroff, suspend, battery/charging
  - Cold-boot qualification, long runs, power loss during writes
  - LEDs, rumble, blank/unblank
  - Autostart (C12 inactive), general ROM browser, SRAM/new saves
  - Other panels
- **Never booted:** rootfs images C38/C56/C64/C69/C78 and the C79 card image.
  Writing C79 whole would destroy p3.
- **Init/fsck:** the BusyBox rcS/rcK/shutdown integration is incomplete. The
  last offline fsck of p2 was in C20. Never fsck the live root.

## Open decisions

1. **Recovery image.** AGENTS.md requires a flashable known-good image in
   `dist/`.
   - Current options are only swapping in original32, or the C89 p2-only
     repair, which needs the retired Deck.
   - A new image must not wipe p3, replay the seed or roll back the counter.
2. **Licences (private-only for now):** Mali r13p0 (Hardkernel query
   drafted, not sent), DDR/miniloader/BL31/BL32, the dirty U-Boot, Gambatte
   (GPLv2/GPLv3/MIT), BT firmware. Tracked in
   `port/packaging/pending-licenses.json`.
3. **Kernel base:** rk351 4.4 BSP vs a ROCKNIX fallback. Not revisited since
   2026-10-27.
4. **Autostart:** needs rcS/rcK ownership and log retention, and a decision
   on whether the C79 layout goes into the image.
5. **Official muOS rootfs recipe:** not found; `mustardroot_external` is a
   lead only.

## Contradictions

These are the ones that matter for current work. The full list is in
[archive/phase4/README.md](archive/phase4/README.md#contradictions).

- **Panel timing:**
  - The matrix gives the stock Linux DTB as 50 MHz, h 450/46/450.
  - phase4-uboot-panel.md and the measured DRM mode give 29 MHz, htotal 732
    / vtotal 661.
  - Only the U-Boot DTB is clearly 50 MHz (450/70/450).
- **Phase 5:** the roadmap says "not started", but own-card boots and the
  C94/C97 p2 migration already happened.
- **Warm Wi-Fi:** fixed in C18, yet phase4-boot-once.md and
  phase4-boot-coordinator.md still say a replug is needed.
- **C123 guard:**
  - phase4-resident-batch.md says guard 200 already includes the C122 files.
  - The checkpoint's C123 plan says to "add nine hashes to the current guard
    (200)".

## Do not repeat or touch

- **Consumed claims:** never re-apply or delete them to retry. They are
  `resident-batch/install.1a1mvhj9`, `internal-rom/import.tgknjpow` (keep its
  `before.tar`), `resident-assets/install.0uvf0x6y`, capsule-prepare,
  manual-caller, the C104 reboot request, the C93/C100 compose, and the C94
  package.
- **Boot tokens:** don't re-arm the `.once` tokens (C12/C25/C94).
- **Card writes:** never restore an old p2 byte-for-byte, because it replays
  the seed and rolls back the counter. Never write the C79/C100 factory image
  to test128.
- **Bootloader:** never run dArkOSen `flash_uboot.sh` or U-Boot `saveenv`.
- **Warm Wi-Fi:** don't retry the dead ends listed in hardware-findings.md.

**Old doc paths:** about 79 `port/` files still reference `docs/analysis/`,
which is now `docs/archive/phase4/` (see the
[archive README](archive/phase4/README.md)). New packagers must reference docs
under `docs/`.

## Proposed next milestone

**M1 — recovery image + C123 resident graphical cycle.**

1. **Recovery image** in `dist/` for the 3-partition test128 layout.
   - It writes the bootloader offsets and p1/p2, preserves p3, and advances
     the seed and counter.
   - Host-only flashing steps go in this file.
   - Tested at T0/T1, plus a T2 dry run against the device's partition
     table.
2. **C123:** point the C121 graphical executor at the installed loader
   (`/usr/libexec/muos-batch-v1`, `load.sh adopt`) instead of six uploads.
   Then run the offline routing/refusal checks.
3. **T3:** one menu→GB→Fn+L2→Fn+Start→menu round. Optionally, flash the
   recovery image to a spare card and boot it.

**Next after M1:** power — Power key, poweroff, suspend, battery and
headphones. It is the largest untested area before autostart.
