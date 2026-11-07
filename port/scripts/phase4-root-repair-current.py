#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C96 two-sector root-mode repair from current independent C95 preimages.

Not a rollback, image writer or extension of C89's recovery mode. C83 supplies
inode planning/writing; C87 supplies verified control FDs/claims/RO cleanup.
"""
from pathlib import Path
import ctypes,fcntl,hashlib,importlib.util,json,os,platform,pwd,re,shutil,signal,stat,struct,sys,tempfile,traceback

SOURCES={'phase4-root-repair-current.py','phase4-card-rearm.py','phase4-root-permissions.py','phase4_root_metadata.py',
    'phase4_backup_core.py','phase4_root_migration.py','phase4-offline-backup.py','phase4-physical-capture.py',
    'phase4_p2_recovery.py','phase4_p2_controller.py','phase4_p2_write_core.py','phase4_recovery_image.py','phase4_root_recovery.py',
    'context.json','repair-inputs.json','host-current-ack.json','native-capture.json','capture-context.json'}

def need(ok,message):
    if not ok:raise ValueError(message)

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def bootstrap():
    need(os.geteuid()==0 and platform.machine()=='x86_64','Local Deck sudo required')
    need(Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),'Deck required')
    source=Path(__file__).resolve().parent;manifest=json.loads((source/'package.json').read_text())
    need(manifest['operation']=='repair-current-root-modes' and set(manifest['files'])==SOURCES,'Finite current-metadata package')
    root=Path(tempfile.mkdtemp(prefix='muos-r35s-c96.',dir='/run'));root.chmod(0o700)
    for n,h in manifest['files'].items():
        fd=os.open(source/n,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and 0<s.st_size<=1024*1024 and not s.st_mode&0o022,'Unsafe payload leaf')
            raw=os.read(fd,s.st_size+1);a=os.fstat(fd)
            need((s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns),'Payload changed')
            need(len(raw)==s.st_size and hashlib.sha256(raw).hexdigest()==h,'Payload hash')
            with (root/n).open('xb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
            (root/n).chmod(0o400)
        finally:os.close(fd)
    os.execve('/usr/bin/python3',['/usr/bin/python3',str(root/'phase4-root-repair-current.py'),'_repair'],
        {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})

def validate_lineage(root,ctx,core,recovery,rearm):
    need(type(ctx) is dict and set(ctx)=={'schema','operation','capture_context_sha256','native_capture_sha256','host_current_ack_sha256',
        'repair_inputs_sha256','qualified_kernel'},'Finite repair context')
    need(type(ctx['schema']) is int and ctx['schema']==96 and ctx['operation']=='repair-current-root-modes','Finite repair operation')
    need(type(ctx['qualified_kernel']) is str and 0<len(ctx['qualified_kernel'])<=128,'Qualified kernel')
    names={'capture_context_sha256':'capture-context.json','native_capture_sha256':'native-capture.json',
        'host_current_ack_sha256':'host-current-ack.json','repair_inputs_sha256':'repair-inputs.json'}
    for field,name in names.items():recovery.digest(ctx[field]);need(core.sha(root/name)==ctx[field],'Current metadata lineage hash')
    cap=json.loads((root/'capture-context.json').read_text());rearm.validate_context(cap,load('current_policy',root/'phase4_root_migration.py'))
    native=json.loads((root/'native-capture.json').read_text());ack=json.loads((root/'host-current-ack.json').read_text());plan=json.loads((root/'repair-inputs.json').read_text())
    need(ack['passed'] is True and ack['schema']==95 and ack['current_preimage_and_capsules_independently_verified'] is True
        and ack['no_payload_repair_executed'] is True and ack['all_aliases_RO_and_guard_verified'] is True,'Independent current preimage required')
    for source,field in [('context.json','capture_context_sha256'),('analysis.json','native_capture_sha256'),('repair-inputs.json','repair_inputs_sha256')]:
        need(ack['files'][source]==ctx[field],'Independent current receipt binding')
    need(native['passed'] is True and native['schema']==95 and native['operation']=='protect-and-capture' and
        native['context_sha256']==ctx['capture_context_sha256'] and native['attempt_sha256']==cap['attempt_sha256'] and
        native['boot_sequence']==cap['expected_boot_sequence'] and native['runtime_guard_sha256']==cap['runtime_guard_sha256'],
        'Fresh protection snapshot binding')
    need(type(native['prefix_bytes']) is int and native['prefix_bytes']==640*1024*1024 and
        native['root_modes']=={'p2':0o777,'p3':0o777} and native['p2_fsck_exit']==native['p3_fsck_exit']==0,
        'Clean current snapshot and root modes required')
    for n in ['physical_payload_written','repair_applied','media_unlocked','seed_loaded_or_generated']:need(native[n] is False,'Capture unexpectedly wrote payload')
    for n in ['historical_independent_backup_reverified','userdata_matches_C82','all_four_aliases_kernel_readonly','runtime_guard_restored_or_reverified']:
        need(native[n] is True,'Incomplete protected capture')
    for n,h in native['source_sha256'].items():
        need(n in rearm.SOURCES,'Unknown capture source')
        need(core.sha(root/('capture-context.json' if n=='context.json' else n))==h,'Captured source changed')
    need(set(native['source_sha256'])==rearm.SOURCES,'Incomplete capture source inventory')
    need(type(plan) is dict and set(plan)=={'schema','current_prefix_before_sha256','current_prefix_after_sha256','patches',
        'native_receipt_sha256','context_sha256','independent_current_preimage_verified','payload_write_authorized'},'Finite current repair plan')
    need(plan['schema']==95 and plan['independent_current_preimage_verified'] is True and plan['payload_write_authorized'] is False and
        plan['context_sha256']==ctx['capture_context_sha256'] and plan['native_receipt_sha256']==ctx['native_capture_sha256'] and
        plan['current_prefix_before_sha256']==native['current_prefix_sha256']==ack['files']['current-prefix.backup'] and
        plan['patches']==native['patches'] and set(plan['patches'])=={'2','3'},'Current plan/preimage binding')
    for n in ['current_prefix_before_sha256','current_prefix_after_sha256']:recovery.digest(plan[n])
    return cap,plan

def repair(stage,ctx,cap,plan,legacy,guard,core,metadata,controller):
    """Coordinate fixed metadata writes; caller derives controller from test128."""
    expected=legacy.backup_check()
    for n in (2,3):legacy.run(['e2fsck','-fn','/dev/mmcblk0p'+str(n)]);guard.identity()
    need(legacy.run(['debugfs','-R','cat /var/lib/muos-diagnostic/boot-seq','/dev/mmcblk0p2']).stdout==str(cap['expected_boot_sequence'])+'\n','Counter changed after protection snapshot')
    legacy.userdata_check(0o777,expected);guard.identity()
    capsules={}
    try:
        controller.open_controls();controller.readonly();controller.flush();fd=controller.acquire()
        need(core.region_sha(fd,0,640*1024*1024)==plan['current_prefix_before_sha256'],'Current prefix differs from independent preimage')
        capsules={n:legacy.capsule(fd,n) for n in (2,3)}
        need({str(n):c['patch'] for n,c in capsules.items()}==plan['patches'],'Fresh capsule/geometry differs from current plan')
        for n,c in capsules.items():
            for key in ['sb','gd','sector']:core.write_new(stage/f'p{n}-{key}.bin',c[key])
        # Re-derived capsules, not caller JSON, are the only sector payloads.
        journal={'kind':'CURRENT_ROOT_MODE_REPAIR_MAY_HAVE_STARTED','context_sha256':core.sha(legacy.ROOT/'context.json'),
            'current_prefix_before_sha256':plan['current_prefix_before_sha256'],
            'sectors':{str(n):{'offset':c['patch']['sector_offset'],'before_sha256':c['patch']['before_sha256'],
                'after_sha256':c['patch']['after_sha256']} for n,c in capsules.items()},'automatic_retry_or_rollback':False}
        core.write_new(stage/'unlock-intent.json',(json.dumps(journal,indent=2)+'\n').encode());core.sync_dir(stage);core.sync_dir(stage.parent)
        controller.close_claim();controller.idle();controller.state([1,1,1,1])
        for index in [0,2,3]:fcntl.ioctl(controller.controls[index],0x125d,struct.pack('i',0))
        controller.state([0,1,0,0]);fd=controller.acquire(True)
        controller.flush()
        need(core.region_sha(fd,0,640*1024*1024)==plan['current_prefix_before_sha256'],'Prefix changed before first metadata write')
        for n in (2,3):need(legacy.capsule(fd,n)==capsules[n],'Capsule changed before first metadata write')
        core.write_new(stage/'write-intent.json',(json.dumps(journal,indent=2)+'\n').encode())
        for n in (2,3):
            controller.state([0,1,0,0])
            metadata.apply_sector(fd,capsules[n]['patch'],os.pread,os.pwrite,os.fsync)
        os.fsync(fd);controller.readonly();controller.close_claim();controller.flush();fd=controller.acquire()
        need(core.region_sha(fd,0,640*1024*1024)==plan['current_prefix_after_sha256'],'Repaired full prefix differs')
        for n in (2,3):
            after=legacy.capsule(fd,n,0o40755)
            need(after['sector'].hex()==capsules[n]['patch']['after'] and after['sb']==capsules[n]['sb'] and
                after['gd']==capsules[n]['gd'],'Cold inode/SB/GDT readback differs')
        controller.state([1,1,1,1]);controller.close_claim()
    finally:
        try:
            try:controller.readonly()
            finally:controller.close_claim()
        finally:
            for fd in controller.controls:os.close(fd)
            controller.controls=[]
    for n in (2,3):legacy.run(['e2fsck','-fn','/dev/mmcblk0p'+str(n)]);guard.identity()
    legacy.userdata_check(0o755,expected);guard.identity()
    report={'passed':True,'schema':96,'operation':'repair-current-root-modes','context_sha256':core.sha(legacy.ROOT/'context.json'),
        'boot_sequence':cap['expected_boot_sequence'],'prefix_before_sha256':plan['current_prefix_before_sha256'],
        'prefix_after_sha256':plan['current_prefix_after_sha256'],'patches':plan['patches'],'written_sectors':2,'written_bytes':1024,
        'all_four_aliases_kernel_readonly':True,'runtime_guard_sha256':cap['runtime_guard_sha256'],
        'p2_fsck_exit':0,'p3_fsck_exit':0,'root_modes':{'p2':0o755,'p3':0o755},'userdata_before_and_after_matches_C82':True,
        'full_prefix_posthash_verified':True,'no_superblock_or_GDT_changes':True,'only_two_fixed_sectors_requested':True,
        'cold_readback_verified':True,'seed_loaded_or_generated':False,'automatic_retry_or_rollback':False,
        'boot_handoff_authorized':False,'source_sha256':{n:core.sha(legacy.ROOT/n) for n in sorted(SOURCES)}}
    core.write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());return report

def operation():
    root=Path(__file__).resolve().parent
    need(os.geteuid()==0 and re.fullmatch(r'/run/muos-r35s-c96\.[a-z0-9_]{8}',str(root)),'Protected Deck root snapshot required')
    s=root.lstat();need(s.st_uid==0 and stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==0o700,'Snapshot metadata')
    need(set(Path('/run').glob('muos-r35s-c*'))=={root},'Prior helper must be inspected')
    import phase4_backup_core as core,phase4_root_migration as policy,phase4_root_metadata as metadata,phase4_root_recovery as recovery
    import phase4_p2_recovery as target
    rearm=load('repair_rearm',root/'phase4-card-rearm.py');ctx=json.loads((root/'context.json').read_text())
    cap,plan=validate_lineage(root,ctx,core,recovery,rearm);need(platform.release()==ctx['qualified_kernel'],'Qualified kernel changed')
    guard=load('repair_guard',root/'phase4-offline-backup.py');legacy=load('repair_shared',root/'phase4-root-permissions.py')
    capture=load('repair_capture',root/'phase4-physical-capture.py')
    guard.core=core;guard.policy=policy;guard.ROOT=root;guard.plan={n:cap['legacy_context'][n] for n in ['mbr_sha256','boot_prefix_16MiB_sha256']}
    legacy.ROOT=root;legacy.core=core;legacy.policy=policy;legacy.metadata=metadata;legacy.guard=guard;legacy.ctx=cap['legacy_context']
    libc=ctypes.CDLL(None,use_errno=True)
    need(libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0,'Private namespace required')
    need(os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'),'Namespace not isolated')
    guard.identity();protection={'automount_guard_sha256':cap['runtime_guard_sha256']};capture.protect_aliases(guard,policy,protection)
    parent=Path('/var/tmp');s=parent.lstat();need(s.st_uid==0 and stat.S_ISDIR(s.st_mode) and s.st_mode&stat.S_ISVTX,'Persistent sticky parent')
    row=legacy.run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN']).stdout.split()
    need(len(row)==2 and row[0] in ('ext4','btrfs') and row[1] not in guard.numbers(),'Persistent off-card journal')
    stage=Path(tempfile.mkdtemp(prefix='muos-r35s-c96-repair.',dir=parent));stage.chmod(0o700);account=pwd.getpwnam('deck')
    try:
        journal=stage/'controller-journal';journal.mkdir(mode=0o700)
        controller=target.card_target(guard,capture,protection,journal)
        repair(stage,ctx,cap,plan,legacy,guard,core,metadata,controller)
        for p in stage.rglob('*'):
            p.chmod(0o700 if p.is_dir() else 0o400);os.chown(p,account.pw_uid,account.pw_gid)
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|(os.O_DIRECTORY if p.is_dir() else 0))
            try:os.fsync(fd)
            finally:os.close(fd)
        os.chown(stage,account.pw_uid,account.pw_gid);core.sync_dir(stage);core.sync_dir(parent)
        shutil.rmtree(root);print('C96 REPAIR COMPLETE '+str(stage),flush=True)
    except BaseException as error:
        info={'passed':False,'error_type':type(error).__name__,'reason':str(error),'traceback':traceback.format_exc(),
            'partial':str(stage),'snapshot':str(root),'no_automatic_retry':True}
        try:capture.protect_aliases(guard,policy,protection);info['RO_reinforced']=True
        except BaseException:info['RO_reinforced']=False
        out=Path(tempfile.mkdtemp(prefix='muos-r35s-c96-failure.',dir=parent));out.chmod(0o700)
        core.write_new(out/'failure.json',(json.dumps(info,indent=2)+'\n').encode());(out/'failure.json').chmod(0o400)
        os.chown(out/'failure.json',account.pw_uid,account.pw_gid);os.chown(out,account.pw_uid,account.pw_gid);core.sync_dir(out);core.sync_dir(parent)
        print('C96 failure report '+str(out),file=sys.stderr,flush=True);raise

if __name__=='__main__':
    os.umask(0o077)
    def interrupted(signum,frame):raise SystemExit(128+signum)
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    try:
        need(len(sys.argv)==2 and sys.argv[1] in ('repair','_repair'),'Only current metadata repair')
        bootstrap() if sys.argv[1]=='repair' else operation()
    except BaseException as error:
        print('C96 FAILED ('+type(error).__name__+'); keep card offline, private partials and journal; no retry.',file=sys.stderr);sys.exit(1)
