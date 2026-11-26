#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M10: the pinned linux-firmware files for the mainline USB Wi-Fi drivers
# (port/packaging/wifi-firmware.txt).
#   fetch-wifi-firmware.sh            download the missing files into
#                                     build/upstream/linux-firmware-TAG
#   fetch-wifi-firmware.sh verify     check every file against its sha256
#   fetch-wifi-firmware.sh stage DIR  verify, then install the firmware to
#                                     DIR/lib/firmware (+ links) and the
#                                     licences to DIR/usr/share/licenses/linux-firmware
#                                     (used by build-image.sh stage_overlay)
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
list=$repo/port/packaging/wifi-firmware.txt
tag=$(awk '$1 == "tag" {print $2}' "$list")
src=$repo/build/upstream/linux-firmware-$tag
url=https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/plain
entries() { awk '$1 ~ /^[0-9a-f]{64}$/' "$list"; }
verify() {
    local want path link bad=0
    while read -r want path link; do
        [ "$(sha256sum "$src/$path" 2>/dev/null | cut -d' ' -f1)" = "$want" ] ||
            { echo "wifi firmware: $path missing or does not match" >&2; bad=1; }
    done < <(entries)
    return "$bad"
}
case "${1:-fetch}" in
fetch)
    while read -r want path link; do
        [ "$(sha256sum "$src/$path" 2>/dev/null | cut -d' ' -f1)" != "$want" ] || continue
        mkdir -p "$(dirname "$src/$path")"
        curl -fsS -o "$src/$path.tmp" "$url/$path?h=$tag"
        mv "$src/$path.tmp" "$src/$path"
    done < <(entries)
    verify && echo "wifi firmware $tag: $(entries | wc -l) files ok" ;;
verify) verify && echo "wifi firmware $tag: ok" ;;
stage)
    dir=${2:?stage DIR}
    verify
    while read -r want path link; do
        case "$path" in
            LICENSES/*) install -D -m 0644 "$src/$path" "$dir/usr/share/licenses/linux-firmware/${path#LICENSES/}" ;;
            *) install -D -m 0644 "$src/$path" "$dir/lib/firmware/$path"
               [ -z "$link" ] || ln -sfn "$path" "$dir/lib/firmware/$link" ;;
        esac
    done < <(entries)
    printf 'linux-firmware %s (%s), unmodified: %s\n' "$tag" \
        "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git" \
        "the licence of each file is in WHENCE there and in this folder" \
        > "$dir/usr/share/licenses/linux-firmware/README" ;;
*) echo 'Usage: fetch-wifi-firmware.sh [fetch|verify|stage DIR]' >&2; exit 2 ;;
esac
