#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Compose a flashable test-card image from a `device.sh capture` directory.
#
#   make-recovery-image.sh [--p3-mib N] [--strip-seed] CAPTURE_DIR OUT.img.zst
#
# Layout: the captured 0..640 MiB prefix (idbloader/U-Boot/trust, p1 FAT,
# p2 ext4 root) followed by a fresh N MiB (default 1024) p3 ext4 rebuilt
# from the captured p3 tar with the same label, UUID and 4.4-safe features.
# The MBR p3 entry is shrunk to match; flash-card.sh --grow extends it.
# Runs rootless on the host (e2fsprogs, sfdisk, zstd); `podman unshare`
# keeps root ownership of p3 files. The output is PRIVATE (Wi-Fi PSK, SSH
# host key, authorized_keys): never commit or share it.
set -euo pipefail
export LC_ALL=C

p3_mib=1024 strip_seed=0
while [ $# -gt 2 ]; do
    case "$1" in
        --p3-mib) p3_mib=$2; shift 2 ;;
        --strip-seed) strip_seed=1; shift ;;
        *) echo "unknown option $1" >&2; exit 2 ;;
    esac
done
[ $# -eq 2 ] || { sed -n '3,4p' "$0"; exit 2; }
cap=$(realpath "$1") out=$(realpath -m "$2")
for f in prefix.img.gz prefix.sha256 p3.tar p3-head.img table.sfdisk; do
    [ -s "$cap/$f" ] || { echo "missing $cap/$f" >&2; exit 1; }
done

mib=$((1024 * 1024)) sec=512
prefix_mib=640 p2_start=262144 p2_sectors=1048576 p3_start=1310720
work=$(mktemp -d "$(dirname "$out")/.work.XXXXXX")
trap 'podman unshare rm -rf "$work"' EXIT
img=$work/card.img

echo "== prefix"
gzip -dc "$cap/prefix.img.gz" > "$img"
(cd "$work" && sed 's/prefix.img/card.img/' "$cap/prefix.sha256" | sha256sum -c --quiet)
[ "$(stat -c %s "$img")" -eq $((prefix_mib * mib)) ]

echo "== p2 check/clean"
dd if="$img" of="$work/p2.img" bs=$sec skip=$p2_start count=$p2_sectors status=none
e2fsck -fn "$work/p2.img" > "$work/p2-fsck.txt" 2>&1 || { cat "$work/p2-fsck.txt"; echo "p2 fsck failed" >&2; exit 1; }
tail -n1 "$work/p2-fsck.txt"
if [ "$strip_seed" = 1 ]; then
    for f in seed.credit seed.no-credit; do
        if debugfs -R "stat /var/lib/muos-seedrng/$f" "$work/p2.img" 2>/dev/null | grep -q '^Inode:'; then
            debugfs -w -R "rm /var/lib/muos-seedrng/$f" "$work/p2.img" >/dev/null 2>&1
            echo "removed seed $f"
        fi
    done
    e2fsck -fy "$work/p2.img" > "$work/p2-fsck2.txt" 2>&1 || [ $? -le 1 ]
    e2fsck -fn "$work/p2.img" >/dev/null 2>&1 || { echo "p2 dirty after seed strip" >&2; exit 1; }
    dd if="$work/p2.img" of="$img" bs=$sec seek=$p2_start conv=notrunc status=none
fi

echo "== p3 rebuild (${p3_mib} MiB)"
sb=$(dumpe2fs -h "$cap/p3-head.img" 2>/dev/null || :)
label=$(sed -n 's/^Filesystem volume name: *//p' <<< "$sb")
uuid=$(sed -n 's/^Filesystem UUID: *//p' <<< "$sb")
features=$(sed -n 's/^Filesystem features: *//p' <<< "$sb" | tr ' ' ',')
[ -n "$label" ] && [ -n "$uuid" ] && [ -n "$features" ]
truncate -s $((p3_mib * mib)) "$work/p3.img"
podman unshare sh -euc '
    mkdir "$1/p3root"; tar -xpf "$2" -C "$1/p3root"
    mkfs.ext4 -q -F -t ext4 -O "none,$3" -b 4096 -I 256 -m 0 -L "$4" -U "$5" \
        -E lazy_itable_init=0,lazy_journal_init=0 -d "$1/p3root" "$1/p3.img"
' sh "$work" "$cap/p3.tar" "$features" "$label" "$uuid"
e2fsck -fn "$work/p3.img" >/dev/null
got=$( (dumpe2fs -h "$work/p3.img" 2>/dev/null || :) | sed -n 's/^Filesystem features: *//p' | tr ' ' ',')
[ "$got" = "$features" ] || { echo "p3 features differ: $got" >&2; exit 1; }
dd if="$work/p3.img" of="$img" bs=$mib seek=$prefix_mib conv=notrunc,sparse status=none
truncate -s $(((prefix_mib + p3_mib) * mib)) "$img"

echo "== partition table"
grep -q 'label-id: 0x4d554432' "$cap/table.sfdisk"
grep -Eq 'p1 : start= *32768, size= *204800, type=c, bootable' "$cap/table.sfdisk"
grep -Eq "p2 : start= *$p2_start, size= *$p2_sectors, type=83" "$cap/table.sfdisk"
grep -Eq "p3 : start= *$p3_start," "$cap/table.sfdisk"
printf '%s\n' 'label: dos' 'label-id: 0x4d554432' 'unit: sectors' \
    'start=32768, size=204800, type=c, bootable' \
    "start=$p2_start, size=$p2_sectors, type=83" \
    "start=$p3_start, size=$((p3_mib * mib / sec)), type=83" |
    sfdisk -q --no-reread --no-tell-kernel "$img"
sfdisk -d "$img" | grep -E "start= *$p3_start, size= *$((p3_mib * mib / sec))" >/dev/null
sfdisk -d "$img" | grep -q 'label-id: 0x4d554432'
dd if="$img" of="$work/p3.chk" bs=$mib skip=$prefix_mib count="$p3_mib" status=none
cmp -s "$work/p3.chk" "$work/p3.img"

echo "== compress"
raw_sum=$(sha256sum "$img" | cut -d' ' -f1)
zstd -q -T0 -12 --long=27 -f "$img" -o "$out"
[ "$(zstd -dc --long=27 "$out" | sha256sum | cut -d' ' -f1)" = "$raw_sum" ]
sha256sum "$out" | sed "s#  .*/#  #" > "$out.sha256"
cat > "${out%.img.zst}.manifest" <<EOF
image=$(basename "$out")
created=$(date -u +%FT%TZ)
raw_bytes=$(stat -c %s "$img")
raw_sha256=$raw_sum
prefix_sha256=$(cut -d' ' -f1 "$cap/prefix.sha256")
p3_mib=$p3_mib p3_label=$label p3_uuid=$uuid
strip_seed=$strip_seed
private=yes  # contains Wi-Fi PSK, SSH host key and authorized_keys
EOF
echo "OK $out raw_sha256=$raw_sum size=$(stat -c %s "$out")"
