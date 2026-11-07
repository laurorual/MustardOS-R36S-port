#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C115 bounded graphical session; run only when physical supervision resumes."""
import os,sys
from phase4_resident_session import rendered_runner
from phase4_root_migration import require
if __name__=='__main__':
 def audit(event,args):
  if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
   require('/port/roms/' not in os.fsdecode(args[0]),'C115 cannot read local ROM input')
 sys.addaudithook(audit)
 exec(compile(rendered_runner(),__file__,'exec'),globals())
