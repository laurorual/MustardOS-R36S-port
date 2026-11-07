#!/bin/sh
# SPDX-License-Identifier: MIT
# C58 read-only seed/verify. No core, ROM, UI, audio or data writer.
set -eu
umask 077
capsule=${1:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
[ "$#" = 1 ] && [ -d "$capsule" ] && [ ! -L "$capsule" ] || exit 64
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
[ ! -e "$capsule/save-store" ] && [ ! -L "$capsule/save-store" ] || exit 64
. /usr/libexec/muos-session/card-guard.sh
. /usr/libexec/muos-session/data-functions.sh
prefs_data_source
if findmnt -rn -S "$prefs_device" >/dev/null; then exit 64; fi
prefs_mount=$capsule/data
mkdir -m 700 "$prefs_mount"
runtime_mounted=0
finish() {
 rc=$?;trap - EXIT HUP INT TERM;cleanup=0
 if findmnt -rn -M "$prefs_mount" >/dev/null; then
  if prefs_data_mounted ro; then umount "$prefs_mount" || cleanup=1;else cleanup=1;fi
 fi
 if [ "$runtime_mounted" = 1 ]; then umount /run/muos || cleanup=1;fi
 printf 'C58_HEADLESS_END status=%s cleanup=%s\n' "$rc" "$cleanup"
 [ "$cleanup" = 0 ] || exit 125
 exit "$rc"
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
# Isolate runtime paths without creating the absent global storage directory.
[ -d /run/muos ] && [ ! -L /run/muos ] || exit 64
mount -t tmpfs -o mode=700,nosuid,nodev,noexec tmpfs /run/muos
runtime_mounted=1
mkdir -m 700 /run/muos/storage
mount -t ext4 -o ro,noload,nosuid,nodev,noexec "$prefs_device" "$prefs_mount"
prefs_data_mounted ro
printf 'MUOS-PREFS-1\nVOLUME=55\nBRIGHTNESS=70\n' | cmp -s - "$prefs_mount/MUOS/preferences/preferences"
/bin/sh "$capsule/store.sh" "$capsule" seed > "$capsule/state/store-seed.log" 2>&1
/bin/sh "$capsule/store.sh" "$capsule" verify > "$capsule/state/store-verify.log" 2>&1
cmp "$capsule/expected-store.sha256" "$capsule/state/store-readonly-before.sha256"
cmp "$capsule/expected-store.sha256" "$capsule/state/store-readonly-after.sha256"
prefs_data_mounted ro
cat "$capsule/state/seed-metadata.txt"
printf 'C58_INSTALLED_BACKEND_SEED_VERIFY_OK store_matches_C54=1 root_ro=1 data_ro=1\n'
