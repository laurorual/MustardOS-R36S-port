#!/bin/sh
# SPDX-License-Identifier: MIT
# Unattended guard for trial boots (developer tool, never shipped).
# Installed as p3 MUOS/init/zz-trial-guard.sh and run by S98 (user init,
# settings/advanced/user_init = 1). On a trial kernel (muos_slot=trial)
# or a trial root, if wlan0 has no IPv4 address after GUARD_SECS (360),
# it logs and reboots: the next boot falls back to main (both trial
# markers are one-shot). On a main boot it does nothing.
#
#   install (host):  device.sh push port/scripts/trial-guard.sh /run &&
#     device.sh run 'cp /run/trial-guard.sh /userdata/MUOS/init/zz-trial-guard.sh &&
#       echo 1 > /opt/muos/config/settings/advanced/user_init'
#   remove: rm the file, user_init back to 0.
log=/userdata/MUOS/log/trial-guard.log
trial=
grep -q 'muos_slot=trial' /proc/cmdline && trial=kernel
/usr/libexec/muos-root-trial status 2>/dev/null | grep -q '^trial-root yes' && trial="${trial:+$trial+}root"
[ -n "$trial" ] || exit 0
(
    sleep "${GUARD_SECS:-360}"
    if ip -4 addr show wlan0 2>/dev/null | grep -q 'inet '; then
        echo "$(date '+%F %T') trial $trial: wlan0 up, guard idle" >> "$log"
        exit 0
    fi
    echo "$(date '+%F %T') trial $trial: no wlan0 address after ${GUARD_SECS:-360} s, rebooting" >> "$log"
    sync
    reboot
) > /dev/null 2>&1 &
exit 0
