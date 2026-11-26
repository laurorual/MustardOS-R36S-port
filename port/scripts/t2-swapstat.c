// SPDX-License-Identifier: MIT
// T2 (M7): frame timing of an SDL2 GL program that has no capture of its
// own (standalone Mupen64Plus). LD_PRELOAD wrapper of SDL_GL_SwapWindow:
// once a second it appends "uptime_s swaps max_interval_ms slow vis
// swap_ms" (swap_ms: time spent inside SDL_GL_SwapWindow) to
// $SWAPSTAT_OUT (default /run/swapstat.log); slow = intervals > 20 ms;
// vis = SDL_PumpEvents calls from libmupen64plus (once per emulated VI in
// new_vi(): 60 a second = full speed, whatever the game's own frame rate).
// Built by t2-swapstat.sh; muos-mupen64plus preloads /run/muos/swapstat.so
// only while /run/muos/perf-capture exists.
// M8: while /run/swapstat-grab exists, the next frame (default framebuffer,
// read before the swap) is written to /run/swapstat-grab.ppm and the
// trigger file is removed: screenshots of GL emulators for T2 (also at
// eglSwapBuffers, v1.1.1).
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

// GLES2 entry points by dlsym (no link-time GL dependency)
static void grab(void) {
    void (*get_iv)(unsigned, int *) = (void (*)(unsigned, int *)) dlsym(RTLD_DEFAULT, "glGetIntegerv");
    void (*bind_fb)(unsigned, unsigned) = (void (*)(unsigned, unsigned)) dlsym(RTLD_DEFAULT, "glBindFramebuffer");
    void (*read_px)(int, int, int, int, unsigned, unsigned, void *) =
        (void (*)(int, int, int, int, unsigned, unsigned, void *)) dlsym(RTLD_DEFAULT, "glReadPixels");
    if (!get_iv || !bind_fb || !read_px) return;
    int fb = 0;
    get_iv(0x8CA6 /* GL_FRAMEBUFFER_BINDING */, &fb);
    bind_fb(0x8D40 /* GL_FRAMEBUFFER */, 0);
    const int w = 640, h = 480;
    unsigned char *px = malloc((size_t) w * h * 4);
    FILE *f = px ? fopen("/run/swapstat-grab.ppm", "w") : NULL;
    if (f) {
        read_px(0, 0, w, h, 0x1908 /* GL_RGBA */, 0x1401 /* GL_UNSIGNED_BYTE */, px);
        fprintf(f, "P6\n%d %d\n255\n", w, h);
        for (int y = h - 1; y >= 0; y--)
            for (int x = 0; x < w; x++) fwrite(px + ((size_t) y * w + x) * 4, 1, 3, f);
        fclose(f);
    }
    free(px);
    bind_fb(0x8D40, (unsigned) fb);
}

static void (*real_swap)(void *);
static double last, window_start, max_gap, in_swap;
static unsigned swaps, slow, vis;
static void (*real_pump)(void);
// main_check_inputs() is inlined into several callers: remember every
// return address seen and whether it lies in the core library
static struct { void *at; int core; } sites[16];

void SDL_PumpEvents(void) {
    if (!real_pump) real_pump = (void (*)(void)) dlsym(RTLD_NEXT, "SDL_PumpEvents");
    void *from = __builtin_return_address(0);
    for (unsigned i = 0; i < sizeof(sites) / sizeof(sites[0]); i++) {
        if (!sites[i].at) {
            Dl_info info;
            sites[i].at = from;
            sites[i].core = dladdr(from, &info) && info.dli_fname && strstr(info.dli_fname, "libmupen64plus");
        }
        if (sites[i].at == from) {
            vis += sites[i].core;
            break;
        }
    }
    real_pump();
}
static FILE *out;

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

void SDL_GL_SwapWindow(void *window) {
    if (!real_swap) {
        real_swap = (void (*)(void *)) dlsym(RTLD_NEXT, "SDL_GL_SwapWindow");
        const char *path = getenv("SWAPSTAT_OUT");
        out = fopen(path ? path : "/run/swapstat.log", "a");
        window_start = last = now();
    }
    if (access("/run/swapstat-grab", F_OK) == 0) {
        grab();
        unlink("/run/swapstat-grab");
    }
    const double before = now();
    real_swap(window);
    const double t = now(), gap = t - last;
    in_swap += t - before;
    last = t;
    swaps++;
    if (gap > max_gap) max_gap = gap;
    if (gap > 0.020) slow++;
    if (t - window_start >= 1.0) {
        if (out) {
            fprintf(out, "%.1f %u %.1f %u %u %.0f\n", t, swaps, max_gap * 1000, slow, vis, in_swap * 1000);
            fflush(out);
        }
        window_start = t;
        swaps = slow = vis = 0;
        max_gap = in_swap = 0;
    }
}

// v1.1.1: the same grab for programs that swap through EGL themselves
// (Godot frt ports; the level bar of muos-levelbar.so, preloaded before
// this, is already drawn then).
unsigned eglSwapBuffers(void *dpy, void *surface) {
    static unsigned (*real)(void *, void *);
    if (!real) real = (unsigned (*)(void *, void *)) dlsym(RTLD_NEXT, "eglSwapBuffers");
    if (access("/run/swapstat-grab", F_OK) == 0) {
        grab();
        unlink("/run/swapstat-grab");
    }
    return real ? real(dpy, surface) : 0;
}
