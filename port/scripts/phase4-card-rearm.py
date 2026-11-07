#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C95 restore the pinned runtime guard/RO and capture current repair preimages.

No payload writer or repair mode. Uses only frozen C83/C82 read/guard utilities.
"""
from pathlib import Path
import ctypes,hashlib,importlib.util,json,os,platform,pwd,re,shutil,stat,sys,tempfile,traceback
import signal

SOURCES={'phase4-card-rearm.py','phase4-root-permissions.py','phase4_root_metadata.py','phase4_backup_core.py',
    'phase4_root_migration.py','phase4-offline-backup.py','context.json'}

def need(ok,message):
    if not ok:raise ValueError(message)

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def validate_context(ctx,policy):
    need(type(ctx) is dict and set(ctx)=={'schema','operation','legacy_context','runtime_guard_sha256','expected_boot_sequence','attempt_sha256'},'Finite rearm context')
    need(type(ctx['schema']) is int and ctx['schema']==95 and ctx['operation']=='protect-and-capture','Rearm operation')
    need(type(ctx['expected_boot_sequence']) is int and 75<=ctx['expected_boot_sequence']<=9998,'Known observed boot required')
    for n in ['runtime_guard_sha256','attempt_sha256']:policy.digest(ctx[n])
    old=ctx['legacy_context']
    keys={'schema','scope','host_copy_verified','metadata_repair_required_before_boot','host_ack_sha256','deck_backup',
        'backup_artifacts','backup_receipt_sha256','prefix_before_sha256','mbr_sha256','boot_prefix_16MiB_sha256','automount_rule_sha256'}
    need(type(old) is dict and set(old)==keys and old['schema']==83 and old['scope']=='inode2_mode0777_to0755_only' and
        old['host_copy_verified'] is True and old['metadata_repair_required_before_boot'] is True,'Pinned historical backup context')
    need(re.fullmatch(r'/var/tmp/muos-r35s-c81-backup\.[a-z0-9_]{8}',old['deck_backup']),'Finite backup role')
    for n in ['host_ack_sha256','backup_receipt_sha256','prefix_before_sha256','mbr_sha256','boot_prefix_16MiB_sha256','automount_rule_sha256']:policy.digest(old[n])

def bootstrap():
    need(os.geteuid()==0 and platform.machine()=='x86_64','Local Deck sudo required')
    need(Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),'Deck required')
    source=Path(__file__).resolve().parent;manifest=json.loads((source/'package.json').read_text())
    need(manifest['operation']=='protect-and-capture' and set(manifest['files'])==SOURCES,'Finite protection-only package')
    root=Path(tempfile.mkdtemp(prefix='muos-r35s-c95.',dir='/run'));root.chmod(0o700)
    for n,wanted in manifest['files'].items():
        fd=os.open(source/n,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            before=os.fstat(fd);need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=1024*1024
                and not before.st_mode&0o022,'Unsafe source leaf')
            raw=os.read(fd,before.st_size+1);after=os.fstat(fd)
            need((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
                (after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Source changed')
            need(len(raw)==before.st_size and hashlib.sha256(raw).hexdigest()==wanted,'Source hash')
            with (root/n).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            (root/n).chmod(0o400)
        finally:os.close(fd)
    os.execve('/usr/bin/python3',['/usr/bin/python3',str(root/'phase4-card-rearm.py'),'_protect'],
        {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})

def protect(stage,ctx,legacy,guard,core,policy):
    """No branch in this body can request writable media or repair a sector."""
    expected=legacy.backup_check()
    rule=Path('/run/udev/rules.d/99-holo-automount.rules')
    if rule.exists() or rule.is_symlink():
        s=rule.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o644 and
            core.sha(rule)==ctx['runtime_guard_sha256'],'Unknown runtime rule; preserve it and abort')
    else:need(legacy.automount_guard()==ctx['runtime_guard_sha256'],'Restored runtime guard differs')
    legacy.readonly_card();guard.identity()
    for n in (2,3):legacy.run(['e2fsck','-fn','/dev/mmcblk0p'+str(n)]);guard.identity()
    boot=legacy.run(['debugfs','-R','cat /var/lib/muos-diagnostic/boot-seq','/dev/mmcblk0p2']).stdout
    need(boot==str(ctx['expected_boot_sequence'])+'\n','Counter changed since the guarded R35S shutdown')
    legacy.userdata_check(0o777,expected);guard.identity()
    fd=legacy.open_whole()
    try:
        capsules={n:legacy.capsule(fd,n) for n in (2,3)}
        for n,c in capsules.items():
            for key in ['sb','gd','sector']:core.write_new(stage/f'p{n}-{key}.bin',c[key])
        prefix=core.copy_region(fd,0,640*1024*1024,stage/'current-prefix.backup')
        need(core.region_sha(fd,0,640*1024*1024)==prefix,'Current prefix changed during snapshot')
        for n,c in capsules.items():need(legacy.capsule(fd,n)==c,'Capsule changed during snapshot')
    finally:os.close(fd)
    legacy.readonly_card();guard.identity()
    report={'passed':True,'schema':95,'operation':'protect-and-capture','context_sha256':core.sha(legacy.ROOT/'context.json'),
        'runtime_guard_sha256':ctx['runtime_guard_sha256'],'boot_sequence':ctx['expected_boot_sequence'],
        'current_prefix_sha256':prefix,'prefix_bytes':640*1024*1024,'attempt_sha256':ctx['attempt_sha256'],
        'root_modes':{'p2':0o777,'p3':0o777},'patches':{str(n):c['patch'] for n,c in capsules.items()},
        'historical_independent_backup_reverified':True,'userdata_matches_C82':True,'p2_fsck_exit':0,'p3_fsck_exit':0,
        'all_four_aliases_kernel_readonly':True,'runtime_guard_restored_or_reverified':True,
        'physical_payload_written':False,'media_unlocked':False,'seed_loaded_or_generated':False,'repair_applied':False,
        'source_sha256':{n:core.sha(legacy.ROOT/n) for n in sorted(SOURCES)}}
    core.write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());return report

def operation():
    root=Path(__file__).resolve().parent
    need(os.geteuid()==0 and re.fullmatch(r'/run/muos-r35s-c95\.[a-z0-9_]{8}',str(root)),'Protected Deck root snapshot required')
    s=root.lstat();need(s.st_uid==0 and stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==0o700,'Snapshot metadata')
    need(set(Path('/run').glob('muos-r35s-c*'))=={root},'Prior helper must be inspected')
    import phase4_backup_core as core,phase4_root_migration as policy,phase4_root_metadata as metadata
    ctx=json.loads((root/'context.json').read_text());validate_context(ctx,policy)
    guard=load('rearm_guard',root/'phase4-offline-backup.py');legacy=load('rearm_shared',root/'phase4-root-permissions.py')
    guard.core=core;guard.policy=policy;guard.ROOT=root
    guard.plan={n:ctx['legacy_context'][n] for n in ['mbr_sha256','boot_prefix_16MiB_sha256']}
    legacy.ROOT=root;legacy.core=core;legacy.policy=policy;legacy.metadata=metadata;legacy.guard=guard;legacy.ctx=ctx['legacy_context']
    libc=ctypes.CDLL(None,use_errno=True)
    need(libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0,'Private namespace required')
    need(os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'),'Namespace not isolated')
    guard.identity();parent=Path('/var/tmp');s=parent.lstat()
    need(s.st_uid==0 and stat.S_ISDIR(s.st_mode) and s.st_mode&stat.S_ISVTX,'Persistent sticky parent')
    row=legacy.run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN']).stdout.split()
    need(len(row)==2 and row[0] in ('ext4','btrfs') and row[1] not in guard.numbers(),'Persistent off-card snapshot')
    need(shutil.disk_usage(parent).free>=2*1024**3,'Need off-card snapshot space')
    stage=Path(tempfile.mkdtemp(prefix='muos-r35s-c95-protect.',dir=parent));stage.chmod(0o700);account=pwd.getpwnam('deck')
    try:
        print('C95_STEP=guard-readonly-and-current-preimage',flush=True);protect(stage,ctx,legacy,guard,core,policy)
        for p in stage.iterdir():p.chmod(0o400);os.chown(p,account.pw_uid,account.pw_gid)
        os.chown(stage,account.pw_uid,account.pw_gid);core.sync_dir(stage);core.sync_dir(parent)
        shutil.rmtree(root);print('C95 PROTECT COMPLETE '+str(stage),flush=True)
    except BaseException as error:
        info={'passed':False,'error_type':type(error).__name__,'reason':str(error),'traceback':traceback.format_exc(),
            'partial':str(stage),'snapshot':str(root),'no_automatic_retry':True}
        try:legacy.readonly_card();info['RO_reinforced']=True
        except BaseException:info['RO_reinforced']=False
        out=Path(tempfile.mkdtemp(prefix='muos-r35s-c95-failure.',dir=parent));out.chmod(0o700)
        core.write_new(out/'failure.json',(json.dumps(info,indent=2)+'\n').encode());(out/'failure.json').chmod(0o400)
        os.chown(out/'failure.json',account.pw_uid,account.pw_gid);os.chown(out,account.pw_uid,account.pw_gid)
        core.sync_dir(out);core.sync_dir(parent);print('C95 failure report '+str(out),file=sys.stderr,flush=True);raise

if __name__=='__main__':
    os.umask(0o077)
    def interrupted(signum,frame):raise SystemExit(128+signum)
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    try:
        need(len(sys.argv)==2 and sys.argv[1] in ('protect','_protect'),'Only protection and capture')
        bootstrap() if sys.argv[1]=='protect' else operation()
    except BaseException as error:
        print('C95 FAILED ('+type(error).__name__+'); keep card and private partials; no retry.',file=sys.stderr);sys.exit(1)
