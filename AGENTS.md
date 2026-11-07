# muOS R35S/R36S Port

## Goal

Develop a native AArch64 port of MustardOS for
genuine RK3326-based R35S/R36S handhelds.

The final goal is a standalone bootable firmware,
not an EmulationStation theme or a permanent
muOS-on-dArkOSen installation.

## Target Hardware

Initial test device:
- Handheld: R35S
- SoC: Rockchip RK3326, Cortex-A35
- Architecture: AArch64
- Device tree model: R36S-V12 2023-08-18 Panel 0
- Current firmware: dArkOSen, Debian 13
- Graphics: DRM/KMS and framebuffer available
- Boot partition: FAT
- Current root filesystem: Btrfs

Do not assume all R35S/R36S panels or hardware
revisions are identical.

## Upstream References

All directories below are READ-ONLY references:

- refs/muos/frontend
- refs/muos/internal
- refs/muos/tool
- refs/darkosen
- refs/rocknix

Do not modify, commit, reset, or clean these
repositories unless explicitly requested.

Because refs/ is Git-ignored, use targeted searches
with rg --no-ignore when necessary.

## Development Rules

1. All original port code belongs under port/.
2. Documentation belongs under docs/.
3. Temporary build files belong under build/.
4. Release artifacts belong under dist/.
5. Prefer native muOS implementations.
6. Reuse hardware knowledge from dArkOSen and
   ROCKNIX rather than copying entire subsystems.
7. Verify source licenses before copying code.
8. Document assumptions and compatibility issues.
9. Keep changes incremental and testable.
10. Never modify, reflash, repartition, or overwrite
    the test device without explicit authorization.
11. Preserve the existing dArkOSen installation.
12. Do not assume a successful compilation means
    the resulting binary is runtime-compatible.

## Initial Development Priorities

1. Document current RK3326 hardware support.
2. Analyze muOS boot, rootfs, and device profiles.
3. Identify display and input requirements.
4. Establish a reproducible build environment.
5. Validate the muOS frontend on the test device.
6. Develop a standalone AArch64 firmware image.

## Build Policy

Use a containerized toolchain when practical.
The development host runs Bazzite Linux.

Do not modify the host operating system to
satisfy build dependencies.

## Storage and Versioning

Use the local Git repository for original code and documentation. Do not add
build/, dist/, refs/, ROMs, private keys, seeds or private provisioning records to Git.
Reuse the installed SDKs and build only the changed component. Generate a full
firmware image when the increment actually changes the filesystem/image or
requires a firmware checkpoint; do not clone a full root for every script edit.

Keep at most five firmware versions in `port/packaging/storage-retention.json`.
Update that inventory when promoting a new version, recording the specific
reason for any older dependency or recovery exception. Preserve frozen proof
files and private recovery material. Small source history and proof metadata
are audit exceptions; they do not require another full build tree per commit.
Keep at most five named Git restore checkpoints; ordinary source commits use
Git's compact storage. Never rewrite qualified source/proof files just to prune
their build directories.

Before deleting historical outputs, review a dry run of
`port/scripts/retain-phase4-builds.py`, verify its current dependency closure,
and check the resulting integrity report. This cleaner covers reviewed legacy
replicas, not arbitrary newly created paths. Extend its scope deliberately when
the retention inventory changes. No automatic cleanup of refs or devices.

Review AArch64 compiler flags, ABI and sysroot
compatibility before deploying binaries.

## Workflow

For each significant task:
- Inspect relevant upstream implementations.
- Explain the chosen approach and tradeoffs.
- Make the smallest useful change.
- Run available checks.
- Record findings in docs/.
- Report what was tested and what remains unverified.
