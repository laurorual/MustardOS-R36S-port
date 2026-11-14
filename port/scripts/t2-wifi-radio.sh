#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M4c): the menu's Wi-Fi toggle backend (S02network.sh radio on|off,
# settings/network/radio). Runs detached on the device (SSH drops while the
# radio is off) and logs to p3 MUOS/log/t2-wifi-radio.log:
#   1. on: adapter marker present, radio up
#   2. off: radio down, 8821cu unloaded, idle; current draw on vs off
#      (30 samples each, same load)
#   3. sleep/wake (RTC, 15 s) with the radio off: it stays off (idle)
#   4. software unplug + USB rebind with the radio off: marker gone while
#      unplugged, back after; hotplug ignores the add; radio stays off
#   5. on: Wi-Fi back (address), toggle file 1
# The original setting is restored at the end (and the radio comes back on
# whatever happens: a 6 min guard in the detached script).
set -u
cd "$(dirname "$0")" || exit 1
dev=./device.sh
r() { "$dev" run "$@"; }
log=/userdata/MUOS/log/t2-wifi-radio.log
r 'cat > /run/t2-wifi-radio.sh' <<'EOF'
o=/userdata/MUOS/log/t2-wifi-radio.log N=/run/muos/network S=/opt/muos/script/init/async/S02network.sh
W=/usr/libexec/muos-network/worker R=/opt/muos/config/settings/network/radio
st() { echo "$(cut -d' ' -f1 /proc/uptime) $1 $($W status | head -n1) mod=$(grep -c '^8821cu ' /proc/modules) flags=[$(cd $N && ls radio ready idle adapter 2>/dev/null | tr '\n' ' ')] usb=[$(cat /sys/bus/usb/devices/1-1/idProduct 2>/dev/null)]" >> $o; }
amps() { s=0; i=0; while [ $i -lt 30 ]; do s=$((s + $(cat /sys/class/power_supply/battery/current_now) / 1000)); i=$((i + 1)); sleep 0.5; done; echo $((s / 30)); }
waitaddr() { i=0; while [ $i -lt "$1" ] && [ ! -s $N/address ]; do sleep 1; i=$((i + 1)); done; echo $i; }
: > $o; : > /run/muos-hotplug.log
before=$(cat $R 2>/dev/null || echo missing); echo "setting before: $before" >> $o
( sleep 360; [ -s $N/address ] || { echo "GUARD: radio on after 6 min" >> $o; $S radio on; } ) &
st on-start; echo "ma_on=$(amps)" >> $o
$S radio off; sleep 3; st off; echo "file=$(cat $R)" >> $o; echo "ma_off=$(amps)" >> $o
w0=$(grep -c woke /opt/muos/log/suspend.log 2>/dev/null); echo 15 > /run/muos/suspend-test-wake
/usr/libexec/muos-press power; sleep 25
i=0; while [ $i -lt 30 ] && [ "$(grep -c woke /opt/muos/log/suspend.log)" -le "$w0" ]; do sleep 1; i=$((i + 1)); done
rm -f /run/muos/suspend-test-wake; sleep 15; st after-wake
echo 1 > /sys/bus/usb/devices/1-1/remove; sleep 5; st unplugged
echo ff300000.usb > /sys/bus/platform/drivers/dwc2/unbind; sleep 2
echo ff300000.usb > /sys/bus/platform/drivers/dwc2/bind; sleep 8; st replugged
$S radio on; echo "back_after=$(waitaddr 90)s" >> $o; sleep 2; st on-again; echo "file=$(cat $R)" >> $o
[ "$before" = missing ] && rm -f $R || echo "$before" > $R
sed 's/^/HP /' /run/muos-hotplug.log >> $o; tail -n 6 $N/worker.log | sed 's/^/W /' >> $o
echo done >> $o; sync
EOF
r '(setsid sh /run/t2-wifi-radio.sh < /dev/null > /dev/null 2>&1 &)'
sleep 60
"$dev" wait 360 > /dev/null || { echo 'FAIL: no SSH 7 min after the start'; exit 1; }
n=0; until r "grep -qx done $log" 2>/dev/null || [ "$n" -ge 24 ]; do sleep 5; n=$((n + 1)); done
out=$(r "cat $log"); printf '%s\n' "$out"
ok=1
chk() { if printf '%s\n' "$out" | grep -q -- "$2"; then echo "ok   $1"; else echo "FAIL $1"; ok=0; fi; }
chk 'on: adapter marker, radio up' '^[0-9.]* on-start radio=up .*adapter=yes'
chk 'off: radio down, driver out, idle' '^[0-9.]* off radio=off .*setting=off .* mod=0 flags=\[adapter idle \]'
chk 'off: setting file 0' '^file=0'
chk 'wake: radio stays off' '^[0-9.]* after-wake radio=off .* mod=0 flags=\[adapter idle \]'
chk 'unplugged: marker gone' '^[0-9.]* unplugged .*adapter=no'
chk 'replugged: marker back, radio off' '^[0-9.]* replugged radio=off .*adapter=yes mod=0'
chk 'hotplug add ignored (radio off)' 'ignored (Wi-Fi off in the menu)'
chk 'on: Wi-Fi back' '^[0-9.]* on-again radio=up .*address=[0-9]'
chk 'on: setting file 1' '^file=1'
printf '%s\n' "$out" | grep -q GUARD && { echo 'FAIL guard fired'; ok=0; }
printf '%s\n' "$out" | sed -n 's/^ma_\(on\|off\)=/\1 /p' | paste -sd' ' | sed 's/^/current mA (negative = drawn): /'
if [ "$ok" = 1 ]; then echo PASS; else echo FAIL; exit 1; fi
