/* SPDX-License-Identifier: MIT */
/* Offline eager-link probe only; no display, input, audio or services. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <link.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 5) return 2;
    /* libui and libmuxcom reference one another. Loading libmuxmod first
       lets the loader resolve the entire dependency group in one operation. */
    const int order[] = {3, 1, 2, 4};
    for (int j = 0; j < 4; j++) {
        int i = order[j];
        void *handle = dlopen(argv[i], RTLD_NOW | RTLD_GLOBAL);
        struct link_map *map = NULL;
        if (!handle) { fprintf(stderr, "%s\n", dlerror()); return 3; }
        if (dlinfo(handle, RTLD_DI_LINKMAP, &map) || !map || strcmp(map->l_name, argv[i])) return 4;
        printf("C65 eager load: %s\n", map->l_name);
    }
    return 0;
}
