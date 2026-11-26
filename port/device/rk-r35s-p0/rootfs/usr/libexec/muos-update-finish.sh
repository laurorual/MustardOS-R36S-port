#!/bin/sh
# SPDX-License-Identifier: MIT
# M9 (v1.0.0): the last step of a firmware update, run on the frontend's
# progress screen as soon as the update's trial boot starts the frontend
# (muos-frontend writes /run/muos/task_autorun, frontend patch 0013): p2 is
# written with its progress (muos-update finish), then the device restarts.
# Not a Task Toolkit entry: it only runs on that boot.

. /opt/muos/script/var/base.sh
. /opt/muos/script/var/ui.sh

TASK_BEGIN "finish_firmware_update" "Finishing Firmware Update"
TASK_STATUS "Installing the update: do not power off"
TASK_DETAIL "About 5 minutes. The device restarts by itself when it is done."
TASK_PROGRESS 0 18
rm -f /run/muos/update-finished
/usr/libexec/muos-update finish 2> /run/muos/update-finish.err | while read -r _ n m; do
	TASK_PROGRESS "$n" "$m"
done
if [ ! -e /run/muos/update-finished ]; then
	TASK_ERROR "update_failed" "The update could not be installed ($(tail -n 1 /run/muos/update-finish.err 2>/dev/null)). See MUOS/update/update.log."
	exit 1
fi
TASK_COMPLETE "Update installed: restarting"
sleep 3
reboot
exit 0
