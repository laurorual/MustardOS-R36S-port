#!/bin/sh
# SPDX-License-Identifier: MIT
# muOS R35S port: Configuration -> General -> Input Remap saves through
#   sdl_remap.sh <modern|retro> <SDL mapping line>
# (the frontend's muxremap calls it, then reloads its own mappings). The
# pinned muOS script set lacked it (M4e T3: a remap never stuck). Same
# contract as upstream: the line replaces any line with the same GUID in
# share/info/gamecontrollerdb/<target>.txt (p3 MUOS/port/gamecontrollerdb
# since M4e.1, bound by S91: the root is read-only) and settings/remap/layout
# follows the target. display.sh caches the matching line per file in
# /tmp/sdl_gc_<target>.txt for launched content: drop it so the next launch
# reads the new mapping.
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
target=${1:-} mapping=${2:-}
db_dir=/opt/muos/share/info/gamecontrollerdb
log() { echo "sdl_remap: $*"; logger -t sdl_remap "$*" 2>/dev/null || :; }
case "$target" in
 modern) layout=1 ;;
 retro) layout=0 ;;
 *) echo 'Usage: sdl_remap.sh modern|retro MAPPING' >&2; exit 2 ;;
esac
guid=${mapping%%,*}
case "$guid" in
 *[!0-9a-fA-F]*|'') log "invalid mapping (no GUID)"; exit 1 ;;
esac
[ "${#guid}" -eq 32 ] || { log "invalid GUID '$guid'"; exit 1; }
case "$mapping" in *'
'*) log 'invalid mapping (several lines)'; exit 1 ;; esac
db=$db_dir/$target.txt
tmp=$db.tmp.$$
{
    printf '%s\n' "$mapping"
    [ ! -f "$db" ] || grep -v "^$guid," "$db" || :
} > "$tmp" && mv -f "$tmp" "$db" || { rm -f "$tmp"; log "cannot write $db"; exit 1; }
conf=/opt/muos/config/settings/remap
mkdir -p "$conf" && printf '%s\n' "$layout" > "$conf/layout.tmp" && mv -f "$conf/layout.tmp" "$conf/layout"
rm -f "/tmp/sdl_gc_$target.txt"
sync
log "saved $guid to $db"
