# SPDX-License-Identifier: MIT
# Last native logger client must have completed before this function runs.
c05_stop_logger() {
    logger_pid=
    if [ -r /run/muos/arborist.pid ]; then
        read logger_pid ignored < /run/muos/arborist.pid || return 1
        case "$logger_pid" in ''|*[!0-9]*) return 1 ;; esac
        [ "$logger_pid" -gt 1 ] || return 1
        [ "$(readlink "/proc/$logger_pid/exe")" = /opt/muos/frontend/mulog ] || return 1
        # Give the native datagram loop time to flush the final service log.
        sleep 1
        kill -TERM "$logger_pid" || return 1
    fi
    count=0
    while pidof mulog >/dev/null && [ "$count" -lt 40 ]; do
        sleep 0.1
        count=$((count + 1))
    done
    ! pidof mulog >/dev/null || return 1
    [ ! -e /run/muos/arborist.pid ] && [ ! -S /run/muos/arborist.sock ] || return 1
    echo C05_LOGGER_STOPPED=1
}
