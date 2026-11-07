# SPDX-License-Identifier: MIT
# Opt-in C21: only two typed settings cross the private runtime/data boundary.
session_preferences_pair() {
    prefs_volume=$(sed -n 's/^VOLUME=//p' "$1")
    prefs_brightness=$(sed -n 's/^BRIGHTNESS=//p' "$1")
    case "$prefs_volume:$prefs_brightness" in *[!0-9:]*|:*|*:) return 1 ;; esac
    [ "$prefs_volume" -ge 0 ] && [ "$prefs_volume" -le 100 ] || return 1
    [ "$prefs_brightness" -ge 40 ] && [ "$prefs_brightness" -le 160 ] || return 1
    printf 'MUOS-PREFS-1\nVOLUME=%s\nBRIGHTNESS=%s\n' "$prefs_volume" "$prefs_brightness" | cmp -s - "$1"
}
session_preferences_prepare() {
    . "$package/data-functions.sh"
    prefs_data_source || return 1
    prefs_mount=$state/data
    mkdir -m 700 "$prefs_mount" || return 1
    ! findmnt -rn -S "$prefs_device" >/dev/null || return 1
    mount -t ext4 -o rw,nosuid,nodev,noexec,data=ordered "$prefs_device" "$prefs_mount" || return 1
    printf '%s\n' "$prefs_mount" >> "$state/mounts"
    prefs_data_mounted rw || return 1
    "$package/bin/muos-preferences" --dir "$prefs_mount/MUOS/preferences" load > "$state/preferences-loaded.txt" || return 1
    session_preferences_pair "$state/preferences-loaded.txt" || return 1
    # The static 21-file profile has already passed, before these RAM overrides.
    printf '%s\n' "$prefs_volume" > "$state/config/settings/general/volume" || return 1
    printf '%s\n' "$prefs_brightness" > "$state/config/settings/general/brightness" || return 1
    printf '0\n' > "$state/config/settings/advanced/volume" || return 1
    # Do not import stale per-output levels into saved-volume policy0. This
    # directory is a private copy; no original slot is changed or persisted.
    for prefs_slot in "$state/volume"/*; do
        [ -e "$prefs_slot" ] || continue
        [ -f "$prefs_slot" ] && [ ! -L "$prefs_slot" ] || return 1
        printf '%s\n' "$prefs_volume" > "$prefs_slot" || return 1
    done
    session_bind "$prefs_mount" /userdata || return 1
    : > "$state/writer-original.sha256"
    for prefs_path in /etc/asound.conf /usr/share/alsa/alsa.conf; do
        [ -f "$prefs_path" ] && [ ! -L "$prefs_path" ] || return 1
        sha256sum "$prefs_path" >> "$state/writer-original.sha256" || return 1
        prefs_copy=$state/files/$(printf '%s' "$prefs_path" | tr / _)
        cp -p "$prefs_path" "$prefs_copy" || return 1
        session_bind "$prefs_copy" "$prefs_path" || return 1
    done
    (cd /usr/share/wireplumber && find . -type f -exec sha256sum '{}' ';' | sort) > "$state/wireplumber-before.sha256" || return 1
    cp -a /usr/share/wireplumber "$state/wireplumber" || return 1
    session_bind "$state/wireplumber" /usr/share/wireplumber || return 1
    mkdir -m 700 "$state/home" "$state/log" || return 1
    session_bind "$state/home" /root || return 1
    session_bind "$state/log" /opt/muos/log || return 1
    findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro
}
session_preferences_sink() {
    [ ! -e /run/muos/headphones ] || return 1
    prefs_target=$(/opt/muos/frontend/muvarctl get device audio/pf_internal) || return 1
    [ "$prefs_target" = alsa_output.platform-rk817-sound.playback.0.0 ] || return 1
    prefs_actual=$(wpctl inspect @DEFAULT_AUDIO_SINK@ | sed -n 's/.*node\.name = "\([^"]*\)".*/\1/p' | head -1)
    [ "$prefs_actual" = "$prefs_target" ] || return 1
    [ "$(cat /opt/muos/config/settings/advanced/volume)" = 0 ] || return 1
}
session_preferences_running() {
    session_preferences_sink || return 1
    [ "$(cat /opt/muos/config/settings/general/volume)" = "$prefs_volume" ] || return 1
    [ "$(/opt/muos/frontend/muvarctl get global settings/general/volume)" = "$prefs_volume" ] || return 1
    session_preferences_software_volume || return 1
    # The native bright helper updates both the hardware and the RAM varstore.
    session_exec /opt/muos/script/device/bright.sh "$prefs_brightness" || return 1
    [ "$(cat /sys/class/backlight/backlight/brightness)" = "$prefs_brightness" ] || return 1
    printf 'VOLUME=%s\nBRIGHTNESS=%s\n' "$prefs_volume" "$prefs_brightness" > "$state/preferences-active.txt"
}
session_preferences_software_volume() {
    prefs_level=$(wpctl get-volume @DEFAULT_AUDIO_SINK@) || return 1
    # Muting is transient and outside the typed pair's contract.
    case "$prefs_level" in *MUTED*) return 1 ;; esac
    prefs_percent=$(printf '%s\n' "$prefs_level" | awk '$1=="Volume:" && $2 ~ /^[0-9]+[.][0-9]+$/ {print int($2*100+0.5)}')
    [ "$prefs_percent" = "$prefs_volume" ]
}
session_preferences_checkpoint() {
    # Called only after UI/hotkeys stop, before audio ramps or transient blanking.
    prefs_data_mounted rw && session_preferences_sink || return 1
    prefs_volume=$(cat /opt/muos/config/settings/general/volume) || return 1
    prefs_brightness=$(cat /opt/muos/config/settings/general/brightness) || return 1
    printf 'MUOS-PREFS-1\nVOLUME=%s\nBRIGHTNESS=%s\n' "$prefs_volume" "$prefs_brightness" > "$state/preferences-candidate.txt"
    session_preferences_pair "$state/preferences-candidate.txt" || return 1
    for prefs_key in volume brightness; do
        [ "$(/opt/muos/frontend/muvarctl get global settings/general/$prefs_key)" = "$(cat /opt/muos/config/settings/general/$prefs_key)" ] || return 1
    done
    [ "$(cat /sys/class/backlight/backlight/brightness)" = "$prefs_brightness" ] || return 1
    session_preferences_software_volume || return 1
    "$package/bin/muos-preferences" --dir "$prefs_mount/MUOS/preferences" save "$prefs_volume" "$prefs_brightness" > "$state/preferences-saved.txt" || return 1
    cmp -s "$state/preferences-candidate.txt" "$state/preferences-saved.txt"
}
