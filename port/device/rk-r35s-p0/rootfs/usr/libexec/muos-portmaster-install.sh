#!/bin/sh
# SPDX-License-Identifier: MIT
# M11: installs PortMaster on the frontend's progress screen (task
# autorun, as muos-update-finish.sh) when Applications -> PortMaster finds
# it missing (muos-portmaster run). Not a Task Toolkit entry.

. /opt/muos/script/var/base.sh
. /opt/muos/script/var/ui.sh
# T TEXT: TEXT in the menu's language (/usr/share/muos-r35s/task-text)
T() {
	t=$(awk -F '\t' -v k="$1" '$1 == k { print $2; exit }' \
		"/usr/share/muos-r35s/task-text/$(cat /opt/muos/config/settings/general/language 2>/dev/null).txt" 2>/dev/null)
	printf '%s' "${t:-$1}"
}

TASK_BEGIN "install_portmaster" "$(T 'Installing PortMaster')"
TASK_STATUS "$(T 'Downloading PortMaster (about 25 MB)')"
TASK_DETAIL "$(T 'Needs Wi-Fi, or muos.portmaster.zip in MUOS/update')"
TASK_PROGRESS 0 4
/usr/libexec/muos-portmaster install 2> /run/muos/portmaster-install.err | while read -r _ n m; do
	TASK_PROGRESS "$n" "$m"
done
if [ "$(/usr/libexec/muos-portmaster status)" = missing ]; then
	TASK_ERROR "portmaster_failed" "$(T 'PortMaster could not be installed') ($(tail -n 1 /run/muos/portmaster-install.err 2>/dev/null | sed 's/^muos-portmaster: //'))"
	exit 1
fi
TASK_STATUS "$(T 'PortMaster installed: open it again from Applications')"
TASK_DETAIL ""
TASK_PROGRESS 4 4
sleep 2
