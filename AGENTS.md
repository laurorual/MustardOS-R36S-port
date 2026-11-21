# muOS R35S/R36S Port

## Goal

Develop a native AArch64 port of MustardOS (muOS) for genuine RK3326-based
R35S/R36S handhelds. The final goal is a standalone bootable firmware, not an
EmulationStation theme or a permanent muOS-on-dArkOSen installation.

The path from the current state to a public v1.0 is the release plan in
`docs/roadmap.md`. Every milestone comes from that plan.

## Documents

- `docs/STATUS.md`: current state only (about 150 lines): phase, device,
  recovery image, open problems, decisions, T3 queue, current milestone.
  Read it at the start of every session; update it at the end of every
  milestone.
- `docs/roadmap.md`: the release plan (remaining milestones up to v1.0
  and beyond), the approach and the kernel-base assessment.
- `docs/procedures.md`: how-tos (flashing, building, trial root, trial
  kernel, boot sequence). Name images generically ("the recovery image in
  STATUS"), never a specific version.
- `docs/milestones.md`: finished milestones, per-step details, T3 results.
- `docs/hardware-findings.md`: durable hardware facts. Read the relevant
  section only when needed.

Keep these current: when a milestone changes a fact stated in roadmap,
procedures, hardware-findings or storage, fix it in the same milestone. A
stale document is a bug.

## Target Hardware

- Handheld: R35S. SoC Rockchip RK3326 (Cortex-A35), AArch64.
- Device tree model: R36S-V12 2023-08-18 Panel 0.
- Test card `test128` in slot 1 runs the port's own firmware.
- `original32` (stock dArkOSen) is the flasher station only.

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
3. Throughput: deliver large, coherent milestones; the user's time for
   physical tests is the scarcest resource.
4. Token efficiency: avoid re-reading, verbose logs and redundant docs.

## Way of Working: Milestones

**Size.** A milestone is a large batch from the release plan: typically
several work sessions and 6–15 items, delivering a user-visible result or
closing a whole area (e.g. "daily-driver polish", "public release
candidate"). Don't create follow-up micro-milestones (no "M4e.1"-style
splits) unless a regression blocks normal use.

**Planning.** At the start, write a short plan in STATUS (goal, items,
tests, expected T3 items). Proceed without approval unless the milestone
needs a decision listed in "Decisions for the user" or a bootloader
write.

**Don't stop for T3.** An item that needs the user's hands or eyes goes
into the **T3 queue** in STATUS; then continue with the next item. Hand
the milestone over only when all of its items are done to T0–T2, or when
every remaining item is blocked. T3 findings from the previous milestone
are fixed inside the current one, not in a new milestone.

**T3 cycle.** One consolidated checklist per milestone (aim for ≤ 12
items, grouped by screen or activity, each with the expected result).
While the user hasn't done it, keep working on the next milestone from
the plan; fold their results in when they arrive.

**Decisions.** Collect anything that needs the user in "Decisions for the
user" in STATUS, with your recommendation, and continue with the work
that doesn't depend on it.

**End of a milestone:** commits, STATUS updated (including the T3 queue
and the next milestone), stale docs fixed, a short report (below).

Explain tradeoffs only for non-obvious decisions. Trivial edits need no
write-up.

## Heavy Systems (user rule, 2026-11-20)

For systems the muOS cores can't run stably and fast (PSP, NDS, DC,
Saturn, N64...), maximum performance comes first:

- Closed-source and standalone emulators and R36S-specific settings are
  all allowed; overclocking is an option for stubborn emulators.
- Main reference: dArkOSen (how it runs each heavy system on the R36S).
  Also consider findings from the web (Reddit, other R36S systems) and
  own ideas that may perform better.
- Integrate standalone emulators as "native" as possible (auto save state
  on exit and load on start, volume/brightness overlay, shortcuts close
  to the other systems), but never above performance in priority.

## Test Levels

- T0 — Host static: build, compiler warnings, shellcheck, unit/lint checks.
- T1 — Host runtime: run AArch64 binaries in the container (qemu-user) where
  possible; inspect ELF/ABI/linked libraries against the target sysroot.
- T2 — Device automated (SSH, agent runs it): deploy, run tests, collect
  logs and exit codes via `port/scripts/device.sh`.
- T3 — Device manual (user): only what needs eyes/hands — display, buttons,
  audio, physical plugs, flashing. Batched per milestone (see above).

A successful compilation does not prove runtime compatibility; T1/T2 are
required before T3.

## Device Access (SSH)

The agent has full autonomy on the test device over SSH. All device
storage is the microSD card in slot 1; its contents are disposable and a
brick is recovered by reflashing the card on the host.

Prefer `port/scripts/device.sh` for repeatable actions so tests stay
reproducible and logs are collected consistently.

**Pre-authorized, also when the user is away** (the fallbacks make them
recoverable without a reflash):
- Writing p2 with `muos-root-trial write-p2` after the same p2 passed T2
  as the trial root.
- Installing, booting and promoting a trial kernel/DTB with
  `muos-boot-slot`, after it passed T2 as the trial boot.
- `install-rootfs.sh` and any change under p3.

**Needs the user nearby** (a failure costs a manual reflash): writing the
bootloader, the boot records' main/previous by hand, or the partition
table. Do these only in a session where the user said they are present.

Before writing the bootloader, partition table or root filesystem, make
sure the change was validated as far as possible at T0–T2 and that the
recovery image matches the current card layout. If a change leaves the
device unreachable, tell the user immediately: what was written, the
likely cause, and the exact reflash steps.

Never boot a public image variant on the bench device unless the user is
there to reflash: it has no developer SSH access.

## Repository Layout

- port/   original port code (incl. port/scripts/, port/packaging/)
- docs/   documentation (see "Documents")
- build/  temporary build files (Git-ignored, compressible, disposable)
- dist/   release artifacts (Git-ignored)

Never add build/, dist/, refs/, ROMs, private keys, seeds or private
provisioning records to Git. Verify licenses before copying upstream code;
prefer reusing hardware knowledge over copying whole subsystems.

## Disk Space Rules

The host disk is small; treat space as a first-class constraint.

- Build only the changed component; reuse installed SDKs and containers.
- Generate a full firmware image only when the milestone changes the
  filesystem/image or needs a firmware checkpoint: normally once per
  milestone, at its end.
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

**Recovery promotion (user rule, 2026-11-13):** when a milestone's T0–T3
show no problems, or only small ones that are easy to fix later and don't
affect gameplay or OS navigation, promote its image to recovery and
retire the oldest kept version (never the image-build base), without
asking.

## Build Policy

- Use the containerized toolchain; the host runs Bazzite Linux (immutable).
- Never modify the host OS to satisfy dependencies. Never use sudo.
- Review AArch64 compiler flags, ABI and sysroot compatibility before
  deploying binaries.

## Token Efficiency

- Start from `docs/STATUS.md` instead of re-exploring the repository.
- Redirect long build/test output to files under build/logs/ and report
  only summaries, errors and the relevant lines.
- Don't paste large files or diffs back to the user; reference paths.
- Record durable findings in docs/ once, concisely; don't write a document
  per small task.

## Language

The user may write in Portuguese or English: reply in the language of
their message. All files in the repository (docs, code, comments, commit
messages) stay in English.

## Reporting

At the end of each milestone report briefly:
- What was done and which tests (T0–T2) passed.
- The T3 checklist for the user.
- Decisions needed, what remains unverified or risky, and the next
  milestone from the release plan.
  
## Telegram Communication

- Use the official Telegram plugin's `reply` tool to notify me whenever you need information, clarification, decisions, or my intervention during a task.
- When my input is required, clearly explain what you need and wait for my response before proceeding.
- Upon completing a task, send a summary via Telegram outlining the results and any remaining issues.
- Avoid unnecessary notifications during routine operations.
