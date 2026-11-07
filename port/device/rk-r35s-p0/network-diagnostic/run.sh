#!/bin/sh
# SPDX-License-Identifier: MIT
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
state=/run/muos/c07
screen() { printf '\033[37;40m\033[2J\033[H%s\n' "$1" > /dev/tty0; }
park() { while :; do sleep 3600; done; }
[ "$(cat /etc/muos-network-diagnostic 2>/dev/null)" = MUOS-R35S-NETWORK-P4-C07 ] || exit 64
[ "$(readlink /proc/1/exe)" = /bin/busybox ] || exit 64
if [ "${1:-}" = stop ]; then
    /usr/libexec/muos-c07-network stop
    /etc/init.d/S10udev stop >/dev/null 2>&1
    exit 0
fi
mkdir -p "$state"
printf '3 4 1 7\n' > /proc/sys/kernel/printk
sequence_dir=/var/lib/muos-diagnostic
[ ! -L "$sequence_dir" ] && [ "$(stat -c '%u:%g:%a' "$sequence_dir")" = 0:0:700 ] || exit 64
sequence=$(cat "$sequence_dir/boot-seq")
case "$sequence" in ''|*[!0-9]*|?????*) exit 64 ;; esac
[ "$sequence" -lt 9999 ] || exit 64
sequence=$((sequence+1))
printf '%s\n' "$sequence" > "$sequence_dir/boot-seq.tmp" &&
    chmod 600 "$sequence_dir/boot-seq.tmp" &&
    mv "$sequence_dir/boot-seq.tmp" "$sequence_dir/boot-seq" || exit 64
archive=$(printf 'BOOT%04d' "$sequence")
last_step=none
last_rc=0
step() {
    step_name=$1; seconds=$2; shift 2
    /usr/libexec/muos-run-bounded "$seconds" "$@" > "$state/$step_name.log" 2>&1
    step_rc=$?
    printf 'STEP=%s LIMIT=%s RC=%s\n' "$step_name" "$seconds" "$step_rc" >> "$state/steps.txt"
    if [ "$step_rc" != 0 ]; then last_step=$step_name; last_rc=$step_rc; return 1; fi
}
screen 'muOS - R35S / Panel 0
C07: waiting for RNG, Wi-Fi and DHCP...
No frontend or audio in this test.'
status=0
step entropy-start 90 /etc/init.d/S05muos-entropy start || status=1
if [ "$status" = 0 ]; then
    step udev 45 /etc/init.d/S10udev start || status=1
fi
if [ "$status" = 0 ]; then
    step usb-mode 120 /usr/libexec/muos-c07-usb-mode || status=1
fi
if [ "$status" = 0 ]; then
    step network 120 /usr/libexec/muos-c07-network start || status=1
fi
# Persist native seed rotation before idle root becomes read-only.
step entropy-stop 30 /etc/init.d/S05muos-entropy stop || status=1
if [ "$status" != 0 ]; then /usr/libexec/muos-c07-network stop >> "$state/network.log" 2>&1 || :; fi
sync
root_ro=1
mount -o remount,ro / > "$state/remount.log" 2>&1 || root_ro=0
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || root_ro=0
[ "$root_ro" = 1 ] || { status=1; last_step=root-remount; last_rc=1; }
{
    echo MUOS-R35S-NETWORK-P4-C07
    uname -r
    echo "STATUS=$status ROOT_RO=$root_ro"
    echo "BOOT_SEQ=$sequence FAILED_STEP=$last_step FAILED_RC=$last_rc"
    for name in steps.txt usb-mode.log network.log udev.log interface address association fingerprint remount.log; do
        echo "FILE=$name"; cat "$state/$name" 2>/dev/null
    done
    echo 'TAINT'; cat /proc/sys/kernel/tainted
    echo 'MODULES'; cat /proc/modules
    echo 'MOUNTS'; cat /proc/mounts
    echo 'RNG LOGS'; cat "$state/entropy-start.log" "$state/entropy-stop.log"
    for name in mode before.txt after.txt start.log stop-ready.txt stop.log; do
        echo "RNG_FILE=$name"; cat "/run/muos/entropy/$name" 2>/dev/null
    done
} > "$state/report.txt"
# Never collect private network config, key material, daemon logs, or /run wholesale.
. /usr/libexec/muos-diag-card-guard
boot=$(diag_card /sys) || { screen 'muOS C07: STOPPED - media guard'; park; }
mount -t vfat -o ro,nosuid,nodev,noexec "$boot" /boot || { screen 'muOS C07: STOPPED - FAT mount'; park; }
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ] || { umount /boot; screen 'muOS C07: STOPPED - media marker'; park; }
mount -o remount,rw,nosuid,nodev,noexec /boot || { umount /boot; screen 'muOS C07: STOPPED - FAT remount'; park; }
mkdir -p /boot/DIAG09
mkdir "/boot/DIAG09/$archive" || { umount /boot; screen 'C07 STOPPED: log archive exists'; park; }
for destination in "/boot/DIAG09/$archive" /boot/DIAG09; do
    cp "$state/report.txt" "$destination/REPORT.TXT" || status=1
    printf 'C07_DIAGNOSTIC_STATUS=%s\n' "$status" > "$destination/RESULT.TXT" || status=1
done
sync
umount /boot || { screen 'muOS C07: STOPPED - FAT unmount'; park; }
if [ "$status" != 0 ]; then
    /usr/libexec/muos-c07-network stop >/dev/null 2>&1 || :
    # Keep the failed boot immutable. A single physical replug can restore SSH
    # without cycling SD cards; record its outcome separately from boot success.
    case "$last_step:$root_ro" in
      network:1|usb-mode:1)
        /usr/libexec/muos-c07-recover > "$state/recovery.txt" 2>&1
        recovery_rc=$?
        printf 'RECOVERY_RC=%s\n' "$recovery_rc" >> "$state/recovery.txt"
        if [ "$recovery_rc" != 0 ]; then /usr/libexec/muos-c07-network stop >> "$state/recovery.txt" 2>&1 || :; fi
        recovery_saved=0
        if mount -t vfat -o ro,nosuid,nodev,noexec "$boot" /boot; then
            if [ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ] &&
               [ -d "/boot/DIAG09/$archive" ] && mount -o remount,rw,nosuid,nodev,noexec /boot; then
                cp "$state/recovery.txt" "/boot/DIAG09/$archive/RECOVER.TXT" && recovery_saved=1
            fi
            sync
            umount /boot || { screen 'C07: recovery FAT unmount failed'; park; }
        fi
        if [ "$recovery_rc:$recovery_saved" = 0:1 ]; then
            screen "muOS - R35S / Panel 0
C07: WIFI / DHCP / SSH RECOVERED
IP: $(cat "$state/address")  Port: 2222  User: root
$(cat "$state/fingerprint")
Boot failed; physical USB reconnect recovered SSH.
Root read-only. Separate recovery report saved."
            exit 0
        fi ;;
    esac
    screen "muOS C07: STOPPED
$last_step rc=$last_rc / root_ro=$root_ro
DIAG09/$archive saved. Return to dArkOSen.
No need to transcribe detailed logs."
    park
fi
screen "muOS - R35S / Panel 0
C07: WIFI / DHCP / SSH READY
IP: $(cat "$state/address")  Port: 2222  User: root
Host fingerprint:
$(cat "$state/fingerprint")
Root read-only. DIAG09 saved, FAT unmounted.
No frontend/audio. Keep powered on for SSH test."
exit 0
