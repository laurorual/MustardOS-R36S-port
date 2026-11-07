#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C106 close recorded native receipts using the unchanged C77 audit."""
from phase4_installed_caller_session import REPO,proof
from phase4_root_migration import require

if __name__=='__main__':
    source=REPO/'port/scripts/finish-phase4-installed-core-session.py'
    require(source.read_bytes()==(proof('installed-core-session')/'source'/source.relative_to(REPO)).read_bytes(),
        'Frozen C77 closure')
    text=source.read_text();old='from phase4_installed_core_session import '
    require(text.count(old)==1,'Finite C106 closure adapter')
    exec(compile(text.replace(old,'from phase4_installed_caller_session import '),__file__,'exec'),globals())
