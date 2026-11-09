#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C116 real native receipts and sampled timing; no device operation."""
from phase4_resident_boot_session import REPO,proof,change
if __name__=='__main__':
    source=REPO/'port/scripts/analyze-phase4-prepared-capsule-session.py'
    assert source.read_bytes()==(proof('prepared-capsule-session')/'source'/source.relative_to(REPO)).read_bytes()
    text=change(source.read_text(),"repo/'build/phase4/prepared-capsule-session'","repo/'build/phase4/resident-boot-session'")
    text=change(text,'C109_local_preparation_analyzed','C116_resident_preparation_analyzed')
    exec(compile(text,__file__,'exec'),globals())
