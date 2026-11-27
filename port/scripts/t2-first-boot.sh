#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # device-side commands in single quotes
# T2 (M13): the first boot's Install on the bench, after the user flashed
# test128 with a developer image made with MUOS_FIRST_BOOT=1 (first boot on,
# SSH kept; flash-card.sh WITHOUT --grow; back up p3 first: card-p3.sh).
# The install runs as the progress screen runs it (muos-install-storage
# request, restart; S89 applies it); the user checks the screens in the T3.
#   t2-first-boot.sh pre          fresh card: factory_reset 1, the menu in the
#                                 installer, p3 not grown
#   t2-first-boot.sh install FS   exfat|vfat|ext4: back into the first boot
#                                 if needed, a language and zone set, request,
#                                 restart; then p3's format and size, the
#                                 settings kept, the start (storage, seeds,
#                                 ScummVM data, time zone link, menu)
# Order for one flash: pre, install exfat, install vfat, install ext4 (each
# formats the card again: it has no games). Log build/logs/m13/t2-first-boot.log.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
dev=$repo/port/scripts/device.sh
log=$repo/build/logs/m13/t2-first-boot.log; mkdir -p "${log%/*}"
say() { echo "$*" | tee -a "$log"; }
fail() { say "FAIL $*"; exit 1; }
on() { "$dev" run "$@" 2>> "$log"; }
wait_up() { # a new start (uptime >= $1 s)
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
    say "PASS pre" ;;
install)
    fs=${2:?exfat|vfat|ext4}
    if [ "$(on 'cat /opt/muos/config/boot/factory_reset')" != 1 ]; then
        on "echo 1 > /opt/muos/config/boot/factory_reset; sync"
        "$dev" reboot >> "$log" 2>&1 || :
        wait_up 30
    fi
    # what the first boot's screens set, to find again after the format
    on 'echo "Portuguese (BR)" > /opt/muos/config/settings/general/language
        printf /usr/share/zoneinfo/America/Sao_Paulo > /opt/muos/config/localtime; sync'
    say "install $fs: before [$(layout)] $(on 'findmnt -rn -o FSTYPE -M /userdata')"
    on "/usr/libexec/muos-install-storage request $fs" || fail "request $fs"
    "$dev" reboot >> "$log" 2>&1 || :
    wait_up 30
    sleep 30 # the 20 s promotes and the menu
    say "install $fs: after [$(layout)]"
    r=$(on 'echo "fs=$(findmnt -rn -o FSTYPE -M /userdata) mmc=$([ "$(stat -c %d:%i /mnt/mmc)" = "$(stat -c %d:%i /userdata)" ] && echo p3 || echo other) factory=$(cat /opt/muos/config/boot/factory_reset) lang=$(tr " " _ < /opt/muos/config/settings/general/language) zone=$(readlink /run/muos/localtime) tz=$(date +%Z) roms=$(ls /mnt/mmc/ROMS | wc -l) themes=$(ls /mnt/mmc/MUOS/theme | wc -l) storage=$([ -f /run/muos/storage/mount_ready ] && echo ready || echo no) scummvm=$(ls /mnt/mmc/MUOS/bios/scummvm/extra 2>/dev/null | wc -l) menu=$(cat /opt/muos/config/system/foreground_process)"')
    say "install $fs: $r"
    say "install $fs: log $(on 'tail -n 1 /userdata/MUOS/log/install-storage.log')"
    case $r in "fs=$fs mmc=p3 factory=0 lang=Portuguese_(BR) zone=/usr/share/zoneinfo/America/Sao_Paulo tz=-03 roms="[1-9]*" themes="[1-9]*" storage=ready scummvm="[1-9]*" menu=muxfrontend") ;; *) fail "after install $fs" ;; esac
    say "PASS install $fs" ;;
*) sed -n '4,17p' "$0"; exit 2 ;;
esac
