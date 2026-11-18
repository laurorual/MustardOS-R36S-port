#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# muOS R35S port: script/mux/screenshot.sh, after MustardOS internal
# (550cc58f). The panel is a KMS plane that /dev/fb0 (mufbset -g) does not
# show, so the request always goes to the frontend (frontend patch 0007
# serves it on every output, not only in HDMI mode). muxretro has no
# capture of its own: in a game the request is dropped and logged.
#   screenshot.sh [FILE]   default MUOS/screenshot/muOS_<date>_<n>.png

. /opt/muos/script/var/display.sh

SS_LOCK="$MUOS_RUN_DIR/screenshot.lock"
mkdir "$SS_LOCK" 2>/dev/null || {
	# a lock left by a killed capture is older than the 8 s wait below
	[ -n "$(find "$SS_LOCK" -maxdepth 0 -mmin +1 2>/dev/null)" ] || exit 0
}
trap 'rmdir "$SS_LOCK" 2>/dev/null' EXIT
trap 'exit 1' HUP INT TERM

for p in /proc/[0-9]*; do
	[ "$(readlink "$p/exe" 2>/dev/null)" = /opt/muos/frontend/muxretro ] || continue
	LOG_WARN "$0" 0 "SCREENSHOT" "In-game screenshots are not supported on this port"
	exit 1
done

BASE_DIR="$MUOS_STORE_DIR/screenshot"
mkdir -p "$BASE_DIR"
SS_FILE=$1
# a given path is replaced (the wait below takes any non-empty file)
[ -z "$SS_FILE" ] || rm -f "$SS_FILE"
if [ -z "$SS_FILE" ]; then
	CURRENT_DATE="$(date +"%Y%m%d_%H%M")"
	INDEX=0
	while [ -f "${BASE_DIR}/muOS_${CURRENT_DATE}_${INDEX}.png" ]; do INDEX=$((INDEX + 1)); done
	SS_FILE="${BASE_DIR}/muOS_${CURRENT_DATE}_${INDEX}.png"
fi

LOG_INFO "$0" 0 "SCREENSHOT" "Capturing screenshot"
SS_REQUEST="$MUOS_RUN_DIR/screenshot_request"
rm -f "$SS_REQUEST" "$SS_REQUEST.$$"
printf '%s\n' "$SS_FILE" >"$SS_REQUEST.$$" && mv -f "$SS_REQUEST.$$" "$SS_REQUEST"

# The frontend polls every 32 ms while it draws; an idle screen still ticks.
SS_WAIT=0
while [ "$SS_WAIT" -lt 80 ]; do
	[ -s "$SS_FILE" ] && break
	sleep 0.1
	SS_WAIT=$((SS_WAIT + 1))
done
rm -f "$SS_REQUEST"

if [ -s "$SS_FILE" ]; then
	RUMBLE "$(GET_VAR "device" "board/rumble")" 0.3
	LOG_SUCCESS "$0" 0 "SCREENSHOT" "$(printf "Screenshot saved: '%s'" "$SS_FILE")"
	printf '%s\n' "$SS_FILE"
else
	LOG_ERROR "$0" 0 "SCREENSHOT" "Screenshot capture failed"
	exit 1
fi
