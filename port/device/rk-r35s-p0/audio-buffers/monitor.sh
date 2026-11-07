#!/bin/sh
# SPDX-License-Identifier: MIT
# Capture only the named playback sink monitor; never select a microphone.
set -eu
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
export XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
umask 077
case "${1:-}" in /run/muos-c26.??????) directory=$1 ;; *) exit 64 ;; esac
case "${2:-}" in run-[0-9][0-9][0-9][0-9]) generation=$2 ;; *) exit 64 ;; esac
[ ! -L "$directory" ] && [ "$(stat -c '%u:%g:%a' "$directory")" = 0:0:700 ] || exit 64
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_media; c25_root_mode ro
package=/usr/libexec/muos-session; base=/run/muos/session
. "$package/control-functions.sh"
session_current && [ "$generation" = "$2" ] && session_identity "$cycle" || exit 64
cmp "$directory/session.conf" "$cycle/run.conf"
[ -f "$cycle/ready" ] && [ ! -e "$cycle/done" ] || exit 64
[ ! -e "$directory/monitor.f32" ] && [ ! -L "$directory/monitor.f32" ] || exit 64
mkdir "$directory/monitor.once"
trap 'rc=$?; trap - EXIT; printf "%s\n" "$rc" > "$directory/monitor.result"; touch "$directory/monitor.done"; exit "$rc"' EXIT
export PIPEWIRE_PROPS='{ target.object = "alsa_output.platform-rk817-sound.playback.0.0" stream.capture.sink = true node.dont-fallback = true node.name = "muos-c26-monitor" }'
"$package/bin/muos-run-bounded" 65 arecord -D pipewire -t raw -f FLOAT_LE -c 2 -r 44100 -d 60 "$directory/monitor.f32"
