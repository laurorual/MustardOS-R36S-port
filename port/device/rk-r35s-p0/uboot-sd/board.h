/* SPDX-License-Identifier: GPL-2.0+ */
/* SD-only host probe. No persistent environment or legacy recovery scripts. */
#ifndef __MUOS_R35S_SD_PROBE_H
#define __MUOS_R35S_SD_PROBE_H

#define ROCKCHIP_DEVICE_SETTINGS "stdout=serial\0stderr=serial\0"
#include <configs/px30_common.h>

#undef CONFIG_USB_FUNCTION_MASS_STORAGE
#undef CONFIG_SUPPORT_EMMC_RPMB
#undef CONFIG_PREBOOT
#undef CONFIG_BOOTDELAY
#define CONFIG_BOOTDELAY (-1)
#undef CONFIG_BOOTCOMMAND
#define CONFIG_BOOTCOMMAND \
    "if mmc dev 1; then " \
      "if fatload mmc 1:1 0x02000000 Image 0x04000000; then " \
        "if fatload mmc 1:1 0x01f00000 rk3326-muos-r35s-panel0.dtb 0x00040000; then " \
          "booti 0x02000000 - 0x01f00000; " \
        "else echo Linux DTB load failed; fi; " \
      "else echo Image load failed; fi; " \
    "else echo SD probe failed; fi"

#undef CONFIG_EXTRA_ENV_SETTINGS
#define CONFIG_EXTRA_ENV_SETTINGS \
    "devtype=mmc\0devnum=1\0" \
    "hwrev=rg351mp\0lcd_rotate=0\0" \
    "fdt_addr_r=0x01e00000\0" \
    "bootargs=console=ttyFIQ0,115200n8 console=tty0 " \
        "root=/dev/mmcblk0p2 rootfstype=ext4 rootwait ro init=/bin/sh " \
        "loglevel=7 consoleblank=0\0"

#endif
