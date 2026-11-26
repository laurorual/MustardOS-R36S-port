#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # the container script expands its own variables
# M3c: libretro cores for muxretro, cross-built with the Buildroot SDK.
#
#   build-cores.sh fetch [NAME...]   network: shallow clone of the pinned
#                                    commit (+ submodules) -> reproducible
#                                    tarball in build/m3c/cores/cache; checks
#                                    or prints its SHA256
#   build-cores.sh build [NAME...]   offline, in the phase4-rootfs container:
#                                    unpack, make, copy the .so to
#                                    build/m3c/cores/out (+ SHA256SUMS);
#                                    ppsspp also its system assets
#                                    (out/ppsspp-assets)
#   CORE_DEBUG=1 build NAME          -g build for gdb: unstripped .so in
#                                    build/m3c/cores/debug, the stripped one
#                                    in debug/stripped (out/ untouched)
#
# NAME: a table row (default: all). Each line of
# the table: name repo commit tarball-sha256 output-so license.
# Patches for a row: port/patches/cores/NAME/*.patch (git apply).
set -euo pipefail
export LC_ALL=C
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work=$repo/build/phase4 area=$repo/build/m3c/cores
cache=$area/cache out=$area/out
mkdir -p "$cache" "$out" "$area/logs"
table() {
    cat <<'EOF'
snes9x2005 https://github.com/libretro/snes9x2005 a79dfe9047e7fec58808aefe48ad2bf499c7af11 180a70f1dab01113418b41bd7a7cc4a639b6f3fa8b45bae9eb0ca8d5c58e59be snes9x2005_plus_libretro.so non-commercial(snes9x)
gpsp https://github.com/libretro/gpsp 5819380c2ffb0900219d700a382ee68c464ebb99 9a2f10b490d569cec7e08d62157dfaa1e8abef6a71384716d5031d04cc804657 gpsp_libretro.so GPL-2.0
picodrive https://github.com/libretro/picodrive 1890c2932234c9d30f4cd3851d02228baae8f09e 85fed6169938d1321dd43ef7d58a505ac482439bbdca3ff98570b3259b4cd8cb picodrive_libretro.so non-commercial(picodrive)
pcsx_rearmed https://github.com/libretro/pcsx_rearmed 7b0e8f8fadfbce3d170d195b9d9eecaabfa08c8e b7856066f7cb2e023192cb2aa72aeb096848ccfeb3e947d128bec5c08dc47dbb pcsx_rearmed_libretro.so GPL-2.0
stella2014 https://github.com/libretro/stella2014-libretro 7d1361e407e63f29e52892655069e5fb4096e691 b00e898f3bbe95802b3a7ad7c64de4f7dd9714a936e2f32fb2c4d8e30f17fbf9 stella2014_libretro.so GPL-2.0
prosystem https://github.com/libretro/prosystem-libretro 8a88014287c7a01cd568067e5a557d0a2b2a051f 38e633de20a4fe1f40a8067fd1228cc145a667312eb0508a7a267c9bd67fdf34 prosystem_libretro.so GPL-2.0
handy https://github.com/libretro/libretro-handy bc55d462f0b2d6b073ea93dc552ebd73cec60fd1 ef78a0130dac48525971cdfc573e1dcc3c317fb19791328fad01cac26cad8bc3 handy_libretro.so Zlib
pce_fast https://github.com/libretro/beetle-pce-fast-libretro 2de1ce1c3f237b161c126c54ba407990bb86d1e9 dbf7bff0662d832f62fc02089dd07c052232ddcebf491e904d0286a8ad44442b mednafen_pce_fast_libretro.so GPL-2.0
ngp https://github.com/libretro/beetle-ngp-libretro a50d5ac288a81f2104ddf43195a4efdd15c72227 3c06ba341e65483d5d778b086d49a0cd690c2d26b6d4ab5e922da6c213700935 mednafen_ngp_libretro.so GPL-2.0
wswan https://github.com/libretro/beetle-wswan-libretro 4b01295838ea89e3f1355bbe4cb5cf98aa6108cd e03d534ca36480ab1256007c6c0906da7943c9c37e63cb5897eadc4b0b8cd09d mednafen_wswan_libretro.so GPL-2.0
bluemsx https://github.com/libretro/blueMSX-libretro e3086eb5d36d77fa11704cf53dc176686e70127d 44d1499be894d699c679d095c09bd33a25ccf01bc032f2416ddc4e02842d2b0f bluemsx_libretro.so GPL-2.0
gearcoleco https://github.com/drhelius/Gearcoleco 8e86678387d0818e87a5b437d74390bf2ad82596 427fc6acd3a74fadd35b94df6f9697ee3f1c418dd6a6f7ef391e9b4e1d2189c9 platforms/libretro/gearcoleco_libretro.so GPL-3.0
gearsystem https://github.com/drhelius/Gearsystem 4b3b1b266e536848ab23b8733f783ae17f0126a6 f5d73da9620112a13990e6f0424cc636efbfa83145925723494ee6eae74be2a3 platforms/libretro/gearsystem_libretro.so GPL-3.0
pokemini https://github.com/libretro/PokeMini 132111b76343559860532a1ccc094f93f1ed5650 8fade789e8990d4066e9c77a714c9728bfbbf8bada46de5415c955191be249a5 pokemini_libretro.so GPL-3.0
fbneo https://github.com/libretro/FBNeo 12ec3ca2de7e5677d03b533c12cd9395a28212b0 0d47a639357e464623b4af4d91d946e2667a50bb826972f39344d890d4d06cd2 src/burner/libretro/fbneo_libretro.so non-commercial(fbneo)
mame2003_plus https://github.com/libretro/mame2003-plus-libretro dce2e9a2ef1ccdca174b1ab870f29bd2fed1a97b 00c3ce1b2a07393581fe0e9d245d6a0cbeb353356833e33191a8f75afe7964d6 mame2003_plus_libretro.so non-commercial(mame)
mupen64plus_next https://github.com/libretro/mupen64plus-libretro-nx 15bada85906593376e8fd697f1b0b3af3a20f512 62fb1629e12283f5eb9ddd951285eae5a6743e5a67b08c4857198ebc3aec2686 mupen64plus_next_libretro.so GPL-2.0
dosbox_pure https://github.com/libretro/dosbox-pure e39497e7c2a32c67c26e6598dd14f6d58c384bfd 37652b8c45d1ef176c1eecbbb6b2c5cb9444bd7d3e0cffb803006e183a6a882b dosbox_pure_libretro.so GPL-2.0
flycast https://github.com/libretro/flycast 328a768ab56b84623974b935b20d5a518265ba4e 3119db6b76cbbdceee304dc8b9f39fc1b9dff64c8aa5e4054068c717d1c4c565 parallel_dc_libretro.so GPL-2.0
ppsspp https://github.com/hrydgard/ppsspp fa50bb1976065c4f8b1b47af227d367fe9771555 8e8c50a3f7f5d40c9ac4207ce2dc4df1107ed97d9494b14c64ab9602df2b44a2 b/lib/ppsspp_libretro.so GPL-2.0
flycast2 https://github.com/flyinghead/flycast 5aa091fde632fb332c8d8c34e280d62dc951954c 6b39696378b3662c95a22c31790f54665f817cf741175c63309351c4ca8401a5 b/flycast_libretro.so GPL-2.0
ppsspp2021 https://github.com/hrydgard/ppsspp ce0a45cf0fcdd5bebf32208b9998f68dfc1107b7 e212d1389dcac45d4835db97a510e425e4768a4775c93d30c69a02e2324bbdae PPSSPPSDL GPL-2.0
melonds https://github.com/libretro/melonds 4081e8358e66f1ea11879560be6b813dfeaab75a cc4b9d3290e4c829981858d1f0278d8f12d183bebf1b06825ea606ce4f02a707 melonds_libretro.so GPL-3.0
flycast2022 https://github.com/libretro/parallel-dc 4c293f306bc16a265c2d768af5d0cea138426054 235422df11e9cf3d5d6eb45dfd69e1b21fd5665ca40777cd833b75327857869b flycast2022_libretro.so GPL-2.0
yabasanshiro https://github.com/libretro/yabause 09ed8e5b2e97e7a848ea2514545c34c7b809e399 6b8f29e7754143971c5db22fcdaafb8ad0ce237a04bb53fd1f71a959403d6cab yabause/src/libretro/yabasanshiro_libretro.so GPL-2.0
gambatte https://github.com/libretro/gambatte-libretro 77f2567d718b8973d02caa2daa8dce4953faf811 bf3829f52464d9c61c636b30eee7b5af7fd4e2526d584287a12cb6d191398e70 gambatte_libretro.so GPL-2.0
fceumm https://github.com/libretro/libretro-fceumm ac0d00a7fc01166f84c7bac01d1084ebfd2b865e ffe8948ad138dc11fb523c05fe678b2e3c0b2b25bcde2f78fd82743ca433efd3 fceumm_libretro.so GPL-2.0
picante8 https://github.com/MustardOS/picante8 86236842fd65500544fba0cf705ca35a379604d3 abf47ac1f82c1802f305ed540b871a063bb148ecf05892cbdd24596d8dadd054 picante8_libretro.so GPL-3.0
fake08 https://github.com/jtothebell/fake-08 814991a2571ad3970e386cef48f3b148aa1c27b9 120cd07b26c8e7264bac4973360314cde2672e6b862b4d4a0050eceb452a024c platform/libretro/fake08_libretro.so MIT
EOF
}
# make invocation per core (inside the container, in the source dir)
make_cmd() {
    case $1 in
        snes9x2005) echo 'make -j4 platform=unix USE_BLARGG_APU=1' ;;
        gpsp) echo 'make -j4 platform=arm64' ;;
        picodrive) echo 'make -j4 -f Makefile.libretro platform=aarch64' ;;
        pcsx_rearmed) echo 'make -j4 -f Makefile.libretro platform=unix ARCH=arm64 DYNAREC=ari64 BUILTIN_GPU=neon HAVE_PHYSICAL_CDROM=0' ;;
        # M6 (fps verdicts in milestones.md)
        stella2014|prosystem|handy|pce_fast|ngp|wswan|pokemini) echo 'make -j8 platform=unix' ;;
        bluemsx) echo 'make -j8 -f Makefile.libretro platform=unix' ;;
        gearcoleco|gearsystem) echo 'make -j8 -C platforms/libretro platform=unix' ;;
        fbneo) echo 'make -j8 -C src/burner/libretro platform=unix' ;;
        mame2003_plus) echo 'make -j8 platform=unix' ;;
        # N64: GLES3 through muxretro's hw render, aarch64 dynarec (the unix
        # rule picks the dynarec from the build host's uname -m). M7: the GLES2
        # build crashed in GLideN64's BufferedDrawer (Mali advertises
        # GL_EXT_buffer_storage, glMapBufferRange returned NULL in the 2.0
        # context); the Mali-G31 has GLES 3.2.
        mupen64plus_next) echo 'make -j8 platform=unix GLES3=1 FORCE_GLES3=1 ARCH=aarch64 WITH_DYNAREC=aarch64 HAVE_PARALLEL_RSP=0 HAVE_THR_AL=1 LLE=0' ;;
        # its unix rule picks CPU flags from the build host (uname -m)
        dosbox_pure) echo 'make -j8 platform=unix CPUFLAGS="-DPAGESIZE=4096 -mcpu=cortex-a35"' ;;
        # M8 (decision 20): GLES3 through muxretro's hw render, CMake from the
        # Buildroot SDK with its toolchain file
        # libretro/flycast is the Makefile fork; its RK3326-class platform
        flycast) echo 'make -j8 platform=arm64_cortex_a53_gles2 AS="$CC"' ;; # its .S go through ASFLAGS = gcc flags
        # M8 (M8 T3, decision 23: the fastest emulator): flyinghead's
        # Flycast v2.7 (the upstream libretro/flycast is now the parallel_dc
        # fork, which hangs at boot here), GLES3, arm64 dynarec
        flycast2) echo 'mkdir -p b && (cd b && $sdk/bin/cmake .. -DCMAKE_TOOLCHAIN_FILE=$sdk/share/buildroot/toolchainfile.cmake -DCMAKE_BUILD_TYPE=Release -DLIBRETRO=ON -DUSE_GLES=ON -DUSE_VULKAN=OFF -DUSE_OPENMP=ON && make -j8 flycast_libretro)' ;;
        # M8 (M8 T3 8: Power Stone 2 unplayable on v2.7): the libretro Flycast
        # dArkOS ships (April 2022, its goadvance platform: LOW_END/LOW_RES
        # defaults, arm64 dynarec), tuned for the A35 instead of A55; no
        # OpenMP (the SDK has no libgomp)
        flycast2022) echo 'sed -i "s/-mtune=cortex-a55 -mcpu=cortex-a55/-mcpu=cortex-a35/; s/ -ggdb3 -fno-omit-frame-pointer//" Makefile && make -j8 platform=goadvance TARGET_NAME=flycast2022 HAVE_OPENMP=0 AS="$CC"' ;;
        ppsspp) echo 'mkdir -p b && (cd b && $sdk/bin/cmake .. -DCMAKE_TOOLCHAIN_FILE=$sdk/share/buildroot/toolchainfile.cmake -DCMAKE_BUILD_TYPE=Release -DLIBRETRO=ON -DUSING_GLES2=ON -DUSING_EGL=OFF -DUSING_FBDEV=OFF -DVULKAN=OFF -DUSING_X11_VULKAN=OFF -DUSE_WAYLAND_WSI=OFF -DUSE_DISCORD=OFF -DUSE_MINIUPNPC=OFF -DUSE_FFMPEG=ON -DUSE_SYSTEM_FFMPEG=OFF -DARM64=ON -DUNITTEST=OFF -DHEADLESS=OFF && make -j8 ppsspp_libretro)' ;;
        melonds) echo 'make -j8 platform=odroidgoa' ;;
        yabasanshiro) echo 'make -j8 -C yabause/src/libretro platform=arm64_cortex_a53_gles3' ;;
        # M9 (licences): the Phase 4 GB/NES builds (build-phase4-gb-core.py,
        # build-phase4-nes-core.py) moved here, same commits and options
        gambatte) echo 'make -j8 -f Makefile.libretro platform=unix HAVE_NETWORK=0 VIDEO_RGB565=1' ;;
        fceumm) echo 'make -j8 -f Makefile.libretro platform=unix HAVE_HDPACK=0 HAVE_NTSC=0 WANT_32BPP=0' ;;
        # M12: PICO-8 (muOS's default Picante8, MustardOS; FAKE-08 as the
        # second libretro core)
        picante8) echo 'make -j8 platform=unix' ;;
        fake08) echo 'make -j8 -C platform/libretro platform=unix' ;;
    esac
}
# T1: every undefined dynamic symbol must be defined by the target's libc,
# libm or ld.so (M6: also libstdc++, libgcc_s, libpthread, libdl, librt, libz
# for the C++ cores) (M3c: pcsx_rearmed once linked cdrom.c without dir_list.c).
check_symbols() { # SO
    local rel=$work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-readelf
    local t=$repo/build/m3a/output/target missing
    missing=$(comm -23 \
        <("$rel" --dyn-syms -W "$1" | awk '$7 == "UND" && $5 == "GLOBAL" && $8 != "" {sub(/@.*/, "", $8); print $8}' | sort -u) \
        <(for l in "$t/lib/libc.so.6" "$t/lib/libm.so.6" "$t/lib/ld-linux-aarch64.so.1" \
                   "$t/usr/lib/libstdc++.so.6" "$t/lib/libgcc_s.so.1" "$t/lib/libpthread.so.0" \
                   "$t/lib/libdl.so.2" "$t/lib/librt.so.1" "$t/usr/lib/libz.so.1" "$t/usr/lib/libmali.so.1"; do
              [ -e "$l" ] || l=$t/usr/lib/${l##*/}
              "$rel" --dyn-syms -W "$l" | awk '$7 != "UND" && $8 != "" {sub(/@.*/, "", $8); print $8}'; done | sort -u))
    [ -z "$missing" ] || { echo "$(basename "$1"): unresolved symbols: $(echo "$missing" | tr '\n' ' ')" >&2; return 1; }
}
mode=${1:-}; shift || :
names=("$@"); [ ${#names[@]} -gt 0 ] || mapfile -t names < <(table | cut -d' ' -f1)
row() { table | awk -v n="$1" '$1 == n' | grep . || { echo "unknown core $1" >&2; exit 2; }; }

case "$mode" in
fetch)
    for n in "${names[@]}"; do
        read -r _ url commit want _ _ < <(row "$n")
        tarball=$cache/$n-$commit.tar
        if [ ! -s "$tarball" ]; then
            tmp=$(mktemp -d "$area/fetch.XXXXXX")
            git -C "$tmp" init -q src
            git -C "$tmp/src" fetch -q --depth 1 "$url" "$commit"
            git -C "$tmp/src" checkout -q FETCH_HEAD
            # M6: mupen64plus-nx has a gitlink without a .gitmodules file
            # (the paraLLEl RSP's gnulib, not built): nothing to init then
            git -C "$tmp/src" submodule -q update --init --recursive --depth 1 || [ ! -e "$tmp/src/.gitmodules" ]
            tar -C "$tmp" --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner \
                --exclude=.git --exclude=.git/* -cf "$tarball" src
            rm -rf "$tmp"
        fi
        got=$(sha256sum "$tarball" | cut -d' ' -f1)
        if [ "$want" = - ]; then echo "$n $got (not pinned yet)"
        elif [ "$got" = "$want" ]; then echo "$n ok $got"
        else echo "$n SHA256 MISMATCH $got != $want" >&2; exit 1; fi
    done ;;
build)
    for n in "${names[@]}"; do
        read -r _ _ commit want so _ < <(row "$n")
        tarball=$cache/$n-$commit.tar
        [ -s "$tarball" ] || { echo "$n: run fetch first" >&2; exit 1; }
        [ "$want" = - ] || [ "$(sha256sum "$tarball" | cut -d' ' -f1)" = "$want" ] || { echo "$n: tarball SHA256 mismatch" >&2; exit 1; }
        stage=$area/stage-$n; rm -rf "$stage"; mkdir -p "$stage"
        tar -C "$stage" -xf "$tarball"
        # port/patches/cores/NAME/*.patch (M8), in name order; the ceiling
        # keeps git from finding this repository above build/ (it would
        # skip every path then)
        for p in "$repo/port/patches/cores/$n"/*.patch; do
            [ -e "$p" ] || continue
            GIT_CEILING_DIRECTORIES=$stage git -C "$stage/src" apply "$p" || { echo "$n: $(basename "$p") does not apply" >&2; exit 1; }
        done
        code='sdk=/work/graphics-config/output/host t=$sdk/bin/aarch64-buildroot-linux-gnu-
export CC=${t}gcc CXX=${t}g++ AR=${t}ar LD=${t}gcc STRIP=${t}strip CROSS_COMPILE=$t
export CFLAGS="-O2 -mcpu=cortex-a35 -fstack-protector-strong -ffile-prefix-map=/stage=.'"${CORE_DEBUG:+ -g}"'" CXXFLAGS="-O2 -mcpu=cortex-a35 -fstack-protector-strong -ffile-prefix-map=/stage=.'"${CORE_DEBUG:+ -g}"'"
export LDFLAGS="-Wl,-z,relro,-z,now"
export CCACHE_DISABLE=1 # the SDK toolchain file wraps ccache; its dir is read-only here
cd /stage/src
'"$(make_cmd "$n")"'
'"${CORE_DEBUG:+cp \"$so\" /stage/unstripped.so}"'
${t}strip --strip-unneeded '"$so"''
        podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
            --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:ro,z" -v "$stage:/stage:rw,z" \
            "$(cat "$work/rootfs-container.iid")" sh -eu -c "$code" > "$area/logs/$n.log" 2>&1 ||
            { tail -20 "$area/logs/$n.log"; echo "$n: build failed (log $area/logs/$n.log)" >&2; exit 1; }
        b=${so##*/}
        if [ -n "${CORE_DEBUG:-}" ]; then # gdb symbols for a core dump; never shipped
            mkdir -p "$area/debug"; cp "$stage/unstripped.so" "$area/debug/$b"
            out=$area/debug/stripped; mkdir -p "$out"
        fi
        cp "$stage/src/$so" "$out/$b"
        if [ "$n" = ppsspp ]; then # M8: what the libretro core reads from system/PPSSPP
            rm -rf "$out/ppsspp-assets"; mkdir -p "$out/ppsspp-assets"
            (cd "$stage/src/assets" && cp -r --parents flash0/font ppge_atlas.zim ppge_atlas.meta \
                compat.ini knownfuncs.ini langregion.ini "$out/ppsspp-assets/")
        fi
        rm -rf "$stage"
        check_symbols "$out/$b" || exit 1
        echo "$n built $(sha256sum "$out/$b" | cut -c1-16) $(du -h "$out/$b" | cut -f1)"
    done
    (cd "$out" && sha256sum ./*.so > SHA256SUMS) ;;
*) sed -n '3,14p' "$0"; exit 2 ;;
esac
