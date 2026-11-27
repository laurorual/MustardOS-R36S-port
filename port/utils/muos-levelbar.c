// SPDX-License-Identifier: MIT
// muOS R35S port (v1.1.1): the in-game volume/brightness bar for programs
// muxretro does not run (PortMaster ports, applications, the official
// PICO-8, the standalone emulators), preloaded by their launchers. A volume
// or brightness key changes config/settings/general/{volume,brightness}
// (muhotkey -> muos-volume-step / bright.sh); this checks them every 100 ms
// at the program's frame swap and then shows the bar exactly as muxretro
// draws it in games (patch 0002: theme panel, glyph and progress bar, 1.5 s,
// 200 ms fade, rounded as the menu's): muos-frontend has `muxretro
// --level-assets` write the active theme's bar to /run/muos/levelbar
// (levelbar.conf, one RGBA panel per kind and glyph level, the rounded track
// and full-width fill, drawn in slices), drawn here
//   SDL_GL_SwapWindow / eglSwapBuffers: a GLES2 program, textured and
//     coloured quads blended over the default framebuffer (every GL state
//     it touches saved and restored; resources per EGL context)
//   SDL_RenderPresent: SDL textures and blended fills (draw colour, blend
//     mode, clip, viewport, scale and logical size restored; not on a
//     render target)
// Without the assets a plain panel of rectangles is drawn instead.
// No SDL/GL headers or link: the hooked and used functions are looked up at
// run time, so it adds nothing to a program that never swaps. Programs that
// load SDL2 or EGL with dlopen and look the functions up with dlsym (Godot
// frt, PortMaster's pysdl2 GUI) get the wrappers from dlsym itself: this
// exports dlsym, returns the wrapper for the three swap functions on a
// library handle and passes everything else to libc's dlsym with a tail
// jump (an aarch64 trampoline, so dlsym(RTLD_NEXT) keeps its caller).
// T2: while /run/muos/levelbar-grab exists, the next frame (with the bar)
// goes to /run/muos/levelbar-grab.ppm and the trigger is removed (with
// /run/muos/levelbar-nodraw too, nothing is drawn: muxretro's own bar). Each
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
#define FADE_MS 200
#define POLL_MS 100
#define ASSETS "/run/muos/levelbar"

typedef struct { int x, y, w, h; } rect_t;
enum { VOLUME, BRIGHT };

static struct level {
    const char *path;
    long long mtime;
    int value, known;
} levels[2] = {{CONF "settings/general/volume", 0, 0, 0}, {CONF "settings/general/brightness", 0, 0, 0}};

static int shown_kind, shown_pct;
static uint64_t shown_at, polled_at;
static int visible, grab_pending, nodraw;
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
    if (visible && t - shown_at >= HOLD_MS + FADE_MS) visible = 0;
    if (polled_at && t - polled_at < POLL_MS) return;
    polled_at = t;
    grab_pending = access("/run/muos/levelbar-grab", F_OK) == 0;
    // T2: grab another program's own bar (muxretro) without drawing over it
    nodraw = grab_pending && access("/run/muos/levelbar-nodraw", F_OK) == 0;
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

// ---- the theme's bar (muxretro --level-assets) ----------------------------
static struct {
    long long mtime;
    int ok, mux_w, mux_h, px, py, pw, ph, bw, bh, main_a, active_a;
    uint32_t main_rgb, active_rgb;
    int bar_off[2][4], radius, round; // round: track.rgba + fill.rgba loaded
    unsigned char *img[2][4], *track, *fill;
    unsigned gen; // bumped on every reload: textures are uploaded again
} as;

// The rounded indicator of FILL_W theme pixels from the full-width fill
// image, as muxretro's fill_slices (patch 0002): left cap, stretched middle
// column, right cap; narrower than both caps, the image's left part.
typedef struct { int sx, sw, dx, dw; } slice_t;
static int fill_slices(const int fill_w, slice_t sl[3]) {
    const int bw = as.bw, r = as.radius;
    int n = 0;
    if (fill_w <= 0) return 0;
    if (fill_w < 2 * r) {
        sl[n++] = (slice_t) {0, fill_w, 0, fill_w};
        return n;
    }
    if (r > 0) sl[n++] = (slice_t) {0, r, 0, r};
    if (fill_w - 2 * r > 0) sl[n++] = (slice_t) {r < bw ? r : bw - 1, 1, r, fill_w - 2 * r};
    if (r > 0) sl[n++] = (slice_t) {bw - r, r, fill_w - r, r};
    return n;
}

static int read_file(const char *path, unsigned char **buf, const size_t size) {
    unsigned char *b = realloc(*buf, size);
    if (!b) return 0;
    *buf = b;
    FILE *f = fopen(path, "re");
    const int full = f && fread(b, 1, size, f) == size;
    if (f) fclose(f);
    return full;
}

// (Re)load when levelbar.conf changed; 1 = usable.
static int assets_load(void) {
    struct stat st;
    if (stat(ASSETS "/levelbar.conf", &st) != 0) return as.ok = 0;
    const long long m = (long long) st.st_mtim.tv_sec * 1000000000LL + st.st_mtim.tv_nsec;
    if (as.gen && m == as.mtime) return as.ok;
    as.mtime = m;
    as.gen++;
    as.ok = 0;
    FILE *f = fopen(ASSETS "/levelbar.conf", "re");
    if (!f) return 0;
    char line[128];
    int got = 0;
    while (fgets(line, sizeof(line), f)) {
        int k, l, o;
        if (sscanf(line, "mux %d %d", &as.mux_w, &as.mux_h) == 2) got |= 1;
        else if (sscanf(line, "panel %d %d %d %d", &as.px, &as.py, &as.pw, &as.ph) == 4) got |= 2;
        else if (sscanf(line, "bar %d %d", &as.bw, &as.bh) == 2) got |= 4;
        else if (sscanf(line, "main %x %d", &as.main_rgb, &as.main_a) == 2) got |= 8;
        else if (sscanf(line, "active %x %d", &as.active_rgb, &as.active_a) == 2) got |= 16;
        else if (sscanf(line, "radius %d", &as.radius) == 1) got |= 32;
        else if (sscanf(line, "image %d %d %d", &k, &l, &o) == 3 && k >= 0 && k < 2 && l >= 0 && l < 4)
            as.bar_off[k][l] = o;
    }
    fclose(f);
    if ((got & 31) != 31 || as.mux_w <= 0 || as.mux_h <= 0 || as.pw <= 0 || as.ph <= 0 || as.pw > 4096 || as.ph > 1024)
        return 0;
    const size_t size = (size_t) as.pw * as.ph * 4;
    for (int k = 0; k < 2; k++) {
        for (int l = 0; l < 4; l++) {
            char path[96];
            snprintf(path, sizeof(path), ASSETS "/%s_%d.rgba", k ? "bright" : "volume", l);
            if (!read_file(path, &as.img[k][l], size)) return 0;
        }
    }
    // v1.1.1: the rounded progress bar (older assets: plain rectangles)
    const size_t bar = (size_t) as.bw * as.bh * 4;
    as.round = (got & 32) && as.bw > 0 && as.bh > 0 && as.bw <= 4096 && as.bh <= 1024 &&
               read_file(ASSETS "/track.rgba", &as.track, bar) && read_file(ASSETS "/fill.rgba", &as.fill, bar);
    return as.ok = 1;
}

// The bar of the theme in a W x H output: panel, track and fill rectangles,
// the glyph level, and the fade (0..1) as muxretro's osd_draw.
typedef struct {
    rect_t panel, track, fill;
    int kind, level, bx, by, fill_w; // bx, by, fill_w: theme units
    float fade, sx, sy;
} bar_t;

static float fade_now(void) {
    const uint64_t age = now_ms() - shown_at;
    if (age <= HOLD_MS) return 1.0f;
    if (age >= HOLD_MS + FADE_MS) return 0.0f;
    return 1.0f - (float) (age - HOLD_MS) / FADE_MS;
}

static void bar_geometry(const int W, const int H, bar_t *b) {
    const float sx = (float) W / as.mux_w, sy = (float) H / as.mux_h;
#define SR(X, Y, WW, HH) ((rect_t) {(int) ((X) * sx + 0.5f), (int) ((Y) * sy + 0.5f), (int) ((WW) * sx + 0.5f), (int) ((HH) * sy + 0.5f)})
    b->kind = shown_kind;
    b->level = shown_pct > 70 ? 3 : shown_pct > 35 ? 2 : shown_pct > 0 ? 1 : 0;
    b->panel = SR(as.px, as.py, as.pw, as.ph);
    const int bx = as.px + as.bar_off[b->kind][b->level], by = as.py + (as.ph - as.bh) / 2;
    b->track = SR(bx, by, as.bw, as.bh);
    b->fill = SR(bx, by, as.bw * shown_pct / 100, as.bh);
#undef SR
    b->bx = bx;
    b->by = by;
    b->fill_w = as.bw * shown_pct / 100;
    b->sx = sx;
    b->sy = sy;
    b->fade = fade_now();
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

// ---- GL path with the theme's bar: a GLES2 textured-quad program ----------
#define GL_BLEND 0x0BE2
#define GL_DEPTH_TEST 0x0B71
#define GL_STENCIL_TEST 0x0B90
#define GL_CULL_FACE 0x0B44
#define GL_RASTERIZER_DISCARD 0x8C89
#define GL_SAMPLE_ALPHA_TO_COVERAGE 0x809E
#define GL_BLEND_SRC_RGB 0x80C9
#define GL_BLEND_DST_RGB 0x80C8
#define GL_BLEND_SRC_ALPHA 0x80CB
#define GL_BLEND_DST_ALPHA 0x80CA
#define GL_BLEND_EQUATION_RGB 0x8009
#define GL_BLEND_EQUATION_ALPHA 0x883D
#define GL_VIEWPORT 0x0BA2
#define GL_CURRENT_PROGRAM 0x8B8D
#define GL_ARRAY_BUFFER 0x8892
#define GL_ARRAY_BUFFER_BINDING 0x8894
#define GL_ACTIVE_TEXTURE 0x84E0
#define GL_TEXTURE0 0x84C0
#define GL_TEXTURE_2D 0x0DE1
#define GL_TEXTURE_BINDING_2D 0x8069
#define GL_SAMPLER_BINDING 0x8919
#define GL_VERTEX_ARRAY_BINDING 0x85B5
#define GL_UNPACK_ALIGNMENT 0x0CF5
#define GL_UNPACK_ROW_LENGTH 0x0CF2
#define GL_UNPACK_SKIP_ROWS 0x0CF3
#define GL_UNPACK_SKIP_PIXELS 0x0CF4
#define GL_PIXEL_UNPACK_BUFFER 0x88EC
#define GL_PIXEL_UNPACK_BUFFER_BINDING 0x88EF
#define GL_VERTEX_ATTRIB_ARRAY_ENABLED 0x8622
#define GL_VERTEX_ATTRIB_ARRAY_SIZE 0x8623
#define GL_VERTEX_ATTRIB_ARRAY_STRIDE 0x8624
#define GL_VERTEX_ATTRIB_ARRAY_TYPE 0x8625
#define GL_VERTEX_ATTRIB_ARRAY_NORMALIZED 0x886A
#define GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING 0x889F
#define GL_VERTEX_ATTRIB_ARRAY_POINTER 0x8645
#define GL_VERTEX_ATTRIB_ARRAY_INTEGER 0x88FD
#define GL_VERTEX_ATTRIB_ARRAY_DIVISOR 0x88FE
#define GL_FLOAT 0x1406
#define GL_TRIANGLE_STRIP 0x0005
#define GL_RGBA 0x1908
#define GL_UNSIGNED_BYTE 0x1401
#define GL_TEXTURE_MIN_FILTER 0x2801
#define GL_TEXTURE_MAG_FILTER 0x2800
#define GL_TEXTURE_WRAP_S 0x2802
#define GL_TEXTURE_WRAP_T 0x2803
#define GL_LINEAR 0x2601
#define GL_CLAMP_TO_EDGE 0x812F
#define GL_SRC_ALPHA 0x0302
#define GL_ONE_MINUS_SRC_ALPHA 0x0303
#define GL_FUNC_ADD 0x8006
#define GL_VERTEX_SHADER 0x8B31
#define GL_FRAGMENT_SHADER 0x8B30
#define GL_COMPILE_STATUS 0x8B81
#define GL_LINK_STATUS 0x8B82
#define GL_VERSION 0x1F02

static struct {
    int ok, es3;
    unsigned (*CreateShader)(unsigned), (*CreateProgram)(void);
    void (*ShaderSource)(unsigned, int, const char *const *, const int *), (*CompileShader)(unsigned);
    void (*GetShaderiv)(unsigned, unsigned, int *), (*AttachShader)(unsigned, unsigned);
    void (*BindAttribLocation)(unsigned, unsigned, const char *), (*LinkProgram)(unsigned);
    void (*GetProgramiv)(unsigned, unsigned, int *), (*UseProgram)(unsigned);
    int (*GetUniformLocation)(unsigned, const char *);
    void (*Uniform1i)(int, int), (*Uniform4f)(int, float, float, float, float);
    void (*GenTextures)(int, unsigned *), (*BindTexture)(unsigned, unsigned), (*ActiveTexture)(unsigned);
    void (*TexParameteri)(unsigned, unsigned, int), (*PixelStorei)(unsigned, int);
    void (*TexImage2D)(unsigned, int, int, int, int, int, unsigned, unsigned, const void *);
    void (*BlendFuncSeparate)(unsigned, unsigned, unsigned, unsigned), (*BlendEquationSeparate)(unsigned, unsigned);
    void (*Viewport)(int, int, int, int), (*BindBuffer)(unsigned, unsigned);
    void (*VertexAttribPointer)(unsigned, int, unsigned, unsigned char, int, const void *);
    void (*VertexAttribIPointer)(unsigned, int, unsigned, int, const void *);
    void (*EnableVertexAttribArray)(unsigned), (*DisableVertexAttribArray)(unsigned);
    void (*GetVertexAttribiv)(unsigned, unsigned, int *), (*GetVertexAttribPointerv)(unsigned, unsigned, void **);
    void (*VertexAttribDivisor)(unsigned, unsigned);
    void (*DrawArrays)(unsigned, int, int);
    void (*BindVertexArray)(unsigned), (*BindSampler)(unsigned, unsigned);
    const unsigned char *(*GetString)(unsigned);
    void *(*GetCurrentContext)(void);
} gx;

static int gx_load(void) {
    if (gx.ok) return gx.ok > 0;
    gx.ok = -1;
    if (!gl_load()) return 0;
#define L(f) (*(void **) &gx.f = sym("gl" #f))
    L(CreateShader); L(CreateProgram); L(ShaderSource); L(CompileShader); L(GetShaderiv); L(AttachShader);
    L(BindAttribLocation); L(LinkProgram); L(GetProgramiv); L(UseProgram); L(GetUniformLocation); L(Uniform1i);
    L(Uniform4f); L(GenTextures); L(BindTexture); L(ActiveTexture); L(TexParameteri); L(PixelStorei);
    L(TexImage2D); L(BlendFuncSeparate); L(BlendEquationSeparate); L(Viewport); L(BindBuffer);
    L(VertexAttribPointer); L(EnableVertexAttribArray); L(DisableVertexAttribArray); L(GetVertexAttribiv);
    L(GetVertexAttribPointerv); L(DrawArrays); L(GetString);
    if (!(gx.CreateShader && gx.CreateProgram && gx.ShaderSource && gx.CompileShader && gx.GetShaderiv &&
          gx.AttachShader && gx.BindAttribLocation && gx.LinkProgram && gx.GetProgramiv && gx.UseProgram &&
          gx.GetUniformLocation && gx.Uniform1i && gx.Uniform4f && gx.GenTextures && gx.BindTexture &&
          gx.ActiveTexture && gx.TexParameteri && gx.PixelStorei && gx.TexImage2D && gx.BlendFuncSeparate &&
          gx.BlendEquationSeparate && gx.Viewport && gx.BindBuffer && gx.VertexAttribPointer &&
          gx.EnableVertexAttribArray && gx.DisableVertexAttribArray && gx.GetVertexAttribiv &&
          gx.GetVertexAttribPointerv && gx.DrawArrays && gx.GetString)) {
        dbg("GL: missing GLES2 functions");
        return 0;
    }
    const char *v = (const char *) gx.GetString(GL_VERSION);
    gx.es3 = v && strncmp(v, "OpenGL ES ", 10) == 0 && v[10] >= '3';
    if (gx.es3) {
        L(BindVertexArray); L(BindSampler); L(VertexAttribIPointer); L(VertexAttribDivisor);
    }
#undef L
    *(void **) &gx.GetCurrentContext = next_sym(egl_lib, "eglGetCurrentContext");
    if (!gx.GetCurrentContext) *(void **) &gx.GetCurrentContext = sym("eglGetCurrentContext");
    gx.ok = 1;
    return 1;
}

// Per EGL context: the program, its uniforms, a white texel and the panels.
static struct {
    void *ctx;
    int failed, loc_s, loc_c;
    unsigned prog, white, tex[2][4], tex_gen[2][4], bar_tex[2], bar_gen[2];
} gr;

static unsigned shader(const unsigned type, const char *src) {
    const unsigned sh = gx.CreateShader(type);
    int ok = 0;
    gx.ShaderSource(sh, 1, &src, NULL);
    gx.CompileShader(sh);
    gx.GetShaderiv(sh, GL_COMPILE_STATUS, &ok);
    return ok ? sh : 0;
}

static void upload(const unsigned tex, const int w, const int h, const void *px) {
    gx.BindTexture(GL_TEXTURE_2D, tex);
    gx.TexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    gx.TexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    gx.TexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    gx.TexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    gx.TexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, px);
}

static void *current_context(void) {
    return gx.GetCurrentContext ? gx.GetCurrentContext() : NULL;
}

// Inside gl_draw_bar's saved state: program and white texel for this context.
static int gr_ready(void) {
    void *ctx = current_context();
    if (gr.ctx != ctx || (!gr.prog && !gr.failed)) {
        memset(&gr, 0, sizeof(gr));
        gr.ctx = ctx;
        const unsigned vs = shader(GL_VERTEX_SHADER, "attribute vec2 p; attribute vec2 t; varying vec2 v;\n"
                                                     "void main() { v = t; gl_Position = vec4(p, 0.0, 1.0); }\n");
        const unsigned fs = shader(GL_FRAGMENT_SHADER, "precision mediump float; varying vec2 v;\n"
                                                       "uniform sampler2D s; uniform vec4 c;\n"
                                                       "void main() { gl_FragColor = texture2D(s, v) * c; }\n");
        int ok = 0;
        if (vs && fs) {
            gr.prog = gx.CreateProgram();
            gx.AttachShader(gr.prog, vs);
            gx.AttachShader(gr.prog, fs);
            gx.BindAttribLocation(gr.prog, 0, "p");
            gx.BindAttribLocation(gr.prog, 1, "t");
            gx.LinkProgram(gr.prog);
            gx.GetProgramiv(gr.prog, GL_LINK_STATUS, &ok);
        }
        if (!ok) {
            dbg("GL: program failed");
            gr.prog = 0;
            gr.failed = 1;
            return 0;
        }
        gr.loc_s = gx.GetUniformLocation(gr.prog, "s");
        gr.loc_c = gx.GetUniformLocation(gr.prog, "c");
        const unsigned char white[4] = {255, 255, 255, 255};
        gx.GenTextures(1, &gr.white);
        upload(gr.white, 1, 1, white);
    }
    return gr.prog && !gr.failed;
}

static void quad_uv(const rect_t r, const int W, const int H, const unsigned tex, const uint32_t rgb, const float a,
                    const float u0, const float u1) {
    if (r.w <= 0 || r.h <= 0 || a <= 0.0f) return;
    const float x0 = 2.0f * r.x / W - 1.0f, x1 = 2.0f * (r.x + r.w) / W - 1.0f;
    const float y0 = 1.0f - 2.0f * r.y / H, y1 = 1.0f - 2.0f * (r.y + r.h) / H;
    const float v[16] = {x0, y0, u0, 0, x0, y1, u0, 1, x1, y0, u1, 0, x1, y1, u1, 1};
    gx.BindTexture(GL_TEXTURE_2D, tex);
    gx.Uniform4f(gr.loc_c, (rgb >> 16 & 0xFF) / 255.0f, (rgb >> 8 & 0xFF) / 255.0f, (rgb & 0xFF) / 255.0f, a);
    gx.VertexAttribPointer(0, 2, GL_FLOAT, 0, 16, v);
    gx.VertexAttribPointer(1, 2, GL_FLOAT, 0, 16, v + 2);
    gx.DrawArrays(GL_TRIANGLE_STRIP, 0, 4);
}

static void quad(const rect_t r, const int W, const int H, const unsigned tex, const uint32_t rgb, const float a) {
    quad_uv(r, W, H, tex, rgb, a, 0.0f, 1.0f);
}

struct attrib { int enabled, size, stride, type, norm, buffer, integer, divisor; void *ptr; };

static void attrib_save(const unsigned i, struct attrib *a) {
    gx.GetVertexAttribiv(i, GL_VERTEX_ATTRIB_ARRAY_ENABLED, &a->enabled);
    gx.GetVertexAttribiv(i, GL_VERTEX_ATTRIB_ARRAY_SIZE, &a->size);
    gx.GetVertexAttribiv(i, GL_VERTEX_ATTRIB_ARRAY_STRIDE, &a->stride);
    gx.GetVertexAttribiv(i, GL_VERTEX_ATTRIB_ARRAY_TYPE, &a->type);
    gx.GetVertexAttribiv(i, GL_VERTEX_ATTRIB_ARRAY_NORMALIZED, &a->norm);
    gx.GetVertexAttribiv(i, GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING, &a->buffer);
    gx.GetVertexAttribPointerv(i, GL_VERTEX_ATTRIB_ARRAY_POINTER, &a->ptr);
    a->integer = a->divisor = 0;
    if (gx.es3) {
        gx.GetVertexAttribiv(i, GL_VERTEX_ATTRIB_ARRAY_INTEGER, &a->integer);
        if (gx.VertexAttribDivisor) gx.GetVertexAttribiv(i, GL_VERTEX_ATTRIB_ARRAY_DIVISOR, &a->divisor);
    }
}

static void attrib_restore(const unsigned i, const struct attrib *a) {
    gx.BindBuffer(GL_ARRAY_BUFFER, (unsigned) a->buffer);
    if (a->integer && gx.VertexAttribIPointer) gx.VertexAttribIPointer(i, a->size, (unsigned) a->type, a->stride, a->ptr);
    else gx.VertexAttribPointer(i, a->size, (unsigned) a->type, (unsigned char) a->norm, a->stride, a->ptr);
    if (gx.VertexAttribDivisor) gx.VertexAttribDivisor(i, (unsigned) a->divisor);
    if (a->enabled) gx.EnableVertexAttribArray(i);
    else gx.DisableVertexAttribArray(i);
}

// The theme's bar over the default framebuffer; 0 = not drawn (no assets or
// no usable GLES2), the caller falls back to the plain panel.
static int gl_draw_bar(const int W, const int H) {
    if (W <= 0 || H <= 0 || !assets_load() || !gx_load()) return 0;
    if (gr.failed && gr.ctx == current_context()) return 0;
    bar_t b;
    bar_geometry(W, H, &b);
    if (b.fade <= 0.0f) return 1;

    int fb = 0, prog = 0, vao = 0, abuf = 0, active = 0, tex2d = 0, sampler = 0, unpack_buf = 0, vp[4];
    int bsrc_rgb, bdst_rgb, bsrc_a, bdst_a, beq_rgb, beq_a, align, row_len = 0, skip_rows = 0, skip_px = 0;
    unsigned char mask[4];
    gl.GetIntegerv(GL_FRAMEBUFFER_BINDING, &fb);
    gl.GetIntegerv(GL_CURRENT_PROGRAM, &prog);
    gl.GetIntegerv(GL_ARRAY_BUFFER_BINDING, &abuf);
    gl.GetIntegerv(GL_ACTIVE_TEXTURE, &active);
    gl.GetIntegerv(GL_VIEWPORT, vp);
    gl.GetIntegerv(GL_BLEND_SRC_RGB, &bsrc_rgb);
    gl.GetIntegerv(GL_BLEND_DST_RGB, &bdst_rgb);
    gl.GetIntegerv(GL_BLEND_SRC_ALPHA, &bsrc_a);
    gl.GetIntegerv(GL_BLEND_DST_ALPHA, &bdst_a);
    gl.GetIntegerv(GL_BLEND_EQUATION_RGB, &beq_rgb);
    gl.GetIntegerv(GL_BLEND_EQUATION_ALPHA, &beq_a);
    gl.GetIntegerv(GL_UNPACK_ALIGNMENT, &align);
    gl.GetBooleanv(GL_COLOR_WRITEMASK, mask);
    static const unsigned caps[] = {GL_BLEND, GL_DEPTH_TEST, GL_STENCIL_TEST, GL_CULL_FACE, GL_SCISSOR_TEST,
                                    GL_SAMPLE_ALPHA_TO_COVERAGE, GL_RASTERIZER_DISCARD};
    const unsigned ncaps = gx.es3 ? 7 : 6;
    unsigned char cap_on[7];
    for (unsigned i = 0; i < ncaps; i++) cap_on[i] = gl.IsEnabled(caps[i]);
    if (gx.es3) {
        if (gx.BindVertexArray) gl.GetIntegerv(GL_VERTEX_ARRAY_BINDING, &vao);
        gl.GetIntegerv(GL_PIXEL_UNPACK_BUFFER_BINDING, &unpack_buf);
        gl.GetIntegerv(GL_UNPACK_ROW_LENGTH, &row_len);
        gl.GetIntegerv(GL_UNPACK_SKIP_ROWS, &skip_rows);
        gl.GetIntegerv(GL_UNPACK_SKIP_PIXELS, &skip_px);
    }
    if (vao) gx.BindVertexArray(0);
    struct attrib a0, a1;
    attrib_save(0, &a0);
    attrib_save(1, &a1);
    gx.ActiveTexture(GL_TEXTURE0);
    gl.GetIntegerv(GL_TEXTURE_BINDING_2D, &tex2d);
    if (gx.es3 && gx.BindSampler) {
        gl.GetIntegerv(GL_SAMPLER_BINDING, &sampler);
        if (sampler) gx.BindSampler(0, 0);
    }
    if (unpack_buf) gx.BindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);
    gx.PixelStorei(GL_UNPACK_ALIGNMENT, 4);
    if (gx.es3) {
        gx.PixelStorei(GL_UNPACK_ROW_LENGTH, 0);
        gx.PixelStorei(GL_UNPACK_SKIP_ROWS, 0);
        gx.PixelStorei(GL_UNPACK_SKIP_PIXELS, 0);
    }

    int drawn = 0;
    if (gr_ready()) {
        if (fb) gl.BindFramebuffer(GL_FRAMEBUFFER, 0);
        for (unsigned i = 1; i < ncaps; i++) gl.Disable(caps[i]);
        gl.Enable(GL_BLEND);
        gx.BlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, 1, GL_ONE_MINUS_SRC_ALPHA);
        gx.BlendEquationSeparate(GL_FUNC_ADD, GL_FUNC_ADD);
        gl.ColorMask(1, 1, 1, 1);
        gx.Viewport(0, 0, W, H);
        gx.UseProgram(gr.prog);
        gx.Uniform1i(gr.loc_s, 0);
        gx.BindBuffer(GL_ARRAY_BUFFER, 0);
        gx.EnableVertexAttribArray(0);
        gx.EnableVertexAttribArray(1);
        if (gx.VertexAttribDivisor) {
            gx.VertexAttribDivisor(0, 0);
            gx.VertexAttribDivisor(1, 0);
        }
        unsigned *t = &gr.tex[b.kind][b.level];
        if (!*t) gx.GenTextures(1, t);
        if (gr.tex_gen[b.kind][b.level] != as.gen) {
            upload(*t, as.pw, as.ph, as.img[b.kind][b.level]);
            gr.tex_gen[b.kind][b.level] = as.gen;
        }
        quad(b.panel, W, H, *t, 0xFFFFFF, b.fade);
        if (as.round) {
            for (int i = 0; i < 2; i++) {
                if (!gr.bar_tex[i]) gx.GenTextures(1, &gr.bar_tex[i]);
                if (gr.bar_gen[i] != as.gen) {
                    upload(gr.bar_tex[i], as.bw, as.bh, i ? as.fill : as.track);
                    gr.bar_gen[i] = as.gen;
                }
            }
            quad(b.track, W, H, gr.bar_tex[0], 0xFFFFFF, b.fade);
            slice_t sl[3];
            const int n = fill_slices(b.fill_w, sl);
            for (int i = 0; i < n; i++) {
                const int x0 = (int) ((b.bx + sl[i].dx) * b.sx + 0.5f), x1 = (int) ((b.bx + sl[i].dx + sl[i].dw) * b.sx + 0.5f);
                const rect_t d = {x0, b.track.y, x1 - x0, b.track.h};
                // the middle column is sampled at its centre, the caps edge to edge
                const float u0 = sl[i].sw == 1 ? (sl[i].sx + 0.5f) / as.bw : (float) sl[i].sx / as.bw;
                const float u1 = sl[i].sw == 1 ? u0 : (float) (sl[i].sx + sl[i].sw) / as.bw;
                quad_uv(d, W, H, gr.bar_tex[1], 0xFFFFFF, b.fade, u0, u1);
            }
        } else {
            quad(b.track, W, H, gr.white, as.main_rgb, as.main_a / 255.0f * b.fade);
            quad(b.fill, W, H, gr.white, as.active_rgb, as.active_a / 255.0f * b.fade);
        }
        drawn = 1;
    }

    gx.UseProgram((unsigned) prog);
    attrib_restore(0, &a0);
    attrib_restore(1, &a1);
    gx.BindBuffer(GL_ARRAY_BUFFER, (unsigned) abuf);
    if (vao) gx.BindVertexArray((unsigned) vao);
    gx.BindTexture(GL_TEXTURE_2D, (unsigned) tex2d);
    if (sampler) gx.BindSampler(0, (unsigned) sampler);
    gx.ActiveTexture((unsigned) active);
    if (unpack_buf) gx.BindBuffer(GL_PIXEL_UNPACK_BUFFER, (unsigned) unpack_buf);
    gx.PixelStorei(GL_UNPACK_ALIGNMENT, align);
    if (gx.es3) {
        gx.PixelStorei(GL_UNPACK_ROW_LENGTH, row_len);
        gx.PixelStorei(GL_UNPACK_SKIP_ROWS, skip_rows);
        gx.PixelStorei(GL_UNPACK_SKIP_PIXELS, skip_px);
    }
    gx.BlendFuncSeparate((unsigned) bsrc_rgb, (unsigned) bdst_rgb, (unsigned) bsrc_a, (unsigned) bdst_a);
    gx.BlendEquationSeparate((unsigned) beq_rgb, (unsigned) beq_a);
    for (unsigned i = 0; i < ncaps; i++) {
        if (cap_on[i]) gl.Enable(caps[i]);
        else gl.Disable(caps[i]);
    }
    gl.ColorMask(mask[0], mask[1], mask[2], mask[3]);
    gx.Viewport(vp[0], vp[1], vp[2], vp[3]);
    if (fb) gl.BindFramebuffer(GL_FRAMEBUFFER, (unsigned) fb);
    return drawn;
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
        if (visible && !nodraw && !gl_draw_bar(w, h)) gl_draw(w, h);
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
            if (visible && !nodraw && !gl_draw_bar(w, h)) gl_draw(w, h);
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

// The theme's bar with SDL textures (one per kind and glyph level, per
// renderer); 0 = no assets or no texture functions.
static struct {
    int ok;
    void *(*CreateTexture)(void *, uint32_t, int, int, int);
    int (*UpdateTexture)(void *, const SDL_Rect *, const void *, int);
    int (*SetTextureBlendMode)(void *, int), (*SetTextureAlphaMod)(void *, uint8_t);
    int (*RenderCopy)(void *, void *, const SDL_Rect *, const SDL_Rect *);
    void *ren, *tex[2][4], *bar_tex[2];
    unsigned gen[2][4], bar_gen[2];
} st;

static void sdl_fill(void *ren, const rect_t r, const uint32_t rgb, const int a) {
    if (r.w <= 0 || r.h <= 0 || a <= 0) return;
    const SDL_Rect q = {r.x, r.y, r.w, r.h};
    sdl.SetRenderDrawColor(ren, rgb >> 16 & 0xFF, rgb >> 8 & 0xFF, rgb & 0xFF, (uint8_t) (a > 255 ? 255 : a));
    sdl.RenderFillRect(ren, &q);
}

static int sdl_draw_bar(void *ren, const int W, const int H) {
    if (!assets_load()) return 0;
    if (!st.ok) {
#define L(f) (*(void **) &st.f = next_sym(sdl_lib, "SDL_" #f))
        L(CreateTexture); L(UpdateTexture); L(SetTextureBlendMode); L(SetTextureAlphaMod); L(RenderCopy);
#undef L
        st.ok = st.CreateTexture && st.UpdateTexture && st.SetTextureBlendMode && st.SetTextureAlphaMod &&
                st.RenderCopy ? 1 : -1;
    }
    if (st.ok < 0) return 0;
    if (st.ren != ren) {
        memset(st.tex, 0, sizeof(st.tex));
        memset(st.gen, 0, sizeof(st.gen));
        memset(st.bar_tex, 0, sizeof(st.bar_tex));
        memset(st.bar_gen, 0, sizeof(st.bar_gen));
        st.ren = ren;
    }
    bar_t b;
    bar_geometry(W, H, &b);
    void **t = &st.tex[b.kind][b.level];
    if (!*t) {
        // SDL_PIXELFORMAT_ABGR8888 (bytes R, G, B, A), SDL_TEXTUREACCESS_STATIC
        *t = st.CreateTexture(ren, 0x16762004u, 0, as.pw, as.ph);
        if (!*t) return 0;
        st.SetTextureBlendMode(*t, 1);
    }
    if (st.gen[b.kind][b.level] != as.gen) {
        if (st.UpdateTexture(*t, NULL, as.img[b.kind][b.level], as.pw * 4) != 0) return 0;
        st.gen[b.kind][b.level] = as.gen;
    }
    const int f = (int) (b.fade * 255.0f + 0.5f);
    st.SetTextureAlphaMod(*t, (uint8_t) f);
    const SDL_Rect dst = {b.panel.x, b.panel.y, b.panel.w, b.panel.h};
    st.RenderCopy(ren, *t, NULL, &dst);
    if (as.round) {
        for (int i = 0; i < 2; i++) {
            void **bt = &st.bar_tex[i];
            if (!*bt) {
                *bt = st.CreateTexture(ren, 0x16762004u, 0, as.bw, as.bh);
                if (!*bt) return 1;
                st.SetTextureBlendMode(*bt, 1);
            }
            if (st.bar_gen[i] != as.gen) {
                if (st.UpdateTexture(*bt, NULL, i ? as.fill : as.track, as.bw * 4) != 0) return 1;
                st.bar_gen[i] = as.gen;
            }
            st.SetTextureAlphaMod(*bt, (uint8_t) f);
        }
        const SDL_Rect td = {b.track.x, b.track.y, b.track.w, b.track.h};
        st.RenderCopy(ren, st.bar_tex[0], NULL, &td);
        slice_t sl[3];
        const int n = fill_slices(b.fill_w, sl);
        for (int i = 0; i < n; i++) {
            const int x0 = (int) ((b.bx + sl[i].dx) * b.sx + 0.5f), x1 = (int) ((b.bx + sl[i].dx + sl[i].dw) * b.sx + 0.5f);
            const SDL_Rect src = {sl[i].sx, 0, sl[i].sw, as.bh}, dst = {x0, b.track.y, x1 - x0, b.track.h};
            if (dst.w > 0) st.RenderCopy(ren, st.bar_tex[1], &src, &dst);
        }
        return 1;
    }
    sdl.SetRenderDrawBlendMode(ren, 1);
    sdl_fill(ren, b.track, as.main_rgb, as.main_a * f / 255);
    sdl_fill(ren, b.fill, as.active_rgb, as.active_a * f / 255);
    return 1;
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
    if (!sdl_draw_bar(ren, W, H)) {
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
    if (visible && !nodraw) sdl_draw(renderer);
    if (grab_pending) sdl_grab(renderer);
    in_sdl++;
    if (real_present) real_present(renderer);
    in_sdl--;
}
