#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M3a image stage (called by build-image.sh image NAME):
#
#   firmware-image.sh ROOTFS.ext4 BASE.img.zst BASE_RAW_PREFIX OUT.img.zst BOOT_DIR
#
# The card image is the base recovery image (bootloader at 64/16384/24576,
# p1 FAT, the MBR and a 1 GiB p3) with p2 replaced by the Buildroot rootfs.
# The device identity (dropbear host key, network.conf with the Wi-Fi PSK,
# the authorized key) is copied from the base p2 with its modes; it is
# never printed. Also writes OUT without .img.zst + .p2.img (the raw p2, for
# the trial root) next to build/m3a. M3b: BOOT_DIR (build-boot.sh output)
# supplies uboot.img (sector 16384) and the kernel + DTB, copied to p1 under
# content names; boot records: main = them, previous = the M2 Image + DTB
# already on p1, no trial. Runs rootless on the host (e2fsprogs, mtools,
# dosfstools, zstd). The output is PRIVATE: never commit or share it.
set -euo pipefail
export LC_ALL=C
[ $# -eq 5 ] || { sed -n '4p' "$0"; exit 2; }
rootfs=$(realpath "$1") base=$(realpath "$2") base_raw=$3 out=$(realpath -m "$4") bootd=$(realpath "$5")
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
p2_start=262144 p2_sectors=1048576 p1_start=32768 p1_sectors=204800
m2_image=780935823cb8c86e4330c8c8157ebb4005fb5580e68e72c4b0c4e480bab42d2f
m2_dtb=496bbe3591f8619f059ebc384277ecdd17fd41f956aef40de20afb46b92d5b49
private=(/var/lib/muos-network/dropbear_ed25519_host_key /var/lib/muos-network/network.conf
    /etc/muos-network-authorized_key)

grep -q "^raw_sha256=$base_raw" "${base%.img.zst}.manifest" || { echo 'base manifest mismatch' >&2; exit 1; }
(cd "$(dirname "$base")" && sha256sum -c --quiet "$(basename "$base").sha256")
[ "$(stat -c %s "$rootfs")" -eq $((p2_sectors * 512)) ] || { echo 'rootfs is not 512 MiB' >&2; exit 1; }
mkdir -p "$(dirname "$out")"
work=$(mktemp -d "$repo/build/m3a/.image.XXXXXX")
trap 'rm -rf "$work"' EXIT
img=$work/card.img

echo "== base $(basename "$base")"
zstd -q -dc --long=27 "$base" | dd of="$img" bs=1M conv=sparse status=none
grep -q "^raw_sha256=$(sha256sum "$img" | cut -d' ' -f1)" "${base%.img.zst}.manifest"
dd if="$img" of="$work/base-p2.img" bs=512 skip=$p2_start count=$p2_sectors status=none

echo "== p2 from $(basename "$rootfs") + device identity"
cp --reflink=auto "$rootfs" "$work/p2.img"
cmds=$work/debugfs.cmds; : > "$cmds"
for p in "${private[@]}"; do
    st=$(debugfs -R "stat $p" "$work/base-p2.img" 2>/dev/null)
    mode=$(sed -n 's/.*Mode: *\([0-7]*\).*/\1/p' <<< "$st" | head -1)
    [ -n "$mode" ] || { echo "base p2 lacks $p" >&2; exit 1; }
    f=$work/priv.$(basename "$p")
    debugfs -R "dump -p $p $f" "$work/base-p2.img" >/dev/null 2>&1
    [ -s "$f" ]
    d=${p%/*}
    debugfs -R "stat $d" "$work/p2.img" 2>/dev/null | grep -q 'Type: directory' ||
        printf 'mkdir %s\nsif %s mode 040700\n' "$d" "$d" >> "$cmds"
    printf 'cd %s\nrm %s\nwrite %s %s\ncd /\nsif %s mode 0100%s\nsif %s uid 0\nsif %s gid 0\n' \
        "$d" "${p##*/}" "$f" "${p##*/}" "$p" "$mode" "$p" "$p" >> "$cmds"
done
debugfs -w -f "$cmds" "$work/p2.img" >/dev/null 2>&1
rm -f "$work"/priv.*
for p in "${private[@]}"; do
    a=$(debugfs -R "cat $p" "$work/base-p2.img" 2>/dev/null | sha256sum)
    b=$(debugfs -R "cat $p" "$work/p2.img" 2>/dev/null | sha256sum)
    [ "$a" = "$b" ] || { echo "identity copy differs: $p" >&2; exit 1; }
done
e2fsck -fn "$work/p2.img" > "$work/fsck.txt" 2>&1 || { cat "$work/fsck.txt"; echo 'p2 fsck failed' >&2; exit 1; }
features=$( (dumpe2fs -h "$work/p2.img" 2>/dev/null || :) | sed -n 's/^Filesystem features: *//p')
for bad in 64bit metadata_csum_seed orphan_file fast_commit; do
    ! grep -qw "$bad" <<< "$features" || { echo "p2 has $bad (not 4.4-safe)" >&2; exit 1; }
done
label=$( (dumpe2fs -h "$work/p2.img" 2>/dev/null || :) | sed -n 's/^Filesystem volume name: *//p')
[ "$label" = ROOTFS ] || { echo "p2 label $label" >&2; exit 1; }
bash "$repo/port/scripts/check-rootfs-contract.sh" "$work/p2.img" || { echo 'p2 breaks the runtime contract' >&2; exit 1; }
dd if="$work/p2.img" of="$img" bs=512 seek=$p2_start conv=notrunc status=none
cmp -s "$work/p2.img" <(dd if="$img" bs=512 skip=$p2_start count=$p2_sectors status=none)
p2_sum=$(sha256sum "$work/p2.img" | cut -d' ' -f1)

echo "== boot chain: U-Boot, p1 kernel, boot records"
sha() { sha256sum "$1" | cut -d' ' -f1; }
(cd "$bootd" && sha256sum -c --quiet SHA256SUMS)
p1="$img@@$((p1_start * 512))" kimg=$bootd/Image kdtb=$bootd/rk3326-muos-r35s-panel0.dtb
mcopy -n -i "$p1" ::Image "$work/m2.Image"
mcopy -n -i "$p1" ::rk3326-muos-r35s-panel0.dtb "$work/m2.dtb"
[ "$(sha "$work/m2.Image")" = "$m2_image" ] && [ "$(sha "$work/m2.dtb")" = "$m2_dtb" ] ||
    { echo 'base p1 does not hold the M2 kernel' >&2; exit 1; }
kin=Image-$(sha "$kimg" | cut -c1-12) kdn=panel0-$(sha "$kdtb" | cut -c1-12).dtb
mcopy -o -i "$p1" "$kimg" "::$kin"
mcopy -o -i "$p1" "$kdtb" "::$kdn"
mcopy -n -i "$p1" "::$kin" "$work/chk.img"; mcopy -n -i "$p1" "::$kdn" "$work/chk.dtb"
cmp "$kimg" "$work/chk.img" && cmp "$kdtb" "$work/chk.dtb"
# Phase 4 leftovers on the M2 base's p1 (M3e): the DIAGnn log folders,
# PROBE.TXT and the empty tools folder. Nothing in the boot chain reads
# them (U-Boot loads only the files the boot records name). DIAG.ID stays
# (Phase 4 tooling checks it).
for f in $(mdir -b -i "$p1" :: | sed -n 's|^::/\([^/]*\)/\{0,1\}$|\1|p' | grep -E '^(DIAG[0-9]+|PROBE\.TXT|tools)$'); do
    mdeltree -i "$p1" "::$f" 2>/dev/null || mdel -i "$p1" "::$f"
done
dd if="$img" of="$work/p1.img" bs=512 skip=$p1_start count=$p1_sectors status=none
fsck.fat -n "$work/p1.img" > "$work/fsck-p1.txt" 2>&1 || { cat "$work/fsck-p1.txt"; echo 'p1 fsck failed' >&2; exit 1; }
rm -f "$work/p1.img" "$work/chk.img" "$work/chk.dtb"
br=$repo/port/scripts/bootrec.py klabel="m3b $(sha "$kimg" | cut -c1-8)"
python3 "$br" encode valid "$kimg" "$kdtb" "$klabel" "$work/main.rec" --image-name "$kin" --fdt-name "$kdn"
python3 "$br" encode valid "$work/m2.Image" "$work/m2.dtb" 'm2 4.4.189' "$work/prev.rec" \
    --image-name Image --fdt-name rk3326-muos-r35s-panel0.dtb
head -c 512 /dev/zero > "$work/trial.rec"
cat "$work/main.rec" "$work/prev.rec" "$work/trial.rec" | dd of="$img" bs=512 seek=32 conv=notrunc status=none
[ "$(stat -c %s "$bootd/uboot.img")" = 4194304 ] || { echo 'uboot.img is not 4 MiB' >&2; exit 1; }
dd if="$bootd/uboot.img" of="$img" bs=512 seek=16384 conv=notrunc status=none
cmp -s "$bootd/uboot.img" <(dd if="$img" bs=512 skip=16384 count=8192 status=none)
cmp -s <(cat "$work/main.rec" "$work/prev.rec" "$work/trial.rec") <(dd if="$img" bs=512 skip=32 count=3 status=none)
uboot_sum=$(sha "$bootd/uboot.img")
echo "main: $kin + $kdn ($klabel); previous: Image + rk3326-muos-r35s-panel0.dtb (m2)"

echo "== compress"
raw_sum=$(sha256sum "$img" | cut -d' ' -f1)
zstd -q -T0 -12 --long=27 -f "$img" -o "$out"
[ "$(zstd -dc --long=27 "$out" | sha256sum | cut -d' ' -f1)" = "$raw_sum" ]
sha256sum "$out" | sed "s#  .*/#  #" > "$out.sha256"
mv "$work/p2.img" "$repo/build/m3a/$(basename "${out%.img.zst}").p2.img"
cat > "${out%.img.zst}.manifest" <<EOF
image=$(basename "$out")
created=$(date -u +%FT%TZ)
raw_bytes=$(stat -c %s "$img")
raw_sha256=$raw_sum
p2_sha256=$p2_sum
rootfs_sha256=$(sha256sum "$rootfs" | cut -d' ' -f1)
base=$(basename "$base") base_raw_sha256=$(sed -n 's/^raw_sha256=//p' "${base%.img.zst}.manifest")
p2_features=$(tr ' ' ',' <<< "$features")
uboot_sha256=$uboot_sum
boot_main=$kin,$kdn,$(sha "$kimg"),$(sha "$kdtb")
boot_previous=Image,rk3326-muos-r35s-panel0.dtb,$m2_image,$m2_dtb
private=yes  # contains Wi-Fi PSK, SSH host key and authorized_keys
EOF
echo "OK $out raw_sha256=$raw_sum p2_sha256=$p2_sum size=$(stat -c %s "$out")"
