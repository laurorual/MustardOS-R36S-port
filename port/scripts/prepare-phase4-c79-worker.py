#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Derive a RAM-only /etc isolation adjustment without editing the C77 worker."""
import ast,subprocess
from phase4_c79_session import REPO,legacy
from phase4_root_migration import require

if __name__=='__main__':
    context,*_=legacy.historical()
    worker=context['worker'];text=worker.read_text()
    changes={
        'session_prepare > "$state/prepare.log" 2>&1':
            '. "$dir/etc-view.sh"\nsession_c79_etc_prepare\nsession_prepare > "$state/prepare.log" 2>&1',
        '    sha256sum "$path" >> "$state/writer-original.sha256"':
            '    # The original C79 /etc/asound.conf is absent; verify absence after unmount.\n    [ "$path" = /etc/asound.conf ] || sha256sum "$path" >> "$state/writer-original.sha256"',
        '        session_restore > "$state/restore.log" 2>&1 || cleanup=1':
            '        session_restore > "$state/restore.log" 2>&1 || cleanup=1\n        [ ! -e /etc/asound.conf ] && [ ! -L /etc/asound.conf ] || cleanup=1\n        [ ! -e /mnt/mmc ] && [ ! -L /mnt/mmc ] || cleanup=1',
    }
    for old,new in changes.items():
        require(text.count(old)==1,'Finite C79 worker adaptation anchor');text=text.replace(old,new)
    target=REPO/'port/device/rk-r35s-p0/c79-session/worker.sh'
    subprocess.run(['sh','-n'],input=text,text=True,check=True)
    target.write_text(text)
    print('C99 private /etc worker prepared; original worker unchanged')
