#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C110 actual installed-mode regression plus original preparation/transaction suite."""
from phase4_capsule_prepare_v2 import REPO,base,require
if __name__=='__main__':
    source=REPO/'port/scripts/check-phase4-capsule-prepare.py'
    require(source.read_bytes()==(base.proof('capsule-preparer-installed')/'source'/source.relative_to(REPO)).read_bytes(),'Frozen C107 checker')
    text=source.read_text().replace('from phase4_capsule_prepare import *','from phase4_capsule_prepare_v2 import *')
    text=text.replace('phase4-capsule-prepare-fixture.py','phase4-capsule-prepare-v2-fixture.py')
    text=text.replace('C107','C110').replace('C108','C110').replace('schema=107','schema=110')
    exec(compile(text,__file__,'exec'),globals())
