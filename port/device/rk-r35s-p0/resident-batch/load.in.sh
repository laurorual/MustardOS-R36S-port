#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
case "${1:-}:$#" in check:1|adopt:2) ;;*) exit 64;;esac
rb_system_root=/;rb_root=/usr/libexec/muos-batch-v1
rb_manifest_sha=@RESIDENT_MANIFEST_SHA@
caller_system_root=/;caller_root=/usr/libexec/muos-caller;caller_manifest_sha=@CALLER_MANIFEST_SHA@
for p in "$caller_root/functions.sh" "$rb_root/resident-functions.sh";do
 [ -f "$p" ] && [ ! -L "$p" ] && [ "$(stat -c %u:%g:%a:%h "$p")" = 0:0:644:1 ] || exit 64
done
printf '%s  %s\n' @CALLER_FUNCTIONS_SHA@ "$caller_root/functions.sh" @RESIDENT_FUNCTIONS_SHA@ "$rb_root/resident-functions.sh" | sha256sum -c - >/dev/null
. "$caller_root/functions.sh"
. "$rb_root/resident-functions.sh"
c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
caller_exec() {
 case "$1" in
 platform) c25_ready && [ ! -e "$c25_store/c25.once" ] && [ ! -L "$c25_store/c25.once" ] && [ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ] ;;
 capsule) [ "$(findmnt -rn -T "$2" -o FSTYPE)" = tmpfs ] ;;
 boot) cat "$c25_store/boot-seq" /proc/sys/kernel/random/boot_id ;;
 adopt) sh "$2/contract-v3/caller.sh" adopt "$2" >/dev/null ;;
 *) return 64;;esac
}
case "$1" in
 check) rb_package && c105_package && c105_dependencies && caller_exec platform || exit 64;echo C122_RESIDENT_BATCH_CHECK_OK_NO_UI ;;
 adopt) rb_adopt "$2";echo C122_RESIDENT_BATCH_ADOPTED_ZERO_UPLOADS ;;
esac
