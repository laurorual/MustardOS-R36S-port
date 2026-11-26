#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M10 T2: the network worker's dongle detection (wifi_module) against fake
# USB devices with real IDs, resolved by the device's own modprobe -R and
# modules.dep. Read-only on the device (fake sysfs trees under /tmp).
#   t2-wifi-detect.sh [WORKER]   default: the repo's worker
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
worker=${1:-$repo/port/device/rk-r35s-p0/rootfs/usr/libexec/muos-network/worker}
dev=$repo/port/scripts/device.sh
# vid pid interface-class expected-module ("-" = not a Wi-Fi dongle)
cases='0bda c820 ff 8821cu
0bda 8176 ff 8192cu
0bda 8179 ff 8188eu
0bda b812 ff 88x2bu
0bda 8812 ff rtl8812au
0bda b720 ff 8723bu
148f 7601 ff mt7601u
148f 5370 ff rt2800usb
148f 2573 ff rt73usb
0bda 8187 ff rtl8187
0bda 8171 ff r8712u
0bda 0724 ff r8723au
0bda 0129 ff -
0781 5567 08 -
045e 028e ff -'
"$dev" run 'mkdir -p /tmp/t2-wifi-detect' < /dev/null
"$dev" run 'cat > /tmp/t2-wifi-detect/worker' < "$worker"
"$dev" run "cases='$cases' sh -s" << 'EOF'
set -u
t=/tmp/t2-wifi-detect
# the detection functions only (from wifi_pref= to the end of unload())
awk '/^wifi_pref=/ { f = 1 } f { print } f && /^unload\(\)/ { u = 1 } u && /^}/ { exit }' $t/worker > $t/fn.sh
state=$t/state; rm -rf "$state" "$t/sys"; mkdir -p "$state"
. $t/fn.sh
wifi_mods > /dev/null
printf '%s\n' "$cases" | while read -r v p c want; do
    d=$t/sys/9-$v$p; i=$d/9-$v$p:1.0
    mkdir -p "$i"; C=$(echo "$c" | tr a-f A-F)
    printf 'usb:v%sp%sd0000dc00dsc00dp00ic%sisc%sip%sin00\n' \
        "$(echo "$v" | tr a-f A-F)" "$(echo "$p" | tr a-f A-F)" "$C" "$C" "$C" > "$i/modalias"
    got=$(wifi_module "$d") || got=-
    if [ "$got" = "$want" ]; then r=ok; else r=FAIL; fi
    echo "$r $v:$p -> $got (want $want)"
done > $t/result
cat $t/result
echo "wifi modules known: $(wc -l < "$state/wifi-mods")"
# the plugged-in dongle through the real sysfs
echo "real dongle: $(dongle) module $(wifi_module "$(dongle)") iface $(wifi_iface)"
! grep -q '^FAIL' $t/result
EOF
