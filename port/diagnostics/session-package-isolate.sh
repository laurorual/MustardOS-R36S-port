#!/bin/sh
# SPDX-License-Identifier: MIT
# C22 test only: hide the boot package in a private parent namespace.
set -eu
case "${1:-}" in /run/muos-c21.??????) directory=$1 ;; *) exit 64 ;; esac
[ "$(readlink /proc/self/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ] || exit 64
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro
[ -d /usr/libexec/muos-boot ] && [ ! -L /usr/libexec/muos-boot ]
! findmnt -rn -M /usr/libexec/muos-boot >/dev/null
[ -d "$directory/boot-hidden" ] && [ ! -L "$directory/boot-hidden" ]
[ -z "$(ls -A "$directory/boot-hidden")" ]
owned=0
finish() {
    rc=$?;trap - EXIT
    if [ "$owned" = 1 ]; then umount /usr/libexec/muos-boot || rc=1;fi
    exit "$rc"
}
trap finish EXIT
mount --bind "$directory/boot-hidden" /usr/libexec/muos-boot
owned=1
[ ! -e /usr/libexec/muos-boot/card-guard.sh ]
export MUOS_SESSION_CONFIG=$directory/session.conf
sh "$directory/package/service.sh" start
# The worker has cloned this namespace and retains its own hidden boot path.
echo C22_STARTED_WITH_BOOT_PACKAGE_HIDDEN
