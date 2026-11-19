#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M3d step 3: build muxretro from source with the port's patches.
#
#   build-muxretro.sh [build]   incremental build -> build/m3d/muxretro/tree/opt/muos/frontend/muxretro
#   build-muxretro.sh release   M6: the release build (TEST_IMAGE=0, its own
#                               tree src-release) linked against the release
#                               libraries of build-frontend-libs.sh release
#                               -> build/m3d/muxretro/release/opt/muos/frontend/muxretro
#   build-muxretro.sh clean     drop the patched trees (next build starts over)
#   build-muxretro.sh mkpatch NAME FILE...   write port/patches/muxretro/NAME
#                               from the edits in src (FILE relative to src;
#                               a file belongs to one patch only)
#
# Source: the Phase 4 provider tree (build/phase4/muxretro-provider/source,
# the source of the pinned muxretro cd67ce60...), reflinked to
# build/m3d/muxretro/src with port/patches/muxretro/*.patch applied (redone
# when the patch set changes). Built by the provider's own build-host.sh in
# the rootfs container against the M3a sysroot; the frontend libraries
# (libui, libmuxcom, ...) are the pinned ones in the M3a target. The image
# takes the result as the pinned input /opt/muos/frontend/muxretro
# (firmware-inputs.json); for a quick test, install it with
# `install-rootfs.sh --tree build/m3d/muxretro/tree opt/muos/frontend/muxretro`.
set -euo pipefail
shopt -s nullglob
repo=$(cd "$(dirname "$0")/../.." && pwd)
base=$repo/build/phase4/muxretro-provider/source
area=$repo/build/m3d/muxretro
src=$area/src stamp=$area/src.patches out=$area/tree/opt/muos/frontend
patches=$repo/port/patches/muxretro
iid=$(cat "$repo/build/phase4/rootfs-container.iid")
mkdir -p "$area" "$out" "$repo/build/logs"

prepare() { # [SRC STAMP]
    local want src=${1:-$src} stamp=${2:-$stamp}
    want=$(cat /dev/null "$patches"/*.patch | sha256sum | cut -d" " -f1)
    [ -d "$src" ] && [ "$(cat "$stamp" 2>/dev/null)" = "$want" ] && return 0
    rm -rf "$src" "$stamp"
    cp -a --reflink=always "$base" "$src"
    for p in "$patches"/*.patch; do
        [ -e "$p" ] || continue
        git -C "$src" apply --whitespace=nowarn "$p" || { echo "muxretro patch failed: $p" >&2; rm -rf "$src"; exit 1; }
    done
    echo "$want" > "$stamp"
}

# Buildroot's TARGET_CFLAGS for the M3a config (O2, FORTIFY 1); the
# toolchain wrapper adds SSP strong, PIE and full RELRO.
compile() { # TREE (under $area) LIBDIR (container path) OUT [TEST_IMAGE]
    local tree=$1 libdir=$2 dest=$3 t=${4:-1} host=build-host.sh
    flags='-D_LARGEFILE_SOURCE -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -O2 -g0 -D_FORTIFY_SOURCE=1'
    if [ "$t" = 0 ]; then
        host=build-host-release.sh
        sed 's/-DTEST_IMAGE=1 /-DTEST_IMAGE=0 -DMUOS_RELEASE /' "$area/$tree/build-host.sh" > "$area/$tree/$host"
        grep -q -- '-DTEST_IMAGE=0 ' "$area/$tree/$host" || { echo 'build-host.sh: no TEST_IMAGE flag' >&2; exit 1; }
    fi
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id --memory=6g --pids-limit=1024 --tmpfs /tmp:rw,nosuid,nodev,size=1g \
        -v "$repo/build/m3a:/m3a:ro,z" -v "$area:/w:rw,z" -v "$repo/build/m4c/frontend-libs/release:/rel:ro,z" -w /w "$iid" sh -euc '
        h=/m3a/output/host
        sysroot=$h/aarch64-buildroot-linux-gnu/sysroot
        PATH=$h/bin:$PATH
        sh /w/'"$tree/$host"' "$h/bin/aarch64-buildroot-linux-gnu-gcc" "$h/bin/aarch64-buildroot-linux-gnu-ar" \
            "$h/bin/pkg-config" "$sysroot" /w/'"$tree"' "'"$flags"'" "-L'"$libdir"'"
        ' > "$repo/build/logs/muxretro-build.log" 2>&1 || { tail -30 "$repo/build/logs/muxretro-build.log" >&2; exit 1; }
    mkdir -p "$dest"
    cp "$area/$tree/frontend/bin/muxretro" "$dest/muxretro.tmp" && mv "$dest/muxretro.tmp" "$dest/muxretro"
    grep -c ' warning: ' "$repo/build/logs/muxretro-build.log" | sed 's/^/muxretro: warnings=/'
    echo "muxretro: $(sha256sum "$dest/muxretro" | cut -c1-16) ($(stat -c %s "$dest/muxretro") bytes)"
}

case "${1:-build}" in
build)
    prepare
    compile src /m3a/output/target/opt/muos/frontend/lib "$out" ;;
release)
    [ -s "$repo/build/m4c/frontend-libs/release/opt/muos/frontend/lib/libmuxcom.so" ] ||
        { echo 'run build-frontend-libs.sh release first' >&2; exit 1; }
    prepare "$area/src-release" "$area/src-release.patches"
    compile src-release /rel/opt/muos/frontend/lib "$area/release/opt/muos/frontend" 0 ;;
clean) rm -rf "$src" "$stamp" "$area/src-release" "$area/src-release.patches" ;;
mkpatch)
    name=$2; shift 2
    { printf 'From: muOS R35S port\nSubject: [PATCH] %s\n\nSPDX-License-Identifier: GPL-3.0\n---\n' "${name%.patch}"
      for f in "$@"; do
          if [ -e "$base/$f" ]; then old=$base/$f lbl=a/$f; else old=/dev/null lbl=/dev/null; fi
          diff -u --label "$lbl" --label "b/$f" "$old" "$src/$f" || [ $? = 1 ]
      done
    } > "$patches/$name.tmp"
    mv "$patches/$name.tmp" "$patches/$name"
    # The tree already holds this content: keep it (no rebuild from scratch).
    cat /dev/null "$patches"/*.patch | sha256sum | cut -d" " -f1 > "$stamp"
    echo "wrote port/patches/muxretro/$name ($(grep -c '^@@' "$patches/$name") hunks)" ;;
*) sed -n '3,6p' "$0"; exit 2 ;;
esac
