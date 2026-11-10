#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Firmware-version retention for build/ and dist/ (AGENTS.md: at most 5).

  retention.py check                    limit, existence and sizes
  retention.py add VERSION REASON PATH...   record a new version (refuses a 6th)
  retention.py retire VERSION [--apply] delete exactly that version's files

Paths in port/packaging/storage-retention.json are relative to the repo root.
Only listed files are ever deleted; `keep` documents what is never pruned.
"""
from pathlib import Path
import json, sys

REPO = Path(__file__).resolve().parents[2]
POLICY = REPO / 'port/packaging/storage-retention.json'


def load():
    return json.loads(POLICY.read_text())


def save(policy):
    POLICY.write_text(json.dumps(policy, indent=2) + '\n')


def size(path):
    return path.stat().st_blocks * 512 if path.exists() else 0


def human(n):
    for unit in ['B', 'KiB', 'MiB', 'GiB']:
        if n < 1024 or unit == 'GiB':
            return f'{n:.1f} {unit}' if unit != 'B' else f'{n} B'
        n /= 1024


def check(policy):
    versions = policy['firmware_versions']
    ok = len(versions) <= policy['maximum_firmware_versions']
    print(f"versions {len(versions)}/{policy['maximum_firmware_versions']}")
    for name, row in versions.items():
        files = [REPO / p for p in row['files']]
        missing = [str(p.relative_to(REPO)) for p in files if not p.is_file()]
        ok &= not missing
        print(f"  {name}: {human(sum(map(size, files)))} {row['reason']}" + (f" MISSING {missing}" if missing else ''))
    return ok


def main(argv):
    policy = load()
    if argv[:1] == ['check']:
        return 0 if check(policy) else 1
    if argv[:1] == ['add'] and len(argv) >= 4:
        name, reason, paths = argv[1], argv[2], argv[3:]
        assert name not in policy['firmware_versions'], 'version exists'
        assert len(policy['firmware_versions']) < policy['maximum_firmware_versions'], 'limit of 5 reached: retire one first'
        assert all((REPO / p).is_file() for p in paths), 'missing file'
        policy['firmware_versions'][name] = {'reason': reason, 'files': paths}
        save(policy)
        return 0 if check(policy) else 1
    if argv[:1] == ['retire'] and len(argv) in (2, 3):
        name, apply = argv[1], argv[2:] == ['--apply']
        row = policy['firmware_versions'][name]
        files = [REPO / p for p in row['files']]
        for p in files:
            print(f"  {'delete' if apply else 'would delete'} {p.relative_to(REPO)} ({human(size(p))})")
        print(f"total {human(sum(map(size, files)))}")
        if apply:
            for p in files:
                p.unlink(missing_ok=True)
            del policy['firmware_versions'][name]
            save(policy)
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
