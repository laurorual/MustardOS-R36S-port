#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C89 handoff tests: real sealed host files, stubbed Deck evidence/transport."""
from pathlib import Path
from unittest.mock import patch
import importlib,json,os,tempfile,types
from phase4_backup_core import sha
import phase4_root_recovery as r

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/p2-recovery';os.umask(0o077)
stage=Path(tempfile.mkdtemp(prefix='handoff-checks.',dir=area));cases=[]
h=importlib.import_module('prepare-phase4-reference-handoff');root=stage/'work';root.mkdir(mode=0o700)
target=root/'p2-recovery';target.mkdir(mode=0o700)
for n in ['latest-checks','latest-entry-checks','latest-transport-checks']:
    p=target/n.replace('latest-','fixture-');p.mkdir();(p/'analysis.json').write_text(json.dumps({'passed':True,'source_sha256':{}}));(target/n).write_text(str(p)+'\n')
rows={n:{'sha256':r.hashed(b'72\n' if n==r.COUNTER else b'x'*64),'bytes':3 if n==r.COUNTER else 64,
    'mode':0o400 if n==r.CREDIT else 0o644 if n.startswith('etc/') else 0o600,'uid':0,'gid':0,'links':1} for n in r.PRIVATE_FILES}
ctx={'backup_private_files':rows,'backup_counter':72,'backup_prefix_sha256':'1'*64,'reference_root_sha256':'2'*64,'automount_guard_sha256':'3'*64}
ready=root/'card-readiness';ready.mkdir();copy=ready/'copy';copy.mkdir();package=ready/'package';(package/'bundle').mkdir(parents=True)
(copy/'analysis.json').write_text(json.dumps({'kernel':'fixture'}));(package/'bundle/context.json').write_text(json.dumps(ctx));(package/'bundle/package.json').write_text('{}')
(copy/'host-copy.json').write_text(json.dumps({'passed':True,'native_MMC_RO_transition_qualified_without_payload':True,
    'files':{'analysis.json':sha(copy/'analysis.json')},'package_manifest_sha256':sha(package/'bundle/package.json')}))
(ready/'latest-complete').write_text(str(copy)+'\n');(ready/'latest-package').write_text(str(package)+'\n')
calls=[];live={'kernel':'fixture','guard':'3'*64,'ro':{'whole':1,'p1':1,'p2':1,'p3':1}}
def native(host,code):calls.append(code);return {} if code=='INSPECT' else live
t=types.SimpleNamespace(native=native,INSPECT='INSPECT',validate_inspection=lambda value:None)
with patch.object(h,'AREA',target),patch.object(h,'WORK',root),patch.object(h,'sums',return_value={}),patch.object(h.prep,'context_from_reference',return_value=ctx),patch.object(h.prep.prep,'transport',return_value=t):
    h.main('192.0.2.1');result=Path((target/'latest-reference-handoff').read_text().strip());a=json.loads((result/'analysis.json').read_text())
    fence=r.load_attempt(Path(a['attempt_directory']),a['attempt_id'],a['attempt_sha256'])
    assert fence['candidate_root_sha256']=='2'*64 and fence['counter_floor']==72 and a['C88_candidate_selected'] is False
    assert a['boot_may_have_occurred'] is True and a['boot_success_assumed'] is False
    cases+=['real-canonical400-fence-fsync-and-pinned-load','current-reference-selected-with-counter72-never-C88','no-boot-success-or-card-write-assumed']
    before=len(calls)
    try:h.main('192.0.2.1')
    except ValueError:pass
    else:raise AssertionError('duplicate handoff')
    assert len(calls)==before;cases.append('existing-pointer-refuses-new-fence-before-SSH')
    (target/'latest-reference-handoff').unlink()
    try:h.main('192.0.2.1')
    except ValueError:pass
    else:raise AssertionError('orphan handoff replaced')
    assert len(calls)==before;cases.append('orphan-fence-refuses-new-ID-even-without-pointer')
sources=[Path(__file__),repo/'port/scripts/prepare-phase4-reference-handoff.py']
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'real_host_fence_synthetic_reference':True,'physical_device_or_network_contacted':False,
    'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-handoff-checks').write_text(str(stage)+'\n');print('C89 reference handoff:',len(cases),'checks passed:',stage)
