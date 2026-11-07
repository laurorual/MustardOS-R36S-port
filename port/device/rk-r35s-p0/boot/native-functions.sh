# SPDX-License-Identifier: MIT
# Native C12 adapters. These functions never load private file contents into reports.
c12_guard() {
    [ "$(id -u)" = 0 ] || return 64
    [ "$(readlink /proc/1/exe)" = /bin/busybox ] || return 64
    [ "$(readlink /proc/self/ns/mnt)" = "$(readlink /proc/1/ns/mnt)" ] || return 64
    [ "$(uname -r)" = 4.4.189-muos-r35s-p4 ] || return 64
    [ "$(tr -d '\000' < /sys/firmware/devicetree/base/model)" = 'R36S-V12 2023-08-18 Panel 0' ] || return 64
    [ "$(cat /proc/sys/kernel/tainted)" = 0 ] || return 64
    [ "$(findmnt -rn -o FSTYPE -T /run)" = tmpfs ] || return 64
    . "$boot_package/card-guard.sh"
    boot_partition=$(diag_card /sys) || return 64
    boot_root=${boot_partition%p1}p2
    [ "$(findmnt -rn -o MAJ:MIN /)" = "$(cat /sys/class/block/${boot_root##*/}/dev)" ] || return 64
    [ "$(findmnt -rn -o FSTYPE /)" = ext4 ] || return 64
    [ "$(findmnt -rn -o PARTUUID /)" = 4d554432-02 ] || return 64
    ! findmnt -rn -M /boot >/dev/null || return 64
    [ "$(cat /etc/muos-network-diagnostic)" = MUOS-R35S-NETWORK-P4-C07 ] || return 64
}
c12_read_config() {
    boot_config=${MUOS_BOOT_CONFIG:-/etc/default/muos-boot}
    [ -f "$boot_config" ] && [ ! -L "$boot_config" ] || return 64
    case "$(stat -c '%u:%g:%a' "$boot_config")" in 0:0:600|0:0:644) ;; *) return 64 ;; esac
    enabled=0; allow_power=0; recover_network=0; session_package=/usr/libexec/muos-session
    session_config=/etc/default/muos-session
    . "$boot_config"
    case "$enabled:$allow_power" in 0:0|0:1|1:0|1:1) ;; *) return 64 ;; esac
    case "$recover_network" in 0|1) ;; *) return 64 ;; esac
    case "$session_package:$session_config" in *..*|*[!a-zA-Z0-9_./:-]*) return 64 ;; esac
    case "$session_package" in /*) ;; *) return 64 ;; esac
    case "$session_config" in /*) ;; *) return 64 ;; esac
    export MUOS_SESSION_CONFIG=$session_config
}
c12_root_ro() { findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro; }
c12_session_quiescent() {
    # status=3 alone does not mean that asynchronous cleanup has finished.
    "$session_package/service.sh" status >/dev/null 2>&1
    status_rc=$?
    [ "$status_rc" = 3 ] || return 1
    (
        package=$session_package; base=/run/muos/session
        . "$package/control-functions.sh"
        if [ -e "$base/current" ]; then
            session_current || exit 1
            ! session_identity "$cycle" || exit 1
            [ -f "$cycle/done" ] && [ "$(cat "$cycle/result")" = 0 ] || exit 1
            [ ! -e "$cycle/ready" ] && [ ! -e "$cycle/attempted" ] || exit 1
        fi
        if [ -e "$base/lifetime.lock" ]; then
            # Opening an existing lock for reading creates no state file.
            exec 8<"$base/lifetime.lock"; flock -n 8 || exit 1
        fi
        for name in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog; do
            ! pidof "$name" >/dev/null || exit 1
        done
        for path in /run/dbus/system_bus_socket /run/muos/arborist.sock /run/muos/arborist.pid /run/muos/core/ready /run/muos/port-storage/ready /run/muos/input-ready/ready; do
            [ ! -e "$path" ] || exit 1
        done
        for path in /mnt/mmc /opt/muos/config /opt/muos/device/config /opt/muos/share/volume /etc/default/muos-ui /etc/default/muos-core; do
            ! findmnt -rn -M "$path" >/dev/null || exit 1
        done
        # Check other namespaces too: an orphan might retain the worker's RAM binds.
        # ENOENT is normal for a process that exits while this scan runs.
        for info in /proc/[0-9]*/mountinfo; do
            [ -r "$info" ] || continue
            if awk '$4 ~ /^\/(run\/)?muos\/session\/run-[0-9][0-9][0-9][0-9]\// {found=1} END {exit !found}' "$info" 2>/dev/null; then exit 1; fi
        done
    )
}
c12_record_pid() {
    pid_file=$1; identity_file=$2; expected_exe=$3
    [ -f "$pid_file" ] || return 0
    read owned_pid < "$pid_file" || return 1
    case "$owned_pid" in ''|*[!0-9]*) return 1 ;; esac
    [ "$owned_pid" -gt 1 ] || return 1
    [ -d "/proc/$owned_pid" ] || return 0
    [ "$(readlink "/proc/$owned_pid/exe")" = "$expected_exe" ] || return 1
    owned_start=$(awk '{print $22}' "/proc/$owned_pid/stat") || return 1
    printf '%s %s\n' "$owned_pid" "$owned_start" > "$identity_file"
}
c12_check_pid() {
    # An extant PID without matching metadata is foreign: never signal it.
    pid_file=$1; identity_file=$2; expected_exe=$3
    if [ ! -f "$pid_file" ]; then
        [ -f "$identity_file" ] || return 0
        read recorded_pid recorded_start < "$identity_file" || return 1
        case "$recorded_pid:$recorded_start" in *[!0-9:]*|:*|*:) return 1 ;; esac
        [ ! -d "/proc/$recorded_pid" ] || return 1
        return 0
    fi
    read owned_pid < "$pid_file" || return 1
    case "$owned_pid" in ''|*[!0-9]*) return 1 ;; esac
    [ "$owned_pid" -gt 1 ] || return 1
    [ -d "/proc/$owned_pid" ] || return 0
    [ -f "$identity_file" ] || return 1
    read recorded_pid recorded_start < "$identity_file" || return 1
    [ "$owned_pid" = "$recorded_pid" ] || return 1
    [ "$(awk '{print $22}' "/proc/$owned_pid/stat")" = "$recorded_start" ] || return 1
    [ "$(readlink "/proc/$owned_pid/exe")" = "$expected_exe" ]
}
c12_network_empty() {
    [ ! -e /run/muos/c07/ready ] || return 1
    for name in dropbear wpa_supplicant udhcpc; do ! pidof "$name" >/dev/null || return 1; done
    for name in dropbear dhcp wpa; do [ ! -e "/run/muos/c07/$name.pid" ] || return 1; done
}
c12_network_identities() {
    identity_action=$1
    for network_name in dropbear dhcp wpa; do
        case "$network_name" in dropbear) network_exe=/usr/sbin/dropbear ;; dhcp) network_exe=/bin/busybox ;; wpa) network_exe=/usr/sbin/wpa_supplicant ;; esac
        "c12_${identity_action}_pid" "/run/muos/c07/$network_name.pid" "$boot_state/network-owned/$network_name" "$network_exe" || return 1
    done
}
c12_start_network() {
    c12_network_empty || return 64
    if [ "$1" = start ]; then mkdir "$boot_state/network-owned" || return 64
    else
        [ -d "$boot_state/recovery-once" ] || return 64
        mkdir -p "$boot_state/network-owned" || return 64
    fi
    # Old identities may only be retired after the previous stop proved empty.
    for network_name in dropbear dhcp wpa; do rm -f "$boot_state/network-owned/$network_name"; done
    /usr/libexec/muos-c07-network "$1"
    network_rc=$?
    c12_network_identities record || network_rc=1
    return "$network_rc"
}
c12_dongle_present() {
    for usb_path in /sys/bus/usb/devices/*; do
        [ -r "$usb_path/idVendor" ] && [ -r "$usb_path/idProduct" ] || continue
        case "$(cat "$usb_path/idVendor"):$(cat "$usb_path/idProduct")" in 0bda:1a2b|0bda:c820) return 0 ;; esac
    done
    return 1
}
c12_native_step() {
    case "$1" in
      entropy.start)
        # C07 may already have run in this boot; importing it must not recredit seed.
        [ ! -e /run/muos/entropy ] || return 64
        mkdir "$boot_state/entropy-attempt" || return 64
        /etc/init.d/S05muos-entropy start ;;
      entropy.stop)
        # A failed refusal to start must not stop an existing C07 owner.
        [ -d "$boot_state/entropy-attempt" ] || { [ ! -e /run/muos/entropy ]; return $?; }
        /etc/init.d/S05muos-entropy stop ;;
      udev.start)
        ! pidof udevd >/dev/null || return 64
        mkdir "$boot_state/udev-owned" || return 64
        /etc/init.d/S10udev start || return 1
        main=
        for p in $(pidof udevd); do
            [ "$(awk '/^PPid:/ {print $2}' /proc/$p/status)" = 1 ] || continue
            [ -z "$main" ] || return 1
            main=$p
        done
        [ -n "$main" ] || return 1
        printf '%s\n' "$main" > "$boot_state/udev-owned/pid"
        c12_record_pid "$boot_state/udev-owned/pid" "$boot_state/udev-owned/identity" "$(readlink -f /sbin/udevd)" || return 1
        udevadm settle --timeout=5 ;;
      usb.switch) /usr/libexec/muos-c07-usb-mode ;;
      recovery.ready)
        c12_root_ro && [ -f /run/muos/entropy/stopped ] && [ ! -e /run/muos/entropy/ready ] || return 64
        key=/var/lib/muos-network/dropbear_ed25519_host_key
        [ ! -L "$key" ] && [ "$(stat -c '%u:%g:%a' "$key")" = 0:0:600 ] || return 64
        /usr/libexec/muos-rng-ready 0 ;;
      usb.wait-remove)
        printf '\033[37;40m\033[2J\033[H%s\n' 'muOS C12: USB RECONNECT NEEDED
Unplug the Wi-Fi dongle. Wait two seconds.
Reconnect it, then wait for the menu.
Do not change SD cards. Root read-only.' > /dev/tty0
        absent=0; count=0
        while [ "$count" -lt 900 ] && [ "$absent" -lt 10 ]; do
            if c12_dongle_present; then absent=0; else absent=$((absent+1)); fi
            sleep 0.1; count=$((count+1))
        done
        [ "$absent" = 10 ] ;;
      usb.wait-add)
        count=0
        while ! c12_dongle_present && [ "$count" -lt 1100 ]; do sleep 0.1; count=$((count+1)); done
        c12_dongle_present ;;
      network.start) c12_start_network start ;;
      network.recover) c12_start_network recover ;;
      network.status)
        [ -d "$boot_state/network-owned" ] || return 64
        c12_network_identities check || return 64
        /usr/libexec/muos-c07-network status ;;
      network.stop)
        if [ ! -d "$boot_state/network-owned" ]; then c12_network_empty; return $?; fi
        c12_network_identities check || return 64
        /usr/libexec/muos-c07-network stop || return 1
        # Keep metadata for idempotent stop, including evidence of a partial stop.
        c12_network_empty ;;
      udev.stop)
        if [ ! -d "$boot_state/udev-owned" ]; then ! pidof udevd >/dev/null; return $?; fi
        c12_check_pid "$boot_state/udev-owned/pid" "$boot_state/udev-owned/identity" "$(readlink -f /sbin/udevd)" || return 64
        read owned_pid < "$boot_state/udev-owned/pid" || return 1
        if [ -d "/proc/$owned_pid" ]; then
            udevadm control --stop-exec-queue || return 1
            kill -TERM "$owned_pid" || return 1
        fi
        count=0
        while pidof udevd >/dev/null && [ "$count" -lt 50 ]; do sleep 0.1; count=$((count+1)); done
        ! pidof udevd >/dev/null ;;
      root.sync) sync ;;
      root.seal) c12_root_ro || mount -o remount,ro / || return 1; c12_root_ro ;;
      power.check)
        [ "$(cat /run/muos/selection/mode)" = c12 ] || return 64
        [ ! -e /var/lib/muos-diagnostic/c12.once ] && [ ! -e "$boot_state/stopped" ] || return 64
        [ -f /run/muos/boot-diagnostic/FINAL.txt ] && [ "$(cat /run/muos/boot-diagnostic/start-rc)" = 0 ] || return 64
        grep -qx 'SESSION_QUIESCENT_RC=0 NETWORK_RC=0' /run/muos/boot-diagnostic/FINAL.txt || return 64
        c12_root_ro && c12_session_quiescent || return 1
        [ -f /run/muos/entropy/stopped ] && [ ! -e /run/muos/entropy/ready ] || return 64
        c12_native_step network.status ;;
      power.sealed)
        c12_root_ro && c12_session_quiescent && c12_network_empty || return 1
        ! pidof udevd >/dev/null || return 1
        [ -f "$boot_state/stopped" ] && [ ! -e "$boot_state/ready" ] || return 1
        [ -f /run/muos/entropy/stopped ] && [ ! -e /run/muos/entropy/ready ] ;;
      session.start) "$session_package/service.sh" start ;;
      session.status) "$session_package/service.sh" status ;;
      session.stop) "$session_package/service.sh" stop ;;
      session.quiescent) c12_session_quiescent ;;
      *) return 64 ;;
    esac
}
