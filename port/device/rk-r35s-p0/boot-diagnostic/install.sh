#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
case "${1:-}" in /run/muos-c12boot.[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]) deployment=$1 ;; *) exit 64 ;; esac
install_root=/; install_payload=$deployment/payload; install_rw=0
boot_package=$install_payload/tree/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
. "$deployment/install-functions.sh"
install_exec() {
    case "$1" in
      guard)
        c12_guard && c12_root_ro && /usr/libexec/muos-c07-network status || return 64
        [ ! -e /run/muos/session ] && [ ! -e /run/muos/boot ] || return 64
        sha256sum -c "$install_payload/prerequisites.sha256" ;;
      originals) sha256sum -c "$install_payload/prerequisites.sha256" ;;
      rw) mount -o remount,rw / ;;
      ro) mount -o remount,ro / && c12_root_ro ;;
      sync) sync ;;
      file-installed) return 0 ;;
      selection-installed)
        [ "$(sha256sum /etc/inittab | cut -d' ' -f1)" = "$(sha256sum "$install_payload/inittab.selected" | cut -d' ' -f1)" ] ;;
      *) return 64 ;;
    esac
}
finish_install() {
    trap - EXIT HUP INT TERM
    if [ "$install_rw" = 1 ]; then
        c12_install_rollback > "$deployment/rollback.log" 2>&1
        printf 'ROLLBACK_RC=%s\n' "$?"
    fi
}
trap finish_install EXIT
trap 'exit 1' HUP INT TERM
c12_install_apply || exit $?
printf 'C12_INSTALL_OK_ROOT_RO_ONCE_ARMED\n'
