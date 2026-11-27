#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # device-side commands in single quotes
# T2 (M13): the first boot's Install on the bench, after the user flashed
# test128 with a developer image made with MUOS_FIRST_BOOT=1 (first boot on,
# SSH kept; flash-card.sh WITHOUT --grow; back up p3 first: card-p3.sh).
# The install runs as muos-frontend would run it (muos-install-storage, then a
# restart); the user checks the screens themselves in the T3.
#   t2-first-boot.sh pre          fresh card: factory_reset 1, the menu in the
#                                 installer, p3 not grown, three partitions
#   t2-first-boot.sh install FS   exfat|vfat|ext4: factory_reset 1, install,
#                                 restart, then check the layout and the start
# Order for one flash: pre, install exfat, install vfat (p4 reformatted),
# install ext4 (p4 removed, p3 to the end). Log build/logs/m13/t2-first-boot.log.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
dev=$repo/port/scripts/device.sh
log=$repo/build/logs/m13/t2-first-boot.log; mkdir -p "${log%/*}"
say() { echo "$*" | tee -a "$log"; }
fail() { say "FAIL $*"; exit 1; }
on() { "$dev" run "$@" 2>> "$log"; }
wait_up() { # a new start with the menu up (uptime >= $1 s)
    sleep 60
    for _ in $(seq 1 40); do
        u=$(on 'cut -d. -f1 /proc/uptime' || :)
        [ -n "$u" ] && [ "$u" -ge "$1" ] && return 0
        sleep 10
    done
    fail "the device did not come back"
}
layout() { on 'd=$(/usr/libexec/muos-boot-disk); sfdisk -d $d | sed -n "s|^${d}p\([0-9]\) : start= *\([0-9]*\), size= *\([0-9]*\), type=\([0-9a-f]*\).*|p\1=\2+\3:\4|p" | tr "\n" " "'; }
case "${1:-}" in
pre)
    s=$(on 'echo "factory=$(cat /opt/muos/config/boot/factory_reset) action=$(head -n1 /run/muos/action 2>/dev/null) installer=$(grep -c "first boot: installer" /opt/muos/log/frontend-loop.log)"')
    say "pre: $s layout=[$(layout)]"
    case $s in "factory=1 action=installer installer="[1-9]*) ;; *) fail "not in the first boot" ;; esac
    [ "$(layout | wc -w)" = 3 ] || fail "not three partitions"
    say "PASS pre" ;;
install)
    fs=${2:?exfat|vfat|ext4}
    if [ "$(on 'cat /opt/muos/config/boot/factory_reset')" != 1 ]; then
        # back into the first boot: S89 leaves p4 unmounted for the install
        on "echo 1 > /opt/muos/config/boot/factory_reset; sync"
        "$dev" reboot >> "$log" 2>&1 || :
        wait_up 30
    fi
    on '! findmnt -rn -M /mnt/content > /dev/null' || fail "p4 mounted during the first boot"
    on "echo $fs > /opt/muos/device/config/storage/rom/type"
    say "install $fs: before [$(layout)]"
    on "/usr/libexec/muos-install-storage $fs" > "${log%.log}-$fs.out" || { tail -n 3 "${log%.log}-$fs.out" | tee -a "$log"; fail "install $fs"; }
    [ "$(on 'cat /opt/muos/config/boot/factory_reset')" = 0 ] || fail "factory_reset still set"
    "$dev" reboot >> "$log" 2>&1 || :
    wait_up 30
    sleep 30 # the 20 s promotes and the menu
    say "install $fs: after [$(layout)]"
    r=$(on 'c=$(findmnt -rn -o FSTYPE -M /mnt/content 2>/dev/null || echo none)
        m=$(stat -c %d:%i /mnt/mmc); p=$(stat -c %d:%i /mnt/content 2>/dev/null || echo -); u=$(stat -c %d:%i /userdata)
        root=p3; [ "$m" = "$p" ] && root=p4; [ "$m" = "$u" ] || [ "$root" = p4 ] || root=other
        echo "content=$c root=$root roms=$(ls /mnt/mmc/ROMS | wc -l) themes=$(ls /mnt/mmc/MUOS/theme | wc -l) storage=$([ -f /run/muos/storage/mount_ready ] && echo ready || echo no) scummvm=$(ls /mnt/mmc/MUOS/bios/scummvm/extra 2>/dev/null | wc -l) factory=$(cat /opt/muos/config/boot/factory_reset) menu=$(cat /opt/muos/config/system/foreground_process)"')
    say "install $fs: $r"
    case $fs in exfat|vfat) want="content=$fs root=p4" ;; ext4) want="content=none root=p3" ;; esac
    case $r in "$want roms="[1-9]*" themes="[1-9]*" storage=ready scummvm="[1-9]*" factory=0 menu=muxfrontend") ;; *) fail "after install $fs" ;; esac
    say "PASS install $fs" ;;
*) sed -n '4,15p' "$0"; exit 2 ;;
esac
