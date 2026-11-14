#!/bin/sh
# SPDX-License-Identifier: MIT
# Port adapter for upstream script/web/service.sh (muxwebserv): SSH (web/sshd)
# and SFTP (web/sftp) only; the other web services are not ported.
case "${1:-}" in
    apply) exec /usr/libexec/muos-network/worker service "${2:-}" ;;
    stopall) /usr/libexec/muos-network/worker service off ;;
    *) exec /usr/libexec/muos-network/worker service all ;;
esac
