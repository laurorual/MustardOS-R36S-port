#!/bin/sh
# SPDX-License-Identifier: MIT
# One observation around the original USB helper; no recovery operation is added.
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
base=/usr/libexec/muos-c16
token=/var/lib/muos-diagnostic/c16.once
if [ ! -e "$token" ] && [ ! -L "$token" ];then exec "$base/usb-mode.original";fi
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard || exit 64
[ "$(cat /run/muos/selection/mode)" = c07 ] || exit 64
! c12_root_ro || exit 64
[ ! -L "$token" ] && [ "$(stat -c '%u:%g:%a:%h:%s' "$token")" = 0:0:600:1:14 ] || exit 64
[ "$(cat "$token")" = MUOS-C16-ONCE ] || exit 64
[ ! -e /var/lib/muos-diagnostic/c16.used ] && [ ! -L /var/lib/muos-diagnostic/c16.used ] || exit 64
mv "$token" /var/lib/muos-diagnostic/c16.used && sync || exit 1
state=/run/muos/c07/control-probe
mkdir -m 700 "$state" || exit 64
/usr/libexec/muos-run-bounded 10 "$base/usb-control-probe" retained-pre > "$state/before.txt" 2> "$state/before.stderr"
printf 'C16_PRE_PROBE_RC=%s\n' "$?"
cat "$state/before.txt"
"$base/usb-mode.original"
original_rc=$?
printf 'C16_ORIGINAL_USB_RC=%s\n' "$original_rc"
/usr/libexec/muos-run-bounded 10 "$base/usb-control-probe" retained-post > "$state/after.txt" 2> "$state/after.stderr"
printf 'C16_POST_PROBE_RC=%s\n' "$?"
cat "$state/after.txt"
exit "$original_rc"
