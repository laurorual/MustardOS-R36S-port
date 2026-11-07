#!/bin/sh
# SPDX-License-Identifier: MIT
# C77 fixed installed host and core; no path/flags/ELF fallback supplied by the caller.
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
for name in muxretro save-store host core.so;do
 [ ! -e "$capsule/$name" ] && [ ! -L "$capsule/$name" ] || exit 64
done
[ -f "$capsule/role" ] && [ ! -L "$capsule/role" ]
[ "$(stat -c '%u:%g:%a:%h' "$capsule/role")" = 0:0:600:1 ]
printf 'load\n' | cmp -s - "$capsule/role"
# Pin all 40 C72/C76 leaves, including manifests and core license review.
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
done <<'C73_PINNED_PAYLOAD'
2913dbf7d901a258d338995e0d937c2f6559465c41a3bd0e097072820f57cd21 644 opt/muos/frontend/lib/libmuxcom.so
bfd909c6eae5d6d692025e8a0b489840c9a552d3ad22e902183b6265d700ae17 644 opt/muos/frontend/lib/libmuxmod.so
99377c313fdb5401e4535be4750afb8db9c6c6acc052818a2eee0c956cbe8683 644 opt/muos/frontend/lib/libplutosvg.so
639c1df8c75dc5007abfb87817d8cb1ea6b3ed7e0366f008e976a0e74491791e 644 opt/muos/frontend/lib/libui.so
cd67ce605cfa406f6084c7348ebf27d475b73340edd981c1343f07b00a995e9d 755 opt/muos/frontend/muxretro
9913af6a06b6979d63e3fa762c9cfb7b0d02d90141efb0e5b9b3b7e4249b757a 644 usr/share/licenses/muos-frontend-libs/deps/mojibake-0.3.6/LICENSE
3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986 644 usr/share/licenses/muos-frontend-libs/frontend/LICENSE
6f24b341ab0c9ffc7aa3b83b0fb13025141455f9092a5b46b8564c4f3f05eba1 644 usr/share/licenses/muos-frontend-libs/frontend/vendor/json/LICENSE
8494fee5b3451da29a545f889af62fb719b2969e1f8ed57aa52fab8f887324aa 644 usr/share/licenses/muos-frontend-libs/frontend/vendor/lvgl/LICENCE
88d9b4eb60579c191ec391ca04c16130572d7eedc4a86daa58bf28c6e14c9bcd 644 usr/share/licenses/muos-frontend-libs/frontend/vendor/mdns/LICENSE
2842d42dd84f5021f152a424a3644b584583d83e1e96635b62545c392a4fdd90 644 usr/share/licenses/muos-frontend-libs/frontend/vendor/mini/LICENSE
656928d6d5f662a18d02752f868f8b08a0e94f8f8f3aa3c1b1173505de8016e0 644 usr/share/licenses/muos-frontend-libs/frontend/vendor/miniz/LICENSE
a55d1e78eaf75779c336b4ba061e74aae56a21195d234474fb24a398935d6ce1 644 usr/share/licenses/muos-frontend-libs/frontend/vendor/plutosvg/LICENSE
a55d1e78eaf75779c336b4ba061e74aae56a21195d234474fb24a398935d6ce1 644 usr/share/licenses/muos-frontend-libs/frontend/vendor/plutosvg/plutovg/LICENSE
28f238ce7f775ecb52d7b83a80cce95b457b8635e614d5ae3bb67205976a1cdb 644 usr/share/licenses/muos-frontend-libs/frontend/vendor/stb/LICENSE
b84e847ddcdc83c5224945810ff8ec9db4fc2151dd8a42f51ef836507fc0371c 644 usr/share/licenses/muos-frontend-libs/frontend/vendor/xxhash/LICENSE
3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986 644 usr/share/licenses/muos-muxretro-provider/frontend/LICENSE
a11f7887be2af72bdf7f97dbd975f24df66922aaa6d5e6a7100f0bc1595fc1ae 644 usr/share/licenses/muos-muxretro-provider/frontend/retro/core/libretro.h
6f24b341ab0c9ffc7aa3b83b0fb13025141455f9092a5b46b8564c4f3f05eba1 644 usr/share/licenses/muos-muxretro-provider/frontend/vendor/json/LICENSE
8494fee5b3451da29a545f889af62fb719b2969e1f8ed57aa52fab8f887324aa 644 usr/share/licenses/muos-muxretro-provider/frontend/vendor/lvgl/LICENCE
88d9b4eb60579c191ec391ca04c16130572d7eedc4a86daa58bf28c6e14c9bcd 644 usr/share/licenses/muos-muxretro-provider/frontend/vendor/mdns/LICENSE
2842d42dd84f5021f152a424a3644b584583d83e1e96635b62545c392a4fdd90 644 usr/share/licenses/muos-muxretro-provider/frontend/vendor/mini/LICENSE
656928d6d5f662a18d02752f868f8b08a0e94f8f8f3aa3c1b1173505de8016e0 644 usr/share/licenses/muos-muxretro-provider/frontend/vendor/miniz/LICENSE
28f238ce7f775ecb52d7b83a80cce95b457b8635e614d5ae3bb67205976a1cdb 644 usr/share/licenses/muos-muxretro-provider/frontend/vendor/stb/LICENSE
b84e847ddcdc83c5224945810ff8ec9db4fc2151dd8a42f51ef836507fc0371c 644 usr/share/licenses/muos-muxretro-provider/frontend/vendor/xxhash/LICENSE
bf820c034966a3b6be050bb85f94ec841a0b972bd5d477e362337d0574b5c219 644 usr/share/licenses/muos-muxretro-provider/rcheevos/LICENSE
a8f1b2b09a8a9ac70c26ed48541861cdd158b1a2a0b2288033501f3ceda0a9d2 644 usr/share/muos-frontend-libs/payload.sha256
3ef6c57dc077ce25ec44eb9bb7aef0fa04b2ab85ca7e74d5243453d15c2c834e 644 usr/share/muos-frontend-libs/provenance.json
b058d37f8abc9143bd38dbd4fb8c056727dbbf7eeea848324b300ac1aa555016 644 usr/share/muos-muxretro-provider/payload.sha256
b64f485175b36c50d45ee430d8a29be4076e70fdad5a2b517ba0b5ab8a397b3c 644 usr/share/muos-muxretro-provider/provenance.json
5fef77d5065d1db8fc50a1aaa6b9114b281d3f4f8d9a1ec440b3ce2fcfad7158 644 usr/share/muos-muxretro-provider/provider-runtime.sha256
3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57 644 opt/muos/share/core/gambatte_libretro.so
ab15fd526bd8dd18a9e77ebc139656bf4d33e97fc7238cd11bf60e2b9b8666c6 644 usr/share/licenses/muos-gambatte/COPYING
3e05e66cdfa2ddb8e9ac4eee6bb38ff4d735ed82e8563ef116b710089c732512 644 usr/share/licenses/muos-gambatte/libgambatte/libretro-common/include/libretro.h
9bb3ad7ab44aea1ba1c0d44a87f47144390ca8cef89c704c86cc83a7bdfbf417 644 usr/share/licenses/muos-gambatte/libgambatte/libretro-common/streams/file_stream.c
6924cd1affc8b6d3119389551141fe2c47600b8bfc5ab09bbec7e4d6dfae2634 644 usr/share/licenses/muos-gambatte/libgambatte/libretro/blipper.c
9a2d67e42f674d4cdd896fe183f70e4e4e2585fc51cd5bed0f65f538e6513f95 644 usr/share/licenses/muos-gambatte/libgambatte/libretro/cc_resampler.c
f0ff28b448704a06d30f624fd25f7534a42b0f8baf55e2c34c31879b6babeda9 644 usr/share/licenses/muos-gambatte/libgambatte/libretro/cc_resampler.h
a23da3a77df1f74174e2343008a52e5af00305113d65bc968777ca74eaa9d1d7 644 usr/share/muos-gambatte/license-review.json
71c05642b46b4e0a5ca4bc8a63f37ce7aaf3918ca92c1b4bcdb8479e32c48244 644 usr/share/muos-gambatte/payload.sha256
C73_PINNED_PAYLOAD
# Pinning the manifest itself prevents accepting an altered payload list.
/bin/sh "$capsule/frontend-libs.sh" "$capsule" "$operation"
[ "$operation" = check ] || [ "$(findmnt -rn -M /mnt/mmc -o FSTYPE)" = tmpfs ]
if [ "$operation" = check ];then
 printf 'C77_INSTALLED_HOST_CORE_VALID files=40 operation=check\n'
 exit 0
fi
content=/mnt/mmc/ROMS/GB/private.gb
for path in /mnt/mmc /mnt/mmc/ROMS /mnt/mmc/ROMS/GB;do [ -d "$path" ] && [ ! -L "$path" ] || exit 64;done
for file in "$content" "/opt/muos/share/core/gambatte_libretro.so" "$capsule/private.gb";do
 [ -f "$file" ] && [ ! -L "$file" ] || exit 64
 [ "$(stat -c '%u:%g:%h' "$file")" = 0:0:1 ] || exit 64
done
[ "$(stat -c '%a' "$content")" = 400 ]
cmp -s "$capsule/private.gb" "$content"
printf 'C77_INSTALLED_HOST_CORE_VALID files=40 operation=launch\n'
exec /opt/muos/frontend/muxretro "/opt/muos/share/core/gambatte_libretro.so" "$content" --fresh --diagnostic-content --diagnostic-seconds=45 --diagnostic-hotkey-exit
