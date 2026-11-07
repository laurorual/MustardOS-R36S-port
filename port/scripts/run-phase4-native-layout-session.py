#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C103 temporary installed-core caller, without the C99 directory views."""
from phase4_native_layout_session import rendered_runner

if __name__=='__main__':
    exec(compile(rendered_runner(),__file__,'exec'),globals())
