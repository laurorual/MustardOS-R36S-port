# SPDX-License-Identifier: MIT
session_bind() {
    [ ! -L "$2" ] && ! findmnt -rn -M "$2" >/dev/null || return 1
    mount --bind "$1" "$2" || return 1
    printf '%s\n' "$2" >> "$state/mounts"
}
session_volume_manifest() {
    (cd /opt/muos/share/volume && find . -type f -exec sha256sum '{}' ';' | sort)
}
session_prepare() {
    (cd "$profile_dir" && sha256sum -c "$package/profile-source.sha256") > "$state/profile-source.txt" 2>&1 || return 1
    [ "$(jq -r .model "$profile_dir/profile.json")" = 'R36S-V12 2023-08-18 Panel 0' ] || return 1
    [ "$(jq -r .ui_autostart "$profile_dir/manifest.json")" = false ] || return 1
    jq -r '.files|keys[]' "$profile_dir/manifest.json" > "$state/profile-files"
    [ "$(wc -l < "$state/profile-files")" -eq 21 ] || return 1
    jq -r '.files|to_entries[]|"\(.value.sha256)  /\(.key)"' "$profile_dir/manifest.json" > "$state/effective.sha256"
    : > "$state/original.sha256"
    while IFS= read -r path; do
        case "$path" in *..*|*[!a-zA-Z0-9_./-]*) return 1 ;; esac
        case "$path" in
            opt/muos/config/*|opt/muos/device/config/*|opt/muos/device/control/asound.state|etc/default/muos-core|etc/default/muos-ui|opt/muos/share/hotkey/r35s-bringup.json|opt/muos/share/theme/MustardOS/sound/navigate.wav|opt/muos/share/theme/MustardOS/sound/info_open.wav|opt/muos/share/theme/MustardOS/sound/info_close.wav) ;;
            *) return 1 ;;
        esac
        [ -f "/$path" ] && [ ! -L "/$path" ] || return 1
        sha256sum "/$path" >> "$state/original.sha256" || return 1
    done < "$state/profile-files"
    "$bounded" 5 alsactl -U -f "$state/mixer-before.state" store || return 1
    "$bounded" 3 amixer -c 0 contents > "$state/mixer-before.txt" || return 1
    cat /sys/class/backlight/backlight/brightness > "$state/brightness-before.txt" || return 1
    [ "$(cat /sys/class/backlight/backlight/max_brightness)" = 160 ] || return 1
    value=$(cat "$state/brightness-before.txt")
    [ "$value" -ge 40 ] && [ "$value" -le 160 ] || return 1
    session_volume_manifest > "$state/volume-before.sha256" || return 1
    [ -z "$(find /opt/muos/share/volume -type l -print)" ] || return 1
    "$bounded" 5 "$package/bin/muos-drm-mode-probe" > "$state/drm-before.txt" || return 1
    cp -a /opt/muos/config "$state/config" || return 1
    cp -a /opt/muos/device/config "$state/device-config" || return 1
    cp -a /opt/muos/share/volume "$state/volume" || return 1
    mkdir "$state/files" || return 1
    while IFS= read -r path; do
        case "$path" in
            opt/muos/config/*) destination=$state/config/${path#opt/muos/config/} ;;
            opt/muos/device/config/*) destination=$state/device-config/${path#opt/muos/device/config/} ;;
            *) continue ;;
        esac
        cat "$profile_dir/overlay/$path" > "$destination" || return 1
    done < "$state/profile-files"
    session_bind "$state/config" /opt/muos/config || return 1
    session_bind "$state/device-config" /opt/muos/device/config || return 1
    session_bind "$state/volume" /opt/muos/share/volume || return 1
    while IFS= read -r path; do
        case "$path" in opt/muos/config/*|opt/muos/device/config/*) continue ;; esac
        filename=$(printf '%s' "$path" | tr '/' '_')
        [ "$path" != etc/default/muos-ui ] || filename=ui.conf
        cp "$profile_dir/overlay/$path" "$state/files/$filename" || return 1
        if [ "$filename" = ui.conf ]; then
            mv "$state/files/$filename" "$state/ui.conf" || return 1
            session_bind "$state/ui.conf" "/$path" || return 1
        else
            session_bind "$state/files/$filename" "/$path" || return 1
        fi
    done < "$state/profile-files"
    sha256sum -c "$state/effective.sha256" > "$state/profile-effective.txt" 2>&1
}
session_stop_logger() {
    if [ -r /run/muos/arborist.pid ]; then
        read logger ignored < /run/muos/arborist.pid || return 1
        case "$logger" in ''|*[!0-9]*) return 1 ;; esac
        [ "$logger" -gt 1 ] && [ "$(readlink "/proc/$logger/exe")" = /opt/muos/frontend/mulog ] || return 1
        kill -TERM "$logger" || return 1
    fi
    n=0
    while pidof mulog >/dev/null && [ "$n" -lt 50 ]; do sleep 0.1; n=$((n+1)); done
    ! pidof mulog >/dev/null && [ ! -S /run/muos/arborist.sock ] && [ ! -e /run/muos/arborist.pid ]
}
session_restore() {
    restore_failed=0
    if [ -f "$state/mounts" ]; then
        for target in $(awk '{a[NR]=$0} END{for(i=NR;i>0;i--)print a[i]}' "$state/mounts"); do
            umount "$target" || restore_failed=1
        done
    fi
    if [ -f "$state/mixer-before.state" ]; then
        "$bounded" 5 alsactl -U -f "$state/mixer-before.state" restore || restore_failed=1
        "$bounded" 3 amixer -c 0 contents > "$state/mixer-after.txt" || restore_failed=1
        cmp -s "$state/mixer-before.txt" "$state/mixer-after.txt" || restore_failed=1
    fi
    if [ -f "$state/brightness-before.txt" ]; then
        cat "$state/brightness-before.txt" > /sys/class/backlight/backlight/brightness || restore_failed=1
        cat /sys/class/backlight/backlight/brightness > "$state/brightness-after.txt"
        cmp -s "$state/brightness-before.txt" "$state/brightness-after.txt" || restore_failed=1
    fi
    if [ -f "$state/original.sha256" ]; then
        sha256sum -c "$state/original.sha256" > "$state/original-restored.txt" 2>&1 || restore_failed=1
        session_volume_manifest > "$state/volume-after.sha256" || restore_failed=1
        cmp -s "$state/volume-before.sha256" "$state/volume-after.sha256" || restore_failed=1
        /opt/muos/frontend/muvarctl build || restore_failed=1
        for key in settings/general/volume settings/general/brightness; do
            [ "$(/opt/muos/frontend/muvarctl get global "$key")" = "$(cat "/opt/muos/config/$key")" ] || restore_failed=1
        done
    fi
    if [ -f "$state/drm-before.txt" ]; then
        "$bounded" 5 "$package/bin/muos-drm-mode-probe" > "$state/drm-after.txt" || restore_failed=1
        cmp -s "$state/drm-before.txt" "$state/drm-after.txt" || restore_failed=1
    fi
    if [ -f "$state/writer-original.sha256" ]; then
        sha256sum -c "$state/writer-original.sha256" > "$state/writer-restored.txt" 2>&1 || restore_failed=1
        (cd /usr/share/wireplumber && find . -type f -exec sha256sum '{}' ';' | sort) > "$state/wireplumber-after.sha256" || restore_failed=1
        cmp -s "$state/wireplumber-before.sha256" "$state/wireplumber-after.sha256" || restore_failed=1
    fi
    [ "$restore_failed" = 0 ]
}
