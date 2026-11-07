# SPDX-License-Identifier: MIT
# C09 wraps the audited C06/C08 chain. Configuration remains bound to RAM.
c09_monitor=
c09_brightness_saved=0
c09_volume_bound=0
c09_volume_manifest() {
    (cd /opt/muos/share/volume && find . -type f -exec sha256sum '{}' ';' | sort)
}
c09_stop_monitor() {
    if [ -n "$c09_monitor" ]; then
        kill -TERM "$c09_monitor" 2>/dev/null || :
        wait "$c09_monitor" 2>/dev/null || :
        c09_monitor=
    fi
}
c06_before_core() {
    c09_brightness=/sys/class/backlight/backlight/brightness
    c09_max=$(cat /sys/class/backlight/backlight/max_brightness) || return 1
    c09_original=$(cat "$c09_brightness") || return 1
    [ "$c09_max" = 160 ] && [ "$c09_original" -ge 40 ] && [ "$c09_original" -le 160 ] || return 1
    printf '%s\n' "$c09_original" > "$state/brightness-before.txt" || return 1
    c09_brightness_saved=1
    [ -d /opt/muos/share/volume ] && [ ! -L /opt/muos/share/volume ] || return 1
    [ -z "$(find /opt/muos/share/volume -type l -print)" ] || return 1
    c09_volume_manifest > "$state/volume-store-before.sha256" || return 1
    cp -a /opt/muos/share/volume "$state/volume-store" || return 1
    mount --bind "$state/volume-store" /opt/muos/share/volume || return 1
    c09_volume_bound=1
    sha256sum /opt/muos/config/settings/general/brightness \
        /opt/muos/config/settings/advanced/incbright /opt/muos/config/settings/advanced/incvolume \
        /opt/muos/config/settings/advanced/overdrive \
        /opt/muos/share/hotkey/r35s-bringup.json > "$state/controls-before.sha256" || return 1
    c09_orig_before_core || return 1
    # The native helpers update these files and the RAM cache. Keep their
    # startup state consistent with the actual backlight; prevent overdrive.
    printf '%s\n' "$c09_original" > "$state/config/settings/general/brightness" || return 1
    printf '5\n' > "$state/config/settings/advanced/incbright" || return 1
    printf '5\n' > "$state/config/settings/advanced/incvolume" || return 1
    printf '0\n' > "$state/config/settings/advanced/overdrive" || return 1
}
c06_frontend() {
    # Exercise the real helpers once before the user window, returning to unity
    # and the original backlight before the reference tones/menu are started.
    (
        set -e
        /usr/libexec/muos-run-bounded 8 /opt/muos/script/device/audio.sh D || exit 1
        [ "$(/opt/muos/frontend/muvarctl get global settings/general/volume)" = 95 ] || exit 1
        wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{exit !(int($2*100+0.5)==95)}' || exit 1
        echo HELPER_VOLUME_DOWN=95
        /usr/libexec/muos-run-bounded 8 /opt/muos/script/device/audio.sh U || exit 1
        [ "$(/opt/muos/frontend/muvarctl get global settings/general/volume)" = 100 ] || exit 1
        echo HELPER_VOLUME_UP=100
        /usr/libexec/muos-run-bounded 8 /opt/muos/script/device/bright.sh D || exit 1
        [ "$(cat "$c09_brightness")" = "$((c09_original-5))" ] || exit 1
        echo "HELPER_BRIGHT_DOWN=$((c09_original-5))"
        /usr/libexec/muos-run-bounded 8 /opt/muos/script/device/bright.sh U || exit 1
        [ "$(cat "$c09_brightness")" = "$c09_original" ] || exit 1
        echo "HELPER_BRIGHT_UP=$c09_original"
    ) > "$state/helpers.txt" 2>&1 || return 1
    # A small state-change trace measures single steps without reading input
    # devices a second time or interfering with muinput/muhotkey ownership.
    (
        trap - EXIT HUP INT TERM
        previous=
        while :; do
            v=$(cat /opt/muos/config/settings/general/volume)
            b=$(cat /sys/class/backlight/backlight/brightness)
            case "$v:$b" in *[!0-9:]*|:*|*:) exit 1 ;; esac
            if [ "$v:$b" != "$previous" ]; then
                read timestamp ignored < /proc/uptime
                printf 'CONTROL_STATE t=%s volume=%s brightness=%s\n' "$timestamp" "$v" "$b"
                wpctl get-volume @DEFAULT_AUDIO_SINK@ || :
                previous=$v:$b
            fi
            sleep 0.2
        done
    ) > "$state/controls-events.txt" 2>&1 &
    c09_monitor=$!
    c09_orig_frontend
}
c09_restore() {
    c09_rc=0
    c09_stop_monitor
    if [ "$c09_volume_bound" = 1 ]; then
        if umount /opt/muos/share/volume; then c09_volume_bound=0; else c09_rc=1; fi
        c09_volume_manifest > "$state/volume-store-after.sha256" || c09_rc=1
        cmp -s "$state/volume-store-before.sha256" "$state/volume-store-after.sha256" || c09_rc=1
    fi
    if [ "$c09_brightness_saved" = 1 ]; then
        [ "$(cat /sys/class/backlight/backlight/max_brightness)" = "$c09_max" ] || return 1
        if [ "$(cat "$c09_brightness")" != "$c09_original" ]; then
            printf '%s\n' "$c09_original" > "$c09_brightness" || c09_rc=1
        fi
        cat "$c09_brightness" > "$state/brightness-after.txt" || c09_rc=1
        cmp -s "$state/brightness-before.txt" "$state/brightness-after.txt" || c09_rc=1
        if [ -f "$state/controls-before.sha256" ]; then
            sha256sum -c "$state/controls-before.sha256" > "$state/controls-restored.txt" || c09_rc=1
        fi
        value=$(/opt/muos/frontend/muvarctl get global settings/general/brightness)
        printf 'RESTORED_CACHE_BRIGHTNESS=%s\n' "$value" > "$state/controls-cache.txt"
        [ "$value" = "$(cat /opt/muos/config/settings/general/brightness)" ] || c09_rc=1
    fi
    return "$c09_rc"
}
