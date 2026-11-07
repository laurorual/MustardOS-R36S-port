/* SPDX-License-Identifier: MIT */
/* Includes the exact patched loader and environment arms, extracted by builder. */
#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include "core.h"

struct core_cbs current_core;
int core_no_content_session;
char core_content_path[PATH_MAX] = "stale content";
char core_resolved_content_path[PATH_MAX] = "stale resolved";
char core_active_patches[1024] = "stale patch";
int core_active_patch_count = 1;
char core_content_load_method[32];
static unsigned calls, enters, exits, frames;
static enum retro_pixel_format pixel_format;
#define LOG_ERROR(...) ((void)0)
static void hw_render_bridge_enter_core_call(void) { ++enters; }
static void hw_render_bridge_exit_core_call(void) { ++exits; }
#include "loader-under-test.inc"

static bool environment(unsigned cmd, void *data) {
    switch (cmd) {
#include "environment-under-test.inc"
        default: return false;
    }
}
static bool reject(const struct retro_game_info *info) { assert(!info); ++calls; return false; }
static void video(const void *data, unsigned width, unsigned height, size_t pitch) {
    assert(data && width == 160 && height == 120 && pitch == 320); ++frames;
}
static size_t audio(const int16_t *data, size_t count) {
    assert(count == 735);
    for (size_t i = 0; i < count * 2; ++i) assert(!data[i]);
    return count;
}
int main(int argc, char **argv) {
    assert(argc == 2);
    assert(!environment(RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME, NULL));
    assert(core_load_no_content() == -1 && !enters);
    current_core.initialised = true;
    current_core.retro_load_game = reject;
    assert(core_load_no_content() == -1 && !calls);
    bool supported = true;
    assert(environment(RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME, &supported));
    assert(current_core.supports_no_game);
    assert(core_load_no_content() == -1 && calls == 1 && enters == exits && !core_no_content_session);
    supported = false;
    assert(environment(RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME, &supported));
    assert(core_load_no_content() == -1 && calls == 1);
    supported = true; environment(RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME, &supported);
    current_core.retro_load_game = NULL;
    assert(core_load_no_content() == -1 && enters == 1);
    void *library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL); assert(library);
#define SYMBOL(type, name) type name; do { void *p = dlsym(library, #name); assert(p); memcpy(&name, &p, sizeof(name)); } while (0)
    typedef void (*env_fn)(retro_environment_t);
    typedef void (*video_fn)(retro_video_refresh_t);
    typedef void (*audio_fn)(retro_audio_sample_batch_t);
    typedef bool (*load_fn)(const struct retro_game_info *);
    typedef void (*void_fn)(void);
    SYMBOL(env_fn, retro_set_environment); SYMBOL(video_fn, retro_set_video_refresh);
    SYMBOL(audio_fn, retro_set_audio_sample_batch); SYMBOL(load_fn, retro_load_game);
    SYMBOL(void_fn, retro_init); SYMBOL(void_fn, retro_run); SYMBOL(void_fn, retro_deinit);
    current_core.supports_no_game = false;
    retro_set_environment(environment); assert(current_core.supports_no_game);
    retro_set_video_refresh(video); retro_set_audio_sample_batch(audio); retro_init();
    current_core.retro_load_game = retro_load_game;
    assert(core_load_no_content() == 0 && core_no_content_session);
    assert(!core_content_path[0] && !core_resolved_content_path[0] && !core_active_patches[0]);
    assert(!core_active_patch_count && !strcmp(core_content_load_method, "No content"));
    assert(!current_core.game_info_ext && enters == exits && pixel_format == RETRO_PIXEL_FORMAT_RGB565);
    retro_run(); assert(frames == 1);
    retro_deinit(); assert(!dlclose(library));
    puts("MUXRETRO_REAL_NO_CONTENT_LOADER_AND_SMOKE_CORE_OK");
    return 0;
}
