#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze an audited host checkpoint, excluding license-pending boot payloads."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile
import tempfile
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument('--name', default='uboot-sd-memory')
args = parser.parse_args()
assert re.fullmatch(r'uboot-sd-[a-z0-9-]+', args.name)

repo = Path(__file__).resolve().parents[2]
work = repo/'build/phase4'
stage = Path((work/'uboot-sd/latest-build').read_text().strip())
package = Path((stage/'latest-package').read_text().strip())
assert stage.is_relative_to(work/'uboot-sd') and package.is_relative_to(stage)
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
report = json.loads((stage/'audit/report.json').read_text())
pack = json.loads((package/'audit.json').read_text())
assert report['passed'] and pack['passed'] and report['panic_hangs_without_automatic_reset']
assert report['control_fdt_reserved_in_sysmem_and_bootm_lmb']
assert pack['manifest']['u_boot_audit_sha256'] == sha(stage/'audit/report.json')
assert pack['verifier_sha256'] == sha(repo/'port/scripts/verify-phase4-boot-package.py')
for name, digest in report['inputs']['port_inputs'].items():
    assert sha(repo/name) == digest, name
for name, digest in report['audit_port_inputs'].items():
    assert sha(repo/name) == digest, name
for name, digest in report['output_sha256'].items():
    assert sha(stage/'output'/name) == digest, name
for name, digest in pack['output_sha256'].items():
    assert sha(package/name) == digest, name
final_destination = repo/'dist/phase4'/args.name
assert not final_destination.exists(), 'Do not overwrite an immutable checkpoint'
for name in ['negative-checks.json', 'package-negative-checks.json']:
    assert (stage/name).is_file(), name
destination = Path(tempfile.mkdtemp(prefix='checkpoint.', dir=stage))
for name in report['output_sha256']:
    shutil.copy2(stage/'output'/name, destination/('uboot.config' if name == '.config' else name))
shutil.copy2(stage/'rk3326-muos-r35s-panel0-uboot.dtb', destination/'rk3326-muos-r35s-panel0-uboot.dtb')
shutil.copytree(stage/'audit', destination/'audit')
shutil.copytree(stage/'memory-audit', destination/'memory-audit')
for name in ['inputs.json', 'compiler.txt', 'build.log', 'configure.log', 'negative-checks.json', 'package-negative-checks.json']:
    shutil.copy2(stage/name, destination/name)
metadata = destination/'packaging'
metadata.mkdir()
for name in ['manifest.json', 'audit.json', 'RK3326TRUST.ini', 'idb-pack.log', 'uboot-pack.log', 'trust-pack.log']:
    shutil.copy2(package/name, metadata/name)
for name in ['Licenses/README', 'Licenses/gpl-2.0.txt']:
    shutil.copy2(stage/'source'/name, destination/('LICENSE-README' if name.endswith('README') else 'COPYING.GPL2'))
shutil.copy2(repo/'port/packaging/pending-licenses.json', destination/'pending-licenses.json')
inputs = set(report['inputs']['port_inputs']) | set(report['audit_port_inputs'])
inputs |= set(report['native_allocator_host_fixture']['port_inputs'])
inputs |= {str(p.relative_to(repo)) for p in [Path(__file__), repo/'port/scripts/package-phase4-uboot-sd.py',
           repo/'port/scripts/check-phase4-uboot-negative.py',
           repo/'port/scripts/verify-phase4-boot-package.py', repo/'port/scripts/verify-phase4-dtb.py']}
with tarfile.open(destination/'port-source.tar.gz', 'w:gz') as archive:
    for name in sorted(inputs):
        archive.add(repo/name, arcname=name, recursive=False)
(destination/'checkpoint.json').write_text(json.dumps({
    'scope': 'host U-Boot executable/display proof; not a flashable media image',
    'private_candidate': True, 'build_directory': str(stage.relative_to(repo)),
    'private_package_directory': str(package.relative_to(repo)),
    'port_source_sha256': {name: sha(repo/name) for name in sorted(inputs)},
    'vendor_payloads_and_containers_excluded': True, 'boot_tested': False,
    'automatic_boot': report['automatic_boot'], 'panic_hangs': True,
    'control_fdt_reserved_in_both_allocators': True,
    'trust_matches_installed_reference': pack['trust_matches_installed_reference']}, indent=2)+'\n')
(destination/'NOT-A-MEDIA-IMAGE.txt').write_text(
    'Host-built SD '+('Linux diagnostic' if report['automatic_boot'] else 'monitor')+' proof only. Never boot-tested. No card image/MBR.\n'
    'DDR/miniloader/BL31/BL32 and their containers stay private under build/.\n'
    +('Diagnostic Linux autoboot is enabled; panic hangs.\n' if report['automatic_boot'] else 'Autoboot is disabled; panic hangs. Serial diagnostics and memory map require review.\n')+
    'Do not flash this directory or replace the installed dArkOSen boot files.\n')
files = sorted(p for p in destination.rglob('*') if p.is_file())
(destination/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(destination)}\n' for p in files))
destination.replace(final_destination)
print('Frozen immutable host checkpoint:', final_destination)
