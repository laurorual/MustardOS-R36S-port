# SPDX-License-Identifier: MIT
"""Bounded p2 transaction controller; no CLI or arbitrary device discovery.

A target adapter must derive its four aliases from guarded hardware identity.
The physical-card deployment still requires a validated candidate/recovery
composer and independent backups. The qualification adapter is loop-only.
"""
from pathlib import Path
import errno,fcntl,json,os,stat,struct,subprocess
import phase4_p2_write_core as core
from phase4_backup_core import sync_dir
from phase4_root_migration import require,ROOT_OFFSET,ROOT_BYTES,digest
from phase4_root_recovery import encoded

SETRO=0x125d;GETRO=0x125e;GETSIZE=0x80081272;FLUSH=0x1261

def block_open(path,device,size,flags):
    fd=os.open(path,flags|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        s=os.fstat(fd)
        require(stat.S_ISBLK(s.st_mode) and s.st_rdev==device,'Opened block identity')
        require(struct.unpack('Q',fcntl.ioctl(fd,GETSIZE,bytes(8)))[0]==size,'Opened block size')
        return fd
    except BaseException:os.close(fd);raise

def process_credentials(process):
    text=(process/'status').read_text()
    rows={line.split(':',1)[0]:line.split(':',1)[1].split() for line in text.splitlines() if line.startswith(('Uid:','Gid:'))}
    uid=list(map(int,rows['Uid']));gid=list(map(int,rows['Gid']))
    require(len(uid)==len(gid)==4 and len(set(uid))==len(set(gid))==1 and uid[0]>0,'Unqualified fd owner credentials')
    # Include starttime: do not reuse another process's credentials after PID
    # recycling. Linux stat comm may contain spaces and closing parentheses.
    start=(process/'stat').read_text().rsplit(')',1)[1].split()[19]
    return uid[0],gid[0],start

def owner_fd_stat(leaf):
    """FUSE can deny root getattr while allowing the owning process UID.

    Do not skip an unreadable fd or guess its type from its symlink/path/fs.
    A short-lived child drops all supplementary groups and UID/GID to the
    stable non-root process owner, then performs stat only. Unknowns fail.
    """
    require(os.geteuid()==0 and re_proc_fd(leaf),'Qualified proc fd fallback only')
    process=leaf.parent.parent;uid,gid,start=process_credentials(process)
    code="""import json,os,sys
try:
 s=os.stat(sys.argv[1]);print(json.dumps({'mode':s.st_mode,'rdev':s.st_rdev}))
except OSError as e:
 print(json.dumps({'errno':e.errno}));sys.exit(1)
"""
    p=subprocess.run(['/usr/bin/python3','-c',code,str(leaf)],user=uid,group=gid,extra_groups=[],
        stdin=subprocess.DEVNULL,capture_output=True,timeout=5,
        env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})
    require(len(p.stdout)<=256,'Fd metadata worker output bound')
    result=json.loads(p.stdout)
    require(process_credentials(process)==(uid,gid,start),'Fd owner/PID changed')
    if p.returncode!=0:
        error=result.get('errno');require(type(error) is int,'Fd worker failed')
        raise OSError(error,'Fd metadata remains unreadable')
    require(set(result)=={'mode','rdev'} and all(type(v) is int for v in result.values()),'Fd metadata schema')
    return result['mode'],result['rdev']

def re_proc_fd(leaf):
    return (leaf.is_absolute() and len(leaf.parts)==5 and leaf.parts[:2]==('/','proc')
        and leaf.parts[2].isdigit() and leaf.parts[3]=='fd' and leaf.parts[4].isdigit())

def no_foreign_fds(devices,owned,proc=Path('/proc')):
    """Exclusive block claims do not exclude other raw opens. Refuse them too."""
    fallbacks=0
    for process in proc.glob('[0-9]*'):
        try:
            for leaf in (process/'fd').iterdir():
                if process.name==str(os.getpid()) and int(leaf.name) in owned:continue
                try:s=leaf.stat();mode,device=s.st_mode,s.st_rdev
                except OSError as e:
                    if e.errno in (errno.ENOENT,errno.ESRCH):continue
                    if e.errno!=errno.EACCES:raise
                    fallbacks+=1;require(fallbacks<=32,'Fd metadata fallback bound')
                    try:mode,device=owner_fd_stat(leaf)
                    except OSError as fallback_error:
                        if fallback_error.errno in (errno.ENOENT,errno.ESRCH):continue
                        raise
                require(not stat.S_ISBLK(mode) or device not in devices,'Foreign raw block descriptor')
        except OSError as e:
            if e.errno in (errno.ENOENT,errno.ESRCH):continue
            raise # permission/namespace uncertainty is not absence of consumers.

class Journal:
    def __init__(self,parent):
        self.parent=Path(parent)
        s=self.parent.lstat()
        require(stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700,'Private persistent journal')
        require(not any(self.parent.iterdir()),'Journal already used; inspect, never retry')

    def record(self,name,value):
        require(name in ('unlock-intent','write-intent','complete'),'Finite journal event')
        fd=os.open(self.parent/(name+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
        with os.fdopen(fd,'wb') as out:
            data=encoded(value)
            require(out.write(data)==len(data),'Short journal write')
            out.flush();os.fsync(out.fileno())
        sync_dir(self.parent)

class Controller:
    """Fixed whole-device fd, fixed p2 extent, protected complement fully hashed.

    aliases are ordered whole,p1,p2,p3; each tuple is (path,rdev,bytes).
    identity() must check hardware, namespace/mount/swap/holders and guard rule.
    control fds are retained, so finally never opens an unverified replacement.
    A durable unlock intent precedes SETRO0; no resume/rollback is provided.
    """
    def __init__(self,aliases,identity,capacity,journal):
        require(len(aliases)==4 and type(capacity) is int and capacity>ROOT_OFFSET+ROOT_BYTES,'Four aliases and protected p3 required')
        require(aliases[0][2]==capacity and aliases[2][2]==ROOT_BYTES,'Fixed p2 dimensions')
        require(len({d for p,d,n in aliases})==4,'Distinct aliases')
        self.aliases=aliases;self.identity=identity;self.capacity=capacity;self.journal=journal
        self.controls=[];self.claim=None

    def idle(self):
        self.identity()
        no_foreign_fds({d for p,d,n in self.aliases},set(self.controls)|({self.claim} if self.claim is not None else set()))

    def open_controls(self):
        self.identity()
        for path,device,size in self.aliases:
            self.identity()
            self.controls.append(block_open(path,device,size,os.O_RDONLY))
        self.idle()

    def state(self,expected):
        self.idle()
        actual=[struct.unpack('i',fcntl.ioctl(fd,GETRO,bytes(4)))[0] for fd in self.controls]
        require(len(actual)==4 and actual==expected,'Alias readonly transition differs')

    def readonly(self):
        # Best effort on every *owned verified fd*, including when removal or
        # another protection fails. Never rediscover aliases during cleanup.
        errors=[]
        for i in [1,2,3,0]:
            if i>=len(self.controls):continue
            try:fcntl.ioctl(self.controls[i],SETRO,struct.pack('i',1))
            except BaseException as e:errors.append(e)
        if errors:raise errors[0]
        if len(self.controls)==4:self.state([1,1,1,1])

    def close_claim(self):
        if self.claim is not None:
            fd=self.claim;self.claim=None;os.close(fd)

    def flush(self):
        self.idle()
        for i in [1,2,3,0]:
            os.fsync(self.controls[i]);fcntl.ioctl(self.controls[i],FLUSH,0)
        self.idle()

    def acquire(self,writable=False):
        require(self.claim is None,'Claim already held');self.idle()
        path,device,size=self.aliases[0]
        self.claim=block_open(path,device,size,(os.O_RDWR if writable else os.O_RDONLY)|os.O_EXCL)
        fcntl.flock(self.claim,fcntl.LOCK_EX|fcntl.LOCK_NB);self.idle()
        return self.claim

    def protected(self,fd):
        return [core.region_hash(fd,0,ROOT_OFFSET,os.pread),
            core.region_hash(fd,ROOT_OFFSET+ROOT_BYTES,self.capacity-ROOT_OFFSET-ROOT_BYTES,os.pread)]

    def apply(self,source,source_sha256,current_sha256,protected_sha256,validate_source):
        """validate_source must derive image eligibility from the guarded fd.

        It executes before unlock, not from a caller's boolean receipt. The
        deployed qualification CLI supplies ext4/fsck checks for synthetic
        images only. No card candidate is accepted by that entrypoint.
        """
        digest(source_sha256);digest(current_sha256)
        require(type(protected_sha256) is list and len(protected_sha256)==2,'Protected complement hashes')
        for h in protected_sha256:digest(h)
        before=os.fstat(source)
        require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
            and stat.S_IMODE(before.st_mode) in (0o400,0o600) and before.st_size==ROOT_BYTES,'Guarded private regular source')
        signature=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink)
        fcntl.flock(source,fcntl.LOCK_EX|fcntl.LOCK_NB)
        def source_check():
            require(signature(os.fstat(source))==signature(before),'Source metadata changed')
            require(core.region_hash(source,0,ROOT_BYTES,os.pread)==source_sha256,'Source hash changed')
        try:
            self.open_controls();self.readonly();self.flush();fd=self.acquire()
            source_check();validate_source(source);source_check()
            require(core.region_hash(fd,ROOT_OFFSET,ROOT_BYTES,os.pread)==current_sha256,'Current p2 changed')
            require(self.protected(fd)==protected_sha256,'Protected complement changed')
            self.state([1,1,1,1])
            self.journal.record('unlock-intent',{'kind':'P2_UNLOCK_MAY_HAVE_STARTED','source_sha256':source_sha256,
                'previous_sha256':current_sha256,'protected_sha256':protected_sha256,'offset':ROOT_OFFSET,'bytes':ROOT_BYTES})
            # Closing/reopening is deliberate: Linux cannot upgrade an RDONLY
            # file description. Guard+idle checks cover the gap; EXCL fails if
            # a conflicting claim appears. Any error restores owned aliases.
            self.close_claim();self.idle()
            fcntl.ioctl(self.controls[0],SETRO,struct.pack('i',0))
            fcntl.ioctl(self.controls[2],SETRO,struct.pack('i',0))
            self.state([0,1,0,1]);fd=self.acquire(True)
            def preflight():self.state([0,1,0,1]);source_check()
            def protected():
                self.flush();require(self.protected(fd)==protected_sha256,'Protected complement changed during write')
            def restore():
                try:self.readonly()
                finally:self.close_claim()
            def complete(value):
                self.state([1,1,1,1]);self.flush();readback=self.acquire()
                try:
                    require(core.region_hash(readback,ROOT_OFFSET,ROOT_BYTES,os.pread)==source_sha256,'Cold alias readback differs')
                    require(self.protected(readback)==protected_sha256,'Final protected complement differs')
                    source_check();self.state([1,1,1,1])
                    self.journal.record('complete',{**value,'all_four_aliases_kernel_readonly':True,
                        'alias_cache_synchronized':True,'protected_complement_verified':True,'boot_handoff_authorized':False})
                finally:self.close_claim()
            return core.write_p2(source,fd,source_sha256,current_sha256,preflight=preflight,
                record_intent=lambda v:self.journal.record('write-intent',v),record_complete=complete,
                restore_readonly=restore,verify_protected=protected)
        finally:
            try:
                try:self.readonly()
                finally:self.close_claim()
            finally:
                for fd in self.controls:os.close(fd)
                self.controls=[]
