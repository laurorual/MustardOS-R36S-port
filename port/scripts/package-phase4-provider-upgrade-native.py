#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C72 sanitized native migration receipts; exclude private bindings."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha, sums

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'provider-upgrade-native'
stage = Path((area / 'latest-plan').read_text().strip())
r = json.loads((stage / 'install-analysis.json').read_text())
b = json.loads((stage / 'binding.json').read_text())
c = json.loads((stage / 'checks.json').read_text())
f = json.loads((stage / 'final-audit.json').read_text())
assert r['passed'] and c['passed'] and f['passed'] and len(c['cases']) == 18
assert r['binding_sha256'] == c['binding_sha256'] == f['binding_sha256'] == sha(stage / 'binding.json')
assert f['install_analysis_sha256'] == sha(stage / 'install-analysis.json')
assert f['RAM_removed'] and f['root_read_only'] and f['installed_31_file_model_verified']
assert r['initial_positional_probe_failure_preserved'] and not r['deployment_redispatched']
assert r['C65_probe_positional_ABI_restored'] == ['libui.so', 'libmuxcom.so', 'libmuxmod.so', 'libplutosvg.so']
assert r['native_installed_provider4_and_host_eager_CLI_passed']
for key in ['reboot_requested', 'p3_mounted', 'GUI_replayed', 'token_or_service_enabled', 'image_C70_flashed']:
    assert r[key] is False
assert sha(stage / 'plan.json') == b['plan_sha256'] and sha(stage / 'backup.json') == b['backup_sha256']
assert sha(stage / 'deployment.tar') == b['deployment_sha256']
parent = repo / 'dist/phase4/provider-upgrade'
for n, h in sums(parent / 'SHA256SUMS').items(): assert sha(parent / n) == h
assert sha(parent / 'SHA256SUMS') == b['C71_proof_sha256']
assert (stage / 'result.stdout').read_text().startswith('0\n')
assert (stage / 'native-ABI.exit').read_text() == '0\n'
assert (stage / 'native-ABI-positional-failure.exit').read_text() == '3\n'
assert 'undefined symbol: lang' in (stage / 'native-ABI-positional-failure.stderr').read_text()
assert (stage / 'native-ABI.stdout').read_text().count('C65 eager load: ') == 4
for label in ['pre-cleanup-health', 'pre-cleanup-tree', 'cleanup', 'stopped-screen', 'post-cleanup-health']:
    assert (stage / (label + '.exit')).read_text() == '0\n'
sources = {Path(__file__), repo / 'docs/archive/phase4/phase4-provider-upgrade-native.md'}
for report in [r, b, c, f]:
    for n, h in report['source_sha256'].items():
        assert sha(repo / n) == h, n
        sources.add(repo / n)
out = repo / 'dist/phase4/provider-upgrade-native'
assert not out.exists()
public = Path(tempfile.mkdtemp(prefix='public.', dir=area))
for name, report in [('analysis.json', r), ('checks.json', c), ('final-audit.json', f)]:
    (public / name).write_text(json.dumps(report, indent=2) + '\n')
for label in ['native-ABI', 'native-ABI-positional-failure']:
    for ext in ['stdout', 'stderr', 'exit']:
        name = label + '.' + ext
        shutil.copyfile(stage / name, public / name)
for name in ['collected-apply.log', 'collected-apply.result', 'collected-apply.done']:
    shutil.copyfile(stage / name, public / name)
(public / 'proof.json').write_text(json.dumps({'passed': True,
    'experiment': 'C72_SANITIZED_NATIVE_PROVIDER_MIGRATION_PROOF',
    'C71_proof_sha256': b['C71_proof_sha256'], 'before_public_payloads_backed_up': 17,
    'final_public_files': 31, 'private_binding_and_fingerprints_included': False,
    'ELF_deployment_ROM_or_save_included': False, 'new_GUI_tested': False}, indent=2) + '\n')
for source in sorted(sources):
    target = public / 'source' / source.relative_to(repo)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
assert (work / 'graphics-config/output/.config').read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
for path in public.rglob('*'):
    assert not path.is_symlink()
    if path.is_file():
        assert path.suffix.lower() not in {'.gb', '.gbc', '.so', '.img', '.ext4', '.fat', '.bin', '.dtb', '.png', '.wav', '.sav', '.state', '.bundle', '.ini', '.gz', '.tar'}
        data = path.read_bytes()
        assert not data.startswith(b'\x7fELF') and b['kernel_boot_id'].encode() not in data, path
(public / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(public)) + '\n'
                                         for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public, out)
for n, h in sums(out / 'SHA256SUMS').items(): assert sha(out / n) == h
print('C72 sanitized migration proof frozen; no private bindings or payload:', out)
