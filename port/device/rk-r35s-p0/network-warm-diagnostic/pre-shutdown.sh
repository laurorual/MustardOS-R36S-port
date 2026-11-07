#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 64
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
. "$package/pre-shutdown-functions.sh"
bounded=/usr/libexec/muos-run-bounded
c17_state=$package/state
controller=/sys/bus/platform/devices/ff300000.usb
driver=/sys/bus/platform/drivers/dwc2
sequence=$(cat "$package/sequence") || exit 64
case "$sequence" in ''|*[!0-9]*|?????*) exit 64;;esac
[ "$sequence" -gt 0 ] && [ "$sequence" -lt 9999 ] || exit 64
exec 9>/run/muos/c07/maintenance.lock
flock -n 9 || exit 75
trap '' HUP
call() { (exec 9>&-;exec "$bounded" "$@"); }
root_guard() { c12_guard && c12_read_config && c12_root_ro; }
sole_working_host() {
    [ "$(readlink -f "$controller/driver")" = "$driver" ] || return 64
    roots=0;devices=0
    for p in /sys/bus/usb/devices/*;do
        [ -r "$p/idVendor" ] && [ -r "$p/idProduct" ] || continue
        case "$(cat "$p/idVendor"):$(cat "$p/idProduct")" in
          1d6b:0002)
            [ "$(dirname "$(readlink -f "$p")")" = "$(readlink -f "$controller")" ] || return 64
            roots=$((roots+1)) ;;
          0bda:c820)
            case "$(readlink -f "$p")" in /sys/devices/platform/ff300000.usb/usb*/*) ;; *) return 64;;esac
            [ "$(cat "$p/bNumInterfaces" | tr -d ' ')" = 3 ] || return 64
            for intf in "$p":*;do
                [ -r "$intf/bInterfaceClass" ] || continue
                kind=$(cat "$intf/bInterfaceClass"):$(cat "$intf/bInterfaceSubClass"):$(cat "$intf/bInterfaceProtocol")
                case "$kind" in
                  ff:ff:ff) [ "$(basename "$(readlink -f "$intf/driver")")" = rtl8821cu ] || return 64 ;;
                  e0:01:01) [ ! -L "$intf/driver" ] || [ "$(basename "$(readlink -f "$intf/driver")")" = btusb ] || return 64 ;;
                  *) return 64 ;;
                esac
            done
            devices=$((devices+1)) ;;
          *) return 64 ;;
        esac
    done
    [ "$roots:$devices" = 1:1 ] || return 64
    for net in /sys/class/net/*;do
        [ "$(basename "$(readlink -f "$net/device/driver/module")")" = 8821cu ] || continue
        case "$(readlink -f "$net/device")" in /sys/devices/platform/ff300000.usb/usb*/*) return 0 ;; esac
    done
    return 64
}
bind_host() {
    [ ! -L "$controller/driver" ] || { [ "$(readlink -f "$controller/driver")" = "$driver" ];return $?; }
    call 30 /bin/sh -c 'printf "%s\n" ff300000.usb > "$1/bind"' bind "$driver"
}
restore_token() {
    root_guard || return 1
    for token in /var/lib/muos-diagnostic/c16.once /var/lib/muos-diagnostic/c17.c16-used;do
        [ ! -L "$token" ] && [ "$(stat -c '%u:%g:%a:%h:%s' "$token")" = 0:0:600:1:14 ] || return 1
    done
    [ "$(cat /var/lib/muos-diagnostic/c16.once)" = MUOS-C16-ONCE ] || return 1
    [ "$(cat /var/lib/muos-diagnostic/c17.c16-used)" = MUOS-C16-ONCE ] || return 1
    [ ! -e /var/lib/muos-diagnostic/c16.used ] || return 1
    mount -o remount,rw / || return 1
    rm /var/lib/muos-diagnostic/c16.once &&
      mv /var/lib/muos-diagnostic/c17.c16-used /var/lib/muos-diagnostic/c16.used &&
      sync
    rc=$?
    mount -o remount,ro / && c12_root_ro || return 1
    return "$rc"
}
save_public() {
    report=$c17_state/PRE.txt
    {
        echo MUOS-C17-PRE-SHUTDOWN
        echo "BOOT_SEQ=$sequence NORMAL_REBOOT_INTENT=1"
        cat "$c17_state/steps.txt"
        echo DWC2_DETACHED=1
        echo ROOT_RO=1
        echo PID1_REQUEST_NOT_YET_ATTEMPTED=1
        cat "$c17_state/baseline.txt"
    } > "$report" || return 1
    mounted=0
    mount -t vfat -o ro,nosuid,nodev,noexec "$boot_partition" /boot || return 1
    mounted=1
    [ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ] || return 1
    destination=$(printf '/boot/DIAG09/BOOT%04d' "$sequence")
    [ -f "$destination/REPORT.TXT" ] &&
      [ ! -e "$destination/C17PRE.TXT" ] && [ ! -e "$destination/C17PRE.TMP" ] || return 1
    mount -o remount,rw,nosuid,nodev,noexec /boot || return 1
    cp "$report" "$destination/C17PRE.TMP" &&
      mv "$destination/C17PRE.TMP" "$destination/C17PRE.TXT" &&
      sync && cmp "$report" "$destination/C17PRE.TXT" || return 1
    umount /boot || return 1
    mounted=0
}
c17_exec() {
    case "$1" in
      preflight)
        root_guard || return 64
        [ "$(cat /run/muos/selection/mode)" = c07 ] &&
        [ "$(cat /var/lib/muos-diagnostic/boot-seq)" = "$sequence" ] || return 64
        [ "$allow_power" = 0 ] && [ ! -e /var/lib/muos-diagnostic/c12.once ] || return 64
        c12_session_quiescent || return 64
        ! pidof bluetoothd >/dev/null || return 64
        sole_working_host || return 64
        /usr/libexec/muos-c07-network status || return 64
        for token in /var/lib/muos-diagnostic/c16.once /var/lib/muos-diagnostic/c17.c16-used;do
            [ ! -L "$token" ] && [ "$(stat -c '%u:%g:%a:%h:%s' "$token")" = 0:0:600:1:14 ] || return 64
        done
        [ "$(cat /var/lib/muos-diagnostic/c16.once)" = MUOS-C16-ONCE ] &&
        [ ! -e /var/lib/muos-diagnostic/c16.used ] &&
        [ "$(cat /var/lib/muos-diagnostic/c17.c16-used)" = MUOS-C16-ONCE ] || return 64
        sha256sum -c "$package/installed.sha256" >/dev/null &&
          sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null ;;
      baseline)
        call 10 /usr/libexec/muos-c16/usb-control-probe baseline > "$c17_state/baseline.txt" || return 1
        grep -qx READ_FAILURES=0 "$c17_state/baseline.txt" ;;
      network-stop)
        mkdir "$c17_state/identities" || return 1
        for name in dropbear dhcp wpa;do
            case "$name" in dropbear) exe=/usr/sbin/dropbear;;dhcp) exe=/bin/busybox;;wpa) exe=/usr/sbin/wpa_supplicant;;esac
            c12_record_pid "/run/muos/c07/$name.pid" "$c17_state/identities/$name" "$exe" || return 1
            c12_check_pid "/run/muos/c07/$name.pid" "$c17_state/identities/$name" "$exe" || return 1
        done
        call 20 /usr/libexec/muos-c07-network stop && c12_network_empty ;;
      controller-unbind)
        [ "$(readlink -f "$controller/driver")" = "$driver" ] || return 64
        call 20 /bin/sh -c 'printf "%s\n" ff300000.usb > "$1/unbind"' unbind "$driver" ;;
      controller-absent)
        [ ! -L "$controller/driver" ] || return 1
        for hub in /sys/devices/platform/ff300000.usb/usb*;do [ ! -d "$hub" ] || return 1;done ;;
      archive) call 10 sync && c12_root_ro && save_public ;;
      final-seal)
        root_guard && c12_network_empty && [ ! -L "$controller/driver" ] &&
        [ "$(cat /var/lib/muos-diagnostic/c16.once)" = MUOS-C16-ONCE ] ;;
      request)
        c17_requested=1
        /sbin/reboot
        request_rc=$?
        [ "$request_rc" = 0 ] || c17_requested=0
        return "$request_rc" ;;
      abort-restore)
        # PID1 has not been asked. Preserve RO and attempt one rollback.
        [ "$c17_abort_attempted" = 0 ] || return 0
        c17_abort_attempted=1
        if [ "$mounted" = 1 ];then umount /boot || return 1;mounted=0;fi
        if [ "$c17_unbound" = 1 ];then bind_host || return 1;fi
        restore_token || return 1
        /usr/libexec/muos-c07-network status && return 0
        c12_network_empty || return 1
        call 120 /usr/libexec/muos-c16/usb-mode.original || return 1
        call 120 /usr/libexec/muos-c07-network recover ;;
      *) return 64 ;;
    esac
}
c17_stopped=0;c17_unbound=0;c17_requested=0;c17_abort_attempted=0;mounted=0
finish() {
    trap - EXIT INT TERM
    if [ "$c17_requested" = 0 ];then c17_exec abort-restore > "$package/abort-restore.log" 2>&1 || :;fi
}
trap finish EXIT
trap 'exit 143' INT TERM
c17_run
