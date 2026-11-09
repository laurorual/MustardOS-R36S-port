#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
v2_root=${0%/caller.sh}
case "$v2_root" in /run/muos-prefs-data.??????/contract-v2) ;;*) exit 64;;esac
v2_cap=${v2_root%/contract-v2}
case "${1:-}:$#" in check:1|adopt:2|staged:2) ;;*) exit 64;;esac
v2_manifest_sha=@MANIFEST_SHA@
caller_system_root=/;caller_root=/usr/libexec/muos-caller
caller_manifest_sha=@LEGACY_MANIFEST_SHA@
c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
for file in "$caller_root/functions.sh" "$v2_root/functions.sh";do
 [ -f "$file" ] && [ ! -L "$file" ] && [ "$(stat -c %u:%g:%a:%h "$file")" = 0:0:644:1 ] || exit 64
done
printf '%s  %s\n' @LEGACY_FUNCTIONS_SHA@ "$caller_root/functions.sh" @FUNCTIONS_SHA@ "$v2_root/functions.sh" | sha256sum -c - >/dev/null
. "$caller_root/functions.sh"
. "$v2_root/functions.sh"
caller_exec() {
 case "$1" in
 platform) c25_ready && [ ! -e "$c25_store/c25.once" ] && [ ! -L "$c25_store/c25.once" ] && [ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ] ;;
 capsule) [ "$(findmnt -rn -T "$2" -o FSTYPE)" = tmpfs ] ;;
 boot) cat "$c25_store/boot-seq" /proc/sys/kernel/random/boot_id ;;
 *) return 64;;
 esac
}
case "${1:-}:$#" in
 check:1) c119_package && c105_package && c105_dependencies && caller_exec platform || exit 64;echo C119_CONTRACT_CHECK_OK_NO_UI ;;
 adopt:2) c119_adopt "$2";echo C119_ADOPTED_CAPSULE_READY_NO_UI ;;
 staged:2) c119_staged "$2";echo C119_STAGED_CHECK_OK_NO_UI ;;
 # C119 qualifies adoption/check only. A later explicit version will enable run.
 *) exit 64;;
esac
