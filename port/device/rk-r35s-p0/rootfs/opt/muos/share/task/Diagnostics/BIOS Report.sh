#!/bin/sh
# HELP: BIOS Report - Lists the BIOS files each installed core looks for in MUOS/bios and which are missing
# ICON: diagnostic
# EXECUTION_MODE: progress
# CAN_CANCEL: 0
# PROTOCOL_VERSION: 1
# SPDX-License-Identifier: MIT
# muOS R35S port (M6): the firmware lists of the libretro .info files
# (share/emulator/retroarch/info, the same lists muxretro checks before a
# launch) against MUOS/bios. A name that only matches in another case is
# reported: muxretro accepts it, most cores open the exact name.
# "required" only for the cores that run nothing without it (muxretro
# refuses gearcoleco; blueMSX needs its Databases and Machines); other
# entries the .info marks as not optional (gpSP's gba_bios.bin: it has a
# built-in replacement) are shown as "listed".
NEEDS_BIOS=" gearcoleco_libretro bluemsx_libretro "

. /opt/muos/script/var/diag.sh

BIOS_DIR=/run/muos/storage/bios
INFO_DIR=/opt/muos/share/emulator/retroarch/info
CORE_DIR=/opt/muos/share/core

DIAG_BEGIN "bios_report" "BIOS Report"
DIAG_KV "BIOS folder" "$(DIAG_STORE_DIR | sed 's|/log/diagnostics$|/bios|')"

for CORE in "$CORE_DIR"/*_libretro.so; do
	[ -f "$CORE" ] || continue
	NAME=$(basename "$CORE" .so)
	INFO="$INFO_DIR/$NAME.info"
	[ -f "$INFO" ] || continue
	LIST=$(sed -n 's/^firmware\([0-9]*\)_path *= *"\(.*\)"$/\1|\2/p' "$INFO")
	[ -n "$LIST" ] || continue

	DIAG_SECTION "$(sed -n 's/^corename *= *"\(.*\)"$/\1/p' "$INFO") ($NAME)"
	printf '%s\n' "$LIST" | while IFS='|' read -r IDX FILE; do
		OPT=$(sed -n "s/^firmware${IDX}_opt *= *\"\(.*\)\"$/\1/p" "$INFO")
		KIND=optional
		if [ "$OPT" != true ]; then
			case "$NEEDS_BIOS" in
				*" $NAME "*) KIND=required ;;
				*) KIND=listed ;;
			esac
		fi
		if [ -e "$BIOS_DIR/$FILE" ]; then
			STATE="ok   $(md5sum "$BIOS_DIR/$FILE" 2>/dev/null | cut -d' ' -f1)"
		else
			ALT=$(find "$BIOS_DIR" 2>/dev/null | grep -i -x -F "$BIOS_DIR/$FILE" | head -n 1)
			if [ -n "$ALT" ]; then
				STATE="case ${ALT#"$BIOS_DIR"/}"
			else
				STATE="missing"
			fi
		fi
		DIAG_OUT "$(printf '   %-9s %-34s %s' "$KIND" "$FILE" "$STATE")"
		printf '%s|%s|%s\n' "$KIND" "$FILE" "$STATE" >>/tmp/muos_bios_report.$$
	done
done

if [ -f /tmp/muos_bios_report.$$ ]; then
	while IFS='|' read -r KIND FILE STATE; do
		case "$STATE" in
			case*) DIAG_FINDING "bios" "$FILE is present as ${STATE#case } - rename it to $FILE" ;;
			missing) [ "$KIND" = required ] && DIAG_FINDING "bios" "$FILE is missing (required)" ;;
		esac
	done </tmp/muos_bios_report.$$
	rm -f /tmp/muos_bios_report.$$
fi

DIAG_FINISH "BIOS report saved"
exit 0
