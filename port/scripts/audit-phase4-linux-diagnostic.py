#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Audit the initramfs archive, own ABI/applets and read-only card guard."""
from pathlib import Path
import gzip
import hashlib
import json
import stat
import subprocess

repo=Path(__file__).resolve().parents[2]
work=repo/'build/phase4'
stage=Path((work/'linux-diagnostic/latest-initramfs').read_text().strip())
record=json.loads((stage/'manifest.json').read_text())
root=stage/'root'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in record['port_inputs'].items(): assert sha(repo/name)==digest,name
for name,info in record['assets'].items(): assert sha(Path(info['path']))==info['sha256'],name
# Independent archive reader verifies every regular payload, link and node.
raw=gzip.decompress((stage/'initramfs.cpio.gz').read_bytes())
assert raw==(stage/'initramfs.cpio').read_bytes()
offset=0; entries={}
while True:
    assert raw[offset:offset+6]==b'070701'
    fields=[int(raw[offset+6+i*8:offset+14+i*8],16) for i in range(13)]
    _,mode,uid,gid,_,_,size,_,_,major,minor,namesize,_=fields
    assert uid==gid==0
    start=offset+110
    name=raw[start:start+namesize-1].decode()
    assert raw[start+namesize-1]==0 and name not in entries
    assert not name.startswith('/') and '..' not in Path(name).parts
    start=(start+namesize+3)&~3
    data=raw[start:start+size]; assert len(data)==size
    offset=(start+size+3)&~3
    entries[name]=(mode,data,major,minor)
    if name=='TRAILER!!!': break
assert not any(raw[offset:])
for name,digest in record['initramfs_regular_files'].items():
    assert stat.S_ISREG(entries[name][0])
    assert hashlib.sha256(entries[name][1]).hexdigest()==digest,name
assert stat.S_ISCHR(entries['dev/console'][0]) and entries['dev/console'][2:]==(5,1)
assert stat.S_ISCHR(entries['dev/null'][0]) and entries['dev/null'][2:]==(1,3)
for p in (root/'bin').iterdir():
    if p.is_symlink(): assert stat.S_ISLNK(entries['bin/'+p.name][0]) and entries['bin/'+p.name][1]==b'busybox'
image=(work/'rootfs-container.iid').read_text().strip()
assert image=='sha256:ccef62bd0d6602d0f891f160e2040653df3b782976458308d8fcd6f1e99e6787'
command=['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
         '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
         '-v',f'{work}:/work:rw,z','-e','DIAG_REL='+str(stage.relative_to(work)),image,'sh','-eu','-c',r'''
cd "/work/$DIAG_REL"
root=$PWD/root
for file in bin/busybox lib/ld-linux-aarch64.so.1 lib/libc.so.6 lib/libresolv.so.2; do
    readelf -h -l -d "$root/$file"
done > elf.txt
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" --list > applets.txt
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/init"
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/card-guard.sh"
gzip -dc initramfs.cpio.gz | cpio -it --quiet > cpio-list.txt
if qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh "$root/init" > pid-guard.txt 2>&1; then
    exit 1
else
    test "$?" = 64
fi
''']
with (stage/'audit.log').open('w') as log:
    subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
applets=set((stage/'applets.txt').read_text().splitlines())
assert {p.name for p in (root/'bin').iterdir() if p.is_symlink()} <= applets
assert 'This init requires PID 1' in (stage/'pid-guard.txt').read_text()
# Card identities come from the read-only live inventory, never from a test
# relaxation in the production init. The fixtures contain no block devices.
device=json.loads((work/'linux-diagnostic/device-before.json').read_text())
assert device['taint']=='0' and device['btrfs']['exit']==0
fixtures=stage/'card-fixtures'; fixtures.mkdir()
def card(folder,name,cid,sectors):
    p=folder/'block'/name; (p/'device').mkdir(parents=True)
    (p/'device/cid').write_text(cid+'\n'); (p/'size').write_text(str(sectors)+'\n')
primary=device['cards']['mmcblk0']; secondary=device['cards']['mmcblk1']
assert hashlib.sha256(primary['cid'].encode()).hexdigest()=='9b4fc38015ae4a049ecd796ceceb2ef9473f4773c9b3a066ce59b567c516bbef'
assert hashlib.sha256(secondary['cid'].encode()).hexdigest()=='12d2c78fbc14993fe2f8a00c413a5e3ef8d9659a3eba9a41a77b5c37029aa193'
assert int(secondary['sectors'])*512==127934660608
cases={}
for name in ['absent','secondary-only','wrong-size','protected-present','duplicate-secondary','primary-only']:
    f=fixtures/name; f.mkdir()
    if name not in ['absent','primary-only']:
        card(f,'mmcblk0',secondary['cid'],1 if name=='wrong-size' else secondary['sectors'])
    if name in ['protected-present','primary-only']:
        card(f,'mmcblk1',primary['cid'],primary['sectors'])
    if name=='duplicate-secondary': card(f,'mmcblk1',secondary['cid'],secondary['sectors'])
    p=subprocess.run(['sh','-c','. "$1"; diag_card "$2"','guard',str(root/'card-guard.sh'),str(f)],text=True,capture_output=True)
    if name=='secondary-only': assert p.returncode==0 and p.stdout.strip()=='/dev/mmcblk0p1'
    else: assert p.returncode!=0 and not p.stdout
    cases[name]='accepted correct secondary' if p.returncode==0 else 'rejected'
report={'scope':'host archive/ABI/QEMU and host-shell card selection; not PID1/native boot',
        'passed':True,'archive_verified':True,'qemu_cortex_a35_busybox_and_shell':True,
        'pid1_refusal_checked':True,'card_guard_cases':cases,'elf_files':4,
        'container_image_id':image,'kernel_booted':False,'init_pid1_executed':False,
        'device_writes':False,'audit_source_sha256':sha(Path(__file__))}
(stage/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
record['userspace_qemu_checked']=True
record['userspace_audit_sha256']=sha(stage/'audit.json')
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print('Initramfs archive, own ABI/QEMU and six card-guard cases passed')
