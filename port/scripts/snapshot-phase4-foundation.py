#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Archive proof/source without distributing the unresolved GPU runtime."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
f = work / 'foundation'
assert (f / 'audit.exit').read_text().strip() == '0'
stage = Path((f / 'latest-staging').read_text().strip())
native = Path((f / 'latest-native-storage').read_text().strip())
assert stage.parent == f and native.parent == f
manifest = json.loads((stage / 'staging-manifest.json').read_text())
result = json.loads((native / 'evidence/storage-native.json').read_text())
assert result['passed'] and result['incorrect_bind_identity_rejected']
assert (native / 'evidence/storage-cleanup.txt').exists()
assert json.loads((native / 'evidence/staging-manifest.json').read_text())['staging_sha256'] == manifest['staging_sha256']
log = (native / 'native-session.log').read_text()
assert 'PHASE4_CORE_WORKER_EXIT_STATUS=0' in log
assert 'not found' not in log and 'Traceback' not in log
out = repo / 'dist/phase4/private-foundation'
out.mkdir()  # Immutable checkpoint: do not overwrite a prior proof.
for name in ['provider-manifest.json', 'overlay-manifest.json', 'candidate.defconfig',
             'configure.log', 'provider.log', 'frontend-compile.log', 'busybox.log', 'image.log']:
    shutil.copy2(f / name, out / name)
shutil.copytree(f / 'audit', out / 'audit')
# The probes are original port code; the audit directory contains no Mali ELF.
shutil.copytree(native / 'evidence', out / 'native-storage')
shutil.copy2(native / 'native-session.log', out / 'native-session.log')
shutil.copytree(f / 'frontend-bin', out / 'frontend-bin')
shutil.copy2(stage / 'staging-manifest.json', out / 'staging-manifest.json')
shutil.copy2(work / 'graphics-config/output/.config', out / 'buildroot.config')
shutil.copy2(repo / 'port/packaging/pending-licenses.json', out / 'pending-licenses.json')
shutil.copy2(work / 'menu/frontend-source.tar', out / 'frontend-source.tar')
shutil.copy2(f / 'deps/mojibake-0.3.6.tar.gz', out / 'mojibake-0.3.6.tar.gz')
shutil.copy2(f / 'frontend-source/LICENSE', out / 'frontend-LICENSE')
shutil.copy2(f / 'deps/mojibake-0.3.6/LICENSE', out / 'mojibake-LICENSE')
with tarfile.open(out / 'port-source.tar.gz', 'w:gz') as archive:
    for p in sorted((repo / 'port').rglob('*')):
        if p.is_file() and '__pycache__' not in str(p) and p.suffix != '.pyc':
            archive.add(p, arcname=str(p.relative_to(repo)), recursive=False)
invalidated = []
for attempt in sorted(f.glob('native-storage.*/evidence/storage-native.json')):
    if attempt.parents[1] == native:
        continue
    attempt_log = attempt.parents[1] / 'native-session.log'
    if attempt_log.exists() and 'stat: not found' in attempt_log.read_text():
        invalidated.append({'session': attempt.parents[1].name,
                            'reason': 'missing stat and empty identity comparison; original status0 rejected'})
        shutil.copytree(attempt.parent, out / 'invalidated-initial-attempt')
        shutil.copy2(attempt_log, out / 'invalidated-initial-attempt.log')
record = {'scope': 'private foundation host/link and native storage proof',
          'staging': manifest, 'native_storage': result,
          'invalidated_attempts': invalidated, 'runtime_included': False,
          'redistribution_approved': False, 'firmware_boot_tested': False,
          'frontend_full_native_tested': False, 'native_session_cleaned': True}
(out / 'build-manifest.json').write_text(json.dumps(record, indent=2) + '\n')
(out / 'PRIVATE-NOT-FOR-DEVICE-BOOT.txt').write_text(
    'Private proof checkpoint; not a bootable firmware or standalone executable package.\n'
    'Unresolved GPU ZIP/provider ELF, rootfs image and RAM tar intentionally excluded.\n'
    'Compiled UI requires its own Buildroot libraries; no Debian ABI compatibility is assumed.\n'
    'Native storage used a tmpfs fixture, no block/input/audio/GPU nodes. No cold boot was performed.\n'
    'An initial status0 with missing stat is invalidated; use the final native-storage proof.\n'
    'Pending licenses are recorded for one consolidated Markdown at project completion.\n')
with (out / 'SHA256SUMS').open('w') as sums:
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.name != 'SHA256SUMS':
            with p.open('rb') as stream:
                sums.write(f'{hashlib.file_digest(stream, "sha256").hexdigest()}  {p.relative_to(out)}\n')
print('Immutable private proof/source checkpoint:', out)
