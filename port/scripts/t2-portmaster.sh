#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # device-side commands in single quotes
# M11 T2: PortMaster on the bench (developer image, Wi-Fi up).
#   1. install (muos-portmaster install: download, SHA256, unzip) unless
#      present; status = installed
#   2. harbourmaster CLI installs the test ports (SDL2: sdlsopwith;
#      Godot frt runtime squashfs: turbotabletennis; libretro via the
#      retroarch shim: 2048)
#   3. each port through the frontend's content handoff, 30 s, Fn+Start,
#      back to the menu (t2-standalone.sh); no leftover processes or
#      runtime mounts
#   4. Applications -> PortMaster (action app): pugwash runs 20 s without
#      a traceback in MUOS/PortMaster/log.txt, then Fn+Start
#   t2-portmaster.sh [--reinstall]
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
dev=port/scripts/device.sh
log=build/logs/m11/t2-portmaster.log; mkdir -p "${log%/*}"; : > "$log"
say() { echo "$*" | tee -a "$log"; }
fail() { say "FAIL $*"; exit 1; }
r() { "$dev" run "$@" 2>> "$log"; }
pm=/mnt/mmc/MUOS/PortMaster
[ "${1:-}" != --reinstall ] || r "rm -rf $pm"
if [ "$(r '/usr/libexec/muos-portmaster status')" = missing ]; then
    r '/usr/libexec/muos-portmaster install' >> "$log" 2>&1 || fail "1: install"
fi
st=$(r '/usr/libexec/muos-portmaster status'); case $st in installed*) ;; *) fail "1: $st" ;; esac
say "ok   1: $st"
for p in sdlsopwith turbotabletennis 2048; do
    r "cd $pm && HOME=/root PYSDL2_DLL_PATH=/usr/lib python3 ./harbourmaster --quiet install $p.zip" >> "$log" 2>&1 ||
        fail "2: harbourmaster install $p"
done
say "ok   2: ports installed: $(r 'ls /mnt/mmc/ROMS/Ports | tr "\n" "|"')"
# NAME SCRIPT PROCESS
while read -r n s p; do
    s=${s//_/ }
    port/scripts/t2-standalone.sh "port-$n" external Ports "$s" "$p" 30 >> "$log" 2>&1 || fail "3: $n (t2-standalone)"
    sleep 4
    left=$(r 'pidof '"$p"' gptokeyb gptokeyb2 || :')
    [ -z "$left" ] || fail "3: $n left processes: $left"
    r 'grep -q "^/dev/loop[0-9]* [^ ]* squashfs " /proc/mounts' && fail "3: $n left a runtime mounted"
    say "ok   3: $n ran, quit, nothing left"
done <<'EOF'
sopwith SDL_Sopwith.sh sopwith
ttt TurboTableTennis.sh frt_3.5.2
2048 2048.sh muxretro
EOF
r 'printf %s /opt/muos/share/application/PortMaster > /run/muos/application; echo app > /run/muos/action
   for q in $(pidof muxfrontend); do kill -TERM "$q"; done'
ok=
for _ in $(seq 40); do r 'pgrep -f pugwash' > /dev/null && { ok=1; break; }; sleep 1; done
[ -n "$ok" ] || fail "4: pugwash did not start ($(r "tail -n 3 $pm/log.txt" | tr '\n' ' '))"
sleep 20
r 'pgrep -f pugwash' > /dev/null || fail "4: pugwash died: $(r "grep -m1 -A3 Traceback $pm/log.txt" | tr '\n' ' ')"
r "grep -q Traceback $pm/log.txt" && fail "4: traceback in log.txt"
r '/usr/libexec/muos-press fn+start'
sleep 6
r 'pgrep -f pugwash' > /dev/null && fail "4: pugwash still running after Fn+Start"
say "ok   4: PortMaster GUI ran 20 s, quit on Fn+Start"
say PASS
