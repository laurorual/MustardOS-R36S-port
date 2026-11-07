# SPDX-License-Identifier: MIT
# PID identity checks are shared by the controller and its isolated fixtures.
session_identity() {
    [ -f "$1/manager" ] || return 1
    read session_pid session_start < "$1/manager" || return 1
    case "$session_pid:$session_start" in *[!0-9:]*|:*|*:) return 1 ;; esac
    [ "$session_pid" -gt 1 ] || return 1
    [ "$(awk '{print $22}' "/proc/$session_pid/stat" 2>/dev/null)" = "$session_start" ] || return 1
    tr '\000' '\n' < "/proc/$session_pid/cmdline" | grep -Fxq "$package/worker.sh" || return 1
    tr '\000' '\n' < "/proc/$session_pid/cmdline" | grep -Fxq "$1"
}
session_current() {
    [ -f "$base/current" ] || return 1
    read generation < "$base/current" || return 1
    case "$generation" in run-[0-9][0-9][0-9][0-9]) ;; *) return 1 ;; esac
    cycle=$base/$generation
    [ -d "$cycle" ] && [ ! -L "$cycle" ]
}
