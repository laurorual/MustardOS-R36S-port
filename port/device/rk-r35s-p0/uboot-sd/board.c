/* SPDX-License-Identifier: GPL-2.0+ */
/* Host-build probe for R35S / R36S-V12 Panel 0 only.
 * Keep the native Rockchip display drivers, without the legacy board's
 * recovery, raw GPIO, charge-display, autotest or filesystem policies.
 */
#include <common.h>
#include <asm/arch/boot_mode.h>
#include <configs/muos-r35s-memory.h>
#include <odroidgoa_status.h>
#include <rockchip_display_cmds.h>
#include <sysmem.h>

DECLARE_GLOBAL_DATA_PTR;
/* Global owned by the pinned native rockchip_display_cmds implementation. */
extern struct lcd *lcd;

#if !defined(CONFIG_SYSMEM) || !defined(CONFIG_LMB)
#error The R35S control FDT requires both native memory allocators
#endif

int muos_reserve_control_fdt(void)
{
    void *address;

    if (!sysmem_has_init())
        return -ENOSYS;
    address = sysmem_alloc_base_by_name(MUOS_CONTROL_FDT_NAME,
                                       MUOS_CONTROL_FDT_BASE,
                                       MUOS_CONTROL_FDT_SIZE);
    return (ulong)address == MUOS_CONTROL_FDT_BASE ? 0 : -ENOMEM;
}

int board_sysmem_reserve(struct sysmem *sysmem)
{
    (void)sysmem;
    /* The native allocator resets its map before and after relocation.
     * Re-register the dedicated buffer in each map, before FAT/DM can use it.
     */
    return muos_reserve_control_fdt();
}

void muos_reserve_bootm_fdt(struct lmb *lmb)
{
    /* bootm owns another LMB instance; it does not inherit sysmem allocations. */
    if (lmb_reserve(lmb, MUOS_CONTROL_FDT_BASE, MUOS_CONTROL_FDT_SIZE) < 0)
        panic("muOS SD probe: cannot reserve control FDT in bootm LMB\n");
}

void boot_devtype_init(void)
{
    /* CONFIG_ROCKCHIP_BOOT_MODE_REG=0 removes the generic boot-mode code.
     * The inherited resource reader still needs a fixed boot-device helper.
     */
    env_set("devtype", "mmc");
    env_set("devnum", "1");
}

int get_rg351_rev(void)
{
    /* Compatibility selector used by the inherited display rotation code.
     * This is not hardware detection; this build is exclusively Panel 0.
     */
    return MODEL_RG351MP;
}

int rk_board_late_init(void)
{
    /* Native DRM reserves a 640x480x32 framebuffer plus a 32-MiB pool.
     * A serial-free monitor must reject implausible ranges before probing
     * the display; physical addresses below remain runtime observations.
     */
    const ulong video_bytes = 640UL * 480UL * 4UL + (32UL << 20);
    int ret;

    if (gd->video_top <= gd->video_bottom ||
        gd->video_top - gd->video_bottom < video_bytes ||
        gd->video_bottom < gd->start_addr_sp ||
        gd->video_top > gd->ram_top || gd->video_top > 0xffffffffUL)
        return -EINVAL;
    ret = lcd_init();
    if (ret)
        return ret;
    if (!lcd || lcd->w != 640 || lcd->h != 480 || lcd->rot != 0 || lcd->bpp != 24 ||
        lcd->drm_fb_size != 640UL * 480UL * 3UL ||
        lcd->drm_fb_mem < gd->video_bottom || lcd->drm_fb_mem >= gd->video_top ||
        gd->video_top - lcd->drm_fb_mem < lcd->drm_fb_size)
        return -EINVAL;
    lcd_setfg_color("white");
    lcd_setbg_color("black");
    lcd_clear();
    lcd_printf(0, 1, 0, "muOS - R35S / Panel 0");
#ifdef MUOS_LINUX_DIAGNOSTIC
    lcd_printf(0, 3, 0, "Linux diagnostic: U-Boot reached");
#ifdef MUOS_EXT4_DIAGNOSTIC
    lcd_printf(0, 5, 0, "Linux + ext4 init will start automatically");
#else
    lcd_printf(0, 5, 0, "Linux + RAM init will start automatically");
#endif
#else
    lcd_printf(0, 3, 0, "SD monitor: U-Boot reached");
    lcd_printf(0, 5, 0, "Automatic kernel boot: OFF");
#endif
    lcd_printf(0, 7, 0, "RAM top    %08lx", gd->ram_top);
    lcd_printf(0, 8, 0, "Video      %08lx-%08lx", gd->video_bottom, gd->video_top);
    lcd_printf(0, 9, 0, "U-Boot     %08lx", gd->relocaddr);
    lcd_printf(0, 10, 0, "Stack      %08lx", gd->start_addr_sp);
    lcd_printf(0, 11, 0, "Control DTB %08lx", MUOS_CONTROL_FDT_BASE);
#ifdef MUOS_LINUX_DIAGNOSTIC
    lcd_printf(0, 13, 0, "No product frontend or network");
#else
    lcd_printf(0, 13, 0, "No Linux or frontend started");
#endif
    puts("muOS R35S Panel 0 SD probe: automatic boot disabled\n");
    return 0;
}

int odroid_display_status(int mode, int storage, const char *message)
{
    (void)mode;
    (void)storage;
    printf("muOS SD probe status: %s\n", message ? message : "unspecified");
    return 0;
}

void odroid_drop_errorlog(const char *message, unsigned int size)
{
    /* The old helper wrote a file to FAT. Diagnostics stay on the console. */
    printf("muOS SD probe: %.*s\n", (int)size, message);
}

void odroid_wait_pwrkey(void)
{
    panic("muOS SD probe stopped; inspect serial diagnostics\n");
}

void odroid_alert_leds(void)
{
    panic("muOS SD probe stopped; no unverified LED GPIO toggling\n");
}
