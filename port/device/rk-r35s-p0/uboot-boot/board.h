/* SPDX-License-Identifier: GPL-2.0+ */
/* M3b: the ext4 product boot through boot records; U-Boot appends
 * muos_slot=trial|main|previous.
 * M8: root by the slot-1 device (decision 16; the kernel numbers slot 1
 * mmcblk0 by its DT alias, so an image copy in slot 2 with the same
 * PARTUUID can't be taken for the root); the kernel console on the serial
 * port only and quiet, so the LCD shows the boot logo instead of the log
 * (dmesg keeps it). */
#include <configs/muos-r35s-linux.h>
#define MUOS_EXT4_DIAGNOSTIC 1
#undef CONFIG_BOOTDELAY
#define CONFIG_BOOTDELAY 0 /* M8; the control DT says 0 too (uboot-tree.py) */
#undef CONFIG_BOOTCOMMAND
#define CONFIG_BOOTCOMMAND "muos_boot"
#undef CONFIG_EXTRA_ENV_SETTINGS
#define CONFIG_EXTRA_ENV_SETTINGS \
    "devtype=mmc\0devnum=1\0hwrev=rg351mp\0lcd_rotate=0\0" \
    "fdt_addr_r=0x01e00000\0fdt_high=0xffffffffffffffff\0" \
    "initrd_high=0xffffffffffffffff\0" \
    "bootargs=console=ttyFIQ0,115200n8 " \
        "root=/dev/mmcblk0p2 rootfstype=ext4 rootwait ro " \
        "init=/sbin/muos-ext4-diag quiet loglevel=3 consoleblank=0 " \
        "vt.global_cursor_default=0 panic=0 oops=panic " \
        "muos_diag=MUOS-R35S-EXT4-P4-B01\0"
