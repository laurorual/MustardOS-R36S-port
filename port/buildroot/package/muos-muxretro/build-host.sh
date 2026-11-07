#!/bin/sh
# SPDX-License-Identifier: MIT
# Compile only the host and its pinned MIT rcheevos, never UI or provider libs.
set -eu
[ "$#" = 8 ]
cc=$1;ar=$2;pkgconfig=$3;sysroot=$4;source=$5;platform=$6;flags=$7;ldflags=$8
export PKG_CONFIG_LIBDIR="$sysroot/usr/lib/pkgconfig:$sysroot/usr/share/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="$sysroot"
mkdir -p "$source/include/libarchive" "$source/rc-objects"
cp "$source"/rcheevos/include/*.h "$source/include/"
cp "$source/rcheevos/src/rc_libretro.h" "$source/include/"
printf '#include <archive.h>\n' > "$source/include/libarchive/archive.h"
printf '#include <archive_entry.h>\n' > "$source/include/libarchive/archive_entry.h"
rc=$source/rcheevos
for file in "$rc"/src/*.c "$rc"/src/rcheevos/*.c "$rc"/src/rapi/*.c "$rc"/src/rhash/*.c; do
 case "$file" in */rc_client_external.c|*/rc_client_raintegration.c) continue ;; esac
 name=$(basename "$(dirname "$file")")_$(basename "$file" .c)
 # TARGET_CFLAGS controls CPU/ABI; retain the qualified host's code generation.
 "$cc" $flags -fPIC -DRC_CLIENT_SUPPORTS_HASH -I"$rc/include" -I"$rc/src" -I"$rc/src/rcheevos" -I"$source/frontend/retro/core" -c "$file" -o "$source/rc-objects/$name.o"
done
"$ar" rcs "$source/librcheevos.a" "$source"/rc-objects/*.o
pkgs='sdl2 SDL2_image SDL2_mixer SDL2_ttf harfbuzz freetype2 libpng libcurl libarchive openssl'
cflags="$flags -std=c11 -D_GNU_SOURCE -DTEST_IMAGE=1 -DRC_CLIENT_SUPPORTS_HASH -DMINIZ_NO_ZLIB_COMPATIBLE_NAMES -fPIE -fstack-protector-strong -MMD -MP -Wall -Werror=implicit-function-declaration -Werror=incompatible-pointer-types -Werror=return-type -Wno-unused-function -I$source/include $($pkgconfig --cflags $pkgs)"
libs="-L$platform/lib -lui -lmuxcom -lmuxmod -lplutosvg $source/librcheevos.a $($pkgconfig --libs $pkgs) -lEGL -lGLESv2 -lz -ldl -lm -lpthread -latomic"
make -C "$source/frontend/retro" -j4 DEVICE=GENERIC ARCH_FLAGS=-mcpu=cortex-a35 CC="$cc" CFLAGS="$cflags" LDLIBS="$libs" LDFLAGS="$ldflags -pie -Wl,-z,relro,-z,now -Wl,--enable-new-dtags,-rpath,/opt/muos/frontend/lib -Wl,--export-dynamic-symbol=eglGetProcAddress -Wl,-rpath-link,$platform/lib -Wl,-rpath-link,$sysroot/lib -Wl,-rpath-link,$sysroot/usr/lib"
