# SPDX-License-Identifier: MIT
# Called only inside the owned C45 namespace; fixed app, fixed script, one consumption.
c46_file() {
    [ -f "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u:%g:%a:%h' "$1")" = "0:0:$2:1" ]
}
c46_request() {
    c46_file /run/muos/action 600 && c46_file /run/muos/application 600 || return 64
    printf 'app\n' | cmp -s - /run/muos/action || return 64
    printf '%s' "$appdir" | cmp -s - /run/muos/application || return 64
}
c46_validate() {
    c46_request || return 64
    [ ! -e "$capsule/app-consumed" ] && [ ! -L "$capsule/app-consumed" ] || return 64
    [ -d "$appdir" ] && [ ! -L "$appdir" ] && [ "$(readlink -f "$appdir")" = "$appdir" ] || return 64
    [ "$(stat -c '%u:%g:%a' "$appdir")" = 0:0:700 ] || return 64
    [ "$(stat -c '%d:%i' "$appdir")" = "$(stat -c '%d:%i' "$capsule/app-tree/R35S-Diagnostic")" ] || return 64
    c46_file "$appdir/mux_launch.sh" 700 && c46_file "$capsule/launcher.sha256" 600 || return 64
    read expected_sha < "$capsule/launcher.sha256" || return 64
    [ "${#expected_sha}" = 64 ] || return 64
    case "$expected_sha" in *[!0-9a-f]*) return 64 ;; esac
    printf '%s  %s\n' "$expected_sha" "$appdir/mux_launch.sh" | sha256sum -c - >/dev/null || return 64
}
c46_options() {
    c46_file /run/muos/governor 600 && c46_file /run/muos/controller 600 || return 64
    expected_governor=$(cat /opt/muos/device/config/cpu/default) || return 64
    case "$expected_governor" in ''|*[!a-zA-Z0-9_-]*) return 64 ;; esac
    [ "${#expected_governor}" -le 48 ] || return 64
    printf '%s' "$expected_governor" | cmp -s - /run/muos/governor || return 64
    printf 'system' | cmp -s - /run/muos/controller || return 64
    # These are scalar launch options, not requests for the next frontend.
    # Keep CPU/sysfs unchanged and archive only these known test values.
    mv /run/muos/governor "$capsule/state/application-governor.txt" || return 64
    mv /run/muos/controller "$capsule/state/application-controller.txt" || return 64
}
c46_consume() {
    c46_validate || return 64
    c46_options || return 64
    (set -C; : > "$capsule/app-consumed") || return 64
    mv /run/muos/application "$capsule/state/selected-application.txt" || return 64
    mv /run/muos/action "$capsule/state/selected-action.txt" || return 64
}
