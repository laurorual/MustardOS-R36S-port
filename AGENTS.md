# muOS R35S/R36S Port

## Goal

Develop a native AArch64 port of MustardOS (muOS) for genuine RK3326-based
R35S/R36S handhelds. The final goal is a standalone bootable firmware, not an
EmulationStation theme or a permanent muOS-on-dArkOSen installation.

Current phase, recovery image, open problems and next milestone live in
`docs/STATUS.md` (current state only, about 150 lines). Read it at the
start of every session; update it at the end of every milestone.
How-tos (flashing, building, trial root, trial kernel, boot sequence) are
in `docs/procedures.md`; finished milestones, per-step details and T3
results go to `docs/milestones.md`, not STATUS.

## Target Hardware

Initial test device:
- Handheld: R35S — SoC Rockchip RK3326 (Cortex-A35), AArch64
- Device tree model: R36S-V12 2023-08-18 Panel 0
- Current firmware: dArkOSen, Debian 13 (FAT boot, Btrfs root)
- Graphics: DRM/KMS and framebuffer available

Do not assume all R35S/R36S panels or hardware revisions are identical.

## Upstream References (READ-ONLY)

refs/muos/frontend, refs/muos/internal, refs/muos/tool, refs/darkosen,
refs/rocknix

- Never modify, commit, reset or clean these repositories.
- refs/ is Git-ignored: search with `rg --no-ignore <pattern> refs/...`.
- Search narrowly and read only the relevant excerpts; never read whole
  subsystems into context.

## Priorities (in order)

1. Recoverability: the device is disposable, but every brick costs a manual
   reflash by the user. Always keep a known-good recovery image available.
2. Disk space on the host: the SSD is small. Every task must avoid
   unnecessary copies, caches and images.
3. Throughput: deliver larger, coherent milestones per user test cycle.
4. Token efficiency: avoid re-reading, verbose logs and redundant docs.

## Way of Working: Milestones

Work is organized in milestones, not micro-steps.

- A milestone is a coherent batch of changes that delivers one user-visible
  or architectural result (e.g. "input mapping + battery + brightness").
- At the start: propose a short plan (goal, files touched, tests, what the
  user must check). For large or risky milestones, wait for approval;
  otherwise proceed.
- During: implement the whole batch, validating with T0–T2 tests (below)
  as you go. Fix your own failures before involving the user.
- Involve the user only when the milestone is complete and has passed T0–T2,
  or when blocked by a decision or a physical test that cannot be avoided.
- At the end: one commit (or a few logical commits), update
  `docs/STATUS.md`, and hand the user a single consolidated T3 checklist.

Explain tradeoffs only for non-obvious decisions. Trivial edits need no
write-up.

## Test Levels

- T0 — Host static: build, compiler warnings, shellcheck, unit/lint checks.
- T1 — Host runtime: run AArch64 binaries in the container (qemu-user) where
  possible; inspect ELF/ABI/linked libraries against the target sysroot.
- T2 — Device automated (SSH, agent runs it): deploy to the scratch area,
  run tests, collect logs and exit codes via `port/scripts/device.sh`.
- T3 — Device manual (user): only what needs eyes/hands — display, buttons,
  audio, boot from SD card. Batch all T3 checks into one checklist per
  milestone, with expected results for each item.

A successful compilation does not prove runtime compatibility; T1/T2 are
required before T3.

## Device Access (SSH)

The agent has full autonomy on the test device over SSH, including
flashing, repartitioning and overwriting the system. All device storage
is the microSD card in slot 1; its contents are disposable and a brick is
recovered by reflashing the card on the host.

Prefer `port/scripts/device.sh` for repeatable actions so tests stay
reproducible and logs are collected consistently.

Because each brick costs a manual reflash (a T3 cycle) and loses SSH
access until then:
- Keep one known-good, flashable recovery image in dist/ (counts toward
  the five-version limit), name it in docs/STATUS.md and keep the flash
  steps in docs/procedures.md.
- Before writing the bootloader, partition table or root filesystem,
  make sure the change was validated as far as possible at T0–T2 and
  that the recovery image matches the current card layout.
- If a change leaves the device unreachable, tell the user immediately:
  what was written, the likely cause, and the exact reflash steps.

## Repository Layout

- port/   original port code (incl. port/scripts/, port/packaging/)
- docs/   documentation (STATUS.md, procedures.md, milestones.md,
          hardware notes)
- build/  temporary build files (Git-ignored, compressible, disposable)
- dist/   release artifacts (Git-ignored)

Never add build/, dist/, refs/, ROMs, private keys, seeds or private
provisioning records to Git. Verify licenses before copying upstream code;
prefer reusing hardware knowledge over copying whole subsystems.

## Disk Space Rules

The host disk is small; treat space as a first-class constraint.

- Build only the changed component; reuse installed SDKs and containers.
- Generate a full firmware image only when the milestone changes the
  filesystem/image or needs a firmware checkpoint.
- Never duplicate a full rootfs with a plain copy. On Btrfs use
  `cp --reflink=always` or subvolume snapshots; otherwise patch in place.
- Keep build/ compressed (Btrfs zstd) and cap ccache size.
- Keep at most five firmware versions, tracked in
  `port/packaging/storage-retention.json` (record the reason for any
  exception). Keep at most five named Git restore checkpoints.
- Preserve frozen proof files and private recovery material.
- Before deleting outputs: dry-run `port/scripts/retention.py retire`
  and review the listed files. Details in `docs/storage.md`. Never
  auto-clean refs.
- At the end of a milestone, report disk usage of build/, dist/ and
  container images if it grew significantly.

## Build Policy

- Use the containerized toolchain; the host runs Bazzite Linux (immutable).
- Never modify the host OS to satisfy dependencies.
- Review AArch64 compiler flags, ABI and sysroot compatibility before
  deploying binaries.

## Token Efficiency

- Start from `docs/STATUS.md` instead of re-exploring the repository.
- Redirect long build/test output to files under build/logs/ and report
  only summaries, errors and the relevant lines.
- Don't paste large files or diffs back to the user; reference paths.
- Record durable findings in docs/ once, concisely; don't write a document
  per small task.

## Reporting

At the end of each milestone report briefly:
- What was done and which tests (T0–T2) passed.
- The T3 checklist for the user.
- What remains unverified or risky, and the proposed next milestone.
