/* SPDX-License-Identifier: GPL-2.0+ */
#include <configs/muos-r35s-linux.h>
#define MUOS_EXT4_DIAGNOSTIC 1
#undef CONFIG_EXTRA_ENV_SETTINGS
#define CONFIG_EXTRA_ENV_SETTINGS \
    "devtype=mmc\0devnum=1\0hwrev=rg351mp\0lcd_rotate=0\0" \
    "fdt_addr_r=0x01e00000\0fdt_high=0xffffffffffffffff\0" \
    "initrd_high=0xffffffffffffffff\0" \
    "bootargs=console=ttyFIQ0,115200n8 console=tty0 " \
        "root=PARTUUID=4d554432-02 rootfstype=ext4 rootwait ro " \
        "init=/sbin/muos-ext4-diag loglevel=7 consoleblank=0 " \
        "vt.global_cursor_default=0 panic=0 oops=panic " \
        "muos_diag=MUOS-R35S-EXT4-P4-B01\0"
