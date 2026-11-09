#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C116 close recorded receipts against their exact current-boot guard."""
from phase4_resident_boot_session import REPO,proof,change
if __name__=='__main__':
    source=REPO/'port/scripts/finish-phase4-installed-core-session.py'
    assert source.read_bytes()==(proof('installed-core-session')/'source'/source.relative_to(REPO)).read_bytes()
    text=change(source.read_text(),'from phase4_installed_core_session import ','from phase4_resident_boot_session import ')
    text=change(text,"current_common(context['common'], prior['boot_sequence'], r['boot_sequence'])",
                "current_common(context['common'], prior['boot_sequence'], r['boot_sequence'], r['kernel_boot_id'])")
    exec(compile(text,__file__,'exec'),globals())
