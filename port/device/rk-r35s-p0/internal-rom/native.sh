#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
rom_cap=${1:-};operation=${2:-}
case "$rom_cap" in /run/muos-prefs-data.??????) ;;*) exit 64;;esac
case "$operation:$#" in inspect:2|apply:2|verify:2) ;;*) exit 64;;esac
[ -d "$rom_cap" ] && [ ! -L "$rom_cap" ] && [ "$(stat -c '%u:%g:%a' "$rom_cap")" = 0:0:700 ]
[ "$(findmnt -rn -T "$rom_cap" -o FSTYPE)" = tmpfs ]
. "$rom_cap/functions.sh"
. /usr/libexec/muos-session/card-guard.sh;. /usr/libexec/muos-session/data-functions.sh
prefs_mount=$rom_cap/data;rom_mount=$prefs_mount;owned=0
prefs_data_source
! findmnt -rn -S "$prefs_device" >/dev/null
exec 9>/run/muos/session/lifetime.lock;flock -n 9
[ ! -e "$prefs_mount" ] && [ ! -L "$prefs_mount" ];mkdir -m 700 "$prefs_mount"
finish() {
 rc=$?;trap - EXIT HUP INT TERM
 if [ "$owned" = 1 ];then umount "$prefs_mount" || rc=74;fi
 rmdir "$prefs_mount" || rc=74
 printf 'C113_END operation=%s status=%s\n' "$operation" "$rc"
 exit "$rc"
}
trap finish EXIT;trap 'exit 143' HUP INT TERM
mount_ro() {
 mount -t ext4 -o ro,noload,nosuid,nodev,noexec "$prefs_device" "$prefs_mount";owned=1
 prefs_data_mounted ro
}
unmount() { umount "$prefs_mount";owned=0; }
rom_exec() { case "$1" in sync) shift;"$rom_cap/sync-path" "$@";;directory-created|ROM-copied|before-publish|after-publish) return 0;;*) return 64;;esac; }
case "$operation" in
 inspect)
  mount_ro;rom_absent
  [ "$(du -sk "$prefs_mount" | awk '{print $1}')" -le 65536 ]
  rom_inventory > "$rom_cap/before.tree"
  tar -cf "$rom_cap/before.tar" -C "$prefs_mount" .
  rom_inventory > "$rom_cap/inspect-after.tree";cmp "$rom_cap/before.tree" "$rom_cap/inspect-after.tree"
  printf 'C113_INSPECT_RO_BACKUP_COMPLETE\n'
  ;;
 apply)
  rom_inputs
  [ -f "$rom_cap/host-backup-verified" ] && [ ! -L "$rom_cap/host-backup-verified" ]
  printf 'C113_INDEPENDENT_BACKUP_VERIFIED\n' | cmp -s - "$rom_cap/host-backup-verified"
  [ ! -e "$rom_cap/apply.once" ] && [ ! -L "$rom_cap/apply.once" ];mkdir -m 700 "$rom_cap/apply.once"
  mount_ro;rom_absent;rom_inventory > "$rom_cap/apply-before.tree";cmp "$rom_cap/before.tree" "$rom_cap/apply-before.tree"
  unmount
  mount -t ext4 -o rw,nosuid,nodev,noexec,data=ordered "$prefs_device" "$prefs_mount";owned=1
  prefs_data_mounted rw;rom_absent;rom_inventory > "$rom_cap/rw-before.tree";cmp "$rom_cap/before.tree" "$rom_cap/rw-before.tree"
  rom_write
  rom_inventory > "$rom_cap/after-write.tree";cmp "$rom_cap/before.tree" "$rom_cap/after-write.tree"
  unmount;mount_ro
  rom_check "$rom_mount/MUOS/port-roms-v1"
  rom_inventory > "$rom_cap/after-remount.tree";cmp "$rom_cap/before.tree" "$rom_cap/after-remount.tree"
  printf 'C113_ROM_INTERNAL_IMPORTED_RO_VERIFIED\n'
  ;;
 verify)
  mount_ro;rom_inputs;rom_check "$rom_mount/MUOS/port-roms-v1"
  rom_inventory > "$rom_cap/verify.tree";cmp "$rom_cap/before.tree" "$rom_cap/verify.tree"
  printf 'C113_ROM_INTERNAL_VERIFY_NO_WRITE\n'
  ;;
esac
