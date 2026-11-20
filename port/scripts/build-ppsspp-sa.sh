#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # the container script expands its own variables
# M8 (decision 20; the user, 2026-11-20: standalone emulators follow
# dArkOSen): standalone PPSSPP (PPSSPPSDL) as dArkOS builds it for RK3326
# (christianhaitian/rk3326_core_builds scripts/ppsspp.sh): tag v1.20.4, its
# patches (port/patches/ppsspp, 001/002/003/006/007/008: no mouse, the
# handheld input, window size, FMV stutter, no mute), GLES2 without EGL
# (SDL's GL context), FBDEV, bundled FFmpeg, no Vulkan/Qt/Discord/UPnP, C
# flags -Ofast ... -mtune=cortex-a35 (its later -DCMAKE_CXX_FLAGS replaces
# the C++ ones with -fpermissive, so C++ gets the Release -O3). Built with
# the Buildroot SDK (gcc) instead of the dArkOS chroot's clang.
#
#   build-ppsspp-sa.sh build   offline, in the phase4-rootfs container, from
#                              the pinned tarball of build-cores.sh (row
#                              ppsspp) -> build/m8/ppsspp/tree/opt/muos/
#                              share/emulator/ppsspp/ (PPSSPPSDL, assets/)
set -euo pipefail
export LC_ALL=C
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work=$repo/build/phase4 area=$repo/build/m8/ppsspp
tree=$area/tree dest=opt/muos/share/emulator/ppsspp
mkdir -p "$area/logs"
read -r _ _ commit want _ < <(grep '^ppsspp ' "$repo/port/scripts/build-cores.sh")
tarball=$repo/build/m3c/cores/cache/ppsspp-$commit.tar
case "${1:-}" in
build)
    [ -s "$tarball" ] || { echo "run build-cores.sh fetch ppsspp first" >&2; exit 1; }
    [ "$(sha256sum "$tarball" | cut -d' ' -f1)" = "$want" ] || { echo 'ppsspp tarball SHA256 mismatch' >&2; exit 1; }
    stage=$area/stage; rm -rf "$stage" "$tree"; mkdir -p "$stage"
    tar -C "$stage" -xf "$tarball"
    code='set -eu
sdk=/work/graphics-config/output/host
export PATH=$sdk/bin:$PATH CCACHE_DISABLE=1
cd /stage/src
for p in /patches/ppsspp-patch-*.patch; do patch -s -Np1 < "$p"; done
# dArkOS builds without SDL2_ttf (not in its chroot): the atlas fonts. The
# SDK has the library, found by pkg-config only, which then breaks the link.
sed -i "s/^\(\s*\)pkg_check_modules(SDL2_ttf_PKGCONFIG /\1#&/" CMakeLists.txt
mkdir -p build && cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=$sdk/share/buildroot/toolchainfile.cmake \
    -DCMAKE_BUILD_TYPE=Release -DUSING_EGL=OFF -DUSING_GLES2=ON -DUSE_FFMPEG=YES \
    -DUSE_SYSTEM_FFMPEG=NO -DUSE_SYSTEM_LIBPNG=OFF -DVULKAN=OFF -DUSE_VULKAN_DISPLAY_KHR=OFF \
    -DUSING_X11_VULKAN=OFF -DUSE_WAYLAND_WSI=OFF -DUSING_FBDEV=ON -DUSE_MINIUPNPC=OFF \
    -DUSING_QT_UI=OFF -DUSE_DISCORD=OFF -DUNITTEST=OFF -DHEADLESS=OFF \
    -DCMAKE_DISABLE_FIND_PACKAGE_SDL2_ttf=TRUE -DCMAKE_DISABLE_FIND_PACKAGE_Fontconfig=TRUE \
    -DCMAKE_C_FLAGS="-Ofast -fno-tree-slp-vectorize -D_NDEBUG -march=armv8-a+crc -mtune=cortex-a35 -ftree-vectorize -funsafe-math-optimizations -ffile-prefix-map=/stage=." \
    -DCMAKE_CXX_FLAGS="-fpermissive -ffile-prefix-map=/stage=."
make -j8 PPSSPPSDL
aarch64-buildroot-linux-gnu-strip PPSSPPSDL'
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev,exec -v "$work:/work:ro,z" -v "$stage:/stage:rw,z" \
        -v "$repo/port/patches/ppsspp:/patches:ro,z" "$(cat "$work/rootfs-container.iid")" sh -c "$code" \
        > "$area/logs/build.log" 2>&1 ||
        { tail -25 "$area/logs/build.log"; echo "build failed (log $area/logs/build.log)" >&2; exit 1; }
    mkdir -p "$tree/$dest"
    cp "$stage/src/build/PPSSPPSDL" "$tree/$dest/"
    # dArkOS ships build/assets whole; the debugger web UI and the PPSSPP
    # UI's own language files are left out (unused on this device)
    cp -r "$stage/src/build/assets" "$tree/$dest/"
    rm -rf "$tree/$dest/assets/debugger"
    cp "$stage/src/LICENSE.TXT" "$tree/$dest/"
    rm -rf "$stage"
    (cd "$tree/$dest" && find . -type f | sort | xargs -d '\n' sha256sum > "$area/SHA256SUMS")
    du -sh "$tree/$dest"; grep -c . "$area/SHA256SUMS" ;;
*) sed -n '3,17p' "$0"; exit 2 ;;
esac
