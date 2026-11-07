#!/bin/sh
# SPDX-License-Identifier: MIT
# A fixed no-content diagnostic dispatch, never an arbitrary command/file loader.
set -eu
umask 077
dir=${1:-};mode=${2:-}
case "$mode" in cycle|core-failure|observe) ;; *) exit 64 ;; esac
[ "$#" = 2 ] && [ -d "$dir" ] && [ ! -L "$dir" ]
[ "$(stat -c '%u:%g:%a' "$dir")" = 0:0:700 ]
[ ! -e "$dir/cycle.once" ]; (set -C; : > "$dir/cycle.once")
run_menu() {
    phase=$1;delay=$2;expected=$3
    mkdir -m 700 "$dir/$phase-owner"
    rm -f /run/muos/first_paint /run/muos/safe_quit /run/muos/action
    printf 'launcher\n' > /run/muos/action
    MUOS_PORT_DIAGNOSTIC_CYCLE=$phase MUOS_PORT_DIAGNOSTIC_WAIT=$delay \
    LD_LIBRARY_PATH="$dir/lib:/opt/muos/frontend/lib" \
        "$dir/runner" 45 "$dir/$phase-owner" /opt/muos/frontend/muxfrontend > "$dir/state/$phase.log" 2>&1
    grep -q "^C45_LAUNCHER_PRESENT phase=$phase serial=[1-9]" "$dir/state/$phase.log"
    grep -qx "C45_LAUNCHER_EXIT action=$expected" "$dir/state/$phase.log"
    [ -f /run/muos/action ] && [ ! -L /run/muos/action ]
    printf '%s\n' "$expected" | cmp -s - /run/muos/action
    # Consume the exact fixed request only after the owner has reaped the frontend.
    mv /run/muos/action "$dir/state/$phase-action.txt"
    printf 'C45_MENU_REAPED phase=%s\n' "$phase"
}
menu_wait=2;return_wait=2
if [ "$mode" = observe ];then menu_wait=10;return_wait=30;fi
run_menu dispatch "$menu_wait" port-retro-diagnostic
mkdir -m 700 "$dir/core-owner"
core_rc=0
if [ "$mode" = core-failure ];then
    "$dir/runner" 20 "$dir/core-owner" /bin/false > "$dir/state/game.log" 2>&1 || core_rc=$?
    [ "$core_rc" = 1 ]
else
    "$dir/runner" 30 "$dir/core-owner" "$dir/muxretro" "$dir/core.so" --no-content --diagnostic-seconds=15 > "$dir/state/game.log" 2>&1 || core_rc=$?
    [ "$core_rc" = 0 ]
    grep -q '^C44_FIRST_PRESENT seconds=15' "$dir/state/game.log"
    grep -q '^C44_NORMAL_EXIT expired=1 frames=[1-9]' "$dir/state/game.log"
fi
printf 'C45_CORE_REAPED status=%s\n' "$core_rc"
run_menu return "$return_wait" port-cycle-done
printf 'C45_CYCLE_COMPLETE core_status=%s\n' "$core_rc"
[ "$mode" != core-failure ] || exit 42
