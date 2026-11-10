#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C67 source, license, staging/composition receipts without payload."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha, sums

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'muxretro-provider'
stage = Path((area / 'latest-build').read_text().strip())
assert stage.is_relative_to(area)
r = json.loads((stage / 'analysis.json').read_text())
assert r['passed'] and r['dependency_graph_contains_frontend_provider']
assert r['C07_boot_contract_and_eager_loader_passed'] and not r['device_contacted']
assert not r['image_built_or_booted'] and not r['full_Buildroot_rebuild']
assert r['existing_items_changed'] == r['existing_library_modes_changed_755_to_644'] == 4
assert r['existing_hashes_changed'] == 2 and r['C56_items_removed'] == 0
for name, digest in r['parent_proofs_sha256'].items():
    proof = repo / 'dist/phase4' / name
    assert sha(proof / 'SHA256SUMS') == digest
    for n, h in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == h, (name, n)
qualified = json.loads((repo / 'dist/phase4/frontend-libs-session/load/analysis.json').read_text())
assert qualified['passed'] and qualified['installed_host_used']
assert r['runtime_provider'] == qualified['libraries']
assert r['C66_native_evidence_reused'] == (r['binary_sha256'] == qualified['host_binary_sha256'])
assert sha(stage / 'target/opt/muos/frontend/muxretro') == r['binary_sha256']
for n, h in r['source_sha256'].items():
    assert sha(repo / n) == h, n
for name in ['usr/share/muos-muxretro-provider/payload.sha256',
             'usr/share/muos-frontend-libs/payload.sha256', 'usr/libexec/muos-save-store/payload.sha256']:
    for n, h in sums(stage / 'composition' / name).items():
        assert sha(stage / 'composition' / n.lstrip('/')) == h
assert sha(work / 'muxretro-image/image.n_uthilw/images/rootfs.ext4') == r['C64_image_preserved_sha256']
assert (work / 'graphics-config/output/.config').read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
out = repo / 'dist/phase4/muxretro-provider'
assert not out.exists()
public = Path(tempfile.mkdtemp(prefix='public.', dir=area))
for n in ['analysis.json', 'source-files.json', 'shared-frontend-sources.json', 'package-info.json',
          'composition-changed.json', 'composition-added.json', 'recipe.mk',
          'minimal.defconfig', 'default.config', 'opt-in.config', 'wrong-arch.config', 'old-host-conflict.config']:
    shutil.copyfile(stage / n, public / n)
labels = ['kconfig', 'legal-info', 'kconfig-refusals', 'copy-staging', 'recipe', 'elf', 'composition', 'composition-loader',
          'guard-missing', *('guard-' + n for n in r['runtime_provider'])]
for label in labels:
    for suffix in ['sh', 'stdout', 'stderr', 'exit']:
        shutil.copyfile(stage / (label + '.' + suffix), public / (label + '.' + suffix))
for name in ['muos-frontend-libs', 'muos-muxretro-provider']:
    shutil.copytree(stage / 'target/usr/share/licenses' / name, public / 'licenses' / name)
    shutil.copyfile(stage / 'target/usr/share' / name / 'payload.sha256', public / (name + '-payload.sha256'))
old = work / 'muxretro-package/build.mdou4mqr'
shutil.copyfile(old / 'prepared-source/provenance.json', public / 'C60-input-provenance.json')
shutil.copyfile(stage / 'prepared-source/provenance.json', public / 'provenance.json')
sources = {repo / n for n in r['source_sha256']} | {Path(__file__), repo / 'docs/archive/phase4/phase4-muxretro-provider.md'}
for source in sorted(sources):
    dest = public / 'source' / source.relative_to(repo)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
first = area / 'build.ispvtcnb'
attempt = json.loads((first / 'attempt-outcome.json').read_text())
assert attempt['passed'] is False and attempt['device_contacted'] is False
shutil.copyfile(first / 'attempt-outcome.json', public / 'first-attempt.json')
shutil.copyfile(first / 'recipe.stderr', public / 'first-attempt-linker.stderr')
(public / 'proof.json').write_text(json.dumps({
    'passed': True, 'experiment': 'C67_PROVIDER_CONSUMER_PROOF',
    'source_license_and_receipts_only': True, 'runtime_payload_included': False,
    'native_evidence_reused_only_for_identical_C66_host_and_libraries': r['C66_native_evidence_reused'],
    'new_native_host_qualification_required': not r['C66_native_evidence_reused'],
    'historical_recipes_and_images_preserved': True, 'device_contacted': False
}, indent=2) + '\n')
for p in public.rglob('*'):
    assert not p.is_symlink()
    if p.is_file():
        assert p.suffix.lower() not in {'.o', '.a', '.so', '.gb', '.gbc', '.img', '.ext4', '.png', '.wav', '.sav', '.srm', '.state', '.bundle', '.ini', '.gz', '.tar'}
        assert not p.read_bytes().startswith(b'\x7fELF')
(public / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(public)) + '\n'
                                         for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public, out)
for n, h in sums(out / 'SHA256SUMS').items():
    assert sha(out / n) == h
print('C67 source/license/staging/composition proof frozen:', out)
