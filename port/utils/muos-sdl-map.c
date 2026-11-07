// SPDX-License-Identifier: MIT
// Mapping contract for this board's muinput profile and SDL 2.30.12 evdev.
#include <SDL.h>
#include <fcntl.h>
#include <glob.h>
#include <linux/input.h>
#include <linux/joystick.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

struct button { const char *name; unsigned short code; };
static const struct button buttons[] = {
    {"a", BTN_EAST}, {"b", BTN_SOUTH}, {"x", BTN_NORTH}, {"y", BTN_WEST},
    {"leftshoulder", BTN_TL}, {"rightshoulder", BTN_TR},
    {"lefttrigger", BTN_TL2}, {"righttrigger", BTN_TR2},
    {"back", BTN_SELECT}, {"start", BTN_START}, {"guide", BTN_MODE},
    {"leftstick", BTN_THUMBL}, {"rightstick", BTN_THUMBR},
    {"volumedown", KEY_VOLUMEDOWN}, {"volumeup", KEY_VOLUMEUP}
};

static int joydev_codes(unsigned short *codes) {
    glob_t paths = {0};
    if (glob("/dev/input/js*", 0, NULL, &paths)) return -1;
    int matches = 0;
    for (size_t i = 0; i < paths.gl_pathc; i++) {
        int fd = open(paths.gl_pathv[i], O_RDONLY | O_NONBLOCK | O_CLOEXEC);
        if (fd < 0) continue;
        char name[128] = {0};
        unsigned char count = 0, axes = 0, axis_map[ABS_CNT] = {0};
        unsigned short map[KEY_MAX - BTN_MISC + 1] = {0};
        if (ioctl(fd, JSIOCGNAME(sizeof(name)), name) >= 0 && !strcmp(name, "muOS-Keys")) {
            const unsigned char expected_axes[] = {ABS_X, ABS_Y, ABS_RX, ABS_RY, ABS_HAT0X, ABS_HAT0Y};
            int valid = ioctl(fd, JSIOCGBUTTONS, &count) >= 0 && count == 13 &&
                ioctl(fd, JSIOCGAXES, &axes) >= 0 && axes == sizeof(expected_axes) &&
                ioctl(fd, JSIOCGAXMAP, axis_map) >= 0 &&
                !memcmp(axis_map, expected_axes, sizeof(expected_axes)) &&
                ioctl(fd, JSIOCGBTNMAP, map) >= 0;
            for (unsigned b = 0; valid && b < 13; b++) {
                int seen = 0;
                for (unsigned j = 0; j < 13; j++) seen += map[j] == buttons[b].code;
                valid = seen == 1;
            }
            if (!valid) {
                fprintf(stderr, "joydev %s: buttons=%u axes=%u, axis codes=", name, count, axes);
                for (unsigned j = 0; j < axes && j < ABS_CNT; j++) fprintf(stderr, "%u,", axis_map[j]);
                fputs(" button codes=", stderr);
                for (unsigned j = 0; j < count && j < 32; j++) fprintf(stderr, "%u,", map[j]);
                fputc('\n', stderr);
                close(fd); globfree(&paths); return -1;
            }
            memcpy(codes, map, 13 * sizeof(*codes));
            matches++;
        }
        close(fd);
    }
    globfree(&paths);
    return matches == 1 ? 0 : -1;
}

int main(int argc, char **argv) {
    SDL_version version;
    SDL_GetVersion(&version);
    if (argc == 2 && !strcmp(argv[1], "--info")) {
        printf("muos-sdl-map: SDL %u.%u.%u, muinput 756d:3504, no input injection\n",
               version.major, version.minor, version.patch);
        return 0;
    }
    if (argc != 1 || version.major != 2 || version.minor != 30 || version.patch != 12) {
        fputs("Review this mapping contract for the selected SDL version\n", stderr);
        return 2;
    }
    SDL_SetHint(SDL_HINT_JOYSTICK_HIDAPI, "0");
    // A readiness service must not hang indefinitely in an SDL backend.
    alarm(2);
    if (SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_GAMECONTROLLER)) {
        fprintf(stderr, "SDL input init: %s\n", SDL_GetError()); return 1;
    }
    SDL_Joystick *pad = NULL;
    int matches = 0;
    char descriptors[2048] = {0};
    size_t used = 0;
    for (int i = 0; i < SDL_NumJoysticks(); i++) {
        if (used < sizeof(descriptors)) {
            int n = snprintf(descriptors + used, sizeof(descriptors) - used,
                "SDL index=%d name=%s vendor=%04x product=%04x\n", i,
                SDL_JoystickNameForIndex(i), SDL_JoystickGetDeviceVendor(i), SDL_JoystickGetDeviceProduct(i));
            if (n > 0) used += (size_t)n;
        }
        if (SDL_JoystickGetDeviceVendor(i) != 0x756d || SDL_JoystickGetDeviceProduct(i) != 0x3504) continue;
        if (++matches == 1) pad = SDL_JoystickOpen(i);
    }
    unsigned short codes[15] = {0};
    if (matches != 1 || !pad || strcmp(SDL_JoystickName(pad), "muOS-Keys") ||
        SDL_JoystickNumButtons(pad) != 15 || SDL_JoystickNumAxes(pad) != 4 ||
        SDL_JoystickNumHats(pad) != 1 || joydev_codes(codes)) {
        fputs("Unexpected muinput/SDL/joydev descriptor; mapping refused\n", stderr);
        fputs(descriptors, stderr);
        if (pad) fprintf(stderr, "SDL opened name=%s buttons=%d axes=%d hats=%d\n",
            SDL_JoystickName(pad), SDL_JoystickNumButtons(pad), SDL_JoystickNumAxes(pad), SDL_JoystickNumHats(pad));
        if (pad) SDL_JoystickClose(pad);
        SDL_Quit(); return 1;
    }
    // This SDL evdev version appends the two KEY_VOLUME* buttons after BTN_*.
    // They are consumed explicitly by muOS in addition to SDL's controller map.
    codes[13] = KEY_VOLUMEDOWN;
    codes[14] = KEY_VOLUMEUP;
    char guid[33];
    SDL_JoystickGetGUIDString(SDL_JoystickGetGUID(pad), guid, sizeof(guid));
    printf("%s,muOS-Keys", guid);
    for (unsigned i = 0; i < sizeof(buttons)/sizeof(buttons[0]); i++) {
        unsigned index = 0;
        while (index < 15 && codes[index] != buttons[i].code) index++;
        printf(",%s:b%u", buttons[i].name, index);
    }
    puts(",leftx:a0,lefty:a1,rightx:a2,righty:a3,dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,platform:Linux,");
    SDL_JoystickClose(pad);
    SDL_Quit();
    return 0;
}
