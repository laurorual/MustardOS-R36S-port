#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2: find what stalls in-game frames (M3c T3: PSX first-run slowdowns,
# slowdowns after waking from sleep, volume/brightness judder). Starts a
# game (t2-game.lib.sh content handoff, muxretro frame-time capture), runs
# a device-side sampler (10 Hz: CPU/DDR/GPU clocks, /proc/stat, mmcblk0
# reads; 1 Hz: per-task CPU incl. muxretro's threads, /proc/interrupts)
# and collects every performance.csv dump with its uptime, then
# stall-report.py rebuilds the frame timeline and ties each frame > 20 ms
# to what ran at that moment.
#   t2-stall.sh [--dir DIR] [--rom ROM] [--gov GOV] [--cold] [--wake] [--vol | --act CMD] [--prio CMD] [--secs N] LABEL
# --gov: CPU governor for the launch instead of the folder's core.gov.
# --prio CMD: run CMD on the device once muxretro runs ($retro is its pid),
#         e.g. 'chrt -r -p 5 $retro'.
# --cold: drop the page cache before the launch (first run from the card).
# --wake: after 20 s, one sleep/resume through the Power key (RTC wake 10 s),
#         then N more seconds. --act CMD: after 15 s, repeat the device
#         command CMD for N s (PipeWire env set). --vol: --act with Vol+/Vol-
#         key presses (muos-press, i.e. muhotkey -> audio.sh + overlay).
# Default: NES (game_rom), 45 s. Output: build/logs/stall-LABEL/ (raw) and
# the report on stdout. FAIL when the window after the action (or the
# whole run) has more than --max-slow frames > 20 ms (default: not checked).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
dev=$here/device.sh
act='' prio='' dir=NES rom='' cold=0 wake=0 secs=45 maxslow=''
while [ $# -gt 1 ]; do
    case $1 in
        --dir) dir=$2; shift 2 ;; --rom) rom=$2; shift 2 ;;
        --cold) cold=1; shift ;; --wake) wake=1; shift ;;
        --vol) act='/usr/libexec/muos-press volup voldown'; shift ;;
        --act) act=$2; shift 2 ;;
        --secs) secs=$2; shift 2 ;; --max-slow) maxslow=$2; shift 2 ;;
        --gov) game_gov=$2; shift 2 ;;
        --prio) prio=$2; shift 2 ;;
        *) break ;;
    esac
done
label=${1:?LABEL}
out=$(cd "$here/../.." && pwd)/build/logs/stall-$label
rm -rf "$out"; mkdir -p "$out"
# shellcheck source=port/scripts/t2-game.lib.sh
. "$here/t2-game.lib.sh"
[ -n "$rom" ] || rom=$(game_rom)

# Sampler: no forks in the 10 Hz path except sleep; the csv is moved away
# as soon as muxretro has written it, named by the uptime it appeared at.
# muxretro also writes a csv when it exits: drop the last run's.
r 'rm -rf /run/t2-stall /run/muos/storage/pickles/performance.csv; mkdir -p /run/t2-stall; cat > /run/t2-stall/sampler <<"EOF"
#!/bin/sh
d=/run/t2-stall csv=/run/muos/storage/pickles/performance.csv
cpu=/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
dmc=/sys/class/devfreq/dmc/cur_freq gpu=/sys/class/devfreq/ff400000.gpu/cur_freq
n=0; exec 3> $d/samples
while [ ! -e $d/stop ]; do
    read up _ < /proc/uptime; read c < $cpu; read m < $dmc; read g < $gpu
    read _ u ni s i w q sq _ < /proc/stat; read rd _ rs _ < /sys/block/mmcblk0/stat
    echo "$up $c $m $g $((u+ni+s+q+sq)) $((i+w)) $w $rs" >&3
    if [ -e $csv ]; then sleep 0.3; mv $csv $d/perf-$up.csv; fi
    n=$((n+1))
    if [ $((n % 10)) = 0 ]; then
        { echo "T $up"; awk "{print \$1, \$2, \$14+\$15}" /proc/[0-9]*/stat /proc/$(cat $d/retro 2>/dev/null || echo self)/task/*/stat 2>/dev/null; } > $d/tasks.$n
        { echo "T $up"; cat /proc/interrupts; } > $d/irq.$n
    fi
    sleep 0.1
done
EOF
chmod +x /run/t2-stall/sampler'
r 'nohup /run/t2-stall/sampler >/dev/null 2>&1 &'
event() { r 'echo "$(cut -d" " -f1 /proc/uptime) '"$1"'" >> /run/t2-stall/events'; }

[ "$cold" = 0 ] || { r 'sync; echo 3 > /proc/sys/vm/drop_caches'; event drop-caches; }
event launch
game_start "$rom" "$dir"
r "$(pids_of muxretro) | head -n1 > /run/t2-stall/retro"
# --prio: a device command run once muxretro is up, with $retro = its pid
[ -z "$prio" ] || { r 'retro=$(cat /run/t2-stall/retro); '"$prio"; event "prio:${prio// /_}"; }
event running
if [ "$wake" = 1 ]; then
    sleep 20
    r 'echo 10 > /run/muos/suspend-test-wake'; event power-press
    r 'nohup /usr/libexec/muos-press power >/dev/null 2>&1 &' || :
    sleep 25; "$dev" wait 180 >/dev/null || fail "no SSH after resume"
    r 'rm -f /run/muos/suspend-test-wake'
    sleep "$secs"
elif [ -n "$act" ]; then
    sleep 15; event act-start
    r 'export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run
       end=$(( $(date +%s) + '"$secs"' )); while [ "$(date +%s)" -lt $end ]; do '"$act"'; done'
    event act-end; sleep 16
else
    sleep "$secs"
fi
sleep 16   # one more csv dump
event stop
r 'touch /run/t2-stall/stop; sleep 0.5; { tail -8 /opt/muos/log/suspend.log 2>/dev/null || :; } > /run/t2-stall/suspend.log'
game_stop
r 'cd /run/t2-stall && tar cf - samples events retro suspend.log perf-*.csv tasks.* irq.*' | tar xf - -C "$out"
r 'rm -rf /run/t2-stall'
python3 -I "$here/stall-report.py" "$out" ${maxslow:+--max-slow "$maxslow"} | tee "$out/report.txt"
