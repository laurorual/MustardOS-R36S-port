#!/bin/sh
# SPDX-License-Identifier: MIT
# C32: bounded daemon-local rate renegotiation, no tones or saved settings.
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
export XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
generation=${1:-}
case "$generation" in run-[0-9][0-9][0-9][0-9]) ;; *) exit 64 ;; esac
package=/usr/libexec/muos-session; base=/run/muos/session
. "$package/control-functions.sh"
session_current;[ "${cycle##*/}" = "$generation" ];session_identity "$cycle"
[ -f "$cycle/ready" ];[ ! -e "$cycle/done" ]
pw_pid=$(pidof pipewire)
case "$pw_pid" in ''|*[!0-9]*) exit 64 ;; esac
[ "$pw_pid" -gt 1 ]
pw_start=$(awk '{print $22}' /proc/"$pw_pid"/stat)
bounded=$package/bin/muos-run-bounded
owns_audio() {
    [ -r /proc/"$pw_pid"/stat ] &&
    [ "$(awk '{print $22}' /proc/"$pw_pid"/stat)" = "$pw_start" ] &&
    [ "$(readlink /proc/"$pw_pid"/exe)" = /usr/bin/pipewire ]
}
metadata() { "$bounded" 3 pw-metadata -n settings 0 "$@"; }
metadata clock.force-rate | grep -F "key:'clock.force-rate' value:'0'"
metadata clock.force-quantum | grep -F "key:'clock.force-quantum' value:'1024'"
restore() {
    result=$?
    trap - EXIT HUP INT TERM
    if owns_audio; then
        metadata clock.force-rate 0 || result=1
        metadata clock.force-rate | grep -F "key:'clock.force-rate' value:'0'" || result=1
    else result=1; fi
    exit "$result"
}
trap restore EXIT
trap 'exit 143' HUP INT TERM
point() {
    owns_audio;session_identity "$cycle"
    [ -f "$cycle/ready" ];[ ! -e "$cycle/done" ]
    echo "$1";cat /proc/uptime
    cat /proc/asound/card0/pcm0p/sub0/hw_params
    cat /proc/asound/card0/pcm0p/sub0/status
}
point BEFORE_FIRST;sleep 2;point BEFORE_SECOND
owns_audio;metadata clock.force-rate 48000
sleep 2
point RATE48000_FIRST;sleep 2;point RATE48000_SECOND
owns_audio;metadata clock.force-rate 0
sleep 2
point RESTORED_FIRST;sleep 2;point RESTORED_SECOND
metadata clock.force-rate
echo C32_RATE_CYCLE_COMPLETE_NO_SAVED_SETTING_CHANGED
