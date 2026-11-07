# SPDX-License-Identifier: MIT
# Caller supplies state/bounded/pcm/tone. Gain is fixed to 95 or diagnostic157.
audio_snapshot() {
    label=$1
    {
        echo "SNAPSHOT=$label"
        echo PCM_BEGIN; cat "$pcm" || return 1
        for control in 'name=Playback Volume' 'name=Playback Path' 'iface=CARD,name=Headphone Jack'; do
            "$bounded" 3 amixer -c 0 cget "$control" || return 1
        done
        "$bounded" 3 wpctl get-volume @DEFAULT_AUDIO_SINK@ || return 1
        echo PCM_END; cat "$pcm" || return 1
        if [ "${audio_hardware_debug:-0}" = 1 ]; then
            echo CODEC_REGISTERS
            "$bounded" 3 cat "$debug_root/regmap/0-0020-rk817-codec/registers" || return 1
            echo I2S_REGISTERS
            "$bounded" 3 cat "$debug_root/regmap/ff070000.i2s/registers" || return 1
            "$bounded" 3 cat "$debug_root/clk/clk_summary" > "$state/$label-clocks.txt" || return 1
            echo I2S_CLOCKS; awk '/i2s1/' "$state/$label-clocks.txt"
        fi
    } > "$state/$label.txt" 2>&1
}
audio_restore_volume() {
    [ -n "$saved_volume" ] || return 0
    "$bounded" 3 wpctl set-volume @DEFAULT_AUDIO_SINK@ "$saved_volume" || return 1
    "$bounded" 3 wpctl get-volume @DEFAULT_AUDIO_SINK@ > "$state/software-restored.txt" || return 1
    [ "$(awk '{print $2}' "$state/software-restored.txt")" = "$saved_volume" ] || return 1
    saved_volume=
}
audio_restore_codec() {
    [ -n "${saved_codec:-}" ] || return 0
    "$bounded" 3 amixer -c 0 cset 'name=Playback Volume' "$saved_codec" > "$state/codec-restore-set.txt" || return 1
    "$bounded" 3 amixer -c 0 cget 'name=Playback Volume' > "$state/codec-restored.txt" || return 1
    grep -Eq '^[[:space:]]*: values=95,95$' "$state/codec-restored.txt" || return 1
    saved_codec=
}
audio_restore_path() {
    [ -n "${saved_path:-}" ] || return 0
    "$bounded" 3 amixer -c 0 cset 'name=Playback Path' "$saved_path" > "$state/path-restore-set.txt" || return 1
    "$bounded" 3 amixer -c 0 cget 'name=Playback Path' > "$state/path-restored.txt" || return 1
    grep -Eq '^[[:space:]]*: values=1$' "$state/path-restored.txt" || return 1
    saved_path=
}
audio_restore_all() {
    restore_result=0
    audio_restore_volume || restore_result=1
    # Route changes can rewrite DAC registers; restore the gain afterwards.
    audio_restore_path || restore_result=1
    audio_restore_codec || restore_result=1
    return "$restore_result"
}
audio_play() {
    case "${probe_codec_gain:-95}" in 95|157) ;; *) return 1 ;; esac
    case "${probe_playback_path:-SPK}" in SPK|SPK_HP) ;; *) return 1 ;; esac
    "$bounded" 5 wpctl inspect @DEFAULT_AUDIO_SINK@ > "$state/sink.txt" 2>&1 || return 1
    grep -q 'node.name = "alsa_output.platform-rk817-sound.playback.0.0"' "$state/sink.txt" || return 1
    audio_snapshot before || return 1
    "$bounded" 3 amixer -c 0 cget 'name=Playback Volume' > "$state/codec.txt" || return 1
    grep -Eq '^[[:space:]]*: values=95,95$' "$state/codec.txt" || return 1
    if [ "${probe_playback_path:-SPK}" = SPK_HP ]; then
        "$bounded" 3 amixer -c 0 cget 'name=Playback Path' > "$state/path-before.txt" || return 1
        grep -q "Item #3 'SPK_HP'" "$state/path-before.txt" || return 1
        grep -Eq '^[[:space:]]*: values=1$' "$state/path-before.txt" || return 1
        saved_path=SPK
        saved_codec=95,95
        "$bounded" 3 amixer -c 0 cset 'name=Playback Path' SPK_HP > "$state/path-probe-set.txt" || return 1
    fi
    if [ "${probe_codec_gain:-95}" = 157 ]; then
        saved_codec=95,95
        "$bounded" 3 amixer -c 0 cset 'name=Playback Volume' '157,157' > "$state/codec-probe-set.txt" || return 1
    fi
    "$bounded" 3 wpctl get-volume @DEFAULT_AUDIO_SINK@ > "$state/software-before.txt" || return 1
    ! grep -q MUTED "$state/software-before.txt" || return 1
    saved_volume=$(awk '/^Volume: [0-9]+\.[0-9]+$/ {print $2}' "$state/software-before.txt")
    case "$saved_volume" in ''|*[!0-9.]*) return 1 ;; esac
    "$bounded" 3 wpctl set-volume @DEFAULT_AUDIO_SINK@ 1.0 || return 1
    "$bounded" 3 wpctl get-volume @DEFAULT_AUDIO_SINK@ > "$state/software-unity.txt" || return 1
    grep -Eq '^Volume: 1\.0+$' "$state/software-unity.txt" || return 1
    (sleep 0.6; audio_snapshot during) & sampler=$!
    play_status=0
    "$bounded" 12 aplay -v -D pipewire "$tone" > "$state/aplay.txt" 2>&1 || play_status=$?
    sample_status=0
    wait "$sampler" || sample_status=$?
    sampler=
    audio_snapshot after || return 1
    audio_restore_all || return 1
    printf 'C05_PLAY_STATUS=%s\nC05_SAMPLE_STATUS=%s\n' "$play_status" "$sample_status" > "$state/result.txt"
    [ "$play_status" = 0 ] && [ "$sample_status" = 0 ] || return 1
    grep -Eq '^format: (S16_LE|S32_LE)$' "$state/during.txt" || return 1
    grep -Eq "^[[:space:]]*: values=${probe_codec_gain:-95},${probe_codec_gain:-95}$" "$state/during.txt" || return 1
    if [ "${probe_playback_path:-SPK}" = SPK_HP ]; then
        grep -Eq '^[[:space:]]*: values=3$' "$state/during.txt" || return 1
    fi
    echo "C05_CODEC_PROBE_GAIN=${probe_codec_gain:-95}" >> "$state/result.txt"
    echo "C05_PLAYBACK_PATH=${probe_playback_path:-SPK}" >> "$state/result.txt"
    echo C05_AUDIO_PROBE_OK=1 >> "$state/result.txt"
}
