#!/bin/sh
# SPDX-License-Identifier: MIT
# Caller supplies a service directory and executor. Tests use real failing
# fixture executables; production uses the bounded executor on this rootfs.
c01_start_chain() {
    service_dir=$1
    mkdir -p "$c01_state"
    : > "$c01_state/attempted"
    for service in S10udev S30dbus-daemon S90muos-storage S95muos-core S96muos-input-ready S99muos-ui; do
        printf '%s\n' "$service" >> "$c01_state/attempted"
        c01_exec "$service_dir/$service" start || return 1
        if [ "$service" = S10udev ]; then c01_udev_ready || return 1; fi
    done
    for service in S90muos-storage S95muos-core S96muos-input-ready; do
        c01_exec "$service_dir/$service" status || return 1
    done
}
c01_stop_chain() {
    service_dir=$1
    [ -f "$c01_state/attempted" ] || return 0
    failure=0
    for service in $(awk '{a[NR]=$0} END {for(i=NR;i>0;i--) print a[i]}' "$c01_state/attempted"); do
        c01_exec "$service_dir/$service" stop || failure=1
    done
    rm -f "$c01_state/attempted"
    return "$failure"
}
