#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # container-side commands in single quotes
# T1 (M13): the first boot's Install (muos-install-storage request/apply)
# without a device. The Buildroot target runs as a rootless podman container
# (overlay, nothing written back; aarch64 through qemu binfmt; the script
# from the source tree) on sparse card images with the port's MBR (disk id
# 4d554432, p1 FAT, p2 and p3 ext4 as in the public image) and a first-boot
# p3 tree (settings, a theme marker, logs, empty ROMS folders).
# MUOS_INSTALL_TEST: the table is written with the target's sfdisk, the
# kernel, mount and resize steps are skipped, the new filesystem is made in a
# file and checked with the target's fsck, the state is restored to a folder.
# Cases (32 GiB card):
#   exfat / vfat: p3 to the end, type 7 / c, fsck clean, label; the state
#                 back with factory_reset 0, without the theme markers or
#                 the request
#   ext4 on ext4: p3 grown in place (type 83), no format, factory_reset 0
#   ext4 on an exFAT p3 (an earlier install): formatted ext4, state back
#   a ROM on the card: refused, nothing written, request removed
#   a failing exFAT format: ext4 again with the state and factory_reset 1
#   another disk id: refused
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
target=$repo/build/m3a/output/target
logs=$repo/build/logs; mkdir -p "$logs"
work=$repo/build/t1-install-storage; rm -rf "$work"; mkdir -p "$work"
trap 'rm -rf "$work"' EXIT
[ -x "$target/usr/sbin/mkfs.exfat" ] && [ -x "$target/sbin/mkfs.vfat" ] || { echo "no exfatprogs/dosfstools in $target (build first)" >&2; exit 1; }
src=$repo/port/device/rk-r35s-p0/rootfs/usr/libexec/muos-install-storage
script='set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
w=/w
card() { # NAME GiB [DISKID]
    rm -f "$w/$1"; truncate -s "$2G" "$w/$1"
    printf "label: dos\nlabel-id: 0x%s\nunit: sectors\n\n32768,204800,c\n262144,2097152,83\n2359296,2097152,83\n" "${3:-4d554432}" |
        sfdisk -q "$w/$1" > /dev/null
}
fresh() { # a first-boot p3 tree in $w/t/data (+ request FS)
    rm -rf "$w/t"; d=$w/t/data; mkdir -p "$d/MUOS/port/config/boot" "$d/MUOS/port/config/settings/general" \
        "$d/MUOS/port/seeded-theme" "$d/MUOS/log" "$d/ROMS/NES" "$d/ROMS/SNES" "$d/MUOS/bios"
    echo 1 > "$d/MUOS/port/config/boot/factory_reset"; echo "Portuguese (BR)" > "$d/MUOS/port/config/settings/general/language"
    echo /usr/share/zoneinfo/America/Sao_Paulo > "$d/MUOS/port/config/localtime"
    : > "$d/MUOS/port/seeded-theme/MustardOS"; echo boot > "$d/MUOS/log/system.log"
    printf "MUOS-R35S-DATA-V1\n" > "$d/.muos-r35s-data-v1"
    MUOS_INSTALL_TEST=$w/t /usr/libexec/muos-install-storage request "$1" > /dev/null
}
run() { # LABEL NAME [env] -> rc, table, fs check, state
    env MUOS_INSTALL_TEST=$w/t ${3:-} /usr/libexec/muos-install-storage apply "$w/$2" > /dev/null 2> "$w/t/err"; rc=$?
    tab=$(sfdisk -d "$w/$2" | sed -n "s|^$w/$2\([0-9]\) : start= *\([0-9]*\), size= *\([0-9]*\), type=\([0-9a-f]*\).*|p\1=\2+\3:\4|p" | tr "\n" " ")
    fs=$(cat "$w/t/p3.type" 2>/dev/null || echo -) chk=-
    if [ -f "$w/t/p3.img" ]; then
        case $fs in
            exfat) fsck.exfat -n "$w/t/p3.img" > /dev/null 2>&1 && chk=$(exfatlabel "$w/t/p3.img" 2>/dev/null | sed -n "s/.*[Ll]abel: *//p") || chk=fsck-fail ;;
            vfat) fsck.fat -n "$w/t/p3.img" > /dev/null 2>&1 && chk=$(fatlabel "$w/t/p3.img" 2>/dev/null) || chk=fsck-fail ;;
            ext4) e2fsck -fn "$w/t/p3.img" > /dev/null 2>&1 && chk=$(e2label "$w/t/p3.img" 2>/dev/null) || chk=fsck-fail ;;
        esac
    fi
    r=$w/t/restored st=-
    [ -d "$r" ] && st="factory=$(cat "$r/MUOS/port/config/boot/factory_reset") lang=$(tr " " _ < "$r/MUOS/port/config/settings/general/language") zone=$(cat "$r/MUOS/port/config/localtime") marker=$([ -f "$r/.muos-r35s-data-v1" ] && echo y || echo n) themes=$(ls "$r/MUOS/port/seeded-theme" 2>/dev/null | wc -l) req=$([ -e "$r/MUOS/port/install-storage" ] && echo y || echo n) log=$(grep -c "" "$r/MUOS/log/install-storage.log" 2>/dev/null)"
    inplace="factory=$(cat "$w/t/data/MUOS/port/config/boot/factory_reset") req=$([ -e "$w/t/data/MUOS/port/install-storage" ] && echo y || echo n)"
    echo "case $1: rc=$rc table=[$tab] fs=$fs check=[$chk] state=[$st] data=[$inplace] err=[$(tail -n 1 "$w/t/err")]"
}
card c32.img 32; fresh exfat; run exfat c32.img
card c32.img 32; fresh vfat; run vfat c32.img
card c32.img 32; fresh ext4; run ext4-in-place c32.img
card c32.img 32; fresh ext4; echo exfat > "$w/t/p3.type"; run ext4-over-exfat c32.img
card c32.img 32; fresh exfat; : > "$w/t/data/ROMS/NES/game.nes"; run rom-on-card c32.img
card c32.img 32; fresh exfat; run exfat-fails c32.img MUOS_INSTALL_FAIL=exfat
card cx.img 32 12345678; fresh exfat; run foreign cx.img'
podman run --rm --network=none -v "$work:/w:z" -v "$src:/usr/libexec/muos-install-storage:ro" --rootfs "$target:O" \
    /bin/sh -c "$script" > "$logs/t1-install-storage.log" 2>&1 || :
cat "$logs/t1-install-storage.log"
l=$logs/t1-install-storage.log
G=$((1024 * 1024 * 2)) p3=2359296
head="p1=32768+204800:c p2=262144+2097152:83"
full="p3=$p3+$((32 * G - p3))"
st0="factory=0 lang=Portuguese_(BR) zone=/usr/share/zoneinfo/America/Sao_Paulo marker=y themes=0 req=n log="
ok=1
expect() { grep -qF -- "$1" "$l" || { echo "MISSING: $1"; ok=0; }; }
expect "case exfat: rc=0 table=[$head $full:7 ] fs=exfat check=[MustardOS] state=[$st0"
expect "case vfat: rc=0 table=[$head $full:c ] fs=vfat check=[MUSTARDOS] state=[$st0"
expect "case ext4-in-place: rc=0 table=[$head $full:83 ] fs=- check=[-] state=[-] data=[factory=0 req=n]"
expect "case ext4-over-exfat: rc=0 table=[$head $full:83 ] fs=ext4 check=[MUOSDATA] state=[$st0"
expect "case rom-on-card: rc=1 table=[$head p3=$p3+2097152:83 ] fs=- check=[-] state=[-] data=[factory=1 req=n] err=[the card already has files in ROMS"
expect "case exfat-fails: rc=1 table=[$head $full:83 ] fs=ext4 check=[MUOSDATA] state=[factory=1 lang=Portuguese_(BR)"
expect "case foreign: rc=1 table=[p1=32768+204800:c p2=262144+2097152:83 p3=$p3+2097152:83 ] fs=- check=[-] state=[-] data=[factory=1 req=y] err=[not the port card (disk id)]"
if [ "$ok" = 1 ]; then echo 'PASS install storage (exfat, vfat, ext4 grow, ext4 over exfat, a card with games, a failing format, foreign card)'
else echo 'FAIL install storage'; exit 1; fi
