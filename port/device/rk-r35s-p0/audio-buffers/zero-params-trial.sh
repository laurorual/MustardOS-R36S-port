#!/bin/sh
# SPDX-License-Identifier: MIT
# Called in a private namespace under the session lifetime lock. Zero PCM only.
set -eu
umask 077
dir=${1:-}
case "$dir" in /run/muos-zero.??????) ;; *) exit 64 ;; esac
[ "$#" = 1 ] && [ -d "$dir" ] && [ ! -L "$dir" ]
[ "$(stat -c '%u:%g:%a' "$dir")" = 0:0:700 ]
[ "$(readlink /proc/self/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ]
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
amixer -c 0 contents > "$dir/mixer-before.txt"
alsactl -f "$dir/mixer.state" store 0
player=; player_start=
cleanup() {
    result=$?
    trap - EXIT HUP INT TERM
    if [ -n "$player" ] && [ -r /proc/"$player"/stat ] &&
       [ "$(awk '{print $22}' /proc/"$player"/stat)" = "$player_start" ]; then
        kill -TERM "$player" 2>/dev/null || :
        wait "$player" 2>/dev/null || :
    fi
    alsactl -f "$dir/mixer.state" restore 0 || result=1
    amixer -c 0 contents > "$dir/mixer-after.txt" || result=1
    cmp "$dir/mixer-before.txt" "$dir/mixer-after.txt" || result=1
    [ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ] || result=1
    exit "$result"
}
trap cleanup EXIT
trap 'exit 143' HUP INT TERM
amixer -c 0 cset name='Playback Path' SPK_HP > /dev/null
amixer -c 0 cset name='Playback Volume' 215,215 > /dev/null
"$dir/alsa-zero-params" --info
/usr/libexec/muos-session/bin/muos-run-bounded 12 "$dir/alsa-zero-params" > "$dir/player.log" 2>&1 &
player=$!
player_start=$(awk '{print $22}' /proc/"$player"/stat)
sleep 1
echo FIRST
cat /proc/asound/card0/pcm0p/sub0/hw_params
cat /proc/asound/card0/pcm0p/sub0/sw_params
cat /proc/asound/card0/pcm0p/sub0/status
sleep 2
echo SECOND
cat /proc/asound/card0/pcm0p/sub0/status
echo END_PCM
wait "$player"
player=
cat "$dir/player.log"
