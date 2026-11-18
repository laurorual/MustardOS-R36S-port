#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M5 T2: drive and look at the menu over SSH.
#   t2-ui.sh mod                  the current frontend module (muxfrontend's comm)
#   t2-ui.sh press KEY...         muos-press KEY, 1 s apart (KEYs as muos-press)
#   t2-ui.sh shot NAME            screenshot (frontend patch 0007) to
#                                 build/logs/m5/shots/NAME.png
#   t2-ui.sh go NAME KEY...       press KEY... then shot NAME, print the module
#   t2-ui.sh home                 B until the launcher (muxlaunch), at most 8
#   t2-ui.sh open MODULE [NAME]   restart muxfrontend straight into MODULE (the
#                                 /run/muos/action name, e.g. theme, backup),
#                                 shot NAME (default MODULE)
# Never press A without knowing the screen (see procedures.md): `go` prints
# the module after every step so a script can stop on a surprise.
set -euo pipefail
cd "$(dirname "$0")"
dev=./device.sh
shots=$(cd ../.. && pwd)/build/logs/m5/shots
r() { "$dev" run "$@"; }
mod() {
    r 'for p in /proc/[0-9]*; do case "$(readlink $p/exe)" in /opt/muos/frontend/muxretro|/opt/muos/frontend/muxfrontend) cat $p/comm;; esac; done | sort -r | head -n1'
}
press() {
    local k cmd=
    for k in "$@"; do cmd="$cmd /usr/libexec/muos-press $k; sleep 1;"; done
    r "$cmd"
}
shot() {
    mkdir -p "$shots"
    r "/opt/muos/script/mux/screenshot.sh /run/t2-ui.png > /dev/null" || { echo "shot $1: failed" >&2; return 1; }
    "$dev" pull /run/t2-ui.png "$shots" > /dev/null && mv "$shots/t2-ui.png" "$shots/$1.png"
    echo "$shots/$1.png"
}
case "${1:-}" in
mod) mod ;;
press) shift; press "$@" ;;
shot) shot "$2" ;;
go) name=$2; shift 2; [ $# -eq 0 ] || press "$@"; sleep 1; echo "module: $(mod)"; shot "$name" ;;
open)
    m=$2 n=${3:-$2}
    r "echo $m > /run/muos/action; p=\$(pidof muxfrontend) && kill -TERM \$p; i=0
       while [ \$i -lt 40 ]; do sleep 0.25; i=\$((i+1)); q=\$(pidof muxfrontend) && [ \"\$q\" != \"\$p\" ] && break; done"
    sleep 3; echo "module: $(mod)"; shot "$n" ;;
home)
    for _ in 1 2 3 4 5 6 7 8; do [ "$(mod)" = muxlaunch ] && { echo muxlaunch; exit 0; }; press b; done
    echo "not home: $(mod)" >&2; exit 1 ;;
*) sed -n '3,11p' "$0"; exit 2 ;;
esac
