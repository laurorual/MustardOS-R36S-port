#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M5: upstream MustardOS internal share/ data (themes, profiles, lookup and
# name tables, media, tasks, languages) for the image. refs/muos/internal
# is a blob:none sparse clone without share/ (reading its blobs fetches
# them one by one into refs, which must stay untouched), so this keeps a
# separate sparse clone in build/upstream/internal at the pinned commit,
# limited to the 640x480 variants (no other resolutions, no video walls)
# and without upstream's music, credits and factory-reset media (55 MiB)
# (the CJK fonts ship since M8, decision 17: the 1 GiB p2).
# M7: the languages come from the pinned upstream language pack
# (port/packaging/muos-language.txt) instead of internal's share/language,
# which upstream no longer updates; the port's additions are merged in.
#   fetch-upstream-share.sh          clone or update the checkout, fetch the
#                            language pack
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
        '!/share/media/music/' '!/share/media/credits/' '!/share/media/factory.mp3'
}
langcfg=$repo/port/packaging/muos-language.txt
langdir=$repo/build/upstream/language
lang_value() { sed -n "s/^$1 //p" "$langcfg"; }
lang_fetch() {
    local zip=$langdir/lang.muxzip want
    want=$(lang_value sha256)
    mkdir -p "$langdir"
    if [ "$(sha256sum "$zip" 2>/dev/null | cut -d' ' -f1)" != "$want" ]; then
        curl -fsSL -o "$zip.tmp" "$(lang_value url)"
        [ "$(sha256sum "$zip.tmp" | cut -d' ' -f1)" = "$want" ] || { rm -f "$zip.tmp"; echo "language pack: sha256 mismatch" >&2; exit 1; }
        mv "$zip.tmp" "$zip"
    fi
}
# Copy the pack's language files (minus the excluded ones) to DIR, merged
# with port/packaging/language/*.json.
lang_stage() {
    local zip=$langdir/lang.muxzip dst=$1
    [ "$(sha256sum "$zip" | cut -d' ' -f1)" = "$(lang_value sha256)" ] || { echo "language pack missing: run $0 fetch" >&2; exit 1; }
    rm -rf "$dst"; mkdir -p "$dst"
    lang_value exclude | python3 -I -c '
import json, os, sys, zipfile
zip_path, dst, overlay_dir = sys.argv[1:4]
excluded = {line.strip() for line in sys.stdin if line.strip()}
shipped = 0
with zipfile.ZipFile(zip_path) as z:
    for name in z.namelist():
        base = os.path.basename(name)
        if not (name.startswith("language/") and base.endswith(".json")) or base[:-5] in excluded:
            continue
        data = json.loads(z.read(name))
        extra = os.path.join(overlay_dir, base)
        if os.path.exists(extra):
            with open(extra, encoding="utf-8") as f:
                for section, entries in json.load(f).items():
                    data.setdefault(section, {}).update(entries)
        with open(os.path.join(dst, base), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        shipped += 1
missing = [n for n in os.listdir(overlay_dir) if not os.path.exists(os.path.join(dst, n))]
if missing:
    sys.exit("overlay without a language file: %s" % missing)
print("languages: %d files" % shipped)
' "$zip" "$dst" "$repo/port/packaging/language"
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
    lang_fetch
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
    find "$out/opt/muos/share" -name .gitkeep -delete
    lang_stage "$out/opt/muos/share/language" ;;
*) sed -n '3,19p' "$0"; exit 2 ;;
esac
