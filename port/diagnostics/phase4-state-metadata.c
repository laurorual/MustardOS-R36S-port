// SPDX-License-Identifier: MIT
// Owned, read-only PKST metadata inspector. Never prints content or manifests.
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/vfs.h>
#include <unistd.h>
#include <zlib.h>

static void reject(void) { fputs("C51_STATE_REJECTED\n", stderr); exit(64); }
static void require(int ok) { if (!ok) reject(); }
static uint32_t le32(const unsigned char *p) {
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static unsigned char *read_file(int dir, const char *name, size_t limit, size_t *len) {
    int fd = openat(dir, name, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK);
    require(fd >= 0);
    struct stat s; struct statfs fs;
    require(fstat(fd, &s) == 0 && fstatfs(fd, &fs) == 0);
    require(S_ISREG(s.st_mode) && s.st_uid == geteuid() && s.st_gid == getegid()
            && (s.st_mode & 07777) == 0600 && s.st_nlink == 1
            && fs.f_type == 0x01021994 && s.st_size > 0 && (uint64_t)s.st_size <= limit);
    *len = (size_t)s.st_size;
    unsigned char *data = calloc(*len + 1, 1); require(data != NULL);
    size_t done = 0;
    while (done < *len) {
        ssize_t n = read(fd, data + done, *len - done); require(n > 0); done += (size_t)n;
    }
    unsigned char extra; require(read(fd, &extra, 1) == 0); require(close(fd) == 0);
    return data;
}
static char *trim(char *p) {
    while (*p == ' ' || *p == '\t' || *p == '\r') ++p;
    size_t n = strlen(p);
    while (n && (p[n-1] == ' ' || p[n-1] == '\t' || p[n-1] == '\r')) p[--n] = 0;
    return p;
}
int main(int argc, char **argv) {
    require(argc == 2);
    int dir = open(argv[1], O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    require(dir >= 0);
    struct stat s; struct statfs fs;
    require(fstat(dir, &s) == 0 && fstatfs(dir, &fs) == 0);
    require(S_ISDIR(s.st_mode) && s.st_uid == geteuid() && s.st_gid == getegid()
            && (s.st_mode & 07777) == 0700 && fs.f_type == 0x01021994);
    size_t n = 0; unsigned char *data = read_file(dir, "quicksave.state", 8*1024*1024, &n);
    require(n >= 32 && memcmp(data, "PKST", 4) == 0 && data[4] == 1 && data[5] == 0);
    // This diagnostic disables achievements; refuse other envelope variants.
    require(data[6] == 0 && data[7] == 0 && le32(data+12) == 0 && le32(data+20) == 0);
    for (size_t i = 24; i < 32; ++i) require(data[i] == 0);
    uint32_t core = le32(data+8); require(core > 0 && (uint64_t)core + 32 == n);
    require((uint32_t)crc32(0, data+32, core) == le32(data+16));
    free(data);
    data = read_file(dir, "states.ini", 16384, &n);
    require(memchr(data, 0, n) == NULL);
    unsigned fields = 0; int group = 0, seen = 0; char *save = NULL;
    const char *keys[] = {"name", "created", "crc", "core", "core_version"};
    for (char *line = strtok_r((char *)data, "\n", &save); line; line = strtok_r(NULL, "\n", &save)) {
        char *p = trim(line);
        if (*p == '[') {
            group = strcmp(p, "[quicksave]") == 0;
            if (group) require(++seen == 1);
        } else if (group && *p && *p != ';' && *p != '#') {
            char *eq = strchr(p, '='); require(eq != NULL); *eq = 0;
            char *key = trim(p), *value = trim(eq+1);
            for (unsigned i = 0; i < 5; ++i) if (strcmp(key, keys[i]) == 0) {
                require(*value != 0 && !(fields & (1u<<i))); fields |= 1u<<i;
            }
        }
    }
    require(seen == 1 && fields == 31); free(data);
    data = read_file(dir, "quicksave.png", 2*1024*1024, &n);
    require(n >= 8 && memcmp(data, "\x89PNG\r\n\x1a\n", 8) == 0); free(data);
    require(close(dir) == 0);
    printf("C51_STATE_VALID version=1 core_bytes=%u core_crc_valid=1 manifest_valid=1 thumbnail_signature_valid=1 tmpfs=1\n", core);
    return 0;
}
