#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M4c): Wi-Fi bring-up after a real sleep, timed. Each cycle arms an RTC
# wake (/run/muos/suspend-test-wake), starts a detached recorder (state
# changes of the dongle, the worker flags, wpa_supplicant and the address,
# 0.2 s steps, /proc/uptime), presses Power (muos-press: the real sleep
# path) and waits for SSH. Works in the menu or in a running game.
#   t2-wake-wifi.sh [CYCLES] [SETTLE_MS]
# SETTLE_MS (optional) sets the T2 hook /run/muos/network-settle-ms (the
# worker's CD-ROM settle) for the run and removes it afterwards. A cycle
# fails if Wi-Fi isn't back 60 s after the wake: the recorder (on the
# device, so it works without SSH) then drops the settle override and
# sleeps once more, which cuts the dongle's power (it returns in CD-ROM
# mode, as after a replug) and brings it up with the default settle.
# Output: per cycle "wake->address N s" and the timeline; logs on p3
# MUOS/log/t2-wake-wifi.log, host build/logs/m4c/t2-wake-wifi.log.
set -u
cd "$(dirname "$0")" || exit 1
dev=./device.sh
r() { "$dev" run "$@"; }
cycles=${1:-1} settle=${2:-}
out=$(cd ../.. && pwd)/build/logs/m4c; mkdir -p "$out"
r 'cat > /run/t2-wake-rec.sh' <<'EOF'
o=/userdata/MUOS/log/t2-wake-wifi.log N=/run/muos/network last=
t0=$(cut -d' ' -f1 /proc/uptime); end=${t0%.*}; end=$((end + 120))
echo "cycle start $t0" >> $o
while :; do
    u=$(cut -d' ' -f1 /proc/uptime); [ "${u%.*}" -lt "$end" ] || break
    p=$(cat /sys/bus/usb/devices/1-1/idProduct 2>/dev/null)
    f=$(cd $N && ls radio usb-done ready idle freq-hint 2>/dev/null | tr '\n' ' ')
    w=$(wpa_cli -p /run/wpa_supplicant -i "$(cat $N/interface 2>/dev/null || echo wlan0)" status 2>/dev/null | sed -n 's/^wpa_state=//p')
    a=$(cat $N/address 2>/dev/null)
    cur="usb=[$p] flags=[$f] wpa=$w addr=$a"
    [ "$cur" = "$last" ] || { echo "$u $cur" >> $o; last=$cur; }
    case "$f" in *ready*) [ -n "$a" ] && [ -n "$woke" ] && break ;; esac
    if [ -z "$woke" ] && [ "$(grep -c woke /opt/muos/log/suspend.log 2>/dev/null)" -gt "$w0" ]; then
        woke=${u%.*}; end=$((woke + 150))
    fi
    if [ -n "$woke" ] && [ -z "$a" ] && [ -z "$rescue" ] && [ "${u%.*}" -ge $((woke + 60)) ]; then
        rescue=1; echo "$u DEAF: no address 60 s after the wake: recovery sleep (power cut, default settle)" >> $o
        rm -f /run/muos/network-settle-ms; echo 15 > /run/muos/suspend-test-wake; /usr/libexec/muos-press power
    fi
    sleep 0.2
done
grep woke /opt/muos/log/suspend.log | tail -n1 | sed 's/^/suspend: /' >> $o
tail -n 3 $N/worker.log | sed 's/^/worker: /' >> $o
echo "cycle done" >> $o; sync
EOF
[ -z "$settle" ] || r "echo $settle > /run/muos/network-settle-ms"
r ': > /userdata/MUOS/log/t2-wake-wifi.log'
rc=0
for i in $(seq 1 "$cycles"); do
    r 'echo 15 > /run/muos/suspend-test-wake; w0=$(grep -c woke /opt/muos/log/suspend.log 2>/dev/null || echo 0)
       (export w0 woke= rescue=; setsid sh /run/t2-wake-rec.sh < /dev/null > /dev/null 2>&1 &); sleep 2; /usr/libexec/muos-press power'
    sleep 20
    if ! "$dev" wait 300 > /dev/null 2>&1; then echo "FAIL cycle $i: no SSH 5 min after the wake (recovery sleep failed?)"; rc=1; break; fi
    n=0; until [ "$(r 'grep -c "cycle done" /userdata/MUOS/log/t2-wake-wifi.log')" -ge "$i" ] || [ "$n" -ge 30 ]; do sleep 4; n=$((n + 1)); done
    t=$(r 'cat /userdata/MUOS/log/t2-wake-wifi.log' | awk -v c="$i" '/^cycle start/ { k++ } k == c')
    woke=$(sed -n 's/^suspend: \([0-9.]*\) woke.*/\1/p' <<< "$t" | tail -n1)
    addr=$(awk -v w="$woke" '$1 + 0 > w + 0 && / addr=[0-9]/ { print $1; exit }' <<< "$t")
    if [ -n "$woke" ] && [ -n "$addr" ]; then
        echo "cycle $i: wake->address $(awk -v a="$addr" -v w="$woke" 'BEGIN { printf "%.1f", a - w }') s"
    else
        echo "cycle $i: no address after the wake"; rc=1
    fi
    grep -q DEAF <<< "$t" && { echo "FAIL cycle $i: deaf dongle (recovered: $(grep -c ' addr=[0-9]' <<< "$t") address lines)"; rc=1; break; }
    sleep 5
done
[ -z "$settle" ] || r 'rm -f /run/muos/network-settle-ms'
r 'rm -f /run/muos/suspend-test-wake; cat /userdata/MUOS/log/t2-wake-wifi.log' > "$out/t2-wake-wifi.log" 2>&1
echo "log: $out/t2-wake-wifi.log"
exit "$rc"
