#!/bin/sh
# HELP: Install a firmware update copied to MUOS/update on the card (NAME.p2.img.gz and its .sha256). It shows its progress and restarts the device twice (about 10 minutes); your games, saves and settings stay. Needs the charger or 30 % battery.
# ICON: system
# EXECUTION_MODE: progress
# CAN_CANCEL: 0
# PROTOCOL_VERSION: 1
# SPDX-License-Identifier: MIT
# R35S port (M9 item 8): see /usr/libexec/muos-update.

. /opt/muos/script/var/base.sh
. /opt/muos/script/var/ui.sh
# T TEXT: TEXT in the menu's language (/usr/share/muos-r35s/task-text,
# port/scripts/task-texts.py), else as given (English)
T() {
	t=$(awk -F '\t' -v k="$1" '$1 == k { print $2; exit }' \
		"/usr/share/muos-r35s/task-text/$(cat /opt/muos/config/settings/general/language 2>/dev/null).txt" 2>/dev/null)
	printf '%s' "${t:-$1}"
}

TASK_BEGIN "install_firmware_update" "$(T 'Install Firmware Update')"
TASK_STATUS "$(T 'Checking and unpacking the update')"
TASK_DETAIL "$(T 'Keep the device on until the menu returns')"
size=$(blockdev --getsize64 "$(/usr/libexec/muos-boot-disk)p2" 2>/dev/null || echo 1073741824)
/usr/libexec/muos-update stage > /run/muos/update-stage.out 2>&1 &
pid=$!
while kill -0 "$pid" 2>/dev/null; do
	n=$(stat -c %s /userdata/MUOS/trial/rootfs.img.tmp 2>/dev/null || echo 0)
	TASK_PROGRESS "$((n / 1048576))" "$((size / 1048576))"
	sleep 2
done
if ! wait "$pid"; then
	TASK_ERROR "stage_failed" "$(T 'Not installed'): $(tail -n 1 /run/muos/update-stage.out)"
	exit 1
fi
TASK_PROGRESS 1 1
TASK_COMPLETE "$(T 'Update ready: restarting')"
sleep 2
reboot
exit 0
