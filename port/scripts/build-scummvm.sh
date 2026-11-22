#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # the container script expands its own variables
# M8 item 5 (ScummVM, decision 17): ScummVM v2026.4.0 (the version
# dArkOSen ships as /opt/scummvm/scummvm) built from one source tree two
# ways, so the standalone and the libretro core can be compared on the
# device: both with the libretro port's "lite" engine list
# (backends/platform/libretro/lite_engines.list: the classic 2D adventure
# engines), software rendering (no OpenGL), MT-32 emulation, FLAC/Vorbis
# (CD audio tracks), zlib, PNG, FreeType, the virtual keyboard (M8f T3 4:
# typing save names; Select opens it in both, its packs in the extra
# path). dArkOSen's binary needs ~20 Debian libraries the rootfs does not have (libvpx, libFLAC, curl,
# speechd...), so it is not reused. libogg/libvorbis/FLAC are built static
# from pinned xiph tarballs for the standalone; the core uses the
# libretro port's own pinned libretro-deps/libretro-common clones.
#
#   build-scummvm.sh standalone   -> build/m8f/scummvm/tree/opt/muos/share/emulator/scummvm/scummvm
#   build-scummvm.sh libretro     -> build/m8f/scummvm/scummvm_libretro.so
# Inputs: build/scummvm-src (tag v2026.4.0, commit below; libretro deps
# fetched into backends/platform/libretro/deps at the commits pinned in
# its dependencies.mk), build/m8f/dl/*.tar.xz (sha256 below).
set -euo pipefail
export LC_ALL=C
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work=$repo/build/phase4 area=$repo/build/m8f/scummvm
src=$repo/build/scummvm-src src_commit=7d2709da5136866589f7602f5f5a7b17de03420e
dl=$repo/build/m8f/dl dest=opt/muos/share/emulator/scummvm
mkdir -p "$area/logs"
[ "$(git -C "$src" rev-parse HEAD)" = "$src_commit" ] || { echo "scummvm-src is not at $src_commit" >&2; exit 1; }
engines=$(grep -v '^\s*$' "$src/backends/platform/libretro/lite_engines.list" | paste -sd, -)
run() { # NAME CODE: run CODE in the rootfs SDK container, src mounted rw at /src
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev,exec -e ENGINES="$engines" \
        -v "$work:/work:ro,z" -v "$src:/src:rw,z" -v "$dl:/dl:ro,z" -v "$area:/out:rw,z" \
        "$(cat "$work/rootfs-container.iid")" sh -c 'set -eu
sdk=/work/graphics-config/output/host; sys=$sdk/aarch64-buildroot-linux-gnu/sysroot
export PATH=$sdk/bin:$PATH CCACHE_DISABLE=1 X=aarch64-buildroot-linux-gnu-
OPT="-O2 -march=armv8-a+crc -mtune=cortex-a35 -ffile-prefix-map=/src=."
'"$2" > "$area/logs/$1.log" 2>&1 ||
        { tail -25 "$area/logs/$1.log"; echo "$1 failed (log $area/logs/$1.log)" >&2; exit 1; }
}
case "${1:-}" in
standalone)
    for t in "libogg-1.3.5 c4d91be36fc8e54deae7575241e03f4211eb102afb3fc0775fbbc1b740016705" \
             "libvorbis-1.3.7 b33cc4934322bcbf6efcbacf49e3ca01aadbea4114ec9589d1b1e9d20f72954b" \
             "flac-1.4.3 6c58e69cd22348f441b861092b825e591d0b822e106de6eb0ee4d05d27205b70"; do
        read -r n h <<< "$t"
        [ "$(sha256sum "$dl/$n.tar.xz" | cut -d' ' -f1)" = "$h" ] || { echo "$n SHA256 mismatch" >&2; exit 1; }
    done
    run standalone '
d=/tmp/deps; mkdir -p $d /tmp/b; cd /tmp/b
for t in libogg-1.3.5 libvorbis-1.3.7 flac-1.4.3; do tar -xJf /dl/$t.tar.xz; done
common="--host=aarch64-buildroot-linux-gnu --prefix=$d --disable-shared --enable-static --with-pic"
(cd libogg-1.3.5 && CFLAGS="$OPT" ./configure $common && make -j16 install)
(cd libvorbis-1.3.7 && CFLAGS="$OPT" ./configure $common --with-ogg=$d --disable-examples --disable-docs && make -j16 install)
(cd flac-1.4.3 && CFLAGS="$OPT" ./configure $common --with-ogg=$d --disable-cpplibs --disable-programs \
    --disable-examples --disable-doxygen-docs --disable-xmms-plugin --disable-oggtest && make -j16 install)
rm -rf /tmp/sv; mkdir /tmp/sv; cd /src
git -c safe.directory=/src archive --format=tar HEAD | tar -C /tmp/sv -xf -
cd /tmp/sv
CXX=${X}g++ CXXFLAGS="$OPT" PKG_CONFIG_LIBDIR=$sys/usr/lib/pkgconfig PKG_CONFIG_SYSROOT_DIR=$sys \
./configure --host=aarch64-buildroot-linux-gnu --backend=sdl --enable-release --disable-debug \
    --enable-optimizations --with-sdl-prefix=$sys/usr --disable-all-engines --enable-engine=$ENGINES \
    --enable-vorbis --with-vorbis-prefix=$d --with-ogg-prefix=$d --enable-flac --with-flac-prefix=$d \
    --enable-zlib --enable-png --enable-freetype2 --enable-mt32emu --enable-vkeybd --disable-mad --disable-tremor \
    --disable-fluidsynth --disable-fluidlite --disable-timidity --disable-mpeg2 --disable-a52 --disable-theoradec \
    --disable-faad --disable-jpeg --disable-gif --disable-vpx --disable-sndio --disable-fribidi \
    --disable-libcurl --disable-sdlnet --disable-cloud --disable-tts --disable-discord --disable-updates \
    --disable-eventrecorder --disable-opengl-game --disable-opengl-game-shaders --disable-opengl-game-classic \
    --disable-detection-full --disable-lua --disable-imgui --disable-tinygl 2>&1 | tail -60
make -j16
${X}strip scummvm
mkdir -p /out/tree/'"$dest"'
cp scummvm /out/tree/'"$dest"'/
cp gui/themes/scummremastered.zip gui/themes/scummclassic.zip gui/themes/translations.dat /out/tree/'"$dest"'/ 2>/dev/null || :
cp backends/vkeybd/packs/vkeybd_default.zip backends/vkeybd/packs/vkeybd_small.zip /out/tree/'"$dest"'/
for f in dists/engine-data/*.dat; do case ${f##*/} in kyra.dat|lure.dat|queen.tbl|sky.cpt|drascula.dat|teenagent.dat|tony.dat|toon.dat|hugo.dat|cryo.dat|mort.dat|fonts.dat|macgui.dat|wintermute.zip) cp $f /out/tree/'"$dest"'/ ;; esac; done
cp COPYING /out/tree/'"$dest"'/ '
    du -sh "$area/tree/$dest"; ls -la "$area/tree/$dest" ;;
libretro)
    run libretro '
cd /src/backends/platform/libretro
make -j16 platform=unix BUILD_64BIT=1 LITE=1 FORCE_OPENGLNONE=1 NO_WIP=1 USE_LIBCO=0 \
    CC=${X}gcc CXX=${X}g++ AR="${X}ar cru" RANLIB=${X}ranlib \
    CFLAGS="$OPT" CXXFLAGS="$OPT" core
${X}strip scummvm_libretro.so
cp scummvm_libretro.so /out/'
    ls -la "$area/scummvm_libretro.so" ;;
*) sed -n '3,21p' "$0"; exit 2 ;;
esac
