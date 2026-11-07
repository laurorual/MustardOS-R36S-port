#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
case "${1:-}" in /run/muos-c12power.[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]) deployment=$1 ;; *) exit 64 ;; esac
update_root=/; update_payload=$deployment/payload; update_rw=0
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
. "$deployment/install-functions.sh"
. "$deployment/power-update-functions.sh"
update_exec() {
    case "$1" in
      guard)
        c12_guard && c12_read_config && c12_root_ro || return 64
        [ "$allow_power" = 0 ] && [ "$(cat /run/muos/selection/mode)" = c07 ] || return 64
        [ ! -e /run/muos/session ] && [ ! -e /run/muos/boot ] || return 64
        [ ! -e /var/lib/muos-diagnostic/c12.once ] && [ ! -L /var/lib/muos-diagnostic/c12.once ] || return 64
        /usr/libexec/muos-c07-network status && sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 ;;
      originals) (cd / && sha256sum -c "$update_payload/unchanged.sha256") && sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 ;;
      rw) mount -o remount,rw / ;;
      ro) mount -o remount,ro / && c12_root_ro ;;
      sync) sync ;;
      file-installed) return 0 ;;
      *) return 64 ;;
    esac
}
finish_update() {
    trap - EXIT HUP INT TERM
    if [ "$update_rw" = 1 ]; then
        c12_update_rollback > "$deployment/rollback.log" 2>&1
        printf 'ROLLBACK_RC=%s\n' "$?"
    fi
}
trap finish_update EXIT
trap 'exit 1' HUP INT TERM
c12_update_apply || exit $?
printf 'C12_POWER_UPDATE_OK_ROOT_RO_NO_TOKEN_POWER_DISABLED\n'
