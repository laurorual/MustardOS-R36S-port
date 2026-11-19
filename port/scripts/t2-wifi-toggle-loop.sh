#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M6): repeated Wi-Fi radio off/on through the menu's backend
# (S02network.sh radio off|on), as in M5 T3 item 11, where one "on" left the
# 8821cu in its C2H firmware error loop until a second toggle. Runs
# detached on the device (SSH drops while the radio is off) and logs to p3
# MUOS/log/t2-wifi-toggle.log: per cycle the seconds to an address and
# whether the worker reset the dongle on C2H errors (fw_broken, M6).
#   t2-wifi-toggle-loop.sh [CYCLES]   default 8; PASS = every cycle got an
#                                     address within 150 s
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
dev=$repo/port/scripts/device.sh
cycles=${1:-8}
case "$cycles" in ''|*[!0-9]*) echo "cycles: a number" >&2; exit 2 ;; esac
"$dev" run "cycles=$cycles"'
o=/userdata/MUOS/log/t2-wifi-toggle.log N=/run/muos/network S=/opt/muos/script/init/async/S02network.sh
: > $o
setsid sh -c "
    i=1
    while [ \$i -le $cycles ]; do
        $S radio off; sleep 3
        start=\$(cut -d. -f1 /proc/uptime); $S radio on
        n=0; while [ \$n -lt 150 ] && [ ! -s $N/address ]; do sleep 1; n=\$((n+1)); done
        [ -s $N/address ] && r=ok || r=FAIL
        echo \"cycle \$i \$r \${n}s c2h_resets=\$(grep -c \"driver firmware errors\" $N/worker.log)\" >> $o
        [ \$r = ok ] || $S radio on
        sleep 5; i=\$((i+1))
    done
    echo done >> $o" > /dev/null 2>&1 < /dev/null &'
# Each cycle takes 20-40 s; SSH answers again between cycles.
sleep $((cycles * 25))
while :; do
    out=$("$dev" run 'cat /userdata/MUOS/log/t2-wifi-toggle.log' 2>/dev/null) || out=
    case "$out" in *done*) break ;; esac
    sleep 20
done
printf '%s\n' "$out"
"$dev" run 'grep -E "attempt|firmware|reassociate|ready|vanished" /run/muos/network/worker.log | tail -n 40'
if printf '%s\n' "$out" | grep -q ' FAIL '; then echo FAIL; exit 1; fi
echo PASS
