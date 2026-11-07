#!/bin/sh
# SPDX-License-Identifier: MIT
# Exact dongle only: virtual CD-ROM 0bda:1a2b -> Wi-Fi 0bda:c820.
set -eu
[ "$(cat /etc/muos-network-diagnostic 2>/dev/null)" = MUOS-R35S-NETWORK-P4-C07 ] || exit 64
state=/run/muos/c07
[ ! -e "$state/ready" ] || { echo 'C07: refuse USB initialization while network is active'; exit 64; }
mkdir -p "$state/private"
chmod 700 "$state/private"
candidate=
n=0
while [ "$n" -lt 100 ]; do
    candidate=
    for path in /sys/bus/usb/devices/*; do
        [ -r "$path/idVendor" ] && [ -r "$path/idProduct" ] || continue
        case "$(cat "$path/idVendor"):$(cat "$path/idProduct")" in
            0bda:1a2b|0bda:c820)
                [ -z "$candidate" ] || { echo 'C07: ambiguous USB dongles'; exit 1; }
                candidate=$path ;;
        esac
    done
    [ -z "$candidate" ] || break
    sleep 0.1; n=$((n+1))
done
[ -n "$candidate" ] || { echo 'C07: USB dongle absent'; exit 1; }
origin=$(cat "$candidate/idProduct")
reset_done=0
eject_done=0
if [ "$(cat "$candidate/idProduct")" = c820 ]; then
    # A warm reboot can retain c820 but leave the new kernel without a netdev.
    # Reset this device only; no EEPROM/flash command, block path or hub reset.
    bus=$(cat "$candidate/busnum"); device=$(cat "$candidate/devnum")
    case "$bus:$device" in *[!0-9:]*|:*|*:) exit 1 ;; esac
    /usr/libexec/muos-run-bounded 20 usb_modeswitch -R -v 0bda -p c820 -b "$bus" -g "$device" \
        > "$state/private/usb-reset.log" 2>&1 || { echo 'C07: USB reset command failed'; exit 1; }
    # usb_modeswitch2.6.1 can exit0 after its void resetUSB() reports failure.
    grep -q 'Device was reset' "$state/private/usb-reset.log" || { echo 'C07: USB reset not confirmed'; exit 1; }
    reset_done=1
    n=0
    while [ "$n" -lt 100 ]; do
        if [ -r "$candidate/idVendor" ] && [ -r "$candidate/idProduct" ] && [ "$(cat "$candidate/idVendor")" = 0bda ]; then
            case "$(cat "$candidate/idProduct")" in 1a2b|c820) break ;; esac
        fi
        sleep 0.1; n=$((n+1))
    done
    [ "$n" -lt 100 ] || { echo 'C07: reset dongle missing'; exit 1; }
fi
# Require mass-storage interface before issuing the standard CD-ROM eject.
if [ "$(cat "$candidate/idProduct")" = 1a2b ]; then
storage=0
for interface in "$candidate":*; do
    [ -r "$interface/bInterfaceClass" ] || continue
    [ "$(cat "$interface/bInterfaceClass")" != 08 ] || storage=1
done
[ "$storage" = 1 ] || { echo 'C07: initial USB mode is not mass storage'; exit 1; }
bus=$(cat "$candidate/busnum"); device=$(cat "$candidate/devnum")
case "$bus:$device" in *[!0-9:]*|:*) exit 1 ;; esac
# Same operation as the installed dArkOSen custom rule, additionally pinned
# to this bus/device. Never invoke eject on /dev/sdX or touch SD partitions.
/usr/libexec/muos-run-bounded 20 usb_modeswitch -K -v 0bda -p 1a2b -b "$bus" -g "$device" \
    > "$state/private/usb-switch.log" 2>&1 || { echo 'C07: standard eject failed'; exit 1; }
eject_done=1
fi
n=0
while [ "$n" -lt 300 ]; do
    if [ -r "$candidate/idVendor" ] && [ -r "$candidate/idProduct" ] &&
       [ "$(cat "$candidate/idVendor"):$(cat "$candidate/idProduct")" = 0bda:c820 ]; then
        break
    fi
    sleep 0.1; n=$((n+1))
done
[ "$n" -lt 300 ] || { echo 'C07: USB dongle did not return as 0bda:c820'; exit 1; }
/usr/libexec/muos-run-bounded 12 udevadm settle --timeout=10 || { echo 'C07: USB settle failed'; exit 1; }
if [ "$reset_done" = 1 ]; then
    modprobe 8821cu || exit 1
    # Reset alone need not retry an interface whose initial probe failed.
    # Retry only an unbound FF/FF/FF interface (the compiled8821cu alias).
    for interface in "$candidate":*; do
        [ -r "$interface/bInterfaceClass" ] && [ -r "$interface/bInterfaceSubClass" ] && [ -r "$interface/bInterfaceProtocol" ] || continue
        [ "$(cat "$interface/bInterfaceClass"):$(cat "$interface/bInterfaceSubClass"):$(cat "$interface/bInterfaceProtocol")" = ff:ff:ff ] || continue
        [ ! -L "$interface/driver" ] || continue
        /usr/libexec/muos-run-bounded 12 /bin/sh -c 'printf "%s\n" "$1" > /sys/bus/usb/drivers_probe' probe "${interface##*/}" || { echo 'C07: Wi-Fi interface reprobe failed'; exit 1; }
        echo "USB_WIFI_REPROBE=${interface##*/}"
    done
fi
if [ "$reset_done" = 0 ]; then
    echo "USB_MODE_BEFORE=0bda:$origin USB_MODE_AFTER=0bda:c820 SWITCH=standard-eject"
else
    echo "USB_MODE_BEFORE=0bda:$origin USB_MODE_AFTER=0bda:c820 SWITCH=port-reset EJECT=$eject_done"
fi
