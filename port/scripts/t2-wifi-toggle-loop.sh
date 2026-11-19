#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M6): repeated Wi-Fi radio off/on through the menu's backend
# (S02network.sh radio off|on), as in M5 T3 item 11, where one "on" left the
# 8821cu in its C2H firmware error loop until a second toggle. Runs
# detached on the device (SSH drops while the radio is off) and logs to p3
# MUOS/log/t2-wifi-toggle.log: per cycle the seconds to an address and
# whether the worker reset the dongle on C2H errors (fw_broken, M6).
#   t2-wifi-toggle-loop.sh [--inject-c2h] [CYCLES]
#       default 8 cycles; PASS = every cycle got an address within 150 s.
#       --inject-c2h: in cycle 1, a fake 8821cu C2H error line goes to the
#       kernel log right after the radio's load marker; PASS then also
#       needs the worker's reset ("driver firmware errors") in that cycle.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
dev=$repo/port/scripts/device.sh
inject=0; [ "${1:-}" != --inject-c2h ] || { inject=1; shift; }
cycles=${1:-8}
case "$cycles" in ''|*[!0-9]*) echo "cycles: a number" >&2; exit 2 ;; esac
"$dev" run "cycles=$cycles inject=$inject"'
o=/userdata/MUOS/log/t2-wifi-toggle.log N=/run/muos/network S=/opt/muos/script/init/async/S02network.sh
: > $o
setsid sh -c "
    i=1
    while [ \$i -le $cycles ]; do
        $S radio off; sleep 3
        m=\$(dmesg | grep -c \"muos-network: radio up\")
        $S radio on
        if [ \$i = 1 ] && [ $inject = 1 ]; then
            k=0; while [ \$k -lt 600 ] && [ \$(dmesg | grep -c \"muos-network: radio up\") = \$m ]; do sleep 0.1; k=\$((k+1)); done
            echo \"RTW: ERROR c2h_handler_rtl8821c: [ERROR] C2H_ID(01) t2-injected\" > /dev/kmsg
        fi
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
if [ "$inject" = 1 ] && ! printf '%s\n' "$out" | grep -q '^cycle 1 ok .* c2h_resets=[1-9]'; then echo 'FAIL (no reset on the injected C2H error)'; exit 1; fi
echo PASS
