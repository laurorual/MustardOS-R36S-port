#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C99 close authentic C77 executor receipts using the additional C79 guard."""
from phase4_c79_session import REPO,proof
from phase4_root_migration import require

if __name__=='__main__':
    source=REPO/'port/scripts/finish-phase4-installed-core-session.py'
    frozen=proof('installed-core-session')/'source'/source.relative_to(REPO)
    require(source.read_bytes()==frozen.read_bytes(),'Frozen C77 closure source required')
    text=source.read_text();old='from phase4_installed_core_session import '
    require(text.count(old)==1,'Finite C99 closure adaptation')
    exec(compile(text.replace(old,'from phase4_c79_session import '),__file__,'exec'),globals())
