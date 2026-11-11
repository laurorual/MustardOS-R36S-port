// SPDX-License-Identifier: MIT
// Audio check for the muOS SDL clients.
//   muos-sdl-audio-probe --require DRIVER  exit 1 unless SDL registers DRIVER
//                                          (T1: runs under qemu-user, no server)
//   muos-sdl-audio-probe [SECONDS]         T2: open audio as the frontend does
//                                          (driver from SDL_AUDIODRIVER, F32
//                                          stereo 44100 Hz, 2048 frames), play
//                                          silence; exit 0 = opened and played
#include <SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *req = argc > 2 && !strcmp(argv[1], "--require") ? argv[2] : NULL;
    int found = 0;
    printf("registered drivers:");
    for (int i = 0; i < SDL_GetNumAudioDrivers(); i++) {
        printf(" %s", SDL_GetAudioDriver(i));
        if (req && !strcmp(SDL_GetAudioDriver(i), req)) found = 1;
    }
    printf("\n");
    if (req) {
        printf("%s %s\n", found ? "OK" : "FAIL missing", req);
        return !found;
    }
    int secs = argc > 1 ? atoi(argv[1]) : 2;
    const char *drv = getenv("SDL_AUDIODRIVER");
    printf("SDL_AUDIODRIVER=%s\n", drv ? drv : "(unset)");
    if (SDL_Init(SDL_INIT_AUDIO) < 0) {
        printf("FAIL SDL_Init: %s\n", SDL_GetError());
        return 1;
    }
    SDL_AudioSpec want = {0}, have;
    want.freq = 44100;
    want.format = AUDIO_F32LSB;
    want.channels = 2;
    want.samples = 2048;
    SDL_AudioDeviceID dev = SDL_OpenAudioDevice(NULL, 0, &want, &have, 0);
    if (!dev) {
        printf("FAIL SDL_OpenAudioDevice (%s): %s\n", SDL_GetCurrentAudioDriver(), SDL_GetError());
        SDL_Quit();
        return 1;
    }
    printf("OK driver=%s freq=%d fmt=0x%x ch=%d samples=%d\n", SDL_GetCurrentAudioDriver(),
           have.freq, have.format, have.channels, have.samples);
    SDL_PauseAudioDevice(dev, 0); // no callback, nothing queued: SDL plays silence
    SDL_Delay((Uint32)secs * 1000);
    SDL_CloseAudioDevice(dev);
    SDL_Quit();
    return 0;
}
