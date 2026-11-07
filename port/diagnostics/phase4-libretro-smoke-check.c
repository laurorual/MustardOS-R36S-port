/* SPDX-License-Identifier: MIT */
/* Host-side ABI check; run the AArch64 binary under QEMU, never on the console. */
#define _POSIX_C_SOURCE 200809L
#include "libretro.h"
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

static unsigned frames, polls, samples, pixel_negotiations;
static bool no_content, right;
static uint64_t image_hash;
static bool environment(unsigned command, void *data) {
    if (command == RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME) {
        no_content = *(bool *)data;
        return true;
    }
    if (command == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT) {
        assert(*(enum retro_pixel_format *)data == RETRO_PIXEL_FORMAT_RGB565);
        ++pixel_negotiations;
        return true;
    }
    return false;
}
static void video(const void *data, unsigned width, unsigned height, size_t pitch) {
    assert(data && width == 160 && height == 120 && pitch == 320);
    const unsigned char *bytes = data;
    image_hash = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < height * pitch; ++i)
        image_hash = (image_hash ^ bytes[i]) * UINT64_C(1099511628211);
    ++frames;
}
static size_t audio(const int16_t *data, size_t count) {
    assert(count == 735);
    for (size_t i = 0; i < count * 2; ++i) assert(data[i] == 0);
    samples += (unsigned)count;
    return count;
}
static void audio_sample(int16_t left, int16_t right_sample) {
    assert(left == 0 && right_sample == 0);
    ++samples;
}
static void poll_input(void) { ++polls; }
static int16_t input(unsigned port, unsigned device, unsigned index, unsigned id) {
    assert(port == 0 && device == RETRO_DEVICE_JOYPAD && index == 0);
    return id == RETRO_DEVICE_ID_JOYPAD_RIGHT && right;
}
int main(int argc, char **argv) {
    assert(argc == 2);
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!handle) { fprintf(stderr, "%s\n", dlerror()); return 1; }
#define LOAD(type, name) type name; do { void *symbol = dlsym(handle, #name); assert(symbol); memcpy(&name, &symbol, sizeof(name)); } while (0)
    typedef unsigned (*version_fn)(void);
    typedef void (*void_fn)(void);
    typedef void (*set_env_fn)(retro_environment_t);
    typedef void (*set_video_fn)(retro_video_refresh_t);
    typedef void (*set_audio_fn)(retro_audio_sample_batch_t);
    typedef void (*set_sample_fn)(retro_audio_sample_t);
    typedef void (*set_poll_fn)(retro_input_poll_t);
    typedef void (*set_input_fn)(retro_input_state_t);
    typedef void (*info_fn)(struct retro_system_info *);
    typedef void (*av_fn)(struct retro_system_av_info *);
    typedef bool (*load_fn)(const struct retro_game_info *);
    LOAD(version_fn, retro_api_version); LOAD(set_env_fn, retro_set_environment);
    LOAD(set_video_fn, retro_set_video_refresh); LOAD(set_audio_fn, retro_set_audio_sample_batch);
    LOAD(set_sample_fn, retro_set_audio_sample); LOAD(set_poll_fn, retro_set_input_poll);
    LOAD(set_input_fn, retro_set_input_state); LOAD(info_fn, retro_get_system_info);
    LOAD(av_fn, retro_get_system_av_info); LOAD(load_fn, retro_load_game);
    LOAD(void_fn, retro_init); LOAD(void_fn, retro_run); LOAD(void_fn, retro_reset);
    LOAD(void_fn, retro_unload_game); LOAD(void_fn, retro_deinit);
    const char *required[] = {"retro_set_controller_port_device", "retro_load_game_special", "retro_get_region",
        "retro_serialize_size", "retro_serialize", "retro_unserialize", "retro_cheat_reset", "retro_cheat_set",
        "retro_get_memory_data", "retro_get_memory_size"};
    for (unsigned i = 0; i < sizeof(required) / sizeof(required[0]); ++i) assert(dlsym(handle, required[i]));
    assert(retro_api_version() == RETRO_API_VERSION);
    retro_set_environment(environment); assert(no_content);
    retro_set_video_refresh(video); retro_set_audio_sample_batch(audio);
    retro_set_audio_sample(audio_sample); retro_set_input_poll(poll_input); retro_set_input_state(input);
    retro_init();
    struct retro_system_info info; retro_get_system_info(&info);
    assert(!info.need_fullpath && !strcmp(info.library_name, "R35S no-content smoke"));
    struct retro_system_av_info av; retro_get_system_av_info(&av);
    assert(av.geometry.base_width == 160 && av.geometry.base_height == 120);
    assert(av.timing.fps == 60 && av.timing.sample_rate == 44100);
    struct retro_game_info forbidden = {0}; assert(!retro_load_game(&forbidden));
    assert(retro_load_game(NULL) && pixel_negotiations == 1);
    retro_run(); uint64_t original = image_hash;
    right = true; retro_run(); assert(image_hash != original);
    right = false; retro_reset(); retro_run(); assert(image_hash == original);
    for (unsigned i = 0; i < 7; ++i) retro_run();
    assert(frames == 10 && polls == 10 && samples == 7350);
    retro_set_audio_sample_batch(NULL); retro_run();
    assert(frames == 11 && polls == 11 && samples == 8085);
    retro_unload_game(); retro_deinit(); assert(dlclose(handle) == 0);
    puts("LIBRETRO_SMOKE_ABI_RGB565_INPUT_RESET_ZERO_AUDIO_OK frames=11 samples=8085");
    return 0;
}
