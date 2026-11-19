#!/usr/bin/env bash
# shellcheck disable=SC2016
# SPDX-License-Identifier: MIT
# Install files from port/device/rk-r35s-p0/rootfs/ onto the live device root.
#
#   install-rootfs.sh [--tree DIR] [--remove PATH]... [REL_PATH...]
#                         (default: every file; --tree installs a build
#                         staging tree instead of the Git rootfs/ tree)
#
# Each file is staged next to its target and renamed into place (atomic per
# file). The first time a path is touched its original is kept under
# /var/lib/muos-m1-backup/ (a marker records paths that did not exist), so
# `--restore` can undo everything. Root is remounted rw for the install and
# returned to ro if it was ro. Executable bit from Git -> 0755, else 0644.
set -euo pipefail

repo=${MUOS_REPO:-$(cd "$(dirname "$0")/../.." && pwd)}
tree=$repo/port/device/rk-r35s-p0/rootfs
dev=$repo/port/scripts/device.sh
removes=() restore=0
while [ $# -gt 0 ]; do
    case "$1" in
        --remove) removes+=("$2"); shift 2 ;;
        --restore) restore=1; shift ;;
        --tree) tree=$(realpath "$2"); shift 2 ;;
        *) break ;;
    esac
done
if [ $# -gt 0 ]; then files=("$@"); elif [ ${#removes[@]} -gt 0 ]; then files=(); else mapfile -t files < <(cd "$tree" && find . \( -type f -o -type l \) -printf '%P\n' | sort); fi

remote='set -eu
was_ro=0; grep -q "^/dev/root / ext4 ro," /proc/mounts && was_ro=1
mount -o remount,rw /
# Write through a plain bind of the root filesystem so runtime binds (e.g.
# /opt/muos/config -> p3) never hide the real p2 target. S91 copies config
# files added this way into an existing p3 config at the next boot.
R=$(mktemp -d /run/m1-root.XXXXXX); mount --bind / "$R"
finish() { sync; umount "$R"; rmdir "$R"; [ "$was_ro" = 0 ] || mount -o remount,ro / || echo "WARN: root stays rw (busy)"; }
trap finish EXIT
backup=$R/var/lib/muos-m1-backup
mkdir -p "$backup"; chmod 700 "$backup"
keep() {
    [ ! -e "$backup/$1" ] && [ ! -e "$backup/$1.absent" ] || return 0
    mkdir -p "$backup/$(dirname "$1")"
    if [ -e "$R/$1" ] || [ -L "$R/$1" ]; then cp -a "$R/$1" "$backup/$1"; else : > "$backup/$1.absent"; fi
}
if [ "$RESTORE" = 1 ]; then
    cd "$backup"
    find . -type f -name "*.absent" | while read -r m; do p=${m#./}; p=${p%.absent}; rm -f "$R/$p"; echo "restored-absent /$p"; done
    find . \( -type f -o -type l \) ! -name "*.absent" | while read -r f; do p=${f#./}; cp -a "$f" "$R/$p.m1new"; mv -f "$R/$p.m1new" "$R/$p"; echo "restored /$p"; done
    cd /; exit 0
fi
IFS0=$IFS; IFS="|"; set -f # REMOVES is "|"-separated (paths may hold spaces)
for p in $REMOVES; do keep "$p"; rm -f "$R/$p"; echo "removed /$p"; done
IFS=$IFS0; set +f
stage=$(mktemp -d /run/m1-stage.XXXXXX)
tar -xf - -C "$stage"
cd "$stage"
find . -type f | sort | while read -r f; do
    p=${f#./}
    keep "$p"
    mkdir -p "$R/$(dirname "$p")"
    cp "$f" "$R/$p.m1new"
    if [ -x "$f" ]; then chmod 755 "$R/$p.m1new"; else chmod 644 "$R/$p.m1new"; fi
    chown 0:0 "$R/$p.m1new"
    mv -f "$R/$p.m1new" "$R/$p"
    echo "installed /$p"
done
cd /; rm -rf "$stage"'

if [ "$restore" = 1 ]; then
    tar -cf - -T /dev/null | "$dev" run "RESTORE=1 REMOVES='' sh -c '$remote'"
    exit 0
fi
for f in "${files[@]}"; do [ -e "$tree/$f" ] || { echo "not in tree: $f" >&2; exit 1; }; done
joined=$(IFS="|"; echo "${removes[*]}")
case "$joined" in *"'"*) echo "--remove: no quotes in paths" >&2; exit 1 ;; esac
(cd "$tree" && if [ ${#files[@]} -gt 0 ]; then tar -h --owner=0 --group=0 -cf - "${files[@]}"; else tar -cf - -T /dev/null; fi) |
    "$dev" run "RESTORE=0 REMOVES='$joined' sh -c '$remote'"
