#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C71 exact migration policy and fault receipts, without ELF payloads."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha, sums

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'provider-upgrade'
stage = Path((area / 'latest-plan').read_text().strip())
checks = Path((area / 'latest-checks').read_text().strip())
plan = json.loads((stage / 'plan.json').read_text())
report = json.loads((checks / 'analysis.json').read_text())
assert stage.is_relative_to(area) and checks.is_relative_to(area)
assert plan['passed'] and report['passed'] and report['plan_sha256'] == sha(stage / 'plan.json')
assert len(report['cases']) == 140 and all(v['passed'] for v in report['cases'])
assert plan['selective_backup_files'] == 17 and plan['replace_files'] == 5
assert plan['add_files'] == 26 and plan['remove_obsolete_metadata_files'] == 12
assert len(plan['old_directories']) == 13 and len(plan['new_directories']) == 29
assert not plan['device_contacted'] and not plan['device_written'] and not report['native_adapter_tested']
manifest = json.loads((stage / 'manifest.json').read_text())
for file, key in [('plan.json', 'plan_sha256'), ('backup.json', 'backup_sha256'), ('deployment.tar', 'deployment_sha256')]:
    assert sha(stage / file) == manifest[key]
for n, h in sums(stage / 'SHA256SUMS').items(): assert sha(stage / n) == h
for name, digest in plan['parent_proofs_sha256'].items():
    proof = repo / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items(): assert sha(proof / n) == h
    assert sha(proof / 'SHA256SUMS') == digest
sources = {Path(__file__), repo / 'docs/analysis/phase4-provider-upgrade.md'}
for record in [plan, report]:
    for n, h in record['source_sha256'].items():
        assert sha(repo / n) == h, n
        sources.add(repo / n)
out = repo / 'dist/phase4/provider-upgrade'
assert not out.exists()
public = Path(tempfile.mkdtemp(prefix='public.', dir=area))
for name in ['plan.json', 'backup.json', 'manifest.json', 'policy.sh', 'SHA256SUMS']:
    shutil.copyfile(stage / name, public / ('payload-hashes.txt' if name == 'SHA256SUMS' else name))
shutil.copyfile(checks / 'analysis.json', public / 'checks.json')
for directory in sorted(checks.glob('case-*')):
    target = public / 'fixtures' / directory.name
    target.mkdir(parents=True)
    for name in ['test.sh', 'stdout', 'stderr', 'exit', 'before.json', 'before-case.json']:
        shutil.copyfile(directory / name, target / name)
    for file in sorted((directory / 'state').iterdir()):
        assert file.is_file() and not file.is_symlink()
        shutil.copyfile(file, target / file.name)
for source in sorted(sources):
    target = public / 'source' / source.relative_to(repo)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
(public / 'proof.json').write_text(json.dumps({'passed': True,
    'experiment': 'C71_OFFLINE_PUBLIC_UPGRADE_TRANSACTION_PROOF',
    'case_count': 140, 'source_and_metadata_only': True,
    'ELF_deployment_tar_or_private_state_included': False,
    'device_written': False, 'native_adapter_tested': False}, indent=2) + '\n')
assert (work / 'graphics-config/output/.config').read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
for p in public.rglob('*'):
    assert not p.is_symlink()
    if p.is_file():
        assert p.suffix.lower() not in {'.gb', '.gbc', '.so', '.img', '.ext4', '.fat', '.bin', '.dtb', '.png', '.wav', '.sav', '.state', '.bundle', '.ini', '.gz', '.tar'}
        assert not p.read_bytes().startswith(b'\x7fELF')
(public / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(public)) + '\n'
                                         for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public, out)
for n, h in sums(out / 'SHA256SUMS').items(): assert sha(out / n) == h
print('C71 offline transaction/source receipts frozen:', out)
