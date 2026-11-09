#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C121 close authentic already-collected graphical receipts; never redispatch."""
from phase4_batch_graphics import REPO,session,proof
if __name__=='__main__':
    source=REPO/'port/scripts/finish-phase4-installed-core-session.py'
    assert source.read_bytes()==(proof('installed-core-session')/'source'/source.relative_to(REPO)).read_bytes()
    text=session.change(source.read_text(),'from phase4_installed_core_session import ','from phase4_batch_graphics import ')
    text=session.change(text,"current_common(context['common'], prior['boot_sequence'], r['boot_sequence'])",
      "current_common(context['common'], prior['boot_sequence'], r['boot_sequence'], r['kernel_boot_id'])")
    text=session.change(text,'stage = args.stage.resolve()',"stage = args.stage.resolve()\nassert stage.is_relative_to(WORK/'batch-graphics')")
    text=session.change(text,"assert r['passed'] and r['RAM_removed'] and r['cleanup_passed']",
      "assert r['schema']==121 and r['C121_graphical_provider_routing'] is True\nassert r['passed'] and r['RAM_removed'] and r['cleanup_passed']")
    exec(compile(text,__file__,'exec'),globals())
