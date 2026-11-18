#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# muOS R35S port: script/device/storage.sh, after MustardOS internal
# (550cc58f) device/storage.sh, for the second card slot only.
#   storage.sh sdcard mount|eject|down|status [DURING_BOOT]
#   storage.sh rom status
# Slot 2 is the SD controller ff380000.dwmmc (card detect in the DT; the
# kernel numbers cards in detection order, so the device is found by
# controller, never as mmcblk1). Partition 1, else the whole card;
# exFAT, FAT32 or ext4 at /mnt/sdcard, as upstream's MOUNT_DEVICE (ROMS,
# ARCHIVE and ports folders created). Called by the Storage tasks, the
# slot-2 udev rule (muos-sdcard-hotplug) and S90muos-storage.
# Upstream's bind.sh (per-location SD1/SD2 preferences, muxstorage) is not
# ported: the MUOS folders stay on the card in slot 1; slot 2 adds content.
# The SD1 card ('rom') is mounted by S89/S90 and only reports its status.

. /opt/muos/script/var/base.sh
. /opt/muos/script/var/config.sh
. /opt/muos/script/var/log.sh
. /opt/muos/script/var/ui.sh

TYPE=${1:-}
ACTION=${2:-}
MOUNT_POINT=/mnt/sdcard
LOCK=/run/muos/sdcard.lock

slot2_disk() {
	# T2 hook (t2-sdcard.sh): a loop device stands in for the slot-2 card
	[ -n "${MUOS_SD2_TEST_DISK:-}" ] && {
		echo "$MUOS_SD2_TEST_DISK"
		return 0
	}
	for b in /sys/devices/platform/ff380000.dwmmc/mmc_host/mmc*/mmc*:*/block/mmcblk*; do
		[ -e "$b" ] || continue
		echo "${b##*/}"
		return 0
	done
	return 1
}

MOUNTED() {
	grep -q " $MOUNT_POINT " /proc/mounts
}

MOUNT_DEVICE() {
	DISK=$(slot2_disk) || return 2
	DEVICE=$DISK
	[ -b "/dev/${DISK}p1" ] && DEVICE=${DISK}p1

	FS_TYPE=$(blkid -o value -s TYPE "/dev/$DEVICE" 2>/dev/null)
	FS_LABEL=$(blkid -o value -s LABEL "/dev/$DEVICE" 2>/dev/null)
	case "$FS_TYPE" in
		exfat) FS_OPTS="rw,noatime,nosuid,nodev" ;;
		vfat) FS_OPTS="rw,noatime,nosuid,nodev,utf8,shortname=mixed,errors=remount-ro" ;;
		ext4) FS_OPTS="rw,noatime,nosuid,nodev" ;;
		*)
			LOG_WARN "$0" 0 "STORAGE" "$(printf "SD2: unsupported filesystem '%s' on /dev/%s" "$FS_TYPE" "$DEVICE")"
			return 3
			;;
	esac

	if [ "$FS_TYPE" = vfat ] || [ "$FS_TYPE" = exfat ]; then
		fsck_tool=fsck.$FS_TYPE
		[ "$FS_TYPE" = exfat ] && fsck_tool=exfatfsck
		command -v "$fsck_tool" >/dev/null 2>&1 && "$fsck_tool" -a "/dev/$DEVICE" >/dev/null 2>&1
	fi

	mkdir -p "$MOUNT_POINT"
	mount -t "$FS_TYPE" -o "$FS_OPTS" "/dev/$DEVICE" "$MOUNT_POINT" || return 4

	SET_VAR "device" "storage/sdcard/active" "1"
	SET_VAR "device" "storage/sdcard/label" "${FS_LABEL:-}"
	SET_VAR "device" "storage/sdcard/type" "$FS_TYPE"
	echo "deadline" >"/sys/block/$DISK/queue/scheduler" 2>/dev/null
	mkdir -p "$MOUNT_POINT/ROMS" "$MOUNT_POINT/ARCHIVE" "$MOUNT_POINT/ports"
	LOG_SUCCESS "$0" 0 "STORAGE" "$(printf "SD2: /dev/%s (%s) at %s" "$DEVICE" "$FS_TYPE" "$MOUNT_POINT")"
	return 0
}

UNMOUNT_DEVICE() {
	sync
	umount "$MOUNT_POINT" 2>/dev/null || umount -l "$MOUNT_POINT" || return 1
	SET_VAR "device" "storage/sdcard/active" "0"
	SET_VAR "device" "storage/sdcard/label" ""
	return 0
}

case "$TYPE:$ACTION" in
	sdcard:mount)
		exec 9>"$LOCK"
		flock -x 9
		if MOUNTED; then
			TASK_STATUS "Secondary storage already mounted"
			exit 0
		fi
		MOUNT_DEVICE
		rc=$?
		case $rc in
			0)
				TASK_STATUS "Secondary storage mounted"
				TASK_DETAIL "$MOUNT_POINT"
				exit 0
				;;
			2) TASK_ERROR "no_device" "No card in the second slot" ;;
			3) TASK_ERROR "mount_failed" "Unsupported filesystem on the second card (use exFAT, FAT32 or ext4)" ;;
			*) TASK_ERROR "mount_failed" "The second card could not be mounted" ;;
		esac
		SET_VAR "device" "storage/sdcard/active" "0"
		exit 1
		;;
	sdcard:eject | sdcard:down)
		exec 9>"$LOCK"
		flock -x 9
		if ! MOUNTED; then
			SET_VAR "device" "storage/sdcard/active" "0"
			TASK_STATUS "Secondary storage already unmounted"
			exit 0
		fi
		if UNMOUNT_DEVICE; then
			TASK_STATUS "Secondary storage ejected"
			exit 0
		fi
		TASK_ERROR "eject_failed" "Secondary storage could not be ejected"
		exit 1
		;;
	sdcard:status)
		MOUNTED && {
			echo mounted
			exit 0
		}
		slot2_disk >/dev/null && echo present || echo absent
		exit 1
		;;
	rom:status)
		grep -q " $(GET_VAR "device" "storage/rom/mount") " /proc/mounts && echo mounted && exit 0
		echo absent
		exit 1
		;;
	*)
		printf 'usage: %s sdcard mount|eject|down|status | rom status\n' "$0" >&2
		exit 2
		;;
esac
