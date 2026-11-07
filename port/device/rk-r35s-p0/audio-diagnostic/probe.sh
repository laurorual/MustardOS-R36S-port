#!/bin/sh
# SPDX-License-Identifier: MIT
# C05 playback probe only. Boot integration/cleanup belongs to the future runner.
set -u
export PATH=/opt/muos/frontend:/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/root XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
[ "$(id -u)" = 0 ] || exit 64
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ] || exit 64
[ "$(cat /etc/muos-audio-diagnostic 2>/dev/null)" = MUOS-R35S-AUDIO-P4-C05 ] || exit 64
[ -f /run/muos/core/audio ] && [ -f /run/muos/core/ready ] || exit 64
[ ! -e /run/muos/ui/manager ] || exit 64
! pidof muxfrontend muhotkey >/dev/null || exit 64
[ -r /usr/share/muos-diagnostic/c05-tone.wav ] || exit 64
state=/run/muos/c05-audio
mkdir -p "$state" || exit 1
bounded=/usr/libexec/muos-run-bounded
pcm=/proc/asound/card0/pcm0p/sub0/hw_params
tone=/usr/share/muos-diagnostic/c05-tone.wav
saved_volume=
saved_codec=
saved_path=
probe_codec_gain=95
probe_playback_path=SPK
audio_hardware_debug=0
debug_bound=0
debug_root=/sys/kernel/debug
sampler=
. /usr/libexec/muos-audio-functions
cleanup() {
    rc=$?
    trap - EXIT
    # A normal bounded playback always waits for its read-only sampler.
    if [ -n "$sampler" ]; then wait "$sampler" || rc=1; fi
    audio_restore_all || rc=1
    if [ "$debug_bound" = 1 ]; then
        if umount "$debug_root"; then echo C05_DEBUGFS_RELEASED=1; else rc=1; fi
    fi
    exit "$rc"
}
trap cleanup EXIT
/etc/init.d/S95muos-core status || exit 1
if [ "$audio_hardware_debug" = 1 ]; then
    if ! mountpoint -q "$debug_root"; then
        mount -t debugfs -o nosuid,nodev,noexec debugfs "$debug_root" || exit 1
        debug_bound=1
    fi
fi
audio_play
