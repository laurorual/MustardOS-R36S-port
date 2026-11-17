#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# T1 (host, also runs under the device's busybox sh): muos-lowbattery against a fake sysfs/run/config tree.
# Cases (M4d): the cut-off at CRITICAL % judged on the current-corrected
# voltage (V + I x 200 mOhm < 3550 mV), the warning overlay, charging.
set -u
repo=$(cd "$(dirname "$0")/../.." && pwd)
lb=$repo/port/device/rk-r35s-p0/rootfs/usr/libexec/muos-lowbattery
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
ok=1
case_() { # NAME CAP CHARGING MV MA EXPECT(off|ignored|warn|none)
    rm -rf "$t/r" "$t/s" "$t/c"; mkdir -p "$t/r/battery" "$t/s" "$t/c/settings/power"
    echo "$2" > "$t/r/battery/capacity"; echo "$3" > "$t/r/battery/charging"
    echo $(($4 * 1000)) > "$t/s/voltage_now"; echo $(($5 * 1000)) > "$t/s/current_now"
    echo 25 > "$t/c/settings/power/low_battery"
    # No timeout(1) in the device's busybox: run for 2 s, then kill.
    MUOS_RUN_DIR=$t/r MUOS_BATTERY_SYSFS=$t/s MUOS_CONFIG_DIR=$t/c MUOS_BATTERY_INTERVAL=0.05 \
        MUOS_BATTERY_EMPTY_CMD="touch $t/r/off" sh "$lb" > "$t/out" 2>&1 &
    pid=$!; sleep 2; kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
    out=$(cat "$t/out")
    got=none
    [ -e "$t/r/overlay.battery" ] && got=warn
    printf '%s\n' "$out" | grep -q 'ignored' && got=ignored
    [ -e "$t/r/off" ] && got=off
    if [ "$got" = "$6" ]; then echo "ok   $1 ($got)"; else echo "FAIL $1: got $got, want $6"; printf '%s\n' "$out" | sed 's/^/     /'; ok=0; fi
}
case_ 'CTR end: 1%, 3352 mV at 729 mA (corrected 3497)'  1 0 3352 -729 off
case_ 'idle end: 1%, 3380 mV at 390 mA (corrected 3458)' 1 0 3380 -390 off
case_ 'gauge error: 1% at 3900 mV'                        1 0 3900 -700 ignored
case_ 'game load at ~15%: 1%, 3420 mV at 750 mA'         1 0 3420 -750 ignored
case_ '2%: warning only'                                  2 0 3360 -700 warn
case_ '24%: warning only'                                24 0 3600 -400 warn
case_ 'charging at 1%'                                    1 1 3700 1200 none
case_ 'no current reading: plain voltage'                 1 0 3400 0 off
[ "$ok" = 1 ] && echo PASS || { echo FAIL; exit 1; }
