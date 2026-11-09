#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C119 sanitized adoption proof; run/launch qualification remains separate."""
from phase4_batch_caller import REPO,session,require
if __name__=='__main__':
    source=REPO/'port/scripts/package-phase4-launch-profile.py'
    require(source.read_bytes()==(session.proof('launch-profile')/'source'/source.relative_to(REPO)).read_bytes(),'Frozen C117 publisher')
    text=session.change(source.read_text(),'import phase4_launch_profile as m','import phase4_batch_caller as m')
    for old,new in [("'dist/phase4/launch-profile'","'dist/phase4/batch-caller'"),
                    ("'docs/analysis/phase4-launch-profile.md'","'docs/analysis/phase4-batch-caller.md'"),
                    ("m.session.proof('resident-boot-session')","m.session.proof('batch-validation')"),
                    ("'prepare','validate','profile'","'prepare','bundle','contract-check','validate','adopt','refusals','profile'"),
                    ("p.suffix in {'.py','.md','.json'}","p.suffix in {'.py','.sh','.md','.json'}")]:
        text=session.change(text,old,new)
    text=text.replace('C117','C119').replace("r['schema']==117","r['schema']==119").replace('C116_analysis_sha256','C118_analysis_sha256')
    exec(compile(text,__file__,'exec'),globals())
