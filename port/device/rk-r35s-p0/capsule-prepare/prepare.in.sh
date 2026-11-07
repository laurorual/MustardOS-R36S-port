#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
capsule_system_root=/
capsule_package_root=/usr/libexec/muos-capsule
capsule_manifest_sha=@MANIFEST_SHA@
capsule_core_sha=@CORE_SHA@
[ ! -L "$capsule_package_root/functions.sh" ] && [ "$(stat -c '%u:%g:%a:%h' "$capsule_package_root/functions.sh")" = 0:0:644:1 ] || exit 64
[ "$(sha256sum "$capsule_package_root/functions.sh" | cut -d' ' -f1)" = @FUNCTIONS_SHA@ ] || exit 64
. "$capsule_package_root/functions.sh"
capsule_exec() {
    case "$1" in
    platform)
        c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
        . /usr/libexec/muos-c25/policy.sh
        . /usr/libexec/muos-c25/card-guard.sh
        . /usr/libexec/muos-c25/native.sh
        c25_ready
        ;;
    tmpfs) [ "$(findmnt -rn -T "$2" -o FSTYPE)" = tmpfs ] ;;
    stage) sh /usr/libexec/muos-caller/caller.sh stage "$2" >/dev/null ;;
    copied) return 0 ;;
    staged)
        . /usr/libexec/muos-caller/functions.sh
        caller_system_root=/;caller_root=/usr/libexec/muos-caller
        caller_manifest_sha=$(cat "$2/caller-stage/package")
        caller_exec() { case "$1" in boot) cat /var/lib/muos-diagnostic/boot-seq /proc/sys/kernel/random/boot_id;;*) return 64;;esac; }
        c105_staged "$2" && c105_assets "$2"
        ;;
    *) return 64;;esac
}
case "${1:-}:$#" in
check:1) capsule_package && capsule_exec platform || exit 64;echo C107_PREPARER_CHECK_OK_NO_UI ;;
prepare:2) capsule_prepare "$2";echo C107_CAPSULE_PREPARED_RAM_ONLY ;;
*) exit 64;;esac
