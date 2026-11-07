#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C88 real 32MiB ext4 provision/fault fixtures inside the existing container."""
from pathlib import Path
from unittest.mock import patch
import hashlib,os,shutil,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_initial_image as c
import phase4_recovery_image as image
import phase4_root_recovery as recovery
from phase4_backup_core import sha

stage=Path(sys.argv[1]);stage.mkdir(mode=0o700,exist_ok=True);os.umask(0o077)
factory_tree=stage/'factory-tree';factory_tree.mkdir(mode=0o755);factory_tree.chmod(0o755)
for name,mode in [('etc',0o755),('var',0o755),('var/lib',0o755),('var/lib/muos-diagnostic',0o700)]:
    p=factory_tree/name;p.mkdir(mode=mode);p.chmod(mode)
for name,data,mode in [('etc/banner',b'public-factory\n',0o644),('etc/muos-network-authorized_key',b'factory-placeholder\n',0o644),
    (recovery.COUNTER,b'0\n',0o600)]:
    p=factory_tree/name;p.write_bytes(data);p.chmod(mode)
(factory_tree/'etc/link').symlink_to('banner')
backup_tree=stage/'reference-tree';shutil.copytree(factory_tree,backup_tree,symlinks=True)
for n in c.NEW_DIRS:(backup_tree/n).mkdir(mode=0o700)
rows={}
for n in sorted(recovery.PRIVATE_FILES|{'var/lib/muos-network/dropbear_ed25519_host_key.tmp.pub'}):
    data=b'72\n' if n==recovery.COUNTER else b'fixture-private-not-a-real-key-or-seed'*2
    mode=0o400 if n==recovery.CREDIT else 0o644 if n.startswith('etc/') else 0o600
    p=backup_tree/n;p.write_bytes(data);p.chmod(mode)
    rows[n]={'sha256':recovery.hashed(data),'mode':mode,'uid':0,'gid':0,'links':1,'bytes':len(data)}
history=backup_tree/'var/lib/muos-diagnostic/c25.used.BOOT0064';history.write_bytes(b'MUOS-C25-ONCE\nBOOT=64\n');history.chmod(0o600)
def make(tree,name):
    path=stage/name
    with path.open('xb') as out:out.truncate(32*1024*1024)
    path.chmod(0o600)
    # Match the qualified C79 filesystem: host SELinux labels must not leak
    # into these deliberately xattr-free factory fixtures.
    p=subprocess.run(['mke2fs','-q','-t','ext4','-F','-m','0','-E','no_copy_xattrs','-d',str(tree),str(path)],capture_output=True)
    assert p.returncode==0,p.stderr
    return path
factory=make(factory_tree,'factory.ext4');reference=make(backup_tree,'reference.ext4')
factory_sha=sha(factory);ref_sha=sha(reference)
def compose(name,source=factory,source_sha=None,manifest=rows):
    out=stage/name;out.mkdir(mode=0o700)
    return c.compose(source,source_sha or sha(source),reference,ref_sha,32*1024*1024,out,manifest,72)
def fail(name,call):
    try:call()
    except (ValueError,OSError):pass
    else:raise AssertionError(name)
    assert sha(factory)==factory_sha and sha(reference)==ref_sha
    print('C88_PASS_'+name,flush=True)
r=compose('success')
assert r['passed'] and r['counter_preserved']==72 and r['historical_marker_count']==1
assert not r['boot_handoff_authorized'] and not r['seed_generated_or_loaded']
print('C88_PASS_real-ext4-private-state-history-public-metadata-and-symlink-readback',flush=True)
assert sha(factory)==factory_sha and sha(reference)==ref_sha
print('C88_PASS_factory-and-reference-byte-identical-after-provisioning',flush=True)
fail('wrong-factory-hash-refused',lambda:compose('bad-sha',source_sha='0'*64))
badrows={n:dict(v) for n,v in rows.items()};badrows[recovery.COUNTER]['sha256']='f'*64
fail('counter-manifest-mismatch-refused',lambda:compose('bad-rows',manifest=badrows))
original_clone=image.sparse_clone
def mutate_public(source,target,size):
    original_clone(source,target,size);image.debug(target,'set_inode_field /etc/banner mode 0100600',True)
with patch.object(image,'sparse_clone',mutate_public):
    fail('public-inode-mode-tamper-detected',lambda:compose('tampered-public'))
def short_clone(source,target,size):
    assert os.pwrite(target,os.pread(source,512,0),0)==512
    raise OSError('fixture interrupted clone')
with patch.object(image,'sparse_clone',short_clone):fail('interrupted-regular-clone-no-completion',lambda:compose('short-clone'))
for name,mutate in [('active-token',lambda tree:(tree/'var/lib/muos-diagnostic/c12.once').write_bytes(b'not-armed')),
    ('private-dir-already-present',lambda tree:(tree/'var/lib/muos-network').mkdir(mode=0o700)),
    ('factory-counter-not-zero',lambda tree:(tree/recovery.COUNTER).write_bytes(b'71\n')),
    ('placeholder-not-public-mode',lambda tree:(tree/'etc/muos-network-authorized_key').chmod(0o600))]:
    tree=stage/('bad-'+name);shutil.copytree(factory_tree,tree,symlinks=True);mutate(tree)
    bad=make(tree,name+'.ext4');fail(name,lambda bad=bad,name=name:compose('refused-'+name,source=bad))
bad=stage/'factory-xattrs.ext4';shutil.copyfile(factory,bad);bad.chmod(0o600)
out=os.open(bad,os.O_RDWR)
try:image.debug(out,'ea_set /etc/banner user.fixture unexpected',True);os.fsync(out)
finally:os.close(out)
fail('unqualified-factory-xattrs-refused',lambda:compose('bad-xattrs',source=bad))
for p in stage.iterdir():
    if p.is_dir() and (p/'candidate.ext4').exists():
        if p.name!='success':assert not (p/'analysis.json').exists()
        (p/'candidate.ext4').unlink()
print('C88_PASS_failed-compositions-never-publish-completion',flush=True)
