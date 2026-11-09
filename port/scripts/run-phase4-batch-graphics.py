#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C121 later supervised cycle; observes explicitly and never uploads host ROM."""
import os,sys
from phase4_batch_graphics import rendered_runner,require
if __name__=='__main__':
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            require('/port/roms/' not in os.fsdecode(args[0]),'C121 host ROM reads forbidden')
    sys.addaudithook(audit)
    exec(compile(rendered_runner(),__file__,'exec'),globals())
