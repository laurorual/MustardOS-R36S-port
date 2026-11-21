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
# Rows whose core file is not in CORE_DIR (when given) are skipped; an
# ext-NAME-* row (external runtime, launcher column "ext-KEY") needs
# CORE_DIR/../emulator/NAME. M7c: the coredb's external N64 entries the
# image does not build are dropped (Glide64mk2; "- Full" = the 4:3 entry on
# this 640x480 panel), so the assignment list only offers what runs.
# M8: the same for the heavy systems (no external emulator shipped), and a
# default core marked "extra" (hidden unless Advanced -> Extra Cores) is
# unmarked: it is the only core the image has for its system.
# M8d T3 6 (Saturn's core list offered only the missing Yabadabadoo, while
# the installed YabaSanshiro libretro was "extra"): with CORE_DIR, every
# libretro entry is marked by what the image has: installed = shown
# (extra 0), not installed = extra 1 (hidden unless Advanced -> Extra
# Cores), so the lists offer what runs.
#   coredb-governors.py CORE_ASSIGN_TXT CORE_JSON [CORE_DIR]
import json
import os
import sys

# external cores the image ships, per system (others in that system dropped)
EXTERNAL = {"Nintendo N64": {"ext-mupen64plus-rice", "ext-mupen64plus-gliden64"},
            "Sega Dreamcast": {"ext-flycast"}, "Sony PlayStation Portable": {"ext-ppsspp", "ext-ppsspp-2021"},
            "Nintendo DS": {"ext-drastic"}, "Sega Saturn": {"ext-yabasanshiro"}}
# M8 (decision 23): external emulators upstream's coredb has no entry for
ADD = {"Nintendo DS": {"drastic": {"name": "DraStic (Advanced)", "core": "ext-drastic",
                                   "launcher": "drastic.sh", "control": "modern"}},
       "Sony PlayStation Portable": {"ppsspp-2021": {"name": "PPSSPP 2021 (v1.12)", "core": "ext-ppsspp-2021",
                                                     "launcher": "ppsspp.sh", "control": "modern"}},
       # M8 thermal block T9: dArkOSen's standalone Flycast (build-flycast-sa.sh)
       "Sega Dreamcast": {"flycast-sa": {"name": "Flycast - Standalone (dArkOSen)", "core": "ext-flycast",
                                         "launcher": "flycast.sh", "control": "modern"}},
       "Sega Saturn": {"yabasanshiro-sa": {"name": "YabaSanshiro - Standalone (dArkOSen)", "core": "ext-yabasanshiro",
                                        "launcher": "yabasanshiro.sh", "control": "modern"}}}
# M8e T3 6: upstream's own entry for the same emulator (two "DraStic" rows
# that both start the advanced DraStic)
DROP = {"Nintendo DS": {"drastic - standalone"}, "Sega Dreamcast": {"flycast"}}
# M8 T3 8: libretro cores upstream's coredb has no entry for
ADD_LIBRETRO = {"Sega Dreamcast": {"flycast 2022": {"name": "Flycast 2022 (dArkOSen)",
                                                    "core": "flycast2022_libretro.so"}}}


def main(table, path, core_dir=None):
    want, default = {}, {}
    for line in open(table, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip("\n").split("|")
        if f[1].startswith("ext-"):
            em = os.path.join(core_dir or "", "..", "emulator")
            have = any(os.path.isdir(os.path.join(em, d)) for d in (f[1][4:], f[1][4:].split("-")[0]))
        else:
            have = os.path.isfile(os.path.join(core_dir or "", f[1]))
        if core_dir and not have:
            print(f"coredb-governors: {f[0]}: {f[1]} not in the image, skipped")
            continue
        if len(f) >= 5 and f[4]:
            want[f[2]] = f[4]
        if len(f) >= 4 and f[3][:3] in ("mu-", "ext"):
            key = (f[3][3:] if f[3].startswith("mu-") else f[3][4:], "libretro" if f[3].startswith("mu-") else "external")
            if default.setdefault(f[2], key) != key:
                sys.exit(f"coredb-governors: {f[2]!r}: two default cores ({default[f[2]]!r}, {key!r})")
    with open(path, encoding="utf-8") as fh:
        db = json.load(fh)
    changed = 0
    for system, cores in sorted(ADD.items()):
        ext = db.get(system, {}).setdefault("external", {})
        for key, e in cores.items():
            if ext.get(key) != e:
                ext[key] = e
                changed += 1
                print(f"coredb-governors: {system}: external {key!r} added")
    for system, cores in sorted(ADD_LIBRETRO.items()):
        lr = db.get(system, {}).setdefault("libretro", {})
        for key, e in cores.items():
            if lr.get(key) != e:
                lr[key] = e
                changed += 1
                print(f"coredb-governors: {system}: libretro {key!r} added")
    for system, gov in sorted(want.items()):
        if system not in db:
            sys.exit(f"coredb-governors: no system {system!r} in {path}")
        if db[system].get("governor") != gov:
            db[system]["governor"] = gov
            changed += 1
            print(f"coredb-governors: {system} -> {gov}")
    for system, keys in sorted(DROP.items()):
        ext = db.get(system, {}).get("external", {})
        for key in sorted(keys & ext.keys()):
            del ext[key]
            changed += 1
            print(f"coredb-governors: {system}: external {key!r} dropped (duplicate)")
    for system, keep in sorted(EXTERNAL.items()):
        ext = db.get(system, {}).get("external", {})
        for key in [k for k, e in ext.items() if e.get("core") not in keep]:
            del ext[key]
            changed += 1
            print(f"coredb-governors: {system}: external {key!r} dropped")
        if {e.get("core") for e in ext.values()} != keep:
            sys.exit(f"coredb-governors: {system}: external cores {sorted(keep)} not all in {path}")
    if core_dir:
        for system, entry in sorted(db.items()):
            if not isinstance(entry, dict):
                continue
            for key, e in sorted(entry.get("libretro", {}).items()):
                if not isinstance(e, dict) or not e.get("core"):
                    continue
                want_extra = 0 if os.path.isfile(os.path.join(core_dir, e["core"])) else 1
                if int(e.get("extra", 0)) != want_extra:
                    e["extra"] = want_extra
                    changed += 1
                    print(f"coredb-governors: {system}: libretro {key!r} extra -> {want_extra}")
    for system, (key, section) in sorted(default.items()):
        if key not in db.get(system, {}).get(section, {}):
            sys.exit(f"coredb-governors: no {section} core {key!r} for {system!r} in {path}")
        if db[system].get("default") != key:
            db[system]["default"] = key
            changed += 1
            print(f"coredb-governors: {system} default -> {key}")
        if db[system][section][key].pop("extra", 0):
            changed += 1
            print(f"coredb-governors: {system}: {key!r} no longer extra")
    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(db, fh, indent=4, ensure_ascii=False)
            fh.write("\n")
    print(f"coredb-governors: {changed} system(s) changed")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit("usage: coredb-governors.py CORE_ASSIGN_TXT CORE_JSON [CORE_DIR]")
    main(*sys.argv[1:])
