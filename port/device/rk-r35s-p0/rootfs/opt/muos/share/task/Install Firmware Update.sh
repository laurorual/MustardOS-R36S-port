#!/bin/sh
# HELP: Install a firmware update copied to MUOS/update on the card (NAME.p2.img.gz and its .sha256). It shows its progress and restarts the device twice (about 10 minutes); your games, saves and settings stay. Needs the charger or 30 % battery.
# ICON: update
# EXECUTION_MODE: progress
# CAN_CANCEL: 0
# PROTOCOL_VERSION: 1
# SPDX-License-Identifier: MIT
# R35S port (M9 item 8): see /usr/libexec/muos-update.

. /opt/muos/script/var/base.sh
. /opt/muos/script/var/ui.sh
. /usr/share/muos-r35s/update-task.sh

TASK_BEGIN "install_firmware_update" "$(T 'Install Firmware Update')"
stage_and_restart
