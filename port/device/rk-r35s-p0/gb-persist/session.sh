#!/bin/sh
# SPDX-License-Identifier: MIT
# C53: selective persistent snapshot; retain C51 runtime lifecycle.
set -eu
umask 077
capsule=${1:-};mode=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
case "$mode" in observe) ;; *) exit 64 ;; esac
[ "$#" = 2 ] && [ -d "$capsule" ] && [ ! -L "$capsule" ]
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
(set -C; : > "$capsule/state-session.once")
/bin/sh "$capsule/store.sh" "$capsule" seed > "$capsule/state/store-seed.log" 2>&1
[ "$mode" = observe ]
MUXRETRO_PERF_CAPTURE=1 /bin/sh "$capsule/select.sh" "$capsule" observe
grep -q '^C50_HOTKEY_READY seconds=45 modifier=menu button=start auto_save=0 timeline=0 sram_flush=0' "$capsule/state/game.log"
grep -q '^C44_FIRST_PRESENT seconds=45' "$capsule/state/game.log"
grep -Eq '^C50_EXIT reason=(hotkey|deadline) frames=[1-9]' "$capsule/state/game.log"
trace=/run/muos/storage/pickles/performance.csv
[ -f "$trace" ] && [ ! -L "$trace" ]
[ "$(stat -c '%u:%g:%h' "$trace")" = 0:0:1 ]
[ "$(stat -c '%s' "$trace")" -le 131072 ]
cp "$trace" "$capsule/state/performance.csv"
printf 'C53_CONTENT_COMPLETE\nC45_CYCLE_COMPLETE core_status=0\n'
