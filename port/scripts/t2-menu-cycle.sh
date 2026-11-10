#!/usr/bin/env bash
# shellcheck disable=SC2016
# SPDX-License-Identifier: MIT
# T2: cold-ish boot -> menu -> Explore -> GB -> private.gb -> quick save ->
# quick load -> quit -> menu -> Reboot from the launcher -> state persisted.
# Drives the real buttons through /usr/libexec/muos-press (evdev injection).
#   t2-menu-cycle.sh [--no-reboot-first]
set -euo pipefail
dev=$(dirname "$0")/device.sh
pass() { printf 'PASS %s\n' "$*"; }
fail() { printf 'FAIL %s\n' "$*"; exit 1; }
r() { "$dev" run "cd /; $*"; }
module() { r 'pgrep -l "mux[a-z]*" | grep -v muxretro_ | awk "{print \$2}" | grep -v muhotkey | head -n1'; }
wait_module() { # NAME SECONDS
    for _ in $(seq 1 "$2"); do [ "$(module)" = "$1" ] && return 0; sleep 1; done
    return 1
}

if [ "${1:-}" != --no-reboot-first ]; then
    "$dev" reboot >/dev/null || fail "reboot"
fi
wait_module muxlaunch 40 || fail "menu after boot (got $(module))"
paint=$(r 'awk "/S99muos-ui start/ {print \$1}" /run/muos-rc.log')
pass "boot to menu (rcS done at ${paint}s uptime)"

r 'rm -f /userdata/MUOS/pickles/state/gambatte/GB/private/quicksave.state'
r '/usr/libexec/muos-press a; sleep 2; /usr/libexec/muos-press a; sleep 2; /usr/libexec/muos-press a'
wait_module muxretro 20 || fail "game start (got $(module))"
pass "menu -> GB launched in muxretro"

sleep 4
r '/usr/libexec/muos-press fn+r2'; sleep 2
r 'test -s /userdata/MUOS/pickles/state/gambatte/GB/private/quicksave.state' || fail "quick save on p3"
pass "Fn+R2 quick save written to p3"
r '/usr/libexec/muos-press fn+l2'; sleep 2
r 'grep -q "Quick Load (hotkey)" /opt/muos/log/frontend.log' || fail "quick load"
pass "Fn+L2 quick load"
r '/usr/libexec/muos-press fn+start'
wait_module muxplore 15 || fail "back to explore after quit (got $(module))"
pass "Fn+Start -> back to explore"

old=$(r 'cat /proc/sys/kernel/random/boot_id')
for _ in 1 2 3; do
    [ "$(module)" = muxlaunch ] && break
    r '/usr/libexec/muos-press b'; sleep 2
done
wait_module muxlaunch 10 || fail "back to launcher (got $(module))"
# MustardOS launcher is a 4x2 grid: explore collection history apps /
# info config reboot shutdown. Reboot = down, right, right; A opens the
# confirm dialog (default No), Up selects Yes, A confirms.
r '/usr/libexec/muos-press down right right a; sleep 1; /usr/libexec/muos-press up a' || :
sleep 25
for _ in $(seq 1 30); do
    new=$(r 'cat /proc/sys/kernel/random/boot_id' 2>/dev/null || :)
    [ -n "$new" ] && [ "$new" != "$old" ] && break
    sleep 5
done
[ -n "${new:-}" ] && [ "$new" != "$old" ] || fail "menu reboot"
pass "menu Reboot -> device rebooted"
r 'grep -q "S99muos-ui stop rc=0" /userdata/MUOS/log/rc-last.log' || fail "ordered UI stop on reboot"
pass "rcK stopped the UI cleanly (rc-last.log)"
r 'test -s /userdata/MUOS/pickles/state/gambatte/GB/private/quicksave.state' || fail "save state after reboot"
r '! dmesg | grep -q "mmcblk0p3.*recovery"' || fail "p3 needed journal recovery"
pass "save state persisted; p3 clean"
wait_module muxlaunch 40 || fail "menu after menu-reboot"
pass "menu up again after reboot"
