// SPDX-License-Identifier: MIT
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static double now(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) _exit(125);
    return t.tv_sec + t.tv_nsec / 1e9;
}
static void tick(void) {
    struct timespec t = {0, 50000000};
    nanosleep(&t, NULL);
}
int main(int argc, char **argv) {
    char *end;
    if (argc < 3) return 125;
    long seconds = strtol(argv[1], &end, 10);
    if (*end || seconds < 1 || seconds > 120) return 125;
    pid_t child = fork();
    if (child < 0) return 125;
    if (!child) {
        if (setpgid(0, 0)) _exit(125);
        execvp(argv[2], argv + 2);
        _exit(127);
    }
    if (setpgid(child, child) && errno != EACCES && errno != ESRCH) {
        kill(child, SIGKILL); waitpid(child, NULL, 0); return 125;
    }
    int status;
    double deadline = now() + seconds;
    for (;;) {
        pid_t result = waitpid(child, &status, WNOHANG);
        if (result == child)
            return WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status);
        if (result < 0 && errno != EINTR) return 125;
        if (now() >= deadline) break;
        tick();
    }
    fprintf(stderr, "bounded: timeout running %s\n", argv[2]);
    kill(-child, SIGTERM);
    deadline = now() + 1;
    while (now() < deadline) tick();
    kill(-child, SIGKILL);
    while (waitpid(child, &status, 0) < 0 && errno == EINTR) {}
    return 124;
}
