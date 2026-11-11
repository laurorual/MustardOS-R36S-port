// SPDX-License-Identifier: MIT
// Boot record codec for scripts (same bootrec.c as U-Boot).
//   muos-bootrec decode FILE        key=value lines; exit 0 valid, 1 empty, 2 invalid
//   muos-bootrec encode STATE IMAGE IMAGE_BYTES IMAGE_SHA256 FDT FDT_BYTES FDT_SHA256 LABEL OUT
//                                   STATE: valid|trial; OUT gets one 512-byte sector
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "bootrec.h"

static const char *state_name(bootrec_u32 s) {
    switch (s) {
    case BOOTREC_VALID: return "valid";
    case BOOTREC_TRIAL_ARMED: return "trial-armed";
    case BOOTREC_TRIAL_CONSUMED: return "trial-consumed";
    }
    return "?";
}

static int hex32(const char *hex, bootrec_u8 out[32]) {
    if (strlen(hex) != 64) return -1;
    for (int i = 0; i < 32; i++) {
        unsigned v;
        if (sscanf(hex + 2 * i, "%2x", &v) != 1) return -1;
        out[i] = (bootrec_u8)v;
    }
    return 0;
}

static int number(const char *s, bootrec_u32 *out) {
    char *end;
    errno = 0;
    unsigned long v = strtoul(s, &end, 10);
    if (errno || !*s || *end || v > 0xffffffffUL) return -1;
    *out = (bootrec_u32)v;
    return 0;
}

static int copy_field(char *dst, size_t len, const char *src) {
    if (strlen(src) >= len) return -1;
    memset(dst, 0, len);
    memcpy(dst, src, strlen(src));
    return 0;
}

static int do_decode(const char *path) {
    bootrec_u8 s[BOOTREC_SECTOR_BYTES];
    struct bootrec r;
    FILE *f = strcmp(path, "-") ? fopen(path, "rb") : stdin;
    if (!f || fread(s, 1, sizeof(s), f) != sizeof(s)) {
        fprintf(stderr, "cannot read 512 bytes from %s\n", path);
        return 2;
    }
    if (f != stdin) fclose(f);
    int err = bootrec_decode(s, &r);
    if (err) {
        printf("record=%s\n", err == BOOTREC_E_EMPTY ? "empty" : "invalid");
        printf("error=%s\n", bootrec_strerror(err));
        return err == BOOTREC_E_EMPTY ? 1 : 2;
    }
    printf("record=ok\nstate=%s\nimage=%s\nimage_bytes=%u\nimage_sha256=", state_name(r.state),
           r.image, (unsigned)r.image_bytes);
    for (int i = 0; i < 32; i++) printf("%02x", r.image_sha256[i]);
    printf("\nfdt=%s\nfdt_bytes=%u\nfdt_sha256=", r.fdt, (unsigned)r.fdt_bytes);
    for (int i = 0; i < 32; i++) printf("%02x", r.fdt_sha256[i]);
    printf("\nlabel=%s\n", r.label);
    return 0;
}

static int do_encode(char **a) {
    struct bootrec r;
    bootrec_u8 s[BOOTREC_SECTOR_BYTES];
    memset(&r, 0, sizeof(r));
    if (!strcmp(a[0], "valid")) r.state = BOOTREC_VALID;
    else if (!strcmp(a[0], "trial")) r.state = BOOTREC_TRIAL_ARMED;
    else { fprintf(stderr, "state must be valid or trial\n"); return 2; }
    if (copy_field(r.image, sizeof(r.image), a[1]) || number(a[2], &r.image_bytes) ||
        hex32(a[3], r.image_sha256) || copy_field(r.fdt, sizeof(r.fdt), a[4]) ||
        number(a[5], &r.fdt_bytes) || hex32(a[6], r.fdt_sha256) ||
        copy_field(r.label, sizeof(r.label), a[7])) {
        fprintf(stderr, "bad argument\n");
        return 2;
    }
    bootrec_encode(&r, s);
    struct bootrec check;
    int err = bootrec_decode(s, &check);
    if (err) { fprintf(stderr, "record does not validate: %s\n", bootrec_strerror(err)); return 2; }
    FILE *f = fopen(a[8], "wb");
    if (!f || fwrite(s, 1, sizeof(s), f) != sizeof(s) || fclose(f)) {
        fprintf(stderr, "cannot write %s\n", a[8]);
        return 2;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 3 && !strcmp(argv[1], "decode")) return do_decode(argv[2]);
    if (argc == 11 && !strcmp(argv[1], "encode")) return do_encode(argv + 2);
    fprintf(stderr, "usage: muos-bootrec decode FILE | encode STATE IMAGE BYTES SHA FDT BYTES SHA LABEL OUT\n");
    return 2;
}
