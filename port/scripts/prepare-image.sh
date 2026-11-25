#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Plan B (decision 36): if a closed component ever has to leave the public
# image, the user's PC puts it back before flashing. Downloads each
# component from its original source, checks every file against the
# SHA256 pinned in port/packaging/planb-components.txt, and writes it into
# the image's root partition (p2, ext4) with debugfs: no root, no mount,
# no download on the handheld.
#
#   prepare-image.sh check  IMAGE.img             which components are present
#   prepare-image.sh inject IMAGE.img [COMP...]   add the missing ones (default:
#                                                 all); the downloads are kept
#                                                 in $PLANB_CACHE (default
#                                                 ~/.cache/mustardos-r36s-planb)
#   prepare-image.sh strip  IMAGE.img [COMP...]   remove them (tests, or a
#                                                 release without them)
#   prepare-image.sh manifest                     (developers) regenerate the
#                                                 manifest from the build trees
#
# IMAGE is the uncompressed card image (xz -d / zstd -d it first). Needs
# bash, python3, curl, sha256sum, sfdisk, debugfs and e2fsck (e2fsprogs).
# Components: mali (Arm Mali-G31 r13p0 userspace, Hardkernel's archive),
# drastic (DraStic r2.5.2.2, trngaje's advanced_drastic hook and
# steward-fu's 640x480 layout art, from the GitHub repositories dArkOS uses).
set -euo pipefail
export LC_ALL=C
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
manifest=${PLANB_MANIFEST:-$here/../packaging/planb-components.txt}
cache=${PLANB_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/mustardos-r36s-planb}
mode=${1:-}; img=${2:-}
[ -n "$mode" ] || { sed -n '3,22p' "$0"; exit 2; }

if [ "$mode" = manifest ]; then
    repo=$(cd -- "$here/../.." && pwd)
    adv_commit=d445a56349cce68f5337d02c9fe890de9d390f3f lay_commit=e8dc3eb5bb51351bf3e93229e388ae9e5fea9adc
    d=/opt/muos/share/emulator/drastic
    {
    echo "# Plan B components (prepare-image.sh manifest). Columns: component, source"
    echo "# key, member in the downloaded archive, path in p2, mode, sha256."
    echo "source mali https://dn.odroid.com/RK3326/ODROID-GO-Advance/rk3326_r13p0_gbm_with_vulkan_and_cl.zip zip ef1a18fabf270d0a6029917d6b0e6237d328613c2f8be4d420ea23e022288dd9"
    echo "source adv https://codeload.github.com/trngaje/advanced_drastic/tar.gz/$adv_commit tgz -"
    echo "source lay https://codeload.github.com/trngaje/drastic_layout/tar.gz/$lay_commit tgz -"
    echo "file mali mali libmali.so_rk3326_gbm_arm64_r13p0_with_vulkan_and_cl /usr/lib/libmali-bifrost-g31-rxp0-gbm.so 755 2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea"
    while read -r sum p; do
        p=${p#./}
        case $p in
            drastic) src=adv m=advanced_drastic-$adv_commit/drastic_v2522 mo=755 ;;
            libs/*) src=adv m=advanced_drastic-$adv_commit/libs/arkos/${p#libs/} mo=644 ;;
            resources/bg/*) src=lay m=drastic_layout-$lay_commit/${p#resources/} mo=644 ;;
            *) src=adv m=advanced_drastic-$adv_commit/$p mo=644 ;;
        esac
        echo "file drastic $src $m $d/$p $mo $sum"
    done < "$repo/build/m8/advdrastic/SHA256SUMS"
    } > "$manifest"
    echo "wrote $(realpath --relative-to="$repo" "$manifest") ($(grep -c '^file' "$manifest") files)"; exit 0
fi

[ -f "$img" ] || { echo "no image $img" >&2; exit 2; }
case $img in *.xz|*.zst|*.gz) echo "decompress $img first" >&2; exit 2 ;; esac
shift 2; comps=("$@"); [ ${#comps[@]} -gt 0 ] || comps=(mali drastic)
for c in "${comps[@]}"; do grep -q "^file $c " "$manifest" || { echo "unknown component $c" >&2; exit 2; }; done
for t in python3 sha256sum sfdisk debugfs e2fsck; do command -v "$t" > /dev/null || { echo "needs $t" >&2; exit 2; }; done
work=$(mktemp -d "${TMPDIR:-/tmp}/planb.XXXXXX"); trap 'rm -rf "$work"' EXIT
read -r start size < <(sfdisk -d "$img" 2>/dev/null | sed -n 's|^.*[^0-9]2 : start= *\([0-9]*\), size= *\([0-9]*\),.*|\1 \2|p')
[ -n "${size:-}" ] || { echo 'no partition 2 in the image' >&2; exit 1; }
p2=$work/p2.img
dd if="$img" of="$p2" bs=512 skip="$start" count="$size" conv=sparse status=none
[ "$(debugfs -R 'stat /etc/muos-port-release' "$p2" 2>/dev/null | grep -c '^Inode:')" = 1 ] ||
    { echo 'partition 2 is not a MustardOS R36S port root' >&2; exit 1; }
files() { awk -v c="$1" '$1 == "file" && $2 == c' "$manifest"; }
p2sum() { debugfs -R "cat $1" "$p2" 2>/dev/null | sha256sum | cut -d' ' -f1; }
state() { # component -> present | missing | partial
    local n=0 ok=0 want dest
    while read -r _ _ _ _ dest _ want; do
        n=$((n + 1)); [ "$(p2sum "$dest")" != "$want" ] || ok=$((ok + 1))
    done < <(files "$1")
    if [ $ok = "$n" ]; then echo present; elif [ $ok = 0 ]; then echo missing; else echo "partial ($ok/$n)"; fi
}
writeback() {
    e2fsck -fn "$p2" > "$work/fsck.txt" 2>&1 || { cat "$work/fsck.txt"; echo 'p2 fsck failed, image unchanged' >&2; exit 1; }
    # not conv=sparse: zero blocks must overwrite what the image had there
    dd if="$p2" of="$img" bs=1M oflag=seek_bytes seek=$((start * 512)) conv=notrunc status=none
    cmp -s "$p2" <(dd if="$img" bs=512 skip="$start" count="$size" status=none) || { echo 'write-back mismatch' >&2; exit 1; }
}
fetch() { # source key -> local archive path (downloaded once, then cached)
    local key=$1 url kind want f
    read -r _ _ url kind want < <(awk -v k="$key" '$1 == "source" && $2 == k' "$manifest")
    f=$cache/$key.$kind; mkdir -p "$cache"
    if [ ! -s "$f" ]; then
        echo "  download $url" >&2
        if ! curl -fsSL --retry 3 -o "$f.part" "$url"; then
            # dn.odroid.com answers scripts with a browser check (HTTP 403)
            rm -f "$f.part"
            echo "  $key: the server refused the download. Open the URL above in a web browser," >&2
            echo "  save the file as $f and run this command again." >&2
            exit 1
        fi
        mv "$f.part" "$f"
    fi
    [ "$want" = - ] || [ "$(sha256sum < "$f" | cut -d' ' -f1)" = "$want" ] ||
        { rm -f "$f"; echo "  $key: archive SHA256 mismatch (deleted, try again)" >&2; exit 1; }
    echo "$f"
}
extract() { # archive kind outdir member... (one pass over the archive)
    python3 -I - "$@" <<'PY'
import os, sys, tarfile, zipfile, shutil
arc, kind, out, *members = sys.argv[1:]
want = set(members)
def put(name, src):
    dst = os.path.join(out, name)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'wb') as d: shutil.copyfileobj(src, d)
    want.discard(name)
if kind == 'zip':
    with zipfile.ZipFile(arc) as z:
        for m in members:
            with z.open(m) as src: put(m, src)
else:
    with tarfile.open(arc, 'r|gz') as t:
        for ti in t:
            if ti.name in want and ti.isfile(): put(ti.name, t.extractfile(ti))
if want: sys.exit('not in the archive: ' + ' '.join(sorted(want)))
PY
}
case $mode in
check)
    for c in "${comps[@]}"; do echo "$c: $(state "$c")"; done ;;
strip)
    : > "$work/cmds"
    for c in "${comps[@]}"; do
        while read -r _ _ _ _ dest _ _; do echo "rm $dest" >> "$work/cmds"; done < <(files "$c")
        # then the directories this component created, deepest first, if empty
        files "$c" | awk '{ print $5 }' | while read -r dest; do
            dir=${dest%/*}; while [ "$dir" != /opt/muos/share/emulator ] && [ "$dir" != /usr/lib ] && [ -n "$dir" ]; do echo "$dir"; dir=${dir%/*}; done
        done | sort -u | awk '{ print length, $0 }' | sort -rn | cut -d' ' -f2- | sed 's/^/rmdir /' >> "$work/cmds"
    done
    debugfs -w -f "$work/cmds" "$p2" > /dev/null 2>&1
    writeback
    for c in "${comps[@]}"; do echo "$c: $(state "$c")"; done ;;
inject)
    for c in "${comps[@]}"; do
        s=$(state "$c"); [ "$s" != present ] || { echo "$c: already present"; continue; }
        echo "$c: $s -> injecting"
        files "$c" | while read -r _ _ key member dest mo want; do
            [ "$(p2sum "$dest")" = "$want" ] || echo "$key $member $dest $mo $want"
        done > "$work/need"
        for key in $(cut -d' ' -f1 "$work/need" | sort -u); do
            arc=$(fetch "$key")
            mapfile -t members < <(awk -v k="$key" '$1 == k { print $2 }' "$work/need")
            extract "$arc" "${arc##*.}" "$work/x/$key" "${members[@]}"
        done
        : > "$work/cmds"; declare -A made=()
        while read -r key member dest mo want; do
            f=$work/x/$key/$member
            [ "$(sha256sum < "$f" | cut -d' ' -f1)" = "$want" ] || { echo "  $dest: SHA256 mismatch from $key" >&2; exit 1; }
            dir=${dest%/*} parts=() p=
            IFS=/ read -r -a parts <<< "${dir#/}"
            for part in "${parts[@]}"; do
                p=$p/$part; [ -z "${made[$p]:-}" ] || continue; made[$p]=1
                debugfs -R "stat $p" "$p2" 2>/dev/null | grep -q '^Inode:' && continue
                printf 'mkdir %s\nsif %s mode 040755\nsif %s uid 0\nsif %s gid 0\n' "$p" "$p" "$p" "$p" >> "$work/cmds"
            done
            printf 'rm %s\nwrite %s %s\nsif %s mode 0100%s\nsif %s uid 0\nsif %s gid 0\n' \
                "$dest" "$f" "$dest" "$dest" "$mo" "$dest" "$dest" >> "$work/cmds"
        done < "$work/need"
        debugfs -w -f "$work/cmds" "$p2" > /dev/null 2>&1
        unset made; rm -rf "$work/x"
        echo "$c: $(state "$c")"
    done
    writeback ;;
*) sed -n '3,22p' "$0"; exit 2 ;;
esac
