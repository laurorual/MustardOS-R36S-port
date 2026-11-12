#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Image post-build: set the per-system governor of the pinned muOS coredb
# (opt/muos/share/info/manifest/core.json) from the port's
# core-assign.txt (5th column), so that muOS's own assignment (muxassign,
# Content Options -> Governor default) matches the folders S91 seeds.
#   coredb-governors.py CORE_ASSIGN_TXT CORE_JSON
import json
import sys


def main(table, path):
    want = {}
    for line in open(table, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip("\n").split("|")
        if len(f) >= 5 and f[4]:
            want[f[2]] = f[4]
    with open(path, encoding="utf-8") as fh:
        db = json.load(fh)
    changed = 0
    for system, gov in sorted(want.items()):
        if system not in db:
            sys.exit(f"coredb-governors: no system {system!r} in {path}")
        if db[system].get("governor") != gov:
            db[system]["governor"] = gov
            changed += 1
            print(f"coredb-governors: {system} -> {gov}")
    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(db, fh, indent=4, ensure_ascii=False)
            fh.write("\n")
    print(f"coredb-governors: {changed} system(s) changed")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: coredb-governors.py CORE_ASSIGN_TXT CORE_JSON")
    main(sys.argv[1], sys.argv[2])
