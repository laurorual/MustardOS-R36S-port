#!/bin/sh
# SPDX-License-Identifier: MIT
# Native muxapp selection with a single owned application. No general script dispatcher.
set -eu
umask 077
capsule=${1:-};mode=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
case "$mode" in cycle|observe) ;; *) exit 64 ;; esac
[ "$#" = 2 ] && [ -d "$capsule" ] && [ ! -L "$capsule" ] || exit 64
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
(set -C; : > "$capsule/selection.once")
appdir=/opt/muos/config/port-apps/R35S-Diagnostic
mkdir -m 700 "$capsule/app-tree" "$capsule/app-tree/R35S-Diagnostic"
cp "$capsule/app-launch.sh" "$capsule/app-tree/R35S-Diagnostic/mux_launch.sh"
chmod 700 "$capsule/app-tree/R35S-Diagnostic/mux_launch.sh"
[ ! -L /opt/muos/config/port-apps ] && [ ! -L "$appdir" ] || exit 64
mkdir -p -m 700 /opt/muos/config/port-apps "$appdir"
if findmnt -rn -M "$appdir" >/dev/null;then exit 64;fi
mount --bind "$capsule/app-tree/R35S-Diagnostic" "$appdir"
printf '%s\n' "$appdir" >> "$capsule/state/mounts"
. "$capsule/adapter.sh"
if [ "$mode" = cycle ];then
    # Guard-only native rehearsal: no UI or app execution, no claim of selection.
    printf 'app\n' > /run/muos/action;printf '%s' "$appdir" > /run/muos/application
    c46_validate
    printf '/tmp/other-app\n' > /run/muos/application
    if c46_validate;then exit 1;fi
    printf '%s' "$appdir" > /run/muos/application
    mv /run/muos/application "$capsule/application.saved"
    ln -s "$capsule/application.saved" /run/muos/application
    if c46_validate;then exit 1;fi
    rm /run/muos/application;mv "$capsule/application.saved" /run/muos/application
    chmod 777 "$appdir/mux_launch.sh";if c46_validate;then exit 1;fi
    chmod 700 "$appdir/mux_launch.sh"
    printf '#changed\n' >> "$appdir/mux_launch.sh";if c46_validate;then exit 1;fi
    cp "$capsule/app-launch.sh" "$appdir/mux_launch.sh";chmod 700 "$appdir/mux_launch.sh"
    printf '%s' "$(cat /opt/muos/device/config/cpu/default)" > /run/muos/governor
    printf 'system' > /run/muos/controller
    c46_consume
    [ ! -e /run/muos/governor ] && [ ! -e /run/muos/controller ]
    if c46_validate;then exit 1;fi
    mkdir -m 700 "$capsule/nes-system"
    "$capsule/core-check" "$capsule/core.so" "$capsule/r35s-flight.nes" "$capsule/nes-system" > "$capsule/state/nes-api.log" 2>&1
    grep -q '^C47_NES_API_OK' "$capsule/state/nes-api.log"
    printf 'C47_NATIVE_GUARDS_OK cases=6 no_ui=1 core_API_executed=1\n' 
    printf 'C45_CYCLE_COMPLETE core_status=guard-only\n'
    exit 0
fi
mkdir -m 700 "$capsule/dispatch-owner"
rm -f /run/muos/first_paint /run/muos/safe_quit /run/muos/application /run/muos/action
printf 'app\n' > /run/muos/action
MUOS_PORT_APP_DIAGNOSTIC=1 LD_LIBRARY_PATH="$capsule/lib:/opt/muos/frontend/lib" \
    "$capsule/runner" 135 "$capsule/dispatch-owner" /opt/muos/frontend/muxfrontend > "$capsule/state/dispatch.log" 2>&1
grep -q '^C46_APP_PRESENT serial=[1-9]' "$capsule/state/dispatch.log"
for kind in cancel timeout;do
    if printf 'port-app-%s\n' "$kind" | cmp -s - /run/muos/action;then
        grep -qx "C46_APP_LEAVE action=port-app-$kind" "$capsule/state/dispatch.log"
        printf 'C46_CANCELLED kind=%s\nC45_CYCLE_COMPLETE core_status=cancel\n' "$kind"
        exit 0
    fi
done
c46_consume
printf 'C46_NATIVE_SELECTION_CONSUMED options_quarantined=1\n'
mkdir -m 700 "$capsule/app-owner"
app_rc=0
"$capsule/runner" 50 "$capsule/app-owner" /bin/sh "$appdir/mux_launch.sh" "$capsule" > "$capsule/state/game.log" 2>&1 || app_rc=$?
if [ "$app_rc" = 0 ];then
grep -q '^C44_FIRST_PRESENT seconds=30' "$capsule/state/game.log"
grep -q '^C44_NORMAL_EXIT expired=1 frames=[1-9]' "$capsule/state/game.log"
fi
printf 'C46_APP_REAPED status=%s\n' "$app_rc"
mkdir -m 700 "$capsule/return-owner"
rm -f /run/muos/first_paint /run/muos/safe_quit /run/muos/action
printf 'launcher\n' > /run/muos/action
MUOS_PORT_DIAGNOSTIC_CYCLE=return MUOS_PORT_DIAGNOSTIC_WAIT=20 \
    LD_LIBRARY_PATH="$capsule/lib:/opt/muos/frontend/lib" \
    "$capsule/runner" 35 "$capsule/return-owner" /opt/muos/frontend/muxfrontend > "$capsule/state/return.log" 2>&1
grep -q '^C45_LAUNCHER_PRESENT phase=return serial=[1-9]' "$capsule/state/return.log"
grep -qx 'C45_LAUNCHER_EXIT action=port-cycle-done' "$capsule/state/return.log"
printf 'port-cycle-done\n' | cmp -s - /run/muos/action
printf 'C46_SELECTION_COMPLETE app_status=%s\nC45_CYCLE_COMPLETE core_status=%s\n' "$app_rc" "$app_rc"
