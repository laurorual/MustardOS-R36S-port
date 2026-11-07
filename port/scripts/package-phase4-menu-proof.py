#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Package frontend proof/source only; exclude private Mali and runtime image."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile

repo = Path(__file__).resolve().parents[2]
menu = repo / 'build/phase4/menu'
out = repo / 'dist/phase4/menu-native'
results = json.loads((menu / 'native-results.json').read_text())
assert results['video_user_confirmed'] and results['audio_user_confirmed'] and results['restore_regression_passed']
assert (menu / 'compile.exit').read_text().strip() == '0'
assert (menu / 'legal-info.exit').read_text().strip() == '0'
out.mkdir(parents=True, exist_ok=True)


def sha(p):
    with p.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


for label, pointer in [('initial-inspect','initial-inspect-session'),('video','latest-menu-video'),
                       ('audio','latest-menu-audio'),('restore-regression','latest-menu-inspect')]:
    work = Path((menu / pointer).read_text().strip()).resolve()
    assert work.is_relative_to(menu)
    for line in (work / 'evidence-SHA256SUMS').read_text().splitlines():
        digest, path = line.split('  ', 1)
        assert sha(work / path) == digest
    shutil.copytree(work / 'evidence', out / label, dirs_exist_ok=True)
for name in ['source-manifest.json','config-report.json','native-results.json','native-inspect.log',
             'native-video.log','native-audio.log','native-restore-regression.log',
             'phase4-menu','phase4-menu.elf.txt','menu-info-qemu.txt','menu.defconfig','compile.log']:
    shutil.copy2(menu / name, out / name)
stage = Path((menu / 'latest-staging').read_text().strip())
for name in ['staging-manifest.json','base-rootfs-audit.json','base-e2fsck.txt']:
    shutil.copy2(stage / name, out / name)
shutil.copy2(menu / 'frontend-source.tar', out / 'frontend-source.tar')
shutil.copy2(menu / 'deps/mojibake-0.3.6.tar.gz', out / 'mojibake-0.3.6.tar.gz')
shutil.copytree(menu / 'assets', out / 'assets', dirs_exist_ok=True)
# Dependency source material; the original Mali archive is already catalogued
# separately, and this proof must not bundle any Mali userspace binary.
legal = repo / 'build/phase4/graphics-config/output/legal-info'
shutil.copytree(legal, out / 'dependency-legal-info', dirs_exist_ok=True,
                ignore=lambda directory,names: [n for n in names if n.startswith('rockchip-mali-')])
(out / 'PRIVATE-RUNTIME-NOT-INCLUDED.txt').write_text(
    'Frontend proof, source, assets and dependency legal material only.\n'
    'No rootfs image, Hardkernel ZIP, Mali binary or runtime staging is included.\n'
    'The SDK/base-image Mali provider was not runtime-approved; the private R13 replacement remains subject to unresolved terms.\n'
    'The recorded audio restoration mismatch was repaired and a separate automatic regression passed.\n')
with tarfile.open(out / 'port-source.tar.gz', 'w:gz') as archive:
    archive.add(repo / 'port', arcname='port', filter=lambda m:
                None if '__pycache__' in m.name or m.name.endswith('.pyc') else m)
with (out / 'SHA256SUMS').open('w') as sums:
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.name != 'SHA256SUMS':
            sums.write(f'{sha(path)}  {path.relative_to(out)}\n')
print('Menu proof packaged without the private GPU runtime or firmware image')
