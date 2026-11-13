#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Attribute muxretro's slow frames to stages (M3d step 3).

Reads muxretro performance.csv dumps (port patch 0001: the "slow_frames"
section) and, per file, takes the slow frames of the t2-level-fps window
(14.5 s to 1 s before the dump). Each stage's exclusive time is its own time
minus its children's (the csv's parent column); "frame" exclusive is the
untracked rest of the frame ("untracked"). Prints per file: the slow-frame count, how many
each stage dominated, and the mean exclusive ms of the top stages.
    slow-frames.py [--window LO HI] FILE...
"""
import collections
import os
import sys


def parse(path):
    parents, rows, now, section = {}, [], None, None
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                section = None
                continue
            if line.startswith("stage,parent,"):
                section = "stages"
                continue
            if line.startswith("slow_frames"):
                section = "slow"
                now = int(line.split("now=")[1])
                continue
            if section == "stages":
                c = line.split(",")
                # Top-level stages are the frame's parts; "value" rows
                # (queue depths, delays) are not time.
                parents[c[0]] = None if c[2] == "value" else (c[1] if c[1] != "none" or c[0] == "frame" else "frame")
            elif section == "slow":
                c = line.split()
                rows.append((int(c[0]), {k: float(v) for k, v in (x.split("=") for x in c[1:])}))
    return parents, rows, now


def exclusive(stages, parents):
    out = {k: v for k, v in stages.items() if parents.get(k, "frame") is not None}
    for name, ms in list(out.items()):
        p = parents.get(name, "frame")
        if p in out and p != name:
            out[p] -= ms
    if "frame" in out:
        out["untracked"] = out.pop("frame")
    return out


def main(argv):
    lo, hi = 14500, 1000
    if argv[:1] == ["--window"]:
        lo, hi, argv = int(argv[1]), int(argv[2]), argv[3:]
    for path in argv:
        parents, rows, now = parse(path)
        name = os.path.basename(path)
        if now is None:
            print(f"{name}: no slow_frames section (unpatched muxretro?)")
            continue
        sel = [s for t, s in rows if now - lo <= t <= now - hi]
        dom, tot = collections.Counter(), collections.Counter()
        for s in sel:
            ex = exclusive(s, parents)
            top = max(ex, key=ex.get)
            dom[top] += 1
            for k, v in ex.items():
                tot[k] += v
        frames = " ".join(f"{s.get('frame', 0):.0f}" for s in sel)
        print(f"{name}: {len(sel)} slow frames [{frames}]")
        if sel:
            print("  dominant: " + ", ".join(f"{k} {n}" for k, n in dom.most_common(6)))
            print("  mean ms:  " + ", ".join(f"{k} {v / len(sel):.1f}" for k, v in tot.most_common(8)))


if __name__ == "__main__":
    main(sys.argv[1:])
