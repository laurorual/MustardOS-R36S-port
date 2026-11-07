#!/bin/sh
# SPDX-License-Identifier: MIT
# One physical dongle reconnect after a failed C07 boot; never a reset loop.
set -eu
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
state=/run/muos/c07
[ "$(cat /etc/muos-network-diagnostic)" = MUOS-R35S-NETWORK-P4-C07 ] || exit 64
[ "$(readlink /proc/1/exe)" = /bin/busybox ] || exit 64
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ] || exit 64
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || exit 64
[ -f /run/muos/entropy/stopped ] && [ ! -e "$state/ready" ] || exit 64
/usr/libexec/muos-run-bounded 3 /usr/libexec/muos-rng-ready 0 || exit 64
. /usr/libexec/muos-diag-card-guard
boot=$(diag_card /sys) || exit 64
root=${boot%p1}p2
[ "$(findmnt -rn -o MAJ:MIN /)" = "$(cat /sys/class/block/${root##*/}/dev)" ] || exit 64
key=/var/lib/muos-network/dropbear_ed25519_host_key
[ -f "$key" ] && [ ! -L "$key" ] && [ "$(stat -c '%u:%g:%a' "$key")" = 0:0:600 ] || exit 64
# Reentry is refused; no repeated rescans/resets while someone uses SSH.
mkdir "$state/recovery" || exit 64
/usr/libexec/muos-c07-network stop || exit 1
screen() { printf '\033[37;40m\033[2J\033[H%s\n' "$1" > /dev/tty0; }
dongle_present() {
    for path in /sys/bus/usb/devices/*; do
        [ -r "$path/idVendor" ] && [ -r "$path/idProduct" ] || continue
        case "$(cat "$path/idVendor"):$(cat "$path/idProduct")" in
            0bda:1a2b|0bda:c820) return 0 ;;
        esac
    done
    return 1
}
screen 'muOS C07: USB RECONNECT NEEDED
Unplug the Wi-Fi dongle. Wait two seconds.
Reconnect it, then wait for SSH READY.
Do not change SD cards. Root read-only.'
# Observe actual absence for a full second, then a new supported device.
absent=0; ticks=0
while [ "$ticks" -lt 900 ] && [ "$absent" -lt 10 ]; do
    if dongle_present; then absent=0; else absent=$((absent+1)); fi
    sleep 0.1; ticks=$((ticks+1))
done
[ "$absent" -eq 10 ] || { echo 'RECOVERY=removal-timeout'; exit 1; }
echo 'RECOVERY=physical-removal-observed'
ticks=0
while ! dongle_present && [ "$ticks" -lt 1200 ]; do sleep 0.1; ticks=$((ticks+1)); done
[ "$ticks" -lt 1200 ] || { echo 'RECOVERY=insertion-timeout'; exit 1; }
/usr/libexec/muos-run-bounded 120 /usr/libexec/muos-c07-usb-mode || exit 1
/usr/libexec/muos-run-bounded 120 /usr/libexec/muos-c07-network recover || exit 1
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || exit 1
echo 'RECOVERY=ssh-process-ready ROOT_RO=1'
