// SPDX-License-Identifier: MIT
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/random.h>
#include <time.h>

static double now(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) exit(2);
    return t.tv_sec + t.tv_nsec / 1e9;
}
int main(int argc, char **argv) {
    char *end;
    if (argc != 2 || !*argv[1]) return 2;
    long seconds = strtol(argv[1], &end, 10);
    if (*end || seconds < 0 || seconds > 60) return 2;
    double start = now();
    for (;;) {
        unsigned char byte;
        ssize_t result = getrandom(&byte, sizeof(byte), GRND_NONBLOCK);
        if (result == (ssize_t)sizeof(byte)) {
            byte = 0; /* Never print or save random material. */
            printf("rng_ready=1 wait_ms=%.0f\n", (now() - start) * 1000);
            return 0;
        }
        if (result < 0 && errno != EAGAIN && errno != EINTR) {
            perror("getrandom readiness");
            return 2;
        }
        if (now() - start >= seconds) {
            printf("rng_ready=0 wait_ms=%.0f\n", (now() - start) * 1000);
            return 3;
        }
        struct timespec pause = {0, 100000000};
        nanosleep(&pause, NULL);
    }
}
