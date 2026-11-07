# SPDX-License-Identifier: MIT
# Included in the C04 runner. The installed UI configuration stays disabled.
c04_frontend() {
    ui_result=0
    ui_config_bound=0
    frontend_pid=0
    manager_pid=0
    for item in 'system debug_mode 2' 'global settings/general/sound 0' 'global settings/power/idle_display 0' 'global settings/power/idle_sleep 0'; do
        # Fixed local words only, never untrusted input.
        set -- $item
        /opt/muos/frontend/muvarctl set "$1" "$2" "$3" || return 1
    done
    /usr/libexec/muos-run-bounded 5 /usr/libexec/muos-drm-mode-probe > "$state/drm-before.txt" 2>&1 || return 1
    echo 'DRM_BEFORE'; cat "$state/drm-before.txt"
    printf 'enabled=1\nhotkeys=0\n' > "$state/ui.conf" || return 1
    mount --bind "$state/ui.conf" /etc/default/muos-ui || return 1
    ui_config_bound=1
    /usr/libexec/muos-run-bounded 25 /etc/init.d/S99muos-ui start || ui_result=1
    if [ "$ui_result" = 0 ]; then
        read manager_pid ignored < /run/muos/ui/manager || ui_result=1
        frontend_pid=$(awk '/^CHILD frontend / {pid=$3} END {print pid}' /run/muos/ui/supervisor.log)
        case "$frontend_pid:$manager_pid" in *[!0-9:]*|:*|*:) ui_result=1 ;; esac
        [ "$(readlink "/proc/$frontend_pid/exe")" = /opt/muos/frontend/muxfrontend ] || ui_result=1
        parent_pid=$(awk '/^PPid:/ {print $2}' "/proc/$frontend_pid/status")
        [ "$parent_pid" = "$manager_pid" ] || ui_result=1
        [ -s /run/muos/first_paint ] && [ -f /run/muos/ui/ready ] || ui_result=1
        echo "UI_ID manager=$manager_pid frontend=$frontend_pid parent=$parent_pid"
        echo 'FIRST_PAINT'; cat /run/muos/first_paint
        ! pidof muhotkey pipewire wireplumber >/dev/null || ui_result=1
    fi
    if [ "$ui_result" = 0 ]; then
        read now ignored < /proc/uptime
        deadline=$((${now%%.*} + 75))
        previous=
        echo 'UI_WINDOW_STARTED'
        while :; do
            /usr/libexec/muos-ui-supervisor --status || { ui_result=1; break; }
            module=$(cat "/proc/$frontend_pid/comm") || { ui_result=1; break; }
            if [ "$module" != "$previous" ]; then
                echo "UI_MODULE=$module"
                previous=$module
            fi
            read now ignored < /proc/uptime
            [ "${now%%.*}" -lt "$deadline" ] || break
            sleep 0.25
        done
        echo 'UI_WINDOW_ENDED'
    fi
    # Always use the installed stop path, including after a failed start.
    /usr/libexec/muos-run-bounded 15 /etc/init.d/S99muos-ui stop || ui_result=1
    /usr/libexec/muos-ui-supervisor --status
    [ "$?" = 3 ] || ui_result=1
    [ ! -e /run/muos/ui/failed ] || ui_result=1
    [ ! -d "/proc/$frontend_pid" ] || ui_result=1
    [ ! -d "/proc/$manager_pid" ] || ui_result=1
    if [ "$ui_config_bound" = 1 ]; then umount /etc/default/muos-ui || ui_result=1; fi
    grep -qx enabled=0 /etc/default/muos-ui || ui_result=1
    echo 'UI_SUPERVISOR_LOG'
    tail -c 196608 /run/muos/ui/supervisor.log 2>/dev/null
    echo 'UI_FAILED_MARKER'
    cat /run/muos/ui/failed 2>/dev/null || :
    echo 'DRM_AFTER'
    /usr/libexec/muos-run-bounded 5 /usr/libexec/muos-drm-mode-probe > "$state/drm-after.txt" 2>&1 || ui_result=1
    cat "$state/drm-after.txt"
    cmp -s "$state/drm-before.txt" "$state/drm-after.txt" || ui_result=1
    if [ "$ui_result" = 0 ]; then echo 'C04_UI_STOPPED=1'; fi
    return "$ui_result"
}
