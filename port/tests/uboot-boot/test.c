// SPDX-License-Identifier: MIT
// Host test of the M3b U-Boot boot logic (uboot-boot/boot.c) against mock
// U-Boot APIs: SD sectors, FAT files, RAM, sysmem, env and booti.
//   test OLD_IMAGE OLD_DTB NEW_IMAGE NEW_DTB
#include <setjmp.h>
#include <stdarg.h>
#include "mock.h"
#include "bootrec.h"
#include "boot.c"

unsigned char *mock_ram;
static unsigned char disk[64][512];
static int fail_write, fail_wide, booti_returns, booti_calls, panicked, writes;
static char booted_args[700], panic_msg[200], env_bootargs[700], env_filesize[32];
static int trial_state_at_booti;
static jmp_buf out;

struct file { const char *name; unsigned char *data; size_t len; };
static struct file files[8];
static int nfiles;

// ---- sha256 (FIPS 180-4) ----
static const u32 K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};
#define ROR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))
static void block(u32 h[8], const unsigned char *p) {
    u32 w[64], a[8];
    for (int i = 0; i < 16; i++) w[i] = (u32)p[4 * i] << 24 | p[4 * i + 1] << 16 | p[4 * i + 2] << 8 | p[4 * i + 3];
    for (int i = 16; i < 64; i++)
        w[i] = w[i - 16] + (ROR(w[i - 15], 7) ^ ROR(w[i - 15], 18) ^ (w[i - 15] >> 3)) + w[i - 7] +
               (ROR(w[i - 2], 17) ^ ROR(w[i - 2], 19) ^ (w[i - 2] >> 10));
    memcpy(a, h, sizeof(a));
    for (int i = 0; i < 64; i++) {
        u32 t1 = a[7] + (ROR(a[4], 6) ^ ROR(a[4], 11) ^ ROR(a[4], 25)) + ((a[4] & a[5]) ^ (~a[4] & a[6])) + K[i] + w[i];
        u32 t2 = (ROR(a[0], 2) ^ ROR(a[0], 13) ^ ROR(a[0], 22)) + ((a[0] & a[1]) ^ (a[0] & a[2]) ^ (a[1] & a[2]));
        memmove(a + 1, a, 7 * sizeof(u32));
        a[4] += t1;
        a[0] = t1 + t2;
    }
    for (int i = 0; i < 8; i++) h[i] += a[i];
}
void sha256_csum_wd(const unsigned char *in, unsigned int len, unsigned char *outd, unsigned int chunk) {
    (void)chunk;
    u32 h[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
    unsigned char tail[128] = {0};
    size_t full = len / 64 * 64, rem = len - full;
    for (size_t i = 0; i < full; i += 64) block(h, in + i);
    memcpy(tail, in + full, rem);
    tail[rem] = 0x80;
    size_t tl = rem < 56 ? 64 : 128;
    u64 bits = (u64)len * 8;
    for (int i = 0; i < 8; i++) tail[tl - 1 - i] = (unsigned char)(bits >> (8 * i));
    for (size_t i = 0; i < tl; i += 64) block(h, tail + i);
    for (int i = 0; i < 8; i++) for (int j = 0; j < 4; j++) outd[4 * i + j] = (unsigned char)(h[i] >> (24 - 8 * j));
}

// ---- mocks ----
static const char *slot_of(const char *args) {
    static char s[16];
    const char *p = strstr(args, "muos_slot=");
    if (!p) return "?";
    sscanf(p + 10, "%15s", s);
    return s;
}
int run_command(const char *cmd, int flag) {
    (void)flag;
    ulong addr, max;
    char name[64];
    if (!strcmp(cmd, "mmc dev 1")) return 0;
    if (sscanf(cmd, "fatload mmc 1:1 %lx %63s %lx", &addr, name, &max) == 3) {
        for (int i = 0; i < nfiles; i++)
            if (!strcmp(files[i].name, name)) {
                size_t n = files[i].len < max ? files[i].len : max;
                memcpy(mock_ram + addr, files[i].data, n);
                snprintf(env_filesize, sizeof(env_filesize), "%zx", n);
                return 0;
            }
        return 1;
    }
    if (!strcmp(cmd, "booti 0x02000000 - 0x01f00000")) {
        struct bootrec r;
        booti_calls++;
        trial_state_at_booti = bootrec_decode(disk[BOOTREC_SECTOR_TRIAL], &r) ? 0 : (int)r.state;
        if (booti_returns) { booti_returns--; return 1; }
        snprintf(booted_args, sizeof(booted_args), "%s", env_bootargs);
        longjmp(out, 1);
    }
    fprintf(stderr, "unexpected command: %s\n", cmd);
    abort();
}
char *env_get(const char *n) { return !strcmp(n, "bootargs") ? env_bootargs : NULL; }
int env_set(const char *n, const char *v) {
    if (strcmp(n, "bootargs")) abort();
    snprintf(env_bootargs, sizeof(env_bootargs), "%s", v);
    return 0;
}
ulong env_get_hex(const char *n, ulong def) { return strcmp(n, "filesize") ? def : strtoul(env_filesize, NULL, 16); }
void *sysmem_alloc_base_by_name(const char *n, ulong base, ulong size) {
    (void)n;
    return fail_wide && size == 0x02000000UL ? NULL : (void *)base;
}
static struct blk_desc sd = {1};
struct blk_desc *blk_get_dev(const char *i, int d) { return !strcmp(i, "mmc") && d == 1 ? &sd : NULL; }
ulong blk_dread(struct blk_desc *d, lbaint_t s, lbaint_t c, void *b) {
    (void)d;
    if (s + c > 64) return 0;
    memcpy(b, disk[s], c * 512);
    return c;
}
ulong blk_dwrite(struct blk_desc *d, lbaint_t s, lbaint_t c, const void *b) {
    (void)d;
    writes++;
    if (fail_write || s != BOOTREC_SECTOR_TRIAL) return 0;
    memcpy(disk[s], b, c * 512);
    return c;
}
static u32 be32(const unsigned char *p) { return (u32)p[0] << 24 | p[1] << 16 | p[2] << 8 | p[3]; }
int fdt_check_header(const void *f) { return be32(f) == 0xd00dfeed ? 0 : -1; }
u32 fdt_totalsize(const void *f) { return be32((const unsigned char *)f + 4); }
void lcd_clear(void) {}
void lcd_printf(int x, int y, int s, const char *fmt, ...) { (void)x; (void)y; (void)s; (void)fmt; }
void panic(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(panic_msg, sizeof(panic_msg), fmt, ap);
    va_end(ap);
    panicked = 1;
    longjmp(out, 1);
}

// ---- harness ----
static unsigned char *slurp(const char *path, size_t *len) {
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); exit(2); }
    fseek(f, 0, SEEK_END);
    *len = (size_t)ftell(f);
    rewind(f);
    unsigned char *d = malloc(*len);
    if (fread(d, 1, *len, f) != *len) exit(2);
    fclose(f);
    return d;
}
static void add_file(const char *name, unsigned char *data, size_t len) {
    files[nfiles].name = name; files[nfiles].data = data; files[nfiles].len = len; nfiles++;
}
static struct file *find(const char *name) {
    for (int i = 0; i < nfiles; i++) if (!strcmp(files[i].name, name)) return &files[i];
    abort();
}
static void put_record(int sector, u32 state, const char *image, const char *fdt, const char *label) {
    struct bootrec r;
    memset(&r, 0, sizeof(r));
    struct file *i = find(image), *f = find(fdt);
    r.state = state;
    strcpy(r.image, image); r.image_bytes = (u32)i->len; sha256_csum_wd(i->data, (unsigned)i->len, r.image_sha256, 0);
    strcpy(r.fdt, fdt); r.fdt_bytes = (u32)f->len; sha256_csum_wd(f->data, (unsigned)f->len, r.fdt_sha256, 0);
    strcpy(r.label, label);
    bootrec_encode(&r, disk[sector]);
}
static void reset(void) {
    memset(disk, 0, sizeof(disk));
    fail_write = fail_wide = booti_returns = booti_calls = panicked = writes = 0;
    trial_state_at_booti = 0;
    booted_args[0] = panic_msg[0] = 0;
    lcd_line = 8;
    strcpy(env_bootargs, "console=tty0 root=PARTUUID=4d554432-02 ro panic=0");
}
static void reboot_env(void) { // a fresh boot: env and LCD reset, the SD card kept
    strcpy(env_bootargs, "console=tty0 root=PARTUUID=4d554432-02 ro panic=0");
    booted_args[0] = 0; lcd_line = 8;
}
static int run(void) {
    char *argv[] = {"muos_boot", NULL};
    if (!setjmp(out)) muos_cmd_entry(NULL, 0, 1, argv);
    return 0;
}
static int failures;
static void expect(const char *name, int ok) {
    printf("%s %s\n", ok ? "ok  " : "FAIL", name);
    failures += !ok;
}
static int trial_state(void) {
    struct bootrec r;
    return bootrec_decode(disk[BOOTREC_SECTOR_TRIAL], &r) ? 0 : (int)r.state;
}

int main(int argc, char **argv) {
    if (argc != 5) { fprintf(stderr, "usage: test OLD_IMAGE OLD_DTB NEW_IMAGE NEW_DTB\n"); return 2; }
    mock_ram = calloc(1, 0x04100000);
    size_t n;
    unsigned char *d;
    d = slurp(argv[1], &n); add_file("Image", d, n);
    d = slurp(argv[2], &n); add_file("rk3326-muos-r35s-panel0.dtb", d, n);
    d = slurp(argv[3], &n); add_file("Image-new", d, n);
    d = slurp(argv[4], &n); add_file("panel0-new.dtb", d, n);
    // A kernel whose header needs more than the M2 window.
    unsigned char *big = malloc(find("Image")->len);
    memcpy(big, find("Image")->data, find("Image")->len);
    u64 isz = 0xf00000; memcpy(big + 16, &isz, 8);
    add_file("Image-big", big, find("Image")->len);
    // Same name as main's Image but different content (stale file on p1).
    unsigned char *bad = malloc(find("Image")->len);
    memcpy(bad, find("Image")->data, find("Image")->len); bad[1000] ^= 1;

    reset(); put_record(32, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2");
    put_record(33, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2"); run();
    expect("main boots", !panicked && !strcmp(slot_of(booted_args), "main") && writes == 0);
    expect("main keeps panic=0 only", strstr(booted_args, "panic=10") == NULL);

    reset(); put_record(32, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2");
    put_record(34, BOOTREC_TRIAL_ARMED, "Image-new", "panel0-new.dtb", "rng"); run();
    expect("armed trial boots once", !strcmp(slot_of(booted_args), "trial"));
    expect("trial consumed before booti", trial_state_at_booti == BOOTREC_TRIAL_CONSUMED);
    expect("trial gets panic=10 after panic=0", strstr(booted_args, "panic=0 muos_slot=trial panic=10") != NULL);
    reboot_env(); run();
    expect("next boot after a trial is main", !strcmp(slot_of(booted_args), "main"));

    reset(); put_record(32, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2");
    put_record(34, BOOTREC_TRIAL_ARMED, "Image-new", "panel0-new.dtb", "rng");
    find("Image-new")->data[500] ^= 1; run(); find("Image-new")->data[500] ^= 1;
    expect("corrupt trial asset -> consumed, main boots",
           !strcmp(slot_of(booted_args), "main") && trial_state() == BOOTREC_TRIAL_CONSUMED);
    expect("bootargs carry one muos_slot", strstr(strstr(booted_args, "muos_slot=") + 1, "muos_slot=") == NULL);

    reset(); put_record(32, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2");
    put_record(34, BOOTREC_TRIAL_ARMED, "Image-new", "panel0-new.dtb", "rng"); fail_write = 1; run();
    expect("unconsumable trial is skipped", !strcmp(slot_of(booted_args), "main") && booti_calls == 1);

    reset(); put_record(32, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2");
    put_record(34, BOOTREC_TRIAL_CONSUMED, "Image-new", "panel0-new.dtb", "rng"); run();
    expect("consumed trial never boots", !strcmp(slot_of(booted_args), "main") && writes == 0);

    reset(); put_record(32, BOOTREC_VALID, "Image-new", "panel0-new.dtb", "rng");
    put_record(33, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2");
    disk[32][200] ^= 1; run();
    expect("corrupt main record -> previous", !strcmp(slot_of(booted_args), "previous"));

    reset(); put_record(32, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2");
    put_record(33, BOOTREC_VALID, "Image-new", "panel0-new.dtb", "rng");
    unsigned char *keep = find("Image")->data; find("Image")->data = bad; run(); find("Image")->data = keep;
    expect("stale main file (SHA mismatch) -> previous", !strcmp(slot_of(booted_args), "previous"));

    reset(); put_record(32, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2");
    put_record(33, BOOTREC_VALID, "Image-new", "panel0-new.dtb", "rng");
    unsigned char *plus = calloc(1, find("Image")->len + 1);
    memcpy(plus, keep, find("Image")->len);
    find("Image")->data = plus; find("Image")->len += 1; run();
    find("Image")->len -= 1; find("Image")->data = keep;
    expect("oversized main file -> previous", !strcmp(slot_of(booted_args), "previous"));

    reset(); put_record(32, BOOTREC_VALID, "Image-big", "rk3326-muos-r35s-panel0.dtb", "big");
    put_record(33, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2"); run();
    expect("wide window boots a kernel beyond 0xec0000", !strcmp(slot_of(booted_args), "main"));
    reset(); put_record(32, BOOTREC_VALID, "Image-big", "rk3326-muos-r35s-panel0.dtb", "big");
    put_record(33, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2"); fail_wide = 1; run();
    expect("M2 window rejects it -> previous", !strcmp(slot_of(booted_args), "previous") && kernel_span == 0xec0000);

    reset(); put_record(32, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2");
    put_record(33, BOOTREC_VALID, "Image-new", "panel0-new.dtb", "rng"); booti_returns = 1; run();
    expect("failed booti restores bootargs, previous boots",
           !strcmp(slot_of(booted_args), "previous") && booti_calls == 2 &&
           strstr(booted_args, "muos_slot=main") == NULL);

    reset(); run();
    expect("no records -> stop", panicked && strstr(panic_msg, "No bootable record") != NULL && booti_calls == 0);

    reset(); put_record(32, BOOTREC_VALID, "Image", "panel0-new.dtb", "mixed");
    put_record(33, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2");
    files[3].name = "panel0-gone.dtb"; run(); files[3].name = "panel0-new.dtb";
    expect("missing DTB file -> previous", !strcmp(slot_of(booted_args), "previous"));

    // A record whose DTB is not a DTB: header check.
    reset(); put_record(32, BOOTREC_VALID, "Image", "Image-new", "x");
    put_record(33, BOOTREC_VALID, "Image", "rk3326-muos-r35s-panel0.dtb", "m2"); run();
    expect("non-DTB rejected (size or header) -> previous", !strcmp(slot_of(booted_args), "previous"));

    printf("%s: %d failure(s)\n", failures ? "FAIL" : "PASS", failures);
    return failures != 0;
}
