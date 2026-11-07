#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""One-file B01 test-card correction, with exact old/new hashes and card guards."""
from pathlib import Path
import hashlib,json,os,stat,subprocess,sys,tempfile

assert os.geteuid()==0
if sys.argv[-1:]!=['--private']:
    os.execvp('unshare',['unshare','--mount','--propagation','private',sys.executable,__file__,*sys.argv[1:],'--private'])
assert Path('/proc/self/ns/mnt').stat().st_ino!=Path('/proc/1/ns/mnt').stat().st_ino
def cmd(*args):return subprocess.check_output(args,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cid(n):return hashlib.sha256(Path('/sys/block',n,'device/cid').read_text().strip().lower().encode()).hexdigest()
plan_path=Path(sys.argv[1]);plan=json.loads(plan_path.read_text())
assert sha(Path(__file__))==plan['patcher_sha256']
assert cmd('uname','-r')=='4.4.189'
assert cmd('findmnt','-rn','-o','SOURCE','/')=='/dev/mmcblk0p2'
assert cmd('findmnt','-rn','-o','SOURCE','/boot')=='/dev/mmcblk0p1'
assert cid('mmcblk0')=='9b4fc38015ae4a049ecd796ceceb2ef9473f4773c9b3a066ce59b567c516bbef'
assert cid('mmcblk1')=='12d2c78fbc14993fe2f8a00c413a5e3ef8d9659a3eba9a41a77b5c37029aa193'
assert int(Path('/sys/block/mmcblk1/size').read_text())*512==127934660608
assert cmd('blkid','-s','PARTUUID','-o','value','/dev/mmcblk1p2')=='4d554432-02'
number=Path('/sys/class/block/mmcblk1p2/dev').read_text().strip()
assert not [x for x in Path('/proc/self/mountinfo').read_text().splitlines() if x.split()[2]==number]
assert Path('/proc/sys/kernel/tainted').read_text().strip()=='0'
assert all(x.rsplit(None,1)[1]=='0' for x in cmd('btrfs','device','stats','/').splitlines())
assert plan['authorized_secondary_diagnostic_correction'] is True
source=plan_path.parent/'init'
assert stat.S_ISREG(source.lstat().st_mode) and source.stat().st_size<16384 and sha(source)==plan['new_sha256']
result={'scope':'B01 one-file init format correction on secondary only','old_sha256':plan['old_sha256'],'new_sha256':plan['new_sha256'],'file_replaced':False}
with tempfile.TemporaryDirectory(prefix='muos-ext4-fix-',dir='/tmp') as temporary:
    mounted=False
    try:
        subprocess.run(['mount','-t','ext4','-o','rw,nosuid,nodev,noexec','/dev/mmcblk1p2',temporary],check=True);mounted=True
        root=Path(temporary)
        assert cmd('findmnt','-rn','-o','MAJ:MIN','--target',temporary)==number
        assert (root/'etc/muos-ext4-diagnostic').read_text().strip()=='MUOS-R35S-EXT4-P4-B01'
        assert 'enabled=0\n' in (root/'etc/default/muos-ui').read_text()
        assert not (root/'sbin').is_symlink()
        target=root/'sbin/muos-ext4-diag'
        assert stat.S_ISREG(target.lstat().st_mode) and sha(target)==plan['old_sha256']
        # Require precisely the intended one-flag edit, not arbitrary new code.
        assert source.read_bytes()==target.read_bytes().replace(b'findmnt -n -o MAJ:MIN /',b'findmnt -rn -o MAJ:MIN /')
        pending=target.with_name('.muos-ext4-diag.new')
        fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o755)
        with os.fdopen(fd,'wb') as f:
            f.write(source.read_bytes());f.flush();os.fchmod(f.fileno(),0o755);os.fchown(f.fileno(),0,0);os.fsync(f.fileno())
        pending.replace(target)
        fd=os.open(target.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
        assert sha(target)==plan['new_sha256'];result['file_replaced']=True
    finally:
        if mounted:subprocess.run(['umount',temporary],check=True)
result['candidate_unmounted']=True
fsck=subprocess.run(['e2fsck','-fn','/dev/mmcblk1p2'],text=True,capture_output=True)
result['fsck']={'exit':fsck.returncode,'out':fsck.stdout,'err':fsck.stderr}
assert fsck.returncode==0
print(json.dumps(result,indent=2))
