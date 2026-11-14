#!/bin/sh
# SPDX-License-Identifier: MIT
# Port adapter for upstream script/web/ssid.sh (muxnetscan): SSIDs to /tmp/net_scan.
exec /usr/libexec/muos-network/worker scan
