#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M8 (decision 25): carry the card's p3 (ROMs, saves, states, BIOS, Wi-Fi
# profile, settings) across a reflash that moves p3 (the 1 GiB p2 layout),
# with the card in this host's USB reader. Uses sudo (mount, tar as root:
# p3 files are root-owned, some 0700); the user types the password.
#   card-p3.sh backup  /dev/sdX [TAR]   p3 (MUOSDATA) mounted read-only ->
#                                       TAR (default build/m8/p3-backup/p3.tar),
#                                       numeric owners, modes, times, xattrs;
#                                       MUOS/trial (old-layout p2/U-Boot
#                                       images) left out
#   card-p3.sh restore /dev/sdX [TAR]   TAR extracted over the new p3 (after
#                                       flash-card.sh host ... --grow), then a
#                                       file-count check, sync, unmount
# The TAR is PRIVATE (Wi-Fi PSK in MUOS, saves): never commit or share it;
# delete it once the restored card is T3-checked.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
mode=${1:-} dev=${2:-} tar=${3:-$repo/build/m8/p3-backup/p3.tar}
[ -n "$mode" ] && [ -n "$dev" ] || { sed -n '3,16p' "$0"; exit 2; }
name=${dev#/dev/}
case "$name" in sd[a-z]|mmcblk[0-9]) ;; *) echo "refusing $dev: expected a whole card-reader disk" >&2; exit 1 ;; esac
read -r tran rm < <(lsblk -dno TRAN,RM "$dev")
case "$name:$tran:$rm" in mmcblk*|*:usb:*|*:*:1) ;; *) echo "refusing $dev: not USB/removable" >&2; exit 1 ;; esac
case "$(findmnt -no SOURCE /)" in "$dev"*) echo "refusing $dev: holds the running root" >&2; exit 1 ;; esac
p3=${dev}3; case "$name" in mmcblk*) p3=${dev}p3 ;; esac
[ "$(lsblk -no LABEL "$p3")" = MUOSDATA ] || { echo "refusing: $p3 is not MUOSDATA" >&2; exit 1; }
mnt=$(mktemp -d "$repo/build/m8/.p3mnt.XXXXXX")
cleanup() { sudo umount "$mnt" 2>/dev/null || :; rmdir "$mnt" 2>/dev/null || :; }
trap cleanup EXIT
for m in $(lsblk -nro MOUNTPOINT "$dev" | grep .); do udisksctl unmount -b "$(findmnt -no SOURCE "$m")" >/dev/null 2>&1 || sudo umount "$m"; done
count() { sudo find "$mnt" -xdev -path "$mnt/MUOS/trial" -prune -o -path "$mnt/lost+found" -prune -o -print | wc -l; }
case "$mode" in
backup)
    mkdir -p "$(dirname "$tar")"
    sudo mount -o ro "$p3" "$mnt"
    echo "== p3 $(df -h --output=used "$mnt" | tail -1 | tr -d ' ') used -> $tar"
    sudo tar -C "$mnt" --numeric-owner --xattrs --acls --exclude=./MUOS/trial --exclude=./lost+found \
        -cpf "$tar" .
    sudo chown "$(id -u):$(id -g)" "$tar"; chmod 600 "$tar"
    n=$(count); echo "$n" > "$tar.count"
    echo "backup ok: $n entries, $(du -h "$tar" | cut -f1)" ;;
restore)
    [ -s "$tar" ] && [ -s "$tar.count" ] || { echo "no backup $tar" >&2; exit 1; }
    sudo mount "$p3" "$mnt"
    echo "== restore $tar -> $p3 ($(lsblk -no SIZE "$p3"))"
    sudo tar -C "$mnt" --numeric-owner --xattrs --acls -xpf "$tar"
    sudo mkdir -p "$mnt/MUOS/trial"
    sync
    n=$(count); want=$(cat "$tar.count")
    [ "$n" -ge "$want" ] || { echo "restore check FAILED: $n entries, backup had $want" >&2; exit 1; }
    echo "restore ok: $n entries (backup $want)" ;;
*) sed -n '3,16p' "$0"; exit 2 ;;
esac
