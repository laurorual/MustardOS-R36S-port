#!/bin/sh
# SPDX-License-Identifier: MIT
# C58 fixed installed CLI, load-only diagnostic dispatch; no executable fallback.
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
root=/
capsule=${1:-};op=${2:-};store=${3:-};identity=${4:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64 ;; esac
case "$op:$#" in status:4|export:5) ;; *) exit 64 ;; esac
[ "$(id -u)" = 0 ]
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro
[ -d "$capsule" ] && [ ! -L "$capsule" ] || exit 64
[ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
[ "$(findmnt -rn -T "$capsule" -o FSTYPE)" = tmpfs ]
[ ! -e "$capsule/save-store" ] && [ ! -L "$capsule/save-store" ] || exit 64
for name in identity role; do
 [ -f "$capsule/$name" ] && [ ! -L "$capsule/$name" ] || exit 64
 [ "$(stat -c '%u:%g:%a:%h' "$capsule/$name")" = 0:0:600:1 ]
done
printf 'load\n' | cmp -s - "$capsule/role"
[ "${#identity}" = 64 ]
case "$identity" in *[!0-9a-f]*) exit 64 ;; esac
printf '%s\n' "$identity" | cmp -s - "$capsule/identity"
[ "$store" = "$capsule/data/MUOS/port-saves-v1/gb/$identity" ]
if [ "$op" = export ]; then
 [ "$5" = /run/muos/storage/pickles/state/core.so/GB/private ]
fi
# Pin all four files, including the manifest itself, and reject parent aliases.
while read -r digest mode name; do
 path=${root%/}/$name
 parent=$(dirname "$path")
 while [ "$parent" != / ] && [ "$parent" != // ] && [ "$parent" != "$root" ]; do
  [ -d "$parent" ] && [ ! -L "$parent" ] || exit 64
  [ "$(stat -c '%u:%g:%a' "$parent")" = 0:0:755 ]
  parent=$(dirname "$parent")
 done
 [ -f "$path" ] && [ ! -L "$path" ] || exit 64
 [ "$(stat -c '%u:%g:%a:%h' "$path")" = "0:0:$mode:1" ]
 [ "$(sha256sum "$path" | cut -d' ' -f1)" = "$digest" ]
done <<'C58_PINNED_FILES'
e9540c40e00a9b46b3eee0efbb2a669bdc16f6721359a1fd2a1800836929056d 755 usr/libexec/muos-save-store/muos-save-store
ac48f884bffd40f68a0a4cb4b428548af5430292d359108d74a86dc42f4167e3 644 usr/libexec/muos-save-store/payload.sha256
982f991a5aaa6aabe0f2decc45abae103dfe9f776ac3bd248d327532469ee60d 644 usr/share/muos-save-store/contract.json
958d8ca1c391272d8d1c2b46b3ee5b1632c4ec11b9aedbc0436a9539dfb88c81 644 usr/share/licenses/muos-save-store/LICENSE
C58_PINNED_FILES
binary=${root%/}/usr/libexec/muos-save-store/muos-save-store
printf 'C58_INSTALLED_DISPATCH operation=%s binary_verified=1 capsule_binary_absent=1\n' "$op" >&2
shift 2
exec "$binary" "$op" "$@"
