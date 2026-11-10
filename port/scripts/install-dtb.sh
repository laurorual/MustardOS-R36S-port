#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Install a Linux DTB on the device's FAT p1, keeping the original once.
#   install-dtb.sh FILE.dtb    back up the live DTB to
#                              rk3326-muos-r35s-panel0-1296.dtb, then install
#   install-dtb.sh --restore   put that backup back
# U-Boot loads /rk3326-muos-r35s-panel0.dtb from p1 at every boot. If a DTB
# ever prevents booting: mount the card's FAT on another machine (or from
# dArkOSen with the card in slot 2) and copy the -1296.dtb over it.
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
[ -s "${1:-}" ] || { sed -n '3,9p' "$0"; exit 2; }
want=$(sha256sum "$1" | cut -d' ' -f1)
"$dev" run "set -e; mount -o remount,rw /boot
    [ -s $backup ] || cp $live $backup
    cat > $live.new; sync; mv -f $live.new $live; sync
    mount -o remount,ro /boot
    [ \"\$(sha256sum $live | cut -d' ' -f1)\" = $want ] && echo \"installed $live (backup $backup)\"" < "$1"
