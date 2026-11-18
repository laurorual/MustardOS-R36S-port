#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M5: upstream MustardOS internal share/ data (themes, profiles, lookup and
# name tables, media, tasks, languages) for the image. refs/muos/internal
# is a blob:none sparse clone without share/ (reading its blobs fetches
# them one by one into refs, which must stay untouched), so this keeps a
# separate sparse clone in build/upstream/internal at the pinned commit,
# limited to the 640x480 variants (no other resolutions, no video walls)
# and without upstream's music, credits and factory-reset media (55 MiB)
# or the CJK/Arabic fonts (with the languages, M7).
#   fetch-upstream-share.sh          clone or update the checkout
#   fetch-upstream-share.sh verify   tree ids against port/packaging/muos-internal-share.txt
#   fetch-upstream-share.sh stage DIR   verify, then copy the trees to
#                            DIR/opt/muos/<path> without the paths in
#                            muos-internal-share-exclude.txt (used by
#                            build-image.sh stage_overlay; also a tree for
#                            install-rootfs.sh --tree)
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
rev=$(awk '$1 == "refs/muos/internal" {print $2}' "$repo/docs/upstream-revisions.txt")
dst=$repo/build/upstream/internal
list=$repo/port/packaging/muos-internal-share.txt
patterns() {
    sed -n 's|^[0-9a-f]\{40\} \(.*\)$|/\1/|p' "$list"
    # theme variants other than 640x480, video walls and previews of others
    printf '%s\n' '!/share/theme/*/[0-9]*x[0-9]*/' '/share/theme/*/640x480/' '!*.mp4' \
        '!/share/media/music/' '!/share/media/credits/' '!/share/media/factory.mp3' \
        '!/share/font/internal/*/'
}
case "${1:-fetch}" in
fetch)
    if [ ! -d "$dst/.git" ]; then
        mkdir -p "$(dirname "$dst")"
        git clone -q --filter=blob:none --no-checkout --sparse https://github.com/MustardOS/internal.git "$dst"
    fi
    git -C "$dst" cat-file -e "$rev^{commit}" 2>/dev/null || git -C "$dst" fetch -q origin "$rev"
    patterns | git -C "$dst" sparse-checkout set --no-cone --stdin
    git -C "$dst" -c advice.detachedHead=false checkout -q "$rev"
    du -sh --exclude=.git "$dst" ;;
verify)
    bad=0
    while read -r want path; do
        case "$want" in ''|'#'*) continue ;; esac
        have=$(git -C "$dst" rev-parse "$rev:$path")
        [ "$have" = "$want" ] || { echo "MISMATCH $path $have != $want"; bad=1; }
        [ -d "$dst/$path" ] || { echo "MISSING $path"; bad=1; }
    done < "$list"
    [ "$bad" = 0 ] && echo "verified $(grep -c '^[0-9a-f]' "$list") trees at $rev" ;;
stage)
    out=${2:?stage DIR}
    "$0" verify > /dev/null
    while read -r want path; do
        case "$want" in ''|'#'*) continue ;; esac
        mkdir -p "$out/opt/muos/$path"
        cp -a --reflink=auto "$dst/$path/." "$out/opt/muos/$path/"
    done < "$list"
    while IFS= read -r path; do
        case "$path" in ''|'#'*) continue ;; esac
        [ -e "$out/opt/muos/$path" ] || { echo "exclude: no $path" >&2; exit 1; }
        rm -rf "${out:?}/opt/muos/$path"
    done < "${list%.txt}-exclude.txt"
    find "$out/opt/muos/share" -name .gitkeep -delete ;;
*) sed -n '3,15p' "$0"; exit 2 ;;
esac
