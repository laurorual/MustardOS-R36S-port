#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Finite, temporary Steam Deck root helper for the identified test128 only.

Start locally in Konsole with sudo. No sudoers/SSH policy changes, shell RPC,
package installation or arbitrary device/path/command arguments are accepted.
The deck UID can request inspect/backup/ack-backup/partition/format/verify/
restore/stop over one local socket. The original32 is always disqualifying.
"""
from pathlib import Path
import ctypes,errno,fcntl,hashlib,importlib.util,json,os,platform,pwd,re,shutil,socket,stat,struct,subprocess,sys,time

SOCKET='/run/muos-r35s-c20.sock'
ROOT=Path('/run/muos-r35s-c20-root')
BACKUP=Path('/home/deck/muos-r35s-c20-private')
DEVICE=Path('/dev/mmcblk0')
SYS=Path('/sys/class/block/mmcblk0')
SYS_BLOCK=Path('/sys/class/block')
PROC=Path('/proc')
DMI=Path('/sys/class/dmi/id/product_name')
# Exact reader-specific alias, not a generalized truncated-CID match. SDHCI on
# this Deck reports final CID byte00; the R35S DW-MMC reports7d. The other15 bytes
# reconstruct the exact previously pinned R35S hash. MBR+prefix remain required.
DECK_TEST_CID='ddf407810b45ae7713ff682a9bb08985a725defe1d007455cd44b4187c39ee04'
FEATURES={'has_journal','ext_attr','resize_inode','dir_index','filetype','extent',
          'sparse_super','large_file','uninit_bg','dir_nlink','extra_isize'}
state={'acked':False,'partitioned':False,'formatted':False,'mounted':False,'root_mode_repaired':False}
io=layout=plan=before=after=None

def require(condition,message):
    if not condition:raise RuntimeError(message)
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return path.read_text().strip()
def run(args,*,timeout=60,log=None,allowed=(0,)):
    result=subprocess.run(args,text=True,capture_output=True,stdin=subprocess.DEVNULL,timeout=timeout,env={
        'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','HOME':'/root'})
    if log is not None:
        fd=os.open(BACKUP/log,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as f:f.write(result.stdout+result.stderr);f.flush();os.fsync(f.fileno())
        os.chown(BACKUP/log,deck_uid,deck_gid);os.chmod(BACKUP/log,0o400)
    require(result.returncode in allowed,'Command failed: '+args[0]+' rc='+str(result.returncode))
    return result
def sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
def write_new(path,data,mode=0o600):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def load_module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def device_numbers():
    return {read(p/'dev') for p in [SYS,*SYS.glob('mmcblk0p*')] if (p/'dev').is_file()}
def idle_card():
    numbers=device_numbers();busy=[]
    for info in PROC.glob('[0-9]*/mountinfo'):
        try:lines=info.read_text().splitlines()
        except OSError as error:
            # Exited tasks and kernel threads have no readable mount namespace.
            # EACCES, EIO and other errors still abort this preflight.
            if error.errno in (errno.ENOENT,errno.ESRCH,errno.EINVAL):continue
            raise
        for line in lines:
            fields=line.split()
            if len(fields)>4 and fields[2] in numbers:busy.append(fields[4])
    require(not busy,'Card has mounted children; no automatic unmount: '+repr(sorted(set(busy))))
    for line in (PROC/'swaps').read_text().splitlines()[1:]:
        p=Path(line.split()[0]);s=p.stat()
        dev=s.st_rdev if stat.S_ISBLK(s.st_mode) else s.st_dev
        require(f'{os.major(dev)}:{os.minor(dev)}' not in numbers,'Card is used by swap')
    for p in [SYS,*SYS.glob('mmcblk0p*')]:
        require(not list((p/'holders').iterdir()),'Card has block holders: '+p.name)
def identity():
    require(platform.machine()=='x86_64','Expected x86_64 offline station')
    require(read(DMI) in ('Jupiter','Galileo'),'Expected Steam Deck')
    selected=[];cards=[]
    for p in SYS_BLOCK.glob('mmcblk*'):
        if not (p/'device/cid').is_file():continue
        cards.append(p.name)
        digest=hashlib.sha256(read(p/'device/cid').lower().encode()).hexdigest()
        require(digest!=plan['protected_original_card_cid_sha256'],'Protected original32 is present')
        if digest in (plan['test_card_cid_sha256'],DECK_TEST_CID):selected.append(p.name)
    require(cards==['mmcblk0'] and selected==['mmcblk0'],'Expected only the test128 in the built-in reader')
    require(read(SYS/'size')==str(plan['capacity_sectors_512']),'Card capacity changed')
    require(read(SYS/'queue/logical_block_size')=='512','Unexpected logical sector size')
    require(not DEVICE.is_symlink(),'Refusing device symlink')
    idle_card()
def open_card(writable=False,allow_after=False):
    identity()
    aliases=[]
    for name in ['mmcblk0p1','mmcblk0p2','mmcblk0p3','mmcblk0']:
        if not (SYS_BLOCK/name).exists():continue
        maj,minr=map(int,read(SYS_BLOCK/name/'dev').split(':'))
        aliases.append((Path('/dev')/name,os.makedev(maj,minr)))
    io.flush_block_aliases(aliases)
    identity()
    fd=os.open(DEVICE,(os.O_RDWR if writable else os.O_RDONLY)|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        s=os.fstat(fd)
        require(stat.S_ISBLK(s.st_mode) and f'{os.major(s.st_rdev)}:{os.minor(s.st_rdev)}'==read(SYS/'dev'),'Device identity changed')
        require(struct.unpack('Q',fcntl.ioctl(fd,0x80081272,bytes(8)))[0]==plan['capacity_sectors_512']*512,'Block size mismatch')
        mbr=io.read_exact(fd,512)
        require(mbr==before or (allow_after and mbr==after),'Unexpected complete MBR')
        require(io.canonical_prefix_sha256(fd,16*1024*1024,before)==plan['boot_prefix_16MiB_sha256'],'Boot prefix mismatch')
        return fd
    except BaseException:os.close(fd);raise
def geometry():
    for index,start,size in [(1,32768,204800),(2,262144,1048576),(3,plan['new_partition']['start_sector'],plan['new_partition']['sectors'])]:
        path=SYS_BLOCK/f'mmcblk0p{index}'
        require(read(path/'start')==str(start) and read(path/'size')==str(size),'Partition geometry mismatch')
def backup_check():
    require(state['acked'],'Independent host backup must be verified/acknowledged first')
    require(sha(BACKUP/'prefix.backup')==state['backup_sha256'],'Backup changed')
def protected_check(fd):
    expected=state.get('protected_after_mode_repair_sha256',state['backup_sha256'])
    require(io.canonical_prefix_sha256(fd,plan['offline_prefix_backup_bytes'],before)==expected,'Protected640MiB differs from verified baseline')
def empty_partition_probe(output,returncode,parent_dev):
    """blkid success may describe only the containing partition, with no FS."""
    require(returncode in (0,2),'Ambiguous or failed filesystem probe')
    values={}
    for line in output.splitlines():
        require('=' in line and '\x00' not in line,'Malformed probe output')
        key,value=line.split('=',1)
        require(key not in values,'Duplicate probe field');values[key]=value
    if returncode==2:
        require(not values,'Unsuccessful probe unexpectedly returned metadata');return values
    expected={'DEVNAME':'/dev/mmcblk0p3','PART_ENTRY_SCHEME':'dos',
              'PART_ENTRY_UUID':plan['new_partition']['partuuid'],'PART_ENTRY_TYPE':'0x83',
              'PART_ENTRY_NUMBER':'3','PART_ENTRY_OFFSET':str(plan['new_partition']['start_sector']),
              'PART_ENTRY_SIZE':str(plan['new_partition']['sectors']),'PART_ENTRY_DISK':parent_dev}
    require(set(expected)<=set(values) and set(values)<=set(expected)|{'PART_ENTRY_FLAGS'},
            'Existing filesystem, nested partition table, unknown or incomplete probe metadata')
    require(all(values[key]==value for key,value in expected.items()),'Partition probe disagrees with plan')
    require(values.get('PART_ENTRY_FLAGS','0x0')=='0x0','Unexpected partition flags')
    return values
def reread(fd):
    fcntl.ioctl(fd,0x125f) # BLKRRPART, only on an idle offline device.
    run(['udevadm','settle'],timeout=30)
def inspect():
    result=run([sys.executable,str(ROOT/'inspect-phase4-userdata-offline.py')])
    report=json.loads(result.stdout)
    report['helper_state']={k:v for k,v in state.items() if k!='backup_sha256'}
    if any(c['test_card'] for c in report['cards']):
        try:
            fd=open_card(allow_after=True)
            try:
                report['mbr_phase']='p3-applied' if io.read_exact(fd,512)==after else 'original'
                if report['mbr_phase']=='p3-applied':
                    geometry();probe=run(['blkid','-p','-o','export','/dev/mmcblk0p3'],allowed=(0,2))
                    report['data_probe']={'exit':probe.returncode,'export':probe.stdout}
                    try:
                        empty_partition_probe(probe.stdout,probe.returncode,read(SYS/'dev'))
                        report['data_probe']['classification']='empty-filesystem-with-expected-partition-metadata'
                    except RuntimeError as error:report['data_probe']['classification']=str(error)
            finally:os.close(fd)
        except Exception as error:report['raw_inspection_error']=type(error).__name__+': '+str(error)
    return report
def resume():
    require(not state['acked'] and 'backup_sha256' not in state,'Already have an active backup transaction')
    path=BACKUP/'prefix.backup';description=BACKUP/'backup.json'
    for candidate,size in [(path,plan['offline_prefix_backup_bytes']),(description,None)]:
        require(not candidate.is_symlink(),'Recovery file symlink refused')
        s=candidate.stat()
        require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==deck_uid and
                stat.S_IMODE(s.st_mode)==0o400 and (size is None or s.st_size==size),'Recovery file ownership/mode/size differs')
    record=json.loads(description.read_text())
    require(record['bytes']==plan['offline_prefix_backup_bytes'] and record['cid_sha256']==plan['test_card_cid_sha256'] and
            record['mbr_sha256']==hashlib.sha256(before).hexdigest(),'Recovery metadata disagrees with plan')
    require(sha(path)==record['sha256'],'Recovery backup digest mismatch')
    fd=open_card(allow_after=True)
    try:
        require(io.canonical_prefix_sha256(fd,plan['offline_prefix_backup_bytes'],before)==record['sha256'],
                'Current protected prefix differs from original recovery backup')
        applied=io.read_exact(fd,512)==after
        if applied:
            geometry();probe=run(['blkid','-p','-o','export','/dev/mmcblk0p3'],allowed=(0,2))
            empty_partition_probe(probe.stdout,probe.returncode,read(SYS/'dev'))
    finally:os.close(fd)
    state['backup_sha256']=record['sha256'];state['partitioned']=applied
    return {'resumed_readonly':True,'partition_applied':applied,'formatted':False,
            'independent_backup_acknowledgment_required':True,'sha256':record['sha256']}
def repair_root_mode():
    require(state['formatted'] and not state['root_mode_repaired'],'Complete data formatting before one-time permission correction')
    backup_check();fd=open_card(writable=True,allow_after=True)
    try:
        protected_check(fd);geometry()
        run(['e2fsck','-fn','/dev/mmcblk0p2'],timeout=120,log='root-mode-before-fsck.txt')
        info=run(['debugfs','-R','stat <2>','/dev/mmcblk0p2']).stdout
        require(re.search(r'Inode:\s+2\s+Type:\s+directory\s+Mode:\s+0777\b',info) is not None,
                'Expected specifically the observed Deck automount root mode0777')
        require(re.search(r'User:\s+0\s+Group:\s+0\b',info) is not None,'Unexpected root inode ownership')
        mapping=run(['debugfs','-R','imap <2>','/dev/mmcblk0p2']).stdout
        found=re.search(r'located at block\s+(\d+),\s+offset\s+(0x[0-9a-fA-F]+)',mapping)
        require(found is not None,'Cannot bound inode2 location')
        root_offset=262144*512;superblock=root_offset+1024
        block_shift=struct.unpack('<I',io.read_exact(fd,4,superblock+24))[0]
        inode_size=struct.unpack('<H',io.read_exact(fd,2,superblock+88))[0]
        require(block_shift==2 and inode_size==256,'Unqualified root geometry for inode repair')
        inode=root_offset+int(found[1])*4096+int(found[2],16)
        require(root_offset<=inode and inode+256<=plan['offline_prefix_backup_bytes'],'Inode outside root region')
        allowed=[(inode,inode+2),(inode+0x7c,inode+0x7e),(inode+0x82,inode+0x84),
                 (superblock+0x30,superblock+0x34),(superblock+0x3fc,superblock+0x400)]
        run(['debugfs','-w','-R','set_inode_field <2> mode 040755','/dev/mmcblk0p2'],
            log='root-mode-correction.txt')
        # Partition and whole-device nodes have independent block caches.
        # Reopen through the alias synchronization guard after the partition write.
        os.close(fd);fd=-1
        fd=open_card(writable=True,allow_after=True)
        updated=run(['debugfs','-R','stat <2>','/dev/mmcblk0p2']).stdout
        require(re.search(r'Inode:\s+2\s+Type:\s+directory\s+Mode:\s+0755\b',updated) is not None,'Root permission readback failed')
        old=os.open(BACKUP/'prefix.backup',os.O_RDONLY|os.O_NOFOLLOW)
        try:comparison=io.compare_metadata_change(fd,old,plan['offline_prefix_backup_bytes'],before,allowed)
        finally:os.close(old)
        require(comparison['changed_bytes']>0,'Inode mode changed but whole-device readback did not; cache coherence unproven')
        run(['e2fsck','-fn','/dev/mmcblk0p2'],timeout=120,log='root-mode-after-fsck.txt')
        report={'root_mode':'0755','previous_mode':'0777','original_approved_mode':'0755',
                'only_inode2_mode_checksums_and_superblock_time_checksums_allowed':True,
                'before_canonical_prefix_sha256':state['backup_sha256'],'after':comparison,
                'no_file_data_or_boot_FAT_bytes_changed':True,'inode_absolute_offset':inode}
        write_new(BACKUP/'root-mode-repair.json',(json.dumps(report,indent=2)+'\n').encode())
        os.chown(BACKUP/'root-mode-repair.json',deck_uid,deck_gid);os.chmod(BACKUP/'root-mode-repair.json',0o400);sync_dir(BACKUP)
        state['protected_after_mode_repair_sha256']=comparison['sha256'];state['root_mode_repaired']=True
        return report
    finally:
        if fd>=0:os.close(fd)
def backup():
    require(not BACKUP.exists(),'Backup directory already exists; do not overwrite recovery data')
    fd=open_card()
    try:
        home=Path('/home/deck');s=home.stat()
        require(f'{os.major(s.st_dev)}:{os.minor(s.st_dev)}' not in device_numbers(),'Backup must be outside test card')
        require(shutil.disk_usage(home).free>plan['offline_prefix_backup_bytes']+256*1024*1024,'Insufficient backup space')
        BACKUP.mkdir(mode=0o700)
        os.chown(BACKUP,deck_uid,deck_gid)
        output=os.open(BACKUP/'prefix.partial',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        digest=hashlib.sha256()
        with os.fdopen(output,'wb') as f:
            for offset in range(0,plan['offline_prefix_backup_bytes'],1024*1024):
                data=io.read_exact(fd,1024*1024,offset);digest.update(data);f.write(data)
            f.flush();os.fsync(f.fileno())
        (BACKUP/'prefix.partial').rename(BACKUP/'prefix.backup');sync_dir(BACKUP)
        require(sha(BACKUP/'prefix.backup')==digest.hexdigest(),'Backup readback differs')
        # Both checks are read-only; any repair request must be reviewed separately.
        run(['fsck.fat','-n','/dev/mmcblk0p1'],timeout=120,log='fat-before.txt')
        run(['e2fsck','-fn','/dev/mmcblk0p2'],timeout=120,log='root-before.txt')
        require(io.read_exact(fd,512)==before,'MBR changed while backing up')
        identity();state['backup_sha256']=digest.hexdigest()
        write_new(BACKUP/'backup.json',(json.dumps({'bytes':plan['offline_prefix_backup_bytes'],
            'sha256':digest.hexdigest(),'cid_sha256':plan['test_card_cid_sha256'],
            'mbr_sha256':hashlib.sha256(before).hexdigest()},indent=2)+'\n').encode())
        # Private to the authorized deck user, so SSH can retrieve an independent copy.
        for name in ['prefix.backup','backup.json']:
            os.chown(BACKUP/name,deck_uid,deck_gid);os.chmod(BACKUP/name,0o400)
        os.chown(BACKUP,deck_uid,deck_gid);sync_dir(BACKUP);sync_dir(home)
        return {'backup_bytes':plan['offline_prefix_backup_bytes'],'sha256':digest.hexdigest(),
                'private_path':str(BACKUP/'prefix.backup'),'offline_existing_filesystems_ok':True}
    finally:os.close(fd)
def partition():
    backup_check();fd=open_card(writable=True)
    try:
        protected_check(fd);io.commit_mbr(fd,before,after);protected_check(fd);reread(fd)
        require(io.read_exact(fd,512)==after,'Partition table readback mismatch')
    finally:os.close(fd)
    geometry();identity();state['partitioned']=True
    return {'partition_applied':True,'protected640MiB_unchanged_except_p3_slot':True,
            'new_partition':plan['new_partition'],'filesystem_created':False}
def metadata():
    result=run(['blkid','-p','-o','export','/dev/mmcblk0p3'])
    values=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    wanted=plan['new_partition']
    require(values.get('TYPE')=='ext4' and values.get('UUID')==wanted['planned_uuid'] and values.get('LABEL')==wanted['planned_label'],'Data filesystem identity mismatch')
    features=run(['dumpe2fs','-h','/dev/mmcblk0p3']).stdout.split('Filesystem features:')[1].splitlines()[0].split()
    require(set(features)==FEATURES,'Unexpected ext4 features')
    return values
def mount_owned():
    mountpoint=ROOT/'data';mountpoint.mkdir(mode=0o700)
    run(['mount','-t','ext4','-o','rw,nosuid,nodev,noexec,data=ordered','/dev/mmcblk0p3',str(mountpoint)])
    state['mounted']=True
    check_owned_mount()
def check_owned_mount():
    target=str(ROOT/'data')
    values=run(['findmnt','-rn','-M',target,'-o','SOURCE,FSTYPE,MAJ:MIN,OPTIONS']).stdout.split()
    require(len(values)==4 and values[:3]==['/dev/mmcblk0p3','ext4',read(SYS_BLOCK/'mmcblk0p3/dev')],'Unowned data mount')
    require({'rw','nosuid','nodev','noexec'}<=set(values[3].split(',')),'Unsafe data mount options')
    require(not any(line.split()[4]==target for line in Path('/proc/1/mountinfo').read_text().splitlines()),'Data mount leaked into global namespace')
def unmount_owned():
    if state['mounted']:
        check_owned_mount();run(['umount',str(ROOT/'data')]);state['mounted']=False
        (ROOT/'data').rmdir()
def format_data():
    require(state['partitioned'] and not state['formatted'],'Expected fresh p3 from this transaction')
    backup_check();fd=open_card(allow_after=True)
    try:protected_check(fd);geometry()
    finally:os.close(fd)
    probe=run(['blkid','-p','-o','export','/dev/mmcblk0p3'],allowed=(0,2))
    empty_partition_probe(probe.stdout,probe.returncode,read(SYS/'dev'))
    wanted=plan['new_partition'];identity()
    args=['mke2fs','-t','ext4','-b','4096','-I','256','-i','65536','-m','0',
          '-L',wanted['planned_label'],'-U',wanted['planned_uuid'],
          '-O','none,'+','.join(sorted(FEATURES)),'-E','lazy_itable_init=0,lazy_journal_init=0','/dev/mmcblk0p3']
    run(args,timeout=900,log='data-format.txt');metadata()
    run(['e2fsck','-fn','/dev/mmcblk0p3'],timeout=180,log='data-before-marker.txt')
    try:
        mount_owned();mountpoint=ROOT/'data'
        write_new(mountpoint/'.muos-r35s-data-v1',b'MUOS-R35S-DATA-V1\n')
        (mountpoint/'MUOS').mkdir(mode=0o755)
        prefs=mountpoint/'MUOS/preferences';prefs.mkdir(mode=0o700)
        write_new(prefs/'.muos-preferences-v1',b'MUOS-R35S-PREFS-V1\n')
        sync_dir(prefs);sync_dir(mountpoint/'MUOS');sync_dir(mountpoint)
    finally:unmount_owned()
    run(['e2fsck','-fn','/dev/mmcblk0p3'],timeout=180,log='data-after-marker.txt')
    fd=open_card(allow_after=True)
    try:protected_check(fd)
    finally:os.close(fd)
    state['formatted']=True
    return {'data_formatted_and_marked':True,'metadata':metadata(),
            'preferences_record_created':False,'root_and_boot_prefix_preserved':True}
def verify():
    require(state['formatted'],'Data format has not completed in this transaction')
    backup_check();fd=open_card(allow_after=True)
    try:
        geometry();protected_check(fd);values=metadata()
        epoch='final-after-mode-repair' if state['root_mode_repaired'] else 'final'
        run(['fsck.fat','-n','/dev/mmcblk0p1'],timeout=120,log='fat-'+epoch+'.txt')
        run(['e2fsck','-fn','/dev/mmcblk0p2'],timeout=120,log='root-'+epoch+'.txt')
        run(['e2fsck','-fn','/dev/mmcblk0p3'],timeout=180,log='data-'+epoch+'.txt')
    finally:os.close(fd)
    report={'passed':True,'card_cid_sha256':plan['test_card_cid_sha256'],
            'new_partition':plan['new_partition'],'metadata':values,
            'protected640MiB_before_permission_repair_sha256':state['backup_sha256'],
            'protected640MiB_current_canonical_sha256':state.get('protected_after_mode_repair_sha256',state['backup_sha256']),
            'root_mode_repaired':state['root_mode_repaired'],
            'existing_and_new_offline_checks_passed':True,'data_unmounted':not state['mounted'],
            'rootfs_runtime_integration_enabled':False}
    result_name='result-after-mode-repair.json' if state['root_mode_repaired'] else 'result.json'
    write_new(BACKUP/result_name,(json.dumps(report,indent=2)+'\n').encode())
    os.chown(BACKUP/result_name,deck_uid,deck_gid);os.chmod(BACKUP/result_name,0o400);sync_dir(BACKUP)
    return report
def restore():
    backup_check();identity()
    # A partial slot is allowed only by the explicit recovery operation.
    fd=os.open(DEVICE,os.O_RDWR|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        protected_check(fd);io.restore_mbr_slot(fd,before,after);protected_check(fd);reread(fd)
    finally:os.close(fd)
    state['partitioned']=state['formatted']=False
    return {'original_MBR_restored':True,'existing640MiB_matches_independent_backup':True}
def dispatch(request):
    require(type(request) is dict and request.get('action') in {
        'inspect','backup','resume','ack-backup','partition','format','repair-root-mode','verify','restore','stop'},'Unsupported request')
    action=request['action'];require(set(request)==({'action','sha256'} if action=='ack-backup' else {'action'}),'Unexpected request fields')
    if action=='ack-backup':
        require(request['sha256']==state.get('backup_sha256') and type(request['sha256']) is str,'Independent backup digest mismatch')
        state['acked']=True;return {'independent_backup_acknowledged':True}
    if action=='stop':
        require(not state['mounted'],'Owned data mount still active');return {'stopping':True}
    return {'inspect':inspect,'backup':backup,'resume':resume,'partition':partition,'format':format_data,
            'repair-root-mode':repair_root_mode,'verify':verify,'restore':restore}[action]()

def serve():
    global io,layout,plan,before,after,deck_uid,deck_gid
    require(os.geteuid()==0 and len(sys.argv)==2 and sys.argv[1]=='serve','Run locally with sudo and argument serve')
    require(platform.machine()=='x86_64' and read(Path('/sys/class/dmi/id/product_name')) in ('Jupiter','Galileo'),'Expected Steam Deck')
    account=pwd.getpwnam('deck');deck_uid=account.pw_uid;deck_gid=account.pw_gid
    require(not ROOT.exists() and not os.path.lexists(SOCKET),'Another helper or stale state exists; inspect first')
    source=Path(__file__).resolve().parent
    manifest=json.loads((source/'package.json').read_text())
    require(manifest['qualified_offline_adapter'] is True,'Missing host qualification')
    allowed={'phase4-userdata-offline-server.py','phase4_userdata_io.py','phase4_userdata_layout.py',
             'inspect-phase4-userdata-offline.py','userdata-plan.json','inventory.json','mbr.before','mbr.proposed'}
    require(set(manifest['files'])==allowed,'Unexpected package contents')
    ROOT.mkdir(mode=0o700)
    for name,digest in manifest['files'].items():
        path=source/name;require(not path.is_symlink() and path.is_file() and sha(path)==digest,'Package payload changed: '+name)
        write_new(ROOT/name,path.read_bytes())
    sys.dont_write_bytecode=True
    io=load_module('phase4_userdata_io');layout=load_module('phase4_userdata_layout')
    plan=json.loads((ROOT/'userdata-plan.json').read_text());before=(ROOT/'mbr.before').read_bytes();after=(ROOT/'mbr.proposed').read_bytes()
    proposed,regenerated=layout.propose(before,json.loads((ROOT/'inventory.json').read_text()))
    require(proposed==after and regenerated['new_partition']==plan['new_partition'],'Plan no longer reproduces')
    require(hashlib.sha256(before).hexdigest()==plan['mbr_before_sha256'] and hashlib.sha256(after).hexdigest()==plan['mbr_proposed_sha256'],'MBR hashes differ')
    libc=ctypes.CDLL(None,use_errno=True)
    require(libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0,'Cannot isolate mounts')
    require(os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'),'Private namespace missing')
    server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);server.bind(SOCKET)
    os.chown(SOCKET,deck_uid,deck_gid);os.chmod(SOCKET,0o600);server.listen(1)
    print('C20 helper ready. Only inspect is meaningful until test128 is present. Keep this Konsole open.',flush=True)
    try:
        stop=False
        while not stop:
            connection,_=server.accept()
            with connection:
                try:
                    peer=struct.unpack('3i',connection.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
                    require(peer[1] in (0,deck_uid),'Unauthorized local peer')
                    connection.settimeout(15);raw=b''
                    while not raw.endswith(b'\n'):
                        part=connection.recv(1024);require(part and len(raw)+len(part)<=4096,'Invalid request size');raw+=part
                    request=json.loads(raw);result=dispatch(request)
                    response={'ok':True,'result':result};stop=request['action']=='stop'
                except Exception as error:
                    response={'ok':False,'error':type(error).__name__+': '+str(error),
                              'state':{k:v for k,v in state.items() if k!='backup_sha256'}}
                connection.sendall((json.dumps(response)+'\n').encode())
    finally:
        unmount_owned();server.close();os.unlink(SOCKET)
        for name in allowed:(ROOT/name).unlink()
        ROOT.rmdir()
        print('C20 helper stopped; socket/root snapshot removed. Private backup retained.',flush=True)

if __name__=='__main__':serve()
