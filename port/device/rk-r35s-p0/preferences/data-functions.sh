# SPDX-License-Identifier: MIT
# Diagnostic-only guard for a private mount namespace. Never formats media.
prefs_data_source() {
    # The caller loads its own packaged card guard before entering this API.
    # C11 already does so; never source a boot coordinator during cleanup.
    command -v diag_card >/dev/null 2>&1 || return 64
    [ "$(id -u)" = 0 ] || return 64
    [ "$(readlink /proc/self/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ] || return 64
    [ "$(uname -r)" = 4.4.189-muos-r35s-p4 ] || return 64
    [ "$(tr -d '\000' < /sys/firmware/devicetree/base/model)" = 'R36S-V12 2023-08-18 Panel 0' ] || return 64
    [ "$(cat /proc/sys/kernel/tainted)" = 0 ] || return 64
    [ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ] || return 64
    findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || return 64
    prefs_boot=$(diag_card /sys) || return 64
    [ "$prefs_boot" = /dev/mmcblk0p1 ] || return 64
    prefs_device=/dev/mmcblk0p3
    [ -b "$prefs_device" ] && [ ! -L "$prefs_device" ] || return 64
    [ "$(cat /sys/class/block/mmcblk0p1/start)" = 32768 ] || return 64
    [ "$(cat /sys/class/block/mmcblk0p1/size)" = 204800 ] || return 64
    [ "$(cat /sys/class/block/mmcblk0p2/start)" = 262144 ] || return 64
    [ "$(cat /sys/class/block/mmcblk0p2/size)" = 1048576 ] || return 64
    [ "$(cat /sys/class/block/mmcblk0p3/start)" = 1310720 ] || return 64
    [ "$(cat /sys/class/block/mmcblk0p3/size)" = 248561664 ] || return 64
    [ "$(findmnt -rn -o MAJ:MIN /)" = "$(cat /sys/class/block/mmcblk0p2/dev)" ] || return 64
    [ "$(findmnt -rn -o FSTYPE /)" = ext4 ] || return 64
    [ "$(findmnt -rn -o PARTUUID /)" = 4d554432-02 ] || return 64
    ! findmnt -rn -M /boot >/dev/null || return 64
    [ "$(blkid -p -s UUID -o value "$prefs_device")" = 6d756f73-c020-4000-8000-000000000001 ] || return 64
    [ "$(blkid -p -s TYPE -o value "$prefs_device")" = ext4 ] || return 64
    [ "$(blkid -p -s LABEL -o value "$prefs_device")" = MUOSDATA ] || return 64
}
prefs_data_mount_identity() {
    prefs_mode=$1
    case "$prefs_mode" in ro|rw) ;; *) return 64 ;; esac
    case "$prefs_mount" in
        /run/muos-prefs-data.??????/data|/run/muos/session/run-[0-9][0-9][0-9][0-9]/data) ;;
        *) return 64 ;;
    esac
    prefs_data_source || return 64
    [ ! -L "$prefs_mount" ] || return 64
    [ "$(findmnt -rn -M "$prefs_mount" -o SOURCE,FSTYPE,MAJ:MIN)" = "$prefs_device ext4 $(cat /sys/class/block/mmcblk0p3/dev)" ] || return 64
    prefs_options=$(findmnt -rn -M "$prefs_mount" -o OPTIONS) || return 64
    for prefs_option in "$prefs_mode" nosuid nodev noexec; do
        printf '%s\n' "$prefs_options" | tr ',' '\n' | grep -qx "$prefs_option" || return 64
    done
    ! grep -F " $prefs_mount " /proc/1/mountinfo >/dev/null || return 64
}
prefs_data_mounted() {
    prefs_data_mount_identity "$1" || return 64
    [ "$(stat -c '%u:%g:%a' "$prefs_mount")" = 0:0:755 ] || return 64
    prefs_marker=$prefs_mount/.muos-r35s-data-v1
    [ -f "$prefs_marker" ] && [ ! -L "$prefs_marker" ] || return 64
    [ "$(stat -c '%u:%g:%a:%h' "$prefs_marker")" = 0:0:600:1 ] || return 64
    printf 'MUOS-R35S-DATA-V1\n' | cmp -s - "$prefs_marker" || return 64
    [ ! -L "$prefs_mount/MUOS" ] && [ ! -L "$prefs_mount/MUOS/preferences" ] || return 64
    [ "$(stat -c '%u:%g:%a' "$prefs_mount/MUOS/preferences")" = 0:0:700 ] || return 64
    prefs_marker=$prefs_mount/MUOS/preferences/.muos-preferences-v1
    [ -f "$prefs_marker" ] && [ ! -L "$prefs_marker" ] || return 64
    [ "$(stat -c '%u:%g:%a:%h' "$prefs_marker")" = 0:0:600:1 ] || return 64
    printf 'MUOS-R35S-PREFS-V1\n' | cmp -s - "$prefs_marker" || return 64
}
