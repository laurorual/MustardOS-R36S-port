/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdlib.h>
#include <stdint.h>
#include <stddef.h>
static unsigned seen[5];
static void mux_retro_video_refresh_cb(const void *data, unsigned w, unsigned h, size_t pitch) {
    assert(data == seen && w == 16 && h == 8 && pitch == 32); seen[0]++;
}
static size_t mux_retro_audio_sample_batch_cb(const int16_t *data, size_t frames) {
    assert(data == (const int16_t *)seen && frames == 10); seen[1]++; return 7;
}
static void mux_retro_audio_sample_cb(int16_t l, int16_t r) {
    assert(l == -11 && r == 12); seen[2]++;
}
static void mux_retro_input_poll_cb(void) { seen[3]++; }
static int16_t mux_retro_input_state_cb(unsigned port, unsigned device, unsigned index, unsigned id) {
    assert(port == 0 && device == 1 && index == 2 && id == 3); seen[4]++; return -17;
}
#include "phase4-core-callback-profile.h"
int main(void) {
    /* Core loading happens before perf_init: enablement must work at that point. */
    unsetenv("MUXRETRO_PERF_CAPTURE"); assert(!c48_enabled());
    setenv("MUXRETRO_PERF_CAPTURE", "0", 1); assert(!c48_enabled());
    setenv("MUXRETRO_PERF_CAPTURE", "1", 1); assert(c48_enabled());
    c48_video(seen,16,8,32);
    assert(c48_batch((const int16_t *)seen,10) == 7);
    c48_sample(-11,12); c48_poll();
    assert(c48_input(0,1,2,3) == -17);
    for (unsigned i=0;i<5;i++) assert(seen[i] == 1 && c48_calls[i] == 1);
    c48_report();
    puts("C48_CALLBACK_FORWARDING_OK callbacks=5 gate_before_perf_init=1");
    return 0;
}
