#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C110 additive corrected-mode preparer; keep frozen C107/C108 intact."""
from phase4_capsule_prepare_v2 import REPO,base,require
if __name__=='__main__':
    source=REPO/'port/scripts/prepare-phase4-capsule-prepare.py'
    require(source.read_bytes()==(base.proof('capsule-preparer-installed')/'source'/source.relative_to(REPO)).read_bytes(),'Frozen C107 builder')
    text=source.read_text().replace('from phase4_capsule_prepare import *','from phase4_capsule_prepare_v2 import *')
    anchor="text=(NATIVE/'prepare.in.sh').read_text()"
    require(text.count(anchor)==1,'Finite entry prefix')
    text=text.replace(anchor,anchor+".replace('/usr/libexec/muos-capsule','/'+PREFIX)")
    text=text.replace('c108','c110').replace('C108','C110').replace('C107','C110').replace("'schema':107","'schema':110")
    exec(compile(text,__file__,'exec'),globals())
