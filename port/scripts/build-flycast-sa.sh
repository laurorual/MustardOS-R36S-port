#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # the container script expands its own variables
# M8 thermal block T9 (DC; heavy systems = performance first, AGENTS.md):
# standalone Flycast as dArkOSen ships it since 2026-11 (/opt/flycastsa,
# `dreamcast.sh standalone-Flycast`, version v2.7). Its binary in the
# dArkOSen repository is damaged (the repo's `* text eol=lf` attribute
# turned 42 CRLF pairs into LF), so it is built here the way dArkOS does
# (christianhaitian/rk3326_core_builds scripts/flycastsa.sh: -Ofast,
# GLES, OpenMP, no Vulkan, no PulseAudio, system zlib, patch 003 for
# SDL_GAMECONTROLLERCONFIG_FILE; the system SDL2, which has the KMSDRM/Mali
# setup, not its bundled copy) from the same flyinghead/flycast commit
# as the Flycast v2.7 core (build-cores.sh row flycast2).
#   build-flycast-sa.sh build  -> build/m8f/flycast-sa/tree/opt/muos/share/emulator/flycast/flycast
set -euo pipefail
export LC_ALL=C
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work=$repo/build/phase4 area=$repo/build/m8f/flycast-sa
tree=$area/tree dest=opt/muos/share/emulator/flycast
mkdir -p "$area/logs"
read -r _ _ commit want _ < <(grep "^flycast2 " "$repo/port/scripts/build-cores.sh")
tarball=$repo/build/m3c/cores/cache/flycast2-$commit.tar
patch003=$repo/build/rk3326-core-builds/patches/flycastsa-patch-003-fix-sdl-controller.patch
case "${1:-}" in
build)
    [ "$(sha256sum "$tarball" | cut -d' ' -f1)" = "$want" ] || { echo 'flycast2 tarball SHA256 mismatch' >&2; exit 1; }
    stage=$area/stage; rm -rf "$stage" "$tree"; mkdir -p "$stage"
    tar -C "$stage" -xf "$tarball"
    cp "$patch003" "$stage/"
    code='set -eu
sdk=/work/graphics-config/output/host
export PATH=$sdk/bin:$PATH CCACHE_DISABLE=1
cd /stage/src
patch -s -Np1 < /stage/flycastsa-patch-003-fix-sdl-controller.patch
sed -i "s/\-O[23]/-Ofast/" CMakeLists.txt
mkdir -p sa && cd sa
cmake .. -DCMAKE_TOOLCHAIN_FILE=$sdk/share/buildroot/toolchainfile.cmake -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_FLAGS_RELEASE="-DNDEBUG" -DCMAKE_CXX_FLAGS_RELEASE="-DNDEBUG" \
    -DCMAKE_C_FLAGS="-march=armv8-a+crc -mtune=cortex-a35 -ffile-prefix-map=/stage=." \
    -DCMAKE_CXX_FLAGS="-march=armv8-a+crc -mtune=cortex-a35 -ffile-prefix-map=/stage=. -Wno-error=array-bounds" \
    -DWITH_SYSTEM_ZLIB=ON -DUSE_HOST_SDL=ON -DUSE_PULSEAUDIO=OFF -DUSE_LIBAO=OFF -DUSE_BREAKPAD=OFF -DUSE_OPENMP=ON -DUSE_VULKAN=OFF -DUSE_GLES=ON
make -j16 flycast
aarch64-buildroot-linux-gnu-strip flycast'
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev,exec -v "$work:/work:ro,z" -v "$stage:/stage:rw,z" \
        "$(cat "$work/rootfs-container.iid")" sh -c "$code" > "$area/logs/build.log" 2>&1 ||
        { tail -25 "$area/logs/build.log"; echo "build failed (log $area/logs/build.log)" >&2; exit 1; }
    mkdir -p "$tree/$dest"
    cp "$stage/src/sa/flycast" "$tree/$dest/"
    cp "$stage/src/LICENSE" "$tree/$dest/" 2>/dev/null || :
    rm -rf "$stage"
    (cd "$tree/$dest" && find . -type f | sort | xargs -d '\n' sha256sum > "$area/SHA256SUMS")
    ls -la "$tree/$dest" ;;
*) sed -n '3,13p' "$0"; exit 2 ;;
esac
