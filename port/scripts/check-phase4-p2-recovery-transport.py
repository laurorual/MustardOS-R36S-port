#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C89 collector failures and no-postboot gate. No SSH, sudo or device IO."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import ast,importlib,json,os,tempfile
from phase4_backup_core import sha
from phase4_root_migration import ROOT_OFFSET,ROOT_BYTES
import phase4_root_recovery as r

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/p2-recovery';os.umask(0o077)
stage=Path(tempfile.mkdtemp(prefix='transport-checks.',dir=area));cases=[]
prepare=importlib.import_module('prepare-phase4-p2-recovery');collector=importlib.import_module('collect-phase4-p2-recovery')
def reject(name,call):
    try:call()
    except (ValueError,RuntimeError,OSError):cases.append(name)
    else:raise AssertionError(name)
rows={n:{'sha256':r.hashed(b'72\n' if n==r.COUNTER else b'x'*64),'bytes':3 if n==r.COUNTER else 64,
    'mode':0o400 if n==r.CREDIT else 0o644 if n.startswith('etc/') else 0o600,'uid':0,'gid':0,'links':1} for n in r.PRIVATE_FILES}
ctx={'recovery_sha256':'a'*64,'expected_observed_sha256':'b'*64,'expected_recovery_counter':74,'next_attempt_id':'c'*32,
    'physical_capture':{'backup_private_files':rows,'backup_counter':72,'backup_prefix_sha256':'d'*64,'attempt_sha256':'e'*64}}
intent=r.attempt_record(rows,72,'d'*64,'a'*64,74,'c'*32);manifest={'files':{'source.py':'1'*64}}
report={'passed':True,'schema':89,'operation':'recover-p2-only','source_sha256':manifest['files'],'written_bytes':ROOT_BYTES,
    'recovery_sha256':'a'*64,'recovery_counter':74,'next_attempt_id':'c'*32,'next_attempt_sha256':r.hashed(r.encoded(intent)),
    'prior_attempt_sha256':'e'*64,'boot_handoff_authorized':False}
for n in ['physical_card_p2_written','p1_MBR_p3_full_complement_preserved','all_four_aliases_kernel_readonly',
    'fresh_capture_and_three_image_scans_verified','new_no_credit_seed_verified_not_loaded','independent_host_copy_of_next_fence_required']:report[n]=True
unlock={'kind':'P2_UNLOCK_MAY_HAVE_STARTED','source_sha256':'a'*64,'previous_sha256':'b'*64,
    'protected_sha256':['2'*64,'3'*64],'offset':ROOT_OFFSET,'bytes':ROOT_BYTES}
write={k:v for k,v in unlock.items() if k!='protected_sha256'};write['kind']='P2_WRITE_MAY_HAVE_STARTED'
done={'kind':'P2_WRITE_VERIFIED','sha256':'a'*64,'offset':ROOT_OFFSET,'bytes':ROOT_BYTES,'boot_handoff_authorized':False,
    'all_four_aliases_kernel_readonly':True,'alias_cache_synchronized':True,'protected_complement_verified':True}
journal={'unlock-intent':unlock,'write-intent':write,'complete':done}
collector.validate(report,ctx,manifest,journal,intent);cases.append('native-recovery-journal-and-new-fence-bound')
for key,value in [('schema',88),('operation','initial'),('source_sha256',{}),('written_bytes',True),('recovery_counter',73),
    ('physical_card_p2_written',False),('p1_MBR_p3_full_complement_preserved',False),('all_four_aliases_kernel_readonly',False),
    ('new_no_credit_seed_verified_not_loaded',False),('boot_handoff_authorized',True),('prior_attempt_sha256','0'*64),('next_attempt_sha256','0'*64)]:
    bad=deepcopy(report);bad[key]=value;reject('native-'+key,lambda bad=bad:collector.validate(bad,ctx,manifest,journal,intent))
for name,change in [('missing-complete',lambda x:x.pop('complete')),('wrong-offset',lambda x:x['complete'].update({'offset':0})),
    ('wrong-current-p2',lambda x:x['write-intent'].update({'previous_sha256':'0'*64})),
    ('missing-protected-complement',lambda x:x['unlock-intent'].update({'protected_sha256':[]})),
    ('no-cold-readback',lambda x:x['complete'].update({'alias_cache_synchronized':False}))]:
    bad=deepcopy(journal);change(bad);reject('journal-'+name,lambda bad=bad:collector.validate(report,ctx,manifest,bad,intent))
bad=deepcopy(intent);bad['counter_floor']=73
reject('next-fence-counter-rewind',lambda:collector.validate(report,ctx,manifest,journal,bad))

empty=stage/'empty-work';empty.mkdir(mode=0o700)
with patch.object(prepare,'WORK',empty),patch.object(prepare.prep.prep,'transport',side_effect=AssertionError('must not contact Deck')):
    reject('missing-physical-capture-blocks-before-SSH-or-staging',lambda:prepare.main('192.0.2.1'))
    capture=empty/'physical-capture';capture.mkdir();fake=capture/'fake';fake.mkdir()
    (capture/'latest-complete-postboot').write_text(str(fake)+'\n')
    (fake/'analysis.json').write_text('{}')
    (fake/'host-copy.json').write_text(json.dumps({'passed':True,'mode':'reference','physical_postboot_validated':False}))
    reject('reference-cannot-authorize-postboot-writer',prepare.require_postboot)
    (fake/'host-copy.json').write_text(json.dumps({'passed':True,'mode':'postboot','physical_postboot_validated':True,'independent_C85_scan_verified':False}))
    reject('non-independent-capture-cannot-authorize-writer',prepare.require_postboot)
for code in [collector.FETCH]:ast.parse(code)
sources=[Path(__file__),repo/'port/scripts/prepare-phase4-p2-recovery.py',repo/'port/scripts/collect-phase4-p2-recovery.py',
    repo/'port/scripts/stage-phase4-initial-image.py']
for p in sources:ast.parse(p.read_text())
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'physical_device_or_network_contacted':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-transport-checks').write_text(str(stage)+'\n');print('C89 transport:',len(cases),'checks passed:',stage)
