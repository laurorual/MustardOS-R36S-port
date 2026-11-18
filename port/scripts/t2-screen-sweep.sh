#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M5 T2: open every menu screen that is safe without context (t2-ui.sh
# open: muxfrontend restarted straight into the module) and record what
# happened: "ok" (the module runs), "bounced:<module>" (it handed over to
# another one at once), "crash" (muxfrontend exited non-zero, from
# muos-frontend's log). A screenshot per screen and a contact sheet
# (build/logs/m5/shots/sweep-sheet.png, 6 per row, labelled).
#   t2-screen-sweep.sh [MODULE...]   default: the list below
# Not opened: reset/reboot/shutdown/install(er) (actions), space (card
# preparation), content screens that need a selected item (assign,
# governor, control, retroarch, tag, filter, shader, overlay, option),
# app/appcon (no applications), link (USB gadget), text/third/credits.
set -euo pipefail
cd "$(dirname "$0")"
repo=$(cd ../.. && pwd)
dev=./device.sh
shots=$repo/build/logs/m5/shots
out=$repo/build/logs/m5/screen-sweep.txt
mods=("$@")
[ ${#mods[@]} -gt 0 ] || mods=(launcher explore collection history search picker theme themedwn themefilter
    config tweakgen tweakadv danger device rtc timezone info detail tester activity arc archive backup
    core language soundfont connect network netadv net_profile net_proxy net_scan webserv webcode
    btall btcon btdev hdmi rgb rgbzone remap passcfg storage power sort order kiosk profile custom logo
    news task screenshot distemp)
: > "$out"
# muos-frontend's loop log: an exit of the instance started for MODULE
exited() { "$dev" run "awk '/muxfrontend action=$1\$/ {s=1; e=\"\"; next} s && /muxfrontend exit rc=/ {e=\$0} END {print e}' /opt/muos/log/frontend-loop.log"; }
for m in "${mods[@]}"; do
    got=$(./t2-ui.sh open "$m" "sweep-$m" 2>&1 | sed -n 's/^module: //p') || got=error
    state=ok
    [ "$got" = "mux$m" ] || state="bounced:$got"
    e=$(exited "$m")
    case "$e" in ''|*' rc=0 '*) ;; *) state="crash: ${e#* }" ;; esac
    printf '%-12s %s\n' "$m" "$state" | tee -a "$out"
done
./t2-ui.sh open launcher sweep-zz-home > /dev/null
cd "$shots"
files=()
for f in sweep-*.png; do [ "$f" = sweep-sheet.png ] || files+=("$f"); done
montage -label '%t' -pointsize 22 -geometry 320x240+4+4 -tile 6x "${files[@]}" sweep-sheet.png
echo "sheet: $shots/sweep-sheet.png"
