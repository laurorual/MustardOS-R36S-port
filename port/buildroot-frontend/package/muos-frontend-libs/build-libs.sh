#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
cc=$1; ar=$2; pkg_config=$3; sysroot=$4; source=$5; cflags=$6; ldflags=$7
export PKG_CONFIG_LIBDIR="$sysroot/usr/lib/pkgconfig:$sysroot/usr/share/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="$sysroot"
export PATH="$(dirname "$cc"):$PATH"
cd "$source"
# The preparer admits text source only, so this never reuses a prebuilt archive.
mkdir -p deps/pic
for input in deps/mojibake-0.3.6/src/*.c; do
    # Buildroot TARGET_CFLAGS is intentionally a word list.
    "$cc" $cflags -std=c11 -fPIC -Ideps/mojibake-0.3.6/src -c "$input" \
        -o "deps/pic/$(basename "$input" .c).o"
done
"$ar" rcs deps/libmojibake-pic.a deps/pic/*.o
make -C frontend -f phase4-frontend-libs.mk -j8 CC="$cc" PKG_CONFIG="$pkg_config" \
    CFLAGS="$cflags" LDFLAGS="$ldflags"
