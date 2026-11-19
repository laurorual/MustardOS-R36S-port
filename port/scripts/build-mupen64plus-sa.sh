#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # the container script expands its own variables
# M7 (user exception to decision 14, 2026-11-19): standalone Mupen64Plus
# for N64, cross-built with the Buildroot SDK like build-cores.sh.
#
#   build-mupen64plus-sa.sh fetch [NAME...]  network: pinned commit ->
#                            reproducible tarball in build/m7/mupen64plus/cache
#                            (prints or checks its SHA256)
#   build-mupen64plus-sa.sh build            offline, in the phase4-rootfs
#                            container: every part -> build/m7/mupen64plus/
#                            tree/opt/muos/share/emulator/mupen64plus/
#                            (mupen64plus, libmupen64plus.so.2.0.0,
#                            plugins/, configs/ = the core's data files)
#
# Parts (2.6.0 releases; GLideN64 has no recent release tag): the core
# with the aarch64 new dynarec, ui-console (SDL2), audio-sdl (no
# speex/libsamplerate: the SDL resampler), input-sdl, rsp-hle, video-rice
# (GLES2) and GLideN64 (GLES3 + EGL: the M7 GLES2 libretro build crashed in
# BufferedDrawer on this Mali; no hi-res texture packs). Port patches:
# port/patches/mupen64plus/ (0001: a state saved on Stop, MUPEN_AUTOSAVE).
set -euo pipefail
export LC_ALL=C
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work=$repo/build/phase4 area=$repo/build/m7/mupen64plus
cache=$area/cache tree=$area/tree
dest=opt/muos/share/emulator/mupen64plus
mkdir -p "$cache" "$area/logs"
table() {
    cat <<'EOF'
core https://github.com/mupen64plus/mupen64plus-core b0d68c20f49b8f833afa21450e0e8874c87c13c4 c7ada52f7a69ab43e5eb910848fd3f7347794bb0f32f2b7310a928e867293940 GPL-2.0
ui-console https://github.com/mupen64plus/mupen64plus-ui-console 1a68327fddda71f1acbad8a63ef04288b1887d19 463b4eca066fed68d40f53b4970247166ff8632635a14d6ee60bb4ec445a8d8e GPL-2.0
audio-sdl https://github.com/mupen64plus/mupen64plus-audio-sdl 6c2c3f8ae10b7f0f6dfe06f45ca7ca598a6b659a d2c89042baa84410ef7eafbbc140b1981a39ec079b778b54dc6ac8c79f78ea2f GPL-2.0
input-sdl https://github.com/mupen64plus/mupen64plus-input-sdl f2ca3839415d45a547f79d21177dfe15a0ce6d8c a95d32c1119a8dd8c3b84bba2839d50516398c1610814c00d4d191ee261724dc GPL-2.0
rsp-hle https://github.com/mupen64plus/mupen64plus-rsp-hle 2798e65d6fc89d89aace0b0d779af6406809b940 2363133ab8694dc6a1143a4435db3bec5be189bdf1c7d6a54c4d29a89e96fe83 GPL-2.0
video-rice https://github.com/mupen64plus/mupen64plus-video-rice fcf00779f08a9503ef30d26422f6b0350684820d 6d06ddef6e69f2c3062e80e155df5d35f91ac41534d3ba07f82f24cb454fa396 GPL-2.0
gliden64 https://github.com/gonetz/GLideN64 a04081ad6a966a9413bea63a55f502e0dc98bb18 d5287d608fd74c42eb5fb0e4c0b08e6504faab11ea4b006ebaa80540c88aa42a GPL-2.0
EOF
}
mode=${1:-}; shift || :
names=("$@"); [ ${#names[@]} -gt 0 ] || mapfile -t names < <(table | cut -d' ' -f1)
row() { table | awk -v n="$1" '$1 == n' | grep . || { echo "unknown part $1" >&2; exit 2; }; }
tarball() { read -r _ _ commit _ _ < <(row "$1"); echo "$cache/$1-$commit.tar"; }

case "$mode" in
fetch)
    for n in "${names[@]}"; do
        read -r _ url commit want _ < <(row "$n")
        t=$(tarball "$n")
        if [ ! -s "$t" ]; then
            tmp=$(mktemp -d "$area/fetch.XXXXXX")
            git -C "$tmp" init -q "$n"
            git -C "$tmp/$n" fetch -q --depth 1 "$url" "$commit"
            git -C "$tmp/$n" checkout -q FETCH_HEAD
            tar -C "$tmp" --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner \
                --exclude=.git -cf "$t" "$n"
            rm -rf "$tmp"
        fi
        got=$(sha256sum "$t" | cut -d' ' -f1)
        if [ "$want" = - ]; then echo "$n $got (not pinned yet)"
        elif [ "$got" = "$want" ]; then echo "$n ok"
        else echo "$n SHA256 MISMATCH $got != $want" >&2; exit 1; fi
    done ;;
build)
    stage=$area/stage; rm -rf "$stage" "$tree"; mkdir -p "$stage/out"
    while read -r n _ commit want _; do
        t=$cache/$n-$commit.tar
        [ -s "$t" ] || { echo "$n: run fetch first" >&2; exit 1; }
        [ "$want" = - ] || [ "$(sha256sum "$t" | cut -d' ' -f1)" = "$want" ] || { echo "$n: SHA256 mismatch" >&2; exit 1; }
        tar -C "$stage" -xf "$t"
    done < <(table)
    # GLideN64 writes Revision.h with git; the tarball has no history
    read -r _ _ glcommit _ _ < <(row gliden64)
    printf '#define PLUGIN_REVISION "%s"\n#define PLUGIN_REVISION_W L"%s"\n' \
        "${glcommit:0:7}" "${glcommit:0:7}" > "$stage/gliden64/src/Revision.h"
    code='set -eu
sdk=/work/graphics-config/output/host t=$sdk/bin/aarch64-buildroot-linux-gnu-
sys=$sdk/aarch64-buildroot-linux-gnu/sysroot
unset PKG_CONFIG_LIBDIR PKG_CONFIG_PATH
export PATH=$sdk/bin:$PATH PKG_CONFIG=$sdk/bin/pkg-config
# the Makefiles look for sdl2-config, which the SDK lacks
SDL_CFLAGS=$($PKG_CONFIG --cflags sdl2) SDL_LDLIBS=$($PKG_CONFIG --libs sdl2)
export SDL_CFLAGS SDL_LDLIBS
for p in /patches/*.patch; do patch -s -p1 -d /stage < "$p"; done
opt="-O2 -mcpu=cortex-a35 -fstack-protector-strong -ffile-prefix-map=/stage=."
mk="CROSS_COMPILE=$t HOST_CPU=aarch64 PKG_CONFIG=$PKG_CONFIG OPTFLAGS=-O2 PIC=1 V=1"
export CFLAGS="$opt" CXXFLAGS="$opt" LDFLAGS="-Wl,-z,relro,-z,now"
o=/stage/out
make -C /stage/core/projects/unix -j8 all $mk NEW_DYNAREC=1 USE_GLES=1 OSD=0 NO_ASM=0 VULKAN=0
cp /stage/core/projects/unix/libmupen64plus.so.2.0.0 $o/
mkdir -p $o/configs && cp /stage/core/data/* $o/configs/
make -C /stage/ui-console/projects/unix -j8 all $mk APIDIR=/stage/core/src/api \
    COREDIR=./ PLUGINDIR=./plugins SHAREDIR=./configs
cp /stage/ui-console/projects/unix/mupen64plus $o/
mkdir -p $o/plugins
make -C /stage/audio-sdl/projects/unix -j8 all $mk APIDIR=/stage/core/src/api NO_SRC=1 NO_SPEEX=1 NO_OSS=1
make -C /stage/input-sdl/projects/unix -j8 all $mk APIDIR=/stage/core/src/api
make -C /stage/rsp-hle/projects/unix -j8 all $mk APIDIR=/stage/core/src/api
make -C /stage/video-rice/projects/unix -j8 all $mk APIDIR=/stage/core/src/api USE_GLES=1
cp /stage/audio-sdl/projects/unix/mupen64plus-audio-sdl.so /stage/input-sdl/projects/unix/mupen64plus-input-sdl.so \
   /stage/rsp-hle/projects/unix/mupen64plus-rsp-hle.so /stage/video-rice/projects/unix/mupen64plus-video-rice.so $o/plugins/
cp /stage/input-sdl/data/InputAutoCfg.ini /stage/video-rice/data/RiceVideoLinux.ini $o/configs/
mkdir -p /tmp/gl && cd /tmp/gl
cmake /stage/gliden64/src -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=$sdk/share/buildroot/toolchainfile.cmake \
    -DMUPENPLUSAPI=On -DMUPENPLUSAPI_GLIDENUI=Off -DGLES3=On -DEGL=On -DNEON_OPT=On -DCRC_ARMV8=On \
    -DUSE_SYSTEM_LIBS=On -DNOHQ=On -DMUPENPLUS_API_PATH=/stage/core/src/api \
    -DCMAKE_C_FLAGS="$opt" -DCMAKE_CXX_FLAGS="$opt"
make -j8
cp plugin/Release/mupen64plus-video-GLideN64.so $o/plugins/
cp /stage/gliden64/ini/GLideN64.custom.ini $o/configs/
for f in $o/mupen64plus $o/libmupen64plus.so.2.0.0 $o/plugins/*.so; do ${t}strip --strip-unneeded $f; done'
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev,exec -v "$work:/work:ro,z" -v "$stage:/stage:rw,z" \
        -v "$repo/port/patches/mupen64plus:/patches:ro,z" "$(cat "$work/rootfs-container.iid")" sh -c "$code" > "$area/logs/build.log" 2>&1 ||
        { tail -25 "$area/logs/build.log"; echo "build failed (log $area/logs/build.log)" >&2; exit 1; }
    mkdir -p "$tree/$dest"
    cp -a "$stage/out/." "$tree/$dest/"
    rm -rf "$stage"
    (cd "$tree/$dest" && find . -type f | sort | xargs sha256sum > "$area/SHA256SUMS")
    du -sh "$tree/$dest"; grep -c . "$area/SHA256SUMS" ;;
*) sed -n '3,20p' "$0"; exit 2 ;;
esac
