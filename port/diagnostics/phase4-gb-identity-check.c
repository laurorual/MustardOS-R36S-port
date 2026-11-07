/* SPDX-License-Identifier: MIT
 * Loader/API metadata only. Does not initialise a core or load any ROM.
 */
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include "libretro.h"
int main(int argc, char **argv) {
    assert(argc == 2);
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!handle) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }
    unsigned (*version)(void) = (unsigned (*)(void))dlsym(handle,"retro_api_version");
    void (*info)(struct retro_system_info *) = (void (*)(struct retro_system_info *))dlsym(handle,"retro_get_system_info");
    assert(version && info && version() == RETRO_API_VERSION);
    struct retro_system_info system = {0}; info(&system);
    assert(system.library_name && strstr(system.library_name,"Gambatte"));
    assert(system.valid_extensions && strstr(system.valid_extensions,"gb"));
    assert(!system.need_fullpath);
    puts("C48_GB_IDENTITY_OK API=1 memory_content=1 ROM_loaded=0");
    dlclose(handle);
    return 0;
}
