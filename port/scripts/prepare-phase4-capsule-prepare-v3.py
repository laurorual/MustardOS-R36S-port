#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C111 additive corrected-mode preparer; keep frozen C107/C108 intact."""
from phase4_capsule_prepare_v3 import REPO,base,require
if __name__=='__main__':
    source=REPO/'port/scripts/prepare-phase4-capsule-prepare.py'
    require(source.read_bytes()==(base.proof('capsule-preparer-installed')/'source'/source.relative_to(REPO)).read_bytes(),'Frozen C107 builder')
    text=source.read_text().replace('from phase4_capsule_prepare import *','from phase4_capsule_prepare_v3 import *')
    anchor="text=(NATIVE/'prepare.in.sh').read_text()"
    require(text.count(anchor)==1,'Finite entry prefix')
    text=text.replace(anchor,anchor+".replace('/usr/libexec/muos-capsule','/'+PREFIX)")
    text=text.replace('c108','c111').replace('C108','C111').replace('C107','C111').replace("'schema':107","'schema':111")
    callback='caller_exec() { case "$1" in boot)'
    require((REPO/'port/device/rk-r35s-p0/capsule-prepare/prepare.in.sh').read_text().count(callback)==1,'Known C107 staged callback')
    injection=anchor+".replace("+repr(callback)+", "+repr('caller_exec() { case "$1" in capsule) [ "$(findmnt -rn -T "$2" -o FSTYPE)" = tmpfs ];;boot)')+")"
    # Extend only the template rendering expression, not the frozen template.
    text=text.replace(anchor,injection)
    exec(compile(text,__file__,'exec'),globals())
