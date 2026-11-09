#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C116 supervised, bounded resident menu/game/return; no host ROM access."""
import os,sys
from phase4_resident_boot_session import rendered_runner,require
if __name__=='__main__':
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            require('/port/roms/' not in os.fsdecode(args[0]),'C116 cannot read local ROM input')
    sys.addaudithook(audit)
    exec(compile(rendered_runner(),__file__,'exec'),globals())
