#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C89 observer failures: synthetic status only, no SSH, media or subprocess."""
from pathlib import Path
from copy import deepcopy
import ast,importlib,json,os,tempfile
from phase4_backup_core import sha
from phase4_root_migration import DECK_CID,CAPACITY

os.umask(0o077);repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/p2-recovery'
stage=Path(tempfile.mkdtemp(prefix='watch-checks.',dir=area));watch=importlib.import_module('watch-phase4-p2-recovery');cases=[]
context={'qualified_kernel':'fixture','physical_capture':{'automount_guard_sha256':'a'*64}}
helper='muos-r35s-c89.abcdefgh'
base={'cid_sha256':DECK_CID,'capacity_sectors':CAPACITY,'kernel':'fixture','guard_sha256':'a'*64,
    'ro':[1,1,1,1],'root_helpers':[helper],'owned_complete':False,'failures':[],
    'read_bytes':1024,'write_bytes':0}
assert watch.state_action(base,helper,context)=='wait';cases.append('running-readonly-attempt-waits')
rw=deepcopy(base);rw['ro']=[0,1,0,1];assert watch.state_action(rw,helper,context)=='wait';cases.append('writer-transition-observed-without-changing-protection')
done=deepcopy(base);done.update({'owned_complete':True,'root_helpers':[]})
for name,change in [('wrong-card',{'cid_sha256':'b'*64}),('wrong-capacity',{'capacity_sectors':1}),
    ('wrong-kernel',{'kernel':'other'}),('wrong-guard',{'guard_sha256':'b'*64}),
    ('p3-writable',{'ro':[0,1,0,0]}),('failure-report',{'failures':['partial']}),
    ('helper-disappeared',{'root_helpers':[]}),('unrelated-helper',{'root_helpers':['other']}),
    ('early-completion',{'owned_complete':True})]:
    value=deepcopy(base);value.update(change)
    try:watch.state_action(value,helper,context)
    except ValueError:cases.append(name)
    else:raise AssertionError(name)
target=stage/'success';target.mkdir(mode=0o700);states=iter([base,rw,done]);calls=[];clock=[0]
def sleep(seconds):clock[0]+=seconds
watch.observe(target,lambda:next(states),lambda:calls.append('collect'),lambda:calls.append('proof'),helper,context,
    seconds=60,interval=1,now=lambda:clock[0],sleep=sleep)
assert calls==['collect','proof'] and (target/'complete.json').is_file();cases.append('collect-once-then-proof-with-durable-completion')
target=stage/'collector-failure';target.mkdir(mode=0o700);calls=[]
def failed():calls.append('collect');raise ValueError('partial collection')
try:watch.observe(target,lambda:done,failed,lambda:calls.append('proof'),helper,context)
except ValueError:pass
else:raise AssertionError('collector failure')
assert calls==['collect'] and not (target/'complete.json').exists();cases.append('collector-failure-never-retried-or-published')
target=stage/'timeout';target.mkdir(mode=0o700);calls=[];clock[0]=0
try:watch.observe(target,lambda:base,lambda:calls.append('collect'),lambda:calls.append('proof'),helper,context,
    seconds=1,interval=1,now=lambda:clock[0],sleep=sleep)
except ValueError:pass
else:raise AssertionError('timeout')
assert not calls and not (target/'complete.json').exists();cases.append('timeout-only-stops-observer')
target=stage/'ssh-failure';target.mkdir(mode=0o700)
def unavailable():raise OSError('SSH unavailable')
try:watch.observe(target,unavailable,lambda:calls.append('collect'),lambda:calls.append('proof'),helper,context)
except OSError:pass
else:raise AssertionError('SSH error')
assert not calls;cases.append('SSH-error-never-restarts-Deck-operation')
target=stage/'claim';target.mkdir(mode=0o700);watch.claim_observer(target)
assert (target/'watch-recover.claim').is_file();cases.append('durable-exclusive-claim-before-observation')
try:watch.claim_observer(target)
except FileExistsError:pass
else:raise AssertionError('observer duplicate')
cases.append('duplicate-or-interrupted-observer-cannot-collect-again-automatically')
ast.parse(watch.STATUS)
sources=[Path(__file__),repo/'port/scripts/watch-phase4-p2-recovery.py']
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'physical_device_or_network_contacted':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-watch-checks').write_text(str(stage)+'\n')
print('C89 observer:',len(cases),'checks passed:',stage)
