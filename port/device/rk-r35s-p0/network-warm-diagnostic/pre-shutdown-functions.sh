# SPDX-License-Identifier: MIT
# Abortable transaction. Only callbacks can touch services, USB or PID1.
c17_run() {
    c17_exec preflight || return 64
    [ ! -L "$c17_state" ] && mkdir -m 700 "$c17_state" || return 64
    c17_stopped=0;c17_unbound=0
    for step in baseline network-stop controller-unbind controller-absent archive final-seal;do
        case "$step" in network-stop) c17_stopped=1 ;; controller-unbind) c17_unbound=1 ;; esac
        c17_exec "$step"
        rc=$?
        printf 'C17_STEP=%s RC=%s\n' "$step" "$rc" >> "$c17_state/steps.txt"
        if [ "$rc" != 0 ];then
            c17_exec abort-restore || :
            return 1
        fi
    done
    # No callback after this point can revoke an accepted PID1 request.
    c17_exec request
}
