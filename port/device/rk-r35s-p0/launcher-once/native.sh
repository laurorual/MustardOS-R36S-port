# SPDX-License-Identifier: MIT
# No configurable root, token, profile or executable paths in the native adapter.
c25_init_child() {
    [ "$(awk '/^PPid:/ {print $2}' /proc/$$/status)" = 1 ]
}
c25_media() {
    [ "$(id -u)" = 0 ] && [ "$(readlink /proc/1/exe)" = /bin/busybox ] || return 64
    [ "$(readlink /proc/self/ns/mnt)" = "$(readlink /proc/1/ns/mnt)" ] || return 64
    [ "$(uname -r)" = 4.4.189-muos-r35s-p4 ] || return 64
    [ "$(tr -d '\000' < /sys/firmware/devicetree/base/model)" = 'R36S-V12 2023-08-18 Panel 0' ] || return 64
    [ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ] && [ "$(cat /proc/sys/kernel/tainted)" = 0 ] || return 64
    [ "$(diag_card /sys)" = /dev/mmcblk0p1 ] || return 64
    [ "$(findmnt -rn -o MAJ:MIN,FSTYPE,PARTUUID /)" = "$(cat /sys/class/block/mmcblk0p2/dev) ext4 4d554432-02" ] || return 64
    ! findmnt -rn -M /boot >/dev/null && ! findmnt -rn -S /dev/mmcblk0p3 >/dev/null || return 64
    [ "$(stat -c '%u:%g:%a' "$c25_store")" = 0:0:700 ] && [ ! -L "$c25_store" ] || return 64
    c25_regular "$c25_store/boot-seq" || return 64
    [ ! -e "$c25_store/c12.once" ] && [ ! -L "$c25_store/c12.once" ] || return 64
    [ ! -d /sys/module/btusb ] || return 64
}
c25_root_mode() { findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx "$1"; }
c25_quiet() {
    for c25_process in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog; do
        ! pidof "$c25_process" >/dev/null || return 64
    done
    for c25_path in /run/dbus/system_bus_socket /run/muos/core/ready /run/muos/port-storage/ready /run/muos/input-ready/ready; do
        [ ! -e "$c25_path" ] || return 64
    done
    for c25_path in /mnt/mmc /opt/muos/config /opt/muos/device/config /opt/muos/share/volume /etc/default/muos-ui /etc/default/muos-core; do
        ! findmnt -rn -M "$c25_path" >/dev/null || return 64
    done
    for c25_info in /proc/[0-9]*/mountinfo; do
        [ -r "$c25_info" ] || continue
        if awk '$4 ~ /^\/(run\/)?muos\/session\/run-[0-9][0-9][0-9][0-9]\// {found=1} END{exit !found}' "$c25_info" 2>/dev/null; then return 64; fi
    done
}
c25_foundation() {
    . /usr/libexec/muos-candidate-boot-checks
    candidate_boot_check && (cd /usr/libexec/muos-c25 && sha256sum -c payload.sha256 >/dev/null)
}
c25_ready() {
    c25_media && c25_root_mode ro && c25_quiet && c25_foundation || return 64
    [ -f /run/muos/entropy/stopped ] && [ ! -e /run/muos/entropy/ready ] || return 64
    grep -qx 'STATUS=0 ROOT_RO=1' /run/muos/c07/report.txt || return 64
    /usr/libexec/muos-c07-network status || return 64
}
c25_durable() { sync; }
c25_publish() (
    # Only whitelisted reports produced here; no network/seed/SSH files.
    c25_ready || return 64
    c25_archive=$(printf 'BOOT%04d' "$(cat "$c25_store/boot-seq")")
    for c25_report in FINAL; do
        c25_regular "$c25_state/$c25_report.TXT" || return 64
        [ "$(wc -c < "$c25_state/$c25_report.TXT")" -le 65536 ] || return 64
    done
    if [ -e "$c25_state/START.TXT" ]; then
        c25_regular "$c25_state/START.TXT" && [ "$(wc -c < "$c25_state/START.TXT")" -le 65536 ] || return 64
    fi
    c25_fat=0
    trap '[ "$c25_fat" = 0 ] || umount /boot' EXIT
    trap 'exit 143' HUP INT TERM
    mount -t vfat -o ro,nosuid,nodev,noexec /dev/mmcblk0p1 /boot || return 1
    c25_fat=1
    c25_publish_result=1
    if [ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ] &&
       mount -o remount,rw,nosuid,nodev,noexec /boot &&
       mkdir -p /boot/DIAG25 && mkdir "/boot/DIAG25/$c25_archive"; then
        c25_publish_result=0
        for c25_report in START FINAL; do
            [ -e "$c25_state/$c25_report.TXT" ] || continue
            cp "$c25_state/$c25_report.TXT" "/boot/DIAG25/$c25_archive/$c25_report.TXT" &&
                cmp "$c25_state/$c25_report.TXT" "/boot/DIAG25/$c25_archive/$c25_report.TXT" || c25_publish_result=1
        done
        sync || c25_publish_result=1
    fi
    umount /boot || return 1
    c25_fat=0
    [ "$c25_publish_result" = 0 ]
)
