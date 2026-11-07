#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C89 finite post-intent recovery writer. No factory/initial migration mode.

An actual guarded post-handoff capture, composed no-credit recovery image,
independent backup and sealed prior intent must be supplied by the preparer.
This helper never boots, rolls back automatically, or writes p1/p3.
"""
from pathlib import Path
import ctypes,fcntl,hashlib,importlib.util,json,os,platform,pwd,re,shutil,signal,stat,sys,tempfile,traceback

SOURCES={'phase4-p2-recover.py','phase4_p2_recovery.py','phase4_p2_controller.py','phase4_p2_write_core.py',
    'phase4_recovery_image.py','phase4_root_recovery.py','phase4_backup_core.py','phase4_root_migration.py',
    'phase4-offline-backup.py','phase4-physical-capture.py','context.json','attempt.json','host-backup-ack.json'}

def need(ok,message):
    if not ok:raise ValueError(message)

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def bootstrap():
    need(os.geteuid()==0 and platform.machine()=='x86_64','Local Deck sudo required')
    need(Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),'Deck required')
    source=Path(__file__).resolve().parent;manifest=json.loads((source/'package.json').read_text())
    need(manifest['operation']=='recover-p2-only' and set(manifest['files'])==SOURCES,'Finite recovery package')
    root=Path(tempfile.mkdtemp(prefix='muos-r35s-c89.',dir='/run'));root.chmod(0o700)
    for name,wanted in manifest['files'].items():
        fd=os.open(source/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and 0<s.st_size<=1024*1024 and not s.st_mode&0o022,'Unsafe payload leaf')
            data=os.read(fd,s.st_size+1);a=os.fstat(fd)
            need((s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns),'Payload changed')
            need(len(data)==s.st_size and hashlib.sha256(data).hexdigest()==wanted,'Payload hash')
            with (root/name).open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
            (root/name).chmod(0o400)
        finally:os.close(fd)
    os.execve('/usr/bin/python3',['/usr/bin/python3',str(root/'phase4-p2-recover.py'),'_recover'],
        {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})

def validate_context(ctx,capture,policy,recovery):
    keys={'schema','operation','physical_capture','backup_directory','backup_receipt_sha256','backup_artifacts',
        'host_backup_ack_sha256','recovery_file','recovery_sha256','expected_observed_sha256','expected_recovery_counter','next_attempt_id','qualified_kernel'}
    need(type(ctx) is dict and set(ctx)==keys and ctx['schema']==89 and ctx['operation']=='recover-p2-only','Recovery context schema')
    capture.validate_context(ctx['physical_capture'],'postboot',policy,recovery)
    for n in ['backup_receipt_sha256','host_backup_ack_sha256','recovery_sha256','expected_observed_sha256']:policy.digest(ctx[n])
    recovery.sequence(ctx['expected_recovery_counter'])
    need(type(ctx['qualified_kernel']) is str and 0<len(ctx['qualified_kernel'])<=128,'Qualified kernel binding')
    need(type(ctx['next_attempt_id']) is str and re.fullmatch('[0-9a-f]{32}',ctx['next_attempt_id']),'Next intent ID')
    need(re.fullmatch(r'/var/tmp/muos-r35s-c81-backup\.[a-z0-9_]{8}',ctx['backup_directory']),'Known Deck backup directory')
    need(re.fullmatch(r'/home/deck/muos-r35s-c89-recovery\.[a-z0-9_]{8}/recovery\.ext4',ctx['recovery_file']),'Known staged recovery file')
    allowed={'prefix.backup','boot.fat','root.ext4','private-files.json','userdata.tar','userdata-manifest.json'}
    need(type(ctx['backup_artifacts']) is dict and allowed<=set(ctx['backup_artifacts']) and len(ctx['backup_artifacts'])<=13,'Backup inventory')
    for n,row in ctx['backup_artifacts'].items():
        need(n in allowed or re.fullmatch(r'private-[0-9]{2}\.dat',n),'Backup artifact name')
        need(type(row) is dict and set(row)=={'sha256','bytes'} and type(row['bytes']) is int and 0<row['bytes']<=640*1024*1024,'Backup artifact schema')
        policy.digest(row['sha256'])
    need(ctx['backup_artifacts']['prefix.backup']['bytes']==640*1024*1024
        and ctx['backup_artifacts']['root.ext4']['bytes']==policy.ROOT_BYTES,'Backup image dimensions')
    need(ctx['backup_artifacts']['prefix.backup']['sha256']==ctx['physical_capture']['backup_prefix_sha256'],'Prefix backup hash binding')

def checked_regular(path,expected_sha256,expected_bytes,account):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        s=os.fstat(fd)
        need(stat.S_ISREG(s.st_mode) and s.st_uid==account.pw_uid and s.st_nlink==1
            and stat.S_IMODE(s.st_mode) in (0o400,0o600) and s.st_size==expected_bytes,'Private source leaf metadata')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return fd,s
    except BaseException:os.close(fd);raise

def copy_image(path,wanted,target,account,core,image,size):
    # Only fixed role paths from validated_context reach this routine.
    parent=path.parent;s=parent.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==account.pw_uid and stat.S_IMODE(s.st_mode)==0o700,'Private source parent')
    fd,before=checked_regular(path,wanted,size,account)
    try:
        need(image.fd_sha(fd)==wanted,'Private image source hash')
        out=os.open(target,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:image.sparse_clone(fd,out,size);need(image.fd_sha(out)==wanted,'Sealed image readback')
        finally:os.close(out)
        need(image.signature(os.fstat(fd))==image.signature(before) and image.fd_sha(fd)==wanted,'Private source changed')
    finally:os.close(fd)
    core.sync_dir(target.parent)

def check_backup(ctx,root,account,core,image):
    parent=Path(ctx['backup_directory']);s=parent.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==account.pw_uid and stat.S_IMODE(s.st_mode)==0o700,'Backup parent identity')
    need({p.name for p in parent.iterdir()}==set(ctx['backup_artifacts'])|{'backup.json'},'Backup inventory changed')
    for name,row in ctx['backup_artifacts'].items():
        fd,before=checked_regular(parent/name,row['sha256'],row['bytes'],account)
        try:
            need(image.fd_sha(fd)==row['sha256'] and image.signature(os.fstat(fd))==image.signature(before),'Backup artifact changed')
        finally:os.close(fd)
    # Metadata is read through an owned descriptor too, not a path reopened
    # after verification. The pinned hash comes from the independent host.
    fd=os.open(parent/'backup.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_uid==account.pw_uid and s.st_nlink==1
            and stat.S_IMODE(s.st_mode)==0o400 and 0<s.st_size<=1024*1024,'Backup receipt metadata')
        data=os.read(fd,s.st_size+1);need(len(data)==s.st_size and hashlib.sha256(data).hexdigest()==ctx['backup_receipt_sha256'],'Backup receipt hash')
        receipt=json.loads(data)
    finally:os.close(fd)
    ack_raw=(root/'host-backup-ack.json').read_bytes();need(hashlib.sha256(ack_raw).hexdigest()==ctx['host_backup_ack_sha256'],'Host backup acknowledgment hash')
    ack=json.loads(ack_raw);capture=ctx['physical_capture']
    need(ack['passed'] is True and ack['independent_host_copy_verified'] is True and ack['host_files_and_directory_fsynced'] is True
        and ack['helper_receipt_sha256']==ctx['backup_receipt_sha256'] and ack['prefix_sha256']==capture['backup_prefix_sha256']
        and ack['remote_backup']==ctx['backup_directory'],'Independent backup acknowledgment')
    need(receipt['passed'] is True and receipt['artifacts']==ctx['backup_artifacts'] and receipt['boot_sequence']==capture['backup_counter']
        and receipt['prefix_sha256']==capture['backup_prefix_sha256'],'Backup receipt binding')
    return receipt

def operation():
    root=Path(__file__).resolve().parent
    need(os.geteuid()==0 and re.fullmatch(r'/run/muos-r35s-c89\.[a-z0-9_]{8}',str(root)),'Protected root snapshot required')
    s=root.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'Root snapshot identity')
    need({p for p in Path('/run').glob('muos-r35s-c*')}=={root},'Prior root helper/snapshot requires inspection before any retry')
    import phase4_backup_core as core,phase4_root_migration as policy,phase4_root_recovery as recovery
    import phase4_recovery_image as image,phase4_p2_recovery as writer
    capture=module('physical_capture',root/'phase4-physical-capture.py');guard=module('physical_guard',root/'phase4-offline-backup.py')
    ctx=json.loads((root/'context.json').read_text());validate_context(ctx,capture,policy,recovery)
    need(platform.release()==ctx['qualified_kernel'],'Deck kernel changed since block qualification')
    guard.core=core;guard.policy=policy;guard.ROOT=root;guard.plan=ctx['physical_capture']
    attempt_raw=(root/'attempt.json').read_bytes();attempt=json.loads(attempt_raw)
    need(recovery.encoded(attempt)==attempt_raw and recovery.hashed(attempt_raw)==ctx['physical_capture']['attempt_sha256'],'Sealed prior intent hash')
    recovery.checked_attempt(attempt,ctx['physical_capture']['backup_private_files'],ctx['physical_capture']['backup_counter'],ctx['physical_capture']['backup_prefix_sha256'])
    need(ctx['next_attempt_id']!=attempt['attempt_id'],'Never reuse intent ID')
    libc=ctypes.CDLL(None,use_errno=True)
    need(libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0,'Private namespace required')
    need(os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'),'Namespace not isolated')
    guard.identity();capture.protect_aliases(guard,policy,ctx['physical_capture'])
    parent=Path('/var/tmp');s=parent.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and bool(s.st_mode&stat.S_ISVTX),'Persistent sticky root-owned parent')
    row=guard.run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN']).stdout.split()
    need(len(row)==2 and row[0] in ('ext4','btrfs') and row[1] not in guard.numbers(),'Persistent off-card recovery stage')
    need(shutil.disk_usage(parent).free>=4*1024**3,'Need 4GiB off-card workspace')
    stage=Path(tempfile.mkdtemp(prefix='muos-r35s-c89-recovery.',dir=parent));stage.chmod(0o700);account=pwd.getpwnam('deck')
    try:
        print('C89_STEP=verified-backups',flush=True);receipt=check_backup(ctx,root,account,core,image)
        copy_image(Path(ctx['backup_directory'])/'root.ext4',ctx['backup_artifacts']['root.ext4']['sha256'],stage/'backup.ext4',account,core,image,policy.ROOT_BYTES)
        copy_image(Path(ctx['recovery_file']),ctx['recovery_sha256'],stage/'recovery.ext4',account,core,image,policy.ROOT_BYTES)
        fresh=stage/'capture';fresh.mkdir(mode=0o700)
        print('C89_STEP=fresh-readonly-capture',flush=True)
        observed=capture.capture(guard,core,policy,recovery,image,ctx['physical_capture'],'postboot',fresh,attempt)
        need(observed['root_sha256']==ctx['expected_observed_sha256'],'Physical p2 changed since composed recovery')
        physical_context=json.loads((fresh/'capture-context.json').read_text())
        validation=stage/'validation';validation.mkdir(mode=0o700);journal=stage/'write-journal';journal.mkdir(mode=0o700)
        controller=writer.card_target(guard,capture,ctx['physical_capture'],journal)
        print('C89_STEP=hash-entire-protected-complement',flush=True)
        fd=guard.open_card()
        try:
            capture.verify_ro(guard,fd);protected=controller.protected(fd)
            need(core.region_sha(fd,policy.ROOT_OFFSET,policy.ROOT_BYTES)==ctx['expected_observed_sha256'],'Physical root changed before transaction')
        finally:os.close(fd)
        derived=[]
        def validate(source):
            plan=writer.validate_fd(source,stage/'backup.ext4',ctx['backup_artifacts']['root.ext4']['sha256'],
                fresh/'root.ext4',ctx['expected_observed_sha256'],policy.ROOT_BYTES,validation,
                ctx['physical_capture']['backup_private_files'],ctx['physical_capture']['backup_counter'],
                ctx['physical_capture']['backup_prefix_sha256'],attempt,physical_context,receipt['source_root_modes']['p2'])
            need(plan['recovery_counter']==ctx['expected_recovery_counter'],'Fresh counter differs from composed image');derived.append(plan)
        print('C89_STEP=p2-only-transaction-no-automatic-retry',flush=True)
        with image.source_image(stage/'recovery.ext4',ctx['recovery_sha256'],policy.ROOT_BYTES) as source:
            result=controller.apply(source,ctx['recovery_sha256'],ctx['expected_observed_sha256'],protected,validate)
        need(result['passed'] is True and len(derived)==1,'Verified transaction incomplete')
        handoff=stage/'handoff';handoff.mkdir(mode=0o700)
        next_intent=recovery.attempt_record(ctx['physical_capture']['backup_private_files'],ctx['physical_capture']['backup_counter'],
            ctx['physical_capture']['backup_prefix_sha256'],ctx['recovery_sha256'],derived[0]['recovery_counter'],ctx['next_attempt_id'])
        fence=recovery.seal_attempt(handoff,next_intent)
        need(recovery.load_attempt(handoff,ctx['next_attempt_id'],core.sha(fence))==next_intent,'Next fence readback')
        capture.protect_aliases(guard,policy,ctx['physical_capture'])
        report={'passed':True,'schema':89,'operation':'recover-p2-only','written_bytes':policy.ROOT_BYTES,
            'recovery_sha256':ctx['recovery_sha256'],'recovery_counter':derived[0]['recovery_counter'],
            'next_attempt_id':ctx['next_attempt_id'],'next_attempt_sha256':core.sha(fence),'prior_attempt_sha256':recovery.hashed(attempt_raw),
            'physical_card_p2_written':True,'p1_MBR_p3_full_complement_preserved':True,'all_four_aliases_kernel_readonly':True,
            'fresh_capture_and_three_image_scans_verified':True,'new_no_credit_seed_verified_not_loaded':True,
            'boot_handoff_authorized':False,'independent_host_copy_of_next_fence_required':True,
            'source_sha256':{n:core.sha(root/n) for n in sorted(SOURCES)}}
        core.write_new(stage/'analysis.json',recovery.encoded(report))
        for p in stage.rglob('*'):
            p.chmod(0o700 if p.is_dir() else 0o400);os.chown(p,account.pw_uid,account.pw_gid)
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|(os.O_DIRECTORY if p.is_dir() else 0))
            try:os.fsync(fd)
            finally:os.close(fd)
        os.chown(stage,account.pw_uid,account.pw_gid);core.sync_dir(stage);core.sync_dir(parent)
        shutil.rmtree(root)
        print('C89 RECOVERY COMPLETE '+str(stage),flush=True)
        print('Keep card offline/RO until the host has verified the new handoff fence.',flush=True)
    except BaseException as error:
        details={'passed':False,'error_type':type(error).__name__,'reason':str(error),'traceback':traceback.format_exc(),
            'partial':str(stage),'snapshot':str(root),'completion_must_not_be_assumed':True,'automatic_retry_or_rollback':False}
        try:capture.protect_aliases(guard,policy,ctx['physical_capture']);details['RO_reinforced']=True
        except BaseException:details['RO_reinforced']=False
        out=Path(tempfile.mkdtemp(prefix='muos-r35s-c89-failure.',dir=parent));out.chmod(0o700)
        core.write_new(out/'failure.json',recovery.encoded(details));leaf=out/'failure.json';leaf.chmod(0o400)
        os.chown(leaf,account.pw_uid,account.pw_gid);os.chown(out,account.pw_uid,account.pw_gid)
        core.sync_dir(out);core.sync_dir(parent)
        print('C89 private failure report '+str(out),file=sys.stderr,flush=True);raise

if __name__=='__main__':
    os.umask(0o077)
    def interrupted(signum,frame):raise SystemExit(128+signum)
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    try:
        need(len(sys.argv)==2 and sys.argv[1] in ('recover','_recover'),'Only finite recovery')
        if sys.argv[1]=='recover':bootstrap()
        else:operation()
    except BaseException as error:
        print('C89 FAILED ('+type(error).__name__+'); keep card offline/RO and partial journal; no automatic retry or rollback.',file=sys.stderr);sys.exit(1)
