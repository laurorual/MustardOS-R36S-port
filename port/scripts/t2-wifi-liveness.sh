#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M7): Wi-Fi liveness in muos-usb-watchdog (dead while "ready" ->
# dwc2 rebind -> Wi-Fi back through the hotplug path).
#   t2-wifi-liveness.sh c2h      a fake 8821cu C2H error line in the kernel
#                                log while connected: the S97 watchdog must
#                                rebind within ~60 s and Wi-Fi come back.
#   t2-wifi-liveness.sh silent   a second watchdog with test hooks (a frozen
#                                packet counter, a gateway that never
#                                answers, checks every 4 s, exit after the
#                                first rebind): it must rebind after two
#                                silent checks, Wi-Fi come back.
# SSH drops during the rebind: the device side runs detached and logs to
# /run; this waits for SSH and prints the timeline. PASS/FAIL at the end.
set -euo pipefail
dev=$(dirname "$0")/device.sh
mode=${1:?c2h|silent}
t0=$(date +%s)
case "$mode" in
c2h)
    "$dev" run 'n=$(grep -c "Wi-Fi dead" /opt/muos/log/usb-watchdog.log 2>/dev/null || :); echo "${n:-0}" > /run/t2-live.before
        (sleep 2; echo "RTW: ERROR c2h_handler_rtl8821c: [ERROR] C2H_ID(01) t2-injected" > /dev/kmsg) > /dev/null 2>&1 &
        echo injected' ;;
silent)
    "$dev" run 'n=$(grep -c "Wi-Fi dead" /opt/muos/log/usb-watchdog.log 2>/dev/null || :); echo "${n:-0}" > /run/t2-live.before
        echo 1 > /run/t2-live.rx
        MUOS_USB_WATCH_ONCE=1 MUOS_WIFI_LIVE_PERIOD=2 MUOS_WIFI_LIVE_RX=/run/t2-live.rx MUOS_WIFI_LIVE_GW=192.0.2.1 \
            setsid /usr/libexec/muos-usb-watchdog > /run/t2-live.log 2>&1 < /dev/null &
        echo started' ;;
*) sed -n '4,15p' "$0"; exit 2 ;;
esac
# The check runs every 60 s (c2h) or 4 s (silent): wait until SSH drops
# (the rebind), at most 100 s, then until it is back.
n=0
while [ "$n" -lt 20 ] && timeout 8 "$dev" run true > /dev/null 2>&1; do sleep 5; n=$((n + 1)); done
"$dev" wait 240 > /dev/null
back=$(( $(date +%s) - t0 ))
out=$("$dev" run 'before=$(cat /run/t2-live.before); log=/opt/muos/log/usb-watchdog.log
    [ ! -e /run/t2-live.log ] || { log=/run/t2-live.log; before=0; }
    grep "Wi-Fi dead" "$log" | tail -n 1
    echo "rebinds=$(( $(grep -c "Wi-Fi dead" "$log") - before ))"
    tail -n 3 /run/muos/network/private/action.log 2>/dev/null | cut -c1-120
    /usr/libexec/muos-network/worker status | head -n 1
    rm -f /run/t2-live.log /run/t2-live.rx /run/t2-live.before')
printf '%s\nSSH back after %s s\n' "$out" "$back"
if printf '%s\n' "$out" | grep -q '^rebinds=[1-9]' && printf '%s\n' "$out" | grep -q 'address=[0-9]'; then
    echo PASS
else
    echo FAIL; exit 1
fi
