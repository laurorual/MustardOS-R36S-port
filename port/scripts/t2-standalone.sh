#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M8f): one standalone emulator run through the frontend's content
# handoff (as a menu launch): it must start, present frames (swapstat.so,
# muos-flycast/-yabasanshiro/-ppsspp preload it under perf-capture), keep
# running for SECS, and quit on Fn+Start (muos-standalone-quit) back to the
# menu. Prints presented frames/s, the SoC temperature, the CPU clock and
# the emulator's CPU share (t2-threads.sh), and the frontend log lines of
# the launcher.
#   t2-standalone.sh NAME CORE DIR FILE PROC [SECS] [GOV]
#   e.g. t2-standalone.sh flycast-sa ext-flycast DC "Power Stone 2 (USA).cue" flycast 120
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
dev=port/scripts/device.sh
# shellcheck source=port/scripts/t2-game.lib.sh
. port/scripts/t2-game.lib.sh
name=$1 core=$2 dir=$3 file=$4 proc=$5 secs=${6:-60} gov=${7:-performance}
out=build/logs/m8f/sa-$name; mkdir -p "$out"
env_pw='export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run'
vol0=$(r 'cat /opt/muos/config/settings/general/volume')
trap 'port/scripts/t2-swapstat.sh disarm >/dev/null 2>&1; r "$env_pw; /opt/muos/script/device/audio.sh $vol0 >/dev/null 2>&1" || :' EXIT
r "$env_pw; /opt/muos/script/device/audio.sh 10 >/dev/null 2>&1" || :
port/scripts/t2-swapstat.sh arm >/dev/null
wait_module muxlaunch 40 || { r '/usr/libexec/muos-press b'; sleep 2; }
n0=$(r 'wc -l < /opt/muos/log/frontend.log')
label=${file##*/}; label=${label%.*}
r 'printf "%s\n" "'"$label"'" '"$core"' x 0 0 '"$core"' /mnt/mmc/ROMS /'"$dir"' "'"$file"'" > /run/muos/content
   echo '"$gov"' > /run/muos/governor; echo explore > /run/muos/action
   '"$(pids_of muxfrontend)"' | while read -r q; do kill -TERM "$q"; done'
for _ in $(seq 30); do r "pidof $proc" >/dev/null && break; sleep 1; done
r "pidof $proc" >/dev/null || { r "tail -n +$n0 /opt/muos/log/frontend.log" > "$out/frontend.txt"; tail -5 "$out/frontend.txt"; fail "$proc did not start"; }
sleep 20
port/scripts/t2-swapstat.sh grab "$out/1-start.png" >/dev/null 2>&1 || :
sleep "$secs"
port/scripts/t2-swapstat.sh grab "$out/2-run.png" >/dev/null 2>&1 || :
"$dev" run "sh -s $proc" < port/scripts/t2-threads.sh > "$out/threads.txt" 2>/dev/null || :
port/scripts/t2-swapstat.sh report 20 > "$out/swap.txt" 2>&1 || :
alive=$(r "pidof $proc" || echo gone)
r '/usr/libexec/muos-press fn+start'
for i in $(seq 15); do r "pidof $proc" >/dev/null || break; sleep 1; done
r "tail -n +$n0 /opt/muos/log/frontend.log" > "$out/frontend.txt" || :
wait_module muxplore 15 || :
r '/usr/libexec/muos-press b'; sleep 2
echo "$name: alive during run: $alive; quit after ~${i}s; menu: $(module)"
tail -3 "$out/swap.txt"
head -4 "$out/threads.txt"
grep -a -E "muos-$proc|muos-${core#ext-}|standalone-quit|exit rc" "$out/frontend.txt" | cut -c1-200 | tail -6
grep -a -c -i -E "segfault|signal 11|SIGSEGV" "$out/frontend.txt" | sed 's/^/crash lines: /'
[ "$alive" != gone ] || fail "$proc died during the run"
echo PASS
