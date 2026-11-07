#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/opt/muos/frontend:/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/root XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
umask 077
package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 64
state=${1:-}
case "$state" in /run/muos/session/run-[0-9][0-9][0-9][0-9]) ;; *) exit 64 ;; esac
lease_seconds=180; profile_dir=/usr/share/muos-r35s-profile; prerequisites=; preferences_enabled=0
. "$state/run.conf"
. "$package/chain.sh"
. "$package/runtime.sh"
case "$preferences_enabled" in 0) ;; 1) . "$package/preferences.sh" ;; *) exit 64 ;; esac
service_dir=/etc/init.d
bounded=$package/bin/muos-run-bounded
session_exec() { "$bounded" 45 "$@"; }
result=1; reason=startup-failed; root_rw=0; startup_owned=0; runtime_owned=0
screen() { printf '\033[37;40m\033[2J\033[H%s\n' "$1" > /dev/tty0; }
finish() {
    trap - EXIT HUP INT TERM
    rm -f "$state/ready"
    if [ "$runtime_owned" = 1 ]; then
        # Bound the same effect grace used in the approved audio tests.
        [ "$startup_owned" = 0 ] || sleep 3
        if [ "$preferences_enabled" = 1 ] && [ "$startup_owned" = 1 ] && [ "$result" = 0 ]; then
            if session_exec "$service_dir/S99muos-ui" stop > "$state/checkpoint-stop.log" 2>&1; then
                session_preferences_checkpoint > "$state/checkpoint.log" 2>&1 || result=1
            else result=1; fi
        fi
        session_stop_chain > "$state/stop.log" 2>&1 || result=1
        if ! pidof dbus-daemon >/dev/null && [ -S /run/dbus/system_bus_socket ]; then rm /run/dbus/system_bus_socket || result=1; fi
        # Close logger descriptors before unmounting the real data volume.
        if [ "$preferences_enabled" = 1 ]; then session_stop_logger >> "$state/stop.log" 2>&1 || result=1; fi
        session_restore > "$state/restore.log" 2>&1 || result=1
        session_stop_logger >> "$state/stop.log" 2>&1 || result=1
        n=0
        while pidof muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon >/dev/null && [ "$n" -lt 50 ]; do sleep 0.1; n=$((n+1)); done
        for name in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog; do ! pidof "$name" >/dev/null || result=1; done
        "$package/bin/muos-root-writers" > "$state/root-writers.txt" 2>&1
        sync
        if [ "$root_rw" = 1 ]; then mount -o remount,ro / > "$state/remount.txt" 2>&1 || result=1; fi
    fi
    findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || result=1
    [ "$(cat /proc/sys/kernel/tainted)" = 0 ] || result=1
    {
        echo MUOS-R35S-SESSION-P4-C11
        echo "RESULT=$result REASON=$reason"
        echo ROOT; findmnt -rn -o SOURCE,FSTYPE,OPTIONS /
        echo NAMESPACE; readlink /proc/self/ns/mnt; readlink /proc/1/ns/mnt
        echo TAINT; cat /proc/sys/kernel/tainted
    } > "$state/report.txt"
    printf '%s\n' "$result" > "$state/result"
    screen "muOS - R35S / Panel 0
C11 session stopped: $reason / result=$result
Root read-only. SSH infrastructure preserved.
Keep powered on for automatic collection."
    touch "$state/done"
    exit "$result"
}
trap finish EXIT
trap 'reason=manual-stop; exit 0' HUP INT TERM
[ "$(id -u)" = 0 ] && [ "$(readlink /proc/1/exe)" = /bin/busybox ] || exit 64
[ "$(readlink /proc/self/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ] || exit 64
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ] || exit 64
[ "$(tr -d '\000' < /sys/firmware/devicetree/base/model)" = 'R36S-V12 2023-08-18 Panel 0' ] || exit 64
[ "$(cat /proc/sys/kernel/tainted)" = 0 ] || exit 64
. "$package/card-guard.sh"
boot=$(diag_card /sys) || exit 64
root=${boot%p1}p2
[ "$(findmnt -rn -o MAJ:MIN /)" = "$(cat /sys/class/block/${root##*/}/dev)" ] || exit 64
[ "$(findmnt -rn -o FSTYPE /)" = ext4 ] || exit 64
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || exit 64
[ ! -S /run/dbus/system_bus_socket ] && [ ! -e /run/muos/core/ready ] || exit 64
[ ! -e /run/muos/port-storage/ready ] && [ ! -e /run/muos/input-ready/ready ] || exit 64
! findmnt -rn -M /mnt/mmc >/dev/null || exit 64
for name in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog; do ! pidof "$name" >/dev/null || exit 64; done
[ "$(find /opt/muos/share/hotkey -name '*.json' | wc -l)" -eq 1 ] || exit 64
"$package/bin/muos-rng-ready" 0 > "$state/rng.txt" || exit 64
if [ -n "${prerequisites:-}" ]; then sha256sum -c "$prerequisites" > "$state/prerequisites.txt" 2>&1 || exit 64; fi
exec 8>/run/muos/session/lifetime.lock
flock -n 8 || exit 64
printf '%s %s\n' "$$" "$(awk '{print $22}' /proc/$$/stat)" > "$state/manager.tmp"
mv "$state/manager.tmp" "$state/manager"
if [ "$preferences_enabled" = 0 ]; then
    mount -o remount,rw / || exit 1
    root_rw=1
fi
runtime_owned=1
session_prepare > "$state/prepare.log" 2>&1 || exit 1
if [ "$preferences_enabled" = 1 ]; then session_preferences_prepare >> "$state/prepare.log" 2>&1 || exit 1; fi
session_start_chain > "$state/start.log" 2>&1 || exit 1
startup_owned=1
if [ "$preferences_enabled" = 1 ]; then session_preferences_running >> "$state/start.log" 2>&1 || exit 1; fi
[ -s /run/muos/first_paint ] || exit 1
cat /run/muos/first_paint > "$state/first-paint.txt"
cat /run/muos/ui/manager > "$state/ui-manager.txt"
read ui_manager ignored < /run/muos/ui/manager
ui_frontend=$(awk '/^CHILD frontend /{p=$3} END{print p}' /run/muos/ui/supervisor.log)
case "$ui_frontend" in ''|*[!0-9]*) exit 1 ;; esac
[ "$(readlink /proc/$ui_frontend/exe)" = /opt/muos/frontend/muxfrontend ] || exit 1
ui_parent=$(awk '/^PPid:/ {print $2}' /proc/$ui_frontend/status)
[ "$ui_parent" = "$ui_manager" ] || exit 1
printf 'UI_ID manager=%s frontend=%s parent=%s\n' "$ui_manager" "$ui_frontend" "$ui_parent" > "$state/ui-identity.txt"
tail -c 196608 /run/muos/ui/supervisor.log > "$state/ui-start.txt"
wpctl get-volume @DEFAULT_AUDIO_SINK@ > "$state/software-volume.txt" || exit 1
amixer -c 0 contents > "$state/mixer-active.txt" || exit 1
cat /sys/class/backlight/backlight/brightness > "$state/brightness-active.txt" || exit 1
read now ignored < /proc/uptime
deadline=$((${now%%.*}+lease_seconds))
result=0; reason=lease-expired
touch "$state/ready"
while :; do
    session_exec "$service_dir/S99muos-ui" status > "$state/status.log" 2>&1 || { result=1; reason=ui-lost; exit 1; }
    session_exec "$service_dir/S95muos-core" status >> "$state/status.log" 2>&1 || { result=1; reason=core-lost; exit 1; }
    read now ignored < /proc/uptime
    [ "${now%%.*}" -lt "$deadline" ] || break
    sleep 1
done
exit 0
