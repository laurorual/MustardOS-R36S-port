#!/bin/sh
# SPDX-License-Identifier: MIT
# C52 actual-data inventory. Read-only, no service/UI/game and no initialization.
set -eu
umask 077
dir=${1:-}
[ "$#" = 1 ]
case "$dir" in /run/muos-prefs-data.??????) ;; *) exit 64;;esac
[ -d "$dir" ] && [ ! -L "$dir" ]
[ "$(stat -c '%u:%g:%a' "$dir")" = 0:0:700 ]
. /usr/libexec/muos-session/card-guard.sh
. /usr/libexec/muos-session/data-functions.sh
prefs_data_source
! findmnt -rn -S "$prefs_device" >/dev/null
prefs_mount=$dir/data
mkdir -m 700 "$prefs_mount"
mounted=0
finish() {
    rc=$?;trap - EXIT HUP INT TERM
    if [ "$mounted" = 1 ];then umount "$prefs_mount" || rc=74;fi
    exit "$rc"
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
mount -t ext4 -o ro,noload,nosuid,nodev,noexec "$prefs_device" "$prefs_mount"
mounted=1
prefs_data_mounted ro
[ -z "$(find "$prefs_mount/MUOS/preferences" -type l -print)" ]
(cd "$prefs_mount/MUOS/preferences" && find . -type f -exec sha256sum '{}' ';' | sort) > "$dir/preferences-before.sha256"
record=$prefs_mount/MUOS/preferences/preferences
[ "$(stat -c '%u:%g:%a:%h' "$record")" = 0:0:600:1 ]
printf 'MUOS-PREFS-1\nVOLUME=55\nBRIGHTNESS=70\n' | cmp -s - "$record"
for leaf in pickles save port-saves-v1;do
    path=$prefs_mount/MUOS/$leaf
    if [ -e "$path" ] || [ -L "$path" ];then
        [ -d "$path" ] && [ ! -L "$path" ]
        printf 'C52_DATA_PATH name=%s present=1 mode=%s\n' "$leaf" "$(stat -c '%u:%g:%a' "$path")"
    else
        printf 'C52_DATA_PATH name=%s present=0\n' "$leaf"
    fi
done
(cd "$prefs_mount/MUOS/preferences" && find . -type f -exec sha256sum '{}' ';' | sort) > "$dir/preferences-after.sha256"
cmp "$dir/preferences-before.sha256" "$dir/preferences-after.sha256"
prefs_data_mounted ro
printf 'C52_REAL_DATA_RO_NOLOAD_PREFS_UNCHANGED\n'
