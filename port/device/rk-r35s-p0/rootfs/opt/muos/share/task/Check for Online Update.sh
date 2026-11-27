#!/bin/sh
# HELP: Look for a newer firmware on the port's GitHub (needs Wi-Fi). If there is one, it shows the version and asks before downloading it; after the download you choose to install it now (the device restarts twice, about 10 minutes) or later with Install Firmware Update. Your games, saves and settings stay.
# ICON: cloud
# SORT_AFTER: Install Firmware Update
# EXECUTION_MODE: progress
# CAN_CANCEL: 1
# PROTOCOL_VERSION: 1
# SPDX-License-Identifier: MIT
# R35S port (v1.1.1 T3 request): the manual replacement for the old
# background updater; see /usr/libexec/muos-update (check, fetch, stage).

. /opt/muos/script/var/base.sh
. /opt/muos/script/var/ui.sh
. /usr/share/muos-r35s/update-task.sh

upd=/userdata/MUOS/update
TASK_BEGIN "check_online_update" "$(T 'Check for Online Update')"
TASK_STATUS "$(T 'Looking for a new version')"
if [ ! -e /run/muos/network/ready ] && [ ! -e /run/muos/update-test ]; then
	TASK_ERROR "no_network" "$(T 'Connect to Wi-Fi first')"
	exit 1
fi
rc=0
out=$(/usr/libexec/muos-update check 2> /run/muos/update-check.err) || rc=$?
cur=$(/usr/libexec/muos-update status | sed -n 's/^idle (release \(.*\))$/\1/p')
cur=${cur#MustardOS-R36S-port-}
if [ "$rc" = 1 ]; then
	TASK_PROGRESS 1 1
	TASK_COMPLETE "$(T 'You have the latest version')${cur:+ ($cur)}"
	exit 0
elif [ "$rc" != 0 ]; then
	TASK_ERROR "check_failed" "$(T 'Could not reach the update server'): $(tail -n 1 /run/muos/update-check.err 2>/dev/null)"
	exit 1
fi
# shellcheck disable=SC2086 # NAME P2_URL SHA_URL P2_BYTES
set -- $out
name=$1 bytes=${4:-0}
ver=${name#MustardOS-R36S-port-}
mb=$((bytes / 1048576)) sz=
[ "$mb" -le 0 ] || sz=" ($mb MB)"
yes=$(T 'Download') no=$(T 'Cancel')
answer=$(TASK_PROMPT update_available confirm "$(T 'Update available'): $ver" \
	"$(T 'Download it now?')${cur:+ ($(T 'installed'): $cur)}$sz" "$yes|$no" "$no") || answer=$no
if [ "$answer" != "$yes" ]; then
	TASK_COMPLETE "$(T 'Not downloaded')"
	exit 0
fi

TASK_STATUS "$(T 'Downloading') $ver"
TASK_DETAIL "$(T 'Keep Wi-Fi on; a cancelled download resumes next time')"
gz=$upd/$name.p2.img.gz
/usr/libexec/muos-update fetch > /run/muos/update-fetch.out 2>&1 &
pid=$!
while kill -0 "$pid" 2>/dev/null; do
	n=$(stat -c %s "$gz.part" 2>/dev/null || stat -c %s "$gz" 2>/dev/null || echo 0)
	[ "$bytes" -gt 0 ] && TASK_PROGRESS "$((n / 1048576))" "$mb"
	sleep 1
done
if ! wait "$pid" || [ ! -f "$gz" ]; then
	TASK_ERROR "download_failed" "$(T 'Download failed'): $(tail -n 1 "$upd/update.log" 2>/dev/null | cut -d' ' -f3-)"
	exit 1
fi
TASK_PROGRESS 1 1

now=$(T 'Install now') later=$(T 'Later')
answer=$(TASK_PROMPT install_update confirm "$(T 'Download complete'): $ver" \
	"$(T 'Install it now? The device restarts twice (about 10 minutes); games, saves and settings stay. Needs the charger or 30 % battery.')" \
	"$now|$later" "$later") || answer=$later
if [ "$answer" != "$now" ]; then
	TASK_COMPLETE "$(T 'Saved in MUOS/update. To install it later:') $(T 'Install Firmware Update')"
	exit 0
fi
stage_and_restart
