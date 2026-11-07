#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""One-shot final readback after syncing the exact test-card block aliases.

No formatting, repartitioning, inode editing or arbitrary command interface.
Only cache synchronization, RO marker validation, fsck-n and public evidence.
Run locally with sudo on the Deck after the C20 server has been stopped.
"""
from pathlib import Path
import ctypes,fcntl,hashlib,importlib.util,json,os,pwd,re,stat,sys,tempfile
sys.dont_write_bytecode=True
BLKFLSBUF=0x1261
PINNED={'phase4-userdata-offline-server.py':'aa42af171c0513287d85bbe23f46b846c1eed78e682bd907d89d98f6a001ffa7',
        'phase4_userdata_io.py':'3f42a102ffa040c334b13e1ecfe8ffad13dfb3a9f2a3a6304355d8ada9545dc9',
        'phase4_userdata_layout.py':'dc29713c57382f537cbd4c40658431efd8d74cb9742855f8286fbf243fc92a07'}

def flush_aliases(aliases):
    """Only these already-identified, idle block nodes; partition aliases first."""
    flushed=[]
    for path,expected in aliases:
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            s=os.fstat(fd)
            if not stat.S_ISBLK(s.st_mode) or s.st_rdev!=expected:raise RuntimeError('Alias identity mismatch')
            os.fsync(fd);fcntl.ioctl(fd,BLKFLSBUF,0);flushed.append(str(path))
        finally:os.close(fd)
    return flushed

def main():
    if os.geteuid()!=0 or len(sys.argv)!=1:raise SystemExit('Run this fixed audit locally with sudo')
    base=Path(__file__).resolve().parent
    manifest=json.loads((base/'package.json').read_text())
    for name,digest in manifest['files'].items():
        path=base/name
        assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
    for name,digest in PINNED.items():assert hashlib.sha256((base/name).read_bytes()).hexdigest()==digest,name
    def load(name,filename):
        spec=importlib.util.spec_from_file_location(name,base/filename)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    s=load('server','phase4-userdata-offline-server.py');s.io=load('io','phase4_userdata_io.py')
    layout=load('layout','phase4_userdata_layout.py')
    s.plan=json.loads((base/'userdata-plan.json').read_text());s.before=(base/'mbr.before').read_bytes();s.after=(base/'mbr.proposed').read_bytes()
    expected,_=layout.propose(s.before,json.loads((base/'inventory.json').read_text()));assert expected==s.after
    account=pwd.getpwnam('deck');s.deck_uid=account.pw_uid;s.deck_gid=account.pw_gid
    assert not os.path.lexists(s.SOCKET) and not s.ROOT.exists(),'Stop the old helper before auditing'
    s.identity()
    recovery=json.loads((s.BACKUP/'backup.json').read_text())
    assert recovery['bytes']==671088640 and recovery['mbr_sha256']==hashlib.sha256(s.before).hexdigest()
    assert recovery['cid_sha256']==s.plan['test_card_cid_sha256']
    assert s.sha(s.BACKUP/'prefix.backup')==recovery['sha256']
    aliases=[]
    for name in ['mmcblk0p1','mmcblk0p2','mmcblk0p3','mmcblk0']:
        maj,minr=map(int,s.read(s.SYS_BLOCK/name/'dev').split(':'))
        aliases.append((Path('/dev')/name,os.makedev(maj,minr)))
    flushed=flush_aliases(aliases)
    s.identity();fd=s.open_card(allow_after=True)
    try:
        assert s.io.read_exact(fd,512)==s.after
        s.geometry();s.metadata()
        info=s.run(['debugfs','-R','stat <2>','/dev/mmcblk0p2']).stdout
        assert re.search(r'Inode:\s+2\s+Type:\s+directory\s+Mode:\s+0755\b',info)
        assert re.search(r'User:\s+0\s+Group:\s+0\b',info)
        mapping=s.run(['debugfs','-R','imap <2>','/dev/mmcblk0p2']).stdout
        found=re.search(r'located at block\s+(\d+),\s+offset\s+(0x[0-9a-fA-F]+)',mapping);assert found
        root_offset=262144*512;sb=root_offset+1024
        import struct
        assert struct.unpack('<I',s.io.read_exact(fd,4,sb+24))[0]==2
        assert struct.unpack('<H',s.io.read_exact(fd,2,sb+88))[0]==256
        inode=root_offset+int(found[1])*4096+int(found[2],16)
        assert root_offset<=inode and inode+256<=671088640
        allowed=[(inode,inode+2),(inode+0x7c,inode+0x7e),(inode+0x82,inode+0x84),
                 (sb+0x30,sb+0x34),(sb+0x3fc,sb+0x400)]
        old=os.open(s.BACKUP/'prefix.backup',os.O_RDONLY|os.O_NOFOLLOW)
        try:
            # A 0777→0755 claim with zero changed bytes is a stale alias, not success.
            assert s.io.read_exact(old,2,inode)!=s.io.read_exact(fd,2,inode)
            comparison=s.io.compare_metadata_change(fd,old,671088640,s.before,allowed)
            assert comparison['changed_bytes']>0
        finally:os.close(old)
    finally:os.close(fd)
    root=Path(tempfile.mkdtemp(prefix='muos-c20-cache-audit.',dir='/run'));mountpoint=root/'data';mountpoint.mkdir()
    mounted=False
    try:
        libc=ctypes.CDLL(None,use_errno=True)
        assert libc.unshare(0x20000)==0 and libc.mount(None,b'/',None,16384|262144,None)==0
        assert os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt')
        s.run(['mount','-t','ext4','-o','ro,noload,nosuid,nodev,noexec','/dev/mmcblk0p3',str(mountpoint)])
        mounted=True
        values=s.run(['findmnt','-rn','-M',str(mountpoint),'-o','SOURCE,FSTYPE,MAJ:MIN,OPTIONS']).stdout.split()
        assert values[:3]==['/dev/mmcblk0p3','ext4',s.read(s.SYS_BLOCK/'mmcblk0p3/dev')]
        assert {'ro','nosuid','nodev','noexec'}<=set(values[3].split(','))
        assert not any(line.split()[4]==str(mountpoint) for line in Path('/proc/1/mountinfo').read_text().splitlines())
        for path in [mountpoint,mountpoint/'MUOS']:
            directory=path.lstat()
            assert stat.S_ISDIR(directory.st_mode) and directory.st_uid==directory.st_gid==0
            assert stat.S_IMODE(directory.st_mode)==0o755
        for name,text in [('.muos-r35s-data-v1',b'MUOS-R35S-DATA-V1\n'),
                          ('MUOS/preferences/.muos-preferences-v1',b'MUOS-R35S-PREFS-V1\n')]:
            path=mountpoint/name;mode=path.lstat()
            assert stat.S_ISREG(mode.st_mode) and mode.st_uid==mode.st_gid==0 and mode.st_nlink==1
            assert stat.S_IMODE(mode.st_mode)==0o600 and path.read_bytes()==text
        directory=(mountpoint/'MUOS/preferences').lstat()
        assert stat.S_ISDIR(directory.st_mode) and directory.st_uid==directory.st_gid==0 and stat.S_IMODE(directory.st_mode)==0o700
        assert not (mountpoint/'MUOS/preferences/preferences').exists()
    finally:
        if mounted:s.run(['umount',str(mountpoint)])
        mountpoint.rmdir();root.rmdir()
    s.state={'acked':True,'partitioned':True,'formatted':True,'mounted':False,'root_mode_repaired':True,
             'backup_sha256':recovery['sha256'],'protected_after_mode_repair_sha256':comparison['sha256']}
    verified=s.verify()
    report={'root_mode':'0755','previous_mode':'0777','no_file_data_or_boot_FAT_bytes_changed':True,
            'before_canonical_prefix_sha256':recovery['sha256'],'after':comparison,
            'cache_aliases_synchronized':flushed,'markers_readonly_validated':True,
            'supersedes_cached_whole_device_readback':True,
            'legacy_root_mode_report_sha256':s.sha(s.BACKUP/'root-mode-repair.json'),
            'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    destination=s.BACKUP/'root-mode-repair-cache-confirmed.json'
    s.write_new(destination,(json.dumps(report,indent=2)+'\n').encode())
    os.chown(destination,s.deck_uid,s.deck_gid);os.chmod(destination,0o400);s.sync_dir(s.BACKUP)
    print(json.dumps({'passed':verified['passed'],'root_mode':'0755','fresh_readback':comparison,
                      'markers_valid':True,'all_filesystems_offline_clean':True,'card_unmounted':True},indent=2))

if __name__=='__main__':main()
