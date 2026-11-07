#!/bin/sh
# SPDX-License-Identifier: MIT
# Read-only selection. Refuse the preserved OS card anywhere in the system.
diag_card() {
    diag_sys=$1
    diag_selected=
    for diag_path in "$diag_sys"/block/mmcblk*; do
        [ -f "$diag_path/device/cid" ] || continue
        diag_hash=$(printf %s "$(cat "$diag_path/device/cid")" | sha256sum)
        diag_hash=${diag_hash%% *}
        case "$diag_hash" in
            9b4fc38015ae4a049ecd796ceceb2ef9473f4773c9b3a066ce59b567c516bbef)
                return 1 ;;
            12d2c78fbc14993fe2f8a00c413a5e3ef8d9659a3eba9a41a77b5c37029aa193)
                [ "$(cat "$diag_path/size")" = 249872384 ] || return 1
                [ -z "$diag_selected" ] || return 1
                diag_selected="/dev/${diag_path##*/}p1" ;;
        esac
    done
    [ -n "$diag_selected" ] || return 1
    printf '%s\n' "$diag_selected"
}
