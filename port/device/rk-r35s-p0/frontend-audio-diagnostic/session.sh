# SPDX-License-Identifier: MIT
# C06: real S95/S80 + S99 UI, no hotkeys. All overrides live in /run.
core_bound=0
asound_bound=0
device_config_bound=0
global_config_bound=0
ui_config_bound=0
help_open_bound=0
help_close_bound=0
c06_sound_binds=
c06_control_effects=1
c06_nav_adjusted=0
frontend_pid=0
manager_pid=0
c06_theme=/opt/muos/share/theme/MustardOS/sound

c06_before_core() {
    case "$c06_control_effects:$c06_nav_adjusted" in 0:0|0:1|1:0) ;; *) return 1 ;; esac
    [ "$core_bound:$asound_bound:$device_config_bound:$global_config_bound" = 0:0:0:0 ] || return 1
    /usr/libexec/muos-run-bounded 5 alsactl -U -f "$state/alsa-before.state" store || return 1
    /usr/libexec/muos-run-bounded 3 amixer -c 0 contents > "$state/alsa-before.txt" || return 1
    sha256sum /opt/muos/device/control/asound.state /opt/muos/device/config/audio/path \
        /opt/muos/config/settings/general/volume /opt/muos/config/settings/general/sound \
        /opt/muos/config/settings/advanced/volume \
        /opt/muos/config/system/debug_mode /opt/muos/config/settings/power/idle_display \
        /opt/muos/config/settings/power/idle_sleep "$c06_theme/confirm.wav" \
        "$c06_theme/back.wav" "$c06_theme/navigate.wav" "$c06_theme/info_open.wav" \
        "$c06_theme/info_close.wav" > "$state/persistent-before.sha256" || return 1
    # Directory binds preserve native atomic rename semantics (muvarctl).
    cp -a /opt/muos/device/config "$state/device-config" || return 1
    cp -a /opt/muos/config "$state/config" || return 1
    printf 'SPK_HP\n' > "$state/device-config/audio/path" || return 1
    printf '100\n' > "$state/config/settings/general/volume" || return 1
    # Native boot policy2 forces35; policy3 uses the board software maximum
    # (100/unity here) and skips saved per-sink levels. Hardware stays157.
    printf '3\n' > "$state/config/settings/advanced/volume" || return 1
    printf '2\n' > "$state/config/settings/general/sound" || return 1
    printf '2\n' > "$state/config/system/debug_mode" || return 1
    printf '0\n' > "$state/config/settings/power/idle_display" || return 1
    printf '0\n' > "$state/config/settings/power/idle_sleep" || return 1
    mount --bind "$state/device-config" /opt/muos/device/config || return 1
    device_config_bound=1
    mount --bind "$state/config" /opt/muos/config || return 1
    global_config_bound=1
    cat > "$state/asound.state" <<'PROFILE'
state.rockchiprk817co {
  control.1 {
    iface MIXER
    name 'Playback Path'
    value SPK_HP
  }
  control.3 {
    iface MIXER
    name 'Playback Volume'
    value.0 157
    value.1 157
  }
}
PROFILE
    mount --bind "$state/asound.state" /opt/muos/device/control/asound.state || return 1
    asound_bound=1
    printf 'audio=1\ninput=1\n' > "$state/core.conf" || return 1
    mount --bind "$state/core.conf" /etc/default/muos-core || return 1
    core_bound=1
}

c06_help_start() {
    for effect in confirm back navigate info_open info_close; do
        sha256sum "$c06_theme/$effect.wav" || return 1
        case "$c06_control_effects:$effect" in
            0:confirm|0:back) continue ;;
            0:navigate)
                [ "$c06_nav_adjusted" = 1 ] || continue
                effect_source=/usr/share/muos-diagnostic/c06-navigate-normalized.wav ;;
            0:info_open|0:info_close) effect_source="$c06_theme/confirm.wav" ;;
            1:*) effect_source=/usr/share/muos-diagnostic/c06-control-tone.wav ;;
            *) return 1 ;;
        esac
        cp "$effect_source" "$state/$effect.wav" || return 1
        mount --bind "$state/$effect.wav" "$c06_theme/$effect.wav" || return 1
        c06_sound_binds="$effect $c06_sound_binds"
        cmp -s "$effect_source" "$c06_theme/$effect.wav" || return 1
    done
    echo C06_HELP_CONTROL_WAV=1
    if [ "$c06_control_effects" = 1 ]; then
        echo C06_EFFECTS_CONTROL_TONE=1
    elif [ "$c06_nav_adjusted" = 1 ]; then
        echo C06_NATIVE_CONFIRM_BACK=1
        echo C06_NAV_WAVE_ADJUSTED=1
    else
        echo C06_NATIVE_NAV_CONFIRM=1
    fi
}

c06_ui_stop() {
    ui_stop_result=0
    /usr/libexec/muos-run-bounded 15 /etc/init.d/S99muos-ui stop || ui_stop_result=1
    /usr/libexec/muos-ui-supervisor --status
    [ "$?" = 3 ] || ui_stop_result=1
    ! pidof muxfrontend muhotkey >/dev/null || ui_stop_result=1
    if [ "$ui_config_bound" = 1 ]; then
        if umount /etc/default/muos-ui; then ui_config_bound=0; else ui_stop_result=1; fi
    fi
    remaining_sound_binds=
    for effect in $c06_sound_binds; do
        if ! umount "$c06_theme/$effect.wav"; then
            remaining_sound_binds="$effect $remaining_sound_binds"; ui_stop_result=1
        fi
    done
    c06_sound_binds=$remaining_sound_binds
    grep -qx enabled=0 /etc/default/muos-ui || ui_stop_result=1
    return "$ui_stop_result"
}

c06_audio_check() {
    snapshot_name=$1
    audio_snapshot "$snapshot_name" || return 1
    grep -Eq '^format: (S16_LE|S32_LE)$' "$state/$snapshot_name.txt" || return 1
    grep -Eq '^rate: (44100|48000) ' "$state/$snapshot_name.txt" || return 1
    grep -qx 'channels: 2' "$state/$snapshot_name.txt" || return 1
    grep -Eq '^[[:space:]]*: values=157,157$' "$state/$snapshot_name.txt" || return 1
    grep -Eq '^[[:space:]]*: values=3$' "$state/$snapshot_name.txt" || return 1
    grep -Eq '^Volume: 1\.0+$' "$state/$snapshot_name.txt" || return 1
}

c06_reference_group() {
    reference_group=$1
    reference_wave=$2
    reference_rate=$3
    reference_repeats=$4
    case "$reference_group:$reference_rate:$reference_repeats" in reference-48:48000:1|reference-44:44100:3) ;; *) return 1 ;; esac
    reference_index=0
    : > "$state/$reference_group-aplay.txt"
    while [ "$reference_index" -lt "$reference_repeats" ]; do
        reference_delay=0.10
        [ "$reference_group" != reference-48 ] || reference_delay=0.6
        (sleep "$reference_delay"; audio_snapshot "$reference_group-during") &
        reference_sampler=$!
        reference_play_status=0
        "$bounded" 12 aplay -v -D pipewire "$reference_wave" >> "$state/$reference_group-aplay.txt" 2>&1 || reference_play_status=1
        reference_sample_status=0
        wait "$reference_sampler" || reference_sample_status=1
        [ "$reference_play_status:$reference_sample_status" = 0:0 ] || return 1
        grep -Eq "^rate: $reference_rate " "$state/$reference_group-during.txt" || return 1
        grep -Eq '^[[:space:]]*: values=157,157$' "$state/$reference_group-during.txt" || return 1
        grep -Eq '^[[:space:]]*: values=3$' "$state/$reference_group-during.txt" || return 1
        grep -Eq '^Volume: 1\.0+$' "$state/$reference_group-during.txt" || return 1
        reference_index=$((reference_index + 1))
        sleep 0.3
    done
    echo "C06_REFERENCE=$reference_group RATE=$reference_rate STATUS=0"
}

c06_frontend() {
    bounded=/usr/libexec/muos-run-bounded
    pcm=/proc/asound/card0/pcm0p/sub0/hw_params
    audio_hardware_debug=0
    . /usr/libexec/muos-audio-functions
    [ -f /run/muos/core/audio ] && [ -f /run/muos/core/ready ] || return 1
    pidof pipewire >/dev/null && pidof wireplumber >/dev/null || return 1
    ! pidof muhotkey >/dev/null || return 1
    echo "C06_CONFIG_PATH=$(/opt/muos/frontend/muvarctl get device audio/path)"
    echo "C06_CONFIG_VOLUME=$(/opt/muos/frontend/muvarctl get global settings/general/volume)"
    echo "C06_BOOT_VOLUME_POLICY=$(/opt/muos/frontend/muvarctl get global settings/advanced/volume)"
    "$bounded" 3 wpctl get-volume @DEFAULT_AUDIO_SINK@ || return 1
    [ "$(/opt/muos/frontend/muvarctl get device audio/path)" = SPK_HP ] || return 1
    [ "$(/opt/muos/frontend/muvarctl get global settings/general/volume)" = 100 ] || return 1
    [ "$(/opt/muos/frontend/muvarctl get global settings/general/sound)" = 2 ] || return 1
    [ "$(/opt/muos/frontend/muvarctl get global settings/advanced/volume)" = 3 ] || return 1
    screen 'muOS - R35S / Panel 0
C06 A: three baseline beeps at 48000 Hz.
Then wait for three more beeps with the menu.'
    sleep 3
    c06_reference_group reference-48 /usr/share/muos-diagnostic/c05-tone.wav 48000 1 || return 1
    c06_help_start || return 1
    "$bounded" 5 /usr/libexec/muos-drm-mode-probe > "$state/drm-before.txt" || return 1
    echo DRM_BEFORE; cat "$state/drm-before.txt"
    printf 'enabled=1\nhotkeys=0\n' > "$state/ui.conf" || return 1
    mount --bind "$state/ui.conf" /etc/default/muos-ui || return 1
    ui_config_bound=1
    ui_result=0
    "$bounded" 25 /etc/init.d/S99muos-ui start || ui_result=1
    if [ "$ui_result" = 0 ]; then
        read manager_pid ignored < /run/muos/ui/manager || ui_result=1
        frontend_pid=$(awk '/^CHILD frontend / {pid=$3} END {print pid}' /run/muos/ui/supervisor.log)
        case "$frontend_pid:$manager_pid" in *[!0-9:]*|:*|*:) ui_result=1 ;; esac
        [ "$(readlink "/proc/$frontend_pid/exe")" = /opt/muos/frontend/muxfrontend ] || ui_result=1
        parent_pid=$(awk '/^PPid:/ {print $2}' "/proc/$frontend_pid/status")
        [ "$parent_pid" = "$manager_pid" ] || ui_result=1
        tr '\000' '\n' < "/proc/$frontend_pid/environ" | grep '^SDL_AUDIODRIVER=' > "$state/sdl-audio-env.txt"
        grep -qx SDL_AUDIODRIVER=pipewire "$state/sdl-audio-env.txt" || ui_result=1
        [ -s /run/muos/first_paint ] && [ -f /run/muos/ui/ready ] || ui_result=1
        echo "UI_ID manager=$manager_pid frontend=$frontend_pid parent=$parent_pid"
        echo FIRST_PAINT; cat /run/muos/first_paint
        cat "$state/sdl-audio-env.txt"
        c06_audio_check ui-during || ui_result=1
        "$bounded" 5 pw-dump > "$state/pw-active.json" || ui_result=1
    fi
    if [ "$ui_result" = 0 ]; then
        c06_reference_group reference-44 /usr/share/muos-diagnostic/c06-control-tone.wav 44100 3 || ui_result=1
    fi
    if [ "$ui_result" = 0 ]; then
        read now ignored < /proc/uptime
        deadline=$((${now%%.*} + 90))
        previous=
        echo UI_WINDOW_STARTED
        while :; do
            /usr/libexec/muos-ui-supervisor --status || { ui_result=1; break; }
            module=$(cat "/proc/$frontend_pid/comm") || { ui_result=1; break; }
            if [ "$module" != "$previous" ]; then echo "UI_MODULE=$module"; previous=$module; fi
            read now ignored < /proc/uptime
            [ "${now%%.*}" -lt "$deadline" ] || break
            sleep 0.25
        done
        echo UI_WINDOW_ENDED
        # User stops input before the deadline; this is bounded grace, not a
        # claim that SDL/PipeWire drain is externally measurable here.
        sleep 3
        echo C06_AUDIO_GRACE_SECONDS=3
        c06_audio_check ui-before-stop || ui_result=1
    fi
    c06_ui_stop || ui_result=1
    [ ! -e /run/muos/ui/failed ] || ui_result=1
    [ ! -d "/proc/$frontend_pid" ] || ui_result=1
    [ ! -d "/proc/$manager_pid" ] || ui_result=1
    echo UI_SUPERVISOR_LOG; tail -c 196608 /run/muos/ui/supervisor.log 2>/dev/null
    echo UI_FAILED_MARKER; cat /run/muos/ui/failed 2>/dev/null || :
    echo DRM_AFTER
    "$bounded" 5 /usr/libexec/muos-drm-mode-probe > "$state/drm-after.txt" || ui_result=1
    cat "$state/drm-after.txt"
    cmp -s "$state/drm-before.txt" "$state/drm-after.txt" || ui_result=1
    [ "$ui_result" = 0 ] || return 1
    echo C06_UI_STOPPED=1
}

c06_audio_cleanup() {
    cleanup_result=0
    c06_ui_stop || cleanup_result=1
    # S95 may fail before publishing core/audio; stop partial audio as C05 did.
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
    if [ "$core_bound" = 1 ]; then
        if umount /etc/default/muos-core; then core_bound=0; else cleanup_result=1; fi
    fi
    if [ "$asound_bound" = 1 ]; then
        if umount /opt/muos/device/control/asound.state; then asound_bound=0; else cleanup_result=1; fi
    fi
    if [ "$global_config_bound" = 1 ]; then
        if umount /opt/muos/config; then global_config_bound=0; else cleanup_result=1; fi
    fi
    if [ "$device_config_bound" = 1 ]; then
        if umount /opt/muos/device/config; then device_config_bound=0; else cleanup_result=1; fi
    fi
    grep -qx audio=0 /etc/default/muos-core || cleanup_result=1
    if [ -f "$state/alsa-before.state" ]; then
        /usr/libexec/muos-run-bounded 5 alsactl -U -f "$state/alsa-before.state" restore || cleanup_result=1
        /usr/libexec/muos-run-bounded 3 amixer -c 0 contents > "$state/alsa-restored.txt" || cleanup_result=1
        cmp -s "$state/alsa-before.txt" "$state/alsa-restored.txt" || cleanup_result=1
    fi
    if [ -f "$state/persistent-before.sha256" ]; then
        sha256sum -c "$state/persistent-before.sha256" > "$state/persistent-restore.txt" 2>&1 || cleanup_result=1
    fi
    /opt/muos/frontend/muvarctl build || cleanup_result=1
    echo "C06_RESTORED_CACHE_PATH=$(/opt/muos/frontend/muvarctl get device audio/path)" > "$state/cache-restored.txt"
    echo "C06_RESTORED_CACHE_VOLUME=$(/opt/muos/frontend/muvarctl get global settings/general/volume)" >> "$state/cache-restored.txt"
    echo "C06_RESTORED_CACHE_BOOT_VOLUME=$(/opt/muos/frontend/muvarctl get global settings/advanced/volume)" >> "$state/cache-restored.txt"
    [ "$(/opt/muos/frontend/muvarctl get device audio/path)" = "$(cat /opt/muos/device/config/audio/path)" ] || cleanup_result=1
    [ "$(/opt/muos/frontend/muvarctl get global settings/general/volume)" = "$(cat /opt/muos/config/settings/general/volume)" ] || cleanup_result=1
    [ "$(/opt/muos/frontend/muvarctl get global settings/advanced/volume)" = "$(cat /opt/muos/config/settings/advanced/volume)" ] || cleanup_result=1
    [ "$cleanup_result" = 0 ] || return 1
    echo C06_AUDIO_CLEANUP_OK=1 > "$state/audio-cleanup.txt"
}
