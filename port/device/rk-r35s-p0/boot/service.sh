#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
boot_package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 64
boot_state=/run/muos/boot
. "$boot_package/native-functions.sh"
. "$boot_package/order.sh"
. "$boot_package/power-functions.sh"
case "${1:-}" in start|status|check-stop|prepare-stop|shutdown|reboot|poweroff) action=$1 ;; *) exit 2 ;; esac
c12_guard || exit 64
c12_read_config || exit 64
# Read-only commands may run on the current C07 boot. Never adopt its daemons.
case "$action" in
  check-stop) exec "$boot_package/bin/muos-run-bounded" 5 "$boot_package/step.sh" session.quiescent ;;
  status)
    [ -f "$boot_state/ready" ] && [ ! -f "$boot_state/stopped" ] || exit 3
    exec "$boot_package/bin/muos-run-bounded" 5 "$boot_package/step.sh" session.status ;;
  start) [ "$enabled" = 1 ] || exit 0 ;;
  reboot|poweroff) [ "$enabled:$allow_power" = 1:1 ] || exit 64 ;;
esac
# Never stop or adopt infrastructure belonging to an earlier coordinator.
if [ "$action" != start ]; then [ -d "$boot_state/start-once" ] || exit 64; fi
[ ! -L /run/muos ] && [ ! -L "$boot_state" ] || exit 64
mkdir -p "$boot_state" || exit 64
[ "$(stat -c '%u:%g' "$boot_state")" = 0:0 ] || exit 64
chmod 700 "$boot_state"
exec 9>"$boot_state/control.lock"
flock -n 9 || exit 75
# Keep control lock out of descendant service supervisors.
boot_exec() {
    (exec 9>&-; exec "$boot_package/bin/muos-run-bounded" "$2" "$boot_package/step.sh" "$1") > "$boot_state/$1.log" 2>&1
}
case "$action" in
  start) c12_start ;;
  prepare-stop|shutdown) c12_prepare_shutdown ;;
  reboot|poweroff)
    # Abortable only before PID1 receives the request. A failed inittab action
    # cannot cancel BusyBox TERM/KILL. Do not replace the system reboot symlink.
    trap '' HUP
    power_exec() {
        case "$1" in
          check|sealed) (exec 9>&-; exec "$boot_package/bin/muos-run-bounded" 10 "$boot_package/step.sh" "power.$1") ;;
          save) (exec 9>&-; exec "$boot_package/bin/muos-run-bounded" 20 "$boot_package/diagnostic-save.sh" "$2") ;;
          request) "/sbin/$2" ;;
          *) return 64 ;;
        esac
    }
    c12_power_request ;;
esac
