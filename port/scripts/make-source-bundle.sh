#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M9 item 3: the corresponding source of a release (GPL/LGPL obligations;
# components and licences in docs/LICENSING.md and THIRD-PARTY.txt).
#   make-source-bundle.sh check        every source the public image needs
#                                      is still on the host
#   make-source-bundle.sh bundle DIR   write the bundle to DIR (~2 GB:
#                                      release time only), SHA256SUMS last
#   make-source-bundle.sh pack DIR NAME  DIR's files in NAME-source-N.zip
#                                      next to DIR (stored, not recompressed:
#                                      the parts are .tar.zst already), each
#                                      under GitHub's 2 GiB asset limit,
#                                      every part with SHA256SUMS, + .sha256
# Contents (one .tar.zst each):
#   MustardOS-R36S-port-REV this repository at HEAD: patches, build scripts,
#                        device files, notices (kernel/U-Boot configs, the
#                        boot-record U-Boot sources, muxretro/frontend patches)
#   linux, u-boot        the kernel (also its in-tree modules, rtl8821cu) and
#                        U-Boot trees at their pinned commits (git archive)
#   scummvm              v2026.4.0 + backends/platform/libretro/deps
#   yabasanshiro-sa      the standalone with its submodules (eigen) and
#                        its ExternalProject deps (yaba-dep-*)
#   buildroot            Buildroot 2025.02 (the build system itself)
#   frontend-libs, muxretro-provider   the MustardOS frontend source trees
#                        (5e8635b) the libraries, muxfrontend and muxretro
#                        are built from, with their bundled deps/rcheevos
#   darkos-patches       christianhaitian/rk3326_core_builds patches used by
#                        the PPSSPP/Flycast/YabaSanshiro standalone builds
#   cores/*.tar.zst      the libretro core, Mupen64Plus, PPSSPP, Flycast,
#                        Boost and xiph tarballs from the pinned build caches
#   buildroot-legal-info licence texts and sources of every root-filesystem
#                        package (build-image.sh legal-info)
#   model-dts            the source (DTS) of every model DTB (M10)
# Not included (no source exists): Mali r13p0 userspace, DraStic,
# libadvdrastic.so; see docs/LICENSING.md.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
b=$repo/build
# name:dir:expected commit (git trees; submodules are archived too)
trees=("linux:$b/phase4/linux-base:d8402159c04b1044106b4f27b7ed7c22ed09228f"
       "u-boot:$b/phase4/uboot-base:5606e804ffe8f9e5427d55c8da04c638f01a9391"
       "scummvm:$b/scummvm-src:7d2709da5136866589f7602f5f5a7b17de03420e"
       "yabasanshiro-sa:$b/yabasanshiro-sa-src:c7618d2ecbf77b1e8188fa8af4fa1cfb34833a72"
       "yaba-dep-zlib:$b/yabasanshiro-sa-deps/zlib:50893291621658f355bc5b4d450a8d06a563053d"
       "yaba-dep-json:$b/yabasanshiro-sa-deps/json:359f98d14065bf4e53eeb274f5987fd08f16e5bf"
       "yaba-dep-libchdr:$b/yabasanshiro-sa-deps/libchdr:074ff1614f2a685f2b5a95b0e788bff6297d5680"
       "buildroot:$b/phase4/buildroot:")
# name:dir (plain source trees)
plain=("frontend-libs:$b/phase4/frontend-libs/source" "muxretro-provider:$b/phase4/muxretro-provider/source"
       "darkos-patches:$b/rk3326-core-builds/patches" "scummvm-libretro-deps:$b/scummvm-src/backends/platform/libretro/deps")
caches=("$b/m3c/cores/cache" "$b/m7/mupen64plus/cache" "$b/m8f/dl" "$b/m8/dl")
legal=$b/m3a/output/legal-info
core_tarballs() { # every tarball build-cores.sh pins
    bash -c 'source <(sed -n "/^table()/,/^}/p" "$1"); table' _ "$repo/port/scripts/build-cores.sh" |
        while read -r n _ commit _; do echo "$b/m3c/cores/cache/$n-$commit.tar"; done
}
case ${1:-} in
check)
    bad=0
    for t in "${trees[@]}"; do
        IFS=: read -r n d want <<< "$t"
        r=$(git -C "$d" rev-parse HEAD 2>/dev/null) || { echo "MISSING $n ($d)"; bad=1; continue; }
        if [ -n "$want" ] && [ "$r" != "$want" ]; then echo "WRONG $n at $r, want $want"; bad=1; else echo "ok $n ${r:0:12}"; fi
    done
    for t in "${plain[@]}"; do
        d=${t#*:}; if [ -d "$d" ]; then echo "ok ${t%%:*} ($(du -sh "$d" | cut -f1))"; else echo "MISSING ${t%%:*} ($d)"; bad=1; fi
    done
    while read -r f; do [ -s "$f" ] || { echo "MISSING core tarball ${f#"$b"/}"; bad=1; }; done < <(core_tarballs)
    echo "ok $(core_tarballs | wc -l) core tarballs pinned by build-cores.sh"
    for c in "${caches[@]}"; do
        if [ -d "$c" ]; then echo "ok $(find "$c" -maxdepth 1 -name '*.tar*' ! -name '*.json' | wc -l) tarballs in ${c#"$repo"/}"; else echo "MISSING $c"; bad=1; fi
    done
    if [ -s "$legal/manifest.csv" ]; then echo "ok legal-info ($(($(wc -l < "$legal/manifest.csv") - 1)) packages)"
    else echo "MISSING legal-info (build-image.sh legal-info)"; bad=1; fi
    exit $bad ;;
bundle)
    "$0" check > /dev/null || { "$0" check; exit 1; }
    out=$(realpath -m "${2:?usage: bundle DIR}"); mkdir -p "$out/cores"
    z() { zstd -q -T0 -10 -o "$1"; }
    git -C "$repo" archive --format=tar --prefix=MustardOS-R36S-port/ HEAD | z "$out/MustardOS-R36S-port-$(git -C "$repo" rev-parse --short=12 HEAD).tar.zst"
    for t in "${trees[@]}"; do
        IFS=: read -r n d _ <<< "$t"; r=$(git -C "$d" rev-parse --short=12 HEAD)
        tmp=$(mktemp -d "$b/.bundle.XXXXXX")
        git -C "$d" archive --format=tar --prefix="$n/" HEAD > "$tmp/main.tar"
        # initialised submodules at their recorded commits
        git -C "$d" submodule foreach --quiet --recursive \
            "git archive --format=tar --prefix=\"$n/\$displaypath/\" HEAD > \"$tmp/sub-\$(echo \$displaypath | tr / _).tar\""
        for s in "$tmp"/sub-*.tar; do [ -e "$s" ] && tar -Af "$tmp/main.tar" "$s"; done
        z "$out/$n-$r.tar.zst" < "$tmp/main.tar"; rm -rf "$tmp"
    done
    for t in "${plain[@]}"; do
        d=${t#*:}
        tar -C "$(dirname "$d")" --exclude=.git --sort=name --owner=0 --group=0 --numeric-owner \
            --transform="s|^$(basename "$d")|${t%%:*}|" -cf - "$(basename "$d")" | z "$out/${t%%:*}.tar.zst"
    done
    { core_tarballs; for c in "${caches[@]:1}"; do find "$c" -maxdepth 1 -name '*.tar*' ! -name '*.json'; done; } |
        sort -u | while read -r f; do z "$out/cores/${f##*/}.zst" < "$f"; done
    tar -C "$(dirname "$legal")" -cf - legal-info | z "$out/buildroot-legal-info.tar.zst"
    # M10: the model DTBs' source: each decompiled DTS (dArkOSen's DTB + the
    # port's deltas, make-dtb-model.sh) with dArkOSen's licence
    tmp=$(mktemp -d "$b/.bundle.XXXXXX"); mkdir "$tmp/model-dts"
    "$repo/port/scripts/make-dtb-model.sh" "$tmp/model-dts" > "$tmp/model-dts/models.list"
    rm -f "$tmp/model-dts"/*.dtb; cp "$repo/refs/darkosen/LICENSE" "$tmp/model-dts/LICENSE.dArkOSen"
    cp "$repo/port/packaging/models.txt" "$tmp/model-dts/"
    tar -C "$tmp" --sort=name --owner=0 --group=0 --numeric-owner -cf - model-dts | z "$out/model-dts.tar.zst"; rm -rf "$tmp"
    cp "$repo/port/device/rk-r35s-p0/rootfs/usr/share/muos-r35s/THIRD-PARTY.txt" "$repo/docs/LICENSING.md" "$out/"
    # shellcheck disable=SC2094 # SHA256SUMS is excluded from the list
    (cd "$out" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
    du -sh "$out" ;;
pack)
    [ $# -eq 3 ] && [ -f "$2/SHA256SUMS" ] || { echo 'usage: pack DIR NAME (DIR from bundle)' >&2; exit 2; }
    dir=$(realpath "$2") name=$3 limit=$((1900 * 1024 * 1024))
    rm -f "${dir%/*}/$name"-source-*.zip*
    # first-fit decreasing into parts under the limit
    declare -a size=() list=()
    while read -r b f; do
        for ((i = 0; ; i++)); do
            if [ $(( ${size[i]:-0} + b )) -le $limit ]; then size[i]=$(( ${size[i]:-0} + b )); list[i]+="$f"$'\n'; break; fi
        done
    done < <(cd "$dir" && find . -type f ! -name SHA256SUMS -printf '%s %P\n' | sort -rn)
    for i in "${!list[@]}"; do
        z=${dir%/*}/$name-source-$((i + 1)).zip
        (cd "$dir" && printf '%s' "${list[i]}" | sed '/^$/d' | { cat; echo SHA256SUMS; } | zip -q -0 -@ "$z")
        (cd "${z%/*}" && sha256sum "${z##*/}" > "${z##*/}.sha256")
        echo "$(du -h "$z" | cut -f1) ${z##*/} ($(printf '%s' "${list[i]}" | grep -c .) files)"
    done ;;
*) sed -n '3,34p' "$0"; exit 2 ;;
esac
