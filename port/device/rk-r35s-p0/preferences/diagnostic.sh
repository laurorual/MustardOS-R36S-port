#!/bin/sh
# SPDX-License-Identifier: MIT
# Opt-in C20 only: never called by init, C11 or C12.
set -eu
umask 077
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "$base" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
case "${1:-}" in initialize|verify-after-reboot) operation=$1 ;; *) exit 64 ;; esac
. "$base/card-guard.sh"
. "$base/data-functions.sh"
prefs_mount=$base/data
owned=0
cleanup() {
    if [ "$owned" = 1 ]; then
        prefs_data_mount_identity "$mounted_mode" || return 1
        umount "$prefs_mount" || return 1
        owned=0
    fi
}
finish() { rc=$?;trap - EXIT;cleanup || rc=1;exit "$rc"; }
trap finish EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
mount_data() {
    mounted_mode=$1
    prefs_data_source
    mount -t ext4 -o "$mounted_mode,nosuid,nodev,noexec,data=ordered" "$prefs_device" "$prefs_mount"
    owned=1
    prefs_data_mounted "$mounted_mode"
}
if prefs_data_mounted rw; then exit 1; fi
echo PASS_UNMOUNTED_GUARD_REFUSES
mount_data ro
cleanup
mount_data rw
store=$prefs_mount/MUOS/preferences
if [ "$operation" = initialize ]; then
    [ ! -e "$store/preferences" ]
    "$base/muos-preferences" --dir "$store" init > "$base/default"
    printf 'MUOS-PREFS-1\nVOLUME=100\nBRIGHTNESS=80\n' | cmp -s - "$base/default"
    "$base/muos-preferences" --dir "$store" save 60 75 > "$base/saved"
else
    [ -f "$store/preferences" ]
fi
"$base/muos-preferences" --dir "$store" init > "$base/loaded"
printf 'MUOS-PREFS-1\nVOLUME=60\nBRIGHTNESS=75\n' | cmp -s - "$base/loaded"
cleanup
mount_data ro
printf 'MUOS-PREFS-1\nVOLUME=60\nBRIGHTNESS=75\n' | cmp -s - "$store/preferences"
set +e
"$base/muos-preferences" --dir "$store" save 60 75
rc=$?
set -e
[ "$rc" = 64 ]
echo PASS_READONLY_MEDIA_REFUSES
cleanup
mount_data rw
"$base/muos-preferences" --dir "$store" load
cleanup
trap - EXIT
echo DATA_NATIVE_60_75_OK_ROOT_RO_NO_GLOBAL_MOUNT
