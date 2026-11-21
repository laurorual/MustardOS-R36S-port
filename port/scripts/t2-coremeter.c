// SPDX-License-Identifier: MIT
// T2 (M8e): libretro core speed meter, LD_PRELOAD into muxretro (the
// muos-frontend T2 hook preloads /run/muos/coremeter.so while
// /run/muos/perf-capture exists). It wraps dlsym: the core's
// retro_set_audio_sample_batch / retro_set_audio_sample / retro_set_video_refresh
// get counting callbacks in front of muxretro's. Once a second it appends
// "uptime_s audio_frames video_frames dupes" to /run/coremeter.log:
// audio frames per second at the core's own rate (44100 = full speed for
// Flycast) are the game's real speed whatever the core's threading.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

typedef size_t (*batch_t)(const int16_t *, size_t);
typedef void (*sample_t)(int16_t, int16_t);
typedef void (*video_t)(const void *, unsigned, unsigned, size_t);
static batch_t fe_batch; static sample_t fe_sample; static video_t fe_video;
static void (*set_batch)(batch_t); static void (*set_sample)(sample_t); static void (*set_video)(video_t);
static atomic_ulong n_audio, n_video, n_dupe;
static void *(*real_dlsym)(void *, const char *);

static size_t my_batch(const int16_t *d, size_t f) { atomic_fetch_add(&n_audio, f); return fe_batch(d, f); }
static void my_sample(int16_t l, int16_t r) { atomic_fetch_add(&n_audio, 1); fe_sample(l, r); }
static void my_video(const void *d, unsigned w, unsigned h, size_t p) {
    atomic_fetch_add(d ? &n_video : &n_dupe, 1); fe_video(d, w, h, p);
}
static void my_set_batch(batch_t cb) { fe_batch = cb; set_batch(my_batch); }
static void my_set_sample(sample_t cb) { fe_sample = cb; set_sample(my_sample); }
static void my_set_video(video_t cb) { fe_video = cb; set_video(my_video); }

static void *logger(void *arg) {
    (void) arg;
    for (;;) {
        sleep(1);
        unsigned long a = atomic_exchange(&n_audio, 0), v = atomic_exchange(&n_video, 0), d = atomic_exchange(&n_dupe, 0);
        struct timespec ts; clock_gettime(CLOCK_BOOTTIME, &ts);
        FILE *f = fopen("/run/coremeter.log", "a");
        if (f) { fprintf(f, "%ld.%02ld %lu %lu %lu\n", (long) ts.tv_sec, ts.tv_nsec / 10000000, a, v, d); fclose(f); }
    }
    return NULL;
}

// dlsym is entered by a tail jump to glibc's own: glibc resolves RTLD_NEXT
// from the return address, which must stay the original caller's. Only the
// three setters are answered here (by handle, never RTLD_NEXT).
__attribute__((visibility("hidden"))) void *cm_real(void) {
    if (!real_dlsym) {
        real_dlsym = (void *(*)(void *, const char *)) dlvsym(RTLD_NEXT, "dlsym", "GLIBC_2.34");
        if (!real_dlsym) real_dlsym = (void *(*)(void *, const char *)) dlvsym(RTLD_NEXT, "dlsym", "GLIBC_2.17");
    }
    return (void *) real_dlsym;
}

__attribute__((visibility("hidden"))) void *cm_special(void *h, const char *name) {
    if (!name || h == RTLD_NEXT || h == RTLD_DEFAULT) return NULL;
    int which = !strcmp(name, "retro_set_audio_sample_batch") ? 1 : !strcmp(name, "retro_set_audio_sample") ? 2
              : !strcmp(name, "retro_set_video_refresh") ? 3 : 0;
    if (!which) return NULL;
    cm_real();
    void *p = real_dlsym(h, name);
    if (!p) return NULL;
    if (which == 1) { set_batch = p; return (void *) my_set_batch; }
    if (which == 2) { set_sample = p; return (void *) my_set_sample; }
    set_video = p;
    static int started; pthread_t t;
    if (!started && pthread_create(&t, NULL, logger, NULL) == 0) { pthread_detach(t); started = 1; }
    return (void *) my_set_video;
}

__asm__(".text\n.globl dlsym\n.type dlsym, %function\ndlsym:\n"
        "  stp x29, x30, [sp, -32]!\n  mov x29, sp\n  stp x0, x1, [sp, 16]\n"
        "  bl cm_special\n  cbnz x0, 1f\n"
        "  bl cm_real\n  mov x16, x0\n  ldp x0, x1, [sp, 16]\n  ldp x29, x30, [sp], 32\n  br x16\n"
        "1:\n  ldp x29, x30, [sp], 32\n  ret\n.size dlsym, .-dlsym\n");
