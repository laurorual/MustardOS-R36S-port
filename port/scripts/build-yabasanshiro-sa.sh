#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # the container script expands its own variables
# M8 item 17 (Saturn; heavy systems = performance first, AGENTS.md):
# standalone YabaSanshiro as dArkOS builds it for RK3326
# (christianhaitian/rk3326_core_builds scripts/yabasanshirosa.sh): the
# retro_arena port of christianhaitian/yabasanshiro-standalone tag
# pi4-1-9-0, its patches 01-06 and 08 (low-res mode, paths, button order,
# SH2 cache off; 07 is the 480x320 OGA menu size, not used on 640x480),
# n2.cmake (aarch64, EGL), the ARM dynarec, no Vulkan, -O2 -march=armv8-a+crc
# -mtune=cortex-a35. dArkOS links the system Boost (libboost-all-dev); here
# Boost 1.83.0 (system, filesystem, date_time, locale without ICU) is
# built static in the same container and linked in, so the rootfs needs
# no Boost. Our patches (port/patches/yabasanshiro-sa) go on top: vblank
# page flips (this kernel refuses SDL's asynchronous ones), MUOS_YABA_FPSLOG
# (emulated fps on stderr), a crash stack. The data directory (patch 04's /opt/yabasanshiro/) becomes p3
# MUOS/port/yabasanshiro (input.cfg, keymapv2.json, states).
#
#   build-yabasanshiro-sa.sh build   offline, in the phase4-rootfs
#       container: build/m8/dl/boost_1_83_0.tar.bz2 (sha256 pinned) and
#       the clone build/yabasanshiro-sa-src (pinned commit, submodule eigen;
#       patched in a reflinked copy) -> build/m8/yabasanshiro/tree/opt/muos/
#       share/emulator/yabasanshiro/yabasanshiro
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work=$repo/build/phase4 area=$repo/build/m8/yabasanshiro
tree=$area/tree dest=opt/muos/share/emulator/yabasanshiro
src=$repo/build/yabasanshiro-sa-src src_commit=c7618d2ecbf77b1e8188fa8af4fa1cfb34833a72
boost=$repo/build/m8/dl/boost_1_83_0.tar.bz2
boost_sha=6478edfe2f3305127cffe8caf73ea0176c53769f4bf1585be237eb30798c3b8e
# libpng 1.6.37 (sourceforge; the build checks its own png_HASH too)
png=$repo/build/m8/dl/libpng-1.6.37.tar.gz
png_sha=daeb2620d829575513e35fecc83f0d3791a620b9b93d800b763542ece9390fb4
dpatches=$repo/build/rk3326-core-builds/patches
# the build's git dependencies, fetched once (shallow, pinned):
# zlib 50893291621658f355bc5b4d450a8d06a563053d (madler/zlib), json
# v3.2.0 = 359f98d14065bf4e53eeb274f5987fd08f16e5bf (nlohmann/json),
# libchdr 074ff1614f2a685f2b5a95b0e788bff6297d5680 (devmiyax/libchdr)
deps=$repo/build/yabasanshiro-sa-deps
mkdir -p "$area/logs"
case "${1:-}" in
build)
    [ "$(git -C "$src" rev-parse HEAD)" = "$src_commit" ] || { echo "yabasanshiro-sa-src is not at $src_commit" >&2; exit 1; }
    [ "$(sha256sum "$boost" | cut -d' ' -f1)" = "$boost_sha" ] || { echo 'boost tarball SHA256 mismatch' >&2; exit 1; }
    [ "$(sha256sum "$png" | cut -d' ' -f1)" = "$png_sha" ] || { echo 'libpng tarball SHA256 mismatch' >&2; exit 1; }
    for d in zlib:50893291621658f355bc5b4d450a8d06a563053d json:359f98d14065bf4e53eeb274f5987fd08f16e5bf \
             libchdr:074ff1614f2a685f2b5a95b0e788bff6297d5680; do
        [ "$(git -C "$deps/${d%%:*}" rev-parse HEAD 2>/dev/null)" = "${d#*:}" ] || { echo "dependency ${d%%:*} is not at ${d#*:}" >&2; exit 1; }
    done
    stage=$area/stage
    # the static Boost install is kept in $area/boost (built once, 180 MB with headers)
    [ ! -d "$stage/boost/lib" ] || [ -d "$area/boost/lib" ] || mv "$stage/boost" "$area/boost"
    rm -rf "$stage" "$tree"; mkdir -p "$stage/patches" "$area/boost"
    cp -r --reflink=auto "$src/yabause" "$stage/yabause"
    for n in 01 02 03 04 05 06 08; do cp "$dpatches"/yabasanshirosa-patch-$n-*.patch "$stage/patches/"; done
    # ours after dArkOS's (M8d T3): vsync flips, the T2 fps log, a crash stack
    for p in "$repo"/port/patches/yabasanshiro-sa/*.patch; do cp "$p" "$stage/patches/zz-${p##*/}"; done
    code='set -eu
sdk=/work/graphics-config/output/host
export PATH=$sdk/bin:$PATH CCACHE_DISABLE=1
cross=aarch64-buildroot-linux-gnu
sysroot=$sdk/$cross/sysroot
cd /stage
if [ ! -d /boost/lib ]; then
tar -xjf /boost.tar.bz2
cd boost_1_83_0
./bootstrap.sh --with-libraries=system,filesystem,date_time,locale > /stage/boost-bootstrap.log 2>&1
echo "using gcc : cross : $cross-g++ : <cxxflags>\"-O2 -march=armv8-a+crc -mtune=cortex-a35 -fPIC\" ;" > /stage/user-config.jam
./b2 -j8 --user-config=/stage/user-config.jam toolset=gcc-cross target-os=linux architecture=arm address-model=64 \
    link=static runtime-link=shared variant=release threading=multi boost.locale.icu=off boost.locale.iconv=on \
    boost.locale.posix=on --prefix=/boost install > /stage/boost-build.log 2>&1 || { tail -30 /stage/boost-build.log; exit 1; }
cd /stage && rm -rf boost_1_83_0
fi
for p in /stage/patches/*.patch; do patch -s -Np1 < "$p"; done
# offline: the ExternalProjects clone the pinned local copies in /deps
sed -i "s#^set(ZLIB_URL .*#set(ZLIB_URL /deps/zlib)#" yabause/CMake/Packages/external_zlib.cmake
sed -i "s#^set(png_URL .*#set(png_URL file:///png.tar.gz)#" yabause/CMake/Packages/external_libpng.cmake
sed -i "s#GIT_REPOSITORY \"https://github.com/devmiyax/libchdr.git\"#GIT_REPOSITORY /deps/libchdr#" yabause/CMake/Packages/external_libchdr.cmake
sed -i "s#GIT_REPOSITORY https://github.com/nlohmann/json.git#GIT_REPOSITORY /deps/json#; s#GIT_TAG v3.2.0#GIT_TAG 359f98d14065bf4e53eeb274f5987fd08f16e5bf#" yabause/src/retro_arena/CMakeLists.txt
# no desktop libGL in this sysroot (dArkOS has one): GLES3 by EGL is enough
sed -i "s/^\tif (OPENGL_FOUND )$/\tif (OPENGL_FOUND OR USE_EGL)/" yabause/src/CMakeLists.txt
grep -q "if (OPENGL_FOUND OR USE_EGL)" yabause/src/CMakeLists.txt
# dArkOS builds natively; cross, zlib and libchdr need the toolchain file too
sed -i "s#^\( *\)\\\${ADDITIONAL_CMAKE_ARGS}#\1\\\${ADDITIONAL_CMAKE_ARGS} -DCMAKE_TOOLCHAIN_FILE=\\\${CMAKE_TOOLCHAIN_FILE}#" \
    yabause/CMake/Packages/external_zlib.cmake yabause/CMake/Packages/external_libchdr.cmake \
    yabause/CMake/Packages/external_libpng.cmake
grep -q "/deps/libchdr" yabause/CMake/Packages/external_libchdr.cmake && grep -q "/deps/json" yabause/src/retro_arena/CMakeLists.txt
# M8d T3 5 (Select closed the game): the menu (nanogui) compiled an older
# nanovg_gl.h/nanovg.h whose renderFill lacks the compositeOperation
# argument, against the newer src/nanovg/nanovg.c: every menu fill got
# shifted arguments (a garbage scissor pointer, SIGSEGV in
# glnvg__renderFill). The menu builds with the same nanovg as the emulator.
for f in nanovg.c nanovg.h nanovg_gl.h nanovg_gl_utils.h fontstash.h stb_image.h stb_truetype.h; do cp yabause/src/nanovg/$f yabause/src/retro_arena/nanogui-sdl/ext/nanovg/; done
# patch 04 points the data directory at /opt/yabasanshiro/ (read-only p2 here)
grep -rl "/opt/yabasanshiro/" yabause/src/retro_arena | xargs sed -i "s#/opt/yabasanshiro/#/userdata/MUOS/port/yabasanshiro/#g"
# patch 05 keeps backup RAM and states in /roms2 or /roms saturn/yabasanshiro/
sed -i "s#\"/roms2\?/saturn/yabasanshiro/\"#\"/userdata/MUOS/port/yabasanshiro/save/\"#" yabause/src/retro_arena/main.cpp
[ "$(grep -c /userdata/MUOS/port/yabasanshiro/save/ yabause/src/retro_arena/main.cpp)" = 2 ]
mkdir -p build && cd build
# flags by -D only: the host tool m68kmake (an ExternalProject) reads CFLAGS
CFLAGS="-O2 -march=armv8-a+crc -mtune=cortex-a35 -ftree-vectorize -funsafe-math-optimizations -ffile-prefix-map=/stage=."
CXXFLAGS=$CFLAGS
# patch 01 adds "#include <core.h>" (src/) to threads.h
CFLAGS="$CFLAGS -I/stage/yabause/src" CXXFLAGS="$CXXFLAGS -I/stage/yabause/src"
cmake ../yabause -DCMAKE_TOOLCHAIN_FILE=$sdk/share/buildroot/toolchainfile.cmake \
    -DYAB_PORTS=retro_arena -DYAB_WANT_DYNAREC_DEVMIYAX=ON -DYAB_WANT_ARM7=ON -DYAB_WANT_C68K=${YABA_C68K:-ON} -DYAB_WANT_VULKAN=OFF \
    -DCMAKE_BUILD_TYPE=Release -DUSE_EGL=True -DCMAKE_C_FLAGS="$CFLAGS -D_POSIX_C_SOURCE=199309L -D__N2__ -D__RETORO_ARENA__" \
    -DCMAKE_CXX_FLAGS="$CXXFLAGS -D__N2__ -D__RETORO_ARENA__" \
    -DBoost_USE_STATIC_LIBS=ON -DBoost_DIR=/boost/lib/cmake/Boost-1.83.0 -DBoost_NO_SYSTEM_PATHS=ON \
    -DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=BOTH -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=BOTH \
    -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=BOTH
make -j8
cp src/retro_arena/yabasanshiro /stage/yabasanshiro.debug
$cross-strip src/retro_arena/yabasanshiro'
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev,exec -v "$work:/work:ro,z" -v "$stage:/stage:rw,z" \
        -v "$deps:/deps:ro,z" -v "$area/boost:/boost:rw,z" -v "$boost:/boost.tar.bz2:ro,z" -v "$png:/png.tar.gz:ro,z" "$(cat "$work/rootfs-container.iid")" sh -c "$code" \
        > "$area/logs/build.log" 2>&1 ||
        { tail -40 "$area/logs/build.log"; echo "build failed (log $area/logs/build.log)" >&2; exit 1; }
    mkdir -p "$tree/$dest"
    cp "$stage/build/src/retro_arena/yabasanshiro" "$tree/$dest/"
    # unstripped copy for addr2line on a crash stack (not shipped)
    mv "$stage/yabasanshiro.debug" "$area/yabasanshiro.debug"
    cp "$src/yabause/COPYING" "$tree/$dest/" 2>/dev/null || cp "$src/LICENSE" "$tree/$dest/" 2>/dev/null || :
    rm -rf "$stage"
    (cd "$tree/$dest" && find . -type f | sort | xargs -d '\n' sha256sum > "$area/SHA256SUMS")
    du -sh "$tree/$dest" ;;
*) sed -n '3,21p' "$0"; exit 2 ;;
esac
