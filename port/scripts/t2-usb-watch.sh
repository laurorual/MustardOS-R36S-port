#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T3 diagnostic (M4e.1, developer images only, never shipped): the second
# dongle unplug of the M4e T3 left no kernel event at all (no "USB
# disconnect" until a port reset 15 s later). While the user replugs the
# dongle, SSH is gone, so a device-side loop logs once a second to /run:
#   uptime, dwc2 HPRT0 (0xff300440: bit 0 connected, 1 connect detected,
#   2 enabled, 12 power), GINTSTS (0xff300014), the usb 1-1 id/devnum,
#   wlan0 operstate/carrier, rx packets, wpa_state, the hotplug log size
# and copies it to p3 MUOS/log/usb-watch.log every 30 s and at stop.
#   t2-usb-watch.sh start | stop | report   (report = stop + pull + show)
# Reads only (devmem read, sysfs, wpa_cli status); about 1 % CPU.
set -u
cd "$(dirname "$0")" || exit 1
dev=./device.sh
logs=$(cd ../.. && pwd)/build/logs; mkdir -p "$logs"
out=/userdata/MUOS/log/usb-watch.log
loop='#!/bin/sh
run=/run/usb-watch.log out='"$out"'
: > "$run"; i=0
while :; do
    t=$(cut -d" " -f1 /proc/uptime)
    hprt=$(devmem 0xff300440 32 2>/dev/null) gint=$(devmem 0xff300014 32 2>/dev/null)
    d=/sys/bus/usb/devices/1-1
    id=$(cat $d/idProduct 2>/dev/null || echo -):$(cat $d/devnum 2>/dev/null || echo -)
    n=/sys/class/net/wlan0
    op=$(cat $n/operstate 2>/dev/null || echo -)/$(cat $n/carrier 2>/dev/null || echo -)
    rx=$(cat $n/statistics/rx_packets 2>/dev/null || echo -)
    ws=$(wpa_cli -p /run/wpa_supplicant -i wlan0 status 2>/dev/null | sed -n "s/^wpa_state=//p")
    hp=$(wc -l < /run/muos-hotplug.log 2>/dev/null || echo 0)
    echo "$t $hprt $gint $id $op $rx ${ws:--} $hp" >> "$run"
    i=$((i+1)); [ $((i % 30)) -ne 0 ] || cp "$run" "$out"
    sleep 1
done'
case "${1:-}" in
 start)
    printf '%s\n' "$loop" | "$dev" run 'cat > /run/usb-watch.sh; chmod 755 /run/usb-watch.sh
        [ ! -s /run/usb-watch.pid ] || kill "$(cat /run/usb-watch.pid)" 2>/dev/null
        setsid /run/usb-watch.sh < /dev/null > /dev/null 2>&1 & echo $! > /run/usb-watch.pid
        sleep 2; tail -n 1 /run/usb-watch.log' ;;
 stop|report)
    "$dev" run '[ -s /run/usb-watch.pid ] && kill "$(cat /run/usb-watch.pid)" 2>/dev/null; rm -f /run/usb-watch.pid
        cp /run/usb-watch.log '"$out"' 2>/dev/null; sync; wc -l < '"$out"
    [ "$1" = report ] || exit 0
    f=$logs/usb-watch-$(date +%Y%m%d-%H%M).txt
    "$dev" run 'echo "# uptime hprt0 gintsts id:devnum oper/carrier rx wpa hotplug-lines"
        uniq -f 1 '"$out"' | head -n 400; echo "== hotplug"; cat /run/muos-hotplug.log
        echo "== worker"; tail -n 40 /run/muos/network/worker.log
        echo "== kernel"; dmesg | grep -E "usb 1-1|USB disconnect|New USB device found|OnDeAuth|rtw_ndev|usb_submit_urb" | tail -n 60' > "$f"
    echo "$f"; grep -c . "$f" ;;
 *) echo 'Usage: t2-usb-watch.sh start|stop|report' >&2; exit 2 ;;
esac
