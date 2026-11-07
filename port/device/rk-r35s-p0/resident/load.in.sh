#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
resident_system_root=/;resident_root=/usr/libexec/muos-resident
resident_manifest_sha=@MANIFEST_SHA@
[ ! -L "$resident_root/functions.sh" ] && [ "$(stat -c '%u:%g:%a:%h' "$resident_root/functions.sh")" = 0:0:644:1 ] || exit 64
[ "$(sha256sum "$resident_root/functions.sh" | cut -d' ' -f1)" = @FUNCTIONS_SHA@ ] || exit 64
. "$resident_root/functions.sh"
resident_exec() {
 case "$1" in
 platform)
  c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
  . /usr/libexec/muos-c25/policy.sh;. /usr/libexec/muos-c25/card-guard.sh;. /usr/libexec/muos-c25/native.sh
  c25_ready ;;
 read-rom) /usr/libexec/muos-session/mount-namespace /bin/sh "$resident_root/load.sh" read-rom "$2" ;;
 prepare) sh /usr/libexec/muos-capsule-v3/prepare.sh prepare "$2" >/dev/null ;;
 *) return 64;;esac
}
case "${1:-}:$#" in
 check:1) resident_package && resident_exec platform || exit 64;echo C112_RESIDENT_CHECK_OK_NO_UI ;;
 prepare:2) resident_prepare "$2";echo C112_RESIDENT_PREPARED_ZERO_UPLOADS ;;
 read-rom:2)
  cap=$2;resident_capsule "$cap" && resident_package && resident_inputs "$cap" 4 || exit 64
  . /usr/libexec/muos-session/card-guard.sh;. /usr/libexec/muos-session/data-functions.sh
  prefs_mount=$cap/data;owned=0
  prefs_data_source
  ! findmnt -rn -S "$prefs_device" >/dev/null
  [ ! -e "$prefs_mount" ] && [ ! -L "$prefs_mount" ];mkdir -m 700 "$prefs_mount"
  cleanup() { rc=$?;trap - EXIT HUP INT TERM;if [ "$owned" = 1 ];then umount "$prefs_mount" || rc=74;fi;rmdir "$prefs_mount" || rc=74;exit "$rc"; }
  trap cleanup EXIT;trap 'exit 143' HUP INT TERM
  mount -t ext4 -o ro,noload,nosuid,nodev,noexec "$prefs_device" "$prefs_mount";owned=1
  prefs_data_mounted ro
  resident_rom_copy "$prefs_mount" "$cap"
  ;;
 *) exit 64;;esac
