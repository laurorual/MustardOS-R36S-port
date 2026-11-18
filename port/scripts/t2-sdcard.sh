#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M5 T2: secondary storage (slot 2) through the port's
# script/device/storage.sh, with a loop device standing in for the card
# (MUOS_SD2_TEST_DISK): vfat and exFAT images (build/m5/sd2, made with
# mkfs.vfat/mkfs.exfat on the host) and an unformatted one. For each:
# mount -> /mnt/sdcard with the right type, ROMS/ARCHIVE/ports created,
# device storage/sdcard/active = 1, the SFTP jail lists "Secondary Storage"
# (when web/sftp is on); eject -> unmounted, active = 0. Real slot-2
# detection (controller path, udev rule) needs a card: T3.
set -euo pipefail
cd "$(dirname "$0")"
repo=$(cd ../.. && pwd)
dev=./device.sh
pass() { printf 'PASS %s\n' "$*"; }
fail() { printf 'FAIL %s\n' "$*"; cleanup; exit 1; }
r() { "$dev" run "cd /; $*"; }
S=/opt/muos/script/device/storage.sh
ip=$(cat "$repo/build/device/ip")
tmp=$repo/build/device/t2-sdcard; mkdir -p "$tmp"
sed "s/^[^ ]*/[$ip]:2022/" "$repo/build/device/known_hosts" > "$tmp/known"
printf '#!/bin/sh\necho muos\n' > "$tmp/askpass"; chmod 700 "$tmp/askpass"
jail_ls() { # the jail root as the menu's SFTP user sees it
    echo ls | SSH_ASKPASS=$tmp/askpass SSH_ASKPASS_REQUIRE=force DISPLAY=none \
        setsid -w sftp -q -oBatchMode=no -b - -P 2022 -oUserKnownHostsFile="$tmp/known" \
        -oStrictHostKeyChecking=yes -oPubkeyAuthentication=no -oPreferredAuthentications=password \
        -oNumberOfPasswordPrompts=1 -oConnectTimeout=10 "muos@$ip" 2>&1
}
cleanup() {
    r "grep -q ' /mnt/sdcard ' /proc/mounts && umount /mnt/sdcard; for l in \$(losetup -a 2>/dev/null | grep /run/t2-sd2 | cut -d: -f1); do losetup -d \$l; done
       rm -f /run/t2-sd2-*.img; echo 0 > /opt/muos/device/config/storage/sdcard/active" || :
}
r "test -x $S" || fail "no $S"
r "grep -q ' /mnt/sdcard ' /proc/mounts" && fail '/mnt/sdcard is in use (a real card?)'
for fs in vfat exfat; do
    "$dev" push "$repo/build/m5/sd2/$fs.img.gz" /run > /dev/null
    r "gunzip -f /run/$fs.img.gz && mv /run/$fs.img /run/t2-sd2-$fs.img"
done
r "dd if=/dev/zero of=/run/t2-sd2-none.img bs=1M count=8 2>/dev/null"
sftp_on=$(r 'cat /opt/muos/config/web/sftp 2>/dev/null || echo 0')
for fs in vfat exfat; do
    loop=$(r "l=\$(losetup -f) && losetup \$l /run/t2-sd2-$fs.img && echo \$l")
    d=${loop#/dev/}
    out=$(r "MUOS_SD2_TEST_DISK=$d $S sdcard mount; echo rc=\$?")
    echo "$out" | grep -q 'rc=0' || fail "$fs mount: $out"
    t=$(r "awk '\$2 == \"/mnt/sdcard\" {print \$3}' /proc/mounts")
    [ "$t" = "$fs" ] || fail "$fs mounted as '$t'"
    r 'test -d /mnt/sdcard/ROMS -a -d /mnt/sdcard/ARCHIVE -a -d /mnt/sdcard/ports' || fail "$fs folders"
    [ "$(r 'cat /opt/muos/device/config/storage/sdcard/active')" = 1 ] || fail "$fs active flag"
    # only on the mounted card (never into the root's /mnt/sdcard); BusyBox
    # ls prints '?' for non-ASCII, so the name is checked by lookup and
    # by remount (the name must survive the filesystem's encoding)
    r "grep -q ' /mnt/sdcard $fs ' /proc/mounts && mkdir -p /mnt/sdcard/ROMS/GB && echo t2 > '/mnt/sdcard/ROMS/GB/Ação teste.gb' &&
       umount /mnt/sdcard && MUOS_SD2_TEST_DISK=$d $S sdcard mount > /dev/null && test -s '/mnt/sdcard/ROMS/GB/Ação teste.gb' &&
       [ \$(find /mnt/sdcard/ROMS/GB -name 'A*o teste.gb' | wc -l) = 1 ]" || fail "$fs UTF-8 name"
    [ "$(r "$S sdcard status")" = mounted ] || fail "$fs status"
    again=$(r "MUOS_SD2_TEST_DISK=$d $S sdcard mount; echo rc=\$?")
    echo "$again" | grep -q 'rc=0' || fail "$fs second mount: $again"
    pass "$fs: mounted at /mnt/sdcard, folders, active=1, UTF-8 names, idempotent"
    if [ "$sftp_on" = 1 ]; then
        jail_ls | grep -q 'Secondary Storage' || fail "$fs: SFTP jail lacks Secondary Storage"
        pass "$fs: SFTP jail lists Secondary Storage"
    fi
    out=$(r "$S sdcard eject; echo rc=\$?")
    echo "$out" | grep -q 'rc=0' || fail "$fs eject: $out"
    r "grep -q ' /mnt/sdcard ' /proc/mounts" && fail "$fs still mounted"
    [ "$(r 'cat /opt/muos/device/config/storage/sdcard/active')" = 0 ] || fail "$fs active after eject"
    r "losetup -d $loop"
    pass "$fs: ejected, active=0"
done
loop=$(r "l=\$(losetup -f) && losetup \$l /run/t2-sd2-none.img && echo \$l")
out=$(r "MUOS_SD2_TEST_DISK=${loop#/dev/} $S sdcard mount; echo rc=\$?" || :)
echo "$out" | grep -q 'rc=1' || fail "unformatted card accepted: $out"
r "grep -q ' /mnt/sdcard ' /proc/mounts" && fail 'unformatted card mounted'
pass 'unformatted card refused (rc=1, nothing mounted)'
cleanup
r "$S sdcard status" > /dev/null && fail 'status says mounted after cleanup' || :
pass 'cleanup: no loop devices, /mnt/sdcard free'
