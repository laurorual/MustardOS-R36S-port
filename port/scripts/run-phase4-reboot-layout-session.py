#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C104 explicitly observed next-boot instance of the frozen C77 caller."""
from phase4_reboot_layout_session import rendered_runner

if __name__=='__main__':
    exec(compile(rendered_runner(),__file__,'exec'),globals())
