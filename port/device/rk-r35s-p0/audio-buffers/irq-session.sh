#!/bin/sh
# SPDX-License-Identifier: MIT
# Temporary C30 experiment. The installed C22 worker inherits only this
# private bind; its profile, preferences and cleanup stay unchanged.
set -eu
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
dir=${1:-}
case "$dir" in /run/muos-c26.??????) ;; *) exit 64 ;; esac
[ "$#" = 1 ] && [ "$(id -u)" = 0 ]
[ "$(readlink /proc/self/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ]
[ -d "$dir" ] && [ ! -L "$dir" ] && [ "$(stat -c '%u:%g:%a' "$dir")" = 0:0:700 ]
for name in wireplumber.conf original-wp.sha256 session.conf; do
    [ -f "$dir/$name" ] && [ ! -L "$dir/$name" ]
    [ "$(stat -c '%u:%g:%a:%h' "$dir/$name")" = 0:0:600:1 ]
done
target=/opt/muos/device/control/wireplumber.conf
[ -f "$target" ] && [ ! -L "$target" ]
if findmnt -rn -M "$target" >/dev/null; then exit 64; fi
sha256sum -c "$dir/original-wp.sha256" >/dev/null
grep -qx '      api.alsa.disable-tsched = true' "$dir/wireplumber.conf"
foundation=/usr/libexec/muos-session/prerequisites.sha256
foundation_mounted=0
if [ -e "$dir/trial-foundation.sha256" ]; then
    for name in trial-foundation.sha256 original-foundation.sha256; do
        [ -f "$dir/$name" ] && [ ! -L "$dir/$name" ]
        [ "$(stat -c '%u:%g:%a:%h' "$dir/$name")" = 0:0:600:1 ]
    done
    if findmnt -rn -M "$foundation" >/dev/null; then exit 64; fi
    sha256sum -c "$dir/original-foundation.sha256" >/dev/null
fi
mount --bind "$dir/wireplumber.conf" "$target"
cleanup() {
    result=$?
    trap - EXIT
    if [ "$foundation_mounted" = 1 ]; then umount "$foundation" || result=1; fi
    umount "$target" || result=1
    exit "$result"
}
trap cleanup EXIT
trap 'exit 143' HUP INT TERM
cmp "$dir/wireplumber.conf" "$target"
if [ -e "$dir/trial-foundation.sha256" ]; then
    mount --bind "$dir/trial-foundation.sha256" "$foundation"
    foundation_mounted=1
fi
MUOS_SESSION_CONFIG="$dir/session.conf" /usr/libexec/muos-session/service.sh start
