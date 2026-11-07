# SPDX-License-Identifier: MIT
# C12 ordering library only. Caller supplies guarded/bounded boot_exec STEP LIMIT.
# No inittab/rcS/device integration is enabled by sourcing this file.
c12_step() {
    boot_exec "$1" "$2"
    rc=$?
    printf 'STEP=%s LIMIT=%s RC=%s\n' "$1" "$2" "$rc" >> "$boot_state/steps.txt" || return 1
    if [ "${c12_power_record:-0}" = 1 ]; then
        printf 'STEP=%s LIMIT=%s RC=%s\n' "$1" "$2" "$rc" >> "$power_state/steps.txt" || return 1
    fi
    return "$rc"
}
c12_close_entropy() {
    [ "$c12_entropy_live" = 1 ] || return 0
    # One attempt only; failure must not cause another seed consume/credit.
    c12_entropy_live=0
    c12_step entropy.stop 30
}
c12_fallback() {
    if [ "$c12_session_attempted" = 1 ]; then
        c12_step session.stop 110 || :
        c12_step session.quiescent 5 || :
    fi
    c12_close_entropy || :
    c12_step root.seal 10 || :
    # Keep existing networking/udev available for diagnosis on startup failure.
    printf 'failed\n' > "$boot_state/start-result"
    return 1
}
c12_recover_network() {
    # One physical reconnect, never another saved-seed load or key generation.
    mkdir "$boot_state/recovery-once" 2>/dev/null || return 64
    c12_step recovery.ready 5 || return 1
    c12_step network.stop 20 || return 1
    if c12_step usb.wait-remove 95 && c12_step usb.wait-add 120 &&
       c12_step usb.switch 120 && c12_step network.recover 120 &&
       c12_step network.status 5; then
        printf 'recovered\n' > "$boot_state/network-mode"
        return 0
    fi
    # Fail closed if a partial recovery cannot be cleaned up.
    c12_step network.stop 20 || return 2
    return 1
}
c12_start() {
    mkdir -p "$boot_state" || return 1
    # Saved entropy must not be loaded again on a second call in the same boot.
    if ! mkdir "$boot_state/start-once" 2>/dev/null; then
        [ -f "$boot_state/ready" ] || return 64
        c12_step session.status 5
        return $?
    fi
    c12_entropy_live=1; c12_session_attempted=0
    c12_step entropy.start 90 || { c12_fallback; return 1; }
    c12_step udev.start 45 || { c12_fallback; return 1; }
    printf 'offline\n' > "$boot_state/network-mode"
    if c12_step usb.switch 120; then
        if c12_step network.start 120; then
            printf 'online\n' > "$boot_state/network-mode"
        else
            # A degraded/offline UI is permitted only after partial network cleanup.
            c12_step network.stop 20 || { c12_fallback; return 1; }
        fi
    fi
    c12_close_entropy || { c12_fallback; return 1; }
    c12_step root.seal 10 || { c12_fallback; return 1; }
    if [ "${recover_network:-0}" = 1 ] && [ "$(cat "$boot_state/network-mode")" = offline ]; then
        c12_recover_network
        recovery_rc=$?
        # rc1 permits offline UI after cleanup. rc2/64 forbids another attempt.
        case "$recovery_rc" in 0|1) ;; *) c12_fallback; return 1 ;; esac
    fi
    c12_session_attempted=1
    c12_step session.start 120 || { c12_fallback; return 1; }
    # start0 with disabled config is not proof that the UI is ready.
    c12_step session.status 5 || { c12_fallback; return 1; }
    printf 'ready\n' > "$boot_state/start-result"
    touch "$boot_state/ready"
}
c12_prepare_shutdown() {
    mkdir -p "$boot_state" || return 1
    [ ! -f "$boot_state/stopped" ] || return 0
    # Call this BEFORE asking PID1 to reboot/power off. BusyBox shutdown action
    # failures cannot cancel PID1's subsequent TERM/KILL of all processes.
    c12_step session.stop 110 || return 1
    c12_step session.quiescent 5 || return 1
    c12_step network.stop 20 || return 1
    c12_step udev.stop 20 || return 1
    c12_step root.sync 10 || return 1
    c12_step root.seal 10 || return 1
    rm -f "$boot_state/ready"
    touch "$boot_state/stopped"
}
