/* SPDX-License-Identifier: GPL-2.0+ */
/* Exercise the actual pinned sysmem.c/lmb.c/memblk.c and port board hooks.
 * DDR/BIDRAM discovery and gd fields are simulated. No device is accessed.
 */
#define _GNU_SOURCE
#include <common.h>
#include <sys/mman.h>
#include <stdarg.h>
#include <sysmem.h>
#include <bidram.h>
#include <configs/muos-r35s-memory.h>
#include <rockchip_display_cmds.h>

static struct host_bd bd;
static struct host_gd state = { .bd = &bd };
struct host_gd *gd = &state;
extern struct sysmem plat_sysmem;
int muos_reserve_control_fdt(void);
void muos_reserve_bootm_fdt(struct lmb *lmb);
int rk_board_late_init(void);
static int display_calls, display_lines, display_error;
static int display_width = 640;
static struct lcd mock_display;
struct lcd *lcd;

/* Screen calls are mocked: this verifies gating and bounded arguments only,
 * not the native renderer, MMIO, panel initialization or displayed colors. */
int lcd_init(void)
{
    display_calls++;
    if (display_error)
        return display_error;
    lcd = &mock_display;
    lcd->w = display_width;
    lcd->h = 480;
    lcd->rot = 0;
    lcd->bpp = 24;
    lcd->drm_fb_mem = gd->video_bottom;
    lcd->drm_fb_size = display_width * 480UL * 3;
    return 0;
}
int lcd_setfg_color(const char *color) { assert(!strcmp(color, "white")); return 0; }
int lcd_setbg_color(const char *color) { assert(!strcmp(color, "black")); return 0; }
int lcd_clear(void) { return 0; }
int lcd_printf(ulong x, ulong y, unsigned char align, const char *fmt, ...)
{
    char text[128];
    va_list args;
    int size;
    assert(x == 0 && y < 30 && align == 0);
    va_start(args, fmt);
    size = vsnprintf(text, sizeof(text), fmt, args);
    va_end(args);
    assert(size >= 0 && size < 80);
    display_lines++;
    return 0;
}

int env_set(const char *key, const char *value) { (void)key; (void)value; return 0; }
void panic(const char *fmt, ...)
{
    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    abort();
}
struct memblock *bidram_reserved_is_overlap(phys_addr_t base, phys_size_t size)
{
    (void)base; (void)size;
    return NULL; /* Trust carveouts require runtime ATAGS; not modeled here. */
}

static void map_private(ulong base, size_t size)
{
    void *memory = mmap((void *)base, size, PROT_READ|PROT_WRITE,
                        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE, -1, 0);
    assert(memory == (void *)base);
}

static void initial_state(void)
{
    memset(&bd, 0, sizeof(bd));
    bd.bi_dram[0].start = 0x00200000;
    bd.bi_dram[0].size = 0x3fe00000;
    gd->flags = 0;
    gd->start_addr_sp = 0x30000000;
    gd->ram_top = 0x40000000;
    gd->video_top = gd->ram_top;
    gd->video_bottom = 0x3de00000;
    gd->relocaddr = 0x3dc00000;
}

static void assert_control_reserved(void)
{
    struct memblock *mem;
    int found = 0;
    assert(lmb_is_reserved(&plat_sysmem.lmb, MUOS_CONTROL_FDT_BASE));
    assert(lmb_is_reserved(&plat_sysmem.lmb, MUOS_CONTROL_FDT_BASE+MUOS_CONTROL_FDT_SIZE-1));
    list_for_each_entry(mem, &plat_sysmem.allocated_head, node) {
        if (!strcmp(mem->attr.name, MUOS_CONTROL_FDT_NAME)) {
            assert(mem->base == MUOS_CONTROL_FDT_BASE);
            assert(mem->size == MUOS_CONTROL_FDT_SIZE);
            assert(!(mem->attr.flags & M_ATTR_KMEM_RESERVED));
            found++;
        }
    }
    assert(found == 1);
}

int main(void)
{
    _Static_assert(sizeof(ulong) == 8 && sizeof(void *) == 8, "64-bit host required");
    unsigned char *control = (void *)MUOS_CONTROL_FDT_BASE;
    ulong count;
    struct lmb bootm;
    phys_addr_t allocated;
    /* Only private anonymous process pages: never /dev/mem or card nodes. */
    map_private(MUOS_CONTROL_FDT_BASE, MUOS_CONTROL_FDT_SIZE);
    map_private(0x01f00000, 0x2000); /* Native FDT tail sentinel. */
    map_private(0x2fdff000, 0x1000); /* Native stack head sentinel. */
    control[0] = 0x5a;
    initial_state();
    assert(muos_reserve_control_fdt() == -ENOSYS);
    assert(sysmem_init() == 0);
    assert_control_reserved();
    count = plat_sysmem.allocated_cnt;
    assert(muos_reserve_control_fdt() == 0);
    assert(plat_sysmem.allocated_cnt == count);
    assert(sysmem_alloc_base_by_name("collision", MUOS_CONTROL_FDT_BASE, 16) == NULL);
    assert(sysmem_alloc_base_by_name("boundary", MUOS_CONTROL_FDT_BASE+MUOS_CONTROL_FDT_SIZE, 8));
    assert(sysmem_alloc_base(MEMBLK_ID_FDT, 0x01f00000, 0x1000));
    assert(control[0] == 0x5a);
    gd->flags = GD_FLG_RELOC;
    assert(sysmem_initr() == 0);
    assert_control_reserved();
    assert(muos_reserve_control_fdt() == 0);
    assert(control[0] == 0x5a);
    lmb_init(&bootm);
    assert(lmb_add(&bootm, 0x00200000, 0x3fe00000) >= 0);
    muos_reserve_bootm_fdt(&bootm);
    assert(lmb_is_reserved(&bootm, MUOS_CONTROL_FDT_BASE));
    assert(lmb_is_reserved(&bootm, MUOS_CONTROL_FDT_BASE+MUOS_CONTROL_FDT_SIZE-1));
    allocated = lmb_alloc_base(&bootm, MUOS_CONTROL_FDT_SIZE, 1,
                              MUOS_CONTROL_FDT_BASE+MUOS_CONTROL_FDT_SIZE);
    assert(allocated && allocated+MUOS_CONTROL_FDT_SIZE <= MUOS_CONTROL_FDT_BASE);
    initial_state();
    /* Bank layout actually observed in the installed Linux DT, not assumed
     * to be the future candidate's runtime ATAGS. Excludes ATF and TEE. */
    bd.bi_dram[0].size = 0x08200000;
    bd.bi_dram[1].start = 0x0a200000;
    bd.bi_dram[1].size = 0x35e00000;
    assert(sysmem_init() == 0);
    assert_control_reserved();
    assert(!sysmem_alloc_base_by_name("atf-hole", 0x00010000, 0x1000));
    assert(!sysmem_alloc_base_by_name("tee-hole", 0x08400000, 0x1000));
    initial_state();
    gd->start_addr_sp = 0x02000000; /* Simulated stack would overlap control FDT. */
    assert(sysmem_init() != 0);
    assert(control[0] == 0x5a);
    initial_state();
    bd.bi_dram[0].size = 0x00e00000; /* Too little usable RAM to include buffer. */
    assert(sysmem_init() != 0);
    initial_state();
    bd.bi_dram[0].size = MUOS_CONTROL_FDT_BASE-0x00200000;
    bd.bi_dram[1].start = 0x01f00000; /* Firmware gap across control buffer. */
    bd.bi_dram[1].size = 0x3e100000;
    assert(sysmem_init() != 0);
    initial_state();
    gd->video_bottom = gd->video_top;
    assert(rk_board_late_init() == -EINVAL && display_calls == 0);
    initial_state();
    gd->video_bottom = gd->video_top-0x100000;
    assert(rk_board_late_init() == -EINVAL && display_calls == 0);
    initial_state();
    gd->video_bottom = gd->start_addr_sp-1;
    assert(rk_board_late_init() == -EINVAL && display_calls == 0);
    initial_state();
    gd->video_top = gd->ram_top+1;
    assert(rk_board_late_init() == -EINVAL && display_calls == 0);
    initial_state();
    gd->ram_top = gd->video_top = 0x100000001UL;
    gd->video_bottom = gd->video_top-0x2200000;
    assert(rk_board_late_init() == -EINVAL && display_calls == 0);
    initial_state();
    display_error = -ENODEV;
    assert(rk_board_late_init() == -ENODEV && display_lines == 0);
    display_error = 0;
    display_width = 320;
    assert(rk_board_late_init() == -EINVAL && display_lines == 0);
    display_width = 640;
    assert(rk_board_late_init() == 0 && display_lines == 9);
    puts("PASS: actual native allocators; pre/post relocation, idempotence, collision, boundary, separate Linux FDT, bootm LMB, observed banks with ATF/TEE holes, low RAM and bank gap");
    return 0;
}
