#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C83 one-shot inspector / two-sector root mode repair; no formatter or RPC."""
from pathlib import Path
import ctypes,fcntl,hashlib,importlib.util,json,os,platform,pwd,re,shutil,signal,stat,struct,subprocess,sys,tempfile,uuid

BASE={'phase4-root-permissions.py','phase4_root_metadata.py','phase4_backup_core.py',
      'phase4_root_migration.py','phase4-offline-backup.py','context.json'}
ROOT=None;STAGE=None;mounted=False;write_started=False

def need(ok,message):
    if not ok:raise ValueError(message)

def bootstrap(action):
    need(os.geteuid()==0 and platform.machine()=='x86_64','Local Deck sudo required')
    need(Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),'Deck required')
    source=Path(__file__).resolve().parent;manifest=json.loads((source/'package.json').read_text())
    expected=BASE|({'repair-plan.json'} if action=='apply' else set())
    need(manifest['operation']==action and set(manifest['files'])==expected,'Operation package')
    root=Path(tempfile.mkdtemp(prefix='muos-r35s-c83.',dir='/run'));root.chmod(0o700)
    for name,h in manifest['files'].items():
        fd=os.open(source/name,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and 0<s.st_size<=1024*1024 and not s.st_mode&0o022,'Unsafe package leaf')
            data=os.read(fd,s.st_size+1);a=os.fstat(fd)
            need((s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns),'Package changed')
            need(len(data)==s.st_size and hashlib.sha256(data).hexdigest()==h,'Package hash')
            with (root/name).open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
            (root/name).chmod(0o400)
        finally:os.close(fd)
    os.execve('/usr/bin/python3',['/usr/bin/python3',str(root/'phase4-root-permissions.py'),'_'+action],
              {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})

def run(args):
    p=subprocess.run(args,capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=180,
                     env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C'})
    need(p.returncode==0,'Fixed host command failed: '+Path(args[0]).name);return p

def aliases():
    answer=[]
    for name in ['mmcblk0p1','mmcblk0p2','mmcblk0p3','mmcblk0']:
        major,minor=map(int,(guard.SYS/name/'dev').read_text().strip().split(':'))
        p=Path('/dev')/name;need(not p.is_symlink(),'Device symlink');answer.append((p,os.makedev(major,minor)))
    return answer

def open_whole(writable=False):
    guard.identity();core.flush_block_aliases(aliases());guard.identity()
    fd=os.open('/dev/mmcblk0',(os.O_RDWR if writable else os.O_RDONLY)|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        s=os.fstat(fd);need(stat.S_ISBLK(s.st_mode) and s.st_rdev==aliases()[-1][1],'Whole device identity')
        need(struct.unpack('Q',fcntl.ioctl(fd,0x80081272,bytes(8)))[0]==policy.CAPACITY*512,'Whole device capacity')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        mbr=core.read_exact(fd,512,0);policy.geometry(mbr)
        need(hashlib.sha256(mbr).hexdigest()==ctx['mbr_sha256'],'MBR changed')
        need(core.region_sha(fd,0,16*1024*1024)==ctx['boot_prefix_16MiB_sha256'],'Boot prefix changed')
        if writable:need(struct.unpack('i',fcntl.ioctl(fd,0x125e,bytes(4)))[0]==0,'Never clear existing kernel read-only protection')
        return fd
    except BaseException:os.close(fd);raise

def backup_check():
    backup=Path(ctx['deck_backup']);need(re.fullmatch(r'/var/tmp/muos-r35s-c81-backup\.[a-z0-9_]{8}',str(backup)),'Backup path')
    account=pwd.getpwnam('deck');s=backup.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==account.pw_uid and stat.S_IMODE(s.st_mode)==0o700,'Backup directory identity')
    need(ctx['host_copy_verified'] is True and ctx['metadata_repair_required_before_boot'] is True,'Independent backup required')
    need({p.name for p in backup.iterdir()}==set(ctx['backup_artifacts'])|{'backup.json'},'Backup inventory')
    for name,row in {**ctx['backup_artifacts'],'backup.json':{'sha256':ctx['backup_receipt_sha256']}}.items():
        need('/' not in name and name not in ('.','..'),'Backup leaf name')
        p=backup/name;s=p.lstat()
        need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==account.pw_uid and stat.S_IMODE(s.st_mode)==0o400,'Backup leaf identity')
        need(core.sha(p)==row['sha256'],'Backup leaf hash changed')
    receipt=json.loads((backup/'backup.json').read_text())
    need(receipt['passed'] is True and receipt['prefix_sha256']==ctx['prefix_before_sha256'] and receipt['boot_sequence']==72,'Backup receipt binding')
    return json.loads((backup/'userdata-manifest.json').read_text())['records']

def capsule(fd,number,expected_mode=0o40777):
    start,size=(128*1024*1024,512*1024*1024) if number==2 else (640*1024*1024,248561664*512)
    sb=core.read_exact(fd,1024,start+1024);gd=core.read_exact(fd,4096,start+4096)
    if number==3:
        need(sb[104:120]==uuid.UUID('6d756f73-c020-4000-8000-000000000001').bytes and sb[120:136]==b'MUOSDATA'+bytes(8),'Data UUID/label')
    layout=metadata.geometry(sb,gd,start,size);sector=core.read_exact(fd,512,layout['sector_offset'])
    patch=metadata.sector_patch(sb,gd,sector,start,size,expected_mode)
    return {'sb':sb,'gd':gd,'sector':sector,'patch':patch}

def userdata_check(mode,expected):
    global mounted
    need(not mounted,'Owned mount already active')
    mount=ROOT/'data';mount.mkdir(mode=0o700,exist_ok=True)
    guard.identity();run(['mount','-t','ext4','-o','ro,noload,nosuid,nodev,noexec','/dev/mmcblk0p3',str(mount)]);mounted=True
    try:
        guard.mount_check();need(core.userdata_snapshot(mount,source_root_mode=mode)[0]==expected,'Preferences/save bytes changed');guard.mount_check()
    finally:
        guard.mount_check();run(['umount',str(mount)]);mounted=False

def readonly_card():
    guard.identity()
    for path,device in aliases():
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            s=os.fstat(fd);need(stat.S_ISBLK(s.st_mode) and s.st_rdev==device,'Read-only alias identity')
            fcntl.ioctl(fd,0x125d,struct.pack('i',1)) # BLKROSET, kernel state only.
            need(struct.unpack('i',fcntl.ioctl(fd,0x125e,bytes(4)))[0]==1,'Read-only flag not set')
        finally:os.close(fd)

def automount_guard():
    source=Path('/usr/lib/udev/rules.d/99-holo-automount.rules');data=source.read_bytes()
    need(hashlib.sha256(data).hexdigest()==ctx['automount_rule_sha256'] and b'LABEL="holo_automount_end"' in data,'Automount rule changed')
    cid=(guard.SYS/'mmcblk0/device/cid').read_text().strip().lower();need(re.fullmatch('[0-9a-f]{32}',cid),'CID encoding')
    need(hashlib.sha256(cid.encode()).hexdigest()==policy.DECK_CID,'Guard CID')
    guarded=metadata.runtime_automount_rule(data,cid,policy.DECK_CID)
    parent=Path('/run/udev/rules.d');parent.mkdir(mode=0o755,exist_ok=True)
    info=parent.lstat();need(stat.S_ISDIR(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022,'Runtime rule directory')
    target=parent/source.name;core.write_new(target,guarded);target.chmod(0o644)
    try:
        run(['udevadm','verify',str(target)])
        run(['udevadm','control','--reload-rules']) # No trigger and no global service changes.
    except BaseException:
        if not target.is_symlink() and target.read_bytes()==guarded:
            target.unlink();core.sync_dir(parent)
            run(['udevadm','control','--reload-rules'])
        raise
    return hashlib.sha256(guarded).hexdigest()

def finish_report(value):
    core.write_new(STAGE/'analysis.json',(json.dumps(value,indent=2)+'\n').encode())
    account=pwd.getpwnam('deck')
    for p in STAGE.iterdir():p.chmod(0o400);os.chown(p,account.pw_uid,account.pw_gid)
    os.chown(STAGE,account.pw_uid,account.pw_gid);core.sync_dir(STAGE);core.sync_dir(STAGE.parent)
    print('C83 '+value['operation'].upper()+' COMPLETE '+str(STAGE),flush=True)

def operation(action):
    global ROOT,STAGE,core,metadata,policy,guard,ctx,write_started
    ROOT=Path(__file__).resolve().parent
    need(os.geteuid()==0 and re.fullmatch(r'/run/muos-r35s-c83\.[a-z0-9_]{8}',str(ROOT)),'Protected root snapshot required')
    s=ROOT.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'Root snapshot identity')
    sys.dont_write_bytecode=True
    import phase4_backup_core as core_module,phase4_root_metadata as metadata_module,phase4_root_migration as policy_module
    core=core_module;metadata=metadata_module;policy=policy_module
    spec=importlib.util.spec_from_file_location('backup_guard',ROOT/'phase4-offline-backup.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    ctx=json.loads((ROOT/'context.json').read_text());guard.core=core;guard.policy=policy;guard.ROOT=ROOT
    guard.plan={'mbr_sha256':ctx['mbr_sha256'],'boot_prefix_16MiB_sha256':ctx['boot_prefix_16MiB_sha256']}
    for tool in ['e2fsck','mount','umount','findmnt','udevadm']:need(shutil.which(tool),'Missing fixed host tool')
    libc=ctypes.CDLL(None,use_errno=True)
    need(libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0,'Mount isolation failed')
    need(os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'),'Private mount namespace required')
    guard.identity();expected_userdata=backup_check()
    for number in (2,3):run(['e2fsck','-fn','/dev/mmcblk0p'+str(number)]);guard.identity()
    parent=Path('/var/tmp');s=parent.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and bool(s.st_mode&stat.S_ISVTX),'Persistent stage parent')
    row=run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN']).stdout.split()
    need(len(row)==2 and row[0] in ('ext4','btrfs') and row[1] not in guard.numbers(),'Off-card persistent stage required')
    STAGE=Path(tempfile.mkdtemp(prefix='muos-r35s-c83-'+action+'.',dir=parent));STAGE.chmod(0o700)
    try:
        fd=open_whole()
        try:
            need(core.region_sha(fd,0,640*1024*1024)==ctx['prefix_before_sha256'],'Source prefix differs from C82')
            capsules={n:capsule(fd,n) for n in (2,3)}
            for n,c in capsules.items():
                for name in ['sb','gd','sector']:core.write_new(STAGE/('p'+str(n)+'-'+name+'.bin'),c[name])
        finally:os.close(fd)
        userdata_check(0o777,expected_userdata)
        result={'passed':True,'operation':action,'backup_verified':True,'host_copy_verified':True,'userdata_before_matches_C82':True,
                'context_sha256':core.sha(ROOT/'context.json'),'patches':{str(n):c['patch'] for n,c in capsules.items()},
                'device_written':False,'kernel_readonly':False,'reboot_requested':False,'seed_loaded':False}
        if action=='inspect':finish_report(result);return
        planned=json.loads((ROOT/'repair-plan.json').read_text())
        need(planned['context_sha256']==result['context_sha256'] and planned['host_capsule_copy_verified'] is True,'Plan/capsule host binding')
        need(planned['patches']==result['patches'],'Live patches differ from reviewed plan')
        result['automount_guard_sha256']=automount_guard();guard.identity()
        fd=open_whole(True)
        try:
            need(core.region_sha(fd,0,640*1024*1024)==ctx['prefix_before_sha256'],'Source changed immediately before repair')
            for n in (2,3):
                need(capsule(fd,n)['patch']==planned['patches'][str(n)],'Metadata changed immediately before repair')
            for n in (2,3):
                write_started=True
                metadata.apply_sector(fd,planned['patches'][str(n)],os.pread,os.pwrite,os.fsync)
            os.fsync(fd)
        finally:
            try:
                if write_started:readonly_card()
            finally:os.close(fd)
        fd=open_whole()
        try:
            need(core.region_sha(fd,0,640*1024*1024)==planned['prefix_after_sha256'],'Full protected prefix posthash')
            for n in (2,3):
                new=capsule(fd,n,0o40755)
                need(new['sector'].hex()==planned['patches'][str(n)]['after'],'Inode sector posthash')
                need(new['sb']==capsules[n]['sb'] and new['gd']==capsules[n]['gd'],'Superblock/group descriptor changed')
        finally:os.close(fd)
        for number in (2,3):run(['e2fsck','-fn','/dev/mmcblk0p'+str(number)]);guard.identity()
        userdata_check(0o755,expected_userdata);guard.identity()
        result.update({'device_written':True,'written_sectors':2,'kernel_readonly':True,'source_root_modes':{'p2':0o755,'p3':0o755},
             'prefix_after_sha256':planned['prefix_after_sha256'],'full_prefix_posthash_verified':True,
             'userdata_after_matches_C82':True,'p2_fsck_exit':0,'p3_fsck_exit':0,'no_superblock_or_GDT_changes':True})
        finish_report(result)
    finally:
        need(not mounted,'Own mount remains; keep snapshot')
        prefix=str(ROOT)+'/'
        need(not any(line.split()[4].startswith(prefix) for line in Path('/proc/self/mountinfo').read_text().splitlines()),'Mount below snapshot remains')
        shutil.rmtree(ROOT)

if __name__=='__main__':
    os.umask(0o077)
    def interrupted(signum,frame):raise SystemExit(128+signum)
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    try:
        need(len(sys.argv)==2 and sys.argv[1] in ('inspect','apply','_inspect','_apply'),'Only inspect/apply operations')
        if sys.argv[1].startswith('_'):operation(sys.argv[1][1:])
        else:bootstrap(sys.argv[1])
    except BaseException as error:
        print('C83 FAILED ('+type(error).__name__+'); retain card and partial stage for inspection. No automatic retry/rollback.',file=sys.stderr)
        sys.exit(1)
