#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
case "${1:-}" in /run/muos-c102.??????) deployment=$1;;*) exit 64;;esac
case "${2:-}" in inspect|apply) action=$2;;*) exit 64;;esac
[ ! -L "$deployment" ] && [ "$(stat -c '%u:%g:%a' "$deployment")" = 0:0:700 ] || exit 64
(cd "$deployment" && sha256sum -c SHA256SUMS) >/dev/null || exit 64
layout_root=/;layout_payload=$deployment/payload;layout_rw=0
layout_temporary=0;layout_published=0;layout_directory=0
c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
. "$deployment/transaction.sh"
private_fingerprint() {
    (set -e
    for path in /var/lib/muos-network /var/lib/muos-seedrng /root/.ssh /var/lib/muos-diagnostic /var/lib/muos-preferences /userdata/MUOS/preferences; do
        printf '%s\n' "$path"
        if [ -e "$path" ] || [ -L "$path" ];then
            find "$path" -type f -exec sha256sum '{}' ';'
            find "$path" -exec stat -c '%n:%u:%g:%a:%h:%s' '{}' ';'
        else printf 'absent\n';fi
    done) > "$deployment/private.raw" || return 64
    LC_ALL=C sort "$deployment/private.raw" > "$deployment/private.sorted" || return 64
    sha256sum "$deployment/private.sorted" || return 64
    rm "$deployment/private.raw" "$deployment/private.sorted"
}
layout_exec() {
    case "$1" in
    guard)
        c25_ready && sh "$deployment/guard.sh" || return 64
        [ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ] || return 64
        [ "$(df -Pk / | awk 'NR==2 {print $4}')" -ge 16384 ] || return 64
        ;;
    rw) c25_media && c25_quiet || return 64;layout_rw=1;mount -o remount,rw / ;;
    ro) mount -o remount,ro / && c25_root_mode ro ;;
    sync) sync ;;
    staged|linked|published|directory) return 0 ;;
    verify)
        c25_media && c25_quiet && c25_foundation || return 64
        private_fingerprint > "$deployment/private.after" || return 64
        cmp "$deployment/private.before" "$deployment/private.after"
        ;;
    *) return 64;;esac
}
finish() {
    rc=$?;trap - EXIT HUP INT TERM
    if [ "$layout_rw" = 1 ];then
        c102_rollback > "$deployment/rollback.log" 2>&1;rollback_rc=$?
        printf 'C102_ROLLBACK_RC=%s\n' "$rollback_rc"
        rc=1
    fi
    if ! c25_root_mode ro;then sync;mount -o remount,ro / || rc=1;fi
    c25_root_mode ro || rc=1
    printf '%s\n' "$rc" > "$deployment/$action.result"
    touch "$deployment/$action.done"
    exit "$rc"
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
layout_exec guard || exit 64
if [ ! -e /run/muos/session ] && [ ! -L /run/muos/session ];then mkdir -m 700 /run/muos/session || exit 64;fi
[ ! -L /run/muos/session ] && [ "$(stat -c '%u:%g:%a' /run/muos/session)" = 0:0:700 ] || exit 64
exec 8>/run/muos/session/lifetime.lock
flock -n 8 || exit 64
case "$action" in
inspect) c102_preflight || exit $?;echo C102_INSPECT_OK_NO_PERSISTENT_WRITE;;
apply)
    mkdir "$deployment/apply.once" || exit 64
    private_fingerprint > "$deployment/private.before" || exit 64
    c102_apply || exit $?
    sh "$deployment/guard.sh" && c102_verify || exit 64
    echo C102_INSTALLED_444_BYTES_ONE_DIRECTORY_ROOT_RO
    ;;
esac
