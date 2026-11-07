#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C92 production composition with synthetic ext4 only; no media or entropy credit."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import errno,json,os,shutil,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_initial_migration as m
import phase4_recovery_image as image
import phase4_root_recovery as r
from phase4_backup_core import sha

stage=Path(sys.argv[1]);os.umask(0o077);size=32*1024*1024;cases=[]
def folder(name):p=stage/name;p.mkdir(mode=0o700);return p
def passed(name):cases.append(name);print('C92_PASS_'+name,flush=True)
def run(argv):
    p=subprocess.run(argv,capture_output=True,timeout=45);assert p.returncode==0,(argv,p.stderr[-1000:]);return p
factory_tree=folder('factory-tree');factory_tree.chmod(0o755)
for n,mode in [('etc',0o755),('var',0o755),('var/lib',0o755),('var/lib/muos-diagnostic',0o700)]:
    (factory_tree/n).mkdir(mode=mode);(factory_tree/n).chmod(mode)
for n,data,mode in [('etc/banner',b'NEW C79 FACTORY\n',0o644),('etc/muos-network-authorized_key',b'placeholder\n',0o644),(r.COUNTER,b'0\n',0o600)]:
    (factory_tree/n).write_bytes(data);(factory_tree/n).chmod(mode)
(factory_tree/'etc/banner-link').symlink_to('banner')
observed_tree=stage/'observed-tree';shutil.copytree(factory_tree,observed_tree,symlinks=True)
for n in m.initial.NEW_DIRS:(observed_tree/n).mkdir(mode=0o700)
(observed_tree/'etc/banner').write_bytes(b'OLD C76 PUBLIC FIRMWARE\n')
payload={n:('fixture-private '+n).encode() for n in r.STABLE}
payload.update({r.CREDIT:b'O'*256,r.NO_CREDIT:b'N'*256,r.COUNTER:b'75\n'})
rows={}
for n,data in payload.items():
    mode=0o400 if n in (r.CREDIT,r.NO_CREDIT) else 0o644 if n.startswith('etc/') else 0o600
    (observed_tree/n).write_bytes(data);(observed_tree/n).chmod(mode)
    rows[n]={'sha256':r.hashed(data),'bytes':len(data),'mode':mode,'uid':0,'gid':0,'links':1}
marker=observed_tree/'var/lib/muos-diagnostic/c25.used.BOOT0064';marker.write_bytes(b'MUOS-C25-ONCE\nBOOT=64\n');marker.chmod(0o600)
def make(tree,name):
    p=stage/name
    with p.open('xb') as f:f.truncate(size)
    run(['mke2fs','-q','-t','ext4','-F','-m','0','-E','no_copy_xattrs','-d',str(tree),str(p)])
    return p
factory=make(factory_tree,'factory.ext4');observed=make(observed_tree,'observed.ext4')
fd=os.open(observed,os.O_RDWR)
try:
    image.debug(fd,'ea_set /'+r.NO_CREDIT+' user.seed-policy without-credit',True)
    image.debug(fd,'ea_set /var/lib/muos-network/network.conf user.identity unchanged',True);os.fsync(fd)
finally:os.close(fd)
factory_sha,observed_sha=sha(factory),sha(observed)
backup=deepcopy(rows);backup[r.COUNTER].update({'sha256':r.hashed(b'72\n'),'bytes':3})
backup[r.CREDIT].update({'sha256':r.hashed(b'B'*256),'bytes':256})
attempt=r.attempt_record(backup,72,'a'*64,'b'*64,74,'c'*32)
context={'schema':85,'attempt_id':attempt['attempt_id'],'attempt_sha256':r.hashed(r.encoded(attempt)),
    'root_sha256':observed_sha,'root_bytes':size,'cid_sha256':r.DECK_CID,'capacity_sectors':r.CAPACITY,
    'offline':True,'all_namespaces_unmounted':True,'alias_cache_synchronized':True,'captured_after_handoff':True}
fresh=bytes(range(256))
def compose(name,rng=lambda n,f:fresh,ctx=context):
    return m.compose(factory,factory_sha,observed,observed_sha,size,folder(name),backup,72,'a'*64,attempt,ctx,rng)
def reject(name,call):
    try:call()
    except (ValueError,OSError):pass
    else:raise AssertionError(name)
    assert sha(factory)==factory_sha and sha(observed)==observed_sha
    passed(name)
result=compose('success')
with image.source_image(factory,factory_sha,size) as fd:base=m.initial.factory_scan(fd,folder('factory-scan'))
with image.source_image(observed,observed_sha,size) as fd:source=image.scan(fd,folder('observed-scan'))
out=stage/'success/candidate.ext4'
with image.source_image(out,result['candidate_sha256'],size) as fd:after=image.scan(fd,folder('candidate-scan'))
assert result['migration_counter']==76 and result['expected_first_C07_counter']==77 and result['root_fsck_exit']==0
assert after['payloads'][r.NO_CREDIT]==fresh and r.CREDIT not in after['private_files']
assert not result['physical_card_writer_available'] and not result['boot_handoff_authorized']
assert not (stage/'success/intermediate/candidate.ext4').exists() and (stage/'success/intermediate/consumed.json').exists()
passed('real-ext4-new-factory-public-tree-fresh-seed-counter76-next77')
assert after['tree']['etc/banner']['sha256']!=source['tree']['etc/banner']['sha256']
assert after['tree']['etc/banner-link']==base['etc/banner-link'] and after['attrs'][r.NO_CREDIT]==source['attrs'][r.NO_CREDIT]
assert sha(factory)==factory_sha and sha(observed)==observed_sha
passed('source-firmware-not-copied-identity-history-symlink-xattrs-and-inputs-preserved')
def eligible(candidate):return m.eligibility(base,source,candidate,backup,72,'a'*64,attempt,context,observed_sha,size)
for name,change in [
    ('public-mode-tamper',lambda x:x['tree']['etc/banner'].update({'mode':0o600})),
    ('stable-identity-tamper',lambda x:x['payloads'].update({'var/lib/muos-network/network.conf':b'changed'})),
    ('counter-not-reserved',lambda x:x.update({'boot_sequence':75})),
    ('old-seed-reused',lambda x:x['payloads'].update({r.NO_CREDIT:b'O'*256})),
    ('credit-seed-retained',lambda x:x['payloads'].update({r.CREDIT:b'X'*256})),
    ('historical-marker-missing',lambda x:x['tree'].pop('var/lib/muos-diagnostic/c25.used.BOOT0064')),
    ('private-directory-world-writable',lambda x:x['tree']['var/lib/muos-network'].update({'mode':0o777})),
    ('seed-xattr-tamper',lambda x:x['attrs'][r.NO_CREDIT].update({'user.seed-policy':b'changed'}))]:
    value=deepcopy(after);change(value);reject(name,lambda value=value:eligible(value))
for key,value in [('offline',False),('attempt_sha256','d'*64),('root_sha256','d'*64)]:
    ctx=deepcopy(context);ctx[key]=value;reject('capture-'+key,lambda ctx=ctx:compose('bad-'+key,ctx=ctx))
stale=deepcopy(source);stale['boot_sequence']=72
stale['payloads'][r.COUNTER]=b'72\n';stale['private_files'][r.COUNTER].update({'sha256':r.hashed(b'72\n'),'bytes':3})
reject('stale-counter72-below-current-handoff74',lambda:m.eligibility(base,stale,after,backup,72,'a'*64,attempt,context,observed_sha,size))
def unavailable(n,flags):assert flags==os.GRND_NONBLOCK;raise BlockingIOError(errno.EAGAIN,'not ready')
for name,rng in [('unready-RNG-no-fallback',unavailable),('short-RNG-no-retry',lambda n,f:b'x'),('old-RNG-result',lambda n,f:b'O'*256)]:
    reject(name,lambda name=name,rng=rng:compose(name,rng))
    assert not (stage/name/'candidate.ext4').exists() and not (stage/name/'analysis.json').exists()
def interrupted(source_fd,target,size):raise OSError('interrupted regular clone')
with patch.object(image,'sparse_clone',interrupted):reject('interrupted-clone-no-completion',lambda:compose('clone-failure'))
debug=image.debug
def fail_seed_write(fd,command,*args):
    if command.startswith('write ') and 'fresh-payload-1.dat' in command:raise OSError('partial seed replacement')
    return debug(fd,command,*args)
with patch.object(image,'debug',fail_seed_write):reject('partial-seed-replacement-no-completion',lambda:compose('patch-failure'))
for name in ['clone-failure','patch-failure']:
    assert not (stage/name/'analysis.json').exists()
calls=[]
reject('partial-stage-refused-before-another-RNG-call',lambda:m.compose(factory,factory_sha,observed,observed_sha,size,stage/'clone-failure',backup,72,'a'*64,attempt,context,rng=lambda n,f:calls.append('RNG')))
assert not calls
symlink=folder('existing-symlink');(symlink/'candidate.ext4').symlink_to(factory)
reject('output-symlink-never-replaced',lambda:m.compose(factory,factory_sha,observed,observed_sha,size,symlink,backup,72,'a'*64,attempt,context))
(symlink/'candidate.ext4').unlink()
reject('completed-stage-not-reused',lambda:m.compose(factory,factory_sha,observed,observed_sha,size,stage/'success',backup,72,'a'*64,attempt,context))
# Test images are disposable; retain receipts/scans, not another set of large files.
for path in stage.rglob('*.ext4'):path.unlink()
(stage/'fixture-results.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'synthetic_32MiB_ext4_only':True,'C88_intermediate_and_C84_policy_reused':True})+'\n')
