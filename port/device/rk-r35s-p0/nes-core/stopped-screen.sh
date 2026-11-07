#!/bin/sh
# SPDX-License-Identifier: MIT
# Post-collection console-only status page. Never starts/stops/reboots anything.
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
boot=${1:-}
case "$boot" in ''|*[!0-9]*) exit 64 ;; esac
[ "$#" = 1 ]
c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_ready
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = "$boot" ]
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
if pidof muxretro muxfrontend muxlaunch muinput muhotkey pipewire wireplumber dbus-daemon mulog >/dev/null;then exit 64;fi
printf '\033[37;40m\033[2J\033[H%s\n' 'muOS - R35S / Panel 0
C47 diagnostic finished
No game or menu is running.
Root read-only. SSH ready.
Keep powered on for collection.' > /dev/tty0
echo C47_STOPPED_SCREEN_WRITTEN_NO_UI_ROOT_RO
