#!/bin/sh
# SPDX-License-Identifier: MIT
# One trial before C07 network.start. With no token, preserve the original path.
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
base=/usr/libexec/muos-c15
token=/var/lib/muos-diagnostic/c15.once
if [ ! -e "$token" ] && [ ! -L "$token" ];then exec "$base/usb-mode.original";fi
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard || exit 64
[ "$(cat /run/muos/selection/mode)" = c07 ] || exit 64
# C07 owns this initial RW window. Never remount root to consume a late token.
! c12_root_ro || exit 64
[ ! -L "$token" ] && [ "$(stat -c '%u:%g:%a:%h:%s' "$token")" = 0:0:600:1:14 ] || exit 64
[ "$(cat "$token")" = MUOS-C15-ONCE ] || exit 64
[ ! -e /var/lib/muos-diagnostic/c15.used ] && [ ! -L /var/lib/muos-diagnostic/c15.used ] || exit 64
mv "$token" /var/lib/muos-diagnostic/c15.used && sync || exit 1
"$base/usb-mode.original" || exit $?
"$base/controller.sh"
