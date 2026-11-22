#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M9 item 6: the corresponding source of a release (GPL/LGPL obligations;
# components and revisions in rootfs/usr/share/muos-r35s/THIRD-PARTY.txt).
#   make-source-bundle.sh check        every pinned source is still on the
#                                      host (needed to honour the offer)
#   make-source-bundle.sh bundle DIR   write the bundle to DIR (several GB:
#                                      release time only, on request)
# Contents: the port repository (patches, build scripts, notices), the
# kernel, U-Boot, ScummVM and YabaSanshiro trees at their pinned commits,
# the core/emulator source tarballs from the build caches, and Buildroot
# legal-info (licence texts and sources of every root-filesystem package).
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
b=$repo/build
trees=("linux:$b/phase4/linux-base" "u-boot:$b/phase4/uboot-base" "scummvm:$b/scummvm-src"
       "yabasanshiro-sa:$b/yabasanshiro-sa-src" "buildroot:$b/phase4/buildroot")
caches=("$b/m3c/cores/cache" "$b/m7/mupen64plus/cache" "$b/m8f/dl")
case ${1:-} in
check)
    bad=0
    for t in "${trees[@]}"; do
        d=${t#*:}; r=$(git -C "$d" rev-parse --short HEAD 2>/dev/null) || { echo "MISSING ${t%%:*} ($d)"; bad=1; continue; }
        echo "ok ${t%%:*} $r"
    done
    for c in "${caches[@]}"; do
        if [ -d "$c" ]; then echo "ok $(find "$c" -maxdepth 1 -name '*.tar*' | wc -l) tarballs in ${c#"$repo"/}"; else echo "MISSING $c"; bad=1; fi
    done
    exit $bad ;;
bundle)
    out=$(realpath -m "${2:?usage: bundle DIR}"); mkdir -p "$out"
    git -C "$repo" archive --format=tar --prefix=muos-r35s-port/ HEAD | zstd -q -10 -o "$out/muos-r35s-port-$(git -C "$repo" rev-parse --short HEAD).tar.zst"
    for t in "${trees[@]}"; do
        d=${t#*:}; r=$(git -C "$d" rev-parse --short=12 HEAD)
        git -C "$d" archive --format=tar --prefix="${t%%:*}/" HEAD | zstd -q -10 -o "$out/${t%%:*}-$r.tar.zst"
    done
    mkdir -p "$out/cores"
    for c in "${caches[@]}"; do
        for f in "$c"/*.tar "$c"/*.tar.*; do [ -e "$f" ] && zstd -q -10 "$f" -o "$out/cores/${f##*/}.zst"; done
    done
    "$repo/port/scripts/build-image.sh" legal-info
    tar -C "$b/m3a/output" -cf - legal-info | zstd -q -10 -o "$out/buildroot-legal-info.tar.zst"
    cp "$repo/port/device/rk-r35s-p0/rootfs/usr/share/muos-r35s/THIRD-PARTY.txt" "$out/"
    # shellcheck disable=SC2094 # SHA256SUMS is excluded from the list
    (cd "$out" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
    du -sh "$out" ;;
*) sed -n '3,12p' "$0"; exit 2 ;;
esac
