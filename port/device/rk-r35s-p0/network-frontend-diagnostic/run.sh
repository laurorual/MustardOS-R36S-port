#!/bin/sh
# SPDX-License-Identifier: MIT
# Transient C08: reuse C06 exactly, share C07 infrastructure, restore on exit.
export PATH=/opt/muos/frontend:/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/root XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 64
state=$package/state
c08_service_dir=/etc/init.d
c08_result=1
c08_root_rw=0
c08_watchdog=
c08_udev_pid=
c08_bus_attempted=0
[ "$(id -u)" = 0 ] && [ "$(readlink /proc/1/exe)" = /bin/busybox ] || exit 64
[ "$(readlink /proc/self/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ] || exit 64
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ] || exit 64
[ "$(tr -d '\000' < /sys/firmware/devicetree/base/model)" = 'R36S-V12 2023-08-18 Panel 0' ] || exit 64
[ "$(cat /etc/muos-network-diagnostic)" = MUOS-R35S-NETWORK-P4-C07 ] || exit 64
. /usr/libexec/muos-diag-card-guard
c08_boot=$(diag_card /sys) || exit 64
# Check the actual root against the selected card, without relying on /dev/root.
c08_root=${c08_boot%p1}p2
[ "$(findmnt -rn -o MAJ:MIN /)" = "$(cat /sys/class/block/${c08_root##*/}/dev)" ] || exit 64
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || exit 64
grep -qx enabled=0 /etc/default/muos-ui && grep -qx audio=0 /etc/default/muos-core || exit 64
/usr/libexec/muos-c07-network status || exit 64
pidof udevd >/dev/null || exit 64
for c08_name in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog; do
    ! pidof "$c08_name" >/dev/null || exit 64
done
[ ! -S /run/dbus/system_bus_socket ] && [ ! -e /run/muos/core/ready ] || exit 64
mkdir -p -m 700 "$state" || exit 64
exec 9>/run/muos/c08.lock
flock -n 9 || exit 64
sha256sum -c "$package/prerequisites.sha256" > "$state/prerequisites.txt" 2>&1 || exit 64
/usr/libexec/muos-run-bounded 3 /usr/libexec/muos-rng-ready 0 > "$state/rng-before.txt" || exit 64
. /usr/libexec/muos-c06-session
. "$package/chain.sh"
[ "$c06_control_effects:$c06_nav_adjusted" = 0:1 ] || exit 64
c08_exec() { /usr/libexec/muos-run-bounded 45 "$@"; }
screen() { printf '\033[37;40m\033[2J\033[H%s\n' "$1" > /dev/tty0; }
c08_network_identity() {
    /usr/libexec/muos-c07-network status || return 1
    for c08_name in dropbear wpa dhcp; do
        c08_pid=$(cat "/run/muos/c07/$c08_name.pid") || return 1
        printf '%s %s ' "$c08_name" "$c08_pid"
        awk '{print $22}' "/proc/$c08_pid/stat" || return 1
    done
    if [ -z "$c08_udev_pid" ]; then
        c08_udev_pid=$(c08_main_udev /proc $(pidof udevd)) || return 1
    fi
    [ "$(readlink "/proc/$c08_udev_pid/exe")" = /sbin/udevd ] || return 1
    [ "$(awk '/^PPid:/ {print $2}' "/proc/$c08_udev_pid/status")" = 1 ] || return 1
    printf 'udev %s ' "$c08_udev_pid"; awk '{print $22}' "/proc/$c08_udev_pid/stat" || return 1
}
c08_stop_logger() {
    if [ -r /run/muos/arborist.pid ]; then
        read c08_pid c08_ignored < /run/muos/arborist.pid || return 1
        case "$c08_pid" in ''|*[!0-9]*) return 1 ;; esac
        [ "$c08_pid" -gt 1 ] && [ "$(readlink "/proc/$c08_pid/exe")" = /opt/muos/frontend/mulog ] || return 1
        sleep 1
        kill -TERM "$c08_pid" || return 1
    fi
    c08_count=0
    while pidof mulog >/dev/null && [ "$c08_count" -lt 40 ]; do sleep 0.1; c08_count=$((c08_count+1)); done
    ! pidof mulog >/dev/null && [ ! -e /run/muos/arborist.pid ] && [ ! -S /run/muos/arborist.sock ]
}
c08_finish() {
    trap - EXIT HUP INT TERM
    if [ -n "$c08_watchdog" ]; then kill -TERM "$c08_watchdog" 2>/dev/null || :; wait "$c08_watchdog" 2>/dev/null || :; fi
    if [ "$c08_root_rw" = 1 ]; then
        c06_ui_stop >> "$state/cleanup.log" 2>&1 || c08_result=1
        c08_stop_chain >> "$state/cleanup.log" 2>&1 || c08_result=1
        c06_audio_cleanup >> "$state/cleanup.log" 2>&1 || c08_result=1
        c08_stop_logger >> "$state/cleanup.log" 2>&1 || c08_result=1
        # S30 stops its daemon but can leave its Unix socket pathname. It
        # belongs to C08 only because startup refused a pre-existing bus.
        if [ "$c08_bus_attempted" = 1 ] && ! pidof dbus-daemon >/dev/null; then
            if [ -S /run/dbus/system_bus_socket ] && [ ! -L /run/dbus/system_bus_socket ]; then
                rm /run/dbus/system_bus_socket || c08_result=1
            fi
            [ ! -e /run/dbus/system_bus_socket ] || c08_result=1
        fi
        /usr/libexec/muos-root-writers > "$state/root-writers.txt" 2>&1
        sync
        mount -o remount,ro / > "$state/remount.txt" 2>&1 || c08_result=1
    fi
    findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || c08_result=1
    c08_network_identity > "$state/network-after.txt" || c08_result=1
    cmp -s "$state/network-before.txt" "$state/network-after.txt" || c08_result=1
    for c08_name in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog; do
        ! pidof "$c08_name" >/dev/null || c08_result=1
    done
    [ "$(cat /proc/sys/kernel/tainted)" = 0 ] || c08_result=1
    {
        echo MUOS-R35S-NETWORK-FRONTEND-P4-C08
        echo "STATUS=$c08_result"
        echo 'ROOT'; findmnt -rn -o SOURCE,FSTYPE,OPTIONS /
        echo 'NAMESPACE'; readlink /proc/self/ns/mnt; readlink /proc/1/ns/mnt
        for c08_file in network-before.txt network-after.txt services.log frontend.log cleanup.log persistent-restore.txt cache-restored.txt audio-cleanup.txt drm-before.txt drm-after.txt remount.txt; do
            echo "FILE=$c08_file"; cat "$state/$c08_file" 2>/dev/null
        done
        echo 'TAINT'; cat /proc/sys/kernel/tainted
    } > "$state/report.txt"
    printf '%s\n' "$c08_result" > "$state/result"
    if [ "$c08_result" = 0 ]; then
        screen 'muOS - R35S / Panel 0
C08: FRONTEND / AUDIO / INPUT / SSH OK
Menu stopped. Root read-only. SSH remains active.
Report ready for automatic collection.'
    else
        screen 'muOS C08: STOPPED
Report ready for automatic SSH collection.
Keep the console powered on.'
    fi
    touch "$state/done"
    exit "$c08_result"
}
c08_network_identity > "$state/network-before.txt" || exit 64
printf '%s\n' "$$" > "$state/pid"
trap c08_finish EXIT
trap 'c08_result=1; exit 143' HUP INT TERM
c08_owner=$$
(
    exec 9>&-
    trap - EXIT HUP INT TERM
    c08_tick=0
    while [ "$c08_tick" -lt 300 ]; do
        /usr/libexec/muos-c07-network status || { echo network-failed > "$state/watchdog.txt"; kill -TERM "$c08_owner"; exit; }
        sleep 1; c08_tick=$((c08_tick+1))
    done
    echo deadline > "$state/watchdog.txt"
    kill -TERM "$c08_owner"
) &
c08_watchdog=$!
mount -o remount,rw / || exit 1
c08_root_rw=1
c08_start_chain > "$state/services.log" 2>&1 || exit 1
c06_frontend > "$state/frontend.log" 2>&1 || exit 1
c08_result=0
exit 0
