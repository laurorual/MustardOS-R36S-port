/* SPDX-License-Identifier: MIT */
/* Bounded digital-zero reproduction of the observed PipeWire ALSA geometry.
 * No mixer, route, filesystem or capture-device writes. */
#define _POSIX_C_SOURCE 200809L
#include <alsa/asoundlib.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

static int checked(int rc, const char *operation) {
    if (rc < 0) fprintf(stderr, "%s: %s\n", operation, snd_strerror(rc));
    return rc;
}
#define CHECK(call) do { if (checked((call), #call) < 0) goto fail; } while (0)

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--info") == 0) {
        puts("MUOS-ALSA-ZERO-PARAMS-1 rate44100 S32_LE stereo period1024 buffer4096 RW timestamp1 avail3072 manual-start");
        return 0;
    }
    if (argc != 1) return 64;
    snd_pcm_t *pcm = NULL;
    snd_pcm_hw_params_t *hw;
    snd_pcm_sw_params_t *sw;
    snd_pcm_hw_params_alloca(&hw);
    snd_pcm_sw_params_alloca(&sw);
    const snd_pcm_uframes_t period = 1024, buffer = 4096;
    unsigned rate = 44100;
    int direction = 0;
    CHECK(snd_pcm_open(&pcm, "hw:0,0", SND_PCM_STREAM_PLAYBACK, SND_PCM_NONBLOCK));
    CHECK(snd_pcm_hw_params_any(pcm, hw));
    CHECK(snd_pcm_hw_params_set_rate_resample(pcm, hw, 0));
    CHECK(snd_pcm_hw_params_set_access(pcm, hw, SND_PCM_ACCESS_RW_INTERLEAVED));
    CHECK(snd_pcm_hw_params_set_format(pcm, hw, SND_PCM_FORMAT_S32_LE));
    CHECK(snd_pcm_hw_params_set_channels(pcm, hw, 2));
    CHECK(snd_pcm_hw_params_set_rate(pcm, hw, rate, direction));
    CHECK(snd_pcm_hw_params_set_period_size(pcm, hw, period, direction));
    CHECK(snd_pcm_hw_params_set_buffer_size(pcm, hw, buffer));
    CHECK(snd_pcm_hw_params(pcm, hw));
    CHECK(snd_pcm_sw_params_current(pcm, sw));
    CHECK(snd_pcm_sw_params_set_tstamp_mode(pcm, sw, SND_PCM_TSTAMP_ENABLE));
    CHECK(snd_pcm_sw_params_set_avail_min(pcm, sw, buffer - period));
    CHECK(snd_pcm_sw_params_set_start_threshold(pcm, sw, LONG_MAX));
    CHECK(snd_pcm_sw_params_set_stop_threshold(pcm, sw, buffer));
    CHECK(snd_pcm_sw_params_set_silence_threshold(pcm, sw, 0));
    CHECK(snd_pcm_sw_params_set_silence_size(pcm, sw, 0));
    CHECK(snd_pcm_sw_params(pcm, sw));
    CHECK(snd_pcm_prepare(pcm));
    /* BSS initialization guarantees every PCM byte is digital zero. */
    static int32_t zeros[4096 * 2];
    snd_pcm_sframes_t filled = snd_pcm_writei(pcm, zeros, buffer);
    if (filled != (snd_pcm_sframes_t)buffer) {
        fprintf(stderr, "initial fill: %ld\n", (long)filled);
        goto fail;
    }
    CHECK(snd_pcm_start(pcm));
    puts("ZERO_STREAM_STARTED"); fflush(stdout);
    struct timespec first, now;
    if (clock_gettime(CLOCK_MONOTONIC, &first) != 0) goto fail;
    unsigned long frames = buffer;
    for (;;) {
        if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) goto fail;
        if (now.tv_sec - first.tv_sec >= 8) break;
        int rc = snd_pcm_wait(pcm, 250);
        if (checked(rc, "snd_pcm_wait") < 0) goto fail;
        if (rc == 0) continue;
        snd_pcm_sframes_t available = snd_pcm_avail_update(pcm);
        if (available < 0 || available > (snd_pcm_sframes_t)buffer) {
            fprintf(stderr, "invalid avail: %ld\n", (long)available);
            goto fail;
        }
        if (available == 0) continue;
        snd_pcm_sframes_t written = snd_pcm_writei(pcm, zeros, available);
        if (written == -EAGAIN) continue;
        if (written <= 0) {
            fprintf(stderr, "write: %ld\n", (long)written);
            goto fail;
        }
        frames += (unsigned long)written;
    }
    CHECK(snd_pcm_drop(pcm));
    int close_rc = snd_pcm_close(pcm);
    pcm = NULL;
    if (checked(close_rc, "snd_pcm_close") < 0) return 1;
    printf("ZERO_STREAM_COMPLETED submitted=%lu\n", frames);
    return 0;
fail:
    if (pcm) { snd_pcm_drop(pcm); snd_pcm_close(pcm); }
    return 1;
}
