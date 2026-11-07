#!/bin/sh
# SPDX-License-Identifier: MIT
set -u
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
boot_package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 64
boot_state=/run/muos/boot
. "$boot_package/native-functions.sh"
c12_guard || exit 64
c12_read_config || exit 64
c12_native_step "${1:-}"
