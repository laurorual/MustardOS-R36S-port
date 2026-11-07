/* SPDX-License-Identifier: MIT
 * Link/load contract only. No video initialisation is requested.
 * The audit container exposes no GPU/DRM devices, including to library ctors.
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <SDL.h>

int main(void) {
    SDL_version version;
    SDL_GetVersion(&version);
    printf("SDL compiled=%u.%u.%u loaded=%u.%u.%u\n", SDL_MAJOR_VERSION,
           SDL_MINOR_VERSION, SDL_PATCHLEVEL, version.major, version.minor,
           version.patch);
    int kmsdrm = 0, gles2 = 0;
    for (int i = 0; i < SDL_GetNumVideoDrivers(); ++i) {
        const char *name = SDL_GetVideoDriver(i);
        printf("video_driver=%s\n", name);
        if (strcmp(name, "KMSDRM") == 0) kmsdrm = 1;
    }
    for (int i = 0; i < SDL_GetNumRenderDrivers(); ++i) {
        SDL_RendererInfo info;
        if (SDL_GetRenderDriverInfo(i, &info) != 0) return 2;
        printf("render_driver=%s\n", info.name);
        if (strcmp(info.name, "opengles2") == 0) gles2 = 1;
    }
    const char *symbols[] = {
        "eglGetDisplay", "eglInitialize", "eglCreateContext",
        "glGetString", "glClear", "gbm_create_device", "gbm_bo_get_fd",
        "drmModeGetResources", NULL
    };
    for (int i = 0; symbols[i]; ++i) {
        void *address = dlsym(RTLD_DEFAULT, symbols[i]);
        if (!address) {
            fprintf(stderr, "missing_symbol=%s\n", symbols[i]);
            return 3;
        }
        printf("symbol=%s present\n", symbols[i]);
        if (i == 0) {
            Dl_info provider;
            if (!dladdr(address, &provider)) return 5;
            printf("EGL_library=%s\n", provider.dli_fname);
        }
    }
    if (!kmsdrm || !gles2 || SDL_WasInit(0) != 0) return 4;
    puts("GRAPHICS_LINK_LOAD_CONTRACT=OK; video/GPU runtime untested");
    return 0;
}
