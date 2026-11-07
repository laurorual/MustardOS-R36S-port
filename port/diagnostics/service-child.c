// SPDX-License-Identifier: MIT
// Native fixture for process-group teardown tests; not part of the firmware.
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static volatile sig_atomic_t stop;
static void stopped(int sig) { stop = sig; }
int main(int argc, char **argv) {
    (void)argc;
    if (access("/run/muos/ui/fixture-exit", F_OK) == 0) return 7;
    int channel[2];
    if (pipe(channel)) return 1;
    pid_t pid = fork();
    if (pid < 0) return 1;
    if (pid == 0) {
        close(channel[0]);
        if (setsid() < 0) _exit(1);
        pid_t second = fork();
        if (second < 0) _exit(1);
        if (second > 0) _exit(0);
        signal(SIGTERM, SIG_IGN);
        dprintf(channel[1], "%ld\n", (long)getpid());
        close(channel[1]);
        for (;;) pause();
    }
    close(channel[1]);
    FILE *pipe_file = fdopen(channel[0], "r");
    long detached;
    if (!pipe_file || fscanf(pipe_file, "%ld", &detached) != 1) return 1;
    fclose(pipe_file);
    waitpid(pid, NULL, 0);
    char name[80];
    snprintf(name, sizeof(name), "/run/muos/ui/fixture-%ld", (long)getpid());
    FILE *f = fopen(name, "w");
    if (!f) return 1;
    fprintf(f, "%ld %ld\n", (long)getpid(), detached); fclose(f);
    if (strstr(argv[0], "muxfrontend") && access("/run/muos/ui/fixture-no-paint", F_OK) != 0) {
        f = fopen("/run/muos/first_paint", "w");
        if (!f) return 1;
        fputs("fixture only; no actual pixels\n", f); fclose(f);
    }
    signal(SIGTERM, stopped); signal(SIGINT, stopped);
    while (!stop) pause();
    return 0;
}
