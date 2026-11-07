#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze only the bounded C21 public evidence and its as-tested source hashes."""
from pathlib import Path
import argparse, hashlib, json, shutil

repo = Path(__file__).resolve().parents[2]; area = repo / 'build/phase4/preferences'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--stage', type=Path)
p.add_argument('--name', choices=['preferences-session-native', 'preferences-session-physical-edit', 'preferences-session-reboot', 'session-package-independent'], default='preferences-session-native')
a = p.parse_args()
stage = a.stage.resolve() if a.stage else Path((area / 'latest-session-native').read_text().strip())
assert stage.is_relative_to(area.resolve())
report = json.loads((stage / 'analysis.json').read_text()); assert report['passed']
prepared = Path((repo / 'build/phase4/runtime-session/latest-service').read_text().strip())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(prepared / 'manifest.json') == report['prepared_manifest_sha256']
assert sha(repo / 'port/scripts/audit-phase4-preferences-session.py') == report['runner_sha256']
checks = Path((area / 'latest-session-checks').read_text().strip())
assert json.loads((checks / 'analysis.json').read_text())['passed']
out = repo / 'dist/phase4' / a.name; assert not out.exists(); out.mkdir()
for name in ['analysis.json', 'final-health.txt']:
    shutil.copyfile(stage / name, out / name)
shutil.copyfile(checks / 'analysis.json', out / 'boundary-checks.json')
for name in ['physical-observations.jsonl', 'physical-confirmation.json', 'inode-commit.json']:
    if (stage / name).is_file(): shutil.copyfile(stage / name, out / name)
shutil.copyfile(prepared / 'manifest.json', out / 'build-manifest.json')
for number in range(1, len(report['cycles']) + 1):
    label = 'cycle' + str(number)
    shutil.copytree(stage / label, out / label)
    for suffix in ['active.stdout', 'health.stdout', 'start.exit', 'stop.exit']:
        shutil.copyfile(stage / (label + '-' + suffix), out / (label + '-' + suffix))
if a.name == 'session-package-independent':
    assert report['operation'] == 'package-isolation' and report['boot_package_hidden_from_worker']
    checked = Path((repo / 'build/phase4/runtime-session/latest-package-checks').read_text().strip())
    checks_report = json.loads((checked / 'analysis.json').read_text()); assert checks_report['passed']
    for name, digest in checks_report['source_sha256'].items(): assert sha(repo / name) == digest
    shutil.copyfile(checked / 'analysis.json', out / 'package-checks.json')
    shutil.copyfile(checked / 'stdout', out / 'package-checks.stdout')
    for name in ['isolation-proved.stdout', 'isolation-proved.sh', 'binary-equivalence.json', 'prepare-isolation.stdout']:
        shutil.copyfile(stage / name, out / name)
    for name in ['deployment.tar', 'recipe.stdout', 'reinstall.stdout', 'audit.stdout']:
        shutil.copyfile(prepared / name, out / name)
    shutil.copyfile(prepared / 'package/payload.sha256', out / 'payload.sha256')
    shutil.copyfile(prepared / 'recipe-target/etc/default/muos-session', out / 'muos-session.default')
# Snapshot from the prepared tree, not reconstructed from a later working tree.
sources = out / 'source'; sources.mkdir()
for name in ['service.sh', 'worker.sh', 'runtime.sh', 'chain.sh', 'preferences.sh', 'data-functions.sh']:
    shutil.copyfile(prepared / 'source/service' / name, sources / name)
shutil.copyfile(repo / 'port/scripts/audit-phase4-preferences-session.py', sources / 'audit-phase4-preferences-session.py')
if a.name == 'session-package-independent':
    for name, original in {
        'card-guard.sh': prepared / 'source/service/card-guard.sh',
        'Config.in': repo / 'port/buildroot/package/muos-r35s-session/Config.in',
        'muos-r35s-session.mk': repo / 'port/buildroot/package/muos-r35s-session/muos-r35s-session.mk',
        'prepare-phase4-session-service.py': repo / 'port/scripts/prepare-phase4-session-service.py',
        'check-phase4-session-package.py': repo / 'port/scripts/check-phase4-session-package.py',
        'session-package-isolate.sh': repo / 'port/diagnostics/session-package-isolate.sh',
    }.items(): shutil.copyfile(original, sources / name)
(out / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(out)) + '\n' for p in sorted(out.rglob('*')) if p.is_file()))
print('Immutable public session proofs:', out)
