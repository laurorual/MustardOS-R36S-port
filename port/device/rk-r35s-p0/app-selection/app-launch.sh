#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
capsule=${1:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
[ "$#" = 1 ] && [ -d "$capsule" ] && [ ! -L "$capsule" ] || exit 64
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
exec "$capsule/muxretro" "$capsule/core.so" --no-content --diagnostic-seconds=30
