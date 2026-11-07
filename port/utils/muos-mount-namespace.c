// SPDX-License-Identifier: MIT
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <sys/mount.h>
#include <unistd.h>

/* A temporary diagnostic launcher, run only by the already authenticated root. */
int main(int argc, char **argv) {
    if (geteuid() != 0 || argc < 2 || argv[1][0] != '/') return 64;
    if (unshare(CLONE_NEWNS) || mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL)) {
        perror("mount namespace");
        return 125;
    }
    execv(argv[1], argv + 1);
    perror("namespace exec");
    return 127;
}
