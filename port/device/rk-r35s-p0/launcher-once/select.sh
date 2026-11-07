#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
c25_package=/usr/libexec/muos-c25
c25_state=/run/muos/c25
c25_store=/var/lib/muos-diagnostic
. "$c25_package/policy.sh"
. "$c25_package/card-guard.sh"
. "$c25_package/native.sh"
# Refuse SSH invocation before creating RAM state or inspecting any marker.
c25_init_child && c25_media && c25_root_mode rw && c25_foundation || exit 64
[ ! -e "$c25_state" ] && [ ! -L "$c25_state" ] || exit 64
mkdir -p /run/muos && mkdir -m 700 "$c25_state" || exit 64
if c25_select; then rc=0; else rc=$?; fi
printf '%s\n' "$rc" > "$c25_state/select.result"
exit "$rc"
