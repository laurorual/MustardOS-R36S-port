#!/bin/sh
# SPDX-License-Identifier: MIT
# M13 (decision 50): the first boot's "Install" on the frontend's progress
# screen (muos-frontend writes /run/muos/task_autorun when muxinstall exits
# with "install", frontend patch 0013): prepares the games storage in the
# format chosen in muxinstall (device storage/rom/type, muos-install-storage),
# then the device restarts into the menu. Not a Task Toolkit entry.

. /opt/muos/script/var/base.sh
. /opt/muos/script/var/ui.sh
# T TEXT: TEXT in the menu's language (/usr/share/muos-r35s/task-text,
# port/scripts/task-texts.py), else as given (English)
T() {
	t=$(awk -F '\t' -v k="$1" '$1 == k { print $2; exit }' \
		"/usr/share/muos-r35s/task-text/$(cat /opt/muos/config/settings/general/language 2>/dev/null).txt" 2>/dev/null)
	printf '%s' "${t:-$1}"
}

fs=$(cat /opt/muos/device/config/storage/rom/type 2>/dev/null)
case "$fs" in exfat | vfat | ext4) ;; *) fs=exfat ;; esac
TASK_BEGIN "install_storage" "$(T 'Installing MustardOS')"
TASK_STATUS "$(T 'Preparing the games storage: do not power off')"
TASK_DETAIL "$(T 'Less than a minute, then it restarts')"
TASK_PROGRESS 0 6
/usr/libexec/muos-install-storage "$fs" 2>/run/muos/install-storage.err | while read -r _ n m; do
	TASK_PROGRESS "$n" "$m"
done
if [ "$(cat /opt/muos/config/boot/factory_reset 2>/dev/null)" != 0 ]; then
	TASK_ERROR "install_failed" "$(T 'The games storage could not be prepared') ($(tail -n 1 /run/muos/install-storage.err 2>/dev/null)). MUOS/log/install-storage.log"
	exit 1
fi
TASK_COMPLETE "$(T 'MustardOS is installed: restarting')"
sleep 3
reboot
exit 0
