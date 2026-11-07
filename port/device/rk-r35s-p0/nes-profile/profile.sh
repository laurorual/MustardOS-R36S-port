#!/bin/sh
# SPDX-License-Identifier: MIT
# C48: no menu selection or physical input needed; fixed C47 silent content.
set -eu
umask 077
capsule=${1:-}; mode=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
[ "$#" = 2 ] && [ "$mode" = observe ]
[ -d "$capsule" ] && [ ! -L "$capsule" ]
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
(set -C; : > "$capsule/profile.once")
mkdir -m 700 "$capsule/app-owner"
if [ -e "$capsule/physical.once" ] || [ -L "$capsule/physical.once" ];then
    [ -f "$capsule/physical.once" ] && [ ! -L "$capsule/physical.once" ]
    [ "$(stat -c '%u:%g:%a:%h' "$capsule/physical.once")" = 0:0:600:1 ]
    printf 'C48_PHYSICAL\n' | cmp -s - "$capsule/physical.once"
    rm "$capsule/physical.once"
    # C47/C46 selection and return are used unchanged for the new core build.
    # select.sh owns app-owner itself.
    rmdir "$capsule/app-owner"
    MUXRETRO_PERF_CAPTURE=1 /bin/sh "$capsule/select.sh" "$capsule" observe
else
MUXRETRO_PERF_CAPTURE=1 "$capsule/runner" 50 "$capsule/app-owner" \
    /bin/sh "$capsule/app-launch.sh" "$capsule" > "$capsule/state/game.log" 2>&1
fi
grep -q '^C44_FIRST_PRESENT seconds=30' "$capsule/state/game.log"
grep -q '^C44_NORMAL_EXIT expired=1 frames=[1-9]' "$capsule/state/game.log"
trace=/run/muos/storage/pickles/performance.csv
[ -f "$trace" ] && [ ! -L "$trace" ]
[ "$(stat -c '%u:%g:%h' "$trace")" = 0:0:1 ]
[ "$(stat -c '%s' "$trace")" -le 131072 ]
cp "$trace" "$capsule/state/performance.csv"
printf 'C48_PROFILE_COMPLETE\nC45_CYCLE_COMPLETE core_status=0\n'
