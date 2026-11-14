#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M4b): Wi-Fi robustness on the device (developer image, SSH over Wi-Fi).
#   services  menu-started SSH/SFTP (web/sshd, web/sftp via service.sh apply,
#             run inside a stand-in UI process group) must survive the group
#             being killed, as S99muos-ui stop does; toggles restored after
#   hotplug   software unplug (usb 1-1/remove): the udev hook must stop the
#             network service and clear the radio state; USB host rebind
#             (the dongle returns): the hook must restart it, Wi-Fi back
#   all       both (default)
# The hotplug part runs detached on the device (SSH drops while the dongle
# is gone) and logs to p3 MUOS/log/t2-wifi-robust.log. Real replugs and
# sleep/wake (dongle power cut, CD-ROM-mode settle) are t2-sleep-cycle.sh and
# the T3 checklist.
set -u
cd "$(dirname "$0")" || exit 1
dev=./device.sh
r() { "$dev" run "$@"; }
what=${1:-all}
rc=0

services() {
    out=$(r 'C=/opt/muos/config/web; W=/usr/libexec/muos-network/worker
s0=$(cat $C/sshd) f0=$(cat $C/sftp); echo 1 > $C/sshd; echo 1 > $C/sftp
setsid sh -c "/opt/muos/script/web/service.sh apply; sleep 60; true" < /dev/null > /dev/null 2>&1 & g=$!
sleep 3; up0=$($W status | grep -c -E "^(sshd|sftp)=up")
kill -TERM -$g; sleep 2
alive=$(kill -0 $g 2>/dev/null && echo yes || echo no); up1=$($W status | grep -c -E "^(sshd|sftp)=up")
echo $s0 > $C/sshd; echo $f0 > $C/sftp; $W service all
echo "before=$up0 group_alive=$alive after=$up1"')
    echo "services: $out"
    case "$out" in *'before=2 group_alive=no after=2'*) echo 'PASS services' ;; *) echo 'FAIL services'; rc=1 ;; esac
}

hotplug() {
    r 'cat > /run/t2-hotplug.sh' <<'EOF'
o=/userdata/MUOS/log/t2-wifi-robust.log; N=/run/muos/network
st() { echo "$(cut -d' ' -f1 /proc/uptime) $1 usb=[$(cat /sys/bus/usb/devices/1-1/idProduct 2>/dev/null)] flags=[$(cd $N && ls radio usb-done ready 2>/dev/null | tr '\n' ' ')] addr=$(cat $N/address 2>/dev/null)" >> $o; }
: > $o; : > /run/muos-hotplug.log
st start
echo 1 > /sys/bus/usb/devices/1-1/remove
sleep 8; st removed
echo ff300000.usb > /sys/bus/platform/drivers/dwc2/unbind; sleep 2
echo ff300000.usb > /sys/bus/platform/drivers/dwc2/bind
i=0; while [ $i -lt 90 ] && [ ! -s $N/address ]; do sleep 1; i=$((i+1)); done
st readded; echo "back_after=${i}s" >> $o
sed 's/^/HP /' /run/muos-hotplug.log >> $o; echo done >> $o; sync
EOF
    r '(setsid sh /run/t2-hotplug.sh < /dev/null > /dev/null 2>&1 &)'
    sleep 30
    "$dev" wait 180 > /dev/null || { echo 'FAIL hotplug: no SSH 3 min after the re-add'; rc=1; return; }
    n=0; until r 'grep -qx done /userdata/MUOS/log/t2-wifi-robust.log' 2>/dev/null || [ "$n" -ge 12 ]; do sleep 5; n=$((n+1)); done
    log=$(r 'cat /userdata/MUOS/log/t2-wifi-robust.log')
    printf '%s\n' "$log"
    if printf '%s\n' "$log" | grep -q '^[0-9.]* removed usb=\[\] flags=\[\] addr=$' &&
       printf '%s\n' "$log" | grep -q 'hotplug remove: dongle gone' &&
       printf '%s\n' "$log" | grep -q 'hotplug add: restart' &&
       printf '%s\n' "$log" | grep -q '^[0-9.]* readded usb=\[c820\] .*addr=[0-9]'; then
        echo 'PASS hotplug'
    else
        echo 'FAIL hotplug'; rc=1
    fi
}

case "$what" in
    services) services ;;
    hotplug) hotplug ;;
    all) services; hotplug ;;
    *) echo 'usage: t2-wifi-robust.sh [services|hotplug|all]' >&2; exit 2 ;;
esac
exit "$rc"
