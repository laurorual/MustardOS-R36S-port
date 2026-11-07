// SPDX-License-Identifier: MIT
// Resolve the full UI libraries without running their display/input functions.
#include <dlfcn.h>
#include <stdio.h>

int main(void) {
    const char *names[] = {"libplutosvg.so", "libui.so", "libmuxcom.so", "libmuxmod.so"};
    void *handles[4];
    // UI modules and common helpers refer to each other. Resolve their complete
    // dependency group as the real executable does, rather than loading each
    // intermediate library as if it were a standalone public API.
    void *group = dlopen("libmuxmod.so", RTLD_NOW | RTLD_GLOBAL);
    if (!group) { fprintf(stderr, "libmuxmod.so: %s\n", dlerror()); return 1; }
    for (unsigned i = 0; i < 4; i++) {
        handles[i] = dlopen(names[i], RTLD_NOW | RTLD_GLOBAL);
        if (!handles[i]) { fprintf(stderr, "%s: %s\n", names[i], dlerror()); return 1; }
        printf("RESOLVED %s\n", names[i]);
    }
    const char *symbols[] = {"muxlaunch_main", "muxinfo_main", "muxconfig_main", "muxplore_main"};
    for (unsigned i = 0; i < 4; i++) {
        if (!dlsym(handles[3], symbols[i])) { fprintf(stderr, "%s: %s\n", symbols[i], dlerror()); return 1; }
        printf("FOUND %s (not called)\n", symbols[i]);
    }
    return 0;
}
