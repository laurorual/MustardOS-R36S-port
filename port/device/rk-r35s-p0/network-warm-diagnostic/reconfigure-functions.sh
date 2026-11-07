# SPDX-License-Identifier: MIT
# Distinct from USB reset: unconfigure/reconfigure the exact idle composite device.
c14_find() {
    c14_device=
    for path in "$c14_sys"/bus/usb/devices/*; do
        [ -r "$path/idVendor" ] && [ -r "$path/idProduct" ] || continue
        [ "$(cat "$path/idVendor"):$(cat "$path/idProduct")" = 0bda:c820 ] || continue
        [ -z "$c14_device" ] || return 64
        c14_device=$path
    done
    [ -n "$c14_device" ] || return 64
    [ "$(cat "$c14_device/bNumConfigurations")" = 1 ] &&
    [ "$(cat "$c14_device/bConfigurationValue")" = 1 ] &&
    [ "$(cat "$c14_device/bNumInterfaces" | tr -d ' ')" = 3 ] || return 64
    c14_wifi=
    for path in "$c14_device":*; do
        [ -r "$path/bInterfaceClass" ] || continue
        signature=$(cat "$path/bInterfaceClass"):$(cat "$path/bInterfaceSubClass"):$(cat "$path/bInterfaceProtocol")
        case "$signature" in
          e0:01:01) [ ! -L "$path/driver" ] || [ "$(basename "$(readlink -f "$path/driver")")" = btusb ] || return 64 ;;
          ff:ff:ff)
            [ -z "$c14_wifi" ] && [ ! -L "$path/driver" ] || return 64
            c14_wifi=$path ;;
          *) return 64 ;;
        esac
    done
    [ -n "$c14_wifi" ]
}
c14_reconfigure() {
    c14_exec guard || return 64
    c14_find || return 64
    [ ! -L "$c14_state" ] && mkdir -m 700 "$c14_state" || return 64
    c14_restore=1
    c14_exec config-zero
    rc=$?;printf 'C14_CONFIG_ZERO_RC=%s\n' "$rc" >> "$c14_state/report.txt"
    # A timed-out write may have changed device state; attempt configuration1
    # even when config-zero failed. Never force a reset/unload or power off.
    if [ "$rc" = 0 ]; then
        c14_exec pause
        c14_exec config-one
        rc=$?;printf 'C14_CONFIG_ONE_RC=%s\n' "$rc" >> "$c14_state/report.txt"
        if [ "$rc" = 0 ] && c14_exec ready; then
            printf 'C14_DRIVER_NETDEV_READY=1\n' >> "$c14_state/report.txt"
            c14_restore=0
            return 0
        fi
    fi
    c14_exec config-one
    rc=$?;printf 'C14_RESTORE_CONFIG_ONE_RC=%s\n' "$rc" >> "$c14_state/report.txt"
    c14_restore=0
    return 1
}
