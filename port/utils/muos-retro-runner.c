// SPDX-License-Identifier: MIT
// Own one child session and reap descendants on every exit path.
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t stopped;
static void stop(int sig) { stopped = sig; }
static double now(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) _exit(125);
    return t.tv_sec + t.tv_nsec / 1e9;
}
static void tick(void) { struct timespec t = {0, 20000000}; nanosleep(&t, NULL); }
static unsigned long long starttime(pid_t pid) {
    char path[64], line[4096];
    snprintf(path, sizeof(path), "/proc/%ld/stat", (long)pid);
    FILE *file = fopen(path, "r");
    if (!file) return 0;
    char *ok = fgets(line, sizeof(line), file); fclose(file);
    if (!ok) return 0;
    char *cursor = strrchr(line, ')');
    if (!cursor || cursor[1] != ' ') return 0;
    cursor += 2;
    for (int field = 3; field < 22; ++field) {
        cursor = strchr(cursor, ' '); if (!cursor) return 0; ++cursor;
    }
    return strtoull(cursor, NULL, 10);
}
static int receipt(int directory, const char *name, long pid, unsigned long long value) {
    int fd = openat(directory, name, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) return -1;
    int ok = dprintf(fd, "%ld %llu\n", pid, value) > 0;
    if (close(fd)) ok = 0;
    return ok ? 0 : -1;
}
int main(int argc, char **argv) {
    if (argc < 4 || argv[2][0] != '/' || argv[3][0] != '/') return 125;
    char *end;
    long seconds = strtol(argv[1], &end, 10);
    if (*end || seconds < 1 || seconds > 240 || getuid() != geteuid()) return 125;
    int directory = open(argv[2], O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    struct stat st;
    if (directory < 0 || fstat(directory, &st) || st.st_uid != geteuid() || (st.st_mode & 0777) != 0700) return 125;
    if (receipt(directory, "runner.once", (long)getpid(), 1)) return 125;
    pid_t parent = getppid();
    struct sigaction action = {.sa_handler = stop};
    sigemptyset(&action.sa_mask);
    if (sigaction(SIGTERM, &action, NULL) || sigaction(SIGINT, &action, NULL) || sigaction(SIGHUP, &action, NULL)
        || prctl(PR_SET_CHILD_SUBREAPER, 1) || prctl(PR_SET_PDEATHSIG, SIGTERM)) return 125;
    if (parent <= 1 || getppid() != parent) return 125;
    pid_t child = fork();
    if (child < 0) return 125;
    if (!child) {
        pid_t owner = getppid();
        signal(SIGTERM, SIG_DFL); signal(SIGINT, SIG_DFL); signal(SIGHUP, SIG_DFL);
        if (setsid() < 0 || prctl(PR_SET_PDEATHSIG, SIGKILL) || getppid() != owner || owner <= 1) _exit(125);
        for (int fd = 3; fd < 1024; ++fd) close(fd);
        execv(argv[3], argv + 3);
        _exit(127);
    }
    int result = 125;
    if (!receipt(directory, "child.pid", (long)child, starttime(child))) {
        double deadline = now() + seconds;
        for (;;) {
            siginfo_t info = {0};
            if (waitid(P_PID, child, &info, WEXITED | WNOHANG | WNOWAIT) && errno != EINTR) break;
            if (info.si_pid == child) {
                result = info.si_code == CLD_EXITED ? info.si_status : 128 + info.si_status;
                break;
            }
            if (stopped) { result = 128 + stopped; break; }
            if (now() >= deadline) { result = 124; break; }
            tick();
        }
    }
    // Keep the leader unreaped until group cleanup, preventing PID reuse.
    kill(-child, SIGTERM);
    double grace = now() + .5;
    while (now() < grace) tick();
    kill(-child, SIGKILL);
    // Also stop adopted children which deliberately created another session.
    char path[80];
    snprintf(path, sizeof(path), "/proc/self/task/%ld/children", (long)getpid());
    FILE *descendants = fopen(path, "r");
    if (descendants) {
        long pid;
        while (fscanf(descendants, "%ld", &pid) == 1)
            if (pid > 1) kill((pid_t)pid, SIGKILL);
        fclose(descendants);
    }
    grace = now() + 2;
    int clean = 0;
    do {
        descendants = fopen(path, "r");
        if (descendants) {
            long pid;
            while (fscanf(descendants, "%ld", &pid) == 1)
                if (pid > 1) kill((pid_t)pid, SIGKILL);
            fclose(descendants);
        }
        int status;
        pid_t reaped;
        while ((reaped = waitpid(-1, &status, WNOHANG)) > 0) { }
        if (reaped < 0 && errno == ECHILD) { clean = 1; break; }
        tick();
    } while (now() < grace);
    if (!clean) result = 125;
    if (receipt(directory, "runner.result", (long)child, result)) result = 125;
    printf("RETRO_RUNNER_EXIT=%d CLEAN=%d\n", result, clean);
    close(directory);
    return result;
}
