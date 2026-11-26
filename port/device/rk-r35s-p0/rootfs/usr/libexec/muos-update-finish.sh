#!/bin/sh
# SPDX-License-Identifier: MIT
# M9 (v1.0.0): the last step of a firmware update, run on the frontend's
# progress screen as soon as the update's trial boot starts the frontend
# (muos-frontend writes /run/muos/task_autorun, frontend patch 0013): p2 is
# written with its progress (muos-update finish), then the device restarts.
# Not a Task Toolkit entry: it only runs on that boot.

. /opt/muos/script/var/base.sh
. /opt/muos/script/var/ui.sh
# the task texts in Português (Brasil) when the menu is in it, else English
T() { if [ "$(cat /opt/muos/config/settings/general/language 2>/dev/null)" = "Portuguese (BR)" ]; then printf '%s' "$2"; else printf '%s' "$1"; fi; }

TASK_BEGIN "finish_firmware_update" "$(T 'Finishing Firmware Update' 'Concluindo a atualização do sistema')"
TASK_STATUS "$(T 'Installing the update: do not power off' 'Instalando a atualização: não desligue')"
TASK_DETAIL "$(T 'About 5 minutes, then it restarts' 'Cerca de 5 minutos; depois reinicia')"
TASK_PROGRESS 0 18
rm -f /run/muos/update-finished
/usr/libexec/muos-update finish 2> /run/muos/update-finish.err | while read -r _ n m; do
	TASK_PROGRESS "$n" "$m"
done
if [ ! -e /run/muos/update-finished ]; then
	TASK_ERROR "update_failed" "$(T 'The update could not be installed' 'Não foi possível instalar a atualização') ($(tail -n 1 /run/muos/update-finish.err 2>/dev/null)). MUOS/update/update.log"
	exit 1
fi
TASK_COMPLETE "$(T 'Update installed: restarting' 'Atualização instalada: reiniciando')"
sleep 3
reboot
exit 0
