# SPDX-License-Identifier: MIT
# Abortable only until power_exec request. Caller holds the coordinator lock.
c12_power_report() {
    power_phase=$1
    {
        echo MUOS-R35S-POWER-P4-C12
        echo "BOOT_SEQ=$power_sequence PHASE=$power_phase ACTION=$action"
        echo "OUTCOME=$power_outcome"
        # This is intent/evidence BEFORE the syscall, never proof of power loss.
        echo PID1_REQUEST_NOT_YET_ATTEMPTED=1
        if [ -f "$power_state/steps.txt" ]; then cat "$power_state/steps.txt"; fi
    } > "$power_diagnostic/$power_phase.txt" || return 1
    power_exec save "$power_phase"
}
c12_power_abort() {
    power_outcome=$1
    c12_power_report PFAIL || :
    return 1
}
c12_power_request() {
    # Refuse C07, incomplete diagnostic/archive, or an already-stopped cycle.
    # A failed attempt is not retried automatically in this boot.
    power_exec check || return 64
    power_diagnostic=/run/muos/boot-diagnostic
    power_sequence=$(cat "$power_diagnostic/sequence") || return 64
    case "$power_sequence" in ''|*[!0-9]*|?????*) return 64 ;; esac
    [ "$power_sequence" -gt 0 ] && [ "$power_sequence" -le 9999 ] || return 64
    power_state=$boot_state/power
    [ ! -L "$power_state" ] && mkdir -m 700 "$power_state" || return 64
    power_outcome=preflight-pending
    c12_power_report PBEGIN || return 1
    # c12_step also records these six results in the public power transaction.
    c12_power_record=1
    c12_prepare_shutdown
    power_stop_rc=$?
    c12_power_record=0
    [ "$power_stop_rc" = 0 ] || { c12_power_abort stop-failed; return 1; }
    power_exec sealed || { c12_power_abort seal-failed; return 1; }
    power_outcome=preflight-complete
    c12_power_report PREADY || { c12_power_abort archive-failed; return 1; }
    # Recheck after the FAT write/sync/unmount, immediately before PID1.
    power_exec sealed || { c12_power_abort final-seal-failed; return 1; }
    printf '%s\n' "$action" > "$boot_state/power-request" || return 1
    power_exec request "$action"
}
