#!/bin/sh
# SPDX-License-Identifier: MIT
# C66 fixed RAM provider; diagnostic C46 libmuxmod remains a menu override.
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
capsule=${1:-};operation=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64;; esac
case "$operation:$#" in check:2|launch:2) ;; *) exit 64;; esac
[ "$(id -u)" = 0 ]
[ "$(findmnt -rn -T "$capsule" -o FSTYPE)" = tmpfs ]
for path in "$capsule" "$capsule/lib" "$capsule/provider-lib"; do
 [ -d "$path" ] && [ ! -L "$path" ]
 [ "$(stat -c '%u:%g:%a' "$path")" = 0:0:700 ]
done
while read -r digest name; do
 file=$capsule/$name
 [ -f "$file" ] && [ ! -L "$file" ]
 [ "$(stat -c '%u:%g:%a:%h' "$file")" = 0:0:700:1 ]
 [ "$(sha256sum "$file" | cut -d' ' -f1)" = "$digest" ]
done <<'C66_PROVIDER'
639c1df8c75dc5007abfb87817d8cb1ea6b3ed7e0366f008e976a0e74491791e provider-lib/libui.so
2913dbf7d901a258d338995e0d937c2f6559465c41a3bd0e097072820f57cd21 provider-lib/libmuxcom.so
bfd909c6eae5d6d692025e8a0b489840c9a552d3ad22e902183b6265d700ae17 provider-lib/libmuxmod.so
99377c313fdb5401e4535be4750afb8db9c6c6acc052818a2eee0c956cbe8683 provider-lib/libplutosvg.so
639c1df8c75dc5007abfb87817d8cb1ea6b3ed7e0366f008e976a0e74491791e lib/libui.so
2913dbf7d901a258d338995e0d937c2f6559465c41a3bd0e097072820f57cd21 lib/libmuxcom.so
99377c313fdb5401e4535be4750afb8db9c6c6acc052818a2eee0c956cbe8683 lib/libplutosvg.so
C66_PROVIDER
if [ "$operation" = launch ]; then
 [ "${LD_BIND_NOW:-}" = 1 ]
 [ "${LD_LIBRARY_PATH:-}" = "/opt/muos/frontend/lib" ]
fi
printf 'C77_PROVIDER_VALID files=7 operation=%s\n' "$operation"
