/* SPDX-License-Identifier: GPL-2.0+ */
#ifndef __MUOS_R35S_MEMORY_H
#define __MUOS_R35S_MEMORY_H

/* Dedicated lifetime: from early sysmem initialization through kernel handoff.
 * Keep separate from the Linux FDT and its MEMBLK_ID_FDT allocation.
 */
#define MUOS_CONTROL_FDT_BASE 0x01e00000UL
#define MUOS_CONTROL_FDT_SIZE 0x00040000UL
#define MUOS_CONTROL_FDT_NAME "muos-control-fdt"

#endif
