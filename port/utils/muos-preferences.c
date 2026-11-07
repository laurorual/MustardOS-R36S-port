// SPDX-License-Identifier: MIT
#define _GNU_SOURCE
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/vfs.h>
#include <unistd.h>

#define MARKER "MUOS-R35S-PREFS-V1\n"
#define PREFS "preferences"
#define TEMP ".preferences.new"
struct prefs { unsigned volume, brightness; };

static int safe_dir(const char *path) {
    if (!path || path[0]!='/' || path[1]==0 || strlen(path)>4095) return -1;
    char copy[4096];strcpy(copy,path);
    int fd=open("/",O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    char *p=copy+1;
    while (fd>=0) {
        char *slash=strchr(p,'/');
        if (slash) *slash=0;
        if (!*p || !strcmp(p,".") || !strcmp(p,"..")) {close(fd);return -1;}
        int next=openat(fd,p,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
        close(fd);fd=next;
        if (!slash) break;
        p=slash+1;
    }
    if (fd<0) return -1;
    struct stat s;struct statfs fs;struct statvfs vfs;
    if (fstat(fd,&s) || s.st_uid!=0 || s.st_gid!=0 || (s.st_mode&07777)!=0700 ||
        fstatfs(fd,&fs) || (fs.f_type!=0xef53 && fs.f_type!=0x01021994) ||
        fstatvfs(fd,&vfs) || (vfs.f_flag&ST_RDONLY)) {close(fd);return -1;}
    return fd;
}
static int regular(int fd,off_t maximum) {
    struct stat s;
    return fstat(fd,&s)==0 && S_ISREG(s.st_mode) && s.st_uid==0 && s.st_gid==0 &&
           (s.st_mode&07777)==0600 && s.st_nlink==1 && s.st_size>=0 && s.st_size<=maximum;
}
static int get_file(int dir,const char *name,char *buffer,size_t size) {
    int fd=openat(dir,name,O_RDONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);
    if (fd<0) return errno==ENOENT ? 3 : 64;
    if (!regular(fd,(off_t)size-1)) {close(fd);return 64;}
    ssize_t n=read(fd,buffer,size-1);
    int e=errno;close(fd);errno=e;
    if (n<0) return 74;
    buffer[n]=0;
    return strlen(buffer)==(size_t)n ? 0 : 64;
}
static int render(char *out,size_t size,const struct prefs *p) {
    return snprintf(out,size,"MUOS-PREFS-1\nVOLUME=%u\nBRIGHTNESS=%u\n",p->volume,p->brightness);
}
static int parse(const char *text,struct prefs *p) {
    int consumed=0;
    if (sscanf(text,"MUOS-PREFS-1\nVOLUME=%u\nBRIGHTNESS=%u\n%n",&p->volume,&p->brightness,&consumed)!=2 ||
        !consumed || p->volume>100 || p->brightness<40 || p->brightness>160) return 64;
    char canonical[96];render(canonical,sizeof(canonical),p);
    return strcmp(text,canonical) ? 64 : 0;
}
static int number(const char *text,unsigned max,unsigned *value) {
    size_t n=strlen(text);
    if (!n || n>3 || (n>1 && text[0]=='0')) return 64;
    unsigned v=0;
    for (size_t i=0;i<n;i++) {
        if (!isdigit((unsigned char)text[i])) return 64;
        v=v*10+(unsigned)(text[i]-'0');
    }
    if (v>max) return 64;
    *value=v;return 0;
}
static int sync_file(int fd,int directory) {
#ifdef PREFS_TEST
    const char *failure=getenv("PREFS_TEST_FAILURE");
    if (failure && !strcmp(failure,directory ? "directory-sync" : "file-sync")) {
        errno=EIO;return -1;
    }
#else
    (void)directory;
#endif
    return fsync(fd);
}
static int replace(int dir,const struct prefs *p) {
    char text[96];int size=render(text,sizeof(text),p);
    int fd=openat(dir,TEMP,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if (fd<0) return 74; /* Preserve unknown/stale staging files for diagnosis. */
    int rc=74;size_t done=0;
    while (done<(size_t)size) {
        ssize_t n=write(fd,text+done,(size_t)size-done);
        if (n<0 && errno==EINTR) continue;
        if (n<=0) goto before_commit;
        done+=(size_t)n;
    }
    if (sync_file(fd,0)) goto before_commit;
    if (close(fd)) {fd=-1;goto before_commit;}
    fd=-1;
    if (renameat(dir,TEMP,dir,PREFS)) goto before_commit;
    /* After rename the new record is visible. Failure means durability unknown;
       never restore defaults or roll back a potentially committed preference. */
    return sync_file(dir,1) ? 74 : 0;
before_commit:
    if (fd>=0) close(fd);
    unlinkat(dir,TEMP,0);
    return rc;
}
int main(int argc,char **argv) {
    umask(077);
    if (geteuid()!=0 || (argc!=4 && argc!=6) || strcmp(argv[1],"--dir")) return 64;
    const char *operation=argv[3];
    if (strcmp(operation,"init") && strcmp(operation,"load") && strcmp(operation,"save")) return 64;
    if ((strcmp(operation,"save")==0 ? 6 : 4)!=argc) return 64;
    struct prefs desired={100,80},old={0};
    if (!strcmp(operation,"save") &&
        (number(argv[4],100,&desired.volume) || number(argv[5],160,&desired.brightness) || desired.brightness<40)) return 64;
    int dir=safe_dir(argv[2]);if (dir<0) return 64;
    char text[128];
    int rc=get_file(dir,".muos-preferences-v1",text,sizeof(text));
    if (rc || strcmp(text,MARKER)) {close(dir);return 64;}
    int lock=openat(dir,".lock",O_RDWR|O_CREAT|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC,0600);
    if (lock<0 || !regular(lock,0)) {if (lock>=0)close(lock);close(dir);return 64;}
    if (flock(lock,LOCK_EX|LOCK_NB)) {close(lock);close(dir);return 75;}
    rc=get_file(dir,PREFS,text,sizeof(text));
    if (!rc) rc=parse(text,&old);
    if (!strcmp(operation,"load")) {
        if (!rc) fputs(text,stdout);
    } else if (!strcmp(operation,"init")) {
        if (rc==3) {rc=replace(dir,&desired);if (!rc) {render(text,sizeof(text),&desired);fputs(text,stdout);}}
        else if (!rc) fputs(text,stdout);
    } else if (!rc) {
        if (old.volume!=desired.volume || old.brightness!=desired.brightness) rc=replace(dir,&desired);
        if (!rc) {render(text,sizeof(text),&desired);fputs(text,stdout);}
    }
    close(lock);close(dir);
    return rc;
}
