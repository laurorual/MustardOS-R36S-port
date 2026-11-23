#!/bin/sh
# HELP: Install a firmware update copied to MUOS/update on the card (NAME.p2.img.gz and its .sha256). The device restarts once; your games, saves and settings stay.
# ICON: system
# EXECUTION_MODE: progress
# CAN_CANCEL: 0
# PROTOCOL_VERSION: 1
# SPDX-License-Identifier: MIT
# R35S port (M9 item 8): see /usr/libexec/muos-update.

. /opt/muos/script/var/base.sh
. /opt/muos/script/var/ui.sh

TASK_BEGIN "install_firmware_update" "Install Firmware Update"
TASK_STATUS "Checking and unpacking the update"
if ! msg=$(/usr/libexec/muos-update stage 2>&1); then
	TASK_ERROR "${msg##*
}"
	exit 1
fi
TASK_COMPLETE "Update ready: restarting"
sleep 2
reboot
exit 0
