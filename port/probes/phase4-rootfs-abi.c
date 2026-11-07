/* SPDX-License-Identifier: MIT
 * Userspace smoke test, built only against the standalone firmware sysroot.
 * QEMU user-mode success does not validate the BSP kernel or hardware.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <gnu/libc-version.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/epoll.h>
#include <sys/eventfd.h>
#include <time.h>
#include <unistd.h>

static void *signal_event(void *arg) {
    int fd = *(int *)arg;
    uint64_t value = 1;
    return (void *)(uintptr_t)(write(fd, &value, sizeof value) != sizeof value);
}

int main(void) {
    struct timespec now;
    struct epoll_event event = {.events = EPOLLIN};
    pthread_t thread;
    void *thread_result;
    uint64_t value;
    Dl_info libc_info;
    int fd = eventfd(0, EFD_CLOEXEC);
    int epfd = epoll_create1(EPOLL_CLOEXEC);
    if (sizeof(void *) != 8 || fd < 0 || epfd < 0 ||
        clock_gettime(CLOCK_MONOTONIC, &now) ||
        epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &event) ||
        pthread_create(&thread, NULL, signal_event, &fd)) return 1;
    if (epoll_wait(epfd, &event, 1, 5000) != 1 ||
        read(fd, &value, sizeof value) != sizeof value || value != 1 ||
        pthread_join(thread, &thread_result) || thread_result) return 2;
    close(epfd);
    close(fd);
    void *libc_symbol = dlsym(RTLD_DEFAULT, "gnu_get_libc_version");
    if (!libc_symbol || !dladdr(libc_symbol, &libc_info)) return 3;
    printf("glibc=%s pointer_bits=%zu pthread/eventfd/epoll/clock=OK\n",
           gnu_get_libc_version(), sizeof(void *) * 8);
    printf("libc_path=%s\n", libc_info.dli_fname);
    return 0;
}
