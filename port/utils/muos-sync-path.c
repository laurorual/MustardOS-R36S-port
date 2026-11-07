// SPDX-License-Identifier: MIT
// Bounded fsync of root-owned regular files/directories; no content reads.
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <sys/vfs.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if (geteuid() != 0 || argc < 2 || argc > 6) return 64;
    for (int i = 1; i < argc; ++i) {
        if (argv[i][0] != '/') return 64;
        int fd = open(argv[i], O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC);
        struct stat st;
        struct statfs fs;
        if (fd < 0) return 64;
        int valid = !fstat(fd, &st) && !fstatfs(fd, &fs) && st.st_uid == 0 && !(st.st_mode & 0022)
            && (S_ISDIR(st.st_mode) || (S_ISREG(st.st_mode) && st.st_nlink == 1))
            && (fs.f_type == 0xef53 || fs.f_type == 0x01021994);
        if (!valid) { close(fd); return 64; }
        int result = fsync(fd);
        if (close(fd) || result) return 74;
    }
    return 0;
}
