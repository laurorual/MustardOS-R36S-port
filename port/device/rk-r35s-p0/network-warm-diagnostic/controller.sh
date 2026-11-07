#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 64
. "$package/reconfigure-functions.sh"
. "$package/controller-functions.sh"
c15_sys=/sys;c15_state=/run/muos/c07/controller-rebind
bounded=/usr/libexec/muos-run-bounded
c15_exec() {
    case "$1" in
      guard)
        boot_package=/usr/libexec/muos-boot
        . "$boot_package/native-functions.sh"
        c12_guard || return 64
        [ "$(cat /run/muos/selection/mode)" = c07 ] && [ ! -e /run/muos/c07/ready ] || return 64
        for name in dropbear wpa_supplicant udhcpc bluetoothd muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog;do
            ! pidof "$name" >/dev/null || return 64
        done
        [ -d /sys/module/8821cu ] && [ ! -L /run/muos/c07 ] ;;
      unbind)
        "$bounded" 20 /bin/sh -c 'printf "%s\n" ff300000.usb > "$1/unbind"' unbind "$c15_driver" ;;
      bind)
        if [ -L "$c15_controller/driver" ];then
            [ "$(readlink -f "$c15_controller/driver")" = "$(readlink -f "$c15_driver")" ];return $?
        fi
        "$bounded" 30 /bin/sh -c 'printf "%s\n" ff300000.usb > "$1/bind"' bind "$c15_driver" || return 1
        [ "$(readlink -f "$c15_controller/driver")" = "$(readlink -f "$c15_driver")" ] ;;
      pause) sleep 1 ;;
      ready)
        # Bus numbers can change after rebind. Only this controller and VID/PID.
        n=0;candidate=
        while [ "$n" -lt 200 ];do
            candidate=
            for path in /sys/bus/usb/devices/*;do
                [ -r "$path/idVendor" ] && [ -r "$path/idProduct" ] || continue
                case "$(cat "$path/idVendor"):$(cat "$path/idProduct")" in
                  0bda:1a2b|0bda:c820)
                    case "$(readlink -f "$path")" in /sys/devices/platform/ff300000.usb/usb*/*) ;; *) return 64 ;; esac
                    [ -z "$candidate" ] || return 64
                    candidate=$path ;;
                esac
            done
            [ -z "$candidate" ] || break
            sleep 0.1;n=$((n+1))
        done
        [ -n "$candidate" ] || return 1
        if [ "$(cat "$candidate/idProduct")" = 1a2b ];then
            "$bounded" 40 "$package/usb-mode.original" || return 1
        fi
        "$bounded" 12 udevadm settle --timeout=10 || return 1
        n=0
        while [ "$n" -lt 100 ];do
            for net in /sys/class/net/*;do
                [ "$(basename "$(readlink -f "$net/device/driver/module")")" = 8821cu ] || continue
                case "$(readlink -f "$net/device")" in /sys/devices/platform/ff300000.usb/usb*/*) return 0 ;; *) return 64 ;; esac
            done
            sleep 0.1;n=$((n+1))
        done
        return 1 ;;
      *) return 64 ;;
    esac
}
c15_restore=0
finish() {
    trap - EXIT HUP INT TERM
    if [ "$c15_restore" = 1 ];then c15_exec bind >> "$c15_state/restore.log" 2>&1 || :;fi
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
c15_rebind
