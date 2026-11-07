#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Qualify the exact inode2 correction on a PRIVATE regular backup copy only."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import hashlib,importlib.util,json,os,re,shutil,struct,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'preferences'
package=Path((area/'latest-offline-package').read_text().strip());assert package.is_relative_to(area)
record=json.loads((package/'independent-backup.json').read_text());backup=Path(record['host_private_copy'])
assert backup.is_relative_to(work/'private') and not backup.is_symlink()
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert backup.stat().st_size==671088640 and sha(backup)==record['sha256']
stage=Path(tempfile.mkdtemp(prefix='root-mode-checks.',dir=area))
private=Path(tempfile.mkdtemp(prefix='root-mode-fixture.',dir=work/'private'));private.chmod(0o700)
root=private/'root.ext4';prefix=private/'prefix.fixture'
source=repo/'port/scripts/phase4_userdata_io.py'
spec=importlib.util.spec_from_file_location('io',source);io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)
container=(work/'rootfs-container.iid').read_text().strip()
try:
    fd=os.open(root,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with backup.open('rb') as original,os.fdopen(fd,'wb') as f:
        original.seek(128*1024*1024)
        for _ in range(512):
            data=original.read(1024*1024);assert len(data)==1024*1024;f.write(data)
    code='''set -eu
cd /private
e2fsck -fn root.ext4 > fsck-before.txt 2>&1
debugfs -R 'stat <2>' root.ext4 > inode-before.txt 2> stat-before.stderr
debugfs -R 'imap <2>' root.ext4 > inode-map.txt 2> map.stderr
debugfs -w -R 'set_inode_field <2> mode 040755' root.ext4 > correction.stdout 2> correction.stderr
e2fsck -fn root.ext4 > fsck-after.txt 2>&1
debugfs -R 'stat <2>' root.ext4 > inode-after.txt 2> stat-after.stderr
'''
    r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
        '--security-opt=no-new-privileges','--userns=keep-id','-v',f'{private}:/private:rw,z',
        container,'sh','-c',code],capture_output=True,text=True,timeout=45)
    assert r.returncode==0,(r.stdout,r.stderr)
    assert re.search(r'Mode:\s+0777\b',(private/'inode-before.txt').read_text())
    assert re.search(r'Mode:\s+0755\b',(private/'inode-after.txt').read_text())
    mapping=re.search(r'located at block\s+(\d+),\s+offset\s+(0x[0-9a-fA-F]+)',(private/'inode-map.txt').read_text())
    assert mapping,'Cannot locate original root inode2'
    with root.open('rb') as f:
        f.seek(1024+24);assert struct.unpack('<I',f.read(4))[0]==2
        f.seek(1024+88);assert struct.unpack('<H',f.read(2))[0]==256
    inode=128*1024*1024+int(mapping[1])*4096+int(mapping[2],16)
    superblock=128*1024*1024+1024
    allowed=[(inode,inode+2),(inode+0x7c,inode+0x7e),(inode+0x82,inode+0x84),
             (superblock+0x30,superblock+0x34),(superblock+0x3fc,superblock+0x400)]
    # Reproduce the partition mapping with regular files. The full-prefix check
    # observes every changed byte, not just known fields extracted from debugfs.
    fd=os.open(prefix,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with backup.open('rb') as f,os.fdopen(fd,'wb') as output:shutil.copyfileobj(f,output,1024*1024)
    changed=[]
    current=os.open(prefix,os.O_RDWR)
    old=os.open(backup,os.O_RDONLY)
    try:
        with root.open('rb') as modified:
            for offset in range(128*1024*1024,671088640,1024*1024):
                new=modified.read(1024*1024);original=io.read_exact(old,1024*1024,offset)
                assert len(new)==len(original)
                if new==original:continue
                os.pwrite(current,new,offset)
        proposed=(package/'payload/mbr.proposed').read_bytes();before=(package/'payload/mbr.before').read_bytes()
        os.pwrite(current,proposed,0)
        comparison=io.compare_metadata_change(current,old,671088640,before,allowed)
        assert comparison['changed_bytes']>0
        os.pwrite(current,b'X',16*1024*1024)
        try:io.compare_metadata_change(current,old,671088640,before,allowed)
        except ValueError:pass
        else:raise AssertionError('A changed FAT byte was accepted')
    finally:os.close(current);os.close(old)
    for name in ['fsck-before.txt','fsck-after.txt','inode-before.txt','inode-after.txt','inode-map.txt',
                 'correction.stdout','correction.stderr']:
        shutil.copyfile(private/name,stage/name)
    result={'passed':True,'regular_copy_of_actual_private_root_backup_only':True,
            'root_mode_0777_to_0755_fsck_passed':True,'no_file_data_or_boot_FAT_changes':True,
            'comparison':comparison,'inode_absolute_offset':inode,'allowed_metadata_ranges':allowed,
            'unrelated_FAT_change_refused':True,'card_or_device_modified':False,
            'io_source_sha256':sha(source),'check_source_sha256':sha(Path(__file__)),
            'server_source_sha256':sha(repo/'port/scripts/phase4-userdata-offline-server.py')}
    (stage/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
finally:
    # Only this freshly created, private fixture directory is removed. Backups stay.
    shutil.rmtree(private)
(area/'latest-root-mode-checks').write_text(str(stage)+'\n')
print('Actual private root COPY correction passed:0777→0755, fsck and byte bounds; fixtures removed.',stage)
