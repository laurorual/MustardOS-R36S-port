#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[ "$(id -u)" = 0 ] || exit 64
package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
base=/run/muos/session
. "$package/control-functions.sh"
case "${1:-}" in start|status|stop) action=$1 ;; *) exit 2 ;; esac
if [ "$action" = status ]; then
    session_current && [ -f "$cycle/ready" ] && session_identity "$cycle" || exit 3
    echo "muOS session: ready $generation pid=$session_pid"
    exit 0
fi
mkdir -p "$base"; [ ! -L "$base" ] || exit 64
[ "$(stat -c %u "$base")" = 0 ] || exit 64
chmod 700 "$base"
exec 9>"$base/control.lock"
flock -x 9
if [ "$action" = stop ]; then
    session_current || exit 0
    if session_identity "$cycle"; then
        kill -TERM "$session_pid" || exit 1
        count=0
        while session_identity "$cycle" && [ "$count" -lt 1000 ]; do sleep 0.1; count=$((count+1)); done
        ! session_identity "$cycle" || { echo 'muOS session: cleanup still running'; exit 1; }
    fi
    [ -f "$cycle/done" ] && [ "$(cat "$cycle/result")" = 0 ]
    exit $?
fi
config=${MUOS_SESSION_CONFIG:-/etc/default/muos-session}
[ -f "$config" ] && [ ! -L "$config" ] || exit 64
case "$(stat -c '%u:%g:%a' "$config")" in 0:0:600|0:0:644) ;; *) exit 64 ;; esac
enabled=0; lease_seconds=180; profile_dir=/usr/share/muos-r35s-profile; prerequisites=; preferences_enabled=0
. "$config"
case "$preferences_enabled" in 0|1) ;; *) exit 64 ;; esac
[ "$enabled" = 1 ] || { [ "$enabled" = 0 ]; exit $?; }
case "$lease_seconds" in ''|*[!0-9]*) exit 64 ;; esac
[ "$lease_seconds" -ge 30 ] && [ "$lease_seconds" -le 600 ] || exit 64
case "$profile_dir" in /*) ;; *) exit 64 ;; esac
if [ "$preferences_enabled" = 1 ]; then
    [ -f "$package/payload.sha256" ] && [ ! -L "$package/payload.sha256" ] || exit 64
    (cd "$package" && sha256sum -c payload.sha256) >/dev/null || exit 64
fi
if session_current; then
    if session_identity "$cycle"; then
        [ -f "$cycle/ready" ] && exit 0
        echo 'muOS session: existing startup/cleanup in progress' >&2; exit 1
    fi
    [ -f "$cycle/done" ] || { echo 'muOS session: incomplete previous transaction'; exit 1; }
fi
sequence=0
[ ! -f "$base/sequence" ] || sequence=$(cat "$base/sequence")
case "$sequence" in ''|*[!0-9]*|?????*) exit 64 ;; esac
[ "$sequence" -lt 9999 ] || exit 64
sequence=$((sequence+1)); generation=$(printf 'run-%04d' "$sequence"); cycle=$base/$generation
mkdir -m 700 "$cycle"
cp "$config" "$cycle/run.conf"; chmod 600 "$cycle/run.conf"
printf '%s\n' "$sequence" > "$base/sequence"
printf '%s\n' "$generation" > "$base/current.tmp"; mv "$base/current.tmp" "$base/current"
# The worker owns its lifetime lock; never inherit the controller's flock.
( exec 9>&-
  if nohup setsid "$package/mount-namespace" /bin/sh "$package/worker.sh" "$cycle"; then rc=0; else rc=$?; fi
  [ -f "$cycle/done" ] || printf '%s\n' "$rc" > "$cycle/launch-failed"
) > "$cycle/launcher.log" 2>&1 < /dev/null &
count=0
while [ "$count" -lt 1100 ]; do
    if [ -f "$cycle/ready" ] && session_identity "$cycle"; then echo "muOS session: started $generation"; exit 0; fi
    [ ! -f "$cycle/done" ] || { cat "$cycle/result"; exit 1; }
    [ ! -f "$cycle/launch-failed" ] || exit 1
    sleep 0.1; count=$((count+1))
done
if session_identity "$cycle"; then kill -TERM "$session_pid" || :; fi
echo 'muOS session: start deadline; cleanup requested' >&2
exit 1
