#!/bin/sh
# SPDX-License-Identifier: MIT
# One temporary experiment: unload only8821cu before an otherwise normal reboot.
set -eu
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
state=$package/state
bounded=/usr/libexec/muos-run-bounded
[ "$(id -u)" = 0 ] && [ "$(readlink /proc/1/exe)" = /bin/busybox ] || exit 64
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ] || exit 64
[ "$(cat /etc/muos-network-diagnostic)" = MUOS-R35S-NETWORK-P4-C07 ] || exit 64
[ "$(cat /proc/sys/kernel/tainted)" = 0 ] || exit 64
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || exit 64
. /usr/libexec/muos-diag-card-guard
boot=$(diag_card /sys) || exit 64
[ "$boot" = /dev/mmcblk0p1 ] || exit 64
[ "$(findmnt -rn -o MAJ:MIN /)" = "$(cat /sys/class/block/mmcblk0p2/dev)" ] || exit 64
[ -d /sys/module/8821cu ] || exit 64
exec 9>/run/muos/c07/maintenance.lock
flock -n 9 || exit 64
/usr/libexec/muos-c07-network status || exit 64
for name in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog; do
    ! pidof "$name" >/dev/null || exit 64
done
! mountpoint -q /boot || exit 64
sha256sum -c "$package/prerequisites.sha256" >/dev/null || exit 64
sequence=$(sed -n 's/^BOOT_SEQ=\([0-9][0-9]*\) .*/\1/p' /run/muos/c07/report.txt)
case "$sequence" in ''|*[!0-9]*|?????*) exit 64 ;; esac
archive=$(printf 'BOOT%04d' "$sequence")
mkdir "$state" || exit 64
log=$state/report.txt
printf 'MUOS-R35S-NETWORK-UNLOAD-REBOOT\nBOOT_SEQ=%s\n' "$sequence" > "$log"
"$bounded" 3 /usr/libexec/muos-rng-ready 0 >> "$log" || exit 64
mounted=0
stopped=0
reboot_requested=0
finish() {
    trap - EXIT HUP INT TERM
    exec 9>&-
    if [ "$mounted" = 1 ]; then umount /boot || :; fi
    if [ "$reboot_requested" = 0 ] && [ "$stopped" = 1 ]; then
        # On a failed experiment, attempt to restore LAN from the existing key
        # and current RNG state. Never force module removal or force reboot.
        "$bounded" 30 modprobe 8821cu >> "$log" 2>&1 || :
        if "$bounded" 120 /usr/libexec/muos-c07-network recover >> "$log" 2>&1; then
            echo EXPERIMENT_ABORTED_SSH_RESTORED >> "$log"
        else
            echo EXPERIMENT_ABORTED_SSH_NOT_RESTORED >> "$log"
            printf '\033[2J\033[HC07 experiment stopped. Root read-only.\nPower off normally before restarting.\n' > /dev/tty0
        fi
    fi
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
stopped=1
"$bounded" 20 /usr/libexec/muos-c07-network stop >> "$log" 2>&1 || exit 1
echo NETWORK_STOP_RC=0 >> "$log"
"$bounded" 20 rmmod 8821cu >> "$log" 2>&1 || exit 1
[ ! -d /sys/module/8821cu ] || exit 1
echo MODULE_UNLOADED=8821cu >> "$log"
[ "$(cat /proc/sys/kernel/tainted)" = 0 ] || exit 1
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || exit 1
# Public experiment record only; do not touch root, seed, keys or config.
mount -t vfat -o ro,nosuid,nodev,noexec "$boot" /boot || exit 1
mounted=1
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ] || exit 1
[ -d "/boot/DIAG09/$archive" ] && [ ! -e "/boot/DIAG09/$archive/PREBOOT.TXT" ] || exit 1
mount -o remount,rw,nosuid,nodev,noexec /boot || exit 1
echo 'NORMAL_REBOOT_REQUESTED=1 ROOT_RO=1' >> "$log"
cp "$log" "/boot/DIAG09/$archive/PREBOOT.TXT" || exit 1
sync
umount /boot || exit 1
mounted=0
reboot_requested=1
/sbin/reboot || { reboot_requested=0; exit 1; }
