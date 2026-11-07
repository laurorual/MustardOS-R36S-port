#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 64
. "$package/reconfigure-functions.sh"
c14_sys=/sys;c14_state=/run/muos/c07/logical-reconfigure
bounded=/usr/libexec/muos-run-bounded
c14_exec() {
    case "$1" in
      guard)
        boot_package=/usr/libexec/muos-boot
        . "$boot_package/native-functions.sh"
        c12_guard || return 64
        [ "$(cat /run/muos/selection/mode)" = c07 ] || return 64
        [ ! -e /run/muos/c07/ready ] || return 64
        for name in dropbear wpa_supplicant udhcpc bluetoothd muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog;do
            ! pidof "$name" >/dev/null || return 64
        done
        [ -d /sys/module/8821cu ] && [ ! -L /run/muos/c07 ] ;;
      config-zero|config-one)
        [ "$(cat "$c14_device/idVendor"):$(cat "$c14_device/idProduct")" = 0bda:c820 ] || return 64
        value=0;seconds=10
        if [ "$1" = config-one ];then value=1;seconds=30;fi
        "$bounded" "$seconds" /bin/sh -c 'printf "%s\n" "$1" > "$2/bConfigurationValue"' write "$value" "$c14_device" ;;
      pause) sleep 1 ;;
      ready)
        "$bounded" 12 udevadm settle --timeout=10 || return 1
        n=0
        while [ "$n" -lt 100 ];do
            if [ "$(basename "$(readlink -f "$c14_wifi/driver")")" = rtl8821cu ];then
                for net in "$c14_wifi"/net/*;do [ -d "$net" ] && return 0;done
            fi
            sleep 0.1;n=$((n+1))
        done
        return 1 ;;
      *) return 64 ;;
    esac
}
c14_restore=0
finish() {
    trap - EXIT HUP INT TERM
    if [ "$c14_restore" = 1 ];then c14_exec config-one >> "$c14_state/restore.log" 2>&1 || :;fi
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
c14_reconfigure
