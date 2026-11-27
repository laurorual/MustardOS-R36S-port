# SPDX-License-Identifier: MIT
# shellcheck shell=sh
# v1.1.1: shared by the Task Toolkit update tasks (Install Firmware Update,
# Check for Online Update); sourced after base.sh and ui.sh.

# T TEXT: TEXT in the menu's language (/usr/share/muos-r35s/task-text,
# port/scripts/task-texts.py), else as given (English)
T() {
	t=$(awk -F '\t' -v k="$1" '$1 == k { print $2; exit }' \
		"/usr/share/muos-r35s/task-text/$(cat /opt/muos/config/settings/general/language 2>/dev/null).txt" 2>/dev/null)
	printf '%s' "${t:-$1}"
}

# stage_and_restart: unpack and check the update in MUOS/update with its
# progress (muos-update stage), then restart into it; on failure the task
# ends with the reason.
stage_and_restart() {
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
}
