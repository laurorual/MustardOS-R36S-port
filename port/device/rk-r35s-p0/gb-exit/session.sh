#!/bin/sh
# SPDX-License-Identifier: MIT
# C50: automatic deadline/return before native Fn+Start observation.
set -eu
umask 077
capsule=${1:-};mode=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
case "$mode" in cycle|observe) ;; *) exit 64 ;; esac
[ "$#" = 2 ] && [ -d "$capsule" ] && [ ! -L "$capsule" ]
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
(set -C; : > "$capsule/exit-session.once")
if [ "$mode" = observe ];then
    MUXRETRO_PERF_CAPTURE=1 /bin/sh "$capsule/select.sh" "$capsule" observe
else
    mkdir -m 700 "$capsule/app-owner"
    MUXRETRO_PERF_CAPTURE=1 "$capsule/runner" 65 "$capsule/app-owner" \
        /bin/sh "$capsule/app-launch.sh" "$capsule" > "$capsule/state/game.log" 2>&1
    grep -q '^C50_EXIT reason=deadline frames=[1-9]' "$capsule/state/game.log"
    # Same return sequence as C49; no native selection is claimed in this mode.
    mkdir -m 700 "$capsule/return-owner"
    rm -f /run/muos/first_paint /run/muos/safe_quit /run/muos/action
    printf 'launcher\n' > /run/muos/action
    MUOS_PORT_DIAGNOSTIC_CYCLE=return MUOS_PORT_DIAGNOSTIC_WAIT=20 \
        LD_LIBRARY_PATH="$capsule/lib:/opt/muos/frontend/lib" \
        "$capsule/runner" 35 "$capsule/return-owner" /opt/muos/frontend/muxfrontend > "$capsule/state/return.log" 2>&1
    grep -q '^C45_LAUNCHER_PRESENT phase=return serial=[1-9]' "$capsule/state/return.log"
    grep -qx 'C45_LAUNCHER_EXIT action=port-cycle-done' "$capsule/state/return.log"
    printf 'port-cycle-done\n' | cmp -s - /run/muos/action
fi
grep -q '^C50_HOTKEY_READY seconds=45 modifier=menu button=start auto_save=0 timeline=0 sram_flush=0' "$capsule/state/game.log"
grep -q '^C44_FIRST_PRESENT seconds=45' "$capsule/state/game.log"
grep -Eq '^C50_EXIT reason=(hotkey|deadline) frames=[1-9]' "$capsule/state/game.log"
trace=/run/muos/storage/pickles/performance.csv
[ -f "$trace" ] && [ ! -L "$trace" ]
[ "$(stat -c '%u:%g:%h' "$trace")" = 0:0:1 ]
[ "$(stat -c '%s' "$trace")" -le 131072 ]
cp "$trace" "$capsule/state/performance.csv"
printf 'C50_CONTENT_COMPLETE\nC45_CYCLE_COMPLETE core_status=0\n'
