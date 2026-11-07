#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Package proof records only. Do not distribute the unresolved Mali binary."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def session(pointer, target):
    source = Path(pointer.read_text().strip()).resolve()
    assert source.is_relative_to(work)
    assert (source / 'evidence/health-after.json').is_file()
    # Re-check archived data against the collector's checksums before copying.
    for line in (source / 'evidence-SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert sha(source / name) == digest, name
    for item in (source / 'evidence').rglob('*'):
        if item.is_file():
            assert item.suffix in ('.json', '.jsonl', '.txt', '.py', '.state', '.log', '.lock', '')
            if item.suffix == '.lock':
                assert item.stat().st_size == 0
            assert not item.read_bytes().startswith(b'\x7fELF'), 'No driver binary in proof package'
    shutil.copytree(source / 'evidence', target, dirs_exist_ok=True)
    shutil.copy2(source / 'evidence-SHA256SUMS', target.parent / (target.name + '-evidence-SHA256SUMS'))


def finish(out):
    with tarfile.open(out / 'port-source.tar.gz', 'w:gz') as archive:
        archive.add(repo / 'port', arcname='port', filter=lambda member:
                    None if '__pycache__' in member.name or member.name.endswith('.pyc') else member)
    with (out / 'SHA256SUMS').open('w') as sums:
        for path in sorted(out.rglob('*')):
            if path.is_file() and path.name != 'SHA256SUMS':
                sums.write(f'{sha(path)}  {path.relative_to(out)}\n')


input_result = read(work / 'core/input-capture-analysis.json')
assert input_result['pass']
out = repo / 'dist/phase4/core-input-native'
out.mkdir(parents=True, exist_ok=True)
session(work / 'core/latest-input-smoke', out / 'smoke')
session(work / 'core/latest-input-capture', out / 'capture')
shutil.copy2(work / 'core/input-capture-analysis.json', out / 'input-analysis.json')
shutil.copy2(work / 'core/input-sdk-macros.txt', out / 'input-sdk-macros.txt')
for name in ('input-smoke-run.log', 'input-capture-run.log'):
    shutil.copy2(work / 'core' / name, out / name)
record = {'scope': 'native uinput proof for the immutable core image',
          'base_image': '../core-native/rootfs.ext4',
          'base_image_sha256': sha(repo / 'dist/phase4/core-native/rootfs.ext4'),
          'core_staging_sha256': sha(repo / 'dist/phase4/core-native/core-staging.tar.gz'),
          'native_uinput_tested': True, 'input_sequence_passed': True,
          'physical_source_released': True, 'sdl_mapping_tested': False,
          'power_tested': False, 'firmware_boot_tested': False}
(out / 'build-manifest.json').write_text(json.dumps(record, indent=2) + '\n')
finish(out)

c = work / 'mali-r13'
r = read(c / 'native-display-result.json')
assert r['native_context_passed'] and r['native_display_passed'] and r['user_confirmed_display']
out = repo / 'dist/phase4/r13-runtime-diagnostic'
out.mkdir(parents=True, exist_ok=True)
session(c / 'latest-egl-context', out / 'context')
session(c / 'latest-graphics-r13', out / 'display')
for name in ('source-manifest.json', 'diagnostic-manifest.json', 'native-context-result.json',
             'native-display-result.json', 'native-context-run.log', 'native-display-run.log',
             'graphics-contract-qemu.txt', 'gbm-contract-qemu.txt', 'egl-context-loader-qemu.txt', 'libmali.elf.txt'):
    shutil.copy2(c / name, out / name)
if (c / 'final-device-state.txt').is_file():
    shutil.copy2(c / 'final-device-state.txt', out / 'final-device-state.txt')
(out / 'NO-DRIVER-OR-FIRMWARE.txt').write_text(
    'Proof records and port source only. No Mali binary, ZIP, staging or firmware image is included.\n'
    'The private runtime overlay passed on the installed kernel; redistribution terms remain unresolved.\n')
finish(out)
print('Packaged input and R13 proof records; no Mali driver or payload included in the R13 package')
