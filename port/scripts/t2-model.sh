#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # device-side commands in single quotes
# M10 T2: the model switch (muos-model) on the bench, both ways, plus the
# give-up path. Uses a test DTB (a model DTB with the port DTB's battery
# node, so the RK817 gauge keeps its calibration) under the key
# m-t2-panel4; restores p1 and the undervolt choice at the end. Four
# restarts plus one for the undervolt (~10 min). Developer image only.
#   t2-model.sh TEST.DTB   (2026-11-26: build/m10/t2/test.dtb = the Panel 4
#                          model DTB + the port battery node, fdtput)
#     1. p1 model.txt "T2-Panel4\r" (case, CR): check arms, restarts; the
#        trial boots the test DTB and is promoted after 20 s; input names,
#        root, Wi-Fi, undervolt "unavailable"
#     2. model.txt "default": back to the stock DTB the same way
#     3. model.txt + a stale model-armed marker: the start gives up
#        (model.txt.failed), no trial
#     4. restore: dtb-variants.txt, the test DTB removed, undervolt re-armed
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
dev=$repo/port/scripts/device.sh
dtb=$(realpath "$1"); sha=$(sha256sum "$dtb" | cut -c1-12)
log=$repo/build/logs/m10/t2-model.log; mkdir -p "${log%/*}"; : > "$log"
say() { echo "$*" | tee -a "$log"; }
fail() { say "FAIL $*"; exit 1; }
on() { "$dev" run "$@" 2>> "$log"; }
p1() { on "mount -o remount,rw /boot && $1 && sync && mount -o remount,ro /boot"; }
# wait for a start with uptime >= $2 s whose slot is $1
wait_up() {
    sleep 60
    for _ in $(seq 1 40); do
        s=$(on 'echo "$(cut -d. -f1 /proc/uptime) $(sed -n "s/.*muos_slot=\([a-z]*\).*/\1/p" /proc/cmdline)"' || :)
        # shellcheck disable=SC2086 # two words
        set -- "$1" "$2" $s
        [ "${4:-}" = "$1" ] && [ "${3:-0}" -ge "$2" ] && return 0
        sleep 10
    done
    fail "no $1 start"
}
on "cat > /tmp/t2-model.dtb" < "$dtb"
on "cfg=/opt/muos/config/danger; echo \"\$(cat \$cfg/undervolt) \$(cat \$cfg/uv_cpu) \$(cat \$cfg/uv_gpu)\" > /userdata/MUOS/t2/model-uv.before"
p1 "cp /boot/dtb-variants.txt /boot/dtb-variants.txt.t2-before && cp /tmp/t2-model.dtb /boot/panel0-$sha.dtb && echo m-t2-panel4=panel0-$sha.dtb >> /boot/dtb-variants.txt && printf 'T2-Panel4\r\n' > /boot/model.txt"
on reboot || :
wait_up trial 35
[ "$(on /usr/libexec/muos-model status)" = t2-panel4 ] || fail "1: model status"
on 'grep -h "^N: Name" /proc/bus/input/devices' | grep -q 'GO-Super Gamepad' || fail '1: no GO-Super Gamepad'
on 'grep -h "^N: Name" /proc/bus/input/devices' | grep -q 'odroidgo3-keys' || fail '1: no odroidgo3-keys'
on 'mount' | grep -q '^/dev/mmcblk0p2 on / ' || fail '1: root not mmcblk0p2'
on '/usr/libexec/muos-network/worker status' | grep -q 'radio=up wpa=COMPLETED' || fail '1: Wi-Fi'
[ "$(on '/usr/libexec/muos-undervolt status')" = unavailable ] || fail '1: undervolt not unavailable'
say "ok   1: model t2-panel4 promoted (input, root, Wi-Fi, undervolt unavailable)"
p1 "printf 'default\n' > /boot/model.txt"
on reboot || :
wait_up trial 35
[ "$(on /usr/libexec/muos-model status)" = default ] || fail "2: not back to default"
say "ok   2: default promoted"
p1 "printf 't2-panel4\n' > /boot/model.txt"
on 'echo t2-panel4 > /userdata/MUOS/update/model-armed; sync; reboot' || :
wait_up main 25
on 'ls /boot' | grep -qx model.txt.failed || fail '3: no model.txt.failed'
say "ok   3: a failed switch gives up (model.txt.failed)"
p1 "mv -f /boot/dtb-variants.txt.t2-before /boot/dtb-variants.txt && rm -f /boot/model.txt.failed /boot/panel0-$sha.dtb"
read -r u c g < <(on 'cat /userdata/MUOS/t2/model-uv.before')
if [ "$u" = 1 ]; then
    on "cfg=/opt/muos/config/danger; echo 1 > \$cfg/undervolt; echo $c > \$cfg/uv_cpu; echo $g > \$cfg/uv_gpu; /usr/libexec/muos-undervolt arm && sync && reboot" || :
    wait_up trial 35
    [ "$(on '/usr/libexec/muos-undervolt status')" = "on $c $g" ] || fail '4: undervolt not restored'
fi
say "ok   4: restored (undervolt $u $c $g)"
say PASS
