#!/bin/sh
# SPDX-License-Identifier: MIT
# Whitelisted public reports only; no recursive collection of runtime/private data.
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
boot_package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 64
. "$boot_package/native-functions.sh"
c12_guard || exit 64
case "${1:-}" in START|FINAL|PBEGIN|PFAIL|PREADY) phase=$1 ;; *) exit 64 ;; esac
state=/run/muos/boot-diagnostic
sequence=$(cat "$state/sequence") || exit 64
case "$sequence" in ''|*[!0-9]*|?????*) exit 64 ;; esac
[ "$sequence" -gt 0 ] && [ "$sequence" -le 9999 ] || exit 64
report=$state/$phase.txt
[ -f "$report" ] && [ ! -L "$report" ] && [ "$(stat -c %s "$report")" -le 65536 ] || exit 64
archive=$(printf 'BOOT%04d' "$sequence")
mounted=0
cleanup() { if [ "$mounted" = 1 ]; then umount /boot || return 1; mounted=0; fi; }
trap 'cleanup' EXIT
trap 'exit 1' HUP INT TERM
mount -t vfat -o ro,nosuid,nodev,noexec "$boot_partition" /boot || exit 1
mounted=1
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ] || exit 64
destination=/boot/DIAG10/$archive
case "$phase" in PBEGIN|PFAIL|PREADY)
    # Never shut the network down until the completed diagnostic is durable.
    cmp "$state/FINAL.txt" "$destination/FINAL.TXT" || exit 64 ;;
esac
mount -o remount,rw,nosuid,nodev,noexec /boot || exit 1
mkdir -p /boot/DIAG10 || exit 1
if [ "$phase" = START ]; then mkdir "$destination" || exit 1
else [ -d "$destination" ] && [ -f "$destination/START.TXT" ] || exit 1; fi
[ ! -e "$destination/$phase.TXT" ] && [ ! -e "$destination/$phase.TMP" ] || exit 64
cp "$report" "$destination/$phase.TMP" && mv "$destination/$phase.TMP" "$destination/$phase.TXT" || exit 1
sync || exit 1
cmp "$report" "$destination/$phase.TXT" || exit 1
cleanup || exit 1
trap - EXIT
