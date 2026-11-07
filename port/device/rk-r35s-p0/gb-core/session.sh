#!/bin/sh
# SPDX-License-Identifier: MIT
# Owned C46 namespace: native API, automatic profile, or native app selection.
set -eu
umask 077
capsule=${1:-}; mode=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
case "$mode" in cycle|observe) ;; *) exit 64 ;; esac
[ "$#" = 2 ] && [ -d "$capsule" ] && [ ! -L "$capsule" ]
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
(set -C; : > "$capsule/gb-session.once")
if [ "$mode" = cycle ];then
    mkdir -m 700 "$capsule/gb-system" "$capsule/api-owner"
    "$capsule/runner" 25 "$capsule/api-owner" "$capsule/core-check" \
        "$capsule/core.so" "$capsule/private.gb" "$capsule/gb-system" > "$capsule/state/gb-api.log" 2>&1
    grep -q '^C49_GB_API_OK' "$capsule/state/gb-api.log"
    printf 'C49_NATIVE_API_COMPLETE\nC45_CYCLE_COMPLETE core_status=0\n'
    exit 0
fi
if [ -e "$capsule/physical.once" ] || [ -L "$capsule/physical.once" ];then
    [ -f "$capsule/physical.once" ] && [ ! -L "$capsule/physical.once" ]
    [ "$(stat -c '%u:%g:%a:%h' "$capsule/physical.once")" = 0:0:600:1 ]
    printf 'C49_PHYSICAL\n' | cmp -s - "$capsule/physical.once"
    rm "$capsule/physical.once"
    MUXRETRO_PERF_CAPTURE=1 /bin/sh "$capsule/select.sh" "$capsule" observe
else
    mkdir -m 700 "$capsule/app-owner"
    MUXRETRO_PERF_CAPTURE=1 "$capsule/runner" 65 "$capsule/app-owner" \
        /bin/sh "$capsule/app-launch.sh" "$capsule" > "$capsule/state/game.log" 2>&1
fi
grep -q '^C44_FIRST_PRESENT seconds=45' "$capsule/state/game.log"
grep -q '^C44_NORMAL_EXIT expired=1 frames=[1-9]' "$capsule/state/game.log"
trace=/run/muos/storage/pickles/performance.csv
[ -f "$trace" ] && [ ! -L "$trace" ]
[ "$(stat -c '%u:%g:%h' "$trace")" = 0:0:1 ]
[ "$(stat -c '%s' "$trace")" -le 131072 ]
cp "$trace" "$capsule/state/performance.csv"
printf 'C49_CONTENT_COMPLETE\nC45_CYCLE_COMPLETE core_status=0\n'
