// SPDX-License-Identifier: MIT
// Small foreground owner of the native UI processes. Never reboots/restarts.
#include <errno.h>
#include <dirent.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define STATE "/run/muos/ui/"
static volatile sig_atomic_t stop_signal;
struct identity { pid_t pid; unsigned long long start; };
static void request_stop(int sig) { stop_signal = sig; }
static void tick(void) { struct timespec t = {0, 100000000}; nanosleep(&t, NULL); }

static int process(struct identity id) {
    char path[80], line[4096];
    snprintf(path, sizeof(path), "/proc/%ld/stat", (long)id.pid);
    FILE *f = fopen(path, "r");
    if (!f) return 0;
    char *ok = fgets(line, sizeof(line), f); fclose(f);
    if (!ok) return 0;
    char *p = strrchr(line, ')');
    if (!p || p[1] != ' ' || p[2] == 'Z') return 0;
    p += 2;
    char *save = NULL, *field = strtok_r(p, " ", &save);
    for (int n = 3; field && n < 22; n++) field = strtok_r(NULL, " ", &save);
    if (!field) return 0;
    unsigned long long start = strtoull(field, NULL, 10);
    return id.start ? start == id.start : 1;
}
static int read_id(const char *path, struct identity *id) {
    FILE *f = fopen(path, "r");
    if (!f) return 0;
    int ok = fscanf(f, "%d %llu", &id->pid, &id->start) == 2;
    fclose(f);
    return ok && id->pid > 1 && id->start && process(*id);
}
static unsigned long long own_start(void) {
    char line[4096];
    FILE *f = fopen("/proc/self/stat", "r");
    if (!f) return 0;
    char *ok = fgets(line, sizeof(line), f); fclose(f);
    char *p = ok ? strrchr(line, ')') : NULL, *save = NULL;
    if (!p) return 0;
    char *field = strtok_r(p + 2, " ", &save);
    for (int n = 3; field && n < 22; n++) field = strtok_r(NULL, " ", &save);
    return field ? strtoull(field, NULL, 10) : 0;
}
static int write_text(const char *path, const char *text) {
    FILE *f = fopen(path, "w");
    if (!f) return -1;
    int ok = fputs(text, f) >= 0;
    return fclose(f) || !ok ? -1 : 0;
}
static pid_t spawn(const char *program) {
    pid_t parent = getpid(), pid = fork();
    if (pid == 0) {
        if (setpgid(0, 0) || prctl(PR_SET_PDEATHSIG, SIGTERM) || getppid() != parent) _exit(126);
        signal(SIGTERM, SIG_DFL); signal(SIGINT, SIG_DFL); signal(SIGHUP, SIG_DFL);
        execl(program, program, (char *)NULL);
        perror(program); _exit(127);
    }
    if (pid > 0) setpgid(pid, pid);
    return pid;
}
static int adopted_signal(int sig) {
    // Upstream run_exec can setsid()+double-fork. Subreaper ownership keeps
    // these helpers as our children even after they leave the UI's group.
    DIR *dir = opendir("/proc");
    if (!dir) return -1;
    struct dirent *entry;
    int found = 0;
    while ((entry = readdir(dir))) {
        char *end;
        long number = strtol(entry->d_name, &end, 10);
        if (*end || number <= 1 || number == getpid()) continue;
        char path[80], line[4096];
        snprintf(path, sizeof(path), "/proc/%ld/stat", number);
        FILE *f = fopen(path, "r");
        if (!f) continue;
        char *ok = fgets(line, sizeof(line), f); fclose(f);
        char *p = ok ? strrchr(line, ')') : NULL, *save = NULL;
        if (!p) continue;
        char *field = strtok_r(p + 2, " ", &save);
        if (!field || *field == 'Z') continue;
        field = strtok_r(NULL, " ", &save);
        if (!field || strtol(field, NULL, 10) != getpid()) continue;
        for (int n = 4; field && n < 22; n++) field = strtok_r(NULL, " ", &save);
        if (!field) continue;
        struct identity id = {(pid_t)number, strtoull(field, NULL, 10)};
        if (id.start && process(id)) {
            found++;
            if (kill(id.pid, sig) && errno != ESRCH) perror("signal adopted UI helper");
        }
    }
    closedir(dir);
    return found;
}
int main(int argc, char **argv) {
    struct identity owner = {0}, input = {0};
    if (argc == 2 && !strcmp(argv[1], "--status"))
        return read_id(STATE "manager", &owner) && !access(STATE "ready", F_OK) ? 0 : 3;
    if (argc == 2 && !strcmp(argv[1], "--stop")) {
        if (!read_id(STATE "manager", &owner)) return 0;
        if (kill(owner.pid, SIGTERM) && errno != ESRCH) return 1;
        for (int i = 0; i < 70; i++) { if (!process(owner)) return 0; tick(); }
        fputs("UI supervisor did not stop before deadline\n", stderr); return 1;
    }
    if (argc != 2 || (strcmp(argv[1], "0") && strcmp(argv[1], "1"))) return 2;
    int lock = open(STATE "owner.lock", O_CREAT | O_RDWR | O_CLOEXEC, 0600);
    if (lock < 0 || flock(lock, LOCK_EX | LOCK_NB)) return 1;
    if (access("/run/muos/core/ready", F_OK) || access("/run/muos/input-ready/ready", F_OK) ||
        !read_id("/run/muos/input-ready/input.identity", &input)) return 1;
    unlink("/run/muos/first_paint");
    char text[256];
    unsigned long long start = own_start();
    if (!start) return 1;
    snprintf(text, sizeof(text), "%ld %llu\n", (long)getpid(), start);
    if (write_text(STATE "manager", text)) return 1;
    int log = open(STATE "supervisor.log", O_CREAT | O_WRONLY | O_APPEND | O_CLOEXEC, 0600);
    if (log < 0) { unlink(STATE "manager"); return 1; }
    dup2(log, STDOUT_FILENO); dup2(log, STDERR_FILENO); close(log);
    setvbuf(stdout, NULL, _IOLBF, 0);
    struct sigaction sa = {.sa_handler = request_stop};
    sigemptyset(&sa.sa_mask);
    sigaction(SIGTERM, &sa, NULL); sigaction(SIGINT, &sa, NULL); sigaction(SIGHUP, &sa, NULL);
    // Reap orphaned helper grandchildren after their process group is stopped.
    if (prctl(PR_SET_CHILD_SUBREAPER, 1)) { unlink(STATE "manager"); close(lock); return 1; }
    pid_t children[2] = {-1, -1};
    int active[2] = {0}, groups[2] = {0}, count = !strcmp(argv[1], "1") ? 2 : 1;
    const char *reason = "stop";
    int result = 0, iterations = 0;
    for (int i = 0; i < count; i++) {
        children[i] = spawn(i ? "/opt/muos/frontend/muhotkey" : "/opt/muos/frontend/muxfrontend");
        if (children[i] <= 0) { result = 1; reason = "fork_failed"; break; }
        active[i] = 1;
        groups[i] = 1;
        printf("CHILD %s %ld\n", i ? "hotkey" : "frontend", (long)children[i]);
    }
    for (; !result && !stop_signal; iterations++) {
        if (!process(input) || access("/run/muos/input-ready/ready", F_OK) || access("/run/muos/core/ready", F_OK)) {
            reason = "input_or_core_lost"; result = 1; break;
        }
        for (int i = 0; i < count; i++) {
            int status;
            pid_t ended = waitpid(children[i], &status, WNOHANG);
            if (ended == children[i]) {
                active[i] = 0; result = 1; reason = "child_exited";
                printf("EXIT %ld status=%d\n", (long)ended, status);
            }
        }
        if (result) break;
        struct stat painted;
        int first_paint = !stat("/run/muos/first_paint", &painted) && S_ISREG(painted.st_mode) && painted.st_size > 0;
        if (iterations >= 3 && first_paint && access(STATE "ready", F_OK) &&
            write_text(STATE "ready", "processes alive and fresh first_paint observed\n")) {
            reason = "ready_write_failed"; result = 1; break;
        }
        if (iterations >= 100 && !first_paint) {
            reason = "first_paint_timeout"; result = 1; break;
        }
        tick();
    }
    unlink(STATE "ready");
    printf("STOP reason=%s signal=%d\n", reason, (int)stop_signal);
    // Signal the complete owned groups, including helper scripts/descendants.
    for (int i = 0; i < count; i++) if (children[i] > 0) kill(-children[i], SIGTERM);
    for (int n = 0; n < 30; n++) {
        pid_t ended;
        while ((ended = waitpid(-1, NULL, WNOHANG)) > 0)
            for (int i = 0; i < count; i++) if (ended == children[i]) active[i] = 0;
        int any = adopted_signal(SIGTERM);
        if (any < 0) any = 1;
        for (int i = 0; i < count; i++) if (groups[i]) {
            if (kill(-children[i], 0) == 0) any = 1;
            else if (errno == ESRCH) groups[i] = 0;
        }
        if (!any) break;
        tick();
    }
    for (int i = 0; i < count; i++) if (groups[i]) kill(-children[i], SIGKILL);
    for (int i = 0; i < count; i++) if (active[i]) while (waitpid(children[i], NULL, 0) < 0 && errno == EINTR) {}
    for (int n = 0; n < 20; n++) {
        while (waitpid(-1, NULL, WNOHANG) > 0) {}
        if (adopted_signal(SIGKILL) == 0) break;
        tick();
    }
    while (waitpid(-1, NULL, WNOHANG) > 0) {}
    if (result) { snprintf(text, sizeof(text), "%s\n", reason); write_text(STATE "failed", text); }
    unlink(STATE "manager");
    close(lock);
    return result;
}
