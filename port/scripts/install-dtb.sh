#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Install a Linux DTB on the device's FAT p1, keeping the original once.
#   install-dtb.sh FILE.dtb    back up the live DTB to
#                              rk3326-muos-r35s-panel0-1296.dtb, then install
#   install-dtb.sh --restore   put that backup back
# U-Boot loads /rk3326-muos-r35s-panel0.dtb from p1 at every boot and
# REFUSES any DTB (and kernel Image) whose size or SHA256 differs from the
# values compiled into it (port/device/rk-r35s-p0/uboot-linux/boot.c,
# "Asset read/size check failed"; learnt the hard way in M2). So this tool
# only installs a DTB matching the pinned one unless --uboot-repinned is
# given after U-Boot was rebuilt for it. Recovery if a DTB stops the boot:
# mount the card's FAT elsewhere (dArkOSen slot 2 mounts it at /roms2) and
# copy rk3326-muos-r35s-panel0-1296.dtb over rk3326-muos-r35s-panel0.dtb.
set -euo pipefail
dev=$(dirname "$0")/device.sh
live=/boot/rk3326-muos-r35s-panel0.dtb
backup=/boot/rk3326-muos-r35s-panel0-1296.dtb
if [ "${1:-}" = --restore ]; then
    "$dev" run "set -e; [ -s $backup ]; mount -o remount,rw /boot
        cp $backup $live.new; sync; mv -f $live.new $live; sync; mount -o remount,ro /boot
        sha256sum $live | cut -c1-16"
    exit 0
fi
repinned=0; [ "${1:-}" = --uboot-repinned ] && { repinned=1; shift; }
[ -s "${1:-}" ] || { sed -n '3,15p' "$0"; exit 2; }
pinned=496bbe3591f8619f
if [ "$repinned" = 0 ] && [ "$(sha256sum "$1" | cut -c1-16)" != "$pinned" ]; then
    echo "refusing: U-Boot only boots the pinned DTB ($pinned...); rebuild U-Boot first" >&2; exit 1
fi
want=$(sha256sum "$1" | cut -d' ' -f1)
"$dev" run "set -e; mount -o remount,rw /boot
    [ -s $backup ] || cp $live $backup
    cat > $live.new; sync; mv -f $live.new $live; sync
    mount -o remount,ro /boot
    [ \"\$(sha256sum $live | cut -d' ' -f1)\" = $want ] && echo \"installed $live (backup $backup)\"" < "$1"
