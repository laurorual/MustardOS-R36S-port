#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
boot_package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 64
. "$boot_package/native-functions.sh"
. "$boot_package/select-functions.sh"
c12_guard || exit 64
selector_state=/run/muos/selection
selector_dir=/var/lib/muos-diagnostic
[ ! -L /run/muos ] && [ ! -L "$selector_state" ] && [ ! -L "$selector_dir" ] || exit 64
[ "$(stat -c '%u:%g:%a' "$selector_dir")" = 0:0:700 ] || exit 64
selector_exec() {
    case "$1" in
      c12-config) c12_read_config && [ "$enabled" = 1 ] ;;
      sync) sync ;;
      c12) "$boot_package/diagnostic.sh" ;;
      c07) /usr/libexec/muos-c07-run ;;
      c12-stop) "$boot_package/service.sh" shutdown ;;
      c07-stop) /usr/libexec/muos-c07-run stop ;;
      *) return 64 ;;
    esac
}
case "${1:-}" in start) c12_select_start ;; stop) c12_select_stop ;; *) exit 2 ;; esac
