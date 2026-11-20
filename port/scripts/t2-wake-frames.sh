#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M8, M8 T3 5: micro stutters after a wake in a game): where do the slow
# frames after a wake land? Launches the NES test game (t2-game.lib.sh, the
# pickles snapshotted and restored) with muxretro's frame capture, then a
# runner on the device (SSH is down while in game: Wi-Fi is deferred until
# the game ends) sleeps through the real Power path (muos-press power,
# RTC wake after WAKE s), keeps every new performance.csv dump for SECS s
# after the resume (stamped with /proc/uptime), quits the game (Fn+Start)
# and Wi-Fi comes back. The host then prints every slow frame (>18.5 ms,
# muxretro patch 0001: frames over 20 ms) by its time since "resumed" in suspend.log.
#   t2-wake-frames.sh [CYCLES] [WAKE] [SECS]   (default 1 10 30)
set -euo pipefail
dev=$(dirname "$0")/device.sh
repo=$(cd "$(dirname "$0")/../.." && pwd)
cycles=${1:-1} wake=${2:-10} secs=${3:-30}
logs=$repo/build/logs/m8/wake-frames; mkdir -p "$logs"
# shellcheck source=port/scripts/t2-game.lib.sh
. "$(dirname "$0")/t2-game.lib.sh"
game_start "${T2_GAME_ROM:-$(game_rom)}" "${T2_GAME_DIR:-NES}"
sleep 6
r 'rm -rf /run/t2wake; mkdir -p /run/t2wake; cat > /run/t2wake/run.sh' <<EOF
#!/bin/sh
csv=/run/muos/storage/pickles/performance.csv
log=/opt/muos/log/suspend.log
exec > /run/t2wake/runner.log 2>&1
echo $wake > /run/muos/suspend-test-wake
i=0
while [ \$i -lt $cycles ]; do
    i=\$((i+1))
    n0=\$(cat \$log 2>/dev/null | grep -c '^[0-9.]* resumed')
    /usr/libexec/muos-press power
    t=0; while [ "\$(cat \$log 2>/dev/null | grep -c '^[0-9.]* resumed')" -le "\$n0" ] && [ \$t -lt 120 ]; do sleep 0.5; t=\$((t+1)); done
    res=\$(grep '^[0-9.]* resumed' \$log | tail -n1 | cut -d' ' -f1)
    echo "cycle \$i resumed \$res"
    last=\$(stat -c %Y \$csv 2>/dev/null || echo 0); k=0
    end=\$(( \$(cut -d. -f1 /proc/uptime) + $secs ))
    while [ \$(cut -d. -f1 /proc/uptime) -lt \$end ]; do
        m=\$(stat -c %Y \$csv 2>/dev/null || echo 0)
        if [ "\$m" != "\$last" ]; then
            k=\$((k+1)); last=\$m; up=\$(cut -d' ' -f1 /proc/uptime)
            { echo "dump uptime=\$up resumed=\$res"; cat \$csv; } > /run/t2wake/c\$i-\$k.csv
        fi
        sleep 0.3
    done
    sleep 7  # past the recent_wake guard
done
rm -f /run/muos/suspend-test-wake /run/muos/perf-capture
/usr/libexec/muos-press fn+start
echo done
EOF
r 'chmod 755 /run/t2wake/run.sh; nohup /run/t2wake/run.sh >/dev/null 2>&1 &'
echo "runner started: $cycles cycle(s), wake $wake s, $secs s each"
sleep $(( cycles * (wake + secs + 25) ))
"$dev" wait 240 >/dev/null || fail "no SSH after the run"
for _ in $(seq 1 30); do r 'grep -q ^done /run/t2wake/runner.log' && break; sleep 3; done
rm -rf "${logs:?}"/*; "$dev" pull /run/t2wake "$logs" >/dev/null
wait_module muxplore 15 || :
for _ in 1 2 3; do [ "$(module)" = muxlaunch ] && break; r '/usr/libexec/muos-press b'; sleep 2; done
game_snapshot restore
r 'tail -n 30 /opt/muos/log/suspend.log' > "$logs/suspend.log"
# Each slow frame: its uptime = dump uptime - (now - ticks)/1000; the same
# frame shows in several dumps, so keep one per tick value per cycle.
python3 -I - "$logs"/t2wake/c*.csv <<'PY'
import re, sys, collections
seen = collections.defaultdict(dict)
res = {}
for p in sys.argv[1:]:
    cyc = int(re.search(r'/c(\d+)-', p).group(1))
    up = now = None; sect = False
    for line in open(p):
        line = line.rstrip('\n')
        m = re.match(r'dump uptime=([\d.]+) resumed=([\d.]+)', line)
        if m: up = float(m.group(1)); res[cyc] = float(m.group(2)); continue
        m = re.match(r'slow_frames now=(\d+)', line)
        if m: now = int(m.group(1)); sect = True; continue
        if sect:
            if not line: sect = False; continue
            f = line.split()
            if not f[0].isdigit(): continue
            ticks = int(f[0]); stages = dict(x.split('=') for x in f[1:] if '=' in x)
            seen[cyc][ticks] = (up - (now - ticks) / 1000.0 - res[cyc], stages)
for cyc in sorted(seen):
    rows = sorted(seen[cyc].values(), key=lambda r: r[0])
    rows = [r for r in rows if r[0] > -1]
    print(f"cycle {cyc}: {len(rows)} slow frames after the resume")
    for t, st in rows:
        fr = float(st.get('frame', 0))
        top = sorted(((float(v), k) for k, v in st.items() if k != 'frame'), reverse=True)[:3]
        print(f"  +{t:6.2f} s frame {fr:6.1f} ms  " + " ".join(f"{k}={v:.1f}" for v, k in top))
PY
