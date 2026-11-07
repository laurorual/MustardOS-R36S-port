// SPDX-License-Identifier: MIT
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <glob.h>
#include <linux/usbdevice_fs.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/utsname.h>
#include <time.h>
#include <unistd.h>

struct request {
    const char *label;
    unsigned char type, request;
    unsigned short value, length;
};
static const struct request plan[] = {
    {"descriptor", 0x80, 6, 0x0100, 18},
    {"configuration", 0x80, 8, 0, 1},
    {"status", 0x80, 0, 0, 2},
    {"chip_id", 0xc0, 5, 0x00fc, 1},
    {"descriptor_after", 0x80, 6, 0x0100, 18},
    {"configuration_after", 0x80, 8, 0, 1},
    {"status_after", 0x80, 0, 0, 2}
};
typedef int (*transport_fn)(int, unsigned long, void *);
static int transport(int fd, unsigned long op, void *arg) {
    return ioctl(fd, op, arg);
}
static long long milliseconds(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) return 0;
    return (long long)t.tv_sec * 1000 + t.tv_nsec / 1000000;
}
static int identity(const unsigned char *data, int n) {
    return n == 18 && data[0] == 18 && data[1] == 1 &&
           data[8] == 0xda && data[9] == 0x0b &&
           data[10] == 0x20 && data[11] == 0xc8;
}
static int run_plan(int fd, const char *phase, transport_fn call) {
    printf("MUOS-C16-USB-CONTROL-V1\nPHASE=%s\n", phase);
    int failures = 0;
    for (size_t i = 0; i < sizeof(plan)/sizeof(plan[0]); ++i) {
        unsigned char data[18] = {0};
        const struct request *r = &plan[i];
        struct usbdevfs_ctrltransfer ctrl = {
            .bRequestType=r->type, .bRequest=r->request, .wValue=r->value,
            .wIndex=0, .wLength=r->length, .timeout=500, .data=data
        };
        long long start=milliseconds();
        errno=0;
        int n=call(fd, USBDEVFS_CONTROL, &ctrl);
        int saved_errno=errno;
        long long elapsed=milliseconds()-start;
        int rc=n < 0 ? -(saved_errno ? saved_errno : EIO) : n;
        int match=-1;
        if (n == r->length) {
            if (r->request == 6) match=identity(data,n);
            else if (r->request == 8) match=data[0] == 1;
            else if (r->type == 0xc0) match=data[0] == 0x09;
            else match=(data[0] & 0xfc) == 0 && data[1] == 0;
        }
        printf("READ=%s RC=%d EXPECTED=%u ELAPSED_MS=%lld MATCH=%d\n",
               r->label,rc,r->length,elapsed,match);
        if (n != r->length || !match) failures++;
        /* A returned descriptor for another identity forbids any vendor read. */
        if (r->request == 6 && n == 18 && !identity(data,n)) return 64;
    }
    printf("READ_FAILURES=%d\n",failures);
    /* Observation completion is distinct from successful hardware reads. */
    return 0;
}
static int read_text(const char *path, char *out, size_t size) {
    int fd=open(path,O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    if (fd < 0) return -1;
    ssize_t n=read(fd,out,size-1);
    close(fd);
    if (n <= 0) return -1;
    out[n]=0;
    while (n > 0 && (out[n-1]=='\n' || out[n-1]==' ')) out[--n]=0;
    return 0;
}
static int board_guard(void) {
    struct utsname u;
    char text[128], a[128], b[128];
    if (geteuid()!=0 || uname(&u) || strcmp(u.release,"4.4.189-muos-r35s-p4")) return 64;
    if (read_text("/sys/firmware/devicetree/base/model",text,sizeof(text)) ||
        strcmp(text,"R36S-V12 2023-08-18 Panel 0")) return 64;
    if (read_text("/proc/sys/kernel/tainted",text,sizeof(text)) || strcmp(text,"0")) return 64;
    ssize_t na=readlink("/proc/self/ns/mnt",a,sizeof(a)-1);
    ssize_t nb=readlink("/proc/1/ns/mnt",b,sizeof(b)-1);
    if (na<=0 || nb<=0 || na!=nb || memcmp(a,b,(size_t)na)) return 64;
    return 0;
}
#ifndef USB_CONTROL_TEST
int main(int argc, char **argv) {
    setvbuf(stdout,NULL,_IOLBF,0);
    if (argc!=2 || (strcmp(argv[1],"baseline") && strcmp(argv[1],"retained-pre") &&
                   strcmp(argv[1],"retained-post") && strcmp(argv[1],"replug"))) return 2;
    if (board_guard()) return 64;
    glob_t paths={0};
    if (glob("/sys/bus/usb/devices/*",0,NULL,&paths)) return 64;
    char selected[512]={0}, path[640], text[128];
    unsigned bus=0,dev=0;
    int found=0;
    for (size_t i=0;i<paths.gl_pathc;i++) {
        const char *base=paths.gl_pathv[i];
        snprintf(path,sizeof(path),"%s/idVendor",base);
        if (read_text(path,text,sizeof(text)) || strcmp(text,"0bda")) continue;
        snprintf(path,sizeof(path),"%s/idProduct",base);
        if (read_text(path,text,sizeof(text)) || strcmp(text,"c820")) continue;
        if (++found > 1 || strlen(base)>=sizeof(selected)) break;
        strcpy(selected,base);
    }
    globfree(&paths);
    if (found!=1 || !selected[0]) return 64;
    snprintf(path,sizeof(path),"%s/busnum",selected);
    if (read_text(path,text,sizeof(text)) || sscanf(text,"%u",&bus)!=1) return 64;
    snprintf(path,sizeof(path),"%s/devnum",selected);
    if (read_text(path,text,sizeof(text)) || sscanf(text,"%u",&dev)!=1) return 64;
    if (!bus || bus>255 || !dev || dev>127) return 64;
    snprintf(path,sizeof(path),"/dev/bus/usb/%03u/%03u",bus,dev);
    int fd=open(path,O_RDWR|O_CLOEXEC|O_NOFOLLOW);
    if (fd < 0) return 64;
    struct stat st;
    unsigned char descriptor[18];
    if (fstat(fd,&st) || !S_ISCHR(st.st_mode) || major(st.st_rdev)!=189 ||
        minor(st.st_rdev)!=(bus-1)*128+dev-1 ||
        pread(fd,descriptor,sizeof(descriptor),0)!=18 || !identity(descriptor,18)) {
        close(fd);return 64;
    }
    int rc=run_plan(fd,argv[1],transport);
    close(fd);
    return rc;
}
#endif
