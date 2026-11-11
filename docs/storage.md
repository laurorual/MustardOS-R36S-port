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

- At most **5 firmware versions**, inventoried in
  `port/packaging/storage-retention.json` and managed by
  `port/scripts/retention.py`. The tool refuses a 6th version; only files
  listed for a version are ever deleted. Current versions (M2, 11/11):

  | Version | Role |
  |---|---|
  | C100 | Unprovisioned factory ext4, rootfs rebuild reference |
  | M1-baseline | Flashable pre-M1 test128 image (C07 init; boots on test128 only) |
  | M1 | Flashable M1 image (autostart; any card ≥ 2 GiB) |
  | M2 | Flashable M2 image (sleep, battery, headphones; the recovery image) |

  C64, C79, C89 and C93 (audit-only images) were retired in M1.
- At most **5 named Git checkpoints** (tags `checkpoint/*`).
- `keep` in the inventory lists what is never pruned: private material
  (`build/phase4/private`, the C82 offline backup), SDKs, sources and
  downloads, `dist/phase4` proofs, `dist/recovery`, and the latest
  `build/recovery` capture.
- Pruned inside kept areas on 2026-11-11 (M3a): the synthetic self-test
  fixtures in `physical-capture/checks.*` (`fake-card.regular`, `*.ext4`;
  the result JSONs stay) and the extracted Mali SDK `lib/` under
  `graphics-config/output/build/rockchip-mali-721653b5…` (only `include/`
  and `pkgconfig/` are used; the tarball is in `rootfs-downloads`).
  `legal-info/` dirs are fully reflinked to the downloads: deleting them
  frees nothing.

## Cleanup procedure

1. `port/scripts/retention.py check`: limit, presence and sizes.
2. `port/scripts/retention.py retire VERSION`: dry run listing the files
   and bytes; add `--apply` to delete them and drop the entry.
3. `port/scripts/retention.py add VERSION REASON FILE...` after building
   a new image.
4. Measure the gain with `df`, not `du`, because Btrfs CoW shares blocks.

The old `retain-phase4-builds.py` replica pruner and its hash-pinned
dependency trace (`phase4-storage-dependencies.py`) were retired in M1.
Their history is in Git and in the table below.

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
