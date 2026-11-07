#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C90 exact test128 descriptor/RO transition. NO payload writer is called."""
from pathlib import Path
import ctypes,fcntl,hashlib,importlib.util,json,os,platform,pwd,re,shutil,signal,stat,struct,sys,tempfile,traceback

SOURCES={'phase4-p2-card-readiness.py','phase4_p2_recovery.py','phase4_p2_controller.py','phase4_p2_write_core.py',
    'phase4_recovery_image.py','phase4_root_recovery.py','phase4_backup_core.py','phase4_root_migration.py',
    'phase4-offline-backup.py','phase4-physical-capture.py','context.json'}

def need(ok,message):
    if not ok:raise ValueError(message)

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def bootstrap():
    need(os.geteuid()==0 and platform.machine()=='x86_64','Local Deck sudo required')
    need(Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),'Deck required')
    source=Path(__file__).resolve().parent;manifest=json.loads((source/'package.json').read_text())
    need(manifest['operation']=='card-readiness-no-payload' and set(manifest['files'])==SOURCES,'Finite readiness package')
    root=Path(tempfile.mkdtemp(prefix='muos-r35s-c90.',dir='/run'));root.chmod(0o700)
    for name,wanted in manifest['files'].items():
        fd=os.open(source/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and 0<s.st_size<=1024*1024 and not s.st_mode&0o022,'Unsafe readiness leaf')
            data=os.read(fd,s.st_size+1);a=os.fstat(fd)
            need((s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns),'Readiness source changed')
            need(len(data)==s.st_size and hashlib.sha256(data).hexdigest()==wanted,'Readiness source hash')
            with (root/name).open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
            (root/name).chmod(0o400)
        finally:os.close(fd)
    os.execve('/usr/bin/python3',['/usr/bin/python3',str(root/'phase4-p2-card-readiness.py'),'_check'],
        {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})

def transition(controller,verify_bytes,ioctl=fcntl.ioctl):
    """No .apply, write_p2, write/pwrite/writev, image clone, mount or seed IO."""
    try:
        controller.open_controls();controller.readonly();controller.flush()
        fd=controller.acquire();controller.state([1,1,1,1]);verify_bytes(fd)
        controller.journal.record('unlock-intent',{'kind':'CARD_READINESS_UNLOCK_MAY_HAVE_STARTED',
            'device_payload_write_allowed':False,'p1_p3_must_remain_readonly':True})
        controller.close_claim();controller.idle()
        ioctl(controller.controls[0],0x125d,struct.pack('i',0))
        ioctl(controller.controls[2],0x125d,struct.pack('i',0))
        controller.state([0,1,0,1]);fd=controller.acquire(True)
        need(fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_ACCMODE==os.O_RDWR,'Exclusive whole read/write descriptor not acquired')
        controller.state([0,1,0,1]);verify_bytes(fd)
    finally:
        try:controller.readonly()
        finally:controller.close_claim()
    controller.flush();fd=controller.acquire()
    try:
        verify_bytes(fd);controller.state([1,1,1,1])
        controller.journal.record('complete',{'kind':'CARD_READINESS_VERIFIED','exclusive_RDWR_opened_without_payload_write':True,
            'all_four_aliases_kernel_readonly':True,'p1_p3_readonly_during_transition':True,
            'p2_and_MBR_and_boot_prefix_unchanged':True,'physical_device_payload_written':False,'boot_handoff_authorized':False})
    finally:controller.close_claim()

def operation():
    root=Path(__file__).resolve().parent
    need(os.geteuid()==0 and re.fullmatch(r'/run/muos-r35s-c90\.[a-z0-9_]{8}',str(root)),'Protected root snapshot required')
    s=root.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'Root snapshot identity')
    need({p for p in Path('/run').glob('muos-r35s-c*')}=={root},'Prior task snapshot requires inspection')
    import phase4_backup_core as core,phase4_root_migration as policy,phase4_root_recovery as recovery
    import phase4_p2_recovery as adapter
    capture=module('capture_readiness',root/'phase4-physical-capture.py');guard=module('guard_readiness',root/'phase4-offline-backup.py')
    ctx=json.loads((root/'context.json').read_text());capture.validate_context(ctx,'reference',policy,recovery)
    guard.core=core;guard.policy=policy;guard.ROOT=root;guard.plan=ctx
    libc=ctypes.CDLL(None,use_errno=True)
    need(libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0,'Private namespace required')
    need(os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'),'Namespace not isolated')
    capture.protect_aliases(guard,policy,ctx)
    parent=Path('/var/tmp');s=parent.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and bool(s.st_mode&stat.S_ISVTX),'Persistent parent')
    row=guard.run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN']).stdout.split()
    need(len(row)==2 and row[0] in ('ext4','btrfs') and row[1] not in guard.numbers(),'Off-card persistent stage')
    stage=Path(tempfile.mkdtemp(prefix='muos-r35s-c90-readiness.',dir=parent));stage.chmod(0o700)
    journal=stage/'journal';journal.mkdir(mode=0o700);controller=adapter.card_target(guard,capture,ctx,journal);verified=[]
    def verify(fd):
        capture.read_protection(guard,ctx)
        mbr=core.read_exact(fd,512,0);policy.geometry(mbr)
        need(hashlib.sha256(mbr).hexdigest()==ctx['mbr_sha256']
            and core.region_sha(fd,0,16*1024*1024)==ctx['boot_prefix_16MiB_sha256'],'MBR/boot prefix changed')
        need(core.region_sha(fd,policy.ROOT_OFFSET,policy.ROOT_BYTES)==ctx['reference_root_sha256'],'P2 changed since C86')
        verified.append(True)
    try:
        print('C90_STEP=three-p2-readbacks-and-transient-kernel-RO-transition-no-payload-write',flush=True)
        transition(controller,verify)
        need(len(verified)==3,'Readiness triple readback incomplete')
        for fd in controller.controls:os.close(fd)
        controller.controls=[]
        report={'passed':True,'schema':90,'operation':'card-readiness-no-payload','kernel':platform.release(),
            'exclusive_RDWR_opened_without_payload_write':True,'whole_and_p2_transient_kernel_SETRO0':True,
            'all_four_aliases_kernel_readonly':True,'p1_p3_readonly_during_transition':True,
            'p2_512MiB_triple_hash_matches_C86':True,'MBR_and_16MiB_boot_prefix_triple_verified':True,
            'p3_full_content_hashed':False,'physical_device_payload_written':False,'candidate_provisioned_to_media':False,
            'boot_handoff_authorized':False,'seed_generated_or_loaded':False,'handoff_fence_created':False,
            'source_sha256':{n:core.sha(root/n) for n in sorted(SOURCES)}}
        core.write_new(stage/'analysis.json',recovery.encoded(report));account=pwd.getpwnam('deck')
        for p in stage.rglob('*'):
            p.chmod(0o700 if p.is_dir() else 0o400);os.chown(p,account.pw_uid,account.pw_gid)
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|(os.O_DIRECTORY if p.is_dir() else 0))
            try:os.fsync(fd)
            finally:os.close(fd)
        os.chown(stage,account.pw_uid,account.pw_gid);core.sync_dir(stage);core.sync_dir(parent)
        shutil.rmtree(root);print('C90 READINESS COMPLETE '+str(stage),flush=True)
    except BaseException as error:
        info={'passed':False,'error_type':type(error).__name__,'reason':str(error),'traceback':traceback.format_exc(),
            'partial':str(stage),'snapshot':str(root),'physical_device_payload_written':False,'automatic_retry_or_rollback':False}
        try:controller.readonly();info['RO_reinforced']=True
        except BaseException:info['RO_reinforced']=False
        out=Path(tempfile.mkdtemp(prefix='muos-r35s-c90-failure.',dir=parent));out.chmod(0o700)
        core.write_new(out/'failure.json',recovery.encoded(info));account=pwd.getpwnam('deck')
        leaf=out/'failure.json';leaf.chmod(0o400);os.chown(leaf,account.pw_uid,account.pw_gid);os.chown(out,account.pw_uid,account.pw_gid)
        core.sync_dir(out);core.sync_dir(parent);print('C90 private failure report '+str(out),file=sys.stderr,flush=True);raise
    finally:
        try:
            if controller.controls:controller.readonly()
        finally:
            controller.close_claim()
            for fd in controller.controls:os.close(fd)
            controller.controls=[]

if __name__=='__main__':
    os.umask(0o077)
    def interrupted(signum,frame):raise SystemExit(128+signum)
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    try:
        need(len(sys.argv)==2 and sys.argv[1] in ('check','_check'),'Only no-payload card readiness')
        if sys.argv[1]=='check':bootstrap()
        else:operation()
    except BaseException as error:
        print('C90 FAILED ('+type(error).__name__+'); keep card offline/RO and partial journal. No payload writer was called.',file=sys.stderr);sys.exit(1)
