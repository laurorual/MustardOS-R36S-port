#!/bin/sh
# SPDX-License-Identifier: MIT
# M11: muOS's compatibility loader for third-party scripts (PortMaster's
# control.txt sources it for GET_VAR). Upstream's func.sh loads the whole
# script/var set; the port runs its own launchers, so this one offers the
# variable and log helpers (upstream config.sh and log.sh, shipped).
[ -n "${MUOS_FUNC_LOADED-}" ] && return 0
MUOS_FUNC_LOADED=1
. /opt/muos/script/var/config.sh
. /opt/muos/script/var/log.sh
