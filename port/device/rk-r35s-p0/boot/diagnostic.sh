#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
boot_package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 64
boot_state=/run/muos/boot
state=/run/muos/boot-diagnostic
. "$boot_package/native-functions.sh"
screen() { printf '\033[37;40m\033[2J\033[H%s\n' "$1" > /dev/tty0; }
c12_guard && c12_read_config && [ "$enabled" = 1 ] || exit 64
[ ! -L "$state" ] && mkdir -m 700 "$state" || exit 64
printf '3 4 1 7\n' > /proc/sys/kernel/printk
sequence_dir=/var/lib/muos-diagnostic
[ ! -L "$sequence_dir" ] && [ "$(stat -c '%u:%g:%a' "$sequence_dir")" = 0:0:700 ] || exit 64
[ -f "$sequence_dir/boot-seq" ] && [ ! -L "$sequence_dir/boot-seq" ] || exit 64
sequence=$(cat "$sequence_dir/boot-seq") || exit 64
case "$sequence" in ''|*[!0-9]*|?????*) exit 64 ;; esac
[ "$sequence" -lt 9999 ] || exit 64
sequence=$((sequence+1))
printf '%s\n' "$sequence" > "$sequence_dir/boot-seq.tmp" &&
    mv "$sequence_dir/boot-seq.tmp" "$sequence_dir/boot-seq" || exit 1
printf '%s\n' "$sequence" > "$state/sequence"
sync
screen 'muOS - R35S / Panel 0
C12: starting controlled session and network.
If USB RECONNECT NEEDED appears, reconnect the dongle.
No buttons until the menu appears. Next boot defaults to C07.'
"$boot_package/service.sh" start > "$state/start.log" 2>&1
start_rc=$?
printf '%s\n' "$start_rc" > "$state/start-rc"
public_report() {
    echo MUOS-R35S-BOOT-P4-C12
    echo "BOOT_SEQ=$sequence PHASE=$1 START_RC=$start_rc"
    printf 'NETWORK_MODE='; cat "$boot_state/network-mode" 2>/dev/null || echo unknown
    printf 'ROOT_RO='; if c12_root_ro; then echo 1; else echo 0; fi
    printf 'TAINT='; cat /proc/sys/kernel/tainted
    # Only fixed step names/numbers: never copy network private logs/config/keys.
    if [ -f "$boot_state/steps.txt" ]; then
        grep -E '^STEP=[a-z.-]+ LIMIT=[0-9]+ RC=[0-9]+$' "$boot_state/steps.txt" | tail -n 64
    fi
    printf 'SEED_STOPPED='; if [ -f /run/muos/entropy/stopped ] && [ ! -e /run/muos/entropy/ready ]; then echo 1; else echo 0; fi
    if [ "$1" = FINAL ]; then
        echo "SESSION_QUIESCENT_RC=$quiescent_rc NETWORK_RC=$network_rc"
        echo "START_LOG_SAVE_RC=$start_saved"
        if [ -f /run/muos/session/current ]; then
            generation=$(cat /run/muos/session/current)
            case "$generation" in run-[0-9][0-9][0-9][0-9])
                printf 'SESSION_GENERATION=%s\n' "$generation"
                if [ -f "/run/muos/session/$generation/report.txt" ]; then
                    grep -E '^RESULT=[0-9]+ REASON=[a-z-]+$' "/run/muos/session/$generation/report.txt"
                fi ;;
            esac
        fi
    fi
}
public_report START > "$state/START.txt"
"$boot_package/bin/muos-run-bounded" 20 "$boot_package/diagnostic-save.sh" START > "$state/save-start.log" 2>&1
start_saved=$?
# Wait for lease cleanup. status3 alone is deliberately insufficient.
read now ignored < /proc/uptime
deadline=$((${now%%.*}+150)); quiescent_rc=1
while :; do
    if "$boot_package/service.sh" check-stop > "$state/quiescent.log" 2>&1; then quiescent_rc=0; break; fi
    read now ignored < /proc/uptime
    [ "${now%%.*}" -lt "$deadline" ] || break
    sleep 1
done
if [ "$quiescent_rc" != 0 ]; then
    "$boot_package/bin/muos-run-bounded" 110 "$session_package/service.sh" stop > "$state/stop.log" 2>&1 || :
    "$boot_package/service.sh" check-stop > "$state/quiescent.log" 2>&1; quiescent_rc=$?
fi
"$boot_package/bin/muos-run-bounded" 5 "$boot_package/step.sh" network.status > "$state/network-status.log" 2>&1
network_rc=$?
public_report FINAL > "$state/FINAL.txt"
"$boot_package/bin/muos-run-bounded" 20 "$boot_package/diagnostic-save.sh" FINAL > "$state/save-final.log" 2>&1
final_saved=$?
if [ "$start_rc:$quiescent_rc:$network_rc:$start_saved:$final_saved" = 0:0:0:0:0 ] &&
   c12_root_ro && [ "$(cat /proc/sys/kernel/tainted)" = 0 ] && ! findmnt -rn -M /boot >/dev/null; then
    screen "muOS - R35S / Panel 0
C12: SESSION / WIFI / SSH OK
IP: $(cat /run/muos/c07/address)  Port: 2222
Logs saved: DIAG10/$(printf 'BOOT%04d' "$sequence")
Root read-only. FAT unmounted. Next boot defaults to C07.
Keep powered on for SSH collection."
    exit 0
fi
screen "muOS C12: STOPPED
Diagnostic finished; do not transcribe logs.
DIAG10/$(printf 'BOOT%04d' "$sequence") / root_ro=$(if c12_root_ro; then echo 1; else echo 0; fi)
Keep powered on if SSH works. Next boot defaults to C07."
exit 1
