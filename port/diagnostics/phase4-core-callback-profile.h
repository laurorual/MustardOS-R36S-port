/* SPDX-License-Identifier: MIT
 * C48 callback cost inside retro_run. Enabled only by native perf capture.
 * Totals include startup/priming; compare per-call means with perf CSV, not sums.
 */
#include <SDL2/SDL.h>
#include <stdlib.h>
static int c48_enabled(void) {
    const char *env = getenv("MUXRETRO_PERF_CAPTURE");
    return env && *env == '1';
}
static uint64_t c48_ticks[5], c48_calls[5];
static void c48_note(unsigned slot, uint64_t start) {
    c48_ticks[slot] += SDL_GetPerformanceCounter() - start;
    c48_calls[slot]++;
}
static void c48_video(const void *data, unsigned w, unsigned h, size_t pitch) {
    uint64_t t = SDL_GetPerformanceCounter();
    mux_retro_video_refresh_cb(data, w, h, pitch);
    c48_note(0, t);
}
static size_t c48_batch(const int16_t *data, size_t frames) {
    uint64_t t = SDL_GetPerformanceCounter();
    size_t n = mux_retro_audio_sample_batch_cb(data, frames);
    c48_note(1, t);
    return n;
}
static void c48_sample(int16_t left, int16_t right) {
    uint64_t t = SDL_GetPerformanceCounter();
    mux_retro_audio_sample_cb(left, right);
    c48_note(2, t);
}
static void c48_poll(void) {
    uint64_t t = SDL_GetPerformanceCounter();
    mux_retro_input_poll_cb();
    c48_note(3, t);
}
static int16_t c48_input(unsigned port, unsigned device, unsigned index, unsigned id) {
    uint64_t t = SDL_GetPerformanceCounter();
    int16_t n = mux_retro_input_state_cb(port, device, index, id);
    c48_note(4, t);
    return n;
}
static void c48_report(void) {
    static const char *names[] = {"video", "audio_batch", "audio_sample", "input_poll", "input_state"};
    for (unsigned i = 0; i < 5; i++) {
        if (!c48_calls[i]) continue;
        printf("C48_CALLBACK name=%s calls=%llu total_ms=%.4f mean_ms=%.4f\n",
               names[i], (unsigned long long)c48_calls[i],
               (double)c48_ticks[i]*1000.0/(double)SDL_GetPerformanceFrequency(),
               (double)c48_ticks[i]*1000.0/(double)SDL_GetPerformanceFrequency()/(double)c48_calls[i]);
    }
    fflush(stdout);
}
