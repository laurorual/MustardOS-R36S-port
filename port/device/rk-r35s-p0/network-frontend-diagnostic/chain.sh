# SPDX-License-Identifier: MIT
# C07 owns entropy, udev and the network. C08 owns only these four services.
c08_main_udev() {
    c08_proc=$1; shift
    c08_main=
    for c08_candidate in "$@"; do
        case "$c08_candidate" in ''|*[!0-9]*) return 1 ;; esac
        [ "$c08_candidate" -gt 1 ] || return 1
        [ "$(awk '/^PPid:/ {print $2}' "$c08_proc/$c08_candidate/status" 2>/dev/null)" = 1 ] || continue
        [ "$(readlink "$c08_proc/$c08_candidate/exe")" = /sbin/udevd ] || continue
        [ -z "$c08_main" ] || return 1
        c08_main=$c08_candidate
    done
    [ -n "$c08_main" ] || return 1
    printf '%s\n' "$c08_main"
}
c08_start_chain() {
    : > "$state/attempted"
    for c08_service in S30dbus-daemon S90muos-storage S95muos-core S96muos-input-ready; do
        echo "$c08_service" >> "$state/attempted"
        [ "$c08_service" != S30dbus-daemon ] || c08_bus_attempted=1
        if [ "$c08_service" = S95muos-core ]; then c06_before_core || return 1; fi
        c08_exec "$c08_service_dir/$c08_service" start || return 1
    done
    for c08_service in S90muos-storage S95muos-core S96muos-input-ready; do
        c08_exec "$c08_service_dir/$c08_service" status || return 1
    done
}
c08_stop_chain() {
    [ -f "$state/attempted" ] || return 0
    c08_stop_error=0
    for c08_service in $(awk '{a[NR]=$0} END {for(i=NR;i>0;i--) print a[i]}' "$state/attempted"); do
        c08_exec "$c08_service_dir/$c08_service" stop || c08_stop_error=1
    done
    [ "$c08_stop_error" = 0 ] || return 1
    rm -f "$state/attempted"
}
