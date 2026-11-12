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
# NAME: snes9x2005 gpsp picodrive pcsx_rearmed (default: all). Each line of
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
EOF
}
# make invocation per core (inside the container, in the source dir)
make_cmd() {
    case $1 in
        snes9x2005) echo 'make -j4 platform=unix USE_BLARGG_APU=1' ;;
        gpsp) echo 'make -j4 platform=arm64' ;;
        picodrive) echo 'make -j4 -f Makefile.libretro platform=aarch64' ;;
        pcsx_rearmed) echo 'make -j4 -f Makefile.libretro platform=unix ARCH=arm64 DYNAREC=ari64 BUILTIN_GPU=neon HAVE_PHYSICAL_CDROM=0' ;;
    esac
}
# T1: every undefined dynamic symbol must be defined by the target's libc,
# libm or ld.so (M3c: pcsx_rearmed once linked cdrom.c without dir_list.c).
check_symbols() { # SO
    local rel=$work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-readelf
    local t=$repo/build/m3a/output/target missing
    missing=$(comm -23 \
        <("$rel" --dyn-syms -W "$1" | awk '$7 == "UND" && $5 == "GLOBAL" && $8 != "" {sub(/@.*/, "", $8); print $8}' | sort -u) \
        <(for l in "$t/lib/libc.so.6" "$t/lib/libm.so.6" "$t/lib/ld-linux-aarch64.so.1"; do
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
            git -C "$tmp/src" submodule -q update --init --recursive --depth 1
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
        cp "$stage/src/$so" "$out/$so"
        rm -rf "$stage"
        check_symbols "$out/$so" || exit 1
        echo "$n built $(sha256sum "$out/$so" | cut -c1-16) $(du -h "$out/$so" | cut -f1)"
    done
    (cd "$out" && sha256sum ./*.so > SHA256SUMS) ;;
*) sed -n '3,14p' "$0"; exit 2 ;;
esac
