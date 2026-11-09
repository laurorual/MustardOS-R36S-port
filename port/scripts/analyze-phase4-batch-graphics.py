#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C121 later real-session analysis; no SSH and no physical quality inference."""
from phase4_batch_graphics import REPO,session,proof
if __name__=='__main__':
    source=REPO/'port/scripts/analyze-phase4-prepared-capsule-session.py'
    assert source.read_bytes()==(proof('prepared-capsule-session')/'source'/source.relative_to(REPO)).read_bytes()
    text=session.change(source.read_text(),"repo/'build/phase4/prepared-capsule-session'","repo/'build/phase4/batch-graphics'")
    text=session.change(text,'C109_local_preparation_analyzed','C121_batch_graphics_analyzed')
    exec(compile(text,__file__,'exec'),globals())
