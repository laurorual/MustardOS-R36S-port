# SPDX-License-Identifier: MIT
# Read-only C23 gate. Optional tree prefix is for host fixtures only; PID1
# bootstrap always calls without arguments, against its actual root.
candidate_boot_check() {
    candidate_prefix=${1:-/}
    case "$candidate_prefix" in /*) ;; *) return 1 ;; esac
    candidate_prefix=${candidate_prefix%/}
    grep -qx enabled=0 "$candidate_prefix/etc/default/muos-ui" || return 1
    grep -qx audio=1 "$candidate_prefix/etc/default/muos-core" || return 1
    grep -qx enabled=0 "$candidate_prefix/etc/default/muos-session" || return 1
    grep -qx preferences_enabled=0 "$candidate_prefix/etc/default/muos-session" || return 1
    [ "$(grep -c '^::sysinit:/usr/libexec/muos-c07-run$' "$candidate_prefix/etc/inittab")" = 1 ] || return 1
    [ "$(grep -c '^::shutdown:/usr/libexec/muos-c07-run stop$' "$candidate_prefix/etc/inittab")" = 1 ] || return 1
    ! grep -E '^([^#].*)::?(sysinit|shutdown):.*(muos-boot|/rcS|/rcK|S98|S99)' "$candidate_prefix/etc/inittab" >/dev/null || return 1
    candidate_state=$candidate_prefix/var/lib/muos-diagnostic
    [ -d "$candidate_state" ] && [ ! -L "$candidate_state" ] || return 1
    [ "$(stat -c %a "$candidate_state")" = 700 ] || return 1
    [ -f "$candidate_state/boot-seq" ] && [ ! -L "$candidate_state/boot-seq" ] || return 1
    [ "$(stat -c %a "$candidate_state/boot-seq")" = 600 ] || return 1
    if [ -z "$candidate_prefix" ]; then
        [ "$(stat -c '%u:%g' "$candidate_state")" = 0:0 ] || return 1
        [ "$(stat -c '%u:%g' "$candidate_state/boot-seq")" = 0:0 ] || return 1
    fi
    candidate_sequence=$(cat "$candidate_state/boot-seq") || return 1
    case "$candidate_sequence" in ''|*[!0-9]*|?????*) return 1 ;; esac
    [ "$candidate_sequence" -le 9998 ] || return 1
    candidate_count=0
    while read -r candidate_digest candidate_name candidate_extra; do
        [ -z "$candidate_extra" ] && [ "${#candidate_digest}" = 64 ] || return 1
        case "$candidate_digest" in *[!0-9a-f]*) return 1 ;; esac
        case "$candidate_name" in *..*|*[!a-zA-Z0-9_./-]*) return 1 ;; esac
        case "$candidate_name" in /*) ;; *) return 1 ;; esac
        candidate_actual=$(sha256sum "$candidate_prefix$candidate_name") || return 1
        [ "${candidate_actual%% *}" = "$candidate_digest" ] || return 1
        candidate_count=$((candidate_count+1))
    done < "$candidate_prefix/usr/libexec/muos-session/prerequisites.sha256"
    [ "$candidate_count" -gt 0 ]
}
