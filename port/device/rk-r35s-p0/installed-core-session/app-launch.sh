#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
capsule=${1:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
[ "$#" = 1 ] && [ -d "$capsule" ] && [ ! -L "$capsule" ] || exit 64
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
[ -f "$capsule/gb-assets.sha256" ] && [ ! -L "$capsule/gb-assets.sha256" ] || exit 64
[ "$(stat -c '%u:%g:%a:%h' "$capsule/gb-assets.sha256")" = 0:0:600:1 ]
awk 'NF!=2 || length($1)!=64 || $1~/[^0-9a-f]/ || (NR==1 && $2!="/opt/muos/share/core/gambatte_libretro.so") || (NR==2 && $2!="private.gb") {bad=1} END{exit bad || NR!=2}' "$capsule/gb-assets.sha256"
for file in private.gb;do
 [ -f "$capsule/$file" ] && [ ! -L "$capsule/$file" ] || exit 64
 [ "$(stat -c '%u:%g:%a:%h' "$capsule/$file")" = 0:0:700:1 ]
done
[ ! -e "$capsule/core.so" ] && [ ! -L "$capsule/core.so" ] || exit 64
# The fixed dispatcher verifies all C76 leaves before this manifest is consumed.
/bin/sh "$capsule/installed-host.sh" "$capsule" check
(cd "$capsule" && sha256sum -c gb-assets.sha256)
[ "$(findmnt -rn -M /mnt/mmc -o FSTYPE)" = tmpfs ]
[ ! -L /mnt/mmc/ROMS ] && [ ! -L /mnt/mmc/ROMS/GB ] || exit 64
mkdir -p -m 700 /mnt/mmc/ROMS/GB
content=/mnt/mmc/ROMS/GB/private.gb
[ ! -e "$content" ] && [ ! -L "$content" ] || exit 64
cp "$capsule/private.gb" "$content";chmod 400 "$content"
cmp -s "$capsule/private.gb" "$content"
printf 'C53_PRIVATE_CONTENT_VERIFIED\n'
export LD_BIND_NOW=1 LD_LIBRARY_PATH="/opt/muos/frontend/lib"
exec /bin/sh "$capsule/installed-host.sh" "$capsule" launch
