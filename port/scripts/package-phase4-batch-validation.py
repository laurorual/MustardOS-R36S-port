#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C118 sanitized acceptance/performance proof, not launch integration."""
from phase4_batch_validation import REPO,session,require
if __name__=='__main__':
    source=REPO/'port/scripts/package-phase4-launch-profile.py'
    require(source.read_bytes()==(session.proof('launch-profile')/'source'/source.relative_to(REPO)).read_bytes(),'Frozen C117 publisher')
    text=session.change(source.read_text(),'import phase4_launch_profile as m','import phase4_batch_validation as m')
    for old,new in [("'dist/phase4/launch-profile'","'dist/phase4/batch-validation'"),
                    ("'docs/archive/phase4/phase4-launch-profile.md'","'docs/archive/phase4/phase4-batch-validation.md'"),
                    ("m.session.proof('resident-boot-session')","m.session.proof('launch-profile')"),
                    ("'prepare','validate','profile'","'prepare','prototype','validate','profile'")]:
        text=session.change(text,old,new)
    text=text.replace('C117','C118').replace("r['schema']==117","r['schema']==118").replace('C116_analysis_sha256','C117_analysis_sha256')
    exec(compile(text,__file__,'exec'),globals())
