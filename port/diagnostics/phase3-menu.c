/* Temporary harness around the upstream muxlaunch menu, not a firmware init. */
#include <signal.h>
#include <sys/resource.h>
#include <SDL2/SDL.h>
#include "module/muxshare.h"
#include "common/platform/input.h"
#include "common/storage/inotify.h"

static volatile sig_atomic_t interrupted;
static unsigned started;
static int last_index = -1;
static unsigned changes;
static int selected;
static unsigned long long mixed_samples;
static double mixed_energy;
static float mixed_peak;

static void observe_mix(void *unused, Uint8 *stream, int length) {
    (void) unused;
    const float *samples = (const float *) stream;
    for (int i = 0; i < length / (int) sizeof(float); ++i) {
        const float value = samples[i];
        mixed_energy += (double) value * value;
        const float absolute = value < 0 ? -value : value;
        if (absolute > mixed_peak) mixed_peak = absolute;
        ++mixed_samples;
    }
}

void __real_play_sound(int sound);
void __wrap_play_sound(int sound) {
    SDL_ClearError();
    __real_play_sound(sound);
    const Mix_Chunk *chunk = sound >= 0 && sound < sound_total ? sound_cache[sound].chunk : NULL;
    printf("PHASE3_SOUND index=%d enabled=%d bytes=%u volume=%d playing=%d error=%s\n", sound, fe_snd,
           chunk ? chunk->alen : 0, chunk ? chunk->volume : -1, Mix_Playing(-1), Mix_GetError());
    fflush(stdout);
}

static int inspect_input(void) {
    if (SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_GAMECONTROLLER) < 0) return 4;
    int found = 0;
    for (int index = 0; index < SDL_NumJoysticks(); ++index) {
        SDL_Joystick *joy = SDL_JoystickOpen(index);
        if (!joy) continue;
        char guid[33];
        SDL_JoystickGetGUIDString(SDL_JoystickGetGUID(joy), guid, sizeof(guid));
        printf("SDL_JOYSTICK name=%s guid=%s buttons=%d axes=%d hats=%d\n", SDL_JoystickName(joy), guid,
               SDL_JoystickNumButtons(joy), SDL_JoystickNumAxes(joy), SDL_JoystickNumHats(joy));
        if (strcmp(SDL_JoystickName(joy), "muOS-Keys") == 0) ++found;
        SDL_JoystickClose(joy);
    }
    SDL_Quit();
    return found == 1 ? 0 : 5;
}

static int watch_input(void *unused, SDL_Event *event) {
    (void) unused;
    if (event->type == SDL_CONTROLLERBUTTONDOWN || event->type == SDL_CONTROLLERBUTTONUP)
        printf("PHASE3_SDL_BUTTON=%u value=%u elapsed_ms=%u\n", event->cbutton.button,
               event->cbutton.state, SDL_GetTicks()-started);
    if (event->type == SDL_JOYBUTTONDOWN || event->type == SDL_JOYBUTTONUP)
        printf("PHASE3_JOY_BUTTON=%u value=%u elapsed_ms=%u\n", event->jbutton.button,
               event->jbutton.state, SDL_GetTicks()-started);
    fflush(stdout);
    return 1;
}

static void on_signal(int sig) { interrupted = sig; }

/* Link-time boundaries: no script execution or module dispatch in this harness. */
void __wrap_run_exec(const char **args, size_t count, int background, int turbo,
                     const char *log_file, exec_callback cb) {
    (void) background; (void) turbo; (void) log_file;
    printf("PHASE3_EXEC_BLOCKED=%s\n", count && args ? args[0] : "(empty)");
    if (cb) cb(125);
}

void __wrap_load_mux(const char *action) {
    printf("PHASE3_SELECTION=%s index=%d elapsed_ms=%u\n", action, current_item_index,
           SDL_GetTicks() - started);
    selected = 1;
    fflush(stdout);
}

static void observe(lv_timer_t *timer) {
    (void) timer;
    if (last_index != current_item_index) {
        printf("PHASE3_FOCUS=%d elapsed_ms=%u\n", current_item_index, SDL_GetTicks() - started);
        last_index = current_item_index;
        ++changes;
        fflush(stdout);
    }
    if (interrupted || SDL_GetTicks() - started >= 120000) mux_input_stop();
}

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IOLBF, 0);
    if (argc == 2 && strcmp(argv[1], "--inspect-input") == 0) return inspect_input();
    if (argc == 2 && strcmp(argv[1], "--info") == 0) {
        puts("phase3-menu: upstream muxlaunch + LVGL/SDL; dispatch/exec blocked; 120s limit");
        return 0;
    }
    const int audio = argc == 2 && strcmp(argv[1], "--audio") == 0;
    if (argc != 1 && !audio) return 2;
    signal(SIGTERM, on_signal);
    signal(SIGINT, on_signal);
    signal(SIGHUP, on_signal);
    load_device(&device);
    load_config(&config);
    load_kiosk(&kiosk);
    board_init(device.board.name);
    if (strcmp(device.board.name, "rk-r35s-p0") || device.screen.width != 640 || device.screen.height != 480)
        return 3;
    /* No boot scripts, reset, password flow, hotkey daemon, or audio init here. */
    config.boot.factory_reset = 0;
    config.settings.general.orientation = 0;
    fe_snd = fe_bgm = 0;
    init_theme(0, 0);
    init_display();
    SDL_RendererInfo renderer;
    int width, height;
    if (SDL_GetRendererInfo(display_get_renderer(), &renderer) != 0 ||
        SDL_GetRendererOutputSize(display_get_renderer(), &width, &height) != 0) return 8;
    printf("PHASE3_RENDERER driver=%s renderer=%s flags=0x%x size=%dx%d\n",
           SDL_GetCurrentVideoDriver(), renderer.name, renderer.flags, width, height);
    if (strcmp(SDL_GetCurrentVideoDriver(), "KMSDRM") || strcmp(renderer.name, "opengles2") ||
        (renderer.flags & (SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)) !=
        (SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC) || width != 640 || height != 480) return 9;
    inotify_init();
    if (audio) {
        if (!init_audio_backend()) {
            sdl_cleanup();
            return 6;
        }
        init_fe_snd(&fe_snd, 2, 0);
        unsigned loaded = 0;
        for (unsigned i = 0; i < sound_total; ++i) loaded += sound_cache[i].chunk != NULL;
        printf("PHASE3_AUDIO driver=%s loaded_sounds=%u chunk_volume=%d\n", SDL_GetCurrentAudioDriver(),
               loaded, sound_cache[snd_navigate].chunk ? sound_cache[snd_navigate].chunk->volume : -1);
        if (!fe_snd || !sound_cache[snd_navigate].chunk || !sound_cache[snd_confirm].chunk) return 7;
        int rate, channels;
        Uint16 format;
        if (!Mix_QuerySpec(&rate, &format, &channels) || format != AUDIO_F32SYS) return 10;
        printf("PHASE3_AUDIO_SPEC rate=%d format=0x%x channels=%d\n", rate, format, channels);
        Mix_SetPostMix(observe_mix, NULL);
    }
    started = SDL_GetTicks();
    setvbuf(stdout, NULL, _IOLBF, 0);
    SDL_AddEventWatch(watch_input, NULL);
    lv_timer_create(observe, 50, NULL);
    puts("PHASE3_MENU_START");
    int status = muxlaunch_main();
    if (audio && selected && !interrupted) {
        const Uint32 drain_started = SDL_GetTicks();
        while (Mix_Playing(-1) && !interrupted && SDL_GetTicks() - drain_started < 1000)
            SDL_Delay(10);
        const int remaining = Mix_Playing(-1);
        /* The measured ALSA buffer is 4096 frames at 44100 Hz (~93 ms).
         * Keep silence flowing briefly after the last mixed chunk so closing
         * the diagnostic does not discard its tail in the hardware buffer. */
        const unsigned tail_ms = !remaining && !interrupted ? 150 : 0;
        if (tail_ms) SDL_Delay(tail_ms);
        printf("PHASE3_AUDIO_DRAIN elapsed_ms=%u remaining_channels=%d tail_ms=%u\n",
               SDL_GetTicks() - drain_started, remaining, tail_ms);
        if (remaining && !interrupted && !status) status = 11;
    }
    struct rusage usage;
    getrusage(RUSAGE_SELF, &usage);
    printf("PHASE3_MENU_END status=%d selected=%d focus_changes=%u elapsed_ms=%u maxrss_kib=%ld cpu_user=%.3f cpu_system=%.3f\n",
           status, selected, changes, SDL_GetTicks()-started, usage.ru_maxrss,
           usage.ru_utime.tv_sec + usage.ru_utime.tv_usec/1000000.0,
           usage.ru_stime.tv_sec + usage.ru_stime.tv_usec/1000000.0);
    timer_destroy_all();
    free_sound_cache();
    if (audio) {
        Mix_CloseAudio();
        printf("PHASE3_MIX samples=%llu energy=%.9f peak=%.9f\n", mixed_samples, mixed_energy, mixed_peak);
        Mix_Quit();
    }
    sdl_cleanup();
    return status;
}
