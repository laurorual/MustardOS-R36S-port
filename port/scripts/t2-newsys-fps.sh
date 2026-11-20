#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2: frame pacing of the M7 new-system games over a longer run (M7c T3
# item 6: "a few small slowdowns"). Each game runs SECS seconds (default
# 75) without input (title/attract/demo) with muxretro's frame-time
# capture; the last performance.csv dump gives the session histogram
# (frames 18.5-25, 25-50, 50-250 ms) and the mean/p95 frame time. A frame
# of 25 ms or more is a visible hitch (a frame shown twice).
#   t2-newsys-fps.sh [SECS] [DIR...]
# Volume 10 for the run (night rule), the user's level restored.
# Summary on stdout; raw dumps in build/logs/m7/newsys-fps/.
set -euo pipefail
dev=port/scripts/device.sh
cd "$(dirname "$0")/../.."
# shellcheck source=port/scripts/t2-game.lib.sh
. port/scripts/t2-game.lib.sh
secs=${1:-75}; shift || :
dirs=("$@"); [ ${#dirs[@]} -gt 0 ] || dirs=(32X ATARI2600 ATARI7800 GG LYNX SMS PCE)
out=build/logs/m7/newsys-fps; mkdir -p "$out"
env_pw='export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run'
vol=$(r 'cat /opt/muos/config/settings/general/volume')
r "$env_pw; /opt/muos/script/device/audio.sh 10 >/dev/null 2>&1" || :
trap 'r "$env_pw; /opt/muos/script/device/audio.sh $vol >/dev/null 2>&1" || :' EXIT
printf '%-10s %6s %6s %6s %6s %6s %5s %5s %5s %5s  %s\n' dir hz mean p95 peak core 18-25 25-50 50+ temp rom
for d in "${dirs[@]}"; do
    # M8: a disc's index file (cue/m3u/gdi...) rather than its first track
    rom=$(r "cd '/userdata/ROMS/$d' && { ls | grep -i -E '\\.(m3u|cue|gdi|chd|cdi|iso|cso)\$' || ls; } | head -n1")
    game_start "$rom" "$d"
    sleep "$secs"
    t=$(r 'cat /sys/class/thermal/thermal_zone0/temp')
    r 'cat /run/muos/storage/pickles/performance.csv' > "$out/$d.csv" || :
    game_stop
    awk -F, -v d="$d" -v t="$t" -v rom="$rom" '
        /^frame,/{mean=$4; p95=$7; pk=$9}
        /^core,/{core=$4}
        /^observed_present_hz,/{hz=$2}
        /^frame_histogram_18_5_to_25_ms,/{a=$2}
        /^frame_histogram_25_to_50_ms,/{b=$2}
        /^frame_histogram_50_to_250_ms,/{c=$2}
        END{printf "%-10s %6.2f %6.2f %6.2f %6.1f %6.2f %5d %5d %5d %5.1f  %s\n", d, hz, mean, p95, pk, core, a, b, c, t/1000, rom}' "$out/$d.csv"
done
