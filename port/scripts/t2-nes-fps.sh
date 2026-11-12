#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2: launch a ROMS/NES game through the frontend content handoff (see
# below), arm muxretro's own frame-time capture (MUXRETRO_PERF_CAPTURE via
# /run/muos/perf-capture; performance.csv every 15 s, last 1024 frames) and,
# after a 10 s warm-up, read one dump per 15 s window for SECONDS together
# with CPU frequency, governor and SoC temperature. fps = 1000 / mean frame
# interval. (muxretro's "Content rate" log line is audio-derived, not fps.)
#   t2-nes-fps.sh [--reboot] [--dir DIR] [--rom FILE] [SECONDS] [LABEL]
# --dir: another ROMS folder with a core assignment (M3c: GB GBA SNES MD
# PSX); --rom is then required.
# Default ROM: see game_rom in t2-game.lib.sh.
# Prints one summary line; details go to build/logs/nes-fps.log.
set -euo pipefail
dev=$(dirname "$0")/device.sh
logs=$(cd "$(dirname "$0")/../.." && pwd)/build/logs; mkdir -p "$logs"
reboot=0; [ "${1:-}" = --reboot ] && { reboot=1; shift; }
dir=NES; [ "${1:-}" = --dir ] && { dir=$2; shift 2; }
rom=; [ "${1:-}" = --rom ] && { rom=$2; shift 2; }
secs=${1:-60} label=${2:-run}
. "$(dirname "$0")/t2-game.lib.sh"

[ "$reboot" = 0 ] || "$dev" reboot >/dev/null
[ -n "$rom" ] || { [ "$dir" = NES ] || fail "--rom required with --dir"; rom=$(game_rom); }
game_start "$rom" "$dir"
sleep 10
csv=/run/muos/storage/pickles/performance.csv
: > "$logs/nes-fps.samples"; : > "$logs/nes-fps.windows"
for _ in $(seq 1 $(( (secs + 14) / 15 ))); do
    sleep 15
    r "printf 'S %s %s %s %s\n' \"\$(cut -d' ' -f1 /proc/uptime)\" \
         \"\$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)\" \
         \"\$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)\" \
         \"\$(cat /sys/class/thermal/thermal_zone0/temp)\"" >> "$logs/nes-fps.samples"
    # frame interval mean -> fps; also the core and present stage means.
    r "awk -F, '/^frame,/{f=\$4} /^core,/{c=\$4} /^present,/{p=\$4} END{if (f>0) printf \"%.3f %.3f %.3f %.3f\\n\", 1000/f, f, c, p}' $csv" >> "$logs/nes-fps.windows" || :
done
game_stop
summary=$(awk -v label="$label" -v dir="$dir" -v rom="${rom%.*}" -v samples="$logs/nes-fps.samples" '
  NF { n++; s+=$1; fm+=$2; cm+=$3; pm+=$4; if (min=="" || $1<min) min=$1; if ($1>max) max=$1 }
  END {
    while ((getline line < samples) > 0) { split(line, f, " "); m++; mhz+=f[3]/1000; gov=f[4]; if (f[5]>t) t=f[5] }
    if (n==0) { print "FAIL no performance.csv windows"; exit 0 }
    printf "%s %s [%s]: fps avg=%.2f min=%.2f max=%.2f (windows=%d) frame=%.2f ms core=%.2f ms present=%.2f ms cpu=%.0f MHz gov=%s temp_max=%.1f C\n", dir, label, rom, s/n, min, max, n, fm/n, cm/n, pm/n, (m?mhz/m:0), gov, t/1000 }' "$logs/nes-fps.windows")
{ date -u +%FT%TZ; echo "$summary"; cat "$logs/nes-fps.samples" "$logs/nes-fps.windows"; } >> "$logs/nes-fps.log"
echo "$summary"
