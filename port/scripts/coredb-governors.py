#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Image post-build: set the per-system governor of the pinned muOS coredb
# (opt/muos/share/info/manifest/core.json) from the port's
# core-assign.txt (5th column), so that muOS's own assignment (muxassign,
# Content Options -> Governor default) matches the folders S91 seeds.
# M6: also the system's default core (the launcher column without "mu-"):
# muOS auto-assigns an unassigned folder (e.g. ROMS/megadrive on a card in
# slot 2) the default core of the system its name maps to (assign.json),
# and upstream's defaults (Genesis Plus GX, mGBA, snes9x...) are not shipped.
# Rows whose core file is not in CORE_DIR (when given) are skipped.
#   coredb-governors.py CORE_ASSIGN_TXT CORE_JSON [CORE_DIR]
import json
import os
import sys


def main(table, path, core_dir=None):
    want, default = {}, {}
    for line in open(table, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip("\n").split("|")
        if core_dir and not os.path.isfile(os.path.join(core_dir, f[1])):
            print(f"coredb-governors: {f[0]}: {f[1]} not in the image, skipped")
            continue
        if len(f) >= 5 and f[4]:
            want[f[2]] = f[4]
        if len(f) >= 4 and f[3].startswith("mu-"):
            key = f[3][3:]
            if default.setdefault(f[2], key) != key:
                sys.exit(f"coredb-governors: {f[2]!r}: two default cores ({default[f[2]]!r}, {key!r})")
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
    for system, key in sorted(default.items()):
        if key not in db.get(system, {}).get("libretro", {}):
            sys.exit(f"coredb-governors: no core {key!r} for {system!r} in {path}")
        if db[system].get("default") != key:
            db[system]["default"] = key
            changed += 1
            print(f"coredb-governors: {system} default -> {key}")
    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(db, fh, indent=4, ensure_ascii=False)
            fh.write("\n")
    print(f"coredb-governors: {changed} system(s) changed")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit("usage: coredb-governors.py CORE_ASSIGN_TXT CORE_JSON [CORE_DIR]")
    main(*sys.argv[1:])
