#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2: N sleep/resume cycles through the real Power-key path (muos-press power
# -> muhotkey SLEEP_SHORT -> muos-hotkey -> muos-suspend -> "mem"), woken by
# the RTC via /run/muos/suspend-test-wake. Each cycle checks: suspend entered,
# resumed, backlight restored, Wi-Fi/SSH back, frontend (or game) alive.
#   t2-sleep-cycle.sh [--game] [CYCLES] [WAKE_SECONDS]
# --game: launch GB first (frontend content handoff); checks muxretro saved
# on SIGUSR1 and is still running after each resume.
set -euo pipefail
dev=$(dirname "$0")/device.sh
game=0; [ "${1:-}" = --game ] && { game=1; shift; }
cycles=${1:-5} wake=${2:-15}
r() { "$dev" run "cd /; $*"; }
pid_of() { echo 'for p in /proc/[0-9]*; do [ "$(readlink $p/exe)" = /opt/muos/frontend/'"$1"' ] && echo ${p#/proc/}; done'; }
fail() { echo "FAIL $*"; r 'tail -5 /opt/muos/log/suspend.log' || :; exit 1; }

r "echo $wake > /run/muos/suspend-test-wake"
if [ "$game" = 1 ]; then
    r 'printf "%s\n" private gambatte_libretro.so "Nintendo Game Boy" 0 0 mu-gambatte /mnt/mmc/ROMS /GB private.gb > /run/muos/content
       echo explore > /run/muos/action; '"$(pid_of muxfrontend)"' | while read -r q; do kill -TERM "$q"; done'
    sleep 6
    [ -n "$(r "$(pid_of muxretro)")" ] || fail "game did not start"
    echo "game started"
fi
pass=0
for i in $(seq 1 "$cycles"); do
    before=$(r 'grep -c "suspend to" /opt/muos/log/suspend.log 2>/dev/null || echo 0')
    bright=$(r 'cat /sys/class/backlight/backlight/brightness')
    r 'nohup /usr/libexec/muos-press power >/dev/null 2>&1 &' || :
    sleep $((wake + 15))
    "$dev" wait 180 >/dev/null || fail "cycle $i: no SSH after resume"
    after=$(r 'grep -c "suspend to" /opt/muos/log/suspend.log')
    [ "$after" -gt "$before" ] || fail "cycle $i: did not suspend"
    r 'tail -1 /opt/muos/log/suspend.log | grep -q resumed' || fail "cycle $i: not resumed"
    [ "$(r 'cat /sys/class/backlight/backlight/brightness')" = "$bright" ] || fail "cycle $i: backlight not restored"
    if [ "$game" = 1 ]; then
        [ -n "$(r "$(pid_of muxretro)")" ] || fail "cycle $i: muxretro gone"
        r 'tail -12 /opt/muos/log/suspend.log | grep -q "muxretro saved"' || fail "cycle $i: muxretro did not confirm save"
    else
        [ -n "$(r "$(pid_of muxfrontend)")" ] || fail "cycle $i: frontend gone"
    fi
    pass=$((pass+1)); echo "cycle $i ok"
    sleep 8   # past the recent_wake guard
done
r 'rm -f /run/muos/suspend-test-wake'
if [ "$game" = 1 ]; then r '/usr/libexec/muos-press fn+start'; fi
echo "PASS $pass/$cycles sleep cycles$( [ "$game" = 1 ] && echo ' (in game)')"
