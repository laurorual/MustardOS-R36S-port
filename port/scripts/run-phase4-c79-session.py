#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C99 C79-bound instance of the frozen C77 temporary installed-core caller."""
from phase4_c79_session import rendered_runner

if __name__=='__main__':
    exec(compile(rendered_runner(),__file__,'exec'),globals())
