#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2: launch a ROMS/NES game through the frontend content handoff (see
# below), arm muxretro's own frame-time capture (MUXRETRO_PERF_CAPTURE via
# /run/muos/perf-capture; performance.csv every 15 s, last 1024 frames) and,
# after a 10 s warm-up, read one dump per 15 s window for SECONDS together
# with CPU frequency, governor and SoC temperature. fps = 1000 / mean frame
# interval. (muxretro's "Content rate" log line is audio-derived, not fps.)
#   t2-nes-fps.sh [--reboot] [--rom FILE.nes] [SECONDS] [LABEL]
# Default ROM: "Super Mario Bros. 3 (USA) (Rev 1).nes" (MMC3, title/attract
# loop without input) when installed, else the MIT demo r35s-flight.nes.
# Prints one summary line; details go to build/logs/nes-fps.log.
set -euo pipefail
dev=$(dirname "$0")/device.sh
logs=$(cd "$(dirname "$0")/../.." && pwd)/build/logs; mkdir -p "$logs"
reboot=0; [ "${1:-}" = --reboot ] && { reboot=1; shift; }
rom=; [ "${1:-}" = --rom ] && { rom=$2; shift 2; }
secs=${1:-60} label=${2:-run}
r() { "$dev" run "cd /; $*"; }
# Match on /proc/PID/exe: pgrep -f would also match this SSH command line.
pids_of() { echo 'for p in /proc/[0-9]*; do [ "$(readlink $p/exe)" = /opt/muos/frontend/'"$1"' ] && echo ${p#/proc/}; done'; }
module() { r "for q in \$($(pids_of muxretro); $(pids_of muxfrontend)); do cat /proc/\$q/comm; done | head -n1"; }
wait_module() { for _ in $(seq 1 "$2"); do [ "$(module)" = "$1" ] && return 0; sleep 1; done; return 1; }
fail() { echo "FAIL $*"; exit 1; }

[ "$reboot" = 0 ] || "$dev" reboot >/dev/null
if [ -z "$rom" ]; then
    rom="Super Mario Bros. 3 (USA) (Rev 1).nes"
    r "test -f '/userdata/ROMS/NES/$rom'" || rom=r35s-flight.nes
fi
wait_module muxlaunch 40 || { for _ in 1 2 3; do r '/usr/libexec/muos-press b'; sleep 2; done; wait_module muxlaunch 10 || fail "not at launcher"; }
# Explore remembers its last folder and lists wrap, so blind navigation is
# not deterministic. Launch through the frontend's own content handoff
# instead: the 9-line ROM_GO record + governor request muxplore writes,
# then a safe quit of muxfrontend; the frontend loop runs muxretro as for a
# menu launch.
r 'touch /run/muos/perf-capture; rm -f /run/muos/storage/pickles/performance.csv
   printf "%s\n" "'"${rom%.nes}"'" fceumm_libretro.so "Nintendo NES - Famicom" 0 0 mu-fceumm /mnt/mmc/ROMS /NES "'"$rom"'" > /run/muos/content
   gov=$(cat /opt/muos/share/info/content/NES/core.gov 2>/dev/null || cat /opt/muos/device/config/cpu/default)
   printf "%s\n" "$gov" > /run/muos/governor; echo explore > /run/muos/action
   '"$(pids_of muxfrontend)"' | while read -r q; do kill -TERM "$q"; done'
wait_module muxretro 20 || fail "NES did not start (got $(module))"
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
r 'rm -f /run/muos/perf-capture'
r '/usr/libexec/muos-press fn+start'; wait_module muxplore 15 || :
for _ in 1 2 3; do [ "$(module)" = muxlaunch ] && break; r '/usr/libexec/muos-press b'; sleep 2; done
summary=$(awk -v label="$label" -v rom="${rom%.nes}" -v samples="$logs/nes-fps.samples" '
  NF { n++; s+=$1; fm+=$2; cm+=$3; pm+=$4; if (min=="" || $1<min) min=$1; if ($1>max) max=$1 }
  END {
    while ((getline line < samples) > 0) { split(line, f, " "); m++; mhz+=f[3]/1000; gov=f[4]; if (f[5]>t) t=f[5] }
    if (n==0) { print "FAIL no performance.csv windows"; exit 0 }
    printf "NES %s [%s]: fps avg=%.2f min=%.2f max=%.2f (windows=%d) frame=%.2f ms core=%.2f ms present=%.2f ms cpu=%.0f MHz gov=%s temp_max=%.1f C\n", label, rom, s/n, min, max, n, fm/n, cm/n, pm/n, (m?mhz/m:0), gov, t/1000 }' "$logs/nes-fps.windows")
{ date -u +%FT%TZ; echo "$summary"; cat "$logs/nes-fps.samples" "$logs/nes-fps.windows"; } >> "$logs/nes-fps.log"
echo "$summary"
