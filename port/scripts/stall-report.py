#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Report for t2-stall.sh: rebuild the in-game frame timeline and tie each
slow frame (> 20 ms) to the sampler state around it.

Each perf-<uptime>.csv holds the last <=1024 frame intervals, the newest
ending at <uptime>; frames are placed backwards from there and each dump
contributes only the frames after the previous dump. Frames > 250 ms are
not in the history (muxretro counts them as frames_excluded_long_gap).
  stall-report.py DIR [--max-slow N]
"""
import glob
import os
import sys

SLOW = 20.0  # later than a vsync (jitter; may still be shown on time)
MISS = 25.0  # > 1.5 refresh periods: a vsync without a new frame (muxretro's missed_refreshes)


def load_dumps(d):
    dumps = []
    for p in glob.glob(os.path.join(d, "perf-*.csv")):
        t = float(os.path.basename(p)[5:-4])
        frames, metrics, on = [], {}, False
        for line in open(p):
            line = line.strip()
            if line == "frame_interval_ms":
                on = True
                continue
            if on and not line:
                on = False
            if on:
                frames.append(float(line))
            elif "," in line:
                k, _, v = line.partition(",")
                metrics[k] = v
        dumps.append((t, frames, metrics))
    return sorted(dumps)


def timeline(dumps):
    out, prev = [], None
    for t, frames, _ in dumps:
        end, placed = t, []
        for f in reversed(frames):
            if prev is not None and end <= prev:
                break
            placed.append((end, f))
            end -= f / 1000.0
        out.extend(reversed(placed))
        prev = t
    return out


def load_samples(d):
    s = []
    for line in open(os.path.join(d, "samples")):
        v = line.split()
        if len(v) == 8:
            s.append([float(v[0])] + [int(x) for x in v[1:]])
    return s


def load_tasks(d):
    snaps = []
    for p in glob.glob(os.path.join(d, "tasks.*")):
        lines = open(p, errors="replace").read().split("\n")
        if not lines[0].startswith("T "):
            continue
        t = float(lines[0][2:])
        cpu = {}
        for line in lines[1:]:
            v = line.split()
            if len(v) >= 3 and v[-1].isdigit():
                cpu[(v[0], " ".join(v[1:-1]))] = int(v[-1])
        snaps.append((t, cpu))
    return sorted(snaps)


def load_irqs(d):
    snaps = []
    for p in glob.glob(os.path.join(d, "irq.*")):
        lines = open(p, errors="replace").read().split("\n")
        t = float(lines[0][2:])
        irq = {}
        for line in lines[2:]:
            v = line.split()
            if len(v) > 5 and v[0].endswith(":"):
                try:
                    irq[" ".join([v[0]] + v[7:])] = sum(int(x) for x in v[1:5])
                except ValueError:
                    pass
        snaps.append((t, irq))
    return sorted(snaps)


def busiest(snaps, t, n=4):
    """Tasks with the most CPU ticks (1/100 s) in the 1 s window around t."""
    for (t0, a), (t1, b) in zip(snaps, snaps[1:]):
        if t0 <= t <= t1:
            d = {k: v - a.get(k, 0) for k, v in b.items()}
            top = sorted(d.items(), key=lambda kv: -kv[1])[:n]
            return " ".join(f"{k[1].strip('()')}:{v}" for k, v in top if v > 0)
    return "-"


def irq_rate(snaps, t, n=3):
    for (t0, a), (t1, b) in zip(snaps, snaps[1:]):
        if t0 <= t <= t1:
            d = {k: (v - a.get(k, 0)) / (t1 - t0) for k, v in b.items()}
            top = sorted(d.items(), key=lambda kv: -kv[1])[:n]
            return " ".join(f"{k.split()[-1]}:{v:.0f}/s" for k, v in top)
    return "-"


def state_at(samples, t):
    """Sample just before t and the change across [t-0.2, t+0.1]."""
    before = [s for s in samples if s[0] <= t]
    win = [s for s in samples if t - 0.25 <= s[0] <= t + 0.15]
    if not before or len(win) < 2:
        return None
    a, b = win[0], win[-1]
    busy = (b[4] - a[4]) * 400 // max(1, (b[4] - a[4]) + (b[5] - a[5]))
    return {
        "cpu": before[-1][1] // 1000, "dmc": before[-1][2] // 1000000,
        "gpu": before[-1][3] // 1000000,
        "dmc_change": len({s[2] for s in win}) > 1,
        "cpu_change": len({s[1] for s in win}) > 1,
        "gpu_change": len({s[3] for s in win}) > 1,
        "busy": busy, "iowait": b[6] - a[6], "rd_kib": (b[7] - a[7]) // 2,
    }


def main():
    d = sys.argv[1]
    maxslow = int(sys.argv[sys.argv.index("--max-slow") + 1]) if "--max-slow" in sys.argv else None
    dumps = load_dumps(d)
    if not dumps:
        print(f"FAIL stall {d}: no performance.csv dumps")
        return 1
    frames = timeline(dumps)
    samples = load_samples(d)
    tasks = load_tasks(d)
    irqs = load_irqs(d)
    events = [(float(v[0]), v[1]) for v in (l.split() for l in open(os.path.join(d, "events"))) if len(v) > 1]
    for line in open(os.path.join(d, "suspend.log"), errors="replace"):
        v = line.split(None, 1)
        try:
            if v[1].startswith(("suspend to", "woke", "resumed", "muxretro saved")):
                events.append((float(v[0]), v[1].strip().replace(" ", "_")))
        except (ValueError, IndexError):
            pass
    events.sort()
    launch = [t for t, e in events if e == "launch"]
    t0 = launch[0] if launch else frames[0][0]
    events = [(t, e) for t, e in events if t >= t0 - 1]
    m = dumps[-1][2]
    print(f"run {os.path.basename(d)}: {len(frames)} frames, {frames[0][0]-t0:.1f}-{frames[-1][0]-t0:.1f} s after launch;"
          f" refresh {m.get('refresh_hz', '?')} Hz, present {m.get('observed_present_hz', '?')} Hz,"
          f" emulation {m.get('emulation_fps', '?')} fps, >250 ms frames {sum(int(x[2].get('frames_excluded_long_gap', 0)) for x in dumps[-1:])}")
    print("events: " + ", ".join(f"{e}@{t-t0:.1f}" for t, e in events))
    dmc_moves = [(s[0], s[2]) for p, s in zip(samples, samples[1:]) if p[2] != s[2]]
    print(f"DDR (dmc) changes: {len(dmc_moves)}: " + " ".join(f"{t-t0:.1f}s->{f//1000000}" for t, f in dmc_moves[:30]))
    dump_t = [t for t, _, _ in dumps]
    near_dump = lambda t: any(abs(t - d) < 0.4 for d in dump_t)
    # 5 s windows (frames next to a csv dump left out)
    print("window   frames  slow(>20ms)  missed(>25ms)  max_ms  mean_fps")
    w = {}
    for t, f in frames:
        if near_dump(t):
            continue
        w.setdefault(int((t - t0) // 5), []).append(f)
    for k in sorted(w):
        v = w[k]
        print(f"{k*5:4d}-{k*5+5:<4d} {len(v):6d} {sum(1 for f in v if f > SLOW):8d} {sum(1 for f in v if f > MISS):12d} {max(v):12.1f} {len(v)*1000/sum(v):9.2f}")
    slow = [(t, f) for t, f in frames if f > SLOW]
    print(f"slow frames: {len(slow)}")
    # muxretro writes performance.csv (to p3) on its main thread: a frame
    # ending just before a dump is the test's own cost, not the system's.
    art = [x for x in slow if near_dump(x[0])]
    slow = [x for x in slow if not near_dump(x[0])]
    print(f"slow frames from the capture's own csv dumps (excluded): {len(art)}; remaining: {len(slow)}, "
          f"of which missed vsync (>{MISS:.0f} ms): {sum(1 for _, f in slow if f > MISS)}")
    tags = {"dmc": 0, "cpu": 0, "gpu": 0, "io": 0}
    for t, f in slow:
        s = state_at(samples, t)
        if not s:
            continue
        tag = []
        for k in ("dmc", "cpu", "gpu"):
            if s[k + "_change"]:
                tag.append(k + "-switch")
                tags[k] += 1
        if s["rd_kib"]:
            tag.append(f"read {s['rd_kib']} KiB")
            tags["io"] += 1
        print(f"  {t-t0:7.2f}s {f:6.1f} ms cpu {s['cpu']} dmc {s['dmc']} gpu {s['gpu']} busy {s['busy']}% "
              f"{' '.join(tag)} | {busiest(tasks, t)} | irq {irq_rate(irqs, t)}")
    print("slow frames near: " + " ".join(f"{k}={v}" for k, v in tags.items()))
    if maxslow is not None:
        r = "PASS" if len(slow) <= maxslow else "FAIL"
        print(f"{r} stall {os.path.basename(d)}: {len(slow)} slow frames (max {maxslow})")
        return 0 if r == "PASS" else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
