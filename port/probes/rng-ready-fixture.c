// SPDX-License-Identifier: MIT
// Only the syscall boundary is stubbed. No entropy is written or credited.
#define getrandom fixture_getrandom
#define main rng_ready_main
#include "../utils/muos-rng-ready.c"
#undef main
#undef getrandom
#include <string.h>
static const char *scenario;
static int calls;
ssize_t fixture_getrandom(void *buffer, size_t length, unsigned flags) {
    if (flags != GRND_NONBLOCK || length != 1) _Exit(99);
    ++calls;
    if (!strcmp(scenario, "again")) { errno = EAGAIN; return -1; }
    if (!strcmp(scenario, "unsupported")) { errno = ENOSYS; return -1; }
    if (!strcmp(scenario, "interrupted") && calls == 1) { errno = EINTR; return -1; }
    if (!strcmp(scenario, "short")) return 0;
    *(unsigned char *)buffer = 0xa7;
    return 1;
}
int main(int argc, char **argv) {
    if (argc != 3) return 98;
    scenario = argv[1];
    char *args[] = {argv[0], argv[2], NULL};
    return rng_ready_main(2, args);
}
