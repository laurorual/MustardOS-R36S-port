#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
capsule=${1:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
[ "$#" = 1 ] && [ -d "$capsule" ] && [ ! -L "$capsule" ] || exit 64
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
[ -f "$capsule/nes-assets.sha256" ] && [ ! -L "$capsule/nes-assets.sha256" ] || exit 64
[ "$(stat -c '%u:%g:%a:%h' "$capsule/nes-assets.sha256")" = 0:0:600:1 ]
awk 'NF!=2 || length($1)!=64 || $1~/[^0-9a-f]/ || (NR==1 && $2!="core.so") || (NR==2 && $2!="r35s-flight.nes") {bad=1} END{exit bad || NR!=2}' "$capsule/nes-assets.sha256"
for file in core.so r35s-flight.nes;do
 [ -f "$capsule/$file" ] && [ ! -L "$capsule/$file" ] || exit 64
 [ "$(stat -c '%u:%g:%a:%h' "$capsule/$file")" = 0:0:700:1 ]
done
(cd "$capsule" && sha256sum -c nes-assets.sha256)
[ "$(findmnt -rn -M /mnt/mmc -o FSTYPE)" = tmpfs ]
[ ! -L /mnt/mmc/ROMS ] && [ ! -L /mnt/mmc/ROMS/NES ] || exit 64
mkdir -p -m 700 /mnt/mmc/ROMS/NES
content=/mnt/mmc/ROMS/NES/r35s-flight.nes
[ ! -e "$content" ] && [ ! -L "$content" ] || exit 64
cp "$capsule/r35s-flight.nes" "$content";chmod 400 "$content"
cmp -s "$capsule/r35s-flight.nes" "$content"
printf 'C47_FIXED_CONTENT_VERIFIED\n'
exec "$capsule/muxretro" "$capsule/core.so" "$content" --fresh --diagnostic-content --diagnostic-seconds=30
