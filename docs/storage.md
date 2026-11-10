# Host storage and retention

This doc merges `storage-retention.md` (07/11), `storage-cleanup.md` (04/11)
and the host-side lessons from `storage-recovery.md` (Phase 3). The
originals are in [archive/phase4/](archive/phase4/README.md). The rules
summarised in AGENTS.md ("Disk Space Rules") apply in full; this file gives
the details.

## Workflow

- Edit and version code/docs in this checkout.
- Rebuild only the component that changed. Script- or doc-only changes never
  need a new 512 MiB image.
- Packages and receipts referenced by a proof are immutable. Never recycle a
  consumed attempt's private files.
- Git is local only and never pushed. The baseline commit `ce01966` was made
  on 07/11/2026; it includes C104 approved and C105 as an interrupted draft.
- Git never replaces private backups or frozen proofs.
- Never in the Git index: ROMs, `refs/`, `build/`, `dist/`, Python caches,
  keys, provisioning data.

## Limits

- At most **5 firmware milestones**, inventoried in
  `port/packaging/storage-retention.json`. The limit is enforced: a 6th
  version is refused, and a test covers this.
  - The current five are C64, C79, C89, C93 and C100, which together make
    up 7 image files:

  | Milestone | Role |
  |---|---|
  | C64 | Ancestor of the C77/C104 chain |
  | C79 | Factory image, card image and p2 reread |
  | C89 | Physical recovery reference |
  | C93 | Migrated candidate; seed and counter consumed |
  | C100 | Corrected, unprovisioned factory |

  - These are kept for audit and rebuild only. They do **not** authorise
    rewriting a card, and none is a ready-to-flash recovery image.
- At most **5 named Git checkpoints**. Current tags:
  - `checkpoint/2026-11-07-before-retention`
  - `checkpoint/2026-11-07-c105-installed`
  - `checkpoint/2026-11-07-c106-installed-caller`
  - `checkpoint/2026-11-07-c111-local-preparation`
  - `checkpoint/2026-11-07-c114-internal-rom`
- A compact source history is allowed as a recorded audit exception.

## Always preserve

- **Private material:**
  - C82 independent backup (`build/phase4/offline-backup`).
  - C20 and C95 private prefixes.
  - Reference and postboot captures.
  - C89 and C94 receipts and fences.
  - Everything under `build/phase4/private/` (SSH keys, known_hosts, C24
    backups).
- **Toolchain and sources:**
  - Both installed SDKs (`output/host` plus sysroots).
  - Kernel and bootloader downloads and sources.
  - `rootfs-downloads`.
- **Proofs and records:**
  - Licences and sanitised proofs in `dist/phase4/`.
  - The audio template.
  - `internal-rom/import.tgknjpow/before.tar` and the C112/C113 claims.
- **Directories that scripts still reference:** `muos-*`,
  `buildroot-config`, `host-skeleton`, the Rockchip Mali and libnl
  directories. Also `glibc-*/COPYING.LIB`.

## Cleanup procedure

1. **Trace dependencies:** `port/scripts/phase4-storage-dependencies.py`
   traces the current offline preparation. It blocks writes, network access
   and subprocesses; only `git check-ignore` is allowed.
2. **Make a plan (dry run):** `port/scripts/retain-phase4-builds.py`
   cross-checks the trace against the inventory. It writes a private plan to
   `build/cleanup/retention-*.json`. Review that plan.
3. **Apply the plan.** Apply refuses to run if:
   - anything changed since the plan was made,
   - a tree is mounted,
   - files are open,
   - there are directory aliases or special file types.

   Symlinks are deleted without being followed, and hardlinks to protected
   files are kept.
4. **Rules:**
   - Never run cleanup during a build.
   - Never reuse a consumed plan, and never apply an empty dry-run plan.
   - Consumed plans are gzipped and re-read in full.
5. **Measure** the gain with `df`, not `du`, because Btrfs CoW shares
   blocks.
6. **Rebuild** removed historical builds from recipes plus
   `rootfs-downloads`, into a new output tree.

To sparsify images, use `port/scripts/sparsify-phase4-images.py`. It runs
`fallocate --dig-holes` and checks SHA256 before and after. Never use it on
private, root-migration or offline-backup areas.

## History

| Date | What ran | Result |
|---|---|---|
| 04/11 | 145 synthetic test trees, 191 package build intermediates, sparsify of 53 images (~3.25 GiB) | ~15.6 GiB freed; free space 9.4 → 25 GiB. Audit in `build/cleanup/`. |
| 07/11 | Plans `T155500Z`, `T160455Z` | 404,812 files / ~11.8 GiB freed; `build/phase4` 41 → 18 GiB; free space 30 → 42 GiB |
| 07/11 | Plan `T162254Z` (C106) | 1,381 files / 0.5 GiB more; total 406,193 files / ~12.3 GiB; 1,484 protected files verified |
| C107–C122 | Dry runs | Zero candidates. Last recorded dry run: `20261110T001746Z`. `build/phase4` is about 17 GiB. |

The summary is in `build/cleanup/retention-summary.json`.

## Steam Deck (retired)

The Deck was used as the offline card reader for C20 and C82–C97. On 05/11
(C101) the user removed the `muos-r35s-c*` directories, the udev guard rule
and the task SSH key.

That cleanup is recorded on the user's word only. The C101 helper failed and
the result was never audited over SSH.

If the Deck is needed again:
- Reinstall the guard rule and key.
- The automount `chmod 777` issue still applies; see hardware-findings.

## Lessons from the Phase 3 bench recovery

The live card's state is data, not a disposable cache.

- After the 23/10 MMC timeout, recovery took:
  - an fsck,
  - the fstab fix (`compress=zlib:1` → `compress=zlib`),
  - a Btrfs scrub,
  - a `fsck.fat -a` repair of the ROMs FAT.
- No full card image was needed.
- `build/recovery/boot-panel0-reference.tar.gz` holds only `boot.ini` and two
  DTBs. It is not a recovery image.
