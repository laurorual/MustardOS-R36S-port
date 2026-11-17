#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M4f, attended: PMIC writes): automated dongle unplug/plug by cutting
# the RK817 BOOST (5 V of the USB port): POWER_EN_REG(3) 0xB4, enable bit 1
# with write mask bit 5 (0x20 = BOOST off, 0x22 = on; no other output
# changes). Counts the port events the dwc2 driver misses (M4e/M4e.1 T3:
# HPRT0 changed, no kernel event).
#   t2-usb-cycle.sh run [CYCLES]   start detached on the device (SSH drops
#                                  with every cycle), wait, print the result
#   t2-usb-cycle.sh result         the last run's log
# Per cycle: BOOST off for 3/10/30 s (rotating), on, then connected for
# 10/30/60 s. A transition counts as seen when usb 1-1 vanishes (off) or
# appears (on) within 10 s; Wi-Fi must get an address within 45 s. A missed
# plug is logged with HPRT0 and recovered by one more BOOST cycle. The BOOST
# is switched on again on exit (trap) whatever happens.
set -u
cd "$(dirname "$0")" || exit 1
dev=./device.sh
logs=$(cd ../.. && pwd)/build/logs; mkdir -p "$logs"
out=/userdata/MUOS/log/usb-cycle.log
cycle='#!/bin/sh
n=${1:-12} out='"$out"'
boost() { i2cset -f -y 0 0x20 0xb4 "$1"; }
trap "boost 0x22" EXIT INT TERM
up() { [ -e /sys/bus/usb/devices/1-1/idVendor ]; }
hprt() { devmem 0xff300440 32; }
now() { cut -d" " -f1 /proc/uptime; }
waitfor() { # want(0|1) seconds
    i=0; while [ "$i" -lt $(($2 * 10)) ]; do
        if [ "$1" = 1 ]; then up && return 0; else up || return 0; fi
        sleep 0.1; i=$((i + 1)); done; return 1; }
log() { echo "$(now) $*" >> "$out"; sync; }
: > "$out"; log "start cycles=$n dtb_dr_mode=$(cat /proc/device-tree/usb@ff300000/dr_mode)"
miss_off=0 miss_on=0 noip=0 c=1
while [ "$c" -le "$n" ]; do
    case $((c % 3)) in 1) toff=3 ton=10 ;; 2) toff=10 ton=30 ;; 0) toff=30 ton=60 ;; esac
    boost 0x20
    if waitfor 0 10; then d=seen; else d=MISSED; miss_off=$((miss_off + 1)); fi
    log "c$c off: disconnect $d hprt=$(hprt)"
    sleep "$toff"
    boost 0x22
    if waitfor 1 10; then a=seen; else a=MISSED; miss_on=$((miss_on + 1)); fi
    log "c$c on after ${toff}s: connect $a hprt=$(hprt) id=$(cat /sys/bus/usb/devices/1-1/idProduct 2>/dev/null)"
    if [ "$a" = MISSED ]; then
        sleep 10; log "c$c still $(up && echo up || echo absent) hprt=$(hprt): recovery cycle"
        boost 0x20; sleep 3; boost 0x22; waitfor 1 10 || log "c$c recovery: no device"
    fi
    i=0; while [ "$i" -lt 45 ] && [ ! -s /run/muos/network/address ]; do sleep 1; i=$((i + 1)); done
    if [ -s /run/muos/network/address ]; then log "c$c address after ${i}s"; else log "c$c NO ADDRESS"; noip=$((noip + 1)); fi
    sleep "$ton"; c=$((c + 1))
done
log "done missed_disconnect=$miss_off missed_connect=$miss_on no_address=$noip"'
case "${1:-}" in
 run)
    n=${2:-12}
    printf '%s\n' "$cycle" | "$dev" run 'cat > /run/usb-cycle.sh; chmod 755 /run/usb-cycle.sh
        setsid /run/usb-cycle.sh '"$n"' < /dev/null > /run/usb-cycle.err 2>&1 & echo started'
    # ~(10 + 14 + 45) s per cycle at worst; poll over SSH when Wi-Fi is up.
    deadline=$(( $(date +%s) + n * 150 + 120 ))
    while [ "$(date +%s)" -lt "$deadline" ]; do
        sleep 30
        r=$(timeout 15 "$dev" run "tail -n 1 $out" 2>/dev/null) || continue
        case "$r" in *' done '*) break ;; esac
    done
    f=$logs/usb-cycle-$(date +%Y%m%d-%H%M).txt
    timeout 30 "$dev" run "cat $out; i2cget -f -y 0 0x20 0xb4" > "$f" 2>&1
    echo "$f"; grep -E 'MISSED|NO ADDRESS|done|start|still|recovery' "$f"; tail -n 1 "$f" ;;
 result) "$dev" run "cat $out" ;;
 *) echo 'Usage: t2-usb-cycle.sh run [CYCLES] | result' >&2; exit 2 ;;
esac
