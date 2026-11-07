# SPDX-License-Identifier: MIT
# Hook before S95 in the selected diagnostic chain, after entropy readiness.
c05_before_core() {
    [ "$core_bound" = 0 ] || return 1
    /usr/libexec/muos-run-bounded 5 alsactl -U -f "$state/alsa-before.state" store || return 1
    /usr/libexec/muos-run-bounded 3 amixer -c 0 contents > "$state/alsa-before.txt" || return 1
    cp /opt/muos/device/control/asound.state "$state/asound.state" || return 1
    mount --bind "$state/asound.state" /opt/muos/device/control/asound.state || return 1
    asound_bound=1
    printf 'audio=1\ninput=1\n' > "$state/core.conf" || return 1
    mount --bind "$state/core.conf" /etc/default/muos-core || return 1
    core_bound=1
}
c05_play() {
    [ -f /run/muos/core/audio ] && pidof pipewire wireplumber >/dev/null || return 1
    screen 'muOS - R35S / Panel 0
C05: audio ready; three beeps in five seconds.
No buttons needed. Wait for diagnostic result.'
    sleep 5
    /usr/libexec/muos-audio-probe
}
c05_audio_cleanup() {
    cleanup_result=0
    # S95 may fail before publishing core/audio: still stop partial audio.
    if [ "$core_bound" = 1 ]; then
        /usr/libexec/muos-run-bounded 15 /opt/muos/script/init/S80pipewire.sh stop > "$state/audio-stop.txt" 2>&1 || cleanup_result=1
    fi
    for name in pipewire wireplumber aplay; do
        if pidof "$name" >/dev/null; then
            cleanup_result=1
            killall -TERM "$name" 2>/dev/null || :
            sleep 1
            killall -KILL "$name" 2>/dev/null || :
        fi
    done
    if [ "$core_bound" = 1 ]; then umount /etc/default/muos-core || cleanup_result=1; fi
    if [ "$asound_bound" = 1 ]; then umount /opt/muos/device/control/asound.state || cleanup_result=1; fi
    grep -qx audio=0 /etc/default/muos-core || cleanup_result=1
    if [ -f "$state/alsa-before.state" ]; then
        /usr/libexec/muos-run-bounded 5 alsactl -U -f "$state/alsa-before.state" restore || cleanup_result=1
        /usr/libexec/muos-run-bounded 3 amixer -c 0 contents > "$state/alsa-restored.txt" || cleanup_result=1
        cmp -s "$state/alsa-before.txt" "$state/alsa-restored.txt" || cleanup_result=1
    fi
    [ "$cleanup_result" = 0 ] || return 1
    echo C05_AUDIO_CLEANUP_OK=1 > "$state/audio-cleanup.txt"
}
