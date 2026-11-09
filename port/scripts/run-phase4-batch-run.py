#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C120 bounded load-only menu/game/return through versioned RAM contract."""
import os,sys
from phase4_batch_run import rendered_runner,require
if __name__=='__main__':
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            require('/port/roms/' not in os.fsdecode(args[0]),'C120 cannot open host ROM')
    sys.addaudithook(audit)
    exec(compile(rendered_runner(),__file__,'exec'),globals())
