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
# M7 (T3: the screen only said "6 findings"): a closing dialog sums up what
# is missing per core and offers to rename files whose names differ only in
# case; the full list stays in MUOS/log/diagnostics.
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

	CORENAME=$(sed -n 's/^corename *= *"\(.*\)"$/\1/p' "$INFO")
	DIAG_SECTION "$CORENAME ($NAME)"
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
		printf '%s|%s|%s|%s\n' "$KIND" "$FILE" "$STATE" "$CORENAME" >>/tmp/muos_bios_report.$$
	done
done

PT=0
case "$(head -n 1 /opt/muos/config/settings/general/language 2>/dev/null)" in Portuguese*) PT=1 ;; esac
MISSING="" RENAME="" OK=0
REPORT=/tmp/muos_bios_report.$$
if [ -f "$REPORT" ]; then
	while IFS='|' read -r KIND FILE STATE CORENAME; do
		case "$STATE" in
			ok*) OK=$((OK + 1)) ;;
			case*)
				DIAG_FINDING "bios" "$FILE is present as ${STATE#case } - rename it to $FILE"
				RENAME="$RENAME, ${STATE#case } > $FILE"
				;;
			missing)
				if [ "$KIND" = required ]; then
					DIAG_FINDING "bios" "$FILE is missing (required)"
					MISSING="$MISSING, $FILE ($CORENAME)"
				fi
				;;
		esac
	done <"$REPORT"
fi

# Closing dialog (at most TASK_TEXT_MAX = 512 bytes)
if [ "$PT" = 1 ]; then
	T_TITLE="Relatório de BIOS" T_OK="OK" T_FIX="Renomear" T_KEEP="Manter"
	MSG="$OK arquivo(s) de BIOS encontrado(s)."
	[ -n "$MISSING" ] && MSG="$MSG Faltando (o core não roda sem): ${MISSING#, }."
	[ -n "$RENAME" ] && MSG="$MSG Nome com maiúsculas/minúsculas diferentes: ${RENAME#, }."
	[ -z "$MISSING$RENAME" ] && MSG="$MSG Nenhum problema."
	MSG="$MSG Lista completa: MUOS/log/diagnostics."
else
	T_TITLE="BIOS Report" T_OK="OK" T_FIX="Rename" T_KEEP="Keep"
	MSG="$OK BIOS file(s) found."
	[ -n "$MISSING" ] && MSG="$MSG Missing (the core needs it): ${MISSING#, }."
	[ -n "$RENAME" ] && MSG="$MSG Name differs in case: ${RENAME#, }."
	[ -z "$MISSING$RENAME" ] && MSG="$MSG No problems."
	MSG="$MSG Full list: MUOS/log/diagnostics."
fi
MSG=$(printf '%s' "$MSG" | cut -c1-500)

if [ -n "$RENAME" ]; then
	if [ "$(TASK_PROMPT "bios_rename" "choice" "$T_TITLE" "$MSG" "$T_FIX|$T_KEEP" "$T_KEEP")" = "$T_FIX" ]; then
		while IFS='|' read -r KIND FILE STATE CORENAME; do
			case "$STATE" in case*) ;; *) continue ;; esac
			SRC="$BIOS_DIR/${STATE#case }"
			if [ ! -e "$BIOS_DIR/$FILE" ] && mv -n "$SRC" "$BIOS_DIR/$FILE"; then
				DIAG_OUT "renamed ${STATE#case } -> $FILE"
			fi
		done <"$REPORT"
		sync
	fi
else
	TASK_PROMPT "bios_summary" "confirm" "$T_TITLE" "$MSG" "$T_OK" "$T_OK" >/dev/null || :
fi
rm -f "$REPORT"
DIAG_FINISH "BIOS report saved"
exit 0
