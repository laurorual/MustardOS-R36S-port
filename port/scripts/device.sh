#!/usr/bin/env bash
# shellcheck disable=SC2016
# SPDX-License-Identifier: MIT
# Repeatable SSH access to the R35S test device (see docs/STATUS.md).
#
#   device.sh find [ip]        locate the device (DHCP IP changes) by host key
#   device.sh run CMD...       run a shell command on the device (stdin passed)
#   device.sh sh               interactive shell
#   device.sh push SRC DST     copy a local file/dir into device dir DST (tar)
#   device.sh pull SRC DST     copy a device file/dir into local dir DST (tar)
#   device.sh id               boot id, uptime, root/p3 mounts, UI state
#   device.sh wait [secs]      wait until SSH answers again (rescans the LAN)
#   device.sh reboot|poweroff  request it through init (rcK runs), then for
#                              reboot wait for the new boot id
#   device.sh capture DIR      stop UI/p3 services, capture the card for
#                              make-recovery-image.sh (reboot afterwards)
#
# Identity is the pinned host-key fingerprint, never the IP. Every call is
# appended to build/logs/device.log with its exit code.
set -euo pipefail

repo=$(cd "$(dirname "$0")/../.." && pwd)
private=${MUOS_DEVICE_PRIVATE:-$repo/build/phase4/private}
key=$private/c07-client
fingerprint=${MUOS_DEVICE_FP:-SHA256:fDW+/iNaWgqPwqBtO/ESuKPSQHvYN1PSo2RHfilOxK0}
port=2222
state=$repo/build/device
logs=$repo/build/logs
mkdir -p "$state" "$logs"
known=$state/known_hosts
ipfile=$state/ip

log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >> "$logs/device.log"; }
die() { echo "device.sh: $*" >&2; log "ERROR $*"; exit 1; }

# Print the ed25519 host key line of ip:port if its fingerprint is ours.
probe() {
    local ip=$1 line fp
    line=$(ssh-keyscan -p "$port" -t ed25519 -T 3 "$ip" 2>/dev/null | grep -v "^#" | head -n1) || return 1
    [ -n "$line" ] || return 1
    fp=$(printf '%s\n' "$line" | ssh-keygen -lf - 2>/dev/null | awk '{print $2}')
    [ "$fp" = "$fingerprint" ] || return 1
    printf '%s\n' "$line"
}

adopt() {
    local ip=$1 line
    line=$(probe "$ip") || return 1
    printf '%s\n' "$line" > "$known"
    printf '%s\n' "$ip" > "$ipfile"
    echo "$ip"
}

scan() {
    local net h ip
    net=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<NF;i++) if($i=="src") print $(i+1)}' | cut -d. -f1-3)
    [ -n "$net" ] || die "no IPv4 route"
    for h in $(seq 2 254); do
        ( timeout 1 bash -c "exec 3<>/dev/tcp/$net.$h/$port" 2>/dev/null && echo "$net.$h" ) &
    done | while read -r ip; do
        adopt "$ip" && break
    done
    wait 2>/dev/null || :
}

find_device() {
    local ip
    if [ -n "${1:-}" ]; then adopt "$1" && return 0; fi
    if [ -s "$ipfile" ] && ip=$(cat "$ipfile") && adopt "$ip" >/dev/null; then echo "$ip"; return 0; fi
    ip=$(scan | head -n1)
    [ -n "$ip" ] || return 1
    echo "$ip"
}

target() {
    local ip
    ip=$(find_device) || die "device not found (fingerprint $fingerprint)"
    printf '%s\n' "$ip"
}

ssh_dev() {
    local ip=$1; shift
    ssh -p "$port" -i "$key" -oIdentitiesOnly=yes -oBatchMode=yes \
        -oStrictHostKeyChecking=yes -oUserKnownHostsFile="$known" \
        -oConnectTimeout=8 -oServerAliveInterval=5 -oServerAliveCountMax=3 \
        "root@$ip" "$@"
}

boot_id() { ssh_dev "$1" 'cat /proc/sys/kernel/random/boot_id' 2>/dev/null; }

wait_up() {
    local deadline=$(( $(date +%s) + ${1:-180} )) ip
    rm -f "$ipfile.stale"
    while [ "$(date +%s)" -lt "$deadline" ]; do
        if ip=$(find_device 2>/dev/null) && boot_id "$ip" >/dev/null; then
            echo "$ip"; return 0
        fi
        sleep 5
    done
    return 1
}

cmd=${1:-}; [ $# -eq 0 ] || shift
case "$cmd" in
 find)
    ip=$(find_device "${1:-}") || die "device not found"
    log "find $ip"; echo "$ip" ;;
 run)
    [ $# -gt 0 ] || die "run needs a command"
    ip=$(target); rc=0
    ssh_dev "$ip" "$*" || rc=$?
    log "run rc=$rc $*"; exit "$rc" ;;
 sh)
    ip=$(target)
    ssh -t -p "$port" -i "$key" -oIdentitiesOnly=yes -oStrictHostKeyChecking=yes \
        -oUserKnownHostsFile="$known" "root@$ip" ;;
 push)
    [ $# -eq 2 ] || die "push SRC DST"
    ip=$(target); src=$1; dst=$2
    tar -C "$(dirname "$src")" -cf - "$(basename "$src")" |
        ssh_dev "$ip" "mkdir -p '$dst' && tar -xf - -C '$dst'"
    log "push $src -> $dst" ;;
 pull)
    [ $# -eq 2 ] || die "pull SRC DST"
    ip=$(target); src=$1; dst=$2; mkdir -p "$dst"
    ssh_dev "$ip" "tar -C '$(dirname "$src")' -cf - '$(basename "$src")'" | tar -xf - -C "$dst"
    log "pull $src -> $dst" ;;
 id)
    ip=$(target)
    ssh_dev "$ip" 'echo "boot_id=$(cat /proc/sys/kernel/random/boot_id)"; echo "uptime=$(cut -d" " -f1 /proc/uptime)";
        awk '\''$2=="/"||$2=="/userdata"||$2=="/mnt/mmc"||$2=="/boot"{print "mount="$1","$2","$4}'\'' /proc/mounts;
        pgrep -f /opt/muos/frontend/muxfrontend >/dev/null && echo ui=running || echo ui=stopped'
    echo "ip=$ip" ;;
 wait)
    ip=$(wait_up "${1:-180}") || die "device did not come back"
    log "up $ip"; echo "$ip" ;;
 reboot|poweroff)
    ip=$(target); old=$(boot_id "$ip") || die "no boot id"
    ssh_dev "$ip" "nohup sh -c 'sleep 1; $cmd' >/dev/null 2>&1 &" || :
    log "$cmd requested boot_id=$old"
    if [ "$cmd" = poweroff ]; then echo "poweroff requested"; exit 0; fi
    sleep 20
    deadline=$(( $(date +%s) + ${1:-240} ))
    while [ "$(date +%s)" -lt "$deadline" ]; do
        if ip=$(find_device 2>/dev/null) && new=$(boot_id "$ip") && [ "$new" != "$old" ]; then
            log "rebooted $ip boot_id=$new"; echo "rebooted ip=$ip boot_id=$new"; exit 0
        fi
        sleep 5
    done
    die "no new boot id after reboot" ;;
 capture)
    # Consistent card capture for make-recovery-image.sh: 0..640 MiB raw
    # (bootloader, p1, p2), a tar of p3, the p3 superblock and the table.
    [ $# -eq 1 ] || die "capture OUTDIR"
    out=$1; mkdir -p "$out"; ip=$(target)
    # Quiesce the UI and p3 users (network/SSH stay up), then require a
    # consistent card: root ro, p1 not rw, p3 unmounted. Reboot afterwards.
    ssh_dev "$ip" 'cd /; export HOME=/root XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
        export PATH=/opt/muos/frontend:/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin LD_LIBRARY_PATH=/opt/muos/frontend/lib
        for s in S99muos-ui S97muos-battery S96muos-input-ready S95muos-core S91muos-runtime S90muos-storage S89muos-data; do
            [ -x /etc/init.d/$s ] && /etc/init.d/$s stop >/dev/null 2>&1; done; sync' || :
    ssh_dev "$ip" 'set -e
        grep -q "^/dev/root / ext4 ro," /proc/mounts
        ! grep -q "^/dev/mmcblk0p1 [^ ]* vfat rw" /proc/mounts
        ! grep -q "^/dev/mmcblk0p3 " /proc/mounts' || die "need root ro, p1 not rw and p3 unmounted"
    ssh_dev "$ip" 'sfdisk -d /dev/mmcblk0' > "$out/table.sfdisk"
    ssh_dev "$ip" 'dd if=/dev/mmcblk0p3 bs=1M count=4 2>/dev/null' > "$out/p3-head.img"
    ssh_dev "$ip" 'dd if=/dev/mmcblk0 bs=1M count=640 2>/dev/null | gzip -1' > "$out/prefix.img.gz"
    remote=$(ssh_dev "$ip" 'dd if=/dev/mmcblk0 bs=1M count=640 2>/dev/null | sha256sum' | cut -d' ' -f1)
    local_sum=$(gzip -dc "$out/prefix.img.gz" | sha256sum | cut -d' ' -f1)
    [ "$remote" = "$local_sum" ] || die "prefix hash mismatch $remote != $local_sum"
    echo "$local_sum  prefix.img" > "$out/prefix.sha256"
    ssh_dev "$ip" 'set -e; d=$(mktemp -d); mount -o ro,noload /dev/mmcblk0p3 "$d"
        tar -C "$d" --exclude=./lost+found -cf - .; umount "$d"; rmdir "$d"' > "$out/p3.tar"
    tar -tf "$out/p3.tar" > /dev/null
    log "capture $out prefix=$local_sum"
    echo "captured $out prefix_sha256=$local_sum" ;;
 *) sed -n '3,15p' "$0"; exit 2 ;;
esac
