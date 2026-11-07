#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
c25_package=/usr/libexec/muos-c25
c25_state=/run/muos/c25
c25_store=/var/lib/muos-diagnostic
. "$c25_package/policy.sh"
. "$c25_package/card-guard.sh"
. "$c25_package/native.sh"
package=/usr/libexec/muos-session; base=/run/muos/session
. "$package/control-functions.sh"
c25_owned() {
    [ -f "$c25_state/session.attempted" ] && session_current || return 1
    [ -f "$cycle/run.conf" ] && cmp -s "$c25_state/session.conf" "$cycle/run.conf" || return 1
    if [ -f "$c25_state/generation" ]; then [ "$(cat "$c25_state/generation")" = "$generation" ] || return 1; fi
}
c25_stop() {
    if c25_owned; then "$package/service.sh" stop; else return 0; fi
}
case "${1:-}" in
 stop)
    [ "$(id -u)" = 0 ] || exit 64
    # No global stop: a different manual generation belongs to its controller.
    c25_stop; exit $? ;;
 start) c25_init_child || exit 64 ;;
 *) exit 64 ;;
esac
[ -d "$c25_state" ] && [ ! -L "$c25_state" ] && [ "$(stat -c '%u:%g:%a' "$c25_state")" = 0:0:700 ] || exit 64
c25_regular "$c25_state/selected" || exit 64
selected=$(cat "$c25_state/selected")
case "$selected" in
 c07)
    [ "$(cat "$c25_state/fallback")" = 1 ] || exit 0
    c25_ready || exit 64
    { echo MUOS-R35S-LAUNCHER-ONCE-C25; echo SELECTED=c07; printf 'BOOT=%s\n' "$(cat "$c25_store/boot-seq")"; echo RESULT=0; echo REASON=one-shot-fallback; } > "$c25_state/FINAL.TXT"
    c25_fat=0
    if c25_publish > "$c25_state/publish.log" 2>&1; then rc=0; else rc=$?; fi
    printf '%s\n' "$rc" > "$c25_state/result"; touch "$c25_state/done"
    exit "$rc" ;;
 c25) ;;
 *) exit 64 ;;
esac
c25_ready || exit 64
c25_matches "$c25_state/grant" GRANT "$(cat "$c25_store/boot-seq")" || exit 64
[ ! -e /run/muos/session/current ] && [ ! -L /run/muos/session/current ] || exit 64
mkdir "$c25_state/session.once" || exit 64
cat > "$c25_state/session.conf" <<'CONF'
enabled=1
preferences_enabled=1
lease_seconds=180
profile_dir=/usr/share/muos-r35s-profile
prerequisites=/usr/libexec/muos-session/prerequisites.sha256
CONF
result=1; reason=startup-failed; c25_fat=0
finish() {
    trap - EXIT HUP INT TERM
    rm -f "$c25_state/ready"
    c25_stop > "$c25_state/stop.log" 2>&1 || result=1
    # A failed start may still have an owned cleanup in progress: never publish
    # success until its done/result and global quiescence are confirmed.
    if c25_owned; then
        [ -f "$cycle/done" ] && [ "$(cat "$cycle/result")" = 0 ] || result=1
    else result=1; fi
    c25_ready || result=1
    { echo MUOS-R35S-LAUNCHER-ONCE-C25; echo SELECTED=c25; printf 'BOOT=%s\nRESULT=%s\nREASON=%s\n' "$(cat "$c25_store/boot-seq")" "$result" "$reason"; } > "$c25_state/FINAL.TXT"
    c25_publish > "$c25_state/publish.log" 2>&1 || result=1
    [ "$c25_fat" = 0 ] || { umount /boot || result=1; }
    printf '%s\n' "$result" > "$c25_state/result"
    touch "$c25_state/done"
    exit "$result"
}
trap finish EXIT
trap 'reason=interrupted; exit 143' HUP INT TERM
touch "$c25_state/session.attempted"
MUOS_SESSION_CONFIG="$c25_state/session.conf" "$package/service.sh" start > "$c25_state/start.log" 2>&1 || exit 1
c25_owned && [ -f "$cycle/ready" ] || exit 1
printf '%s\n' "$generation" > "$c25_state/generation"
{
    echo MUOS-R35S-LAUNCHER-ONCE-C25
    echo SELECTED=c25
    printf 'BOOT=%s\nGENERATION=%s\nLEASE_SECONDS=180\n' "$(cat "$c25_store/boot-seq")" "$generation"
    echo FIRST_PAINT; cat "$cycle/first-paint.txt"
    echo SOFTWARE_VOLUME; cat "$cycle/software-volume.txt"
    echo BRIGHTNESS; cat "$cycle/brightness-active.txt"
} > "$c25_state/START.TXT"
touch "$c25_state/ready"
read now ignored < /proc/uptime; deadline=$((${now%%.*}+330))
while [ ! -f "$cycle/done" ]; do
    read now ignored < /proc/uptime
    [ "${now%%.*}" -lt "$deadline" ] || { reason=cleanup-deadline; exit 1; }
    sleep 1
done
[ "$(cat "$cycle/result")" = 0 ] || { reason=session-failed; exit 1; }
result=0; reason=lease-completed
exit 0
