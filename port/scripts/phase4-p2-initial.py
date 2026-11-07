#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C94 finite initial C79 p2-only migration, distinct from C89 recovery."""
from pathlib import Path
import ctypes,hashlib,importlib.util,json,os,platform,pwd,re,shutil,signal,stat,sys,tempfile,traceback

C79_FACTORY_SHA256='a09edf63ac5397b0adc5bdf7d9eb7413f6e02e7963e569b915df0ffe674d08fc'
SOURCES={'phase4-p2-initial.py','phase4-p2-recover.py','phase4_p2_initial.py','phase4_initial_migration.py',
    'phase4_initial_image.py','phase4_p2_recovery.py','phase4_p2_controller.py','phase4_p2_write_core.py',
    'phase4_recovery_image.py','phase4_root_recovery.py','phase4_backup_core.py','phase4_root_migration.py',
    'phase4-offline-backup.py','phase4-physical-capture.py','context.json','attempt.json',
    'host-backup-ack.json','host-recovery-ack.json','host-recovery-boot.json'}

def need(ok,message):
    if not ok:raise ValueError(message)

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def bootstrap():
    need(os.geteuid()==0 and platform.machine()=='x86_64','Local Deck sudo required')
    need(Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),'Deck required')
    source=Path(__file__).resolve().parent;manifest=json.loads((source/'package.json').read_text())
    need(manifest['operation']=='migrate-initial-p2-only' and set(manifest['files'])==SOURCES,'Finite initial package')
    root=Path(tempfile.mkdtemp(prefix='muos-r35s-c94.',dir='/run'));root.chmod(0o700)
    for name,wanted in manifest['files'].items():
        fd=os.open(source/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            before=os.fstat(fd);need(stat.S_ISREG(before.st_mode) and before.st_nlink==1
                and 0<before.st_size<=1024*1024 and not before.st_mode&0o022,'Unsafe package leaf')
            data=os.read(fd,before.st_size+1);after=os.fstat(fd)
            need((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
                (after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Package leaf changed')
            need(len(data)==before.st_size and hashlib.sha256(data).hexdigest()==wanted,'Package leaf hash')
            with (root/name).open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
            (root/name).chmod(0o400)
        finally:os.close(fd)
    os.execve('/usr/bin/python3',['/usr/bin/python3',str(root/'phase4-p2-initial.py'),'_migrate'],
        {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})

def validate_context(ctx,capture,policy,recovery):
    keys={'schema','operation','physical_capture','backup_directory','backup_receipt_sha256','backup_artifacts',
        'host_backup_ack_sha256','factory_file','factory_sha256','candidate_file','candidate_sha256',
        'expected_observed_sha256','expected_migration_counter','next_attempt_id','qualified_kernel',
        'recovery_ack_sha256','recovery_boot_sha256','known_boot_floor'}
    need(type(ctx) is dict and set(ctx)==keys and type(ctx['schema']) is int and ctx['schema']==94 and
        ctx['operation']=='migrate-initial-p2-only','Initial context schema/operation')
    capture.validate_context(ctx['physical_capture'],'postboot',policy,recovery)
    for n in ['backup_receipt_sha256','host_backup_ack_sha256','factory_sha256','candidate_sha256',
        'expected_observed_sha256','recovery_ack_sha256','recovery_boot_sha256']:policy.digest(ctx[n])
    need(ctx['factory_sha256']==C79_FACTORY_SHA256 and ctx['candidate_sha256']!=C79_FACTORY_SHA256,
        'Only the pinned C79 factory and a privately provisioned candidate are allowed')
    recovery.sequence(ctx['expected_migration_counter']);recovery.sequence(ctx['known_boot_floor'])
    need(ctx['expected_migration_counter']>ctx['known_boot_floor'],'Migration counter below known boot floor')
    need(type(ctx['qualified_kernel']) is str and 0<len(ctx['qualified_kernel'])<=128,'Qualified Deck kernel binding')
    need(type(ctx['next_attempt_id']) is str and re.fullmatch('[0-9a-f]{32}',ctx['next_attempt_id']),'Next handoff ID')
    need(re.fullmatch(r'/var/tmp/muos-r35s-c81-backup\.[a-z0-9_]{8}',ctx['backup_directory']),'Known Deck backup role')
    for role in ['factory','candidate']:
        need(re.fullmatch(r'/home/deck/muos-r35s-c94-'+role+r'\.[a-z0-9_]{8}/'+role+r'\.ext4',ctx[role+'_file']),
            'Finite staged '+role+' role')
    allowed={'prefix.backup','boot.fat','root.ext4','private-files.json','userdata.tar','userdata-manifest.json'}
    need(type(ctx['backup_artifacts']) is dict and allowed<=set(ctx['backup_artifacts']) and
        len(ctx['backup_artifacts'])<=13,'Backup inventory')
    for name,row in ctx['backup_artifacts'].items():
        need(name in allowed or re.fullmatch(r'private-[0-9]{2}\.dat',name),'Backup artifact leaf')
        need(type(row) is dict and set(row)=={'sha256','bytes'} and type(row['bytes']) is int and
            0<row['bytes']<=640*1024*1024,'Backup artifact schema');policy.digest(row['sha256'])
    need(ctx['backup_artifacts']['prefix.backup']['bytes']==640*1024*1024 and
        ctx['backup_artifacts']['root.ext4']['bytes']==policy.ROOT_BYTES and
        ctx['backup_artifacts']['prefix.backup']['sha256']==ctx['physical_capture']['backup_prefix_sha256'],
        'Backup dimensions/prefix binding')

def validate_lineage(ctx,root,attempt,core,recovery):
    raw=(root/'host-recovery-ack.json').read_bytes();boot_raw=(root/'host-recovery-boot.json').read_bytes()
    need(core.sha(root/'host-recovery-ack.json')==ctx['recovery_ack_sha256'] and
        recovery.hashed(boot_raw)==ctx['recovery_boot_sha256'],'Qualified recovery/boot file hashes')
    ack=json.loads(raw);boot=json.loads(boot_raw)
    need(all(ack[n] is True for n in ['passed','physical_p2_recovery_verified',
        'new_fence_independent_host_copy_verified','all_receipts_and_directory_fsynced']),
        'Independent physical recovery/fence qualification required')
    need(ack['next_attempt_id']==attempt['attempt_id'] and
        ack['next_attempt_sha256']==ctx['physical_capture']['attempt_sha256']==recovery.hashed(recovery.encoded(attempt)),
        'Current recovery fence binding')
    need(boot['passed'] is True and boot['physical_boot_after_recovery_qualified'] is True and
        boot['recovery_host_copy_sha256']==ctx['recovery_ack_sha256'] and type(boot['boot_sequence']) is int and
        boot['boot_sequence']==ctx['known_boot_floor']==attempt['counter_floor']+1,'Qualified recovery first boot binding')
    need(all(boot[n] is True for n in ['seedless_start_without_crediting_2048bits_verified',
        'rng_ready_before_new_creditable_seed_and_stop_verified','old_seed_hashes_absent']),
        'Qualified no-credit recovery entropy path required')

def transaction(root,stage,ctx,attempt,account,core,policy,recovery,image,target,initial,capture,guard,shared):
    """Run one transaction; hardware adapters remain fixed by operation()."""
    print('C94_STEP=verify-backups-and-pin-factory',flush=True)
    shared.check_backup(ctx,root,account,core,image)
    for role in ['factory','candidate']:
        shared.copy_image(Path(ctx[role+'_file']),ctx[role+'_sha256'],stage/(role+'.ext4'),account,core,image,policy.ROOT_BYTES)
    fresh=stage/'capture';fresh.mkdir(mode=0o700)
    print('C94_STEP=fresh-readonly-capture',flush=True)
    observed=capture.capture(guard,core,policy,recovery,image,ctx['physical_capture'],'postboot',fresh,attempt)
    need(observed['root_sha256']==ctx['expected_observed_sha256'] and
        observed['boot_sequence']>=ctx['known_boot_floor'],'Physical p2 changed or is below the known boot floor')
    physical=json.loads((fresh/'capture-context.json').read_text())
    validation=stage/'validation';validation.mkdir(mode=0o700);journal=stage/'write-journal';journal.mkdir(mode=0o700)
    controller=target.card_target(guard,capture,ctx['physical_capture'],journal)
    print('C94_STEP=hash-entire-protected-complement',flush=True)
    fd=guard.open_card()
    try:
        capture.verify_ro(guard,fd);protected=controller.protected(fd)
        need(core.region_sha(fd,policy.ROOT_OFFSET,policy.ROOT_BYTES)==ctx['expected_observed_sha256'],'Current p2 changed before transaction')
    finally:os.close(fd)
    derived=[]
    def validate(source):
        plan=initial.validate_fd(source,ctx['candidate_sha256'],stage/'factory.ext4',ctx['factory_sha256'],
            fresh/'root.ext4',ctx['expected_observed_sha256'],policy.ROOT_BYTES,validation,
            ctx['physical_capture']['backup_private_files'],ctx['physical_capture']['backup_counter'],
            ctx['physical_capture']['backup_prefix_sha256'],attempt,physical)
        need(plan['recovery_counter']==ctx['expected_migration_counter'],'Fresh migration counter differs');derived.append(plan)
    print('C94_STEP=initial-p2-only-transaction-no-retry',flush=True)
    with image.source_image(stage/'candidate.ext4',ctx['candidate_sha256'],policy.ROOT_BYTES) as source:
        result=controller.apply(source,ctx['candidate_sha256'],ctx['expected_observed_sha256'],protected,validate)
    need(result['passed'] is True and len(derived)==1,'Verified initial transaction incomplete')
    handoff=stage/'handoff';handoff.mkdir(mode=0o700)
    next_record=recovery.attempt_record(ctx['physical_capture']['backup_private_files'],ctx['physical_capture']['backup_counter'],
        ctx['physical_capture']['backup_prefix_sha256'],ctx['candidate_sha256'],derived[0]['recovery_counter'],ctx['next_attempt_id'])
    fence=recovery.seal_attempt(handoff,next_record)
    need(recovery.load_attempt(handoff,ctx['next_attempt_id'],core.sha(fence))==next_record,'New handoff readback')
    capture.protect_aliases(guard,policy,ctx['physical_capture'])
    report={'passed':True,'schema':94,'operation':'migrate-initial-p2-only','written_bytes':policy.ROOT_BYTES,
        'candidate_sha256':ctx['candidate_sha256'],'factory_sha256':C79_FACTORY_SHA256,
        'migration_counter':derived[0]['recovery_counter'],'next_attempt_id':ctx['next_attempt_id'],
        'next_attempt_sha256':core.sha(fence),'prior_attempt_sha256':ctx['physical_capture']['attempt_sha256'],
        'physical_card_p2_written':True,'p1_MBR_p3_full_complement_preserved':True,
        'all_four_aliases_kernel_readonly':True,'fresh_capture_and_three_image_scans_verified':True,
        'new_no_credit_seed_verified_not_loaded':True,'pinned_C79_factory_verified':True,
        'recovery_and_first_boot_qualification_checked':True,'boot_handoff_authorized':False,
        'independent_host_copy_of_next_fence_required':True,'physical_boot_after_initial_migration_qualified':False,
        'source_sha256':{n:core.sha(root/n) for n in sorted(SOURCES)}}
    core.write_new(stage/'analysis.json',recovery.encoded(report))
    return report


def operation():
    root=Path(__file__).resolve().parent
    need(os.geteuid()==0 and re.fullmatch(r'/run/muos-r35s-c94\.[a-z0-9_]{8}',str(root)),'Protected root snapshot required')
    s=root.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'Root snapshot identity')
    need(set(Path('/run').glob('muos-r35s-c*'))=={root},'Prior root helper requires inspection; never retry blindly')
    import phase4_backup_core as core,phase4_root_migration as policy,phase4_root_recovery as recovery
    import phase4_recovery_image as image,phase4_p2_recovery as target,phase4_p2_initial as initial
    capture=module('initial_capture',root/'phase4-physical-capture.py');guard=module('initial_guard',root/'phase4-offline-backup.py')
    shared=module('initial_shared_copy',root/'phase4-p2-recover.py')
    ctx=json.loads((root/'context.json').read_text());validate_context(ctx,capture,policy,recovery)
    need(platform.release()==ctx['qualified_kernel'],'Deck kernel changed since qualification')
    guard.core=core;guard.policy=policy;guard.ROOT=root;guard.plan=ctx['physical_capture']
    raw=(root/'attempt.json').read_bytes();attempt=json.loads(raw)
    need(recovery.encoded(attempt)==raw and recovery.hashed(raw)==ctx['physical_capture']['attempt_sha256'],'Canonical current handoff record')
    recovery.checked_attempt(attempt,ctx['physical_capture']['backup_private_files'],
        ctx['physical_capture']['backup_counter'],ctx['physical_capture']['backup_prefix_sha256'])
    need(ctx['next_attempt_id']!=attempt['attempt_id'],'Next handoff ID must be unused')
    validate_lineage(ctx,root,attempt,core,recovery)
    libc=ctypes.CDLL(None,use_errno=True)
    need(libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0,'Private namespace required')
    need(os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'),'Namespace not isolated')
    guard.identity();capture.protect_aliases(guard,policy,ctx['physical_capture'])
    parent=Path('/var/tmp');s=parent.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and s.st_mode&stat.S_ISVTX,'Persistent sticky root-owned parent')
    row=guard.run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN']).stdout.split()
    need(len(row)==2 and row[0] in ('ext4','btrfs') and row[1] not in guard.numbers(),'Persistent off-card stage')
    need(shutil.disk_usage(parent).free>=4*1024**3,'Need 4GiB off-card workspace')
    stage=Path(tempfile.mkdtemp(prefix='muos-r35s-c94-initial.',dir=parent));stage.chmod(0o700);account=pwd.getpwnam('deck')
    try:
        transaction(root,stage,ctx,attempt,account,core,policy,recovery,image,target,initial,capture,guard,shared)
        for p in stage.rglob('*'):
            p.chmod(0o700 if p.is_dir() else 0o400);os.chown(p,account.pw_uid,account.pw_gid)
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|(os.O_DIRECTORY if p.is_dir() else 0))
            try:os.fsync(fd)
            finally:os.close(fd)
        os.chown(stage,account.pw_uid,account.pw_gid);core.sync_dir(stage);core.sync_dir(parent)
        shutil.rmtree(root);print('C94 INITIAL MIGRATION COMPLETE '+str(stage),flush=True)
        print('Keep card offline/RO until the host verifies the new handoff record.',flush=True)
    except BaseException as error:
        info={'passed':False,'error_type':type(error).__name__,'reason':str(error),'traceback':traceback.format_exc(),
            'partial':str(stage),'snapshot':str(root),'completion_must_not_be_assumed':True,'automatic_retry_or_rollback':False}
        try:capture.protect_aliases(guard,policy,ctx['physical_capture']);info['RO_reinforced']=True
        except BaseException:info['RO_reinforced']=False
        out=Path(tempfile.mkdtemp(prefix='muos-r35s-c94-failure.',dir=parent));out.chmod(0o700)
        core.write_new(out/'failure.json',recovery.encoded(info));leaf=out/'failure.json';leaf.chmod(0o400)
        os.chown(leaf,account.pw_uid,account.pw_gid);os.chown(out,account.pw_uid,account.pw_gid)
        core.sync_dir(out);core.sync_dir(parent);print('C94 private failure report '+str(out),file=sys.stderr,flush=True);raise

if __name__=='__main__':
    os.umask(0o077)
    def interrupted(signum,frame):raise SystemExit(128+signum)
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    try:
        need(len(sys.argv)==2 and sys.argv[1] in ('migrate','_migrate'),'Only finite initial migration')
        if sys.argv[1]=='migrate':bootstrap()
        else:operation()
    except BaseException as error:
        print('C94 FAILED ('+type(error).__name__+'); keep card offline/RO and partial journal; never retry/rollback automatically.',file=sys.stderr);sys.exit(1)
