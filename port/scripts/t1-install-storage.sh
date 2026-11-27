#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # container-side commands in single quotes
# T1 (M13): the first boot's Install (muos-install-storage) without a
# device. The Buildroot target runs as a rootless podman container (overlay,
# nothing written back; aarch64 through qemu binfmt) on sparse card images
# with the port's MBR (disk id 4d554432, p1 FAT, p2 and p3 ext4 as in the
# public image). MUOS_INSTALL_TEST: the table is written with the target's
# sfdisk, kernel/mount steps are skipped, p4's filesystem is made in a file
# and checked with the target's fsck. Cases:
#   32 GiB: exfat -> p3 6 GiB + p4 type 7 (exFAT, fsck clean); again (p4
#           kept); vfat on that table (type c, FAT32 fsck clean); ext4 on it
#           (p4 removed, p3 to the end)
#   12 GiB: exfat -> p3 4 GiB + p4
#   6 GiB:  exfat refused (too small), factory_reset untouched; ext4 ok
#   another disk id: refused
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
target=$repo/build/m3a/output/target
logs=$repo/build/logs; mkdir -p "$logs"
work=$repo/build/t1-install-storage; rm -rf "$work"; mkdir -p "$work"
trap 'rm -rf "$work"' EXIT
[ -x "$target/usr/sbin/mkfs.exfat" ] && [ -x "$target/sbin/mkfs.vfat" ] || { echo "no exfatprogs/dosfstools in $target (build first)" >&2; exit 1; }
script='set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
w=/w
card() { # NAME GiB [DISKID]
    rm -f "$w/$1"; truncate -s "$2G" "$w/$1"
    printf "label: dos\nlabel-id: 0x%s\nunit: sectors\n\n32768,204800,c\n262144,2097152,83\n2359296,2097152,83\n" "${3:-4d554432}" |
        sfdisk -q "$w/$1" > /dev/null
}
run() { # NAME FS -> rc, table, fs check
    rm -rf "$w/t"; mkdir -p "$w/t/boot"; echo 1 > "$w/t/boot/factory_reset"
    MUOS_INSTALL_TEST=$w/t /usr/libexec/muos-install-storage "$2" "$w/$1" > "$w/t/out" 2> "$w/t/err"; rc=$?
    last=$(tail -n 1 "$w/t/out"); f=$(cat "$w/t/boot/factory_reset")
    tab=$(sfdisk -d "$w/$1" | sed -n "s|^$w/$1\([0-9]\) : start= *\([0-9]*\), size= *\([0-9]*\), type=\([0-9a-f]*\).*|p\1=\2+\3:\4|p" | tr "\n" " ")
    chk=-
    if [ -f "$w/t/p4.img" ]; then
        case $2 in
            exfat) fsck.exfat -n "$w/t/p4.img" > /dev/null 2>&1 && chk=$(exfatlabel "$w/t/p4.img" 2>/dev/null | sed -n "s/.*[Ll]abel: *//p") || chk=fsck-fail ;;
            vfat) fsck.fat -n "$w/t/p4.img" > /dev/null 2>&1 && chk=$(fatlabel "$w/t/p4.img" 2>/dev/null) || chk=fsck-fail ;;
        esac
    fi
    echo "case $1 $2: rc=$rc last=[$last] factory=$f table=[$tab] p4fs=[$chk] err=[$(tail -n 1 "$w/t/err")]"
}
card c32.img 32; run c32.img exfat; run c32.img exfat; run c32.img vfat; run c32.img ext4
card c12.img 12; run c12.img exfat
card c6.img 6; run c6.img exfat; run c6.img ext4
card cx.img 32 12345678; run cx.img exfat'
# the script from the source tree (the target has the packages: exfatprogs, dosfstools)
src=$repo/port/device/rk-r35s-p0/rootfs/usr/libexec/muos-install-storage
podman run --rm --network=none -v "$work:/w:z" -v "$src:/usr/libexec/muos-install-storage:ro" --rootfs "$target:O" /bin/sh -c "$script" > "$logs/t1-install-storage.log" 2>&1 || :
cat "$logs/t1-install-storage.log"
l=$logs/t1-install-storage.log
G=$((1024 * 1024 * 2)) # sectors per GiB
p3=2359296
ok=1
expect() { grep -qF -- "$1" "$l" || { echo "MISSING: $1"; ok=0; }; }
# 32 GiB card = 67108864 sectors; p3 6 GiB; p4 from the next MiB
s4=$(( (p3 + 6 * G + 2047) / 2048 * 2048 ))
expect "case c32.img exfat: rc=0 last=[progress 6 6] factory=0 table=[p1=32768+204800:c p2=262144+2097152:83 p3=$p3+$((6 * G)):83 p4=$s4+$((32 * G - s4)):7 ] p4fs=[MustardOS]"
expect "case c32.img vfat: rc=0 last=[progress 6 6] factory=0 table=[p1=32768+204800:c p2=262144+2097152:83 p3=$p3+$((6 * G)):83 p4=$s4+$((32 * G - s4)):c ] p4fs=[MUSTARDOS]"
expect "case c32.img ext4: rc=0 last=[progress 6 6] factory=0 table=[p1=32768+204800:c p2=262144+2097152:83 p3=$p3+$((32 * G - p3)):83 ]"
[ "$(grep -c '^case c32.img exfat: rc=0' "$l")" = 2 ] || { echo 'MISSING: the repeated exfat install'; ok=0; }
s4=$(( (p3 + 4 * G + 2047) / 2048 * 2048 ))
expect "case c12.img exfat: rc=0 last=[progress 6 6] factory=0 table=[p1=32768+204800:c p2=262144+2097152:83 p3=$p3+$((4 * G)):83 p4=$s4+$((12 * G - s4)):7 ] p4fs=[MustardOS]"
expect "case c6.img exfat: rc=1 last=[progress 1 6] factory=1 table=[p1=32768+204800:c p2=262144+2097152:83 p3=$p3+2097152:83 ]"; expect "too small for a separate games storage"
expect "case c6.img ext4: rc=0 last=[progress 6 6] factory=0 table=[p1=32768+204800:c p2=262144+2097152:83 p3=$p3+$((6 * G - p3)):83 ]"
expect "case cx.img exfat: rc=1 "; expect "not the port card (disk id)"
if [ "$ok" = 1 ]; then echo 'PASS install storage (exfat, vfat, ext4, retry, small card, foreign card)'; else echo 'FAIL install storage'; exit 1; fi
