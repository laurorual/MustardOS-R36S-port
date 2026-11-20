/* SPDX-License-Identifier: GPL-2.0+ */
/*
 * muOS R35S boot (M3b): boot records instead of compiled-in asset pins.
 * Order: the armed trial record (consumed on the card BEFORE it is tried,
 * so a hang costs one power cycle), then main, then previous. Every asset
 * is size- and SHA256-checked against its record before booti; a failed
 * record falls through to the next one. Never executes an SD script and
 * never writes anything but the trial record sector.
 * M8: quiet LCD. The boot logo (p1 bootlogo.bmp) instead of text; text
 * only for a failure (report, stop_boot).
 */
#include <common.h>
#include <command.h>
#include <blk.h>
#include <memalign.h>
#include <sysmem.h>
#include <linux/libfdt.h>
#include <u-boot/sha256.h>
#include <rockchip_display_cmds.h>
#include "bootrec.h"

#ifndef ram
#define ram(addr) ((void *)(addr)) /* host tests map this to a buffer */
#endif

#define FDT_ADDR 0x01f00000UL
#define FDT_WINDOW 0x00040000UL
#define KERNEL_ADDR 0x02000000UL
/* Bank 0 is DRAM up to 0x08400000 (OP-TEE above). The wide window is
 * tried first; the M2 window (sized for the M2 kernel) is the fallback. */
#define KERNEL_SPAN_WIDE 0x02000000UL
#define KERNEL_SPAN_M2 0x00ec0000UL
#define ARM64_IMAGE_MAGIC 0x644d5241U /* "ARMd" */
#define LOGO_NAME "bootlogo.bmp"
#define LOGO_PIXEL_BYTES (640UL * 480UL * 3UL)
#define LOGO_MAX 0x00200000UL

static ulong kernel_span;
static int lcd_line = 8;

static void stop_boot(const char *reason)
{
	lcd_printf(0, 2, 0, "muOS boot: STOPPED");
	lcd_printf(0, 4, 0, "%s", reason);
	lcd_printf(0, 6, 0, "No kernel started. Hold Power to turn off.");
	panic("muOS boot: %s\n", reason);
}

static void report(const char *slot, const char *what)
{
	printf("muOS boot: %s: %s\n", slot, what);
	if (lcd_line <= 14) {
		lcd_printf(0, lcd_line, 0, "%s: %s", slot, what);
		lcd_line += 2;
	}
}

static u32 get_le32(const u8 *p)
{
	return p[0] | p[1] << 8 | p[2] << 16 | (u32)p[3] << 24;
}

/* The decoder (bmpdecoder) has no bounds checks: only an uncompressed
 * 640x480 24-bit BMP (rows of 1920 bytes, no padding) whose pixel data
 * lies inside the N bytes read may reach it. The header's file-size field
 * is not trusted (one upstream theme logo has it wrong). */
static int logo_valid(const u8 *b, ulong n)
{
	u32 off, height;

	if (n < 54 || b[0] != 'B' || b[1] != 'M')
		return 0;
	off = get_le32(b + 10);
	height = get_le32(b + 22);
	if (get_le32(b + 18) != 640 || (height != 480 && height != (u32)-480))
		return 0;
	if ((b[28] | b[29] << 8) != 24 || get_le32(b + 30) != 0)
		return 0;
	return off >= 54 && off <= n && n - off >= LOGO_PIXEL_BYTES;
}

/* Loaded into the kernel window (reserved, overwritten by the kernel next);
 * a missing or invalid file leaves the screen black. */
static void show_logo(void)
{
	char command[96];
	ulong n;

	if (lcd_init())
		return;
	snprintf(command, sizeof(command), "fatload mmc 1:1 %lx %s %lx",
		 KERNEL_ADDR, LOGO_NAME, LOGO_MAX);
	if (run_command(command, 0)) {
		printf("muOS boot: no %s\n", LOGO_NAME);
		return;
	}
	n = env_get_hex("filesize", 0);
	if (n >= LOGO_MAX || !logo_valid((const u8 *)ram(KERNEL_ADDR), n)) {
		printf("muOS boot: %s is not a 640x480 24-bit BMP\n", LOGO_NAME);
		return;
	}
	if (show_bmp((ulong)ram(KERNEL_ADDR)))
		printf("muOS boot: %s not shown\n", LOGO_NAME);
}

/* Loads NAME (exactly BYTES, read limit BYTES+1 inside WINDOW) and checks
 * its SHA256. A short, long or failed read never reaches booti. */
static const char *load_checked(const char *name, ulong addr, ulong bytes,
				ulong window, const u8 *expected)
{
	char command[160];
	u8 digest[SHA256_SUM_LEN];

	if (bytes >= window)
		return "too large for its RAM window";
	snprintf(command, sizeof(command), "fatload mmc 1:1 %lx %s %lx",
		 addr, name, bytes + 1);
	if (run_command(command, 0) || env_get_hex("filesize", 0) != bytes)
		return "read/size check failed";
	sha256_csum_wd((const unsigned char *)ram(addr), bytes, digest,
		       CHUNKSZ_SHA256);
	if (memcmp(digest, expected, SHA256_SUM_LEN))
		return "SHA256 mismatch";
	return NULL;
}

static const char *check_image_header(void)
{
	const u8 *h = (const u8 *)ram(KERNEL_ADDR);
	u64 text_offset = le64_to_cpu(*(const u64 *)(h + 8));
	u64 image_size = le64_to_cpu(*(const u64 *)(h + 16));

	if (le32_to_cpu(*(const u32 *)(h + 56)) != ARM64_IMAGE_MAGIC)
		return "not an arm64 Image";
	if (!image_size || text_offset + image_size > kernel_span)
		return "Image does not fit the kernel RAM window";
	return NULL;
}

static void try_record(const char *slot, const struct bootrec *rec)
{
	static char saved[512], args[600];
	const char *err;
	const char *old = env_get("bootargs");

	err = load_checked(rec->image, KERNEL_ADDR, rec->image_bytes,
			   kernel_span, rec->image_sha256);
	if (!err)
		err = check_image_header();
	if (!err)
		err = load_checked(rec->fdt, FDT_ADDR, rec->fdt_bytes,
				   FDT_WINDOW - CONFIG_SYS_FDT_PAD,
				   rec->fdt_sha256);
	if (!err && (fdt_check_header(ram(FDT_ADDR)) ||
		     fdt_totalsize(ram(FDT_ADDR)) != rec->fdt_bytes))
		err = "DTB header/size check failed";
	if (err) {
		report(slot, err);
		return;
	}
	if (!old || strlen(old) >= sizeof(saved))
		stop_boot("bootargs missing or too long");
	strcpy(saved, old);
	/* A panicking trial kernel reboots (the trial is consumed: main
	 * boots next); main/previous keep panic=0 (stop, no reboot loop). */
	snprintf(args, sizeof(args), "%s muos_slot=%s%s", saved, slot,
		 strcmp(slot, "trial") ? "" : " panic=10");
	env_set("bootargs", args);
	printf("muOS boot: %s (%s): %s + %s\n", slot, rec->label, rec->image,
	       rec->fdt);
	/* booti checks the header, relocates to 0x02080000 and applies the DT
	 * fixups; the FDT and kernel windows were reserved above. */
	run_command("booti 0x02000000 - 0x01f00000", 0);
	env_set("bootargs", saved);
	report(slot, "kernel handoff returned");
}

/* Reads one record; 0 and REC filled when it decodes with STATE. */
static int read_record(struct blk_desc *desc, lbaint_t sector, u32 state,
		       u8 *buf, struct bootrec *rec, const char *slot)
{
	int err;

	if (blk_dread(desc, sector, 1, buf) != 1) {
		report(slot, "record read failed");
		return -1;
	}
	err = bootrec_decode(buf, rec);
	if (err) {
		if (err != BOOTREC_E_EMPTY)
			report(slot, bootrec_strerror(err));
		return -1;
	}
	return rec->state == state ? 0 : -1;
}

static int do_muos_boot(cmd_tbl_t *cmdtp, int flag, int argc,
			char *const argv[])
{
	ALLOC_CACHE_ALIGN_BUFFER(u8, sector, BOOTREC_SECTOR_BYTES);
	ALLOC_CACHE_ALIGN_BUFFER(u8, check, BOOTREC_SECTOR_BYTES);
	struct blk_desc *desc;
	struct bootrec rec;

	lcd_clear();
	if ((ulong)sysmem_alloc_base_by_name("muos-linux-fdt", FDT_ADDR,
					     FDT_WINDOW) != FDT_ADDR)
		stop_boot("RAM reservation failed (FDT)");
	kernel_span = KERNEL_SPAN_WIDE;
	if ((ulong)sysmem_alloc_base_by_name("muos-kernel", KERNEL_ADDR,
					     kernel_span) != KERNEL_ADDR) {
		kernel_span = KERNEL_SPAN_M2;
		if ((ulong)sysmem_alloc_base_by_name("muos-kernel-m2", KERNEL_ADDR,
						     kernel_span) != KERNEL_ADDR)
			stop_boot("RAM reservation failed (kernel)");
	}
	printf("muOS boot: kernel window %lx\n", kernel_span);
	if (run_command("mmc dev 1", 0))
		stop_boot("SD selection failed");
	desc = blk_get_dev("mmc", 1);
	if (!desc)
		stop_boot("SD block device missing");
	show_logo();

	if (!read_record(desc, BOOTREC_SECTOR_TRIAL, BOOTREC_TRIAL_ARMED,
			 sector, &rec, "trial")) {
		/* Consume first: the trial is never booted twice. */
		rec.state = BOOTREC_TRIAL_CONSUMED;
		bootrec_encode(&rec, sector);
		if (blk_dwrite(desc, BOOTREC_SECTOR_TRIAL, 1, sector) == 1 &&
		    blk_dread(desc, BOOTREC_SECTOR_TRIAL, 1, check) == 1 &&
		    !memcmp(sector, check, BOOTREC_SECTOR_BYTES))
			try_record("trial", &rec);
		else
			report("trial", "could not be consumed: skipped");
	}
	if (!read_record(desc, BOOTREC_SECTOR_MAIN, BOOTREC_VALID, sector,
			 &rec, "main"))
		try_record("main", &rec);
	if (!read_record(desc, BOOTREC_SECTOR_PREVIOUS, BOOTREC_VALID, sector,
			 &rec, "previous"))
		try_record("previous", &rec);
	stop_boot("No bootable record (trial, main, previous)");
	return CMD_RET_FAILURE;
}

U_BOOT_CMD(muos_boot, 1, 0, do_muos_boot,
	   "boot the verified muOS kernel (trial once, main, previous)", "");
