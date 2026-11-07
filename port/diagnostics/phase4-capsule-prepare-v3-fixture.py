#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C111 mode regression plus the actual installed staged callback."""
from pathlib import Path
source=Path('/port/diagnostics/phase4-capsule-prepare-fixture.py').read_text()
anchor=" 'installed-library-changed':lambda:(root/'opt/muos/frontend/lib/libui.so').write_bytes(b'bad'),"
assert source.count(anchor)==1
source=source.replace(anchor,anchor+"\n 'installed-library-executable-mode':lambda:(root/'opt/muos/frontend/lib/libui.so').chmod(0o755),")
source=source.replace('muos-capsule','muos-capsule-v3').replace('c108','c111').replace('C108','C111')
anchor="sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()"
source=source.replace(anchor,anchor+"\nassert all(row.split()[1]=='644' for row in (globals()['source']/'assets.tsv').read_text().splitlines() if row.split()[3].startswith('opt/'))")
anchor='# Run the actual derived transaction'
assert source.count(anchor)==1
addition=r'''
# Exercise the actual entry callback, rather than mocking its dispatch.
entry=(source/'prepare.sh').read_text()
native_callback=entry[entry.index('capsule_exec() {'):entry.index('\ncase "${1:-}:$#"')]
native_callback=native_callback.replace('. /usr/libexec/muos-caller/functions.sh','. '+str(caller/'functions.sh'))
native_callback=native_callback.replace('caller_system_root=/;caller_root=/usr/libexec/muos-caller',
    'caller_system_root='+str(root)+';caller_root='+str(caller))
native_callback=native_callback.replace('cat /var/lib/muos-diagnostic/boot-seq /proc/sys/kernel/random/boot_id',
    "printf '81\\nfixture-UUID\\n'")
invoke('actual-staged-callback-tmpfs-and-boot', 'capsule_prepare "$3"\n'+native_callback+'\ncapsule_exec staged "$3"')
'''
addition=addition.replace(chr(92)*2,chr(92))
source=source.replace(anchor,addition+anchor)
exec(compile(source,__file__+'-derived','exec'),{'__file__':__file__})
