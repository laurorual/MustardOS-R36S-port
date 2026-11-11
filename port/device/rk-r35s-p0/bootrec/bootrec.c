/* SPDX-License-Identifier: GPL-2.0+ OR MIT */
/* muOS R35S boot records; see bootrec.h. No allocation, no libc beyond
 * memcpy/memset/memcmp, so the same file builds into U-Boot. */
#ifdef __UBOOT__
#include <common.h>
#else
#include <string.h>
#endif
#include "bootrec.h"

#define OFF_MAGIC 0
#define OFF_VERSION 8
#define OFF_STATE 12
#define OFF_IMAGE 16
#define OFF_IMAGE_BYTES 64
#define OFF_IMAGE_SHA 68
#define OFF_FDT 100
#define OFF_FDT_BYTES 148
#define OFF_FDT_SHA 152
#define OFF_LABEL 184
#define OFF_END 216
#define OFF_CRC 508

static const char magic[8] = { 'M', 'U', 'O', 'S', 'B', 'R', 'E', 'C' };

bootrec_u32 bootrec_crc32(const bootrec_u8 *data, unsigned int len)
{
	/* zlib/IEEE CRC-32, bitwise (512 bytes per call: no table needed). */
	bootrec_u32 crc = 0xffffffffu;
	unsigned int i, bit;

	for (i = 0; i < len; i++) {
		crc ^= data[i];
		for (bit = 0; bit < 8; bit++)
			crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
	}
	return ~crc;
}

static bootrec_u32 get32(const bootrec_u8 *p)
{
	return (bootrec_u32)p[0] | (bootrec_u32)p[1] << 8 |
	       (bootrec_u32)p[2] << 16 | (bootrec_u32)p[3] << 24;
}

static void put32(bootrec_u8 *p, bootrec_u32 v)
{
	p[0] = v & 0xff;
	p[1] = (v >> 8) & 0xff;
	p[2] = (v >> 16) & 0xff;
	p[3] = (v >> 24) & 0xff;
}

/* A file name on p1: [A-Za-z0-9._-], not starting with '.', NUL-terminated
 * inside the field, NUL-padded after it. */
static int check_name(const bootrec_u8 *field, char *out)
{
	unsigned int i, n = 0;

	while (n < BOOTREC_NAME_LEN && field[n])
		n++;
	if (n == 0 || n == BOOTREC_NAME_LEN || field[0] == '.')
		return BOOTREC_E_NAME;
	for (i = 0; i < n; i++) {
		bootrec_u8 c = field[i];
		if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
		      (c >= '0' && c <= '9') || c == '.' || c == '_' || c == '-'))
			return BOOTREC_E_NAME;
	}
	for (i = n; i < BOOTREC_NAME_LEN; i++)
		if (field[i])
			return BOOTREC_E_NAME;
	memcpy(out, field, BOOTREC_NAME_LEN);
	return BOOTREC_OK;
}

static int check_label(const bootrec_u8 *field, char *out)
{
	unsigned int i, n = 0;

	while (n < BOOTREC_LABEL_LEN && field[n])
		n++;
	if (n == BOOTREC_LABEL_LEN)
		return BOOTREC_E_LABEL;
	for (i = 0; i < n; i++)
		if (field[i] < 0x20 || field[i] > 0x7e)
			return BOOTREC_E_LABEL;
	for (i = n; i < BOOTREC_LABEL_LEN; i++)
		if (field[i])
			return BOOTREC_E_LABEL;
	memcpy(out, field, BOOTREC_LABEL_LEN);
	return BOOTREC_OK;
}

int bootrec_decode(const bootrec_u8 s[BOOTREC_SECTOR_BYTES], struct bootrec *rec)
{
	unsigned int i;
	int err;

	for (i = 0; i < BOOTREC_SECTOR_BYTES && !s[i]; i++)
		;
	if (i == BOOTREC_SECTOR_BYTES)
		return BOOTREC_E_EMPTY;
	if (memcmp(s + OFF_MAGIC, magic, sizeof(magic)))
		return BOOTREC_E_MAGIC;
	if (get32(s + OFF_VERSION) != BOOTREC_VERSION)
		return BOOTREC_E_VERSION;
	if (get32(s + OFF_CRC) != bootrec_crc32(s, OFF_CRC))
		return BOOTREC_E_CRC;
	for (i = OFF_END; i < OFF_CRC; i++)
		if (s[i])
			return BOOTREC_E_PADDING;
	memset(rec, 0, sizeof(*rec));
	rec->state = get32(s + OFF_STATE);
	if (rec->state < BOOTREC_VALID || rec->state > BOOTREC_TRIAL_CONSUMED)
		return BOOTREC_E_STATE;
	err = check_name(s + OFF_IMAGE, rec->image);
	if (!err)
		err = check_name(s + OFF_FDT, rec->fdt);
	if (!err)
		err = check_label(s + OFF_LABEL, rec->label);
	if (err)
		return err;
	rec->image_bytes = get32(s + OFF_IMAGE_BYTES);
	rec->fdt_bytes = get32(s + OFF_FDT_BYTES);
	if (rec->image_bytes < 64 || rec->image_bytes > BOOTREC_IMAGE_MAX ||
	    rec->fdt_bytes < 64 || rec->fdt_bytes > BOOTREC_FDT_MAX)
		return BOOTREC_E_SIZE;
	memcpy(rec->image_sha256, s + OFF_IMAGE_SHA, 32);
	memcpy(rec->fdt_sha256, s + OFF_FDT_SHA, 32);
	return BOOTREC_OK;
}

void bootrec_encode(const struct bootrec *rec, bootrec_u8 s[BOOTREC_SECTOR_BYTES])
{
	unsigned int n;

	memset(s, 0, BOOTREC_SECTOR_BYTES);
	memcpy(s + OFF_MAGIC, magic, sizeof(magic));
	put32(s + OFF_VERSION, BOOTREC_VERSION);
	put32(s + OFF_STATE, rec->state);
	for (n = 0; n < BOOTREC_NAME_LEN - 1 && rec->image[n]; n++)
		s[OFF_IMAGE + n] = rec->image[n];
	put32(s + OFF_IMAGE_BYTES, rec->image_bytes);
	memcpy(s + OFF_IMAGE_SHA, rec->image_sha256, 32);
	for (n = 0; n < BOOTREC_NAME_LEN - 1 && rec->fdt[n]; n++)
		s[OFF_FDT + n] = rec->fdt[n];
	put32(s + OFF_FDT_BYTES, rec->fdt_bytes);
	memcpy(s + OFF_FDT_SHA, rec->fdt_sha256, 32);
	for (n = 0; n < BOOTREC_LABEL_LEN - 1 && rec->label[n]; n++)
		s[OFF_LABEL + n] = rec->label[n];
	put32(s + OFF_CRC, bootrec_crc32(s, OFF_CRC));
}

const char *bootrec_strerror(int error)
{
	switch (error) {
	case BOOTREC_OK: return "ok";
	case BOOTREC_E_EMPTY: return "empty";
	case BOOTREC_E_MAGIC: return "bad magic";
	case BOOTREC_E_VERSION: return "bad version";
	case BOOTREC_E_CRC: return "bad crc";
	case BOOTREC_E_STATE: return "bad state";
	case BOOTREC_E_NAME: return "bad file name";
	case BOOTREC_E_SIZE: return "bad size";
	case BOOTREC_E_LABEL: return "bad label";
	case BOOTREC_E_PADDING: return "non-zero padding";
	}
	return "unknown";
}
