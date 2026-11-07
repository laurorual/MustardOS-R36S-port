#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Export pinned frontend/resources into build; never reuse Debian binaries."""
from pathlib import Path
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4/menu'
source = work / 'source'
assert (work / 'active').exists() and not source.exists()
revision = '5e8635b3b485eec9ad2ace141c415fd2df47d8f1'
archive = subprocess.check_output(['git', '-C', str(repo / 'refs/muos/frontend'), 'archive', revision], timeout=60)
(work / 'frontend-source.tar').write_bytes(archive)
source.mkdir()
with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
    stream.extractall(source, filter='data')
subprocess.run(['git', '-C', str(source), 'apply', str(repo / 'port/patches/0003-frontend-r35s-panel0-board.patch')], check=True)
for filename in ('phase4-menu.c',):
    shutil.copy2(repo / 'port/diagnostics' / filename, source / filename)
shutil.copy2(repo / 'port/packaging/phase4-menu.mk', source / 'phase4-menu.mk')
deps = work / 'deps'
deps.mkdir()
moji = repo / 'build/phase3/deps/mojibake-0.3.6.tar.gz'
assert hashlib.sha256(moji.read_bytes()).hexdigest() == '156bb5c0c1f1265c5d75f4ef53ff4aab09c368e358b05f4f780ba6ec2575fed3'
shutil.copy2(moji, deps / moji.name)
with tarfile.open(moji) as stream:
    stream.extractall(deps, filter='data')
(deps / 'include/mojibake').mkdir(parents=True)
for path in (deps / 'mojibake-0.3.6/src').glob('*.h'):
    shutil.copy2(path, deps / 'include/mojibake')

# Export the exact assets already catalogued in Phase 3, not its binaries or
# mutated diagnostic staging. Object reads use the separate cached Git DB.
assets = work / 'assets/opt/muos'
catalogue = json.loads((repo / 'build/phase3/asset-manifest.json').read_text())
cache = repo / 'build/phase3/deps/internal.git'
env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
for name, oid in catalogue['blobs'].items():
    data = subprocess.check_output(['git', '-C', str(cache), 'cat-file', 'blob', oid], env=env, timeout=20)
    assert hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest() == oid
    path = assets / ('device/config/' + name.removeprefix('device/common/config/') if name.startswith('device/common/config/') else name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
profile = json.loads((repo / 'port/device/rk-r35s-p0/staging-config.json').read_text())
for ns, values in profile.items():
    if ns not in ('device', 'global'):
        continue
    for name, value in values.items():
        path = assets / ('device/config' if ns == 'device' else 'config') / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value + '\n')
for name in ('kiosk', 'config/system', 'share/info/gamecontrollerdb'):
    (assets / name).mkdir(parents=True, exist_ok=True)
for layout in ('modern', 'retro'):
    (assets / 'share/info/gamecontrollerdb' / (layout + '.txt')).write_text('# Diagnostic mapping is generated from the actual virtual controller.\n')
inputs = ['port/diagnostics/phase4-menu.c', 'port/packaging/phase4-menu.mk',
          'port/scripts/prepare-phase4-menu.py', 'port/patches/0003-frontend-r35s-panel0-board.patch',
          'port/device/rk-r35s-p0/staging-config.json']
manifest = {'frontend_revision': revision, 'frontend_archive_sha256': hashlib.sha256(archive).hexdigest(),
            'internal_revision': catalogue['revision'], 'asset_blobs': catalogue['blobs'],
            'mojibake_sha256': hashlib.sha256(moji.read_bytes()).hexdigest(),
            'port_inputs': {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in inputs},
            'no_debian_binary_reuse': True, 'full_firmware_init': False}
(work / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Pinned frontend and resources exported; GPL/MIT/OFL notices retained; refs unchanged')
