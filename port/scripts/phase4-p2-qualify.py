#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Deck qualification: protect test128 RO; exercise writer ONLY on owned loop.

No physical-card write operation or arbitrary device argument is exposed.
"""
from pathlib import Path
import ctypes,fcntl,hashlib,importlib.util,json,os,platform,pwd,re,shutil,signal,stat,struct,subprocess,sys,tempfile,time,traceback

SOURCES={'phase4-p2-qualify.py','phase4_p2_controller.py','phase4_p2_write_core.py',
    'phase4_backup_core.py','phase4_root_migration.py','phase4_root_recovery.py',
    'phase4-offline-backup.py','phase4-physical-capture.py','context.json',
    'phase4-p2-inspect-failure.py','previous-failure.json'}
ROOT=None;STAGE=None

def need(ok,message):
    if not ok:raise ValueError(message)

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def run(args,timeout=180):
    r=subprocess.run(args,capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=timeout,
        env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C'})
    need(r.returncode==0,'Fixed host tool failed: '+Path(args[0]).name);return r

def bootstrap():
    need(os.geteuid()==0 and platform.machine()=='x86_64','Local Deck sudo required')
    need(Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),'Deck required')
    source=Path(__file__).resolve().parent;manifest=json.loads((source/'package.json').read_text())
    need(manifest['operation']=='qualify-loop-only' and set(manifest['files'])==SOURCES,'Qualification package schema')
    root=Path(tempfile.mkdtemp(prefix='muos-r35s-c87.',dir='/run'));root.chmod(0o700)
    for name,h in manifest['files'].items():
        fd=os.open(source/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            s=os.fstat(fd)
            need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and 0<s.st_size<=1024*1024 and not s.st_mode&0o022,'Unsafe package leaf')
            data=os.read(fd,s.st_size+1);a=os.fstat(fd)
            need((s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns),'Package changed')
            need(len(data)==s.st_size and hashlib.sha256(data).hexdigest()==h,'Package hash')
            with (root/name).open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
            (root/name).chmod(0o400)
        finally:os.close(fd)
    os.execve('/usr/bin/python3',['/usr/bin/python3',str(root/'phase4-p2-qualify.py'),'_qualify'],
        {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})

def fixture_mbr(capacity):
    need(capacity==656*1024*1024,'Fixed loop fixture dimensions')
    out=bytearray(512);out[510:512]=b'\x55\xaa'
    for n,(start,size,kind) in enumerate([(32768,204800,0x0c),(262144,1048576,0x83),(1310720,32768,0x83)]):
        offset=446+16*n;out[offset+4]=kind;struct.pack_into('<II',out,offset+8,start,size)
    return bytes(out)

def loop_fixture(stage,controller,core):
    """Real kernel/block/fsync tests, but no real card aliases in the adapter."""
    capacity=656*1024*1024;backing=stage/'loop.raw';source=stage/'source.ext4';loop=None;result=[]
    with backing.open('xb') as out:
        out.truncate(capacity);out.seek(0);out.write(fixture_mbr(capacity))
        out.seek(640*1024*1024);out.write(b'C87 protected p3 sentinel\n');out.flush();os.fsync(out.fileno())
    backing.chmod(0o600);backstat=backing.stat()
    with source.open('xb') as out:out.truncate(core.ROOT_BYTES);out.flush();os.fsync(out.fileno())
    source.chmod(0o600)
    run(['mke2fs','-q','-t','ext4','-F','-m','0',str(source)])
    run(['e2fsck','-fn',str(source)])
    original_fd=os.open(backing,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        old=core.region_hash(original_fd,core.ROOT_OFFSET,core.ROOT_BYTES,os.pread)
        protected=[core.region_hash(original_fd,0,core.ROOT_OFFSET,os.pread),
            core.region_hash(original_fd,640*1024*1024,16*1024*1024,os.pread)]
    finally:os.close(original_fd)
    try:
        loop=run(['losetup','--find','--show','--partscan','--nooverlap',str(backing)]).stdout.strip()
        need(re.fullmatch(r'/dev/loop[0-9]+',loop),'Only allocated loop device')
        run(['udevadm','settle','--timeout=10'],timeout=15)
        name=Path(loop).name;sysroot=Path('/sys/class/block')
        for _ in range(50):
            if all((sysroot/(name+'p'+str(n))/'dev').exists() for n in (1,2,3)):break
            time.sleep(.1)
        aliases=[]
        for suffix,size in [('',capacity),('p1',100*1024*1024),('p2',core.ROOT_BYTES),('p3',16*1024*1024)]:
            path=Path(loop+suffix);p=sysroot/(name+suffix)
            major,minor=map(int,(p/'dev').read_text().strip().split(':'))
            need((major==7 if not suffix else p.resolve().parent==(sysroot/name).resolve())
                and int((p/'size').read_text())*512==size,'Loop alias geometry')
            aliases.append((path,os.makedev(major,minor),size))
        def identity():
            current=backing.lstat()
            need(stat.S_ISREG(current.st_mode) and current.st_uid==0 and current.st_nlink==1
                and (current.st_dev,current.st_ino,current.st_size)==(backstat.st_dev,backstat.st_ino,capacity),'Loop backing changed')
            # LOOP_GET_STATUS64 pins inode/device as well as the path shown by
            # sysfs; another loop or card can never satisfy this adapter.
            fd=controller.block_open(aliases[0][0],aliases[0][1],capacity,os.O_RDONLY)
            try:
                status=fcntl.ioctl(fd,0x4c05,bytes(232))
                dev,ino,rdev,offset,limit=struct.unpack_from('QQQQQ',status)
                need(dev==backstat.st_dev and ino==backstat.st_ino and offset==limit==0,'Loop backing identity ioctl')
            finally:os.close(fd)
            nums={f'{os.major(d)}:{os.minor(d)}' for p,d,n in aliases}
            for proc in Path('/proc').glob('[0-9]*/mountinfo'):
                try:lines=proc.read_text().splitlines()
                except OSError as e:
                    if e.errno in (2,3,22):continue
                    raise
                need(not any(line.split()[2] in nums for line in lines),'Loop unexpectedly mounted')
            observed=[]
            for p,d,n in aliases:
                node=sysroot/p.name
                actual_bytes=int((node/'size').read_text())*512;actual_dev=(node/'dev').read_text().strip()
                observed.append({'name':p.name,'bytes':actual_bytes,'expected_bytes':n,'dev':actual_dev,
                    'expected_dev':f'{os.major(d)}:{os.minor(d)}'})
                if actual_bytes!=n or actual_dev!=f'{os.major(d)}:{os.minor(d)}':
                    raise ValueError('Loop aliases changed: '+json.dumps(observed,sort_keys=True))
                need(not any((node/'holders').iterdir()),'Loop holder')
            for line in Path('/proc/swaps').read_text().splitlines()[1:]:
                s=Path(line.split()[0]).stat();d=s.st_rdev if stat.S_ISBLK(s.st_mode) else s.st_dev
                need(f'{os.major(d)}:{os.minor(d)}' not in nums,'Loop swap')
        def fsck(fd):
            r=subprocess.run(['e2fsck','-fn','/proc/self/fd/'+str(fd)],pass_fds=(fd,),capture_output=True,timeout=180)
            need(r.returncode==0,'Fixture source fsck')
        sourcefd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            sha=core.region_hash(sourcefd,0,core.ROOT_BYTES,os.pread)
            journal=stage/'success';journal.mkdir(mode=0o700)
            c=controller.Controller(aliases,identity,capacity,controller.Journal(journal))
            r=c.apply(sourcefd,sha,old,protected,fsck)
            need(r['passed'] is True and r['boot_handoff_authorized'] is False,'Loop result')
            run(['e2fsck','-fn',loop+'p2']);result.append('real-loop-full512MiB-p2-write-cold-readback-fsck-protected-complement')
            need({p.name for p in journal.iterdir()}=={'unlock-intent.json','write-intent.json','complete.json'},'Journal sequence')
            result.append('durable-unlock-and-write-intents-before-payload-completion-after-RO')
            for path,dev,size in aliases:
                fd=controller.block_open(path,dev,size,os.O_RDONLY)
                try:need(struct.unpack('i',fcntl.ioctl(fd,controller.GETRO,bytes(4)))[0]==1,'Loop final RO')
                finally:os.close(fd)
            result.append('Valve-kernel-whole-and-p2-unlock-with-p1-p3-RO-then-all-four-RO')
            # A real short write, exactly once, on the owned disposable loop.
            journal=stage/'short-write';journal.mkdir(mode=0o700);writes=[];actual_pwrite=core.os.pwrite
            def short(fd,data,offset):
                writes.append(offset);need(len(writes)==1,'Never retry short write')
                return actual_pwrite(fd,data[:512],offset)
            # The primitive's default parameter captured os.pwrite at import.
            # Wrap its call explicitly; keep all other real controller IO.
            actual_write=core.write_p2
            def short_core(*args,**kwargs):return actual_write(*args,**kwargs,pwrite=short)
            core.write_p2=short_core
            try:
                c=controller.Controller(aliases,identity,capacity,controller.Journal(journal))
                try:c.apply(sourcefd,sha,sha,protected,fsck)
                except ValueError as error:need('Short p2 write' in str(error),'Expected short-write failure')
                else:raise ValueError('Short write falsely completed')
            finally:core.write_p2=actual_write
            need(writes==[core.ROOT_OFFSET] and not (journal/'complete.json').exists(),'Failed transaction completed/retried')
            for path,dev,size in aliases:
                fd=controller.block_open(path,dev,size,os.O_RDONLY)
                try:need(struct.unpack('i',fcntl.ioctl(fd,controller.GETRO,bytes(4)))[0]==1,'Failed loop protection')
                finally:os.close(fd)
            result.append('real-short-pwrite-once-no-completion-no-rollback-and-all-four-RO')
        finally:os.close(sourcefd)
    finally:
        if loop is not None:
            run(['losetup','--detach',loop])
            # --detach may defer destruction; wait briefly before removing the
            # backing file, never unbind someone else's existing loop.
            for _ in range(50):
                if not (Path('/sys/class/block')/Path(loop).name/'loop/backing_file').exists():break
                time.sleep(.1)
            need(not (Path('/sys/class/block')/Path(loop).name/'loop/backing_file').exists(),'Owned loop still attached; retain fixture')
    backing.unlink();source.unlink()
    return result

def operation():
    global ROOT,STAGE
    ROOT=Path(__file__).resolve().parent
    need(os.geteuid()==0 and re.fullmatch(r'/run/muos-r35s-c87\.[a-z0-9_]{8}',str(ROOT)),'Root snapshot only')
    s=ROOT.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'Root snapshot identity')
    import phase4_backup_core as backup,phase4_root_migration as policy,phase4_root_recovery as recovery
    import phase4_p2_controller as controller,phase4_p2_write_core as core
    capture=module('ro_capture',ROOT/'phase4-physical-capture.py')
    guard=module('card_guard',ROOT/'phase4-offline-backup.py');ctx=json.loads((ROOT/'context.json').read_text())
    capture.validate_context(ctx,'reference',policy,recovery)
    guard.core=backup;guard.policy=policy;guard.ROOT=ROOT;guard.plan=ctx
    previous=json.loads((ROOT/'previous-failure.json').read_text())
    if previous is not None:
        module('previous_audit',ROOT/'phase4-p2-inspect-failure.py').inspect(ROOT/'previous-failure.json')
    libc=ctypes.CDLL(None,use_errno=True)
    need(libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0,'Private mount namespace required')
    for tool in ['losetup','mke2fs','e2fsck','findmnt','udevadm']:need(shutil.which(tool),'Missing fixed host tool')
    parent=Path('/var/tmp');s=parent.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and bool(s.st_mode&stat.S_ISVTX),'Persistent parent')
    row=run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN']).stdout.split()
    need(len(row)==2 and row[0] in ('ext4','btrfs') and row[1] not in guard.numbers(),'Off-card stage')
    need(shutil.disk_usage(parent).free>=3*1024**3,'Need 3GiB off-card space')
    STAGE=Path(tempfile.mkdtemp(prefix='muos-r35s-c87-qualify.',dir=parent));STAGE.chmod(0o700)
    # Card operations are exclusively C86 SETRO1 / RDONLY. In particular the
    # transition controller receives ONLY paths allocated by loop_fixture().
    def card_check():
        capture.protect_aliases(guard,policy,ctx);fd=guard.open_card()
        try:
            capture.verify_ro(guard,fd)
            need(backup.region_sha(fd,policy.ROOT_OFFSET,policy.ROOT_BYTES)==ctx['reference_root_sha256'],'Card root changed since C86')
            capture.read_protection(guard,ctx)
        finally:os.close(fd)
    try:
        card_check();cases=loop_fixture(STAGE,controller,core);card_check()
        report={'passed':True,'schema':87,'operation':'qualify-loop-only','kernel':platform.release(),
            'cases':cases,'loop_case_count':len(cases),'physical_card_payload_written':False,
            'physical_card_SETRO0':False,'physical_card_all_four_aliases_readonly':True,
            'physical_card_p2_unchanged_since_C86':True,'physical_card_automount_guard_unchanged':True,
            'loop_detached_and_large_fixture_files_removed':True,'physical_card_writer_entrypoint_available':False,
            'candidate_provisioned':False,'boot_handoff_authorized':False,'seed_generated_or_loaded':False,
            'source_sha256':{n:backup.sha(ROOT/n) for n in sorted(SOURCES)}}
        backup.write_new(STAGE/'analysis.json',(json.dumps(report,indent=2)+'\n').encode())
        account=pwd.getpwnam('deck')
        for p in STAGE.rglob('*'):
            p.chmod(0o700 if p.is_dir() else 0o400);os.chown(p,account.pw_uid,account.pw_gid)
        os.chown(STAGE,account.pw_uid,account.pw_gid);backup.sync_dir(STAGE);backup.sync_dir(parent)
        shutil.rmtree(ROOT)
        print('C87 QUALIFY COMPLETE '+str(STAGE),flush=True)
    except BaseException as error:
        # Keep the root snapshot and partial journal on failure for inspection.
        # Best effort SETRO1 only; this helper never clears card protection.
        details={'passed':False,'error_type':type(error).__name__,'reason':str(error),
            'traceback':traceback.format_exc(),'partial':str(STAGE),'snapshot':str(ROOT),
            'physical_card_payload_written':False,'physical_card_SETRO0':False}
        try:capture.protect_aliases(guard,policy,ctx);details['card_RO_reinforced']=True
        except BaseException as protection_error:
            details['card_RO_reinforced']=False;details['protection_error_type']=type(protection_error).__name__
        out=Path(tempfile.mkdtemp(prefix='muos-r35s-c87-failure.',dir=parent));out.chmod(0o700)
        backup.write_new(out/'failure.json',(json.dumps(details,indent=2)+'\n').encode())
        account=pwd.getpwnam('deck');leaf=out/'failure.json';leaf.chmod(0o400)
        os.chown(leaf,account.pw_uid,account.pw_gid);os.chown(out,account.pw_uid,account.pw_gid)
        backup.sync_dir(out);backup.sync_dir(parent)
        print('C87 private failure report '+str(out),file=sys.stderr,flush=True)
        raise

if __name__=='__main__':
    os.umask(0o077)
    def interrupted(signum,frame):raise SystemExit(128+signum)
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    try:
        need(len(sys.argv)==2 and sys.argv[1] in ('qualify','_qualify'),'Only loop qualification')
        if sys.argv[1]=='qualify':bootstrap()
        else:operation()
    except BaseException as error:
        print('C87 FAILED ('+type(error).__name__+'); keep card and private partial stage; no automatic retry.',file=sys.stderr)
        sys.exit(1)
