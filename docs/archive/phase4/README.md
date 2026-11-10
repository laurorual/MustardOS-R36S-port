# Archive: Phase 1–4 reports (C1–C122)

These are the original per-milestone reports, in Portuguese and kept
**unchanged**. On 2026-11-10 they were moved here from `docs/analysis/` with
`git mv`, so `git log --follow` still shows their history.

Use these docs instead:
- [../../STATUS.md](../../STATUS.md): current state
- [../../hardware-findings.md](../../hardware-findings.md): durable facts
- [../../roadmap.md](../../roadmap.md)
- [../../compatibility-matrix.md](../../compatibility-matrix.md)
- [../../storage.md](../../storage.md)

## Path map

Every old path maps the same way:

`docs/analysis/<name>` → `docs/archive/phase4/<name>`

The only exception is `upstream-revisions.txt`, which moved to
`docs/upstream-revisions.txt`. Relative links between archived files still
work, because they all moved together.

Links from these files to `port/`, `refs/` and `dist/` are now broken
(208 links). They were written as `../../port/…`, which was correct from
`docs/analysis/`, but from this directory they need `../../../port/…`. The
originals are kept byte-for-byte, so these links were left as they are.

About 79 files under `port/` still use the old paths. They were left unchanged
on purpose:
- The `port/scripts/package-phase4-*.py` proof packagers are one-shot. They
  refuse to run once their `dist/` proof exists, and their frozen proofs
  record source hashes.
- `port/packaging/pending-licenses.json` points to
  `hardkernel-r13-license-request.md`, `phase4-uboot-sd.md` and `roadmap.md`.
- A comment in `port/device/rk-r35s-p0/rk3326-muos-r35s-panel0-uboot.dts`.
- `port/scripts/build-phase3-menu.sh` writes a manifest line.

If you ever need to re-run one of these scripts, apply the rule above.

## Index

| Group | Files |
|---|---|
| Running log and plans | `phase4-resume-checkpoint.md` (291 KB, state head = C122), `roadmap.md`, `compatibility-matrix.md` |
| Phases 1–3 | `phase1-muinput`, `phase2-display-input`, `phase3-native-menu`, `phase3-audio-resume`, `phase3-storage-stop` |
| BSP, boot chain, rootfs | `phase4-bsp-foundation`, `-boot-chain`, `-uboot-panel`, `-uboot-sd`, `-linux-diagnostic`, `-memory-monitor`, `-rootfs`, `-init-services`, `-modules-firmware`, `-r13-runtime`, `-private-foundation`, `-historical-rootfs-lead`, `-menu-own-rootfs`, `-full-frontend`, `-base-choice`, `hardkernel-r13-license-request` |
| Graphics, input, audio | `phase4-graphics`, `-native-graphics`, `-native-input`, `-native-frontend*`, `-core-audio`, `-native-audio*`, `-audio-buffers`, `-audio-corruption`, `-irq-rate-negotiation`, `-calibrated-boot-audio-clock`, `-image-volume-calibration`, `-rw-audio-startup`, `-primed-rootfs`, `-prime-repeat` |
| Services, network, boot orchestration (C02, C07–C25) | `phase4-entropy-diagnostic`, `-ext4-diagnostic`, `-service-diagnostic`, `-network-*`, `-usb-control`, `-session-*`, `-runtime-profile`, `-boot-coordinator`, `-boot-once`, `-boot-power`, `-preferences-*`, `-userdata-offline`, `-rootfs-candidate`, `-candidate-update` |
| Emulation stack (C40–C79) | `phase4-launcher-*`, `-libretro-smoke`, `-retro-session`, `-app-selection`, `-muxretro-*`, `-nes-*`, `-gb-*`, `-gambatte-*`, `-save-store*`, `-installed-*` (except caller), `-provider-*`, `-frontend-libs*` |
| Card, root, recovery (C70, C80–C104) | `phase4-card-*`, `-recovery-image`, `-root-*`, `-offline-backup`, `-backup-native`, `-physical-capture`, `-p2-*`, `-initial-*`, `-c79-*`, `-native-layout-session`, `-reboot-layout-session`, `-deck-cleanup-current`, `storage-*` |
| Caller, resident, batch (C105–C122) | `phase4-manual-caller`, `-installed-caller-session`, `-local-preparation*`, `-prepared-capsule-session`, `-resident-*`, `-internal-rom`, `-launch-profile`, `-batch-*` |

## Contradictions

These were found during consolidation and are **not resolved**. Each entry
cites both sides.

### Hardware

- **Panel timing.**
  - compatibility-matrix.md, quoting the stock `rk3326-r36s-linux.dtb`
    (`5634eb3e…`): 50 MHz, h 450/46/450, v 17/5/13.
  - phase4-uboot-panel.md: the Linux DTB uses 29 MHz.
  - phase4-native-graphics.md: the measured mode is 29000 kHz, htotal 732,
    vtotal 661.
- **Mali library.** The name `libmali-bifrost-g31-rxp0-gbm.so` refers to two
  different files:
  - phase2-display-input.md: the stock dArkOSen copy works.
  - phase4-graphics.md: the Buildroot copy fails (UK 10.6 vs 11.7). Its
    "10.6" was later corrected in the same file and in
    phase4-bsp-foundation.md.
- **Audio route and gain.** The values change over time:
  - "persistent profile 95/SPK" (phase4-native-audio.md, matrix C05);
  - "route SPK" (phase4-menu-own-rootfs.md);
  - SPK_HP 157 → 195 → 215 (phase4-image-volume-calibration.md, current).
  - The early paragraphs in roadmap.md and the matrix were never updated.
- **Comfortable volume (phase4-core-audio.md).** The same file says both
  "pending" and "confirmed at 153,153". The second claim was on the dArkOSen
  kernel.
- **Profile version (phase4-audio-buffers.md).** The header says profile v3
  at codec 215, while the body describes v2 at 195 as approved.
- **Audio rate.** NES opened at 44100 Hz (phase4-nes-performance.md), while
  GB negotiated 48000 Hz at ALSA (phase4-gb-content.md).
- **Governor.**
  - phase4-app-selection.md receipts show "schedutil/system", which may be
    the app's option default.
  - phase4-nes-performance.md says the governor was performance at 1296000
    kHz.

### Network and storage

- **Warm Wi-Fi.**
  - Fixed by C18 (phase4-usb-control.md).
  - Still described as needing a replug in phase4-boot-once.md ("Estado
    corrente"), phase4-boot-coordinator.md, and the matrix's C06–C11
    paragraph.
  - Boot 80 later failed in a different scenario: the dongle was inserted
    during boot (C105).
- **fsck.**
  - phase4-usb-control.md: "last offline fsck after 21; boots 22..39
    unchecked".
  - phase4-userdata-offline.md: the C20 Deck pass ran fsck on all 3 volumes.
  - "fsck offline pós22..25" (C09, roadmap) is never closed.
- **Profile path.**
  - phase4-runtime-profile.md: `/usr/share/muos-r35s-profile`.
  - phase4-preferences-session.md: `/usr/libexec/muos-session/profile`.
- **p3 in the preparation doc.** phase4-preferences-preparation.md says "sem
  p3" (no p3). C20 superseded this later.
- **The 128 GB card.**
  - storage-recovery.md: SD128 has p1 FAT at `/roms2`.
  - Phase 4: test128 has 3 partitions.
  - Probably the same physical card reformatted, but no document says so.
- **C84 vs C85.**
  - phase4-root-recovery.md: C84 demonstrated the 0777 → 0755 normalisation.
  - phase4-recovery-image.md: the fixture never checked the root inode mode.
- **Deck copies.**
  - phase4-root-permissions.md and phase4-p2-initial.md: keep the Deck
    copies.
  - phase4-deck-cleanup-current.md: C101 deleted them, with no audit.
- **Sparse offline backup.**
  - storage-cleanup.md: the offline-backup areas were excluded from sparsify.
  - phase4-backup-native.md: the host copy "foi tornada esparsa" (was made
    sparse).
  - These were separate operations.

### Milestones and the running log

- **Phases 5–6.**
  - roadmap.md says phases 5–6 "continuam sem execução" (have not been run).
  - The same file records own-card boots (25/10), the C70/C79 images, and
    the C94/C97 p2 write and first boot.
- **Roadmap Phase 4 status line.** It is stale:
  - It says "284 ELF"; later counts are 305 (C23) and 308 (C78).
  - It says power is not approved; C12 approved a reboot.
  - It lists urandom warnings as open; C02 fixed them.
- **Other stale roadmap paragraphs.** Input ("mapping untested", but C01
  passed), Graphics ("integration pending"), and the post-Phase 3 pending
  list.
- **Header dates.** The headers in roadmap.md and compatibility-matrix.md
  still say 23–24/10, but the content runs to 09/11. The matrix has no
  entries for C12–C82.
- **ELF counts.** init-services.md says 283; modules-firmware.md says 284
  without explanation.
- **U-Boot builds.**
  - phase4-uboot-sd.md: BOOTDELAY=-1, `init=/bin/sh`, 857,887 B.
  - phase4-linux-diagnostic.md: autoboot after 3 s, `rdinit=/init`, 860,455
    B.
  - These are probably successive builds.
- **C109 checks.**
  - phase4-prepared-capsule-session.md and the checkpoint: 22 cases.
  - phase4-local-preparation-v3.md: 21 checks.
- **Guard for C123.**
  - phase4-resident-batch.md: guard 200 already includes the 9 C122 files.
  - phase4-resume-checkpoint.md, C123 plan: "add nine hashes to the current
    guard (200)".
- **C118 bytecode.**
  - phase4-batch-validation.md: "prototype bytecode".
  - The checkpoint: "no bytecode or ELF compiled".
- **Stale statements** that later milestones superseded:
  - phase4-batch-graphics.md says `dist/phase4/batch-graphics` must not be
    published. It was published later.
  - phase4-resident-assets.md says "same boot82"; the run actually happened
    on boot83.
  - phase4-resident-session.md has a resume command with `--boot 82`.
  - The checkpoint's old SSH example uses `.17`.
- **Chaining increments.**
  - phase4-installed-provider-session.md (C73): "no further increment should
    start automatically".
  - C74–C79 followed anyway.
  - phase4-muxretro-provider-session.md (C68) had recorded the user's
    permission to chain increments.
- **IP reuse.** 192.168.15.17 and 192.168.15.13 were each used both for the
  R35S and for the Steam Deck in different sessions.
- **Gambatte licence.**
  - phase4-nes-performance.md and phase4-gb-content.md say "GPLv2".
  - phase4-gambatte-package.md (C75) finds cc_resampler is GPLv3, and
    supersedes the earlier label.
