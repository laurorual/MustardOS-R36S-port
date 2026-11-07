#!/bin/sh
# SPDX-License-Identifier: MIT
# C68 fixed RAM host, installed package preserved; no path/flags/ELF fallback supplied by the caller.
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
root=/
capsule=${1:-};operation=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64;;esac
case "$operation:$#" in check:2|launch:2) ;; *) exit 64;;esac
[ "$(id -u)" = 0 ]
[ -d "$capsule" ] && [ ! -L "$capsule" ]
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
[ "$(findmnt -rn -T "$capsule" -o FSTYPE)" = tmpfs ]
findmnt -rn -o OPTIONS "$root" | tr ',' '\n' | grep -qx ro
[ "$(stat -c '%u:%g:%a' "$root")" = 0:0:755 ]
for name in muxretro save-store;do
 [ ! -e "$capsule/$name" ] && [ ! -L "$capsule/$name" ] || exit 64
done
[ -f "$capsule/role" ] && [ ! -L "$capsule/role" ]
[ "$(stat -c '%u:%g:%a:%h' "$capsule/role")" = 0:0:600:1 ]
printf 'load\n' | cmp -s - "$capsule/role"
# All thirteen hashes, including the manifest itself, are pinned from C62.
while read -r digest mode relative;do
 file=${root%/}/$relative
 parent=$(dirname "$file")
 while [ "$parent" != / ] && [ "$parent" != // ] && [ "$parent" != "$root" ];do
  [ ! -L "$parent" ] && [ -d "$parent" ] || exit 64
  [ "$(stat -c '%u:%g:%a' "$parent")" = 0:0:755 ] || exit 64
  parent=$(dirname "$parent")
 done
 [ -f "$file" ] && [ ! -L "$file" ] || exit 64
 [ "$(stat -c '%u:%g:%a:%h' "$file")" = "0:0:$mode:1" ] || exit 64
 [ "$(sha256sum "$file" | cut -d' ' -f1)" = "$digest" ] || exit 64
done <<'C63_PINNED_PAYLOAD'
8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05 755 opt/muos/frontend/muxretro
3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986 644 usr/share/licenses/muos-muxretro/frontend/LICENSE
a11f7887be2af72bdf7f97dbd975f24df66922aaa6d5e6a7100f0bc1595fc1ae 644 usr/share/licenses/muos-muxretro/frontend/retro/core/libretro.h
6f24b341ab0c9ffc7aa3b83b0fb13025141455f9092a5b46b8564c4f3f05eba1 644 usr/share/licenses/muos-muxretro/frontend/vendor/json/LICENSE
88d9b4eb60579c191ec391ca04c16130572d7eedc4a86daa58bf28c6e14c9bcd 644 usr/share/licenses/muos-muxretro/frontend/vendor/mdns/LICENSE
2842d42dd84f5021f152a424a3644b584583d83e1e96635b62545c392a4fdd90 644 usr/share/licenses/muos-muxretro/frontend/vendor/mini/LICENSE
656928d6d5f662a18d02752f868f8b08a0e94f8f8f3aa3c1b1173505de8016e0 644 usr/share/licenses/muos-muxretro/frontend/vendor/miniz/LICENSE
28f238ce7f775ecb52d7b83a80cce95b457b8635e614d5ae3bb67205976a1cdb 644 usr/share/licenses/muos-muxretro/frontend/vendor/stb/LICENSE
b84e847ddcdc83c5224945810ff8ec9db4fc2151dd8a42f51ef836507fc0371c 644 usr/share/licenses/muos-muxretro/frontend/vendor/xxhash/LICENSE
bf820c034966a3b6be050bb85f94ec841a0b972bd5d477e362337d0574b5c219 644 usr/share/licenses/muos-muxretro/rcheevos/LICENSE
3c84fc40d5037adc9545e01ae8bef797b1be152edc32e5bd4bb5205eea5b5e79 644 usr/share/muos-muxretro/payload.sha256
e0a0bb341870532ba1a86725a9e74d91647009df2c5bc459db64008ba1fc36af 644 usr/share/muos-muxretro/platform.sha256
43cac9a373598b8a3e701c4b0b0a64bebf3004d99f1038af734073ddb6cc9445 644 usr/share/muos-muxretro/provenance.json
C63_PINNED_PAYLOAD
# Pinning the manifest itself prevents accepting an altered payload list.
[ -d "$capsule/host" ] && [ ! -L "$capsule/host" ]
[ "$(stat -c '%u:%g:%a' "$capsule/host")" = 0:0:700 ]
[ -f "$capsule/host/muxretro" ] && [ ! -L "$capsule/host/muxretro" ]
[ "$(stat -c '%u:%g:%a:%h' "$capsule/host/muxretro")" = 0:0:700:1 ]
[ "$(sha256sum "$capsule/host/muxretro" | cut -d' ' -f1)" = cd67ce605cfa406f6084c7348ebf27d475b73340edd981c1343f07b00a995e9d ]
printf 'C68_RAM_HOST_VALID operation=%s\n' "$operation"
/bin/sh "$capsule/frontend-libs.sh" "$capsule" "$operation"
[ "$operation" = check ] || [ "$(findmnt -rn -M /mnt/mmc -o FSTYPE)" = tmpfs ]
if [ "$operation" = check ];then
 printf 'C63_INSTALLED_HOST_VALID files=13 operation=check\n'
 exit 0
fi
content=/mnt/mmc/ROMS/GB/private.gb
for path in /mnt/mmc /mnt/mmc/ROMS /mnt/mmc/ROMS/GB;do [ -d "$path" ] && [ ! -L "$path" ] || exit 64;done
for file in "$content" "$capsule/core.so" "$capsule/private.gb";do
 [ -f "$file" ] && [ ! -L "$file" ] || exit 64
 [ "$(stat -c '%u:%g:%h' "$file")" = 0:0:1 ] || exit 64
done
[ "$(stat -c '%a' "$content")" = 400 ]
cmp -s "$capsule/private.gb" "$content"
printf 'C63_INSTALLED_HOST_VALID files=13 operation=launch\n'
exec "$capsule/host/muxretro" "$capsule/core.so" "$content" --fresh --diagnostic-content --diagnostic-seconds=45 --diagnostic-hotkey-exit
