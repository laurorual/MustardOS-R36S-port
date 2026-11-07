#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
state=/run/muos/c07
private=/var/lib/muos-network
mkdir -p "$state"
secure_file() {
    [ -f "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u:%g:%a' "$1")" = 0:0:600 ]
}
stop_one() {
    file=$state/$1.pid
    [ -f "$file" ] || return 0
    pid=$(cat "$file")
    case "$pid" in ''|*[!0-9]*) return 1 ;; esac
    [ "$pid" -gt 1 ] || return 1
    if [ -d "/proc/$pid" ]; then
        [ "$(readlink "/proc/$pid/exe")" = "$2" ] || return 1
        kill -TERM "$pid"
        n=0
        while kill -0 "$pid" 2>/dev/null && [ "$n" -lt 50 ]; do sleep 0.1; n=$((n+1)); done
        ! kill -0 "$pid" 2>/dev/null || return 1
    fi
    rm -f "$file"
}
status() {
    [ -f "$state/ready" ] && [ -f "$state/address" ] || return 1
    for pair in 'dropbear /usr/sbin/dropbear' 'wpa /usr/sbin/wpa_supplicant' 'dhcp /bin/busybox'; do
        set -- $pair
        pid=$(cat "$state/$1.pid") || return 1
        case "$pid" in ''|*[!0-9]*) return 1 ;; esac
        [ "$(readlink "/proc/$pid/exe")" = "$2" ] && kill -0 "$pid" || return 1
    done
}
case "${1:-}" in
 stop)
    rm -f "$state/ready"
    rc=0
    stop_one dropbear /usr/sbin/dropbear || rc=1
    stop_one dhcp /bin/busybox || rc=1
    stop_one wpa /usr/sbin/wpa_supplicant || rc=1
    rm -f "$state/address"
    exit "$rc" ;;
 status) status; exit $? ;;
 start|recover) action=$1 ;;
 *) exit 2 ;;
esac
[ ! -e "$state/ready" ] || exit 1
if [ "$action" = recover ]; then
    # SeedRNG was stopped after the failed boot. Query current kernel readiness;
    # never load/credit a saved seed again in the same boot or create a key on RO.
    [ -f /run/muos/entropy/stopped ] || exit 1
    findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || exit 1
    secure_file "$private/dropbear_ed25519_host_key" || exit 1
    /usr/libexec/muos-run-bounded 3 /usr/libexec/muos-rng-ready 0 || exit 1
else
    [ -f /run/muos/entropy/ready ] || { echo 'C07: RNG readiness missing'; exit 1; }
fi
echo 'NETWORK_STEP=private-files'
[ ! -L "$private" ] && [ "$(stat -c '%u:%g:%a' "$private")" = 0:0:700 ] || exit 1
secure_file "$private/network.conf" || exit 1
umask 077
mkdir -p "$state/private" "$state/auth" "$state/wpa"
chmod 700 "$state/private" "$state/auth" "$state/wpa"
cp "$private/network.conf" "$state/private/network.conf"
cp /etc/muos-network-authorized_key "$state/auth/authorized_keys"
chmod 600 "$state/auth/authorized_keys"
# This key never leaves the device; only its public fingerprint is reported.
echo 'NETWORK_STEP=host-key'
if [ ! -e "$private/dropbear_ed25519_host_key" ]; then
    [ ! -L "$private/dropbear_ed25519_host_key" ] || exit 1
    dropbearkey -t ed25519 -f "$private/dropbear_ed25519_host_key.tmp" > "$state/private/keygen.log" 2>&1
    mv "$private/dropbear_ed25519_host_key.tmp" "$private/dropbear_ed25519_host_key"
fi
secure_file "$private/dropbear_ed25519_host_key" || exit 1
dropbearkey -y -f "$private/dropbear_ed25519_host_key" > "$state/private/host-public.txt" 2>&1
awk '$1=="Fingerprint:" {print $2}' "$state/private/host-public.txt" > "$state/fingerprint"
case "$(cat "$state/fingerprint")" in SHA256:*) ;; *) exit 1 ;; esac
echo 'NETWORK_STEP=driver'
modprobe 8821cu
count=0
while [ "$count" -lt 100 ]; do
    found=
    for path in /sys/class/net/*; do
        [ "$(basename "$(readlink -f "$path/device/driver/module")")" = 8821cu ] || continue
        [ -z "$found" ] || { echo 'C07: multiple dongle interfaces'; exit 1; }
        found=${path##*/}
    done
    [ -z "$found" ] || break
    sleep 0.1; count=$((count+1))
done
[ -n "$found" ] || {
    echo 'C07: interface missing'
    for usb in /sys/bus/usb/devices/*; do
        [ -r "$usb/idVendor" ] && [ -r "$usb/idProduct" ] || continue
        [ "$(cat "$usb/idVendor"):$(cat "$usb/idProduct")" = 0bda:c820 ] || continue
        for interface in "$usb":*; do
            [ -r "$interface/bInterfaceClass" ] || continue
            driver_name=none
            [ ! -L "$interface/driver" ] || driver_name=$(basename "$(readlink -f "$interface/driver")")
            echo "USB_INTERFACE=${interface##*/} CLASS=$(cat "$interface/bInterfaceClass") DRIVER=$driver_name"
        done
    done
    for net in /sys/class/net/*; do
        case "${net##*/}" in lo|wlan[0-9]|p2p[0-9]) public_name=${net##*/} ;; *) public_name=other ;; esac
        echo "NET_INTERFACE=$public_name MODULE=$(basename "$(readlink -f "$net/device/driver/module")")"
    done
    # Only fixed labels and counts leave the kernel ring buffer. Raw lines may
    # contain MAC/SSID and are deliberately never copied to the public report.
    dmesg | awk '
      /rtw_usb_primary_adapter_init Failed/ {primary++}
      /alloc usb_vendor_req_buf failed/ {alloc++}
      /rtw_usb_if1_init, failed/ {ifinit++}
      /rtw_drv_add_iface failed/ {addiface++}
      /rtw_hal_power_on.*fail/ {power++}
      /rtw_hal_init.*fail/ {hal++}
      /usb_read_port.*fail|usb_write_port.*fail|usbctrl_vendorreq.*(fail|status)/ {io++}
      /error -71|error -110|error -32|error -19/ {usb++}
      END {printf "DRIVER_FAILURE_COUNTS primary=%d alloc=%d ifinit=%d addiface=%d power=%d hal=%d io=%d usb=%d\n",primary,alloc,ifinit,addiface,power,hal,io,usb}'
    exit 1
}
printf '%s\n' "$found" > "$state/interface"
for rf in /sys/class/rfkill/rfkill*; do
    [ -r "$rf/type" ] || continue
    [ "$(cat "$rf/type")" != wlan ] || printf '0\n' > "$rf/soft"
done
ifconfig "$found" up
echo 'NETWORK_STEP=association-dhcp'
wpa_supplicant -i "$found" -D nl80211,wext -c "$state/private/network.conf" -C "$state/wpa" \
    > "$state/private/wpa.log" 2>&1 &
printf '%s\n' "$!" > "$state/wpa.pid"
udhcpc -f -i "$found" -p "$state/dhcp.pid" -s /usr/libexec/muos-c07-dhcp -t 10 -T 3 -A 5 \
    > "$state/private/dhcp.log" 2>&1 &
printf '%s\n' "$!" > "$state/dhcp.pid"
count=0
while [ "$count" -lt 90 ]; do
    [ ! -r "$state/address" ] || break
    kill -0 "$(cat "$state/wpa.pid")" && kill -0 "$(cat "$state/dhcp.pid")" || exit 1
    sleep 1; count=$((count+1))
done
[ -r "$state/address" ] || { echo 'C07: no DHCP lease'; exit 1; }
wpa_cli -p "$state/wpa" -i "$found" status | awk -F= '$1=="wpa_state" {print $2}' > "$state/association"
[ "$(cat "$state/association")" = COMPLETED ] || { echo 'C07: association incomplete'; exit 1; }
echo 'NETWORK_STEP=ssh-server'
dropbear -F -E -s -j -k -m -r "$private/dropbear_ed25519_host_key" -D "$state/auth" \
    -p 0.0.0.0:2222 -l "$found" -P "$state/dropbear.pid" -K 30 \
    > "$state/private/dropbear.log" 2>&1 &
printf '%s\n' "$!" > "$state/dropbear.pid"
sleep 1
touch "$state/ready"
status
echo 'C07: association, DHCP and SSH process ready; client authentication still untested'
