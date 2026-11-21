#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M4c: build the muOS frontend libraries (libui, libmuxcom, libmuxmod,
# libplutosvg) from source with the port's frontend patches.
#
#   build-frontend-libs.sh [build]   incremental build -> build/m4c/frontend-libs/tree/opt/muos/frontend/lib/
#   build-frontend-libs.sh release   M6: the release build (TEST_IMAGE=0) of the
#                                    libraries and of muxfrontend, muhotkey and
#                                    mubattery -> build/m4c/frontend-libs/release/
#                                    opt/muos/frontend/ (muxretro: build-muxretro.sh
#                                    release)
#   build-frontend-libs.sh check     unpatched rebuild == the pinned libmuxmod.so
#   build-frontend-libs.sh clean     drop the patched tree (next build starts over)
#   build-frontend-libs.sh mkpatch NAME FILE...   write port/patches/frontend/NAME
#                               from the edits in src (FILE relative to src,
#                               e.g. frontend/module/muxconnect.c)
#
# Source: the Phase 4 C65 source (build/phase4/frontend-libs/source: the
# frontend at the pinned commit with patches 0003 and 0006, mojibake, the
# library makefile), reflinked to build/m4c/frontend-libs/src with
# port/patches/frontend/*.patch applied (redone when the patch set changes).
# Built with the Phase 4 graphics toolchain and sysroot (graphics-config)
# at the C65 build path, so an unpatched build reproduces the pinned
# libmuxmod.so byte for byte (`check`; libui and libmuxcom link their
# objects in `find` order, which differs on the reflinked tree). The
# patches must not change the lang/config/device structs in libmuxcom:
# they are shared with muxfrontend and muxretro, which are not rebuilt here.
# libmuxmod.so is always taken; libmuxcom.so too once a patch touches
# frontend/common/ (M4g: function bodies only). Its unpatched rebuild has
# the pinned symbols (names, types, sizes) and only differs in link order
# (`check`).
# M4g: also builds the upstream tool musftpjail (the SFTP jail, unchanged
# source, upstream's tool flags) into tree/opt/muos/frontend/musftpjail.
# M8: and upstream's libmucursor.so (hides the SDL cursor of standalone
# emulators) into tree/opt/muos/frontend/lib.
# The image takes the result as a pinned input (firmware-inputs.json);
# for a quick test: `install-rootfs.sh --tree build/m4c/frontend-libs/tree
# opt/muos/frontend/lib/libmuxmod.so`.
set -euo pipefail
shopt -s nullglob
repo=$(cd "$(dirname "$0")/../.." && pwd)
base=$repo/build/phase4/frontend-libs/source
gfx=$repo/build/phase4/graphics-config
area=$repo/build/m4c/frontend-libs
src=$area/src stamp=$area/src.patches out=$area/tree/opt/muos/frontend/lib
tool_out=$area/tree/opt/muos/frontend
patches=$repo/port/patches/frontend mk=$repo/port/packaging/phase4-frontend-libs.mk
rel=$area/release/opt/muos/frontend
iid=$(cat "$repo/build/phase4/rootfs-container.iid")
log=$repo/build/logs/frontend-libs-build.log
# The C65 package build directory (debug paths, -ffile-prefix-map=/work=.).
site=/work/frontend-libs/build.84o1r4aj/output/build/muos-frontend-libs-1
mkdir -p "$area" "$out" "$patches" "$repo/build/logs"

prepare() { # [PATCHDIR]: a patch set other than the port's (check: none)
    local dir=${1:-$patches} want
    want=$dir:$(cat /dev/null "$dir"/*.patch | sha256sum | cut -d" " -f1)
    [ -d "$src" ] && [ "$(cat "$stamp" 2>/dev/null)" = "$want" ] && return 0
    rm -rf "$src" "$stamp"
    cp -a --reflink=always "$base" "$src"
    for p in "$dir"/*.patch; do
        git -C "$src" apply --whitespace=nowarn "$p" || { echo "frontend patch failed: $p" >&2; rm -rf "$src"; exit 1; }
    done
    echo "$want" > "$stamp"
}
# M6: the library makefile is kept in Git (TEST_IMAGE switch, executables).
sync_mk() { cmp -s "$mk" "$src/frontend/phase4-frontend-libs.mk" || cp "$mk" "$src/frontend/phase4-frontend-libs.mk"; }

compile() { # [TEST_IMAGE [MAKE GOAL...]]
    local t=${1:-1}; shift || :
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id --memory=6g --pids-limit=1024 --tmpfs /tmp:rw,nosuid,nodev,size=1g \
        -v "$gfx/output/host:/work/graphics-config/output/host:ro,z" -v "$src:$site:rw,z" -w "$site" "$iid" sh -euc '
        h=/work/graphics-config/output/host
        export MAKEFLAGS=TEST_IMAGE='"$t"'
        sh '"$site"'/build-libs.sh "$h/bin/aarch64-buildroot-linux-gnu-gcc" "$h/bin/aarch64-buildroot-linux-gnu-ar" \
            "$h/bin/pkg-config" "$h/aarch64-buildroot-linux-gnu/sysroot" '"$site"' "-O2 -mcpu=cortex-a35" ""
        if [ -n "'"$*"'" ]; then
            export PKG_CONFIG_LIBDIR="$h/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$h/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
            export PKG_CONFIG_SYSROOT_DIR="$h/aarch64-buildroot-linux-gnu/sysroot" PATH="$h/bin:$PATH"
            make -C '"$site"'/frontend -f phase4-frontend-libs.mk -j8 CC="$h/bin/aarch64-buildroot-linux-gnu-gcc" \
                PKG_CONFIG="$h/bin/pkg-config" CFLAGS="-O2 -mcpu=cortex-a35" LDFLAGS= '"$*"'
        fi
        ' > "$log" 2>&1 || { tail -30 "$log" >&2; exit 1; }
}

# Upstream's $(TOOLS) rule with common.mk's BASE/STRICT_CFLAGS and
# BIN_LDFLAGS (no LTO, no rpath: the tool links libc only).
compile_jail() {
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id --memory=2g --pids-limit=256 --tmpfs /tmp:rw,nosuid,nodev,size=256m \
        -v "$gfx/output/host:/work/graphics-config/output/host:ro,z" -v "$src:$site:rw,z" -w "$site/frontend" "$iid" sh -euc '
        cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
        $cc -mcpu=cortex-a35 -std=c11 -O2 -pipe -ffunction-sections -fdata-sections \
            -Wall -Wpedantic -Wno-format-zero-length -Wno-unused-function -fno-plt \
            -fstack-protector-strong -fstack-clash-protection -D_FORTIFY_SOURCE=3 -D_GNU_SOURCE -fPIE -fno-ident \
            -Werror=implicit-function-declaration -Werror=implicit-int -Werror=incompatible-pointer-types \
            -Werror=return-type -Wformat-truncation=2 -Werror=format-truncation -Werror=unused-function \
            -I. module/musftpjail.c common/storage/mount.c -o ../frontend-bin/musftpjail \
            -Wl,--gc-sections -pie -Wl,-z,relro,-z,now -s
        # M8: upstream $(CURSOR_LIB) (SDL_ShowCursor(0) shim that
        # SETUP_SDL_ENVIRONMENT preloads; the standalone emulators here)
        $cc -mcpu=cortex-a35 -std=c11 -O2 -pipe -Wall -fstack-protector-strong -D_GNU_SOURCE -fno-ident \
            -shared -fPIC common/compat/sdl_cursor.c -o ../frontend-bin/lib/libmucursor.so -ldl \
            -Wl,-z,relro,-z,now -s
        ' >> "$log" 2>&1 || { tail -30 "$log" >&2; exit 1; }
}

case "${1:-build}" in
build)
    prepare
    sync_mk
    compile
    compile_jail
    t=$tool_out/musftpjail
    cp "$src/frontend-bin/musftpjail" "$t.tmp" && mv "$t.tmp" "$t"
    echo "musftpjail: $(sha256sum "$t" | cut -c1-16) ($(stat -c %s "$t") bytes)"
    l=$out/libmucursor.so
    cp "$src/frontend-bin/lib/libmucursor.so" "$l.tmp" && mv "$l.tmp" "$l"
    echo "libmucursor.so: $(sha256sum "$l" | cut -c1-16) ($(stat -c %s "$l") bytes)"
    l=$out/libmuxmod.so
    cp "$src/frontend-bin/lib/libmuxmod.so" "$l.tmp" && mv "$l.tmp" "$l"
    echo "frontend-libs: warnings=$(grep -c ' warning: ' "$log" || :) (log $log)"
    echo "libmuxmod.so: $(sha256sum "$l" | cut -c1-16) ($(stat -c %s "$l") bytes)"
    l=$out/libmuxcom.so
    if cat /dev/null "$patches"/*.patch | grep -q '^+++ b/frontend/common/'; then
        cp "$src/frontend-bin/lib/libmuxcom.so" "$l.tmp" && mv "$l.tmp" "$l"
        echo "libmuxcom.so: $(sha256sum "$l" | cut -c1-16) ($(stat -c %s "$l") bytes)"
    else
        rm -f "$l"
    fi ;;
release)
    prepare
    sync_mk
    compile 0 exes
    mkdir -p "$rel/lib"
    for f in lib/libui.so lib/libmuxcom.so lib/libmuxmod.so lib/libplutosvg.so muxfrontend muhotkey mubattery; do
        cp "$src/frontend-bin-release/$f" "$rel/$f.tmp" && mv "$rel/$f.tmp" "$rel/$f"
        echo "$f: $(sha256sum "$rel/$f" | cut -c1-16) ($(stat -c %s "$rel/$f") bytes)"
    done
    echo "frontend release: warnings=$(grep -c ' warning: ' "$log" || :) (log $log)" ;;
check)
    # An unpatched rebuild must equal the pinned libmuxmod.so.
    empty=$area/no-patches; mkdir -p "$empty"
    prepare "$empty"; sync_mk; compile
    want=bfd909c6eae5d6d692025e8a0b489840c9a552d3ad22e902183b6265d700ae17
    got=$(sha256sum "$src/frontend-bin/lib/libmuxmod.so" | cut -d' ' -f1)
    # libmuxcom: link order differs; the symbol table (name, type, size) must not.
    pinned=$repo/build/m3a/inputs/2913dbf7d901a258d338995e0d937c2f6559465c41a3bd0e097072820f57cd21
    syms() { nm -S "$1" | awk 'NF == 4 {print $4, $3, $2}' | sort; }
    if cmp -s <(syms "$pinned") <(syms "$src/frontend-bin/lib/libmuxcom.so"); then com=same; else com=DIFF; fi
    rm -rf "$src" "$stamp"
    echo "$com libmuxcom.so symbols"
    if [ "$got" = "$want" ]; then echo 'same libmuxmod.so'; else echo "DIFF libmuxmod.so $got != $want"; exit 1; fi
    [ "$com" = same ] || exit 1 ;;
clean) rm -rf "$src" "$stamp" ;;
mkpatch)
    name=$2; shift 2
    { printf 'From: muOS R35S port\nSubject: [PATCH] %s\n\nSPDX-License-Identifier: GPL-3.0\n---\n' "${name%.patch}"
      for f in "$@"; do
          if [ -e "$base/$f" ]; then old=$base/$f lbl=a/$f; else old=/dev/null lbl=/dev/null; fi
          diff -u --label "$lbl" --label "b/$f" "$old" "$src/$f" || [ $? = 1 ]
      done
    } > "$patches/$name.tmp"
    mv "$patches/$name.tmp" "$patches/$name"
    echo "$patches:$(cat /dev/null "$patches"/*.patch | sha256sum | cut -d" " -f1)" > "$stamp"
    echo "wrote port/patches/frontend/$name ($(grep -c '^@@' "$patches/$name") hunks)" ;;
*) sed -n '3,10p' "$0"; exit 2 ;;
esac
