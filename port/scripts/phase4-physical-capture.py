#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C86 one-shot physical p2 capture; only O_RDONLY media IO and SETRO=1."""
from pathlib import Path
import ctypes,fcntl,hashlib,importlib.util,json,os,platform,pwd,re,shutil,signal,stat,struct,sys,tempfile

SOURCES={'phase4-physical-capture.py','phase4_backup_core.py','phase4_root_migration.py',
    'phase4-offline-backup.py','phase4_root_recovery.py','phase4_recovery_image.py','context.json'}
ROOT=None;STAGE=None

def need(ok,message):
    if not ok:raise ValueError(message)

def bootstrap(action):
    need(os.geteuid()==0 and platform.machine()=='x86_64','Local Deck sudo required')
    need(Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),'Deck required')
    source=Path(__file__).resolve().parent;package=json.loads((source/'package.json').read_text())
    expected=SOURCES|({'attempt.json'} if action=='postboot' else set())
    need(package['operation']==action and set(package['files'])==expected,'Capture package schema')
    root=Path(tempfile.mkdtemp(prefix='muos-r35s-c86.',dir='/run'));root.chmod(0o700)
    for name,h in package['files'].items():
        fd=os.open(source/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            before=os.fstat(fd)
            need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=1024*1024 and not before.st_mode&0o022,'Unsafe source leaf')
            data=os.read(fd,before.st_size+1);after=os.fstat(fd)
            need((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Source changed')
            need(len(data)==before.st_size and hashlib.sha256(data).hexdigest()==h,'Source hash')
            with (root/name).open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
            (root/name).chmod(0o400)
        finally:os.close(fd)
    os.execve('/usr/bin/python3',['/usr/bin/python3',str(root/'phase4-physical-capture.py'),'_'+action],
        {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})

def read_protection(guard,context):
    guard.identity()
    rule=Path('/run/udev/rules.d/99-holo-automount.rules');s=rule.lstat()
    need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o644,'Targeted automount guard missing')
    need(hashlib.sha256(rule.read_bytes()).hexdigest()==context['automount_guard_sha256'],'Automount guard changed')

def protect_aliases(guard,policy,context):
    """SETRO=1 only, after identity and before any cache flush or payload read."""
    read_protection(guard,context)
    for name in ['mmcblk0p1','mmcblk0p2','mmcblk0p3','mmcblk0']:
        guard.identity();path=Path('/dev')/name;need(not path.is_symlink(),'Alias symlink')
        dev=tuple(map(int,(guard.SYS/name/'dev').read_text().strip().split(':')))
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            s=os.fstat(fd);need(stat.S_ISBLK(s.st_mode) and s.st_rdev==os.makedev(*dev),'Alias identity')
            fcntl.ioctl(fd,0x125d,struct.pack('i',1))
            need(struct.unpack('i',fcntl.ioctl(fd,0x125e,bytes(4)))[0]==1,'Alias kernel RO not active')
        finally:os.close(fd)
    read_protection(guard,context)

def verify_ro(guard,fd):
    guard.identity()
    need(struct.unpack('i',fcntl.ioctl(fd,0x125e,bytes(4)))[0]==1,'Whole device lost RO')
    need(all((guard.SYS/name/'ro').read_text().strip()=='1' for name in
        ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']),'An alias lost kernel RO')

def validate_context(context,action,policy,recovery):
    need(action in ('reference','postboot'),'Finite capture mode')
    keys={'schema','operation','mbr_sha256','boot_prefix_16MiB_sha256','automount_guard_sha256',
        'backup_private_files','backup_counter','backup_prefix_sha256','reference_root_sha256'}
    need(type(context) is dict and set(context)==(keys|({'attempt_sha256'} if action=='postboot' else set())),'Capture context schema')
    need(context['schema']==86 and context['operation']==action,'Capture operation binding')
    for n in keys-{'schema','operation','backup_private_files','backup_counter'}:policy.digest(context[n])
    if action=='postboot':policy.digest(context['attempt_sha256'])
    recovery.manifest(context['backup_private_files'],context['backup_counter'],True)

def capture(guard,core,policy,recovery,image,context,action,stage,attempt=None):
    """Derive a C85 receipt from guarded physical IO; no caller-supplied receipt."""
    validate_context(context,action,policy,recovery)
    if action=='postboot':
        need(attempt is not None and recovery.hashed(recovery.encoded(attempt))==context['attempt_sha256'],'Sealed intent required')
        recovery.checked_attempt(attempt,context['backup_private_files'],context['backup_counter'],context['backup_prefix_sha256'])
    else:need(attempt is None,'Reference cannot carry handoff intent')
    protect_aliases(guard,policy,context)
    fd=guard.open_card() # C82: exact geometry, O_RDONLY|O_EXCL, flush identified aliases.
    try:
        verify_ro(guard,fd)
        root_hash=core.copy_region(fd,policy.ROOT_OFFSET,policy.ROOT_BYTES,stage/'root.ext4')
        verify_ro(guard,fd)
        if action=='reference':need(root_hash==context['reference_root_sha256'],'Reference changed since C83 repair')
        with image.source_image(stage/'root.ext4',root_hash,policy.ROOT_BYTES) as snapshot:
            scanned=image.scan(snapshot,stage)
        observed=None;capture_context=None
        if action=='reference':
            need(scanned['private_files']==context['backup_private_files'] and scanned['boot_sequence']==context['backup_counter'],'Reference private state changed')
        else:
            capture_context={'schema':85,'attempt_id':attempt['attempt_id'],'attempt_sha256':context['attempt_sha256'],
                'root_sha256':root_hash,'root_bytes':policy.ROOT_BYTES,'cid_sha256':policy.DECK_CID,
                'capacity_sectors':policy.CAPACITY,'offline':True,'all_namespaces_unmounted':True,
                'alias_cache_synchronized':True,'captured_after_handoff':True}
            observed=image.observation(scanned,attempt,capture_context,root_hash,policy.ROOT_BYTES)
            recovery.recovery_plan(context['backup_private_files'],context['backup_counter'],context['backup_prefix_sha256'],attempt,observed)
        verify_ro(guard,fd)
        need(core.region_sha(fd,policy.ROOT_OFFSET,policy.ROOT_BYTES)==root_hash,'Source p2 changed after scan')
        mbr=core.read_exact(fd,512,0);policy.geometry(mbr)
        need(hashlib.sha256(mbr).hexdigest()==context['mbr_sha256'] and
            core.region_sha(fd,0,16*1024*1024)==context['boot_prefix_16MiB_sha256'],'Boot prefix changed during capture')
        verify_ro(guard,fd);read_protection(guard,context)
    finally:os.close(fd)
    result={'passed':True,'schema':86,'operation':action,'root_sha256':root_hash,'root_bytes':policy.ROOT_BYTES,
        'context_sha256':recovery.hashed(recovery.encoded(context)),'root_fsck_exit':0,
        'boot_sequence':scanned['boot_sequence'],'private_file_count':len(scanned['private_files']),
        'tree_entry_count':len(scanned['tree']),'all_namespaces_unmounted':True,'alias_cache_synchronized':True,
        'all_four_aliases_kernel_readonly':True,'source_p2_double_read_verified':True,
        'MBR_and_16MiB_boot_prefix_preserved':True,'root_snapshot_matches_physical_p2':True,
        'physical_postboot_capture':action=='postboot','handoff_intent_checked':action=='postboot',
        'device_payload_written':False,'device_writer_available':False,'seed_generated_or_loaded':False,
        'reboot_requested':False,'userdata_mounted_or_copied':False}
    core.write_new(stage/'tree.json',(json.dumps(scanned['tree'],indent=2)+'\n').encode())
    core.write_new(stage/'private-files.json',(json.dumps(scanned['private_files'],indent=2)+'\n').encode())
    if observed is not None:
        core.write_new(stage/'capture-context.json',(json.dumps(capture_context,indent=2)+'\n').encode())
        core.write_new(stage/'observation.json',(json.dumps(observed,indent=2)+'\n').encode())
    return result

def operation(action):
    global ROOT,STAGE
    ROOT=Path(__file__).resolve().parent
    need(os.geteuid()==0 and re.fullmatch(r'/run/muos-r35s-c86\.[a-z0-9_]{8}',str(ROOT)),'Protected root snapshot required')
    s=ROOT.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'Root snapshot identity')
    import phase4_backup_core as core,phase4_root_migration as policy,phase4_root_recovery as recovery,phase4_recovery_image as image
    spec=importlib.util.spec_from_file_location('capture_guard',ROOT/'phase4-offline-backup.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    context=json.loads((ROOT/'context.json').read_text());validate_context(context,action,policy,recovery)
    guard.core=core;guard.policy=policy;guard.ROOT=ROOT;guard.plan=context
    for tool in ['e2fsck','debugfs','findmnt']:need(shutil.which(tool),'Missing fixed host tool')
    libc=ctypes.CDLL(None,use_errno=True)
    need(libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0,'Private mount namespace required')
    need(os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'),'Namespace not isolated')
    guard.identity()
    parent=Path('/var/tmp');s=parent.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and bool(s.st_mode&stat.S_ISVTX),'Persistent stage parent')
    row=guard.run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN']).stdout.split()
    need(len(row)==2 and row[0] in ('ext4','btrfs') and row[1] not in guard.numbers(),'Off-card persistent destination required')
    space=os.statvfs(parent);need(space.f_bavail*space.f_frsize>=2*1024**3,'Need 2GiB off-card space')
    attempt=None
    if action=='postboot':
        # Bootstrap sealed this exact host-journal leaf by hash in root0400.
        leaf=ROOT/'attempt.json';s=leaf.lstat()
        need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o400,'Sealed intent leaf')
        raw=leaf.read_bytes();attempt=json.loads(raw)
        need(recovery.encoded(attempt)==raw and recovery.hashed(raw)==context['attempt_sha256'],'Intent canonical encoding/hash')
    STAGE=Path(tempfile.mkdtemp(prefix='muos-r35s-c86-capture.',dir=parent));STAGE.chmod(0o700)
    try:
        report=capture(guard,core,policy,recovery,image,context,action,STAGE,attempt)
        report['snapshot_source_sha256']={name:core.sha(ROOT/name) for name in sorted(SOURCES)}
        report['artifacts']={p.name:{'sha256':core.sha(p),'bytes':p.stat().st_size} for p in STAGE.iterdir()}
        core.write_new(STAGE/'analysis.json',(json.dumps(report,indent=2)+'\n').encode())
        account=pwd.getpwnam('deck')
        for p in STAGE.iterdir():p.chmod(0o400);os.chown(p,account.pw_uid,account.pw_gid)
        os.chown(STAGE,account.pw_uid,account.pw_gid);core.sync_dir(STAGE);core.sync_dir(STAGE.parent)
        print('C86 CAPTURE COMPLETE '+str(STAGE),flush=True)
    finally:
        prefix=str(ROOT)+'/'
        need(not any(line.split()[4].startswith(prefix) for line in Path('/proc/self/mountinfo').read_text().splitlines()),'Mount below snapshot remains')
        shutil.rmtree(ROOT)

if __name__=='__main__':
    os.umask(0o077)
    def interrupted(signum,frame):raise SystemExit(128+signum)
    for sig in [signal.SIGINT,signal.SIGTERM]:signal.signal(sig,interrupted)
    try:
        need(len(sys.argv)==2 and sys.argv[1] in ('reference','postboot','_reference','_postboot'),'Only finite reference/postboot captures')
        if sys.argv[1].startswith('_'):operation(sys.argv[1][1:])
        else:bootstrap(sys.argv[1])
    except BaseException as error:
        print('C86 FAILED ('+type(error).__name__+'); keep card/RO and private partial stage. No automatic retry or rollback.',file=sys.stderr);sys.exit(1)
