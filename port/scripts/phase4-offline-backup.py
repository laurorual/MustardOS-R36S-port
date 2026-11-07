#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C81 one-shot Steam Deck backup. No socket, writer, formatter or restore."""
from pathlib import Path
import ctypes, errno, fcntl, hashlib, json, os, platform, pwd, re, shutil, signal, stat, struct, subprocess, sys, tempfile

SYS=Path('/sys/class/block');PROC=Path('/proc');DEVICE=Path('/dev/mmcblk0')
DMI=Path('/sys/class/dmi/id/product_name')
ALLOWED={'phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json'}
ROOT=None;STAGE=None;mounted=False

def need(ok,message):
    if not ok:raise RuntimeError(message)

def read(path):return path.read_text().strip()

def run(args):
    r=subprocess.run(args,capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=180,
                     env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C'})
    need(r.returncode==0,'Host tool failed: '+Path(args[0]).name)
    return r

def bootstrap():
    need(os.geteuid()==0 and len(sys.argv)==2 and sys.argv[1]=='backup','Run locally with sudo and backup only')
    need(platform.machine()=='x86_64' and read(DMI) in ('Jupiter','Galileo'),'Expected Steam Deck')
    source=Path(__file__).resolve().parent
    manifest=json.loads((source/'package.json').read_text())
    need(manifest['qualified_backup_only'] is True and set(manifest['files'])==ALLOWED,'Unexpected package')
    root=Path(tempfile.mkdtemp(prefix='muos-r35s-c81.',dir='/run'));root.chmod(0o700)
    for name,wanted in manifest['files'].items():
        fd=os.open(source/name,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            before=os.fstat(fd)
            need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=1024*1024 and not before.st_mode&0o022,'Unsafe package leaf')
            data=os.read(fd,before.st_size+1);after=os.fstat(fd)
            need((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Package changed')
            need(len(data)==before.st_size and hashlib.sha256(data).hexdigest()==wanted,'Package hash')
            with (root/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            (root/name).chmod(0o400)
        finally:os.close(fd)
    if 'source_root_policy' in manifest:
        # This metadata is sealed with the reviewed payload, never read from RPC.
        value=manifest['source_root_policy']
        need(type(value) is dict and set(value)=={'reason','p2_mode','p3_mode','automount_script_sha256','diagnostic_root_sha256'},'Source policy schema')
        need(value['reason']=='SteamOS_automount_chmod777' and type(value['p2_mode']) is int and type(value['p3_mode']) is int and value['p2_mode']==value['p3_mode']==0o777,'Source policy scope')
        need(all(type(value[k]) is str and re.fullmatch('[0-9a-f]{64}',value[k]) for k in ['automount_script_sha256','diagnostic_root_sha256']),'Source policy hashes')
        with (root/'source-root-policy.json').open('xb') as f:
            f.write((json.dumps(value,sort_keys=True)+'\n').encode());f.flush();os.fsync(f.fileno())
        (root/'source-root-policy.json').chmod(0o400)
    os.execve('/usr/bin/python3',['/usr/bin/python3',str(root/'phase4-offline-backup.py'),'_snapshot'],
              {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})

def numbers():
    return {read(p/'dev') for p in [SYS/'mmcblk0',*(SYS.glob('mmcblk0p*'))] if (p/'dev').is_file()}

def idle(owned=None):
    nums=numbers()
    for info in PROC.glob('[0-9]*/mountinfo'):
        try:lines=info.read_text().splitlines()
        except OSError as e:
            if e.errno in (errno.ENOENT,errno.ESRCH,errno.EINVAL):continue
            raise
        for line in lines:
            fields=line.split();need(len(fields)>=10,'Malformed mountinfo')
            if fields[2] not in nums:continue
            permitted=owned is not None and fields[2]==read(SYS/'mmcblk0p3/dev') and fields[4]==str(owned)
            if permitted:
                permitted=os.readlink(info.parent/'ns/mnt')==os.readlink(PROC/'self/ns/mnt') and 'ro' in fields[5].split(',')
            need(permitted,'Card mounted; no automatic unmount')
    for line in (PROC/'swaps').read_text().splitlines()[1:]:
        p=Path(line.split()[0]);s=p.stat();dev=s.st_rdev if stat.S_ISBLK(s.st_mode) else s.st_dev
        need(f'{os.major(dev)}:{os.minor(dev)}' not in nums,'Card swap')
    for p in [SYS/'mmcblk0',*(SYS.glob('mmcblk0p*'))]:need(not list((p/'holders').iterdir()),'Card holder')

def identity(owned=None):
    need(platform.machine()=='x86_64' and read(DMI) in ('Jupiter','Galileo'),'Wrong offline host')
    cards=[]
    for p in sorted(SYS.glob('mmcblk*')):
        if not (p/'device/cid').is_file():continue
        value=hashlib.sha256(read(p/'device/cid').lower().encode()).hexdigest()
        need(value!=policy.ORIGINAL_CID,'Original32 present')
        cards.append((p.name,value))
    need(cards==[('mmcblk0',policy.DECK_CID)],'Expected only exact test128 reader alias')
    need(read(SYS/'mmcblk0/size')==str(policy.CAPACITY) and read(SYS/'mmcblk0/queue/logical_block_size')=='512','Capacity/sector')
    need({p.name for p in SYS.glob('mmcblk0p*')}=={'mmcblk0p1','mmcblk0p2','mmcblk0p3'},'Partition set')
    for n,start,size in [(1,32768,204800),(2,262144,1048576),(3,1310720,248561664)]:
        p=SYS/f'mmcblk0p{n}'
        need(read(p/'start')==str(start) and read(p/'size')==str(size),'Partition geometry')
    idle(owned)

def open_card():
    identity()
    aliases=[]
    for name in ['mmcblk0p1','mmcblk0p2','mmcblk0p3','mmcblk0']:
        p=Path('/dev')/name;need(not p.is_symlink(),'Device alias')
        major,minor=map(int,read(SYS/name/'dev').split(':'));aliases.append((p,os.makedev(major,minor)))
    core.flush_block_aliases(aliases);identity()
    fd=os.open(DEVICE,os.O_RDONLY|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        s=os.fstat(fd);need(stat.S_ISBLK(s.st_mode) and f'{os.major(s.st_rdev)}:{os.minor(s.st_rdev)}'==read(SYS/'mmcblk0/dev'),'Device opened identity')
        need(struct.unpack('Q',fcntl.ioctl(fd,0x80081272,bytes(8)))[0]==policy.CAPACITY*512,'Device bytes')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        mbr=core.read_exact(fd,512,0);policy.geometry(mbr)
        need(hashlib.sha256(mbr).hexdigest()==plan['mbr_sha256'],'Live/offline MBR changed')
        need(core.region_sha(fd,0,16*1024*1024)==plan['boot_prefix_16MiB_sha256'],'Boot prefix changed')
        return fd
    except BaseException:os.close(fd);raise

def mount_check():
    mount=ROOT/'data'
    row=run(['findmnt','-rn','-M',str(mount),'-o','SOURCE,FSTYPE,MAJ:MIN,OPTIONS']).stdout.split()
    need(len(row)==4 and row[:3]==['/dev/mmcblk0p3','ext4',read(SYS/'mmcblk0p3/dev')],'Unowned data mount')
    options=set(row[3].split(','))
    need({'ro','nosuid','nodev','noexec'}<=options and bool({'noload','norecovery'}&options),'Unsafe data mount')
    identity(mount)

def unmount_owned():
    global mounted
    if mounted:
        mount_check();run(['umount',str(ROOT/'data')]);mounted=False

def snapshot():
    global ROOT,STAGE,mounted,core,policy,plan
    ROOT=Path(__file__).resolve().parent
    need(os.geteuid()==0 and re.fullmatch(r'/run/muos-r35s-c81\.[a-z0-9_]{8}',str(ROOT)),'Root snapshot only')
    s=ROOT.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'Snapshot identity')
    sys.dont_write_bytecode=True
    import phase4_backup_core as core_module
    import phase4_root_migration as policy_module
    core=core_module;policy=policy_module
    p2_mode=p3_mode=0o755;source_policy=None
    if (ROOT/'source-root-policy.json').exists():
        leaf=ROOT/'source-root-policy.json';info=leaf.lstat()
        need(stat.S_ISREG(info.st_mode) and info.st_uid==0 and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==0o400,'Sealed source policy')
        source_policy=core.validate_source_root_policy(json.loads(leaf.read_text()))
        need(core.sha(Path('/usr/lib/hwsupport/steamos-automount.sh'))==source_policy['automount_script_sha256'],'Automount implementation changed')
        p2_mode=source_policy['p2_mode'];p3_mode=source_policy['p3_mode']
    plan=json.loads((ROOT/'migration-plan.json').read_text())
    need(plan['experiment']=='C80_ROOT_ONLY_MIGRATION_PLAN' and plan['execution_enabled'] is False and plan['device_writer_available'] is False,'Plan policy')
    need(plan['capacity_sectors']==policy.CAPACITY and plan['prefix_backup_bytes']==policy.PREFIX_BYTES,'Plan geometry')
    need(plan['offline_reader_cid_sha256']==policy.DECK_CID and plan['proposed_write']=={'partition':2,'offset':policy.ROOT_OFFSET,'bytes':policy.ROOT_BYTES},'Plan target')
    for tool in ['debugfs','e2fsck','fsck.fat','blkid','mount','umount','findmnt']:need(shutil.which(tool),'Missing host tool')
    account=pwd.getpwnam('deck')
    libc=ctypes.CDLL(None,use_errno=True)
    need(libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0,'Mount isolation failed')
    need(os.readlink(PROC/'self/ns/mnt')!=os.readlink(PROC/'1/ns/mnt'),'Private namespace absent')
    identity()
    # /var/tmp is sticky and root owns this unpredictable stage until completion.
    parent=Path('/var/tmp');s=parent.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and bool(s.st_mode&stat.S_ISVTX),'Unsafe backup parent')
    fs=run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN']).stdout.split()
    need(len(fs)==2 and fs[0] in ('ext4','btrfs') and fs[1] not in numbers(),'Backup must be persistent off-card storage')
    v=os.statvfs(parent);need(v.f_bavail*v.f_frsize>=3*1024**3,'Need 3GiB backup space')
    STAGE=Path(tempfile.mkdtemp(prefix='muos-r35s-c81-backup.',dir=parent));STAGE.chmod(0o700)
    try:
        fd=open_card()
        try:prefix_sha=core.copy_region(fd,0,policy.PREFIX_BYTES,STAGE/'prefix.backup')
        finally:os.close(fd)
        fd=os.open(STAGE/'prefix.backup',os.O_RDONLY|os.O_NOFOLLOW)
        try:
            core.copy_region(fd,16*1024*1024,100*1024*1024,STAGE/'boot.fat')
            core.copy_region(fd,policy.ROOT_OFFSET,policy.ROOT_BYTES,STAGE/'root.ext4')
        finally:os.close(fd)
        run(['fsck.fat','-n',str(STAGE/'boot.fat')]);run(['e2fsck','-fn',str(STAGE/'root.ext4')])
        if source_policy:
            need(core.sha(STAGE/'root.ext4')==source_policy['diagnostic_root_sha256'],'Root changed after diagnostic')
        private=core.extract_private(STAGE/'root.ext4',STAGE,plan,run,source_root_mode=p2_mode)
        core.write_new(STAGE/'private-files.json',(json.dumps(private,indent=2)+'\n').encode())
        identity()
        probe=run(['blkid','-p','-o','export','/dev/mmcblk0p3']).stdout
        values=dict(line.split('=',1) for line in probe.splitlines())
        need(values.get('TYPE')=='ext4' and values.get('LABEL')=='MUOSDATA' and values.get('UUID')=='6d756f73-c020-4000-8000-000000000001','Data FS identity')
        run(['e2fsck','-fn','/dev/mmcblk0p3']);identity()
        (ROOT/'data').mkdir(mode=0o700)
        run(['mount','-t','ext4','-o','ro,noload,nosuid,nodev,noexec','/dev/mmcblk0p3',str(ROOT/'data')]);mounted=True
        mount_check()
        try:userdata=core.backup_userdata(ROOT/'data',STAGE/'userdata.tar',source_root_mode=p3_mode);mount_check()
        finally:unmount_owned()
        core.write_new(STAGE/'userdata-manifest.json',(json.dumps(userdata,indent=2)+'\n').encode())
        fd=open_card()
        try:need(core.region_sha(fd,0,policy.PREFIX_BYTES)==prefix_sha,'Card prefix changed during backup')
        finally:os.close(fd)
        artifacts={p.name:{'sha256':core.sha(p),'bytes':p.stat().st_size} for p in STAGE.iterdir()}
        receipt={'passed':True,'experiment':'C81_OFFLINE_BACKUP_ONLY','plan_sha256':core.sha(ROOT/'migration-plan.json'),
          'boot_sequence':plan['survey_boot_sequence'],'prefix_sha256':prefix_sha,'artifacts':artifacts,
          'all_namespaces_checked':True,'alias_cache_synchronized':True,'fat_fsck_exit':0,'root_fsck_exit':0,'data_fsck_exit':0,
          'private_state_from_fresh_backup':True,'userdata_archive_verified':True,'p3_unmounted':True,
          'independent_host_copy_verified':False,'device_payload_writer_available':False,
          'device_format_or_restore_available':False,'candidate_provisioned':False,'seed_loaded':False,'reboot_requested':False}
        receipt.update({'source_root_modes':{'p2':p2_mode,'p3':p3_mode},'metadata_repair_required_before_boot':source_policy is not None,
            'source_root_policy_sha256':core.sha(ROOT/'source-root-policy.json') if source_policy else None})
        core.write_new(STAGE/'backup.json',(json.dumps(receipt,indent=2)+'\n').encode())
        for p in STAGE.iterdir():p.chmod(0o400);os.chown(p,account.pw_uid,account.pw_gid)
        os.chown(STAGE,account.pw_uid,account.pw_gid);core.sync_dir(STAGE);core.sync_dir(STAGE.parent)
        print('C81 BACKUP COMPLETE '+str(STAGE),flush=True)
        print('Independent host copy is still required. No media writer is present.',flush=True)
    finally:
        unmount_owned()
        # Refuse recursive removal if any mount remains below the snapshot.
        prefix=str(ROOT)+'/'
        need(not any(line.split()[4].startswith(prefix) for line in (PROC/'self/mountinfo').read_text().splitlines()),'Snapshot mount remains; retain root-owned files')
        shutil.rmtree(ROOT)

if __name__=='__main__':
    os.umask(0o077)
    def interrupted(signum,frame):raise SystemExit(128+signum)
    for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,interrupted)
    try:
        if len(sys.argv)==2 and sys.argv[1]=='_snapshot':snapshot()
        else:bootstrap()
    except BaseException as error:
        if isinstance(error,SystemExit) and error.code==0:raise
        print('C81 FAILED ('+type(error).__name__+'); no usable completion may be assumed. Inspect partial backup/snapshot.',file=sys.stderr)
        sys.exit(1)
