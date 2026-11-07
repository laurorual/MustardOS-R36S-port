#!/bin/sh
# SPDX-License-Identifier: MIT
# One owned speaker step. Only PipeWire volume changes; typed prefs stay55/70.
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
export XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
umask 077
case "${1:-}" in /run/muos-volcal.??????) parent=$1 ;; *) exit 64 ;; esac
case "${2:-}" in run-[0-9][0-9][0-9][0-9]) expected=$2 ;; *) exit 64 ;; esac
case "${3:-}" in 0|55|65|75|85|100) level=$3 ;; *) exit 64 ;; esac
case "${4:-195}" in 195|205|215|225) codec=${4:-195} ;; *) exit 64 ;; esac
case "${5:-195}" in 195|205|215|225) restore_codec=${5:-195} ;; *) exit 64 ;; esac
if [ "$codec" != "$restore_codec" ]; then [ "$level" = 100 ] && [ "$codec" -gt "$restore_codec" ] || exit 64; fi
[ ! -L "$parent" ] && [ "$(stat -c '%u:%g:%a' "$parent")" = 0:0:700 ] || exit 64
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_media && c25_root_mode ro || exit 64
exec 7>"$parent/step.lock"
flock -n 7 || exit 64
package=/usr/libexec/muos-session; base=/run/muos/session
. "$package/control-functions.sh"
owned_session() {
    session_current && [ "$generation" = "$expected" ] && session_identity "$cycle" && [ -f "$cycle/ready" ]
}
owned_session || exit 64
grep -qx lease_seconds=600 "$cycle/run.conf" || exit 64
read now ignored < /proc/uptime
[ "$(cat "$parent/deadline")" -gt "$((${now%%.*}+210))" ] || exit 64
[ ! -e /run/muos/headphones ] || exit 64
pw_pid=$(pidof pipewire)
case "$pw_pid" in ''|*[!0-9]*) exit 64 ;; esac
pw_start=$(awk '{print $22}' /proc/$pw_pid/stat)
sink=$(wpctl inspect @DEFAULT_AUDIO_SINK@) || exit 64
printf '%s\n' "$sink" | grep -Fq 'node.name = "alsa_output.platform-rk817-sound.playback.0.0"' || exit 64
sink_id=$(printf '%s\n' "$sink" | sed -n 's/^id \([0-9]*\),.*/\1/p')
case "$sink_id" in ''|*[!0-9]*) exit 64 ;; esac
sink_serial=$(printf '%s\n' "$sink" | sed -n 's/.*object.serial = "\([0-9]*\)".*/\1/p')
[ -n "$sink_serial" ] || exit 64
[ "$(wpctl get-volume "$sink_id")" = 'Volume: 0.55' ] || exit 64
[ "$(amixer -c 0 cget name='Playback Volume' | sed -n 's/.*: values=//p')" = "$restore_codec,$restore_codec" ] || exit 64
state=$parent/level-$level
mkdir -m 700 "$state" || exit 64
printf '%s %s\n' "$$" "$(awk '{print $22}' /proc/$$/stat)" > "$state/manager"
changed=0; codec_changed=0; result=1; reason=step-failed
same_sink() {
    owned_session && [ "$(awk '{print $22}' /proc/$pw_pid/stat 2>/dev/null)" = "$pw_start" ] || return 1
    wpctl inspect "$sink_id" | grep -Fq "object.serial = \"$sink_serial\""
}
finish() {
    trap - EXIT HUP INT TERM
    if [ "$changed" = 1 ]; then
        if same_sink; then
            wpctl set-volume "$sink_id" 0.55 && [ "$(wpctl get-volume "$sink_id")" = 'Volume: 0.55' ] || result=1
            if [ "$codec_changed" = 1 ]; then
                amixer -c 0 cset name='Playback Volume' "$restore_codec,$restore_codec" > "$state/codec-restored.txt" &&
                    [ "$(amixer -c 0 cget name='Playback Volume' | sed -n 's/.*: values=//p')" = "$restore_codec,$restore_codec" ] || result=1
            fi
        else result=1; fi
    fi
    rm -f "$state/ready"
    printf 'RESULT=%s\nREASON=%s\nLEVEL=%s\nCODEC=%s\n' "$result" "$reason" "$level" "$codec" > "$state/report.txt"
    printf '%s\n' "$result" > "$state/result"; touch "$state/done"
    exit "$result"
}
trap finish EXIT
trap 'result=0; reason=operator-finished; exit 0' HUP INT TERM
changed=1
if [ "$codec" != "$restore_codec" ]; then
    codec_changed=1
    amixer -c 0 cset name='Playback Volume' "$codec,$codec" > "$state/codec-active.txt" || exit 1
fi
target=$(awk "BEGIN {printf \"%.2f\",$level/100}")
wpctl set-volume "$sink_id" "$target" || exit 1
wpctl get-volume "$sink_id" > "$state/volume.txt" || exit 1
[ "$(awk '{print $2}' "$state/volume.txt")" = "$target" ] || exit 1
read now ignored < /proc/uptime
end=$((${now%%.*}+180)); printf 'START=%s\nEND=%s\n' "${now%%.*}" "$end" > "$state/window.txt"
touch "$state/ready"
while :; do
    same_sink || exit 1
    read now ignored < /proc/uptime
    current=$(wpctl get-volume "$sink_id") || exit 1
    printf '%s %s\n' "${now%%.*}" "$current" >> "$state/readback.log"
    [ "$current" = "Volume: $target" ] || { reason=volume-changed; exit 1; }
    [ "$(amixer -c 0 cget name='Playback Volume' | sed -n 's/.*: values=//p')" = "$codec,$codec" ] || { reason=codec-changed; exit 1; }
    [ "${now%%.*}" -lt "$end" ] || break
    sleep 1
done
result=0; reason=deadline-restored
exit 0
