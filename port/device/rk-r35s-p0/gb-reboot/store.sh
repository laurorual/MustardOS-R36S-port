#!/bin/sh
# SPDX-License-Identifier: MIT
# C54 exposes only C53 read operations, with a fixed load role.
set -eu
capsule=${1:-};op=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64;;esac
case "$op" in seed|verify) ;; *) exit 64;;esac
[ "$#" = 2 ] && [ -d "$capsule" ] && [ ! -L "$capsule" ] || exit 64
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ] || exit 64
for name in role store-base.sha256;do
 [ -f "$capsule/$name" ] && [ ! -L "$capsule/$name" ] || exit 64
 [ "$(stat -c '%u:%g:%a:%h' "$capsule/$name")" = 0:0:600:1 ] || exit 64
done
printf 'load\n' | cmp -s - "$capsule/role" || exit 64
[ -f "$capsule/store-base.sh" ] && [ ! -L "$capsule/store-base.sh" ] || exit 64
[ "$(stat -c '%u:%g:%a:%h' "$capsule/store-base.sh")" = 0:0:700:1 ] || exit 64
digest=$(cat "$capsule/store-base.sha256")
[ "${#digest}" = 64 ] || exit 64
case "$digest" in *[!0-9a-f]*) exit 64;;esac
printf '%s  %s\n' "$digest" "$capsule/store-base.sh" | sha256sum -c - >/dev/null
exec /bin/sh "$capsule/store-base.sh" "$capsule" "$op"
