#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C115 closure of authentic session receipts; no new device operation."""
from phase4_resident_session import REPO,proof,require
if __name__=='__main__':
 source=REPO/'port/scripts/finish-phase4-installed-core-session.py'
 require(source.read_bytes()==(proof('installed-core-session')/'source'/source.relative_to(REPO)).read_bytes(),'Frozen closure')
 text=source.read_text();require(text.count('from phase4_installed_core_session import ')==1,'Finite C115 closure')
 exec(compile(text.replace('from phase4_installed_core_session import ','from phase4_resident_session import '),__file__,'exec'),globals())
