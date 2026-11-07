// SPDX-License-Identifier: MIT
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>

static dev_t root_device;
static void inspect(long pid) {
    char path[96], comm[80] = "?", line[2048];
    snprintf(path, sizeof(path), "/proc/%ld/comm", pid);
    FILE *file = fopen(path, "r");
    if (file) { if (fgets(comm, sizeof(comm), file)) comm[strcspn(comm, "\n")] = 0; fclose(file); }
    printf("PROCESS pid=%ld comm=%s\n", pid, comm);
    snprintf(path, sizeof(path), "/proc/%ld/fd", pid);
    DIR *fds = opendir(path);
    struct dirent *entry;
    while (fds && (entry = readdir(fds))) {
        char *end;
        long fd = strtol(entry->d_name, &end, 10);
        if (!*entry->d_name || *end || fd < 0) continue;
        char target[1024]; struct stat info;
        snprintf(path, sizeof(path), "/proc/%ld/fd/%ld", pid, fd);
        if (stat(path, &info) || info.st_dev != root_device || !S_ISREG(info.st_mode)) continue;
        ssize_t n = readlink(path, target, sizeof(target)-1);
        if (n < 0) continue;
        target[n] = 0;
        snprintf(path, sizeof(path), "/proc/%ld/fdinfo/%ld", pid, fd);
        file = fopen(path, "r");
        if (!file) continue;
        unsigned long long flags = 0;
        while (fgets(line, sizeof(line), file)) if (sscanf(line, "flags: %llo", &flags) == 1) break;
        fclose(file);
        if ((flags & O_ACCMODE) != O_RDONLY)
            printf("FD_WRITER pid=%ld fd=%ld flags=%llo path=%s\n", pid, fd, flags, target);
    }
    if (fds) closedir(fds);
    snprintf(path, sizeof(path), "/proc/%ld/maps", pid);
    file = fopen(path, "r");
    if (!file) return;
    while (fgets(line, sizeof(line), file)) {
        char perms[5]; unsigned maj, min; int path_offset = 0;
        if (sscanf(line, "%*s %4s %*s %x:%x %*s %n", perms, &maj, &min, &path_offset) != 3 ||
            perms[1] != 'w' || perms[3] != 's') continue;
        int same_device = maj == major(root_device) && min == minor(root_device);
        // Btrfs subvolume stat devices can differ from maps' superblock
        // device. Use pathname metadata as a fallback, never file bytes.
        if (!same_device && path_offset > 0 && line[path_offset] == '/') {
            char name[2048]; struct stat mapped;
            snprintf(name, sizeof(name), "%s", line + path_offset);
            name[strcspn(name, "\n")] = 0;
            same_device = !stat(name, &mapped) && mapped.st_dev == root_device;
        }
        if (same_device) printf("MAP_WRITER pid=%ld %s", pid, line);
    }
    fclose(file);
}
int main(int argc, char **argv) {
    long selected = 0; const char *device_path = "/";
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--pid") && i+1 < argc) {
            char *end; selected = strtol(argv[++i], &end, 10);
            if (*end || selected <= 0) return 2;
        } else if (!strcmp(argv[i], "--device-path") && i+1 < argc) device_path = argv[++i];
        else return 2;
    }
    struct stat info;
    if (stat(device_path, &info)) { perror("stat device path"); return 1; }
    root_device = info.st_dev;
    printf("DEVICE=%u:%u\n", major(root_device), minor(root_device));
    if (selected) { inspect(selected); return 0; }
    DIR *proc = opendir("/proc");
    if (!proc) return 1;
    struct dirent *entry;
    while ((entry = readdir(proc))) {
        char *end; long pid = strtol(entry->d_name, &end, 10);
        if (*entry->d_name && !*end && pid > 0) inspect(pid);
    }
    closedir(proc);
    return 0;
}
