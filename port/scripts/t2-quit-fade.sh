#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # device-side commands in single quotes
# v1.1.1 T3: Fn+Start out of a standalone emulator must fade the picture
# out (muos-standalone-quit eases the backlight to 0 in ~0.35 s) before the
# emulator takes its picture off the screen. Runs the game through the
# menu's content handoff (t2-standalone.sh, which presses Fn+Start at the
# end) and samples, every ~40 ms, the backlight and the VOP's win1 scanout
# address (debugfs; 0 = the emulator's picture is gone): PASS when the
# backlight reaches 0 while the game's buffer is still scanned out, and
# comes back after the emulator is gone. Timeline in build/logs/m12/.
#   t2-quit-fade.sh [NAME CORE DIR FILE PROCESS]
#   default: n64 ext-mupen64plus-rice N64 "Mario Kart 64 (USA).z64" mupen64plus
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
dev=port/scripts/device.sh
n=${1:-n64} core=${2:-ext-mupen64plus-rice} dir=${3:-N64} file=${4:-Mario Kart 64 (USA).z64} p=${5:-mupen64plus}
out=build/logs/m12/quit-fade-$n.txt; mkdir -p "${out%/*}"
r() { "$dev" run "$@" < /dev/null; }
r 'grep -q " /sys/kernel/debug " /proc/mounts || mount -t debugfs none /sys/kernel/debug' || exit 1
port/scripts/t2-standalone.sh "fade-$n" "$core" "$dir" "$file" "$p" 8 > "${out%.txt}.log" 2>&1 < /dev/null &
t=$!
for _ in $(seq 90); do r "pidof $p" > /dev/null 2>&1 && break; sleep 1; done
r 'i=0; gone=
   while [ $i -lt 3000 ]; do
       b=$(cat /sys/class/backlight/backlight/brightness)
       a=$(grep -m1 -A6 "win1-0" /sys/kernel/debug/dri/0/summary | grep -o "addr: 0x[0-9a-f]*" | head -1)
       m=$(pidof '"$p"' > /dev/null && echo M || echo -)
       echo "$(cut -d" " -f1 /proc/uptime) $b $m ${a#addr: }"
       i=$((i+1)); [ "$m" = - ] && [ -z "$gone" ] && gone=$i
       [ -n "$gone" ] && [ $((i-gone)) -gt 60 ] && break
   done' > "$out"
wait "$t" || { echo "FAIL t2-standalone: $(tail -n 1 "${out%.txt}.log")"; exit 1; }
awk -v name="$n" '
    NR == 1 { level = $2 }
    !dark && $2 == 0 && $3 == "M" { dark = 1; shown = ($4 !~ /^0x0+$/) }
    !blank && $3 == "M" && $4 ~ /^0x0+$/ { blank = 1; if (!dark) early = 1 }
    $3 == "-" { gone = 1 }
    gone && $2 == level { back = 1 }
    END {
        if (early || !dark) { print "FAIL " name ": the picture left the screen before the fade ended"; exit 1 }
        if (!back) { print "FAIL " name ": the backlight did not come back"; exit 1 }
        print "PASS " name ": faded out over the game picture, back after the quit"
    }' "$out"
