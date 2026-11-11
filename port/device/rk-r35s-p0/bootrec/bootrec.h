/* SPDX-License-Identifier: GPL-2.0+ OR MIT */
/*
 * muOS R35S boot records: one 512-byte sector each in the unused gap
 * between the MBR and the idbloader (sector 64). U-Boot boots the armed
 * trial record once (consuming it first), then main, then previous.
 * Shared by U-Boot, the device tool (muos-bootrec) and the host tests;
 * port/scripts/bootrec.py is the host encoder and must stay in sync.
 *
 * Layout (little endian):
 *   0   magic "MUOSBREC"      8   u32 version (1)    12  u32 state
 *   16  char image[48]        64  u32 image_bytes    68  u8 image_sha256[32]
 *   100 char fdt[48]          148 u32 fdt_bytes      152 u8 fdt_sha256[32]
 *   184 char label[32]        216 zero ...           508 u32 crc32(0..507)
 */
#ifndef MUOS_BOOTREC_H
#define MUOS_BOOTREC_H

#ifdef __UBOOT__
#include <linux/types.h>
typedef u8 bootrec_u8;
typedef u32 bootrec_u32;
#else
#include <stddef.h>
#include <stdint.h>
typedef uint8_t bootrec_u8;
typedef uint32_t bootrec_u32;
#endif

#define BOOTREC_SECTOR_BYTES 512
#define BOOTREC_SECTOR_MAIN 32
#define BOOTREC_SECTOR_PREVIOUS 33
#define BOOTREC_SECTOR_TRIAL 34
#define BOOTREC_VERSION 1
#define BOOTREC_NAME_LEN 48
#define BOOTREC_LABEL_LEN 32
#define BOOTREC_IMAGE_MAX 0x02000000u /* also bounded by U-Boot's RAM window */
#define BOOTREC_FDT_MAX 0x3c000u      /* + FDT pad within the 0x40000 window */

enum bootrec_state {
	BOOTREC_VALID = 1,           /* main or previous */
	BOOTREC_TRIAL_ARMED = 2,     /* boot once */
	BOOTREC_TRIAL_CONSUMED = 3,  /* U-Boot took it; never booted again */
};

enum bootrec_error {
	BOOTREC_OK = 0,
	BOOTREC_E_EMPTY = -1,   /* all zero: no record */
	BOOTREC_E_MAGIC = -2,
	BOOTREC_E_VERSION = -3,
	BOOTREC_E_CRC = -4,
	BOOTREC_E_STATE = -5,
	BOOTREC_E_NAME = -6,
	BOOTREC_E_SIZE = -7,
	BOOTREC_E_LABEL = -8,
	BOOTREC_E_PADDING = -9,
};

struct bootrec {
	bootrec_u32 state;
	char image[BOOTREC_NAME_LEN];
	bootrec_u32 image_bytes;
	bootrec_u8 image_sha256[32];
	char fdt[BOOTREC_NAME_LEN];
	bootrec_u32 fdt_bytes;
	bootrec_u8 fdt_sha256[32];
	char label[BOOTREC_LABEL_LEN];
};

bootrec_u32 bootrec_crc32(const bootrec_u8 *data, unsigned int len);
/* Validates everything that does not need the files: 0 or a bootrec_error. */
int bootrec_decode(const bootrec_u8 sector[BOOTREC_SECTOR_BYTES], struct bootrec *rec);
/* Encodes a record (fields as given; validate by decoding the result). */
void bootrec_encode(const struct bootrec *rec, bootrec_u8 sector[BOOTREC_SECTOR_BYTES]);
const char *bootrec_strerror(int error);

#endif
