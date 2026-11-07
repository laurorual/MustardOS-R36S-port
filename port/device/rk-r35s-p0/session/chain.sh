# SPDX-License-Identifier: MIT
session_start_chain() {
    : > "$state/attempted"
    for service in S30dbus-daemon S90muos-storage S95muos-core S96muos-input-ready S99muos-ui; do
        if [ "$service" = S99muos-ui ]; then
            printf 'enabled=1\nhotkeys=1\n' > "$state/ui.conf" || return 1
        fi
        echo "$service" >> "$state/attempted"
        session_exec "$service_dir/$service" start || return 1
        [ "$service" = S30dbus-daemon ] || session_exec "$service_dir/$service" status || return 1
    done
}
session_stop_chain() {
    [ -f "$state/attempted" ] || return 0
    failed=0
    for service in $(awk '{a[NR]=$0} END{for(i=NR;i>0;i--) print a[i]}' "$state/attempted"); do
        session_exec "$service_dir/$service" stop || failed=1
    done
    [ "$failed" = 0 ] || return 1
    rm -f "$state/attempted"
}
