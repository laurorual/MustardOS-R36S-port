// SPDX-License-Identifier: MIT
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/loop.h>
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/sysmacros.h>
#include <sys/vfs.h>
#include <sys/wait.h>
#include <unistd.h>

/* Laboratory only. Never accepts a card/block-device/image path from argv.
 * The caller authenticates the board and hashes the payload before execution.
 * Only a fixed-size regular tmpfs image in an owned /run directory is eligible.
 * No formatter, partition ioctl, root remount, lazy unmount or loop adoption. */
static volatile sig_atomic_t stopped;
static volatile sig_atomic_t child;
static int loopfd=-1, attached, mounted;
static struct stat image_stat;
static char target[256], loopdev[64], executable[256], store[256];
static const char defaults[]="MUOS-PREFS-1\nVOLUME=100\nBRIGHTNESS=80\n";
static const char saved[]="MUOS-PREFS-1\nVOLUME=60\nBRIGHTNESS=75\n";

static void interrupt(int signum) {
    stopped=signum;
    if (child>0) kill((pid_t)child,SIGTERM);
}
static int root_ro(void) {
    struct statvfs v;
    return !statvfs("/",&v) && (v.f_flag&ST_RDONLY);
}
static int owned(const struct stat *s,mode_t mode,int regular) {
    return s->st_uid==0 && s->st_gid==0 && (s->st_mode&07777)==mode &&
           (regular ? S_ISREG(s->st_mode) && s->st_nlink==1 : S_ISDIR(s->st_mode));
}
static int same_loop(const struct stat *expected) {
    struct loop_info64 info={0};
    return attached && !ioctl(loopfd,LOOP_GET_STATUS64,&info) &&
           info.lo_device==(unsigned long long)expected->st_dev &&
           info.lo_inode==(unsigned long long)expected->st_ino &&
           !info.lo_offset && !info.lo_sizelimit && !info.lo_encrypt_type &&
           info.lo_flags==LO_FLAGS_AUTOCLEAR;
}
static int option(const char *list,const char *needle) {
    size_t size=strlen(needle);
    for (const char *p=list;*p;) {
        const char *end=strchr(p,',');
        size_t n=end ? (size_t)(end-p) : strlen(p);
        if (n==size && !memcmp(p,needle,n)) return 1;
        if (!end) break;
        p=end+1;
    }
    return 0;
}
static int ext4_mount(const struct stat *expected,int readonly) {
    struct stat s,device;struct statfs fs;struct statvfs v;
    if (!same_loop(expected) || !root_ro() || stat(target,&s) || fstat(loopfd,&device) ||
        s.st_dev!=device.st_rdev || statfs(target,&fs) || fs.f_type!=0xef53 ||
        statvfs(target,&v) || !!(v.f_flag&ST_RDONLY)!=readonly ||
        !(v.f_flag&ST_NOSUID) || !(v.f_flag&ST_NODEV) || !(v.f_flag&ST_NOEXEC)) return 0;
    FILE *f=fopen("/proc/self/mountinfo","re");if (!f) return 0;
    char *line=NULL;size_t capacity=0;int matches=0,valid=0;
    while (getline(&line,&capacity,f)>0) {
        unsigned id,parent,maj,min;char root[256],point[256],opts[256];
        if (sscanf(line,"%u %u %u:%u %255s %255s %255s",&id,&parent,&maj,&min,root,point,opts)!=7 ||
            strcmp(point,target)) continue;
        matches++;
        char *split=strstr(line," - ");char type[64],source[64];
        valid=split && sscanf(split+3,"%63s %63s",type,source)==2 &&
              !strcmp(type,"ext4") && !strcmp(source,loopdev) && !strcmp(root,"/") &&
              maj==major(device.st_rdev) && min==minor(device.st_rdev) &&
              option(opts,readonly ? "ro" : "rw") && option(opts,"nosuid") &&
              option(opts,"nodev") && option(opts,"noexec");
    }
    free(line);fclose(f);return matches==1 && valid;
}
static int invoke(const char *operation,int expected_rc,const char *expected_text) {
    int pipes[2];if (stopped || pipe2(pipes,O_CLOEXEC)) return 0;
    fflush(stdout);
    pid_t pid=fork();
    if (!pid) {
        if (dup2(pipes[1],STDOUT_FILENO)<0) _exit(127);
        close(pipes[0]);close(pipes[1]);
        if (!strcmp(operation,"save"))
            execl(executable,executable,"--dir",store,"save","60","75",(char *)NULL);
        else execl(executable,executable,"--dir",store,operation,(char *)NULL);
        _exit(127);
    }
    close(pipes[1]);
    if (pid<0) {close(pipes[0]);return 0;}
    child=pid;if (stopped) kill(pid,SIGTERM);
    int status=0;pid_t result;
    do {result=waitpid(pid,&status,0);} while (result<0 && errno==EINTR);
    child=0;
    char output[256];size_t n=0;
    while (n<sizeof(output)-1) {
        ssize_t got=read(pipes[0],output+n,sizeof(output)-1-n);
        if (got<0 && errno==EINTR) continue;
        if (got<=0) break;
        n+=(size_t)got;
    }
    close(pipes[0]);output[n]=0;
    return !stopped && result==pid && WIFEXITED(status) &&
           WEXITSTATUS(status)==expected_rc && !strcmp(output,expected_text);
}
static int checked_store(const struct stat *expected,const char *operation) {
    /* A false guard returns before executing the generic tmpfs-capable store. */
    if (!ext4_mount(expected,0)) return 64;
    return invoke(operation,0,!strcmp(operation,"init") ? defaults : saved) ? 0 : 74;
}
static int mount_image(int readonly) {
    if (stopped || !same_loop(&image_stat) || !root_ro()) return 0;
    if (mount(loopdev,target,"ext4",MS_NOSUID|MS_NODEV|MS_NOEXEC|(readonly ? MS_RDONLY : 0),"data=ordered")) return 0;
    mounted=1;
    return ext4_mount(&image_stat,readonly);
}
static int unmount_image(void) {
    if (!mounted || !same_loop(&image_stat) || umount2(target,0)) return 0;
    mounted=0;return root_ro();
}
int main(int argc,char **argv) {
    int rc=64,dir=-1,image=-1,control=-1;struct stat s;struct statfs fs;
    const char prefix[]="/run/muos-prefs-ext4.";
    umask(077);setvbuf(stdout,NULL,_IOLBF,0);
    if (geteuid()!=0 || (argc!=2 && argc!=3) ||
        (argc==3 && strcmp(argv[2],"--cancel-after-mount")) ||
        strncmp(argv[1],prefix,sizeof(prefix)-1) || strlen(argv[1])!=sizeof(prefix)-1+6) return 64;
    for (const char *p=argv[1]+sizeof(prefix)-1;*p;p++)
        if (!((*p>='A' && *p<='Z') || (*p>='a' && *p<='z') || (*p>='0' && *p<='9'))) return 64;
    int run=open("/run",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (run<0) return 64;
    dir=openat(run,argv[1]+5,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);close(run);
    if (dir<0 || fstat(dir,&s) || !owned(&s,0700,0) || fstatfs(dir,&fs) || fs.f_type!=0x01021994 ||
        !root_ro() || flock(dir,LOCK_EX|LOCK_NB)) goto cleanup;
    snprintf(executable,sizeof(executable),"%s/muos-preferences",argv[1]);
    snprintf(target,sizeof(target),"%s/mnt",argv[1]);
    snprintf(store,sizeof(store),"%s/mnt/store",argv[1]);
    int fd=openat(dir,"muos-preferences",O_RDONLY|O_NOFOLLOW|O_CLOEXEC);
    if (fd<0) goto cleanup;
    int executable_ok=!fstat(fd,&s) && owned(&s,0700,1);close(fd);
    if (!executable_ok) goto cleanup;
    fd=openat(dir,"mnt",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (fd<0) goto cleanup;
    int mountpoint_ok=!fstat(fd,&s) && owned(&s,0700,0) && !fstatfs(fd,&fs) && fs.f_type==0x01021994;
    close(fd);if (!mountpoint_ok) goto cleanup;
    image=openat(dir,"data.ext4",O_RDWR|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if (image<0 || fstat(image,&image_stat) || !owned(&image_stat,0600,1) ||
        image_stat.st_size!=16*1024*1024 || flock(image,LOCK_EX|LOCK_NB)) goto cleanup;
    /* Both files must belong to this exact tmpfs, not a bind to persistent media. */
    if (fstat(dir,&s) || image_stat.st_dev!=s.st_dev) goto cleanup;
    control=open("/dev/loop-control",O_RDWR|O_NOFOLLOW|O_CLOEXEC);
    if (control<0 || fstat(control,&s) || !S_ISCHR(s.st_mode) || major(s.st_rdev)!=10 || minor(s.st_rdev)!=237) goto cleanup;
    int number=ioctl(control,LOOP_CTL_GET_FREE);
    if (number<0 || number>7) goto cleanup;
    snprintf(loopdev,sizeof(loopdev),"/dev/loop%d",number);
    loopfd=open(loopdev,O_RDWR|O_NOFOLLOW|O_CLOEXEC);
    if (loopfd<0 || fstat(loopfd,&s) || !S_ISBLK(s.st_mode) || major(s.st_rdev)!=7 || minor(s.st_rdev)!=(unsigned)number) goto cleanup;
    struct loop_info64 info={0};errno=0;
    if (!ioctl(loopfd,LOOP_GET_STATUS64,&info) || errno!=ENXIO) goto cleanup;
    struct stat original_ns,current_ns;
    if (stat("/proc/self/ns/mnt",&original_ns) || unshare(CLONE_NEWNS) ||
        mount(NULL,"/",NULL,MS_REC|MS_PRIVATE,NULL) || stat("/proc/self/ns/mnt",&current_ns) ||
        current_ns.st_ino==original_ns.st_ino || !root_ro()) goto cleanup;
    struct sigaction action={0};action.sa_handler=interrupt;sigemptyset(&action.sa_mask);
    sigaction(SIGTERM,&action,NULL);sigaction(SIGINT,&action,NULL);sigaction(SIGALRM,&action,NULL);
    signal(SIGPIPE,SIG_IGN);alarm(45);
    if (ioctl(loopfd,LOOP_SET_FD,image)) goto cleanup; /* Busy loop is never replaced. */
    attached=1;info=(struct loop_info64){0};info.lo_flags=LO_FLAGS_AUTOCLEAR;
    if (ioctl(loopfd,LOOP_SET_STATUS64,&info) || !same_loop(&image_stat)) goto cleanup;
    rc=74;
    if (checked_store(&image_stat,"init")!=64) goto cleanup;
    puts("PASS absent-ext4-mount-refused-before-store");
    if (!mount_image(0)) goto cleanup;
    puts("PASS owned-ext4-rw-private-namespace-root-ro");
    if (argc==3) {rc=0;raise(SIGTERM);goto cleanup;}
    struct stat wrong=image_stat;wrong.st_ino++;
    if (checked_store(&wrong,"init")!=64) goto cleanup;
    puts("PASS wrong-backing-inode-refused-before-store");
    if (mkdir(store,0700)) goto cleanup;
    char marker[300];snprintf(marker,sizeof(marker),"%s/.muos-preferences-v1",store);
    fd=open(marker,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if (fd<0) goto cleanup;
    const char text[]="MUOS-R35S-PREFS-V1\n";
    int marker_ok=write(fd,text,sizeof(text)-1)==(ssize_t)sizeof(text)-1 && !fsync(fd);
    if (close(fd)) marker_ok=0;
    if (!marker_ok) goto cleanup;
    fd=open(store,O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    if (fd<0) goto cleanup;
    int sync_ok=!fsync(fd);close(fd);if (!sync_ok) goto cleanup;
    if (checked_store(&image_stat,"init") || checked_store(&image_stat,"save")) goto cleanup;
    puts("PASS defaults-once-and-save-60-75-on-ext4");
    if (!unmount_image() || checked_store(&image_stat,"load")!=64) goto cleanup;
    puts("PASS unmounted-store-refused");
    if (!mount_image(0) || !invoke("init",0,saved) || !invoke("load",0,saved)) goto cleanup;
    puts("PASS saved-60-75-survive-unmount-remount-and-init");
    if (!unmount_image() || !mount_image(1) || checked_store(&image_stat,"save")!=64 ||
        !invoke("save",64,"") || !invoke("load",64,"")) goto cleanup;
    puts("PASS readonly-media-refused");
    if (!unmount_image() || !mount_image(0) || !invoke("load",0,saved)) goto cleanup;
    puts("PASS readonly-refusal-preserves-record");
    rc=0;
cleanup:
    alarm(0);
    if (mounted && !unmount_image()) {fputs("CLEANUP_UNMOUNT_FAILED\n",stderr);rc=74;}
    if (attached && !mounted) {
        /* SET_STATUS failure can leave flags unset: inode/dev remain ownership. */
        struct loop_info64 current={0};
        if (ioctl(loopfd,LOOP_GET_STATUS64,&current) || current.lo_inode!=(unsigned long long)image_stat.st_ino ||
            current.lo_device!=(unsigned long long)image_stat.st_dev || ioctl(loopfd,LOOP_CLR_FD,0)) {
            fputs("CLEANUP_LOOP_FAILED\n",stderr);rc=74;
        } else {attached=0;puts("PASS owned-loop-detached");}
    }
    if (loopfd>=0) close(loopfd);
    if (control>=0) close(control);
    if (image>=0) close(image);
    if (dir>=0) close(dir);
    if (!root_ro()) rc=74;
    if (stopped && rc!=74) rc=128+stopped;
    if (!mounted && !attached && !rc) puts("EXT4_LAB_OK_ROOT_RO_NO_CARD_WRITES");
    return rc;
}
