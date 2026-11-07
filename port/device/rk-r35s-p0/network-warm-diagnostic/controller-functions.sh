# SPDX-License-Identifier: MIT
# Selection uses the C14 composite guard, but recovery acts on its sole DWC2 host.
c15_select() {
    c14_sys=$c15_sys
    c14_find || return 64
    c15_controller=$c15_sys/bus/platform/devices/ff300000.usb
    c15_driver=$c15_sys/bus/platform/drivers/dwc2
    [ "$(readlink -f "$c15_controller/driver")" = "$(readlink -f "$c15_driver")" ] || return 64
    c15_hub=;hubs=0
    for hub in "$c15_sys"/bus/usb/devices/usb*;do
        [ -d "$hub" ] || continue
        [ "$(dirname "$(readlink -f "$hub")")" = "$(readlink -f "$c15_controller")" ] || return 64
        c15_hub=$(readlink -f "$hub");hubs=$((hubs+1))
    done
    [ "$hubs" = 1 ] || return 64
    [ "$(dirname "$(readlink -f "$c14_device")")" = "$c15_hub" ] || return 64
    # No external hub, storage or other USB device may share this operation.
    devices=0
    for path in "$c15_sys"/bus/usb/devices/*;do
        [ -r "$path/idVendor" ] && [ -r "$path/idProduct" ] || continue
        [ "$(readlink -f "$path")" != "$c15_hub" ] || continue
        [ "$(readlink -f "$path")" = "$(readlink -f "$c14_device")" ] || return 64
        devices=$((devices+1))
    done
    [ "$devices" = 1 ]
}
c15_rebind() {
    c15_exec guard || return 64
    c15_select || return 64
    [ ! -L "$c15_state" ] && mkdir -m 700 "$c15_state" || return 64
    c15_restore=1
    c15_exec unbind
    rc=$?;printf 'C15_CONTROLLER_UNBIND_RC=%s\n' "$rc" >> "$c15_state/report.txt"
    if [ "$rc" = 0 ];then
        c15_exec pause
        c15_exec bind
        rc=$?;printf 'C15_CONTROLLER_BIND_RC=%s\n' "$rc" >> "$c15_state/report.txt"
        if [ "$rc" = 0 ] && c15_exec ready;then
            printf 'C15_DRIVER_NETDEV_READY=1\n' >> "$c15_state/report.txt"
            c15_restore=0
            return 0
        fi
    fi
    c15_exec bind
    rc=$?;printf 'C15_RESTORE_CONTROLLER_BIND_RC=%s\n' "$rc" >> "$c15_state/report.txt"
    c15_restore=0
    return 1
}
