/* SPDX-License-Identifier: MIT */
/* Host fixture only: types/platform services, not replacement allocators. */
#ifndef MUOS_HOST_COMMON_H
#define MUOS_HOST_COMMON_H
#define __KERNEL__ 1
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <errno.h>
#include <assert.h>
typedef unsigned long ulong;
typedef uint32_t u32;
typedef uint64_t u64;
typedef uint64_t phys_addr_t;
typedef uint64_t phys_size_t;
#define __weak __attribute__((weak))
#define __section(name) __attribute__((section(name)))
#define ARRAY_SIZE(x) (sizeof(x)/sizeof((x)[0]))
#define min(a,b) ((a)<(b)?(a):(b))
#define ALIGN(x,a) (((x)+((a)-1)) & ~((typeof(x))(a)-1))
#define IS_ALIGNED(x,a) (!((x) & ((typeof(x))(a)-1)))
#define CONFIG_SYSMEM 1
#define CONFIG_LMB 1
#define CONFIG_BIDRAM 1
#define CONFIG_NR_DRAM_BANKS 12
#define CONFIG_SYS_MALLOC_LEN (192 << 20)
#define CONFIG_SYS_MALLOC_F_LEN 0x2000
#define CONFIG_SYS_STACK_SIZE 0x200000
#define ARCH_DMA_MINALIGN 64
#define GD_FLG_RELOC 1
#define container_of(ptr,type,member) ((type *)((char *)(ptr)-offsetof(type,member)))
#define debug(...) ((void)0)
#define U_BOOT_CMD(...)
typedef int cmd_tbl_t;
struct host_bd { struct { phys_addr_t start; phys_size_t size; } bi_dram[12]; };
struct host_gd {
    ulong flags, start_addr_sp, ram_top, video_top, video_bottom, relocaddr;
    struct host_bd *bd;
};
extern struct host_gd *gd;
#define DECLARE_GLOBAL_DATA_PTR extern struct host_gd *gd
void panic(const char *fmt, ...) __attribute__((noreturn));
int env_set(const char *, const char *);
#include <linux/list.h>
#include <lmb.h>
#endif
