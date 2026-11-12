#!/usr/bin/env bash
# shellcheck disable=SC2016
# SPDX-License-Identifier: MIT
# T2: cold-ish boot -> menu -> Explore -> GB -> first game -> quick save ->
# quick load -> quit -> menu -> Reboot from the launcher -> state persisted.
# The game is whichever Explore opens (read from muxretro's command line).
# The user's GB states, GB SRAM and resume.ini are copied to p3
# MUOS/t2-snap first and put back at the end (also on failure).
# Drives the real buttons through /usr/libexec/muos-press (evdev injection).
#   t2-menu-cycle.sh [--no-reboot-first]
set -euo pipefail
dev=$(dirname "$0")/device.sh
pass() { printf 'PASS %s\n' "$*"; }
fail() { printf 'FAIL %s\n' "$*"; exit 1; }
r() { "$dev" run "cd /; $*"; }
# Match on /proc/PID/exe: pgrep would also match this SSH command line.
module() { r 'for p in /proc/[0-9]*; do case "$(readlink $p/exe)" in /opt/muos/frontend/muxretro|/opt/muos/frontend/muxfrontend) cat $p/comm;; esac; done | sort -r | head -n1'; }
wait_module() { # NAME SECONDS
    for _ in $(seq 1 "$2"); do [ "$(module)" = "$1" ] && return 0; sleep 1; done
    return 1
}

# Literal paths only (no rm on an expanded variable).
snap_save() {
    r 'rm -rf /userdata/MUOS/t2-snap && mkdir -p /userdata/MUOS/t2-snap/state /userdata/MUOS/t2-snap/sram
       cp -a /userdata/MUOS/pickles/state/gambatte/GB/. /userdata/MUOS/t2-snap/state/ 2>/dev/null
       cp -a /userdata/MUOS/pickles/sram/gambatte/GB/. /userdata/MUOS/t2-snap/sram/ 2>/dev/null
       cp -a /userdata/MUOS/pickles/resume.ini /userdata/MUOS/t2-snap/ 2>/dev/null; touch /userdata/MUOS/t2-snap/.ok; sync'
}
snap_restore() {
    # A game left running by a failure would autosave on its later quit.
    if [ "$(module)" = muxretro ]; then r '/usr/libexec/muos-press fn+start' || :; wait_module muxplore 15 || :; fi
    r 'test -e /userdata/MUOS/t2-snap/.ok || exit 0
       mkdir -p /userdata/MUOS/pickles/state/gambatte/GB /userdata/MUOS/pickles/sram/gambatte/GB
       rm -rf /userdata/MUOS/pickles/state/gambatte/GB/* /userdata/MUOS/pickles/sram/gambatte/GB/*
       cp -a /userdata/MUOS/t2-snap/state/. /userdata/MUOS/pickles/state/gambatte/GB/
       cp -a /userdata/MUOS/t2-snap/sram/. /userdata/MUOS/pickles/sram/gambatte/GB/
       [ ! -e /userdata/MUOS/t2-snap/resume.ini ] || cp -a /userdata/MUOS/t2-snap/resume.ini /userdata/MUOS/pickles/resume.ini
       rm -rf /userdata/MUOS/t2-snap; sync' || echo "WARN: restore of the GB saves failed; copy is in p3 MUOS/t2-snap"
}
trap 'snap_restore' EXIT

if [ "${1:-}" != --no-reboot-first ]; then
    "$dev" reboot >/dev/null || fail "reboot"
fi
wait_module muxlaunch 40 || fail "menu after boot (got $(module))"
paint=$(r 'awk "/S99muos-ui start/ {print \$1}" /run/muos-rc.log')
pass "boot to menu (rcS done at ${paint}s uptime)"
sleep 5 # the menu opens its SDL_mixer device right after painting
a=$("$(dirname "$0")/t2-audio-state.sh" 2>&1) || fail "audio in the menu: $(grep -E '^(boot|FAIL)' <<< "$a" | cut -c1-160 | tr '\n' ' ')"
pass "audio in the menu ($(grep -o 'rate=[0-9]* streams=[^ ]*' <<< "$a"))"

snap_save
r '/usr/libexec/muos-press a; sleep 2; /usr/libexec/muos-press a; sleep 2; /usr/libexec/muos-press a'
wait_module muxretro 20 || fail "game start (got $(module))"
content=$(r 'for p in /proc/[0-9]*; do [ "$(readlink $p/exe)" = /opt/muos/frontend/muxretro ] && tr "\0" "\n" < $p/cmdline | sed -n 3p; done; true')
stem=$(basename "${content%.*}")
case "$content" in */ROMS/GB/*) ;; *) fail "Explore opened ${content:-nothing}, not a GB game" ;; esac
qs="/userdata/MUOS/pickles/state/gambatte/GB/$stem/quicksave.state"
pass "menu -> GB launched in muxretro ($stem)"

sleep 4
a=$("$(dirname "$0")/t2-audio-state.sh" 2>&1) || fail "audio in the game: $(grep -E '^(boot|FAIL)' <<< "$a" | cut -c1-160 | tr '\n' ' ')"
pass "audio in the game ($(grep -o 'rate=[0-9]* streams=[^ ]*' <<< "$a"))"
r 'touch /run/t2-mark; sleep 1; /usr/libexec/muos-press fn+r2'; sleep 2
r "test -s '$qs' && [ -n \"\$(find '$qs' -newer /run/t2-mark)\" ]" || fail "quick save on p3"
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
r "test -s '$qs'" || fail "save state after reboot"
r '! dmesg | grep -q "mmcblk0p3.*recovery"' || fail "p3 needed journal recovery"
pass "save state persisted; p3 clean"
wait_module muxlaunch 40 || fail "menu after menu-reboot"
pass "menu up again after reboot"
