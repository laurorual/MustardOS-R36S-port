#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
caller_system_root=/
caller_root=/usr/libexec/muos-caller
caller_manifest_sha=@MANIFEST_SHA@
c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
[ ! -L "$caller_root/functions.sh" ] && [ "$(stat -c '%u:%g:%a:%h' "$caller_root/functions.sh")" = 0:0:644:1 ]
[ "$(sha256sum "$caller_root/functions.sh" | cut -d' ' -f1)" = @FUNCTIONS_SHA@ ]
. "$caller_root/functions.sh"
caller_exec() {
    case "$1" in
    platform)
        c25_ready || return 64
        [ ! -e "$c25_store/c25.once" ] && [ ! -L "$c25_store/c25.once" ] || return 64
        [ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ] || return 64
        ;;
    capsule) [ "$(findmnt -rn -T "$2" -o FSTYPE)" = tmpfs ] ;;
    boot) cat "$c25_store/boot-seq" /proc/sys/kernel/random/boot_id ;;
    staged) return 0 ;;
    run)
        exec "$2/runner" 240 "$2/watchdog" /usr/libexec/muos-session/mount-namespace /bin/sh "$caller_root/worker.sh" "$2" observe
        ;;
    *) return 64;;esac
}
case "${1:-}:$#" in
check:1) c105_package && c105_dependencies && caller_exec platform || exit 64;echo C105_CALLER_CHECK_OK_NO_UI ;;
stage:2) c105_stage "$2";echo C105_CALLER_STAGE_OK_RAM_ONLY ;;
run:3) c105_run "$2" "$3" ;;
*) exit 64;;esac
