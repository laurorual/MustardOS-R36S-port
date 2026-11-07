/* SPDX-License-Identifier: MIT */
/* Original no-content diagnostic core: RGB565 + D-pad + digital-zero audio.
 * No files, firmware, ROM, saved state, network or power operations. */
#include "libretro.h"
#include <string.h>

static retro_environment_t environment;
static retro_video_refresh_t video;
static retro_audio_sample_t sample;
static retro_audio_sample_batch_t batch;
static retro_input_poll_t poll_input;
static retro_input_state_t input;
static uint16_t pixels[160 * 120];
static int16_t silence[735 * 2];
static int x = 72, y = 52;

void retro_set_environment(retro_environment_t cb) {
    environment = cb;
    bool supported = true;
    if (cb) cb(RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME, &supported);
}
void retro_set_video_refresh(retro_video_refresh_t cb) { video = cb; }
void retro_set_audio_sample(retro_audio_sample_t cb) { sample = cb; }
void retro_set_audio_sample_batch(retro_audio_sample_batch_t cb) { batch = cb; }
void retro_set_input_poll(retro_input_poll_t cb) { poll_input = cb; }
void retro_set_input_state(retro_input_state_t cb) { input = cb; }
void retro_set_controller_port_device(unsigned port, unsigned device) { (void)port; (void)device; }
unsigned retro_api_version(void) { return RETRO_API_VERSION; }
void retro_init(void) { }
void retro_deinit(void) { }
void retro_reset(void) { x = 72; y = 52; }
void retro_get_system_info(struct retro_system_info *info) {
    memset(info, 0, sizeof(*info));
    info->library_name = "R35S no-content smoke";
    info->library_version = "1";
    info->valid_extensions = "";
}
void retro_get_system_av_info(struct retro_system_av_info *info) {
    memset(info, 0, sizeof(*info));
    info->geometry.base_width = info->geometry.max_width = 160;
    info->geometry.base_height = info->geometry.max_height = 120;
    info->geometry.aspect_ratio = 4.0f / 3.0f;
    info->timing.fps = 60.0;
    info->timing.sample_rate = 44100.0;
}
bool retro_load_game(const struct retro_game_info *game) {
    if (game || !environment) return false;
    enum retro_pixel_format format = RETRO_PIXEL_FORMAT_RGB565;
    if (!environment(RETRO_ENVIRONMENT_SET_PIXEL_FORMAT, &format)) return false;
    retro_reset();
    return true;
}
bool retro_load_game_special(unsigned type, const struct retro_game_info *info, size_t count) {
    (void)type; (void)info; (void)count;
    return false;
}
void retro_unload_game(void) { }
unsigned retro_get_region(void) { return RETRO_REGION_NTSC; }
void retro_run(void) {
    if (poll_input) poll_input();
    if (input) {
        x += input(0, RETRO_DEVICE_JOYPAD, 0, RETRO_DEVICE_ID_JOYPAD_RIGHT) ? 2 : 0;
        x -= input(0, RETRO_DEVICE_JOYPAD, 0, RETRO_DEVICE_ID_JOYPAD_LEFT) ? 2 : 0;
        y += input(0, RETRO_DEVICE_JOYPAD, 0, RETRO_DEVICE_ID_JOYPAD_DOWN) ? 2 : 0;
        y -= input(0, RETRO_DEVICE_JOYPAD, 0, RETRO_DEVICE_ID_JOYPAD_UP) ? 2 : 0;
    }
    if (x < 0) x = 0;
    if (x > 144) x = 144;
    if (y < 0) y = 0;
    if (y > 104) y = 104;
    for (int row = 0; row < 120; ++row)
        for (int col = 0; col < 160; ++col) {
            uint16_t colour = ((row / 8 + col / 8) & 1) ? 0x3186 : 0x1082;
            if (col >= x && col < x + 16 && row >= y && row < y + 16) colour = 0x07e0;
            pixels[row * 160 + col] = colour;
        }
    if (video) video(pixels, 160, 120, 160 * sizeof(uint16_t));
    if (batch) batch(silence, 735);
    else if (sample) for (unsigned i = 0; i < 735; ++i) sample(0, 0);
}
size_t retro_serialize_size(void) { return 0; }
bool retro_serialize(void *data, size_t size) { (void)data; (void)size; return false; }
bool retro_unserialize(const void *data, size_t size) { (void)data; (void)size; return false; }
void retro_cheat_reset(void) { }
void retro_cheat_set(unsigned index, bool enabled, const char *code) { (void)index; (void)enabled; (void)code; }
void *retro_get_memory_data(unsigned id) { (void)id; return NULL; }
size_t retro_get_memory_size(unsigned id) { (void)id; return 0; }
