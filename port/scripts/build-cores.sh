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
#                                    build/m3c/cores/out (+ SHA256SUMS)
#
# NAME: a table row (default: all). Each line of
# the table: name repo commit tarball-sha256 output-so license.
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
        # N64 trial: GLES2 through muxretro's hw render, aarch64 dynarec
        # (the unix rule picks the dynarec from the build host's uname -m)
        mupen64plus_next) echo 'make -j8 platform=unix GLES=1 FORCE_GLES=1 ARCH=aarch64 WITH_DYNAREC=aarch64 HAVE_PARALLEL_RSP=0 HAVE_THR_AL=1 LLE=0' ;;
        # its unix rule picks CPU flags from the build host (uname -m)
        dosbox_pure) echo 'make -j8 platform=unix CPUFLAGS="-DPAGESIZE=4096 -mcpu=cortex-a35"' ;;
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
        code='sdk=/work/graphics-config/output/host t=$sdk/bin/aarch64-buildroot-linux-gnu-
export CC=${t}gcc CXX=${t}g++ AR=${t}ar LD=${t}gcc STRIP=${t}strip CROSS_COMPILE=$t
export CFLAGS="-O2 -mcpu=cortex-a35 -fstack-protector-strong -ffile-prefix-map=/stage=." CXXFLAGS="-O2 -mcpu=cortex-a35 -fstack-protector-strong -ffile-prefix-map=/stage=."
export LDFLAGS="-Wl,-z,relro,-z,now"
cd /stage/src
'"$(make_cmd "$n")"'
${t}strip --strip-unneeded '"$so"''
        podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
            --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:ro,z" -v "$stage:/stage:rw,z" \
            "$(cat "$work/rootfs-container.iid")" sh -eu -c "$code" > "$area/logs/$n.log" 2>&1 ||
            { tail -20 "$area/logs/$n.log"; echo "$n: build failed (log $area/logs/$n.log)" >&2; exit 1; }
        b=${so##*/}
        cp "$stage/src/$so" "$out/$b"
        rm -rf "$stage"
        check_symbols "$out/$b" || exit 1
        echo "$n built $(sha256sum "$out/$b" | cut -c1-16) $(du -h "$out/$b" | cut -f1)"
    done
    (cd "$out" && sha256sum ./*.so > SHA256SUMS) ;;
*) sed -n '3,14p' "$0"; exit 2 ;;
esac
