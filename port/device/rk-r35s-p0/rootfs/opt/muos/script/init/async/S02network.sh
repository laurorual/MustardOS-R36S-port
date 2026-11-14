#!/bin/sh
# SPDX-License-Identifier: MIT
# Port adapter for upstream muOS internal/script/init/async/S02network.sh (the
# contract muxnetwork/muxnetprofile call): usr/libexec/muos-network/worker.
w=/usr/libexec/muos-network/worker
case "${1:-}" in
    start|restart) exec "$w" restart ;;
    connect) exec "$w" connect "${2:-}" ;;
    disconnect) exec "$w" disconnect ;;
    stop|unload) exec /etc/init.d/S41muos-network stop ;;
    load) exec "$w" load ;;
    status) exec "$w" status ;;
    *) echo "Usage: $0 {start|connect <profile>|stop|disconnect|restart|load|unload|status}" >&2; exit 1 ;;
esac
