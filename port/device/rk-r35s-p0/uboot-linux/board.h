/* SPDX-License-Identifier: GPL-2.0+ */
#include <configs/muos-r35s-monitor.h>
#define MUOS_LINUX_DIAGNOSTIC 1
#undef CONFIG_BOOTDELAY
#define CONFIG_BOOTDELAY 3
#undef CONFIG_BOOTCOMMAND
#define CONFIG_BOOTCOMMAND "muos_linux_diag"
#undef CONFIG_EXTRA_ENV_SETTINGS
#define CONFIG_EXTRA_ENV_SETTINGS \
    "devtype=mmc\0devnum=1\0hwrev=rg351mp\0lcd_rotate=0\0" \
    "fdt_addr_r=0x01e00000\0" \
    "fdt_high=0xffffffffffffffff\0initrd_high=0xffffffffffffffff\0" \
    "bootargs=console=ttyFIQ0,115200n8 console=tty0 rdinit=/init " \
        "loglevel=7 ignore_loglevel consoleblank=0 vt.global_cursor_default=0 " \
        "panic=0 oops=panic muos_diag=MUOS-R35S-LINUX-P4-A01\0"
