#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
case "${1:-}" in /run/muos-c24.??????) deployment=$1 ;; *) exit 64 ;; esac
case "${2:-}" in inspect|backup|apply|rollback) action=$2 ;; *) exit 64 ;; esac
update_root=/;update_payload=$deployment/payload;update_rw=0
. "$deployment/card-guard.sh"
. "$deployment/transaction.sh"
c24_media() {
    [ "$(id -u)" = 0 ] && [ "$(readlink /proc/1/exe)" = /bin/busybox ] || return 64
    [ "$(readlink /proc/self/ns/mnt)" = "$(readlink /proc/1/ns/mnt)" ] || return 64
    [ "$(uname -r)" = 4.4.189-muos-r35s-p4 ] || return 64
    [ "$(tr -d '\000' < /sys/firmware/devicetree/base/model)" = 'R36S-V12 2023-08-18 Panel 0' ] || return 64
    [ "$(cat /proc/sys/kernel/tainted)" = 0 ] && [ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ] || return 64
    c24_boot=$(diag_card /sys) || return 64
    [ "$c24_boot" = /dev/mmcblk0p1 ] || return 64
    [ "$(findmnt -rn -o MAJ:MIN,FSTYPE,PARTUUID /)" = "$(cat /sys/class/block/mmcblk0p2/dev) ext4 4d554432-02" ] || return 64
    ! findmnt -rn -M /boot >/dev/null && ! findmnt -rn -S /dev/mmcblk0p3 >/dev/null || return 64
}
c24_ro() { findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro; }
c24_quiet() {
    for c24_process in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog;do ! pidof "$c24_process" >/dev/null || return 64;done
    for c24_path in /run/dbus/system_bus_socket /run/muos/arborist.sock /run/muos/arborist.pid /run/muos/core/ready /run/muos/port-storage/ready /run/muos/input-ready/ready;do [ ! -e "$c24_path" ] || return 64;done
    for c24_path in /mnt/mmc /opt/muos/config /opt/muos/device/config /opt/muos/share/volume /etc/default/muos-ui /etc/default/muos-core;do ! findmnt -rn -M "$c24_path" >/dev/null || return 64;done
    for c24_info in /proc/[0-9]*/mountinfo;do
        [ -r "$c24_info" ] || continue
        if awk '$4 ~ /^\/(run\/)?muos\/session\/run-[0-9][0-9][0-9][0-9]\// {found=1} END {exit !found}' "$c24_info" 2>/dev/null;then return 64;fi
    done
}
c24_private_fingerprint() {
    # Emit only one aggregate into owned RAM. Never export private bytes.
    for c24_private in /var/lib/muos-network /var/lib/muos-seedrng /root/.ssh /var/lib/muos-diagnostic/boot-seq;do
        [ -e "$c24_private" ] || continue
        find "$c24_private" -type f -exec sha256sum '{}' ';'
        find "$c24_private" -exec stat -c '%n:%u:%g:%a' '{}' ';'
    done | LC_ALL=C sort | sha256sum
}
c24_guard() {
    c24_media && c24_ro && c24_quiet || return 64
    [ "$(cat /etc/muos-network-diagnostic)" = MUOS-R35S-NETWORK-P4-C07 ] || return 64
    if [ "$action" = rollback ];then
        [ "$(cat /var/lib/muos-diagnostic/boot-seq)" -ge "$(cat "$update_payload/boot-seq")" ] || return 64
    else [ "$(cat /var/lib/muos-diagnostic/boot-seq)" = "$(cat "$update_payload/boot-seq")" ] || return 64;fi
    [ -f /run/muos/entropy/stopped ] && [ ! -e /run/muos/entropy/ready ] || return 64
    [ ! -e /var/lib/muos-diagnostic/c12.once ] && [ ! -L /var/lib/muos-diagnostic/c12.once ] || return 64
    [ ! -d /sys/module/btusb ] || return 64
    /usr/libexec/muos-c07-network status || return 64
    c24_needed=$(du -sk "$update_payload/new" | awk '{print $1}')
    c24_available=$(df -Pk / | awk 'NR==2{print $4}')
    [ "$c24_available" -ge "$((c24_needed*3+16384))" ] || return 64
    if [ "$action" = rollback ];then
        (cd / && sha256sum -c "$update_payload/after.sha256" && sha256sum -c "$update_payload/unchanged.sha256") >/dev/null || return 64
    else (cd / && sha256sum -c "$update_payload/foundation-before.sha256") >/dev/null || return 64;fi
}
update_exec() {
    case "$1" in
      guard) c24_guard ;;
      rw) c24_media && mount -o remount,rw / ;;
      ro) mount -o remount,ro / && c24_ro ;;
      sync) sync ;;
      file-installed|file-staged) return 0 ;;
      verify-before) (cd / && sha256sum -c "$update_payload/foundation-before.sha256") >/dev/null || return 1; c24_private_fingerprint > "$deployment/private.after";cmp "$deployment/private.before" "$deployment/private.after" ;;
      verify-after)
        . /usr/libexec/muos-candidate-boot-checks
        candidate_boot_check || return 1
        (cd /usr/libexec/muos-session && sha256sum -c payload.sha256) >/dev/null || return 1
        c24_private_fingerprint > "$deployment/private.after"
        cmp "$deployment/private.before" "$deployment/private.after" && /usr/libexec/muos-c07-network status ;;
      *) return 64 ;;
    esac
}
finish() {
    rc=$?;trap - EXIT HUP INT TERM
    if [ "$update_rw" = 1 ];then
        c24_rollback > "$deployment/rollback.log" 2>&1;rollback_rc=$?
        printf 'ROLLBACK_RC=%s\n' "$rollback_rc"
        [ "$rollback_rc" = 0 ] || rc=1
    fi
    c24_ro || rc=1
    case "$action" in apply|rollback)
        printf '%s\n' "$rc" > "$deployment/$action.result"
        touch "$deployment/$action.done" ;;
    esac
    exit "$rc"
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
c24_guard || exit 64
mkdir -p /run/muos/session;chmod 700 /run/muos/session
exec 8>/run/muos/session/lifetime.lock
flock -n 8 || exit 64
case "$action" in
 inspect) c24_preflight || exit $?;echo C24_INSPECT_OK_NO_PERSISTENT_WRITE ;;
 backup) c24_backup || exit $?;c24_private_fingerprint > "$deployment/private.before";echo C24_BACKUP_OK_NO_PERSISTENT_WRITE ;;
 apply)
    [ -f "$deployment/private.before" ] || exit 64
    c24_private_fingerprint > "$deployment/private.now";cmp "$deployment/private.before" "$deployment/private.now" || exit 64
    mkdir "$deployment/apply.once" || exit 64
    c24_apply || exit $?
    echo C24_APPLIED_ROOT_RO_PRIVATE_STATE_PRESERVED_NO_TOKEN_NO_REBOOT ;;
 rollback)
    mkdir "$deployment/rollback.once" || exit 64
    c24_private_fingerprint > "$deployment/private.before"
    update_rw=1
    c24_rollback || exit $?
    echo C24_ROLLBACK_ROOT_RO_CURRENT_PRIVATE_STATE_PRESERVED ;;
esac
