#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M4d T2: Connectivity's "Wi-Fi Network" row is closed while no Wi-Fi
# adapter is plugged in (frontend 0001), not only while the radio is off.
# Drives the real buttons (muos-press) from the launcher: Configuration →
# Connectivity → down to Wi-Fi Network (the launcher's focus must be on
# Explore, its 2x4 grid: Configuration = down, right); A must open muxnetwork with the
# dongle, stay in muxconnect after a software unplug (usb 1-1/remove), and
# open it again after the USB rebind. Runs detached on the device (the
# unplug drops SSH), log /run/t2-wifi-network-row.log.
set -eu
dev="$(dirname "$0")/device.sh"
log=/run/t2-wifi-network-row.log
r() { "$dev" run "$@"; }
r "cat > /run/t2-wnr.sh" <<'EOF2'
o=/run/t2-wifi-network-row.log; : > $o
P=/usr/libexec/muos-press
mod() { for p in /proc/[0-9]*; do case "$(readlink $p/exe)" in /opt/muos/frontend/muxfrontend) cat $p/comm;; esac; done | head -n1; }
st() { echo "$(cut -d' ' -f1 /proc/uptime) $1 mod=$(mod) adapter=$([ -e /run/muos/network/adapter ] && echo yes || echo no)" >> $o; }
waitaddr() { i=0; while [ $i -lt "$1" ] && ! ip -4 addr show wlan0 2>/dev/null | grep -q inet; do sleep 1; i=$((i + 1)); done; echo $i; }
st start
# M4e: stop at the first unexpected screen (blind presses once launched a
# game and overwrote its resume state).
need() { [ "$(mod)" = "$1" ] && return 0; echo "abort: expected $1, got $(mod)" >> $o
    $P b; sleep 2; $P b; sleep 2; echo done >> $o; sync; exit 1; }
$P a; sleep 3; st probe-explore; need muxplore; $P b; sleep 3
$P down; sleep 1; $P right; sleep 1; $P a; sleep 3; st config; need muxconfig
$P down; sleep 1; $P down; sleep 1; $P a; sleep 3; st connect; need muxconnect
$P down; sleep 1; $P a; sleep 3; st a-plugged
$P b; sleep 3; st back
echo 1 > /sys/bus/usb/devices/1-1/remove; sleep 4; st unplugged
$P a; sleep 3; st a-unplugged
$P up; sleep 1; $P a; sleep 2; $P left; sleep 2; $P down; sleep 1; st toggle-unavailable
echo ff300000.usb > /sys/bus/platform/drivers/dwc2/unbind; sleep 2
echo ff300000.usb > /sys/bus/platform/drivers/dwc2/bind; sleep 8; st replugged
$P a; sleep 3; st a-replugged
$P b; sleep 2; $P b; sleep 2; $P b; sleep 2; $P up; sleep 1; $P left; sleep 1; st home
echo "addr_after=$(waitaddr 90)s" >> $o
echo done >> $o; sync
EOF2
r '(setsid sh /run/t2-wnr.sh < /dev/null > /dev/null 2>&1 &)'
sleep 45
"$dev" wait 300 > /dev/null || { echo 'FAIL: no SSH 5 min after the start'; exit 1; }
n=0; until r "grep -qx done $log" 2>/dev/null || [ "$n" -ge 24 ]; do sleep 5; n=$((n + 1)); done
out=$(r "cat $log"); printf '%s\n' "$out"
ok=1
chk() { if printf '%s\n' "$out" | grep -q -- "$2"; then echo "ok   $1"; else echo "FAIL $1"; ok=0; fi; }
chk 'launcher focus on Explore'    ' probe-explore mod=muxplore'
chk 'Connectivity reached'          ' connect mod=muxconnect adapter=yes'
chk 'A with the dongle opens it'    ' a-plugged mod=muxnetwork adapter=yes'
chk 'adapter marker gone'           ' unplugged mod=muxconnect adapter=no'
chk 'A without the dongle blocked'  ' a-unplugged mod=muxconnect adapter=no'
chk 'toggle blocked (no adapter)'   ' toggle-unavailable mod=muxconnect adapter=no'
chk 'A after the replug opens it'   ' a-replugged mod=muxnetwork adapter=yes'
chk 'back home'                     ' home mod=muxlaunch'
[ "$ok" = 1 ] && echo PASS || { echo FAIL; exit 1; }
