#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M3a image stage (called by build-image.sh image NAME):
#
#   firmware-image.sh ROOTFS.ext4 BASE.img.zst BASE_RAW_PREFIX OUT.img.zst BOOT_DIR [public]
#
# public (M4a): no developer identity at all. p2 gets no Wi-Fi config, host
# key or authorized key (dropbear stays off until the user enables SSH in
# muOS; the host key is created on p3 then), root gets a password hash
# (MUOS_PUBLIC_ROOT_PASSWORD, default "root" like upstream muOS: a decision
# for the user, see STATUS.md), p3 is a fresh empty MUOSDATA with only the
# data marker, and check-public-image.sh must pass (also against the base
# p2's secrets). The manifest says private=no.
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
[ $# -eq 5 ] || [ $# -eq 6 ] || { sed -n '4p' "$0"; exit 2; }
rootfs=$(realpath "$1") base=$(realpath "$2") base_raw=$3 out=$(realpath -m "$4") bootd=$(realpath "$5")
variant=${6:-developer}
case "$variant" in developer|public) ;; *) echo "variant $variant" >&2; exit 2 ;; esac
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
# M8 (decision 17): p2 is 1 GiB. The M2 base has p2 = 512 MiB and a 1 GiB p3
# at 1310720; the base p3 moves behind the new p2 and the MBR entries for p2
# and p3 are rewritten (same disk identifier, so PARTUUIDs stay).
p2_start=262144 p2_sectors=2097152 p1_start=32768 p1_sectors=204800
base_p2_sectors=1048576 base_p3_start=1310720 p3_start=2359296 p3_sectors=2097152
m2_image=780935823cb8c86e4330c8c8157ebb4005fb5580e68e72c4b0c4e480bab42d2f
m2_dtb=496bbe3591f8619f059ebc384277ecdd17fd41f956aef40de20afb46b92d5b49
private=(/var/lib/muos-network/dropbear_ed25519_host_key /var/lib/muos-network/network.conf
    /etc/muos-network-authorized_key)

grep -q "^raw_sha256=$base_raw" "${base%.img.zst}.manifest" || { echo 'base manifest mismatch' >&2; exit 1; }
(cd "$(dirname "$base")" && sha256sum -c --quiet "$(basename "$base").sha256")
[ "$(stat -c %s "$rootfs")" -eq $((p2_sectors * 512)) ] || { echo 'rootfs is not 1 GiB' >&2; exit 1; }
mkdir -p "$(dirname "$out")"
work=$(mktemp -d "$repo/build/m3a/.image.XXXXXX")
trap 'rm -rf "$work"' EXIT
img=$work/card.img

echo "== base $(basename "$base")"
zstd -q -dc --long=27 "$base" | dd of="$img" bs=1M conv=sparse status=none
grep -q "^raw_sha256=$(sha256sum "$img" | cut -d' ' -f1)" "${base%.img.zst}.manifest"
dd if="$img" of="$work/base-p2.img" bs=512 skip=$p2_start count=$base_p2_sectors status=none
echo "== layout: p2 $((p2_sectors / 2048)) MiB, p3 moved to sector $p3_start"
sfdisk -d "$img" > "$work/base.sfdisk"
grep -q "^$img""2 : start= *$p2_start, size= *$base_p2_sectors," "$work/base.sfdisk" &&
    grep -q "^$img""3 : start= *$base_p3_start, size= *$p3_sectors," "$work/base.sfdisk" ||
    { cat "$work/base.sfdisk"; echo 'base layout is not the M2 one' >&2; exit 1; }
dd if="$img" of="$work/base-p3.raw" bs=512 skip=$base_p3_start count=$p3_sectors conv=sparse status=none
truncate -s $(( (p3_start + p3_sectors) * 512 )) "$img"
# zero the old p3 and the p2 growth (the new p3 overlaps the old one, and
# the sparse copy below skips zero blocks)
fallocate -p -o $(( (p2_start + base_p2_sectors) * 512 )) -l $(( (p3_start + p3_sectors - p2_start - base_p2_sectors) * 512 )) "$img"
dd if="$work/base-p3.raw" of="$img" bs=512 seek=$p3_start conv=notrunc,sparse status=none
cmp -s "$work/base-p3.raw" <(dd if="$img" bs=512 skip=$p3_start count=$p3_sectors status=none)
rm -f "$work/base-p3.raw"
sed -e "s|^\($img""2 : start= *$p2_start, size= *\)$base_p2_sectors,|\1$p2_sectors,|" \
    -e "s|^\($img""3 : start= *\)$base_p3_start,|\1$p3_start,|" "$work/base.sfdisk" |
    sfdisk -q --no-reread --no-tell-kernel "$img" >/dev/null
sfdisk -d "$img" > "$work/new.sfdisk"
grep -q "^$img""2 : start= *$p2_start, size= *$p2_sectors," "$work/new.sfdisk" &&
    grep -q "^$img""3 : start= *$p3_start, size= *$p3_sectors," "$work/new.sfdisk" &&
    [ "$(grep '^label-id' "$work/base.sfdisk")" = "$(grep '^label-id' "$work/new.sfdisk")" ] ||
    { cat "$work/new.sfdisk"; echo 'relayout failed' >&2; exit 1; }

cp --reflink=auto "$rootfs" "$work/p2.img"
cmds=$work/debugfs.cmds; : > "$cmds"
if [ "$variant" = public ]; then
    echo "== p2 from $(basename "$rootfs"), public: no identity, root password set"
    salt=$(od -An -tx1 -N8 /dev/urandom | tr -d ' \n')
    hash=$(openssl passwd -6 -salt "$salt" "${MUOS_PUBLIC_ROOT_PASSWORD:-root}")
    debugfs -R 'cat /etc/shadow' "$work/p2.img" 2>/dev/null |
        awk -F: -v OFS=: -v h="$hash" '$1 == "root" { $2 = h } { print }' > "$work/shadow"
    grep -q "^root:[\$]6[\$]" "$work/shadow" || { echo 'no root line in /etc/shadow' >&2; exit 1; }
    printf 'cd /etc\nrm shadow\nwrite %s shadow\ncd /\nsif /etc/shadow mode 0100600\nsif /etc/shadow uid 0\nsif /etc/shadow gid 0\n' "$work/shadow" > "$cmds"
    debugfs -w -f "$cmds" "$work/p2.img" >/dev/null 2>&1
    rm -f "$work/shadow"; : > "$cmds"
    for p in "${private[@]}"; do
        ! debugfs -R "stat $p" "$work/p2.img" 2>/dev/null | grep -q '^Inode:' || { echo "rootfs holds $p" >&2; exit 1; }
    done
    private=()
else
    echo "== p2 from $(basename "$rootfs") + device identity"
fi
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
[ ${#private[@]} = 0 ] || debugfs -w -f "$cmds" "$work/p2.img" >/dev/null 2>&1
rm -f "$work"/priv.*
for p in "${private[@]}"; do
    a=$(debugfs -R "cat $p" "$work/base-p2.img" 2>/dev/null | sha256sum)
    b=$(debugfs -R "cat $p" "$work/p2.img" 2>/dev/null | sha256sum)
    [ "$a" = "$b" ] || { echo "identity copy differs: $p" >&2; exit 1; }
done
# M9: the release name (muos-update compares it with GitHub's latest) and,
# in developer images, the marker that keeps muos-update auto off.
echo "release=$(basename "${out%.img.zst}")" > "$work/release"
{ printf 'cd /etc\nwrite %s muos-port-release\n' "$work/release"
  [ "$variant" = public ] || printf 'write %s muos-developer\n' "$work/release"
  for f in muos-port-release $([ "$variant" = public ] || echo muos-developer); do
      printf 'sif /etc/%s mode 0100644\nsif /etc/%s uid 0\nsif /etc/%s gid 0\n' "$f" "$f" "$f"
  done; } > "$cmds"
debugfs -w -f "$cmds" "$work/p2.img" >/dev/null 2>&1; rm -f "$work/release"; : > "$cmds"
[ "$(debugfs -R 'cat /etc/muos-port-release' "$work/p2.img" 2>/dev/null)" = "release=$(basename "${out%.img.zst}")" ] ||
    { echo 'release stamp failed' >&2; exit 1; }
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
# M9 (decision 28): undervolted DTBs next to the stock one, every CPU
# 25..100 x GPU 0..75 mV combination in 25 mV steps (Danger Settings ->
# Undervolt and its two voltage rows; default -50/-25, the M8 thermal
# block's choice); dtb-variants.txt tells muos-undervolt which is which
# (off by default: the boot records keep the stock DTB).
printf 'stock=%s\n' "$kdn" > "$work/dtb-variants.txt"
for c in 25 50 75 100; do for g in 0 25 50 75; do
    "$repo/port/scripts/make-dtb-uv.sh" "$kdtb" "$work/uv.dtb" $c $g > /dev/null
    n=panel0-$(sha "$work/uv.dtb" | cut -c1-12).dtb
    mcopy -o -i "$p1" "$work/uv.dtb" "::$n"
    mcopy -n -i "$p1" "::$n" "$work/chk.uv"; cmp "$work/uv.dtb" "$work/chk.uv"
    echo "uv-$c-$g=$n" >> "$work/dtb-variants.txt"
    [ "$c-$g" != 50-25 ] || { udn=$n; cp "$work/uv.dtb" "$work/uv-default.dtb"; }
done; done
echo "undervolt=$udn" >> "$work/dtb-variants.txt"
mcopy -o -i "$p1" "$work/dtb-variants.txt" ::dtb-variants.txt
rm -f "$work/chk.uv" "$work/uv.dtb"
# M8: the boot logo U-Boot shows (uboot-boot/boot.c), derived from the
# rootfs splash so both stages show the same picture.
python3 "$repo/port/scripts/make-boot-logo.py" --bmp \
    "$repo/port/device/rk-r35s-p0/rootfs/usr/share/muos-r35s/bootlogo.fb.gz" "$work/bootlogo.bmp"
mcopy -o -i "$p1" "$work/bootlogo.bmp" ::bootlogo.bmp
mcopy -n -i "$p1" ::bootlogo.bmp "$work/chk.bmp"; cmp "$work/bootlogo.bmp" "$work/chk.bmp"
rm -f "$work/bootlogo.bmp" "$work/chk.bmp"
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

if [ "$variant" = public ]; then
    echo "== p3: fresh MUOSDATA (same features as the base p3), data marker only"
    dd if="$img" of="$work/base-p3.img" bs=512 skip=$p3_start count=$p3_sectors conv=sparse status=none
    h=$(dumpe2fs -h "$work/base-p3.img" 2>/dev/null)
    v() { sed -n "s/^$1: *//p" <<< "$h"; }
    feat=$(v 'Filesystem features' | tr ' ' ',')
    [ "$(v 'Filesystem volume name')" = MUOSDATA ] || { echo 'base p3 is not MUOSDATA' >&2; exit 1; }
    rm -f "$work/base-p3.img"
    truncate -s $((p3_sectors * 512)) "$work/p3.img"
    mke2fs -q -F -t ext4 -O "none,$feat" -b "$(v 'Block size')" -I "$(v 'Inode size')" -N "$(v 'Inode count')" \
        -m 0 -L MUOSDATA -U "$(v 'Filesystem UUID')" "$work/p3.img"
    printf 'MUOS-R35S-DATA-V1\n' > "$work/marker"
    printf 'write %s .muos-r35s-data-v1\nsif /.muos-r35s-data-v1 mode 0100600\nsif /.muos-r35s-data-v1 uid 0\nsif /.muos-r35s-data-v1 gid 0\n' \
        "$work/marker" > "$cmds"
    debugfs -w -f "$cmds" "$work/p3.img" >/dev/null 2>&1
    h2=$(dumpe2fs -h "$work/p3.img" 2>/dev/null)
    for k in 'Filesystem features' 'Block size' 'Inode size' 'Inode count' 'Filesystem UUID' 'Reserved GDT blocks'; do
        [ "$(sed -n "s/^$k: *//p" <<< "$h2")" = "$(v "$k")" ] || { echo "p3 $k differs from the base" >&2; exit 1; }
    done
    e2fsck -fn "$work/p3.img" > "$work/fsck3.txt" 2>&1 || { cat "$work/fsck3.txt"; echo 'p3 fsck failed' >&2; exit 1; }
    dd if="$work/p3.img" of="$img" bs=512 seek=$p3_start conv=notrunc,sparse status=none
    rm -f "$work/p3.img" "$work/marker"
    echo "== public check"
    bash "$repo/port/scripts/check-public-image.sh" "$img" "$work/base-p2.img" || { echo 'public check failed' >&2; exit 1; }
fi

echo "== compress"
raw_sum=$(sha256sum "$img" | cut -d' ' -f1)
zstd -q -T0 -12 --long=27 -f "$img" -o "$out"
[ "$(zstd -dc --long=27 "$out" | sha256sum | cut -d' ' -f1)" = "$raw_sum" ]
sha256sum "$out" | sed "s#  .*/#  #" > "$out.sha256"
if [ "$variant" = public ]; then
    # M9: the update assets for the GitHub release (muos-update auto/stage)
    n=$(basename "${out%.img.zst}")
    # the card image for users: Etcher, Rufus and Pi Imager read .xz, not .zst
    xz -T0 -6 -c "$img" > "${out%.zst}.xz"
    (cd "$(dirname "$out")" && sha256sum "$n.img.xz" > "$n.img.xz.sha256")
    gzip -9 -c "$work/p2.img" > "${out%.img.zst}.p2.img.gz"
    echo "$p2_sum  $n.p2.img" > "${out%.img.zst}.p2.img.sha256"
fi
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
boot_undervolt=$udn,$(sha "$work/uv-default.dtb")
$([ "$variant" = public ] && echo 'private=no  # public variant: check-public-image.sh passed' || echo 'private=yes  # contains Wi-Fi PSK, SSH host key and authorized_keys')
EOF
echo "OK $out raw_sha256=$raw_sum p2_sha256=$p2_sum size=$(stat -c %s "$out")"
