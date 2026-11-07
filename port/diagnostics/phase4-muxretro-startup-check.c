/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "startup.h"

static unsigned cases;
static startup_options parsed;
static int check(int argc, char **argv, int expected) {
    int result = startup_options_parse(argc, argv, &parsed);
    assert(result == expected);
    ++cases;
    return result;
}
int main(void) {
    char *normal[] = {"muxretro", "core.so", "game.rom", NULL};
    check(3, normal, 1); assert(!parsed.no_content && !strcmp(parsed.content_path, "game.rom"));
    char *fresh[] = {"muxretro", "core.so", "game.rom", "--fresh", NULL};
    check(4, fresh, 1); assert(parsed.fresh && !parsed.no_content);
    char *network[] = {"muxretro", "core.so", "game.rom", "--netplay-host=1234", NULL};
    check(4, network, 1); assert(parsed.netplay_host && parsed.netplay_port == 1234);
    char *empty_core[] = {"muxretro", "", "game.rom", NULL}; check(3, empty_core, 0);
    char *empty_content[] = {"muxretro", "core.so", "", NULL}; check(3, empty_content, 0);
    char *missing[] = {"muxretro", "core.so", NULL}; check(2, missing, 0); check(3, missing, 0);
    check(3, NULL, 0); assert(!startup_options_parse(3, normal, NULL)); ++cases;
    char *none[] = {"muxretro", "core.so", "--no-content", NULL};
    check(3, none, 1); assert(parsed.no_content && parsed.fresh && !parsed.content_path);
    char *restart[] = {"muxretro", "core.so", "--no-content", "--restart", NULL};
    check(4, restart, 1); assert(parsed.no_content && parsed.fresh && parsed.restarting);
    const char *forbidden[] = {"--subsystem=link", "--netplay-host", "--netplay-host=0",
                               "--netplay-join=localhost:55435", "--single-screen", "--unknown"};
    for (unsigned i = 0; i < sizeof(forbidden) / sizeof(forbidden[0]); ++i) {
        char *args[] = {"muxretro", "core.so", "--no-content", (char *)forbidden[i], NULL};
        check(4, args, 0);
    }
    char *unknown[] = {"muxretro", "core.so", "game.rom", "--unknown", NULL};
    check(4, unknown, 0); assert(parsed.unknown_option);
    printf("MUXRETRO_STARTUP_CASES_OK cases=%u\n", cases);
    return 0;
}
