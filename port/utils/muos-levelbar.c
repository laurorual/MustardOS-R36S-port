// SPDX-License-Identifier: MIT
// muOS R35S port (v1.1.1 T3): the volume/brightness level bar for programs
// muxretro does not run (PortMaster ports, applications, the official
// PICO-8), preloaded by muos-frontend. A volume or brightness key changes
// config/settings/general/{volume,brightness} (muhotkey -> muos-volume-step
// / bright.sh); this checks them every 100 ms at the app's frame swap and
// for 1.5 s after a change draws a panel with the level at the top of the
// screen, as muxretro's in-game bar (patch 0002), from rectangles only:
//   SDL_GL_SwapWindow / eglSwapBuffers: scissored glClear on the default
//     framebuffer (GL state saved and restored)
//   SDL_RenderPresent: SDL_RenderFillRect (draw colour, blend mode, clip,
//     viewport and scale saved and restored; not on a render target)
// No SDL/GL headers or link: the hooked and used functions are looked up at
// run time, so it adds nothing to a program that never swaps. Programs that
// load SDL2 or EGL with dlopen and look the functions up with dlsym (Godot
// frt, PortMaster's pysdl2 GUI) get the wrappers from dlsym itself: this
// exports dlsym, returns the wrapper for the three swap functions on a
// library handle and passes everything else to libc's dlsym with a tail
// jump (an aarch64 trampoline, so dlsym(RTLD_NEXT) keeps its caller).
// T2: while /run/muos/levelbar-grab exists, the next frame (with the bar)
// goes to /run/muos/levelbar-grab.ppm and the trigger is removed. Each
// process logs the first swap hook it goes through to stderr.
// Nothing is shown just after a resume (/run/muos/recent_wake): restoring
// the levels is not a key press.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define CONF "/opt/muos/config/"
#define DEV  "/opt/muos/device/config/"
#define HOLD_MS 1500
#define POLL_MS 100

typedef struct { int x, y, w, h; } rect_t;
enum { VOLUME, BRIGHT };

static struct level {
    const char *path;
    long long mtime;
    int value, known;
} levels[2] = {{CONF "settings/general/volume", 0, 0, 0}, {CONF "settings/general/brightness", 0, 0, 0}};

static int shown_kind, shown_pct;
static uint64_t shown_at, polled_at;
static int visible, grab_pending;
// set while an SDL wrapper runs the real function: SDL swaps through the
// eglSwapBuffers it looked up with dlsym (the wrapper), already drawn then
static __thread int in_sdl;

static uint64_t now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t) ts.tv_sec * 1000u + (uint64_t) ts.tv_nsec / 1000000u;
}

#include <stdarg.h>
// T2 diagnostics while /run/muos/levelbar-debug exists: appended to
// /run/muos/levelbar-debug.log (some programs close or redirect stderr)
static void dbg(const char *fmt, ...) {
    static int on = -1;
    if (on < 0) on = access("/run/muos/levelbar-debug", F_OK) == 0;
    if (!on) return;
    FILE *f = fopen("/run/muos/levelbar-debug.log", "ae");
    if (!f) return;
    fprintf(f, "%d: ", (int) getpid());
    va_list ap;
    va_start(ap, fmt);
    vfprintf(f, fmt, ap);
    va_end(ap);
    fputc('\n', f);
    fclose(f);
}

static int read_int(const char *path, const int fallback) {
    FILE *f = fopen(path, "re");
    if (!f) return fallback;
    int v;
    const int ok = fscanf(f, "%d", &v) == 1;
    fclose(f);
    return ok ? v : fallback;
}

static int percent(const int kind, const int v) {
    int max;
    if (kind == VOLUME) {
        max = read_int(CONF "settings/advanced/overdrive", 0) == 1 ? 200 : read_int(DEV "audio/max", 100);
    } else {
        max = read_int(DEV "screen/bright", 100);
    }
    if (max <= 0) max = 100;
    const int p = v * 100 / max;
    return p < 0 ? 0 : p > 100 ? 100 : p;
}

// Once per POLL_MS: a changed level file (mtime) with a new value shows it.
static void poll_levels(void) {
    const uint64_t t = now_ms();
    if (visible && t - shown_at >= HOLD_MS) visible = 0;
    if (polled_at && t - polled_at < POLL_MS) return;
    polled_at = t;
    grab_pending = access("/run/muos/levelbar-grab", F_OK) == 0;
    for (int k = 0; k < 2; k++) {
        struct level *l = &levels[k];
        struct stat st;
        if (stat(l->path, &st) != 0) continue;
        const long long m = (long long) st.st_mtim.tv_sec * 1000000000LL + st.st_mtim.tv_nsec;
        if (l->known && m == l->mtime) continue;
        const int v = read_int(l->path, -1);
        l->mtime = m;
        if (v < 0) continue;
        const int changed = l->known && v != l->value;
        l->value = v;
        l->known = 1;
        if (changed && access("/run/muos/recent_wake", F_OK) != 0) {
            shown_kind = k;
            shown_pct = percent(k, v);
            shown_at = t;
            visible = 1;
        }
    }
}

// The bar's rectangles in a W x H surface (y down) and their colours.
#define MAX_RECTS 12
static int layout(const int W, const int H, rect_t *r, uint32_t *c) {
    int n = 0;
    const int s = H >= 480 ? H / 480 : 1;
    const int pw = W * 11 / 20, ph = 36 * s, px = (W - pw) / 2, py = 12 * s, b = 2 * s;
#define R(X, Y, WW, HH, C) (r[n] = (rect_t) {(X), (Y), (WW), (HH)}, c[n++] = (C))
    R(px, py, pw, ph, 0xE0E0E0u);                                // border
    R(px + b, py + b, pw - 2 * b, ph - 2 * b, 0x202020u);       // panel
    // icon, 20x20 at the left: a speaker (volume) or a sun (brightness)
    const int ix = px + 10 * s, iy = py + (ph - 20 * s) / 2;
    if (shown_kind == VOLUME) {
        R(ix, iy + 7 * s, 5 * s, 6 * s, 0xE0E0E0u);
        R(ix + 5 * s, iy + 4 * s, 3 * s, 12 * s, 0xE0E0E0u);
        R(ix + 8 * s, iy + 1 * s, 3 * s, 18 * s, 0xE0E0E0u);
        if (shown_pct > 0) R(ix + 14 * s, iy + 6 * s, 2 * s, 8 * s, 0xE0E0E0u);
        if (shown_pct > 50) R(ix + 18 * s, iy + 3 * s, 2 * s, 14 * s, 0xE0E0E0u);
    } else {
        R(ix + 5 * s, iy + 5 * s, 10 * s, 10 * s, 0xE0E0E0u);
        R(ix + 9 * s, iy, 2 * s, 3 * s, 0xE0E0E0u);
        R(ix + 9 * s, iy + 17 * s, 2 * s, 3 * s, 0xE0E0E0u);
        R(ix, iy + 9 * s, 3 * s, 2 * s, 0xE0E0E0u);
        R(ix + 17 * s, iy + 9 * s, 3 * s, 2 * s, 0xE0E0E0u);
    }
    // progress: track and fill
    const int tx = ix + 32 * s, tw = px + pw - 14 * s - tx, th = 10 * s, ty = py + (ph - th) / 2;
    R(tx, ty, tw, th, 0x505050u);
    if (shown_pct > 0) R(tx, ty, tw * shown_pct / 100, th, 0xF0F0F0u);
#undef R
    return n;
}

// ---- dlsym --------------------------------------------------------------
void *levelbar_real_dlsym __attribute__((visibility("hidden")));
static void *(*real_dlsym)(void *, const char *);
static void *sdl_lib, *egl_lib; // the handles the hooked functions came from
static void (*real_gl_swap)(void *), (*real_present)(void *);
static unsigned (*real_egl_swap)(void *, void *);
void SDL_GL_SwapWindow(void *window);
void SDL_RenderPresent(void *renderer);
unsigned eglSwapBuffers(void *dpy, void *surface);

static void load_dlsym(void) {
    if (real_dlsym) return;
    void *p = dlvsym(RTLD_NEXT, "dlsym", "GLIBC_2.34");
    if (!p) p = dlvsym(RTLD_NEXT, "dlsym", "GLIBC_2.17");
    levelbar_real_dlsym = p;
    *(void **) &real_dlsym = p;
}

// From the trampoline: the wrapper to return, or NULL to pass the call on.
__attribute__((visibility("hidden"))) void *levelbar_dlsym_hook(void *handle, const char *name) {
    load_dlsym();
    if (!real_dlsym || !name || handle == RTLD_NEXT || handle == RTLD_DEFAULT) return NULL;
    if (strcmp(name, "SDL_GL_SwapWindow") && strcmp(name, "SDL_RenderPresent") && strcmp(name, "eglSwapBuffers"))
        return NULL;
    void *p = real_dlsym(handle, name);
    if (!p) return NULL;
    if (!strcmp(name, "eglSwapBuffers")) {
        if (p == (void *) eglSwapBuffers) return NULL;
        egl_lib = handle;
        *(void **) &real_egl_swap = p;
        return (void *) eglSwapBuffers;
    }
    if (p == (void *) SDL_GL_SwapWindow || p == (void *) SDL_RenderPresent) return NULL;
    sdl_lib = handle;
    if (name[4] == 'G') {
        *(void **) &real_gl_swap = p;
        return (void *) SDL_GL_SwapWindow;
    }
    *(void **) &real_present = p;
    return (void *) SDL_RenderPresent;
}

__asm__(".text\n"
        ".globl dlsym\n"
        ".type dlsym, %function\n"
        "dlsym:\n"
        "    stp x29, x30, [sp, #-32]!\n"
        "    mov x29, sp\n"
        "    stp x0, x1, [sp, #16]\n"
        "    bl levelbar_dlsym_hook\n"
        "    cbnz x0, 1f\n"
        "    ldp x0, x1, [sp, #16]\n"
        "    ldp x29, x30, [sp], #32\n"
        "    adrp x16, levelbar_real_dlsym\n"
        "    ldr x16, [x16, #:lo12:levelbar_real_dlsym]\n"
        "    cbz x16, 2f\n"
        "    br x16\n"
        "1:  ldp x29, x30, [sp], #32\n"
        "2:  ret\n"
        ".size dlsym, .-dlsym\n");

// The next definition of an SDL/EGL function: from the library a wrapper
// came from, else the global scope after this library.
static void *next_sym(void *lib, const char *name) {
    load_dlsym();
    if (!real_dlsym) return NULL;
    void *p = lib ? real_dlsym(lib, name) : NULL;
    return p ? p : real_dlsym(RTLD_NEXT, name);
}

static void *sym(const char *name) {
    static void *gl;
    load_dlsym();
    if (!real_dlsym) return NULL;
    void *p = real_dlsym(RTLD_DEFAULT, name);
    if (p) return p;
    // SDL and EGL loaded the GL library themselves (often RTLD_LOCAL)
    void *(*gpa)(const char *);
    *(void **) &gpa = next_sym(sdl_lib, "SDL_GL_GetProcAddress");
    if (gpa && (p = gpa(name))) return p;
    *(void **) &gpa = next_sym(egl_lib, "eglGetProcAddress");
    if (gpa && (p = gpa(name))) return p;
    static const char *const libs[] = {"libGLESv2.so", "libGLESv2.so.2", "libmali.so", "libmali.so.1"};
    for (unsigned i = 0; !gl && i < sizeof(libs) / sizeof(libs[0]); i++) gl = dlopen(libs[i], RTLD_NOW | RTLD_NOLOAD);
    return gl ? real_dlsym(gl, name) : NULL;
}

// ---- GL path (SDL_GL_SwapWindow, eglSwapBuffers) -------------------------
#define GL_SCISSOR_TEST         0x0C11
#define GL_SCISSOR_BOX          0x0C10
#define GL_COLOR_CLEAR_VALUE    0x0C22
#define GL_COLOR_WRITEMASK      0x0C23
#define GL_COLOR_BUFFER_BIT     0x4000
#define GL_FRAMEBUFFER          0x8D40
#define GL_FRAMEBUFFER_BINDING  0x8CA6

static struct {
    int ok;
    void (*Enable)(unsigned), (*Disable)(unsigned), (*Scissor)(int, int, int, int);
    void (*ClearColor)(float, float, float, float), (*Clear)(unsigned);
    void (*GetIntegerv)(unsigned, int *), (*GetFloatv)(unsigned, float *);
    void (*GetBooleanv)(unsigned, unsigned char *);
    void (*ColorMask)(unsigned char, unsigned char, unsigned char, unsigned char);
    void (*BindFramebuffer)(unsigned, unsigned);
    unsigned char (*IsEnabled)(unsigned);
} gl;

static int gl_load(void) {
    if (gl.ok) return gl.ok > 0;
#define L(f) (*(void **) &gl.f = sym("gl" #f))
    L(Enable); L(Disable); L(Scissor); L(ClearColor); L(Clear); L(GetIntegerv);
    L(GetFloatv); L(GetBooleanv); L(ColorMask); L(BindFramebuffer); L(IsEnabled);
#undef L
    gl.ok = gl.Enable && gl.Disable && gl.Scissor && gl.ClearColor && gl.Clear && gl.GetIntegerv &&
            gl.GetFloatv && gl.GetBooleanv && gl.ColorMask && gl.BindFramebuffer && gl.IsEnabled ? 1 : -1;
    if (gl.ok < 0) fprintf(stderr, "muos-levelbar: no GLES2 functions\n");
    return gl.ok > 0;
}

static void gl_draw(const int W, const int H) {
    if (W <= 0 || H <= 0 || !gl_load()) return;
    int fb = 0, box[4];
    float cc[4];
    unsigned char mask[4];
    gl.GetIntegerv(GL_FRAMEBUFFER_BINDING, &fb);
    gl.GetIntegerv(GL_SCISSOR_BOX, box);
    gl.GetFloatv(GL_COLOR_CLEAR_VALUE, cc);
    gl.GetBooleanv(GL_COLOR_WRITEMASK, mask);
    const unsigned char scissor = gl.IsEnabled(GL_SCISSOR_TEST);
    if (fb) gl.BindFramebuffer(GL_FRAMEBUFFER, 0);
    gl.ColorMask(1, 1, 1, 1);
    gl.Enable(GL_SCISSOR_TEST);
    rect_t r[MAX_RECTS];
    uint32_t c[MAX_RECTS];
    const int n = layout(W, H, r, c);
    for (int i = 0; i < n; i++) {
        if (r[i].w <= 0 || r[i].h <= 0) continue;
        gl.Scissor(r[i].x, H - r[i].y - r[i].h, r[i].w, r[i].h); // GL: y up
        gl.ClearColor((c[i] >> 16 & 0xFF) / 255.0f, (c[i] >> 8 & 0xFF) / 255.0f, (c[i] & 0xFF) / 255.0f, 1.0f);
        gl.Clear(GL_COLOR_BUFFER_BIT);
    }
    gl.ClearColor(cc[0], cc[1], cc[2], cc[3]);
    gl.Scissor(box[0], box[1], box[2], box[3]);
    if (!scissor) gl.Disable(GL_SCISSOR_TEST);
    gl.ColorMask(mask[0], mask[1], mask[2], mask[3]);
    if (fb) gl.BindFramebuffer(GL_FRAMEBUFFER, (unsigned) fb);
}

static void write_ppm(const unsigned char *px, const int w, const int h, const int stride, const int flip) {
    FILE *f = fopen("/run/muos/levelbar-grab.ppm", "we");
    if (f) {
        fprintf(f, "P6\n%d %d\n255\n", w, h);
        for (int y = 0; y < h; y++) {
            const unsigned char *row = px + (size_t) (flip ? h - 1 - y : y) * stride;
            for (int x = 0; x < w; x++) fwrite(row + x * 4, 1, 3, f);
        }
        fclose(f);
    }
    unlink("/run/muos/levelbar-grab");
    grab_pending = 0;
}

static void gl_grab(const int w, const int h) {
    void (*read_px)(int, int, int, int, unsigned, unsigned, void *);
    *(void **) &read_px = sym("glReadPixels");
    if (w <= 0 || h <= 0 || !read_px || !gl_load()) return;
    unsigned char *px = malloc((size_t) w * h * 4);
    if (!px) return;
    int fb = 0;
    gl.GetIntegerv(GL_FRAMEBUFFER_BINDING, &fb);
    if (fb) gl.BindFramebuffer(GL_FRAMEBUFFER, 0);
    read_px(0, 0, w, h, 0x1908 /* RGBA */, 0x1401 /* UNSIGNED_BYTE */, px);
    if (fb) gl.BindFramebuffer(GL_FRAMEBUFFER, (unsigned) fb);
    write_ppm(px, w, h, w * 4, 1);
    free(px);
}

static void said(const char *hook) {
    static int done, debug;
    static unsigned n;
    static uint64_t since;
    if (!done) {
        fprintf(stderr, "muos-levelbar: %s (pid %d)\n", hook, (int) getpid());
        debug = access("/run/muos/levelbar-debug", F_OK) == 0;
        done = 1;
    }
    if (!debug) return;
    n++;
    const uint64_t t = now_ms();
    if (!since) since = t;
    if (t - since >= 1000) {
        dbg("%s %u/s visible %d grab %d", hook, n, visible, grab_pending);
        n = 0;
        since = t;
    }
}

void SDL_GL_SwapWindow(void *window) {
    static void (*drawable)(void *, int *, int *);
    if (!real_gl_swap) *(void **) &real_gl_swap = next_sym(NULL, "SDL_GL_SwapWindow");
    if (!drawable) *(void **) &drawable = next_sym(sdl_lib, "SDL_GL_GetDrawableSize");
    said("SDL_GL_SwapWindow");
    poll_levels();
    if ((visible || grab_pending) && drawable) {
        int w = 0, h = 0;
        drawable(window, &w, &h);
        if (visible) gl_draw(w, h);
        if (grab_pending) gl_grab(w, h);
    }
    in_sdl++;
    if (real_gl_swap) real_gl_swap(window);
    in_sdl--;
}

#define EGL_HEIGHT 0x3056
#define EGL_WIDTH  0x3057
unsigned eglSwapBuffers(void *dpy, void *surface) {
    static unsigned (*query)(void *, void *, int, int *);
    if (!real_egl_swap) *(void **) &real_egl_swap = next_sym(NULL, "eglSwapBuffers");
    if (!query) *(void **) &query = next_sym(egl_lib, "eglQuerySurface");
    if (in_sdl) return real_egl_swap ? real_egl_swap(dpy, surface) : 0;
    said("eglSwapBuffers");
    poll_levels();
    if ((visible || grab_pending) && query) {
        int w = 0, h = 0;
        if (query(dpy, surface, EGL_WIDTH, &w) && query(dpy, surface, EGL_HEIGHT, &h)) {
            if (visible) gl_draw(w, h);
            if (grab_pending) gl_grab(w, h);
        }
    }
    return real_egl_swap ? real_egl_swap(dpy, surface) : 0;
}

// ---- SDL renderer path ----------------------------------------------------
typedef struct { int x, y, w, h; } SDL_Rect;
static struct {
    int ok;
    void *(*GetRenderTarget)(void *);
    int (*GetRendererOutputSize)(void *, int *, int *);
    int (*GetRenderDrawColor)(void *, uint8_t *, uint8_t *, uint8_t *, uint8_t *);
    int (*SetRenderDrawColor)(void *, uint8_t, uint8_t, uint8_t, uint8_t);
    int (*GetRenderDrawBlendMode)(void *, int *);
    int (*SetRenderDrawBlendMode)(void *, int);
    void (*RenderGetViewport)(void *, SDL_Rect *);
    int (*RenderSetViewport)(void *, const SDL_Rect *);
    void (*RenderGetClipRect)(void *, SDL_Rect *);
    int (*RenderSetClipRect)(void *, const SDL_Rect *);
    int (*RenderIsClipEnabled)(void *);
    void (*RenderGetScale)(void *, float *, float *);
    int (*RenderSetScale)(void *, float, float);
    void (*RenderGetLogicalSize)(void *, int *, int *);
    int (*RenderSetLogicalSize)(void *, int, int);
    int (*RenderFillRect)(void *, const SDL_Rect *);
} sdl;

static int sdl_load(void) {
    if (sdl.ok) return sdl.ok > 0;
#define L(f) (*(void **) &sdl.f = next_sym(sdl_lib, "SDL_" #f))
    L(GetRenderTarget); L(GetRendererOutputSize); L(GetRenderDrawColor); L(SetRenderDrawColor);
    L(GetRenderDrawBlendMode); L(SetRenderDrawBlendMode); L(RenderGetViewport); L(RenderSetViewport);
    L(RenderGetClipRect); L(RenderSetClipRect); L(RenderIsClipEnabled); L(RenderGetScale);
    L(RenderSetScale); L(RenderGetLogicalSize); L(RenderSetLogicalSize); L(RenderFillRect);
#undef L
    sdl.ok = sdl.GetRenderTarget && sdl.GetRendererOutputSize && sdl.GetRenderDrawColor &&
             sdl.SetRenderDrawColor && sdl.GetRenderDrawBlendMode && sdl.SetRenderDrawBlendMode &&
             sdl.RenderGetViewport && sdl.RenderSetViewport && sdl.RenderGetClipRect && sdl.RenderSetClipRect &&
             sdl.RenderIsClipEnabled && sdl.RenderGetScale && sdl.RenderSetScale && sdl.RenderGetLogicalSize &&
             sdl.RenderSetLogicalSize && sdl.RenderFillRect ? 1 : -1;
    if (sdl.ok < 0) fprintf(stderr, "muos-levelbar: no SDL renderer functions\n");
    return sdl.ok > 0;
}

static void sdl_draw(void *ren) {
    int W = 0, H = 0, lw = 0, lh = 0, mode = 0, clip_on;
    if (!sdl_load() || sdl.GetRenderTarget(ren) || sdl.GetRendererOutputSize(ren, &W, &H) || W <= 0 || H <= 0) {
        dbg("renderer skipped (load %d target %p size %dx%d)", sdl.ok, sdl.ok > 0 ? sdl.GetRenderTarget(ren) : NULL,
            W, H);
        return;
    }
    uint8_t cr, cg, cb, ca;
    SDL_Rect vp, clip;
    float sx = 1, sy = 1;
    sdl.GetRenderDrawColor(ren, &cr, &cg, &cb, &ca);
    sdl.GetRenderDrawBlendMode(ren, &mode);
    sdl.RenderGetViewport(ren, &vp);
    clip_on = sdl.RenderIsClipEnabled(ren);
    sdl.RenderGetClipRect(ren, &clip);
    sdl.RenderGetScale(ren, &sx, &sy);
    sdl.RenderGetLogicalSize(ren, &lw, &lh);
    static int told;
    if (!told++)
        dbg("out %dx%d logical %dx%d vp %d,%d %dx%d scale %.2f,%.2f clip %d", W, H, lw, lh, vp.x, vp.y, vp.w, vp.h, sx,
            sy, clip_on);
    // Output pixels over the whole output: a logical size (letterboxed
    // games) also clips to its viewport, so it is switched off for the bar
    // and set again afterwards (SDL re-derives its scale and viewport).
    const int logical = lw > 0 && lh > 0;
    if (logical) sdl.RenderSetLogicalSize(ren, 0, 0);
    sdl.RenderSetScale(ren, 1.0f, 1.0f);
    sdl.RenderSetViewport(ren, NULL);
    if (clip_on) sdl.RenderSetClipRect(ren, NULL);
    sdl.SetRenderDrawBlendMode(ren, 0);
    rect_t r[MAX_RECTS];
    uint32_t c[MAX_RECTS];
    const int n = layout(W, H, r, c);
    for (int i = 0; i < n; i++) {
        const SDL_Rect q = {r[i].x, r[i].y, r[i].w, r[i].h};
        if (q.w <= 0 || q.h <= 0) continue;
        sdl.SetRenderDrawColor(ren, c[i] >> 16 & 0xFF, c[i] >> 8 & 0xFF, c[i] & 0xFF, 0xFF);
        sdl.RenderFillRect(ren, &q);
    }
    if (logical) {
        sdl.RenderSetLogicalSize(ren, lw, lh);
    } else {
        sdl.RenderSetScale(ren, sx, sy);
    }
    sdl.RenderSetViewport(ren, &vp);
    if (clip_on) sdl.RenderSetClipRect(ren, &clip);
    sdl.SetRenderDrawBlendMode(ren, mode);
    sdl.SetRenderDrawColor(ren, cr, cg, cb, ca);
}

static void sdl_grab(void *ren) {
    int (*read)(void *, const SDL_Rect *, uint32_t, void *, int);
    *(void **) &read = next_sym(sdl_lib, "SDL_RenderReadPixels");
    int w = 0, h = 0;
    if (!read || !sdl_load() || sdl.GetRendererOutputSize(ren, &w, &h) || w <= 0 || h <= 0) return;
    unsigned char *px = malloc((size_t) w * h * 4);
    // SDL_PIXELFORMAT_ABGR8888: bytes R, G, B, A in memory
    int lw = 0, lh = 0; // the whole output, as drawn (see sdl_draw)
    SDL_Rect vp;
    sdl.RenderGetLogicalSize(ren, &lw, &lh);
    sdl.RenderGetViewport(ren, &vp);
    if (lw > 0 && lh > 0) sdl.RenderSetLogicalSize(ren, 0, 0);
    const int rc = px ? read(ren, NULL, 0x16762004u, px, w * 4) : -2;
    if (lw > 0 && lh > 0) {
        sdl.RenderSetLogicalSize(ren, lw, lh);
        sdl.RenderSetViewport(ren, &vp);
    }
    if (rc == 0) write_ppm(px, w, h, w * 4, 0);
    else dbg("grab failed (%d)", rc);
    free(px);
}

void SDL_RenderPresent(void *renderer) {
    if (!real_present) *(void **) &real_present = next_sym(NULL, "SDL_RenderPresent");
    said("SDL_RenderPresent");
    poll_levels();
    if (visible) sdl_draw(renderer);
    if (grab_pending) sdl_grab(renderer);
    in_sdl++;
    if (real_present) real_present(renderer);
    in_sdl--;
}
