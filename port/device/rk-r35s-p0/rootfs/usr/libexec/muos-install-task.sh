#!/bin/sh
# SPDX-License-Identifier: MIT
# M13 (decision 50): the first boot's "Install" on the frontend's progress
# screen (muos-frontend writes /run/muos/task_autorun when muxinstall exits
# with "install", frontend patch 0013): notes the format chosen in
# muxinstall (device storage/rom/type) for the next start, which formats
# the card before anything uses it (S89, muos-install-storage apply), then
# restarts. Not a Task Toolkit entry.

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
TASK_DETAIL "$(T 'The device restarts and prepares the card (about a minute)')"
TASK_PROGRESS 0 1
if ! /usr/libexec/muos-install-storage request "$fs" 2>/run/muos/install-storage.err; then
	TASK_ERROR "install_failed" "$(T 'The games storage could not be prepared') ($(tail -n 1 /run/muos/install-storage.err 2>/dev/null)). MUOS/log/install-storage.log"
	exit 1
fi
TASK_PROGRESS 1 1
TASK_COMPLETE "$(T 'The device restarts and prepares the card (about a minute)')"
sleep 3
reboot
exit 0
