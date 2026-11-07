#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
umask 077
dir=${1:-}
case "$dir" in /run/muos-prefs-data.??????) ;; *) exit 64;;esac
[ "$#" = 1 ] && [ ! -L "$dir" ] && [ "$(stat -c '%u:%g:%a' "$dir")" = 0:0:700 ]
state=$dir/state
. /usr/libexec/muos-session/card-guard.sh
. /usr/libexec/muos-session/data-functions.sh
prefs_data_source
! findmnt -rn -S "$prefs_device" >/dev/null
for process in muxretro muxfrontend pipewire muinput;do ! pidof "$process" >/dev/null;done
exec 8>/run/muos/session/lifetime.lock;flock -n 8
prefs_mount=$dir/data
mkdir -m 700 "$prefs_mount"
mounted=0
finish() {
 rc=$?;trap - EXIT HUP INT TERM;cleanup=0
 if findmnt -rn -M "$prefs_mount" >/dev/null;then
  if prefs_data_mounted ro;then umount "$prefs_mount" || cleanup=1;else cleanup=1;fi
 fi
 printf 'OPERATION=%s\nCLEANUP=%s\nREASON=c53-prepare\n' "$rc" "$cleanup" > "$state/result.txt"
 touch "$state/done"
 [ "$cleanup" = 0 ] || exit 125
 exit "$rc"
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
mount -t ext4 -o ro,noload,nosuid,nodev,noexec "$prefs_device" "$prefs_mount"
prefs_data_mounted ro
/bin/sh "$dir/store.sh" "$dir" prepare > "$state/store-prepare.log" 2>&1
prefs_data_mounted ro
printf 'C53_PREPARE_COMPLETE\n' > "$state/core.log"
