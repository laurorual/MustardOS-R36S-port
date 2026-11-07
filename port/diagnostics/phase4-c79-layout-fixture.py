#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C100 real32MiB ext4 additions, metadata preservation and failure checks."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import json,os,shutil,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_c79_layout as layout
from phase4_backup_core import sha

os.umask(0o077);stage=Path(sys.argv[1]);cases=[]
tree=stage/'source-tree';tree.mkdir(mode=0o755);tree.chmod(0o755)
for name,mode in [('etc',0o755),('var',0o755),('var/lib',0o755),('var/lib/muos-diagnostic',0o700),('mnt',0o755),
    ('opt',0o755),('opt/muos',0o755),('opt/muos/share',0o755),('opt/muos/share/conf',0o755),('opt/muos/share/conf/rootfs',0o755)]:
    p=tree/name;p.mkdir(mode=mode);p.chmod(mode)
for name,data,mode in [('etc/banner',b'keep public bytes\n',0o644),('etc/muos-network-authorized_key',b'factory-placeholder\n',0o644),
    ('var/lib/muos-diagnostic/boot-seq',b'0\n',0o600),(layout.TEMPLATE,(stage/'template.dat').read_bytes(),0o755)]:
    p=tree/name;p.write_bytes(data);p.chmod(mode)
(tree/'etc/link').symlink_to('banner')
source=stage/'source.ext4'
with source.open('xb') as stream:stream.truncate(32*1024*1024)
subprocess.run(['mke2fs','-q','-t','ext4','-F','-m','0','-E','no_copy_xattrs','-d',str(tree),str(source)],check=True)
digest=sha(source)
def done(name):cases.append(name);print('C100_PASS_'+name,flush=True)
def fail(name,call):
    try:call()
    except (ValueError,OSError,KeyError):pass
    else:raise AssertionError(name)
    assert sha(source)==digest;done(name)
def compose(name,path=source,expected=None):
    dest=stage/name;dest.mkdir(mode=0o700)
    return layout.compose(path,expected or sha(path),32*1024*1024,dest)

r=compose('success');assert r['passed'] and r['fsck_exit']==0 and r['factory_counter_preserved']==0
before=json.loads((stage/'success/before-tree.json').read_text());after=json.loads((stage/'success/tree.json').read_text())
assert set(after)-set(before)==layout.ADDED and after['mnt']['links']==before['mnt']['links']+1
assert after['etc/asound.conf']['mode']==0o644 and after['mnt/mmc']['mode']==0o755
assert after['etc/link']==before['etc/link'] and after['var/lib/muos-diagnostic/boot-seq']==before['var/lib/muos-diagnostic/boot-seq']
done('real-ext4-two-additions-full-tree-ownership-modes-symlink-and-counter-preserved')
assert sha(source)==digest;done('source-byte-identical-after-compose')
for name,change in [('existing-asound',lambda x:x.update({'etc/asound.conf':x[layout.TEMPLATE]})),
    ('existing-mmc',lambda x:x.update({'mnt/mmc':x['mnt']})),
    ('foreign-mnt-content',lambda x:x.update({'mnt/other':x['mnt']})),
    ('missing-template',lambda x:x.pop(layout.TEMPLATE)),
    ('wrong-template-hash',lambda x:x[layout.TEMPLATE].update(sha256='0'*64)),
    ('wrong-template-mode',lambda x:x[layout.TEMPLATE].update(mode=0o644)),
    ('template-hardlink',lambda x:x[layout.TEMPLATE].update(links=2)),
    ('template-owner',lambda x:x[layout.TEMPLATE].update(uid=1000)),
    ('template-size',lambda x:x[layout.TEMPLATE].update(bytes=445)),
    ('template-alias',lambda x:x[layout.TEMPLATE].update(type='symlink')),
    ('template-xattr',lambda x:x[layout.TEMPLATE].update(xattrs={'user.test':'0'*64})),
    ('parent-alias',lambda x:x['etc'].update(type='symlink')),
    ('unsafe-mnt-mode',lambda x:x['mnt'].update(mode=0o777)),
    ('parent-owner',lambda x:x['mnt'].update(gid=1000)),
    ('mnt-directory-hardlink',lambda x:x['mnt'].update(links=3))]:
    bad=deepcopy(before);change(bad);fail(name,lambda bad=bad:layout.expected_tree(bad))
fail('wrong-source-hash',lambda:compose('bad-hash',expected='0'*64))
alias=stage/'alias.ext4';alias.symlink_to(source)
fail('source-symlink',lambda:compose('bad-alias',path=alias,expected=digest));alias.unlink()
link=stage/'hardlink.ext4';os.link(source,link)
fail('source-hardlink',lambda:compose('bad-link'));link.unlink()
source.chmod(0o644);fail('nonprivate-source-mode',lambda:compose('bad-mode'));source.chmod(0o600)
original_debug=layout.image.debug
def corrupt(fd,request,writable=False):
    result=original_debug(fd,request,writable)
    if request=='mkdir /mnt/mmc':original_debug(fd,'set_inode_field /etc/banner mode 0100600',True)
    return result
with patch.object(layout.image,'debug',corrupt):fail('unrelated-public-change-detected-in-full-readback',lambda:compose('corrupt-public'))
def short(src,out,size):
    assert os.pwrite(out,os.pread(src,512,0),0)==512
    raise OSError('interrupted regular clone')
with patch.object(layout.image,'sparse_clone',short):fail('short-clone-preserves-source-and-no-completion',lambda:compose('short'))
with patch.object(layout.os,'fsync',side_effect=OSError('sync failed')):
    fail('sync-failure-no-completion',lambda:compose('sync-fail'))
damaged=stage/'damaged.ext4';shutil.copyfile(source,damaged);damaged.chmod(0o600)
fd=os.open(damaged,os.O_RDWR)
try:os.pwrite(fd,b'\0\0',1024+56)
finally:os.close(fd)
fail('damaged-ext4-refused',lambda:compose('damaged',path=damaged))
for p in stage.iterdir():
    if p.is_dir() and p.name not in ['source-tree','success']:assert not (p/'analysis.json').exists(),p
done('failed-compositions-never-publish-success')
(stage/'fixture-results.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'real_ext4_32MiB':True,'full_scan_fsck_and_regular_writes_executed':True,'physical_media_or_network_accessed':False})+'\n')
