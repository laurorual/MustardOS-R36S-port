#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C110 preserve C107 cases and enforce the actual installed 0644 library mode."""
from pathlib import Path
source=Path('/port/diagnostics/phase4-capsule-prepare-fixture.py').read_text()
anchor=" 'installed-library-changed':lambda:(root/'opt/muos/frontend/lib/libui.so').write_bytes(b'bad'),"
assert source.count(anchor)==1
source=source.replace(anchor,anchor+"\n 'installed-library-executable-mode':lambda:(root/'opt/muos/frontend/lib/libui.so').chmod(0o755),")
source=source.replace('muos-capsule','muos-capsule-v2').replace('c108','c110').replace('C108','C110')
anchor="sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()"
source=source.replace(anchor,anchor+"\nassert all(row.split()[1]=='644' for row in (globals()['source']/'assets.tsv').read_text().splitlines() if row.split()[3].startswith('opt/'))")
# The initial source variable in the executed fixture is the package Path.
exec(compile(source,__file__+'-derived','exec'),{'__file__':__file__})
