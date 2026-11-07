/* SPDX-License-Identifier: GPL-2.0+ */
/* Fixed-address diagnostic handoff. Never execute an SD startup script. */
#include <common.h>
#include <command.h>
#include <sysmem.h>
#include <linux/libfdt.h>
#include <u-boot/sha256.h>
#include <rockchip_display_cmds.h>
#include <configs/muos-r35s-linux-assets.h>

static void stop_probe(const char *reason)
{
    lcd_clear();
    lcd_printf(0, 2, 0, "muOS Linux diagnostic: STOPPED");
    lcd_printf(0, 4, 0, "%s", reason);
    lcd_printf(0, 6, 0, "No kernel started. Hold Power to turn off.");
    panic("muOS Linux diagnostic: %s\n", reason);
}

static void load_checked(const char *name, ulong address, ulong bytes,
                         const unsigned char *expected)
{
    char command[160];
    unsigned char digest[SHA256_SUM_LEN];

    /* A one-byte excess load detects an oversized asset within its reserved
     * region. A failed/short/oversized read can never reach booti.
     */
    snprintf(command, sizeof(command), "fatload mmc 1:1 %lx %s %lx",
             address, name, bytes + 1);
    if (run_command(command, 0) || env_get_hex("filesize", 0) != bytes)
        stop_probe("Asset read/size check failed");
    sha256_csum_wd((const unsigned char *)address, bytes, digest, CHUNKSZ_SHA256);
    if (memcmp(digest, expected, SHA256_SUM_LEN))
        stop_probe("Asset SHA256 mismatch");
}

static int do_muos_linux_diag(cmd_tbl_t *cmdtp, int flag, int argc,
                              char *const argv[])
{
    char command[128];
    const ulong kernel_span = 0x00ec0000;
    static const unsigned char kernel_sha[] = MUOS_IMAGE_SHA256;
    static const unsigned char fdt_sha[] = MUOS_LINUX_FDT_SHA256;
#ifndef MUOS_EXT4_DIAGNOSTIC
    static const unsigned char initrd_sha[] = MUOS_INITRD_SHA256;
#endif

    /* Keep the kernel's load AND relocation/BSS ranges, separate Linux FDT
     * with native padding, and initrd away from framework/stack/secure holes.
     */
    if ((ulong)sysmem_alloc_base_by_name("muos-diag-kernel", 0x02000000,
                                       kernel_span) != 0x02000000 ||
        (ulong)sysmem_alloc_base_by_name("muos-diag-linux-fdt", 0x01f00000,
                                       0x40000) != 0x01f00000)
        stop_probe("RAM reservation failed");
#ifndef MUOS_EXT4_DIAGNOSTIC
    if (
        (ulong)sysmem_alloc_base_by_name("muos-diag-initrd", 0x0a200000,
                                       0x800000) != 0x0a200000)
        stop_probe("RAM reservation failed");
#endif
    if (run_command("mmc dev 1", 0))
        stop_probe("Test SD selection failed");
    load_checked("Image", 0x02000000, MUOS_IMAGE_BYTES, kernel_sha);
    load_checked("rk3326-muos-r35s-panel0.dtb", 0x01f00000,
                 MUOS_LINUX_FDT_BYTES, fdt_sha);
#ifndef MUOS_EXT4_DIAGNOSTIC
    load_checked("initramfs.cpio.gz", 0x0a200000, MUOS_INITRD_BYTES, initrd_sha);
#endif
    if (fdt_check_header((void *)0x01f00000) ||
        fdt_totalsize((void *)0x01f00000) != MUOS_LINUX_FDT_BYTES ||
        MUOS_LINUX_FDT_BYTES + CONFIG_SYS_FDT_PAD > 0x40000)
        stop_probe("Linux FDT bounds failed");
    lcd_clear();
    lcd_printf(0, 2, 0, "muOS - R35S / Panel 0");
    lcd_printf(0, 4, 0, "Linux diagnostic: ASSETS VERIFIED");
#ifdef MUOS_EXT4_DIAGNOSTIC
    lcd_printf(0, 6, 0, "Starting own Linux + ext4 diagnostic...");
#else
    lcd_printf(0, 6, 0, "Starting own Linux + RAM init...");
#endif
    /* Native booti checks the Image header, relocates to 0x02080000,
     * reserves the kernel in bootm's LMB and applies the DT handoff fixups.
     * In-place FDT/initrd were pre-reserved and their bounds checked above.
     */
#ifdef MUOS_EXT4_DIAGNOSTIC
    snprintf(command, sizeof(command), "booti 0x02000000 - 0x01f00000");
#else
    snprintf(command, sizeof(command), "booti 0x02000000 0x0a200000:%lx 0x01f00000",
             (ulong)MUOS_INITRD_BYTES);
#endif
    run_command(command, 0);
    stop_probe("Kernel handoff returned");
    return CMD_RET_FAILURE;
}

U_BOOT_CMD(muos_linux_diag, 1, 0, do_muos_linux_diag,
           "boot the fixed private Linux diagnostic assets", "");
