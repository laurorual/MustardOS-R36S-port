#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copy ROMs from the host to the device's ROM library (p3 ROMS/<DIR>).
#   rom-push.sh DIR FILE...
# DIR is the folder under ROMS (GB, NES, ...); muOS picks the system from
# the folder name (info/manifest/assign.json). Existing files are replaced.
# Each file is checked by SHA256 on the device after the copy. Uses
# device.sh (key-only root over SSH); a GUI client can do the same over
# SFTP (port 2222, /userdata/ROMS).
set -euo pipefail
dev=$(dirname "$0")/device.sh
[ $# -ge 2 ] || { sed -n '3,9p' "$0"; exit 2; }
dir=$1; shift
case "$dir" in ''|*/*|.*) echo "DIR must be one folder name, e.g. NES" >&2; exit 2 ;; esac
for f in "$@"; do [ -f "$f" ] || { echo "not a file: $f" >&2; exit 1; }; done
dst=/userdata/ROMS/$dir
"$dev" run "mkdir -p '$dst' && df -k /userdata | tail -n1" >/dev/null
for f in "$@"; do
    base=$(basename "$f")
    case "$base" in *\'*) echo "skipped (quote in name): $base" >&2; continue ;; esac
    want=$(sha256sum "$f" | cut -d' ' -f1)
    "$dev" push "$f" "$dst" >/dev/null
    got=$("$dev" run "sha256sum '$dst/$base' | cut -d' ' -f1")
    [ "$got" = "$want" ] || { echo "FAIL $base: device sha256 $got != $want" >&2; exit 1; }
    echo "ok $dir/$base"
done
"$dev" run sync
