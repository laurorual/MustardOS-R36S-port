// SPDX-License-Identifier: MIT
// Explicit, bounded three-file snapshots. Platform/card validation is the caller's job.
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/vfs.h>
#include <unistd.h>
#include <zlib.h>

#define MARKER "MUOS-R35S-SAVES-V1\n"
#define LIMIT_GENERATIONS 32u
static const char *names[]={"quicksave.state","states.ini","quicksave.png"};
static const size_t limits[]={8*1024*1024,16384,2*1024*1024};
struct blob { unsigned char *p; size_t n; };
struct head { unsigned current,previous,next; };
static void discard(struct blob *b) { free(b->p); b->p=NULL; b->n=0; }
static uint32_t le32(const unsigned char *p) {
    return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
}
static void put32(unsigned char *p,uint32_t v) { for(unsigned i=0;i<4;i++) p[i]=(unsigned char)(v>>(8*i)); }
static int sync_step(int fd,const char *step) {
#ifdef SAVE_STORE_TEST
    const char *fault=getenv("SAVE_STORE_FAILURE");
    if(fault && !strcmp(fault,step)) { errno=EIO;return -1; }
#else
    (void)step;
#endif
    return fsync(fd);
}
static int regular(int fd,size_t limit) {
    struct stat s;
    return !fstat(fd,&s) && S_ISREG(s.st_mode) && s.st_uid==0 && s.st_gid==0 &&
        (s.st_mode&07777)==0600 && s.st_nlink==1 && s.st_size>=0 && (uint64_t)s.st_size<=limit;
}
static int safe_dir(const char *path,int ram,int writable) {
    if(!path || path[0]!='/' || !path[1] || strlen(path)>4095) return -1;
    char copy[4096];strcpy(copy,path);
    int fd=open("/",O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    char *p=copy+1;
    while(fd>=0) {
        char *slash=strchr(p,'/');if(slash) *slash=0;
        if(!*p || !strcmp(p,".") || !strcmp(p,"..")) { close(fd);return -1; }
        int next=openat(fd,p,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
        close(fd);fd=next;if(!slash) break;p=slash+1;
    }
    struct stat s;struct statfs fs;struct statvfs v;
    if(fd<0) return -1;
    if(fstat(fd,&s) || s.st_uid || s.st_gid || (s.st_mode&07777)!=0700 ||
       fstatfs(fd,&fs) || (ram ? fs.f_type!=0x01021994 : fs.f_type!=0x01021994 && fs.f_type!=0xef53) ||
       fstatvfs(fd,&v) || (writable && (v.f_flag&ST_RDONLY))) { close(fd);return -1; }
    return fd;
}
static int read_blob(int dir,const char *name,size_t limit,struct blob *b) {
    int fd=openat(dir,name,O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC);
    if(fd<0) return errno==ENOENT ? 3 : 64;
    struct stat s,parent;struct statfs a,z;
    if(!regular(fd,limit) || fstat(fd,&s) || fstat(dir,&parent) || s.st_dev!=parent.st_dev ||
       fstatfs(fd,&a) || fstatfs(dir,&z) || a.f_type!=z.f_type) {
        close(fd);return 64;
    }
    b->n=(size_t)s.st_size;b->p=calloc(b->n+1,1);
    if(!b->p) { close(fd);return 74; }
    size_t n=0;
    while(n<b->n) {
        ssize_t got=read(fd,b->p+n,b->n-n);
        if(got<0 && errno==EINTR) continue;
        if(got<=0) { close(fd);discard(b);return 74; }n+=(size_t)got;
    }
    unsigned char extra;int ok=read(fd,&extra,1)==0;
    if(close(fd)) ok=0;
    if(!ok) { discard(b);return 74; }return 0;
}
static int write_blob(int dir,const char *name,const void *data,size_t size,const char *step) {
    int fd=openat(dir,name,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(fd<0) return 74;
    size_t n=0;int rc=74;
    while(n<size) {
        ssize_t got=write(fd,(const unsigned char *)data+n,size-n);
        if(got<0 && errno==EINTR) continue;
        if(got<=0) goto done;
        n+=(size_t)got;
    }
    if(!sync_step(fd,step)) rc=0;
done:
    if(close(fd)) rc=74;
    if(rc) unlinkat(dir,name,0); // Only a file created exclusively by this call.
    return rc;
}
static int head_text(char *out,size_t size,const struct head *h,const char *id) {
    return snprintf(out,size,"MUOS-SAVE-HEAD-1\nIDENTITY=%s\nCURRENT=%08u\nPREVIOUS=%08u\nNEXT=%08u\n",id,h->current,h->previous,h->next);
}
static int load_head(int dir,const char *id,struct head *h) {
    struct blob b={0};int rc=read_blob(dir,"HEAD",256,&b);if(rc) return rc;
    char parsed[65],canonical[256];int used=0;
    int fields=sscanf((char *)b.p,"MUOS-SAVE-HEAD-1\nIDENTITY=%64[0-9a-f]\nCURRENT=%8u\nPREVIOUS=%8u\nNEXT=%8u\n%n",
                      parsed,&h->current,&h->previous,&h->next,&used);
    int valid=fields==4 && used>0 && (size_t)used==b.n && !strcmp(parsed,id) &&
        h->next>=1 && h->next<=LIMIT_GENERATIONS+1 && h->current<h->next && h->previous<h->next &&
        (!h->previous || h->previous!=h->current) && (h->current || (!h->previous && h->next==1));
    if(valid) { head_text(canonical,sizeof(canonical),h,id);valid=!strcmp(canonical,(char *)b.p); }
    discard(&b);return valid ? 0 : 64;
}
static int publish_head(int dir,const char *id,const struct head *h) {
    char text[256];int n=head_text(text,sizeof(text),h,id);
    int rc=write_blob(dir,".head.new",text,(size_t)n,"head-file");if(rc) return rc;
    if(renameat(dir,".head.new",dir,"HEAD")) { unlinkat(dir,".head.new",0);return 74; }
    // After rename, failure means durability unknown. Do not roll back a visible HEAD.
    return sync_step(dir,"head-directory") ? 74 : 0;
}
static void generation(char name[32],unsigned n) { snprintf(name,32,"%08u.bundle",n); }
static int contents_valid(struct blob parts[3]) {
    unsigned char *p=parts[0].p;size_t n=parts[0].n;
    if(n<32 || memcmp(p,"PKST",4) || le32(p+4)!=1 || !le32(p+8) ||
       (uint64_t)le32(p+8)+32!=n || le32(p+12) || le32(p+20) ||
       (uint32_t)crc32(0,p+32,(uInt)(n-32))!=le32(p+16)) return 0;
    for(unsigned i=24;i<32;i++) if(p[i]) return 0;
    if(!parts[1].n || memchr(parts[1].p,0,parts[1].n) || !strstr((char *)parts[1].p,"[quicksave]\n")) return 0;
    return parts[2].n>=8 && !memcmp(parts[2].p,"\x89PNG\r\n\x1a\n",8);
}
static int bundle(int dir,unsigned seq,const char *id,struct blob *b,struct blob parts[3]) {
    char name[32];generation(name,seq);
    int rc=read_blob(dir,name,128+limits[0]+limits[1]+limits[2],b);if(rc) return rc;
    if(b->n<128 || memcmp(b->p,"MUOSSAV1",8) || le32(b->p+8)!=1 || memcmp(b->p+36,id,64)) return 64;
    for(unsigned i=100;i<128;i++) if(b->p[i]) return 64;
    size_t at=128;
    for(unsigned i=0;i<3;i++) {
        size_t size=le32(b->p+12+4*i);
        if(!size || size>limits[i] || size>b->n-at) return 64;
        if((uint32_t)crc32(0,b->p+at,(uInt)size)!=le32(b->p+24+4*i)) return 64;
        parts[i]=(struct blob){b->p+at,size};at+=size;
    }
    // Manifest must be NUL-terminated for semantic checks, not overlap the PNG.
    unsigned char *manifest=calloc(parts[1].n+1,1);if(!manifest) return 74;
    memcpy(manifest,parts[1].p,parts[1].n);struct blob check[3]={parts[0],{manifest,parts[1].n},parts[2]};
    int ok=at==b->n && contents_valid(check);free(manifest);return ok ? 0 : 64;
}
static int empty_dir(int fd) {
    int copy=openat(fd,".",O_RDONLY|O_DIRECTORY|O_CLOEXEC);if(copy<0) return 0;
    DIR *d=fdopendir(copy);if(!d) { close(copy);return 0; }
    int empty=1;struct dirent *e;
    while((e=readdir(d))) if(strcmp(e->d_name,".") && strcmp(e->d_name,"..")) empty=0;
    closedir(d);return empty;
}
static int fresh_store(int fd) {
    int copy=openat(fd,".",O_RDONLY|O_DIRECTORY|O_CLOEXEC);if(copy<0) return 0;
    DIR *d=fdopendir(copy);if(!d) { close(copy);return 0; }
    int fresh=1;struct dirent *e;
    while((e=readdir(d))) if(strcmp(e->d_name,".") && strcmp(e->d_name,"..") &&
        strcmp(e->d_name,".muos-saves-v1") && strcmp(e->d_name,".lock")) fresh=0;
    closedir(d);return fresh;
}
int main(int argc,char **argv) {
    umask(077);
    if(geteuid()!=0 || (argc!=4 && argc!=5)) return 64;
    const char *op=argv[1],*id=argv[3];
    int init=!strcmp(op,"init"),commit=!strcmp(op,"commit"),exporting=!strcmp(op,"export"),recover=!strcmp(op,"recover"),status=!strcmp(op,"status");
    if(!(init||commit||exporting||recover||status) || argc!=((commit||exporting) ? 5 : 4) || strlen(id)!=64 || strspn(id,"0123456789abcdef")!=64) return 64;
    int dir=safe_dir(argv[2],0,init||commit||recover);if(dir<0) return 64;
    struct blob marker={0},old={0},parts[3]={{0}},input[3]={{0}},packed={0};
    struct head h={0,0,1};int lock=-1,ram=-1,rc=64;
    if(read_blob(dir,".muos-saves-v1",64,&marker) || marker.n!=strlen(MARKER) || memcmp(marker.p,MARKER,marker.n)) goto done;
    lock=openat(dir,".lock",(init ? O_RDWR|O_CREAT : O_RDONLY)|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC,0600);
    if(lock<0 || !regular(lock,0)) goto done;
    if(flock(lock,LOCK_EX|LOCK_NB)) { rc=75;goto done; }
    rc=load_head(dir,id,&h);
    if(init && rc==3) {
        if(!fresh_store(dir)) { rc=64;goto done; }
        h=(struct head){0,0,1};rc=publish_head(dir,id,&h);goto report;
    }
    if(rc) goto done;
    if(init) {
        rc=h.current ? bundle(dir,h.current,id,&old,parts) : 0;goto report;
    }
    if(recover) {
        if(!h.previous) { rc=3;goto done; }
        rc=bundle(dir,h.previous,id,&old,parts);if(rc) goto done;
        h.current=h.previous;h.previous=0;rc=publish_head(dir,id,&h);goto report;
    }
    if(h.current) { rc=bundle(dir,h.current,id,&old,parts);if(rc) goto done; }
    if(status) { rc=0;goto report; }
    if(exporting && !h.current) { rc=3;goto done; }
    ram=safe_dir(argv[4],1,exporting);if(ram<0) { rc=64;goto done; }
    if(exporting) {
        if(!empty_dir(ram)) { rc=64;goto done; }
        unsigned created=0;
        for(;created<3;created++) { rc=write_blob(ram,names[created],parts[created].p,parts[created].n,"export-file");if(rc) break; }
        if(rc) { for(unsigned i=0;i<created;i++) unlinkat(ram,names[i],0);goto done; }
        rc=sync_step(ram,"export-directory") ? 74 : 0;goto report;
    }
    if(h.next>LIMIT_GENERATIONS) { rc=73;goto done; }
    for(unsigned i=0;i<3;i++) { rc=read_blob(ram,names[i],limits[i],&input[i]);if(rc) goto done; }
    if(!contents_valid(input)) { rc=64;goto done; }
    packed.n=128+input[0].n+input[1].n+input[2].n;packed.p=calloc(packed.n,1);if(!packed.p) { rc=74;goto done; }
    memcpy(packed.p,"MUOSSAV1",8);put32(packed.p+8,1);memcpy(packed.p+36,id,64);
    size_t at=128;
    for(unsigned i=0;i<3;i++) { put32(packed.p+12+4*i,(uint32_t)input[i].n);put32(packed.p+24+4*i,(uint32_t)crc32(0,input[i].p,(uInt)input[i].n));memcpy(packed.p+at,input[i].p,input[i].n);at+=input[i].n; }
    char name[32];generation(name,h.next);
    rc=write_blob(dir,name,packed.p,packed.n,"bundle-file");if(rc) goto done;
    // A failure after this point leaves an orphan for inspection; never adopt it.
    if(sync_step(dir,"bundle-directory")) { rc=74;goto done; }
    h.previous=h.current;h.current=h.next++;rc=publish_head(dir,id,&h);
report:
    if(!rc) printf("MUOS_SAVE_STORE_OK current=%08u previous=%08u next=%08u\n",h.current,h.previous,h.next);
done:
    if(ram>=0) close(ram);
    if(lock>=0) close(lock);
    close(dir);discard(&marker);discard(&old);discard(&packed);
    for(unsigned i=0;i<3;i++) discard(&input[i]);
    if(rc) fputs("MUOS_SAVE_STORE_REFUSED\n",stderr);
    return rc;
}
