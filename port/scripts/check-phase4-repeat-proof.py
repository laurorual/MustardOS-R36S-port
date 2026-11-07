#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check proof names and the forward-only repeat boundary without hardware."""
from pathlib import Path
import json
import tempfile
from phase4_candidate import sha
from phase4_repeat_proof import repeat_name

ref={'passed':True,'audio_passed':True,'direct_zero_PCM_priming':True,
     'experiment':'C37_PRIMED_LAUNCHER_BOOT','boot_sequence':62}
fallback={**ref,'boot_sequence':63}
trial={'experiment':ref['experiment'],'before_boot':63,'expected_boot':64,'expected_fallback':65}
cases=[]
assert repeat_name('primed-launcher','session',trial,ref,fallback)=='primed-launcher-boot-0064'
assert repeat_name('primed-launcher','fallback',trial,ref,fallback)=='primed-launcher-fallback-0065'
cases.extend(['session_uses_actual_boot','fallback_uses_actual_boot'])
for name, t, r, f in [
    ('original_trial_refused',{**trial,'before_boot':61,'expected_boot':62,'expected_fallback':63},ref,fallback),
    ('skipped_counter_refused',{**trial,'expected_boot':65},ref,fallback),
    ('wrong_fallback_refused',{**trial,'expected_fallback':66},ref,fallback),
    ('unqualified_reference_refused',trial,{**ref,'audio_passed':False},fallback),
    ('unqualified_fallback_refused',trial,ref,{**fallback,'passed':False}),
    ('wrong_experiment_refused',{**trial,'experiment':'C12'},ref,fallback),
]:
    try:repeat_name('primed-launcher','session',t,r,f)
    except AssertionError:cases.append(name)
    else:raise AssertionError(name)
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
stage=Path(tempfile.mkdtemp(prefix='repeat-proof-checks.',dir=area))
report={'passed':True,'cases':cases,'hardware_accessed':False,
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),Path(__file__).with_name('phase4_repeat_proof.py')]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-repeat-proof-checks').write_text(str(stage)+'\n')
print('Repeat proof checks passed:',len(cases),stage)
