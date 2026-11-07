#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C89 derive write eligibility from real qualified C85 regular images."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import os,sys,types
sys.path.insert(0,'/port/scripts')
import phase4_p2_recovery as c
import phase4_recovery_image as image
import phase4_root_recovery as r
from phase4_backup_core import sha

stage=Path(sys.argv[1]);fixture=Path(sys.argv[2]);os.umask(0o077)
size=32*1024*1024;backup=fixture/'backup.ext4';current=fixture/'observed.ext4';candidate=fixture/'composition/recovery.ext4'
def folder(name):p=stage/name;p.mkdir(mode=0o700);return p
def scan(path,name,mode=0o755):
    with image.source_image(path,sha(path),size) as fd:return image.scan(fd,folder(name),mode)
base=scan(backup,'base',0o777);observed=scan(current,'observed');after=scan(candidate,'candidate')
fence=r.attempt_record(base['private_files'],72,sha(backup),r.hashed(b'candidate fixture'),72,'f'*32)
context={'schema':85,'attempt_id':fence['attempt_id'],'attempt_sha256':r.hashed(r.encoded(fence)),
    'root_sha256':sha(current),'root_bytes':size,'cid_sha256':r.DECK_CID,'capacity_sectors':r.CAPACITY,
    'offline':True,'all_namespaces_unmounted':True,'alias_cache_synchronized':True,'captured_after_handoff':True}
def eligible(candidate=after,obs=observed,ctx=context):return c.eligibility(base,obs,candidate,sha(backup),fence,ctx,sha(current),size)
def failed(name,call):
    try:call()
    except (ValueError,OSError):pass
    else:raise AssertionError(name)
    print('C89_PASS_'+name,flush=True)
assert eligible()['recovery_counter']==76
print('C89_PASS_actual-ext4-capture75-recovery76-no-credit-identity-history-and-xattrs',flush=True)
with image.source_image(candidate,sha(candidate),size) as source:
    plan=c.validate_fd(source,backup,sha(backup),current,sha(current),size,folder('validated-fd'),base['private_files'],72,sha(backup),fence,context)
    assert plan['recovery_counter']==76
print('C89_PASS_source-eligibility-derived-from-three-guarded-fd-scans',flush=True)
for name,mutate in [('public-inode-changed',lambda x:x['tree']['usr/share/normal'].update({'mode':0o600})),
    ('history-removed',lambda x:x['tree'].pop('var/lib/muos-diagnostic/c12.used')),
    ('identity-payload-changed',lambda x:x['payloads'].update({'var/lib/muos-network/network.conf':b'changed'})),
    ('counter-rewind',lambda x:x.update({'boot_sequence':72})),
    ('counter-bytes-changed',lambda x:x['payloads'].update({r.COUNTER:b'76'})),
    ('credit-seed-still-present',lambda x:(x['payloads'].update({r.CREDIT:base['payloads'][r.CREDIT]}),x['private_files'].update({r.CREDIT:base['private_files'][r.CREDIT]}))),
    ('missing-no-credit-seed',lambda x:x['payloads'].pop(r.NO_CREDIT)),
    ('short-no-credit-seed',lambda x:x['payloads'].update({r.NO_CREDIT:b'x'*64})),
    ('seed-xattrs-lost',lambda x:x['attrs'].update({r.NO_CREDIT:{}}))]:
    bad=deepcopy(after);mutate(bad);failed(name,lambda bad=bad:eligible(candidate=bad))
bad=deepcopy(observed);seed=after['payloads'][r.NO_CREDIT]
bad['payloads'][r.CREDIT]=seed;bad['private_files'][r.CREDIT]={'sha256':r.hashed(seed),'mode':0o400,'uid':0,'gid':0,'links':1,'bytes':len(seed)}
failed('same-seed-as-observed-credit-refused',lambda:eligible(obs=bad))
for key,value in [('offline',False),('captured_after_handoff',False),('cid_sha256','0'*64),('attempt_sha256','0'*64),('root_sha256','0'*64)]:
    bad=dict(context);bad[key]=value;failed('capture-'+key,lambda bad=bad:eligible(ctx=bad))

with patch.object(c.os,'geteuid',return_value=1000):failed('card-adapter-local-root-before-any-IO',lambda:c.card_target(None,None,None,None))
sysroot=folder('fake-sys');names=[('mmcblk0',r.CAPACITY),('mmcblk0p1',204800),('mmcblk0p2',1048576),('mmcblk0p3',248561664)]
for n,(name,sectors) in enumerate(names):
    p=sysroot/name;p.mkdir();(p/'size').write_text(str(sectors));(p/'dev').write_text('179:'+str(n))
events=[];guard=types.SimpleNamespace(SYS=sysroot,numbers=lambda:{'179:0','179:1','179:2','179:3'},run=lambda a:types.SimpleNamespace(stdout='ext4 8:1\n'))
capture=types.SimpleNamespace(read_protection=lambda g,ctx:events.append('guarded-identity'))
target=c.card_target(guard,capture,{},folder('journal'))
assert len(target.aliases)==4 and str(target.aliases[0][0])=='/dev/mmcblk0' and target.capacity==r.CAPACITY*512 and events
print('C89_PASS_adapter-fixed-test128-paths-size-rdev-and-offcard-journal',flush=True)
(sysroot/'mmcblk0p3/size').write_text('32768')
failed('card-adapter-refuses-other-p3-geometry',lambda:c.card_target(guard,capture,{},folder('bad-journal')))
guard.run=lambda a:types.SimpleNamespace(stdout='ext4 179:3\n')
failed('card-adapter-refuses-journal-on-card',lambda:c.card_target(guard,capture,{},folder('oncard-journal')))
