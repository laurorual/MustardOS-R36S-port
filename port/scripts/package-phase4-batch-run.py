#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C120 proof of contract tests/native check; graphical run explicitly pending."""
import ast
from phase4_batch_run import REPO,session,require
if __name__=='__main__':
    source=REPO/'port/scripts/package-phase4-launch-profile.py'
    require(source.read_bytes()==(session.proof('launch-profile')/'source'/source.relative_to(REPO)).read_bytes(),'Frozen publisher')
    text=session.change(source.read_text(),'import phase4_launch_profile as m','import phase4_batch_run as m')
    for old,new in [("'dist/phase4/launch-profile'","'dist/phase4/batch-run'"),
      ("'docs/archive/phase4/phase4-launch-profile.md'","'docs/archive/phase4/phase4-batch-run.md'"),
      ("m.session.proof('resident-boot-session')","m.session.proof('batch-caller')"),
      ("'prepare','validate','profile'","'prepare','bundle','contract-check','validate','adopt','refusals','profile'")]:text=session.change(text,old,new)
    text=text.replace('C117','C120').replace("r['schema']==117","r['schema']==120").replace('C116_analysis_sha256','C119_analysis_sha256')
    ast.parse(text);exec(compile(text,__file__,'exec'),globals())
