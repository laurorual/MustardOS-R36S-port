#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M3d step 6): long automated play. Plays each DIR/ROM for MINUTES
# (t2-game.lib.sh content handoff; the ROM's pickles are snapshotted and
# restored; no input, so title/attract loops run) and samples once a
# minute: muxretro alive (same pid), its RSS, the SoC temperature and CPU
# clock, the PCM state, and from muxretro's capture (performance.csv: the
# last 1024 frames, ~17 s of each minute) fps and frames > 25 ms (missed
# vsyncs).
#   t2-long-play.sh [--minutes N] [DIR=ROM ...]
# Default: 12 min each of NES (game_rom), SNES, GBA, MD, PSX (first ROM of
# each folder; .cue for PSX). FAIL when muxretro dies or restarts, RSS grows
# by more than 32 MiB within one game, the SoC reaches 85 C, or the PCM
# isn't RUNNING. Samples in build/logs/long-play.log, summary on stdout.
set -euo pipefail
dev=$(dirname "$0")/device.sh
logs=$(cd "$(dirname "$0")/../.." && pwd)/build/logs; mkdir -p "$logs"
minutes=12; [ "${1:-}" = --minutes ] && { minutes=$2; shift 2; }
# shellcheck source=port/scripts/t2-game.lib.sh
. "$(dirname "$0")/t2-game.lib.sh"
log=$logs/long-play.log; : > "$log"

games=("$@")
if [ ${#games[@]} -eq 0 ]; then
    games=("NES=$(game_rom)")
    for d in SNES GBA MD PSX; do
        pat='*'; [ "$d" = PSX ] && pat='*.cue'
        rom=$(r "cd '/userdata/ROMS/$d' 2>/dev/null && ls -1 $pat 2>/dev/null | head -n1") || rom=
        [ -z "$rom" ] || games+=("$d=$rom")
    done
fi

sample='p=$('"$(pids_of muxretro)"' | head -n1); csv=/run/muos/storage/pickles/performance.csv
rss=$(awk "/^VmRSS/{print \$2}" /proc/$p/status 2>/dev/null)
temp=$(cat /sys/class/thermal/thermal_zone0/temp); mhz=$(( $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq) / 1000 ))
pcm=$(sed -n "s/^state: //p" /proc/asound/card0/pcm0p/sub0/status); age=$(( $(date +%s) - $(stat -c %Y $csv 2>/dev/null || echo 0) ))
frames=$(awk "/^frame_interval_ms/{on=1;next} on&&!NF{on=0} on{t+=\$1; n++; if(\$1>25) m++; if(t>60000) exit} END{printf \"%d %.2f %d\", n, n*1000/(t?t:1), m}" $csv 2>/dev/null)
echo "pid=${p:-none} rss=${rss:-0} temp=$temp mhz=$mhz pcm=${pcm:-closed} csvage=$age frames=$frames"'

bad=0 summary=
for g in "${games[@]}"; do
    dir=${g%%=*} rom=${g#*=}
    game_start "$rom" "$dir"
    sleep 20
    first=$(r "$sample"); pid0=$(sed -n 's/^pid=\([^ ]*\).*/\1/p' <<< "$first"); rss0=$(sed -n 's/.* rss=\([0-9]*\).*/\1/p' <<< "$first")
    echo "$(date -u +%T) $dir start $first" >> "$log"
    why='' maxt=0 miss=0 fpsmin=999 n=0 pid='' rss=$rss0 temp=0 pcm='' frames=0 fps=0 missed=0
    for _ in $(seq 1 "$minutes"); do
        sleep 60
        s=$(r "$sample"); echo "$(date -u +%T) $dir $s" >> "$log"
        read -r pid rss temp _ pcm _ frames fps missed < <(sed -n 's/^pid=\([^ ]*\) rss=\([0-9]*\) temp=\([0-9]*\) mhz=\([0-9]*\) pcm=\([^ ]*\) csvage=\([0-9-]*\) frames=\([0-9]*\) \([0-9.]*\) \([0-9]*\).*/\1 \2 \3 \4 \5 \6 \7 \8 \9/p' <<< "$s") || :
        [ "${pid:-none}" = "$pid0" ] || { why+=" muxretro-gone(${pid:-none})"; break; }
        (( rss - rss0 <= 32768 )) || why+=" rss+$(( (rss - rss0) / 1024 ))MiB"
        (( temp < 85000 )) || why+=" temp=$temp"
        [ "$pcm" = RUNNING ] || why+=" pcm=$pcm"
        (( temp > maxt )) && maxt=$temp
        miss=$(( miss + ${missed:-0} )); n=$((n + 1))
        # frames=0: the sample caught muxretro rewriting its capture; skip it.
        if [ "${frames:-0}" -gt 0 ] && awk -v f="${fps:-0}" -v m="$fpsmin" 'BEGIN{exit !(f < m)}'; then fpsmin=$fps; fi
    done
    game_stop
    line="$dir: ${n} min, missed ${miss}, min fps ${fpsmin}, max ${maxt%???} C, rss $(( rss0 / 1024 ))->$(( ${rss:-$rss0} / 1024 )) MiB${why:+ FAIL:$why}"
    echo "$line"; summary+="$line"$'\n'
    [ -z "$why" ] || bad=$((bad + 1))
done
{ echo "--- summary"; printf '%s' "$summary"; } >> "$log"
if [ "$bad" = 0 ]; then echo "PASS long-play: ${#games[@]} games x ${minutes} min"; else echo "FAIL long-play: $bad of ${#games[@]} games"; exit 1; fi
