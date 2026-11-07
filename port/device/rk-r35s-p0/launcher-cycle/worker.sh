#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
export PATH=/opt/muos/frontend:/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/root XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
export LC_ALL=C.UTF-8 SDL_JOYSTICK_HIDAPI=0 SDL_VIDEODRIVER=KMSDRM
export SDL_VIDEO_EGL_DRIVER=libEGL.so SDL_VIDEO_GL_DRIVER=libGLESv2.so SDL_AUDIODRIVER=pipewire
export LD_BIND_NOW=1 LD_LIBRARY_PATH=/opt/muos/frontend/lib
umask 077
dir=${1:-}; mode=${2:-}
case "$dir" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
case "$mode" in prepare-failure|signal-test|cycle|core-failure|observe) ;; *) exit 64 ;; esac
[ "$#" = 2 ] && [ -d "$dir" ] && [ ! -L "$dir" ]
[ "$(stat -c '%u:%g:%a' "$dir")" = 0:0:700 ]
[ "$(readlink /proc/self/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ]
package=/usr/libexec/muos-session;profile_dir=/usr/share/muos-r35s-profile
state=$dir/state;service_dir=/etc/init.d;bounded=$package/bin/muos-run-bounded
. "$package/card-guard.sh"; . "$package/data-functions.sh"
. "$package/runtime.sh"; . "$package/preferences.sh"; . "$package/chain.sh"
session_exec() { "$bounded" 10 "$@"; }
runtime_owned=0;preferences_owned=0;runner_pid=;runner_start=;reason=startup-failed
runner_identity() {
    [ -n "$runner_pid" ] && [ -r /proc/"$runner_pid"/stat ] || return 1
    [ "$(awk '{print $22}' /proc/"$runner_pid"/stat)" = "$runner_start" ]
}
retro_logger_stop() {
    # Our subreaper may already have stopped a detached logger it adopted.
    if ! pidof mulog >/dev/null && [ -f /run/muos/arborist.pid ]; then
        read old_logger ignored < /run/muos/arborist.pid
        case "$old_logger" in ''|*[!0-9]*) return 1 ;; esac
        [ ! -e /proc/"$old_logger" ] || return 1
        [ ! -L /run/muos/arborist.pid ] || return 1
        rm /run/muos/arborist.pid
        [ ! -S /run/muos/arborist.sock ] || rm /run/muos/arborist.sock
    fi
    session_stop_logger
}
finish() {
    operation=$?; trap - EXIT HUP INT TERM; cleanup=0
    if runner_identity; then kill -TERM "$runner_pid" 2>/dev/null || :; fi
    if [ -n "$runner_pid" ]; then wait "$runner_pid" 2>/dev/null || :; fi
    if [ "$runtime_owned" = 1 ]; then
        session_stop_chain > "$state/stop.log" 2>&1 || cleanup=1
        if ! pidof dbus-daemon >/dev/null && [ -S /run/dbus/system_bus_socket ]; then rm /run/dbus/system_bus_socket || cleanup=1; fi
        retro_logger_stop >> "$state/stop.log" 2>&1 || cleanup=1
        if [ "$preferences_owned" = 1 ]; then
            (cd "$prefs_mount/MUOS/preferences" && find . -type f -exec sha256sum '{}' ';' | sort) > "$state/preferences-after.sha256" || cleanup=1
            cmp "$state/preferences-before.sha256" "$state/preferences-after.sha256" || cleanup=1
        fi
        session_restore > "$state/restore.log" 2>&1 || cleanup=1
        retro_logger_stop >> "$state/stop.log" 2>&1 || cleanup=1
    fi
    for process in muxretro muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog; do
        if pidof "$process" >/dev/null; then cleanup=1; fi
    done
    findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro || cleanup=1
    [ "$(cat /proc/sys/kernel/tainted)" = 0 ] || cleanup=1
    printf 'OPERATION=%s\nCLEANUP=%s\nREASON=%s\n' "$operation" "$cleanup" "$reason" > "$state/result.txt"
    touch "$state/done"
    [ "$cleanup" = 0 ] || exit 125
    exit "$operation"
}
trap finish EXIT
trap 'reason=signal; exit 143' HUP INT TERM
[ "$(stat -c '%u:%g:%a' "$state")" = 0:0:700 ]
prefs_data_source
sha256sum -c "$package/prerequisites.sha256" > "$state/prerequisites.txt"
(cd "$package" && sha256sum -c payload.sha256) > "$state/payload.txt"
exec 8>/run/muos/session/lifetime.lock;flock -n 8
printf '%s %s\n' "$$" "$(awk '{print $22}' /proc/$$/stat)" > "$state/manager"
runtime_owned=1
# Preserve the global runtime/action/first-paint files: services and UI see a
# fresh private runtime, while the lifetime lock stays held in the parent view.
: > "$state/mounts"
mkdir -m 700 "$dir/run-muos"
session_bind "$dir/run-muos" /run/muos
mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /tmp
printf '/tmp\n' >> "$state/mounts"
session_prepare > "$state/prepare.log" 2>&1
prefs_mount=$dir/data
mkdir -m 700 "$prefs_mount" "$dir/ramdata"
mount -t ext4 -o ro,noload,nosuid,nodev,noexec "$prefs_device" "$prefs_mount"
printf '%s\n' "$prefs_mount" >> "$state/mounts"
prefs_data_mounted ro
(cd "$prefs_mount/MUOS/preferences" && find . -type f -exec sha256sum '{}' ';' | sort) > "$state/preferences-before.sha256"
preferences_owned=1
mkdir -m 700 "$dir/ramdata/MUOS"
cp -a "$prefs_mount/MUOS/preferences" "$dir/ramdata/MUOS/preferences"
"$package/bin/muos-preferences" --dir "$dir/ramdata/MUOS/preferences" load > "$state/preferences-loaded.txt"
session_preferences_pair "$state/preferences-loaded.txt"
printf 'MUOS-PREFS-1\nVOLUME=55\nBRIGHTNESS=70\n' | cmp -s - "$state/preferences-loaded.txt"
printf '%s\n' "$prefs_volume" > "$state/config/settings/general/volume"
printf '%s\n' "$prefs_brightness" > "$state/config/settings/general/brightness"
printf '0\n' > "$state/config/settings/advanced/volume"
for slot in "$state/volume"/*; do [ ! -e "$slot" ] || printf '%s\n' "$prefs_volume" > "$slot"; done
session_bind "$dir/ramdata" /userdata
printf 'fstype=tmpfs\n' > "$dir/storage.conf";session_bind "$dir/storage.conf" /etc/default/muos-storage
: > "$state/writer-original.sha256"
for path in /etc/asound.conf /usr/share/alsa/alsa.conf; do
    sha256sum "$path" >> "$state/writer-original.sha256"
    copy=$state/files/$(printf '%s' "$path" | tr / _);cp -p "$path" "$copy";session_bind "$copy" "$path"
done
(cd /usr/share/wireplumber && find . -type f -exec sha256sum '{}' ';' | sort) > "$state/wireplumber-before.sha256"
cp -a /usr/share/wireplumber "$state/wireplumber";session_bind "$state/wireplumber" /usr/share/wireplumber
mkdir -m 700 "$state/home" "$state/log";session_bind "$state/home" /root;session_bind "$state/log" /opt/muos/log
for path in /sys/devices/system/cpu /sys/power; do
    session_bind "$path" "$path";mount -o remount,bind,ro "$path"
    findmnt -rn -M "$path" -o OPTIONS | tr ',' '\n' | grep -qx ro
done
: > "$state/attempted"
for service in S30dbus-daemon S90muos-storage S95muos-core S96muos-input-ready; do
    echo "$service" >> "$state/attempted"
    session_exec "$service_dir/$service" start >> "$state/start.log" 2>&1
    [ "$service" = S30dbus-daemon ] || session_exec "$service_dir/$service" status >> "$state/start.log" 2>&1
    if [ "$mode" = prepare-failure ]; then reason=injected-prepare-failure;exit 42;fi
done
session_preferences_running >> "$state/start.log" 2>&1
if [ "$mode" = signal-test ]; then
    "$dir/runner" 60 "$dir/owner" /bin/sleep 30 > "$state/core.log" 2>&1 &
else
    "$dir/runner" 150 "$dir/owner" /bin/sh "$dir/cycle.sh" "$dir" "$mode" > "$state/core.log" 2>&1 &
fi
runner_pid=$!;runner_start=$(awk '{print $22}' /proc/"$runner_pid"/stat)
if [ "$mode" = signal-test ]; then sleep 1;kill -TERM "$$";fi
rc=0;wait "$runner_pid" || rc=$?
runner_pid=
if [ "$mode" = core-failure ];then [ "$rc" = 42 ];else [ "$rc" = 0 ];fi
grep -q '^C45_CYCLE_COMPLETE core_status=' "$state/core.log"
reason=cycle-complete
exit "$rc"
