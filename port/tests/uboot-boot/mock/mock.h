/* SPDX-License-Identifier: MIT */
/* Minimal host stand-ins for the U-Boot APIs boot.c uses (see test.c). */
#ifndef MUOS_UBOOT_MOCK_H
#define MUOS_UBOOT_MOCK_H
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint8_t u8;
typedef uint32_t u32;
typedef uint64_t u64;
typedef unsigned long ulong;
typedef unsigned long lbaint_t;
typedef struct cmd_tbl_s { int unused; } cmd_tbl_t;
struct blk_desc { int devnum; };

#define CMD_RET_FAILURE 1
#define CONFIG_SYS_FDT_PAD 0x3000
#define SHA256_SUM_LEN 32
#define CHUNKSZ_SHA256 (64 * 1024)
#define ALLOC_CACHE_ALIGN_BUFFER(type, name, size) type name[size] __attribute__((aligned(64)))
#define U_BOOT_CMD(name, maxargs, rep, cmd, usage, help) int (*muos_cmd_entry)(cmd_tbl_t *, int, int, char *const[]) = cmd
#define le64_to_cpu(x) (x)
#define le32_to_cpu(x) (x)

extern unsigned char *mock_ram;
#define ram(addr) ((void *)(mock_ram + (addr)))

int run_command(const char *cmd, int flag);
char *env_get(const char *name);
int env_set(const char *name, const char *value);
ulong env_get_hex(const char *name, ulong def);
void *sysmem_alloc_base_by_name(const char *name, ulong base, ulong size);
struct blk_desc *blk_get_dev(const char *ifname, int dev);
ulong blk_dread(struct blk_desc *d, lbaint_t start, lbaint_t cnt, void *buf);
ulong blk_dwrite(struct blk_desc *d, lbaint_t start, lbaint_t cnt, const void *buf);
void sha256_csum_wd(const unsigned char *in, unsigned int len, unsigned char *out, unsigned int chunk);
int fdt_check_header(const void *fdt);
u32 fdt_totalsize(const void *fdt);
void lcd_clear(void);
int lcd_init(void);
int show_bmp(unsigned long bmp_mem);
void lcd_printf(int x, int y, int size, const char *fmt, ...);
void panic(const char *fmt, ...) __attribute__((noreturn));
#endif
