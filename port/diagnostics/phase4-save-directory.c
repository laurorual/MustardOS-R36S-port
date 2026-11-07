// SPDX-License-Identifier: MIT
// C53 exclusive bootstrap only. Card/mount identity must be checked by caller.
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/fs.h>
#include <stdio.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/syscall.h>
#include <sys/vfs.h>
#include <unistd.h>

static int directory(int parent,const char *name,mode_t mode) {
    int fd=openat(parent,name,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    struct stat s;
    if(fd>=0 && (fstat(fd,&s) || s.st_uid || s.st_gid || (s.st_mode&07777)!=mode)) {
        close(fd);return -1;
    }
    return fd;
}
static int marker(int dir,const char *name,const char *text) {
    int fd=openat(dir,name,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(fd<0) return 0;
    size_t n=strlen(text);int ok=write(fd,text,n)==(ssize_t)n && !fsync(fd);
    if(close(fd)) ok=0;
    return ok;
}
int main(int argc,char **argv) {
    umask(077);
    const char prefix[]="/run/muos-prefs-data.";
    if(geteuid()!=0 || argc!=3 || strncmp(argv[1],prefix,sizeof(prefix)-1) ||
       strlen(argv[1])!=sizeof(prefix)-1+6 || strlen(argv[2])!=64 || strspn(argv[2],"0123456789abcdef")!=64) return 64;
    for(const char *p=argv[1]+sizeof(prefix)-1;*p;p++)
        if(!((*p>='A'&&*p<='Z')||(*p>='a'&&*p<='z')||(*p>='0'&&*p<='9'))) return 64;
    int run=-1,cap=-1,data=-1,muos=-1,top=-1,gb=-1,leaf=-1,rc=64;
    run=open("/run",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(run<0) goto done;
    cap=directory(run,argv[1]+5,0700);if(cap<0) goto done;
    struct statfs fs;struct stat parent,child;struct statvfs v;
    if(fstatfs(cap,&fs) || fs.f_type!=0x01021994) goto done;
    data=directory(cap,"data",0755);if(data<0) goto done;
    if(fstatfs(data,&fs) || fstatvfs(data,&v) || (v.f_flag&ST_RDONLY)) goto done;
#ifdef STORE_DIRECTORY_TEST
    if(fs.f_type!=0x01021994) goto done;
#else
    if(fs.f_type!=0xef53) goto done;
#endif
    // The existing C20 MUOS parent is root-owned0755. Preserve it; the newly
    // published subtree and every identity leaf remain private0700.
    muos=directory(data,"MUOS",0755);
    if(muos<0) muos=directory(data,"MUOS",0700);
    if(muos<0) goto done;
    if(fstat(data,&parent) || fstat(muos,&child) || parent.st_dev!=child.st_dev || flock(muos,LOCK_EX|LOCK_NB)) goto done;
    struct stat existing;
    if(!fstatat(muos,"port-saves-v1",&existing,AT_SYMLINK_NOFOLLOW) || errno!=ENOENT) goto done;
    // Never clean/adopt a stale transaction or overwrite an existing directory.
    if(mkdirat(muos,".port-saves-v1.c53-new",0700)) goto done;
    top=directory(muos,".port-saves-v1.c53-new",0700);if(top<0) goto done;
    rc=74;
    if(!marker(top,".muos-save-root-v1","MUOS-R35S-SAVE-ROOT-V1\n") || mkdirat(top,"gb",0700)) goto done;
    gb=directory(top,"gb",0700);if(gb<0 || mkdirat(gb,argv[2],0700)) goto done;
    leaf=directory(gb,argv[2],0700);if(leaf<0) goto done;
    if(!marker(leaf,".muos-saves-v1","MUOS-R35S-SAVES-V1\n") || fsync(leaf) || fsync(gb) || fsync(top)) goto done;
    if(syscall(SYS_renameat2,muos,".port-saves-v1.c53-new",muos,"port-saves-v1",RENAME_NOREPLACE)) goto done;
    // No automatic rollback if this final sync fails after publication.
    if(fsync(muos)) goto done;
    rc=0;puts("C53_SAVE_DIRECTORY_CREATED markers_synced=1 no_replace=1");
done:
    if(leaf>=0) close(leaf);
    if(gb>=0) close(gb);
    if(top>=0) close(top);
    if(muos>=0) close(muos);
    if(data>=0) close(data);
    if(cap>=0) close(cap);
    if(run>=0) close(run);
    if(rc) fputs("C53_SAVE_DIRECTORY_REFUSED\n",stderr);
    return rc;
}
