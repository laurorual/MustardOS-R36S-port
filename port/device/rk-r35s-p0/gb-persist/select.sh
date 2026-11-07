#!/bin/sh
# SPDX-License-Identifier: MIT
# Native muxapp selection with a single owned application. No general script dispatcher.
set -eu
umask 077
capsule=${1:-};mode=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
case "$mode" in observe) ;; *) exit 64 ;; esac
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
"$capsule/runner" 65 "$capsule/app-owner" /bin/sh "$appdir/mux_launch.sh" "$capsule" > "$capsule/state/game.log" 2>&1 || app_rc=$?
printf 'C46_APP_REAPED status=%s\n' "$app_rc"
state_rc=0
role=$(cat "$capsule/role")
if [ "$app_rc" != 0 ] ||
   ! grep -q '^C50_EXIT reason=hotkey frames=[1-9]' "$capsule/state/game.log";then
 state_rc=64
else
 "$capsule/state-metadata" /run/muos/storage/pickles/state/core.so/GB/private > "$capsule/state/state-metadata.txt" 2>&1 || state_rc=$?
 if [ "$state_rc" = 0 ];then
  if [ "$role" = save ];then
   /bin/sh "$capsule/store.sh" "$capsule" commit > "$capsule/state/store-commit.log" 2>&1 || state_rc=$?
  elif [ "$role" = load ] && grep -Fq 'Quick Load (hotkey)' "$capsule/state/game.log" && grep -Fq 'Loaded state from ' "$capsule/state/game.log";then
   /bin/sh "$capsule/store.sh" "$capsule" verify > "$capsule/state/store-verify.log" 2>&1 || state_rc=$?
  else state_rc=64;fi
 fi
fi
printf 'C53_STATE_TRANSACTION role=%s status=%s\n' "$role" "$state_rc"
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
if [ "$app_rc" != 0 ] || [ "$state_rc" != 0 ];then exit 64;fi
printf 'C53_STATE_CYCLE_COMPLETE\n'
