/* SPDX-License-Identifier: MIT */
#include <SDL2/SDL.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static volatile sig_atomic_t running = 1;
static void stop(int sig) { (void)sig; running = 0; }
static int compare(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv) {
    SDL_version version;
    SDL_GetVersion(&version);
    printf("sdl_version=%u.%u.%u\n", version.major, version.minor, version.patch);
    printf("sdl_revision=%s\n", SDL_GetRevision());
    for (int i = 0; i < SDL_GetNumVideoDrivers(); ++i)
        printf("available_video_driver=%s\n", SDL_GetVideoDriver(i));
    if (argc == 2 && strcmp(argv[1], "--info") == 0) return 0;
    char *end = NULL;
    long seconds = argc == 2 ? strtol(argv[1], &end, 10) : 30;
    if (argc > 2 || seconds < 1 || seconds > 120 || (end && *end)) return 2;
    signal(SIGTERM, stop);
    signal(SIGINT, stop);
    setvbuf(stdout, NULL, _IOLBF, 0);
    SDL_SetHint(SDL_HINT_RENDER_DRIVER, "opengles2");
    SDL_SetHint(SDL_HINT_RENDER_VSYNC, "1");
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        fprintf(stderr, "SDL_Init: %s\n", SDL_GetError());
        return 1;
    }
    printf("video_driver=%s\n", SDL_GetCurrentVideoDriver());
    SDL_DisplayMode mode;
    if (SDL_GetCurrentDisplayMode(0, &mode) == 0)
        printf("display_mode=%dx%d@%d\n", mode.w, mode.h, mode.refresh_rate);
    SDL_Window *window = SDL_CreateWindow("muOS R35S phase 2", SDL_WINDOWPOS_CENTERED,
        SDL_WINDOWPOS_CENTERED, 640, 480, SDL_WINDOW_FULLSCREEN | SDL_WINDOW_ALWAYS_ON_TOP | SDL_WINDOW_ALLOW_HIGHDPI);
    if (!window) {
        fprintf(stderr, "SDL_CreateWindow: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }
    SDL_Renderer *renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    SDL_RendererInfo info;
    if (!renderer || SDL_GetRendererInfo(renderer, &info) != 0) {
        fprintf(stderr, "SDL_CreateRenderer: %s\n", SDL_GetError());
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    printf("renderer=%s\nrenderer_flags=0x%x\n", info.name, info.flags);
    int width, height;
    SDL_GetRendererOutputSize(renderer, &width, &height);
    printf("output_size=%dx%d\n", width, height);
    int result = 1;
    if (strcmp(info.name, "opengles2") != 0 || !(info.flags & SDL_RENDERER_ACCELERATED)
        || !(info.flags & SDL_RENDERER_PRESENTVSYNC) || width != 640 || height != 480) {
        fprintf(stderr, "Required GLES2 accelerated/vsync 640x480 renderer was not obtained.\n");
        goto cleanup;
    }
    typedef const unsigned char *(*get_string_fn)(unsigned int);
    void *address = SDL_GL_GetProcAddress("glGetString");
    get_string_fn get_string = NULL;
    _Static_assert(sizeof(get_string) == sizeof(address), "Linux function pointer size");
    memcpy(&get_string, &address, sizeof(get_string));
    if (get_string) {
        const unsigned char *vendor = get_string(0x1f00), *gpu = get_string(0x1f01), *gl = get_string(0x1f02);
        printf("gl_vendor=%s\ngl_renderer=%s\ngl_version=%s\n",
            vendor ? (const char *)vendor : "unavailable", gpu ? (const char *)gpu : "unavailable", gl ? (const char *)gl : "unavailable");
    }
    SDL_ShowCursor(SDL_DISABLE);
    double timings[10000];
    unsigned frames = 0, samples = 0, failures = 0;
    double frequency = (double)SDL_GetPerformanceFrequency();
    Uint64 started = SDL_GetPerformanceCounter(), last = started;
    while (running && (SDL_GetPerformanceCounter() - started) / frequency < seconds) {
        SDL_Event event;
        while (SDL_PollEvent(&event)) if (event.type == SDL_QUIT) running = 0;
        const Uint8 colors[4][3] = {{255,0,0},{0,255,0},{0,0,255},{255,255,255}};
        for (int i = 0; i < 4; ++i) {
            SDL_Rect rect = {(i % 2) * 320, (i / 2) * 240, 320, 240};
            if (SDL_SetRenderDrawColor(renderer, colors[i][0], colors[i][1], colors[i][2], 255) < 0
                || SDL_RenderFillRect(renderer, &rect) < 0) ++failures;
        }
        SDL_Rect moving = {(int)(frames % 580) + 10, 215, 40, 50};
        if (SDL_SetRenderDrawColor(renderer, 255, 255, 0, 255) < 0 || SDL_RenderFillRect(renderer, &moving) < 0) ++failures;
        if (frames == 0) {
            Uint32 pixel = 0;
            SDL_Rect point = {10, 10, 1, 1};
            if (SDL_RenderReadPixels(renderer, &point, SDL_PIXELFORMAT_ARGB8888, &pixel, 4) < 0
                || (pixel & 0x00ffffff) != 0x00ff0000) {
                fprintf(stderr, "Renderer readback did not return the red test pixel.\n");
                ++failures;
            } else printf("readback_red_pixel=PASS\n");
        }
        SDL_RenderPresent(renderer);
        Uint64 now = SDL_GetPerformanceCounter();
        if (frames > 10 && samples < 10000) timings[samples++] = (now - last) * 1000.0 / frequency;
        last = now;
        ++frames;
    }
    double elapsed = (SDL_GetPerformanceCounter() - started) / frequency;
    qsort(timings, samples, sizeof(*timings), compare);
    printf("frames=%u\nelapsed_seconds=%.3f\naverage_fps=%.3f\nrender_failures=%u\n", frames, elapsed, frames / elapsed, failures);
    if (samples) printf("frame_interval_median_ms=%.3f\nframe_interval_p95_ms=%.3f\n", timings[samples/2], timings[(samples-1)*95/100]);
    result = failures || frames < 2 || elapsed < seconds * 0.9 ? 1 : 0;
cleanup:
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    printf("sdl_probe_exit_status=%d\n", result);
    return result;
}
