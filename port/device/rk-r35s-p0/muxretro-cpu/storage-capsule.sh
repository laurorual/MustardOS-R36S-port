#!/bin/sh
# SPDX-License-Identifier: MIT
# One-shot private storage rehearsal. No graphics, audio, input or power service.
set -eu
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
dir=${1:-}
[ "$#" = 1 ] || exit 64
case "$dir" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
[ -d "$dir" ] && [ ! -L "$dir" ]
[ "$(stat -c '%u:%g:%a' "$dir")" = 0:0:700 ]
[ "$(readlink /proc/self/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ]
package=/usr/libexec/muos-session
. "$package/card-guard.sh"
. "$package/data-functions.sh"
prefs_data_source
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
for process in muxretro pipewire wireplumber muinput muxfrontend; do
    if pidof "$process" >/dev/null; then exit 64; fi
done
if findmnt -rn -S "$prefs_device" >/dev/null; then exit 64; fi
if findmnt -rn -M /userdata >/dev/null; then exit 64; fi
if findmnt -rn -M /etc/default/muos-storage >/dev/null; then exit 64; fi
prefs_mount=$dir/data
mounted_data=0; mounted_userdata=0; mounted_config=0; storage_attempted=0
cleanup() {
    result=$?
    trap - EXIT HUP INT TERM
    if [ "$storage_attempted" = 1 ]; then /etc/init.d/S90muos-storage stop || result=1; fi
    if [ "$mounted_config" = 1 ]; then umount /etc/default/muos-storage || result=1; fi
    if [ "$mounted_userdata" = 1 ]; then umount /userdata || result=1; fi
    if [ "$mounted_data" = 1 ]; then
        (cd "$prefs_mount/MUOS/preferences" && find . -type f -exec sha256sum '{}' ';' | sort) > "$dir/preferences-after.sha256" || result=1
        cmp "$dir/preferences-before.sha256" "$dir/preferences-after.sha256" || result=1
        umount "$prefs_mount" || result=1
    fi
    exit "$result"
}
trap cleanup EXIT
trap 'exit 143' HUP INT TERM
mkdir -m 700 "$prefs_mount" "$dir/ramdata"
mount -t ext4 -o ro,noload,nosuid,nodev,noexec "$prefs_device" "$prefs_mount"
mounted_data=1
prefs_data_mounted ro
[ -z "$(find "$prefs_mount/MUOS/preferences" -type l -print)" ]
(cd "$prefs_mount/MUOS/preferences" && find . -type f -exec sha256sum '{}' ';' | sort) > "$dir/preferences-before.sha256"
mkdir -m 700 "$dir/ramdata/MUOS"
cp -a "$prefs_mount/MUOS/preferences" "$dir/ramdata/MUOS/preferences"
"$package/bin/muos-preferences" --dir "$dir/ramdata/MUOS/preferences" load > "$dir/preferences-loaded.txt"
printf 'MUOS-PREFS-1\nVOLUME=55\nBRIGHTNESS=70\n' | cmp -s - "$dir/preferences-loaded.txt"
cat "$dir/preferences-loaded.txt"
printf 'fstype=tmpfs\n' > "$dir/storage.conf"
chmod 600 "$dir/storage.conf"
mount --bind "$dir/ramdata" /userdata
mounted_userdata=1
mount --bind "$dir/storage.conf" /etc/default/muos-storage
mounted_config=1
[ "$(findmnt -rn -o FSTYPE -T /userdata)" = tmpfs ]
storage_attempted=1
/etc/init.d/S90muos-storage start
/etc/init.d/S90muos-storage status
[ "$(findmnt -rn -o FSTYPE -T /run/muos/storage/pickles)" = tmpfs ]
[ "$(stat -c '%d:%i' /run/muos/storage/pickles)" = "$(stat -c '%d:%i' "$dir/ramdata/MUOS/pickles")" ]
[ ! -e "$prefs_mount/MUOS/pickles/c43-probe" ]
printf 'C43_RAM_ONLY\n' > /run/muos/storage/pickles/c43-probe
cmp /run/muos/storage/pickles/c43-probe "$dir/ramdata/MUOS/pickles/c43-probe"
cmp /run/muos/storage/pickles/c43-probe /mnt/mmc/MUOS/pickles/c43-probe
rm /run/muos/storage/pickles/c43-probe
[ ! -e "$prefs_mount/MUOS/pickles/c43-probe" ]
prefs_data_mounted ro
echo C43_STORAGE_ALIASES_RAM_REAL_PREFERENCES_RO_UNCHANGED
