#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C90 readiness receipt must exclude payload writes / boot / seed actions."""
from pathlib import Path
from copy import deepcopy
import ast,importlib,json,os,tempfile
from phase4_backup_core import sha

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/card-readiness';os.umask(0o077)
stage=Path(tempfile.mkdtemp(prefix='transport-checks.',dir=area));cases=[]
c=importlib.import_module('collect-phase4-p2-card-readiness');manifest={'files':{'fixture.py':'1'*64}}
report={'passed':True,'schema':90,'operation':'card-readiness-no-payload','kernel':'fixture','source_sha256':manifest['files']}
true=['exclusive_RDWR_opened_without_payload_write','whole_and_p2_transient_kernel_SETRO0','all_four_aliases_kernel_readonly',
    'p1_p3_readonly_during_transition','p2_512MiB_triple_hash_matches_C86','MBR_and_16MiB_boot_prefix_triple_verified']
false=['p3_full_content_hashed','physical_device_payload_written','candidate_provisioned_to_media','boot_handoff_authorized','seed_generated_or_loaded','handoff_fence_created']
for n in true:report[n]=True
for n in false:report[n]=False
journal={'unlock-intent':{'kind':'CARD_READINESS_UNLOCK_MAY_HAVE_STARTED','device_payload_write_allowed':False,'p1_p3_must_remain_readonly':True},
    'complete':{'kind':'CARD_READINESS_VERIFIED','exclusive_RDWR_opened_without_payload_write':True,'all_four_aliases_kernel_readonly':True,
        'p1_p3_readonly_during_transition':True,'p2_and_MBR_and_boot_prefix_unchanged':True,'physical_device_payload_written':False,'boot_handoff_authorized':False}}
c.validate(report,journal,manifest,'fixture');cases.append('no-payload-native-journal-and-reviewed-source-accepted')
def reject(name,call):
    try:call()
    except ValueError:cases.append(name)
    else:raise AssertionError(name)
for name in true+false:
    bad=deepcopy(report);bad[name]=not bad[name];reject('receipt-'+name,lambda bad=bad:c.validate(bad,journal,manifest,'fixture'))
for key,value in [('kernel','other'),('source_sha256',{}),('operation','recover-p2-only')]:
    bad=deepcopy(report);bad[key]=value;reject('receipt-'+key,lambda bad=bad:c.validate(bad,journal,manifest,'fixture'))
for name,change in [('unexpected-write-intent',lambda j:j.update({'write-intent':{}})),
    ('unlock-payload-permission',lambda j:j['unlock-intent'].update({'device_payload_write_allowed':True})),
    ('completion-without-RO',lambda j:j['complete'].update({'all_four_aliases_kernel_readonly':False}))]:
    bad=deepcopy(journal);change(bad);reject(name,lambda bad=bad:c.validate(report,bad,manifest,'fixture'))
ast.parse(c.READ)
sources=[Path(__file__),repo/'port/scripts/prepare-phase4-p2-card-readiness.py',repo/'port/scripts/collect-phase4-p2-card-readiness.py']
for p in sources:ast.parse(p.read_text())
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,'physical_device_or_network_contacted':False,
    'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-transport-checks').write_text(str(stage)+'\n');print('C90 transport:',len(cases),'checks passed:',stage)
