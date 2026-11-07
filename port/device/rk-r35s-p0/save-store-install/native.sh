#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
case "${1:-}" in /run/muos-c57.??????) deployment=$1 ;; *) exit 64 ;; esac
case "${2:-}" in inspect|apply|rollback) action=$2 ;; *) exit 64 ;; esac
install_root=/;install_payload=$deployment/payload;install_state=$deployment;install_rw=0
c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
. "$deployment/transaction.sh"
private_fingerprint() {
    for path in /var/lib/muos-network /var/lib/muos-seedrng /root/.ssh /var/lib/muos-diagnostic/boot-seq; do
        [ -e "$path" ] || continue
        find "$path" -type f -exec sha256sum '{}' ';'
        find "$path" -exec stat -c '%n:%u:%g:%a' '{}' ';'
    done | LC_ALL=C sort | sha256sum
}
install_exec() {
    case "$1" in
    guard)
        c25_ready || return 64
        if [ "$action" = rollback ]; then
            [ "$(cat "$c25_store/boot-seq")" -ge "$(cat "$install_payload/boot-seq")" ] || return 64
        else [ "$(cat "$c25_store/boot-seq")" = "$(cat "$install_payload/boot-seq")" ] || return 64; fi
        [ ! -e "$c25_store/c25.once" ] && [ ! -L "$c25_store/c25.once" ] || return 64
        [ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ] || return 64
        if pidof muxretro smoke-check >/dev/null; then return 64; fi
        [ "$(df -Pk / | awk 'NR==2 {print $4}')" -ge 16384 ] || return 64
        ;;
    rw) c25_media && c25_quiet || return 64;install_rw=1;mount -o remount,rw / ;;
    ro) mount -o remount,ro / && c25_root_mode ro ;;
    sync) sync ;;
    directory-created|file-staged|file-installed) return 0 ;;
    verify)
        c25_media && c25_quiet && c25_foundation || return 64
        private_fingerprint > "$deployment/private.after"
        cmp "$deployment/private.before" "$deployment/private.after" || return 64
        ;;
    *) return 64 ;;
    esac
}
finish() {
    rc=$?;trap - EXIT HUP INT TERM
    if [ "$install_rw" = 1 ]; then
        c57_rollback > "$deployment/rollback.log" 2>&1;rollback_rc=$?
        printf 'C57_ROLLBACK_RC=%s\n' "$rollback_rc"
        [ "$rollback_rc" = 0 ] || rc=1
    fi
    if ! c25_root_mode ro; then
        sync
        mount -o remount,ro / || rc=1
    fi
    c25_root_mode ro || rc=1
    printf '%s\n' "$rc" > "$deployment/$action.result"
    touch "$deployment/$action.done"
    exit "$rc"
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
(cd "$deployment" && sha256sum -c SHA256SUMS) >/dev/null || exit 64
install_exec guard || exit 64
# The existing lifetime lock excludes any frontend/runtime writer.
exec 8>/run/muos/session/lifetime.lock
flock -n 8 || exit 64
case "$action" in
inspect) c57_preflight || exit $?;echo C57_INSPECT_OK_NO_PERSISTENT_WRITE ;;
apply)
    mkdir "$deployment/apply.once" || exit 64
    private_fingerprint > "$deployment/private.before"
    c57_apply || exit $?
    echo C57_INSTALLED_ROOT_RO_NO_SERVICE_NO_TOKEN_NO_REBOOT
    ;;
rollback)
    c57_schema && c57_verify || exit 64
    mkdir "$deployment/rollback.once" || exit 64
    private_fingerprint > "$deployment/private.before"
    install_exec rw || exit $?
    c57_rollback || exit $?
    echo C57_ABSENCE_RESTORED_ROOT_RO
    ;;
esac
