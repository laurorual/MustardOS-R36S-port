#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C65 source/license/check receipts, without ELF or private payload."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha, sums

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'frontend-libs'
stage = Path((area / 'latest-build').read_text().strip())
assert stage.is_relative_to(area)
report = json.loads((stage / 'analysis.json').read_text())
assert report['passed'] and report['four_eager_dlopen_and_C60_version_help_passed']
assert not report['device_contacted'] and not report['full_Buildroot_rebuild']
assert not report['native_runtime_qualified'] and not report['new_image_built']
assert not report['private_prebuilt_frontend_SDK_used'] and not report['C46_diagnostic_variant_included']
for name, digest in report['parent_proofs_sha256'].items():
    proof = repo / 'dist/phase4' / name
    assert sha(proof / 'SHA256SUMS') == digest
    for n, h in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == h, (name, n)
for n, h in report['source_sha256'].items():
    assert sha(repo / n) == h, n
for n, item in report['libraries'].items():
    assert sha(stage / 'target/opt/muos/frontend/lib' / n) == item['sha256']
    assert sha(stage / 'staging/usr/lib' / n) == item['sha256']
for n, h in sums(stage / 'target/usr/share/muos-frontend-libs/payload.sha256').items():
    assert sha(stage / 'target' / n.lstrip('/')) == h
assert (work / 'graphics-config/output/.config').read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
out = repo / 'dist/phase4/frontend-libs'
assert not out.exists()
public = Path(tempfile.mkdtemp(prefix='public.', dir=area))
for name in ['analysis.json', 'source-files.json', 'package-info.json', 'recipe.mk',
             'minimal.defconfig', 'default.config', 'opt-in.config', 'wrong-arch.config']:
    shutil.copyfile(stage / name, public / name)
labels = ['kconfig', 'legal-info', 'wrong-arch', 'recipe', 'staging', 'loader']
labels += [prefix + n for n in report['libraries'] for prefix in ['elf-', 'old-elf-']]
for label in labels:
    for suffix in ['sh', 'stdout', 'stderr', 'exit']:
        shutil.copyfile(stage / (label + '.' + suffix), public / (label + '.' + suffix))
# The first clean compilation succeeded before its standalone-UI probe failed.
# Preserve its build receipts and compare outputs, without claiming runtime approval.
first = area / 'build.fr0v680t'
assert first != stage and (first / 'recipe.exit').read_text().strip() == '0'
assert (first / 'source-files.json').read_bytes() == (stage / 'source-files.json').read_bytes()
for n, item in report['libraries'].items():
    assert sha(first / 'target/opt/muos/frontend/lib' / n) == item['sha256'], n
for suffix in ['sh', 'stdout', 'stderr', 'exit']:
    shutil.copyfile(first / ('recipe.' + suffix), public / ('first-build-recipe.' + suffix))
(public / 'repeat-build.json').write_text(json.dumps({
    'passed': True, 'first_stage': first.name, 'second_stage': stage.name,
    'four_ELFs_byte_identical_across_clean_stages': True,
    'source_files_manifest_sha256': sha(stage / 'source-files.json'),
    'library_sha256': {n: item['sha256'] for n, item in report['libraries'].items()},
    'first_probe_failed_and_is_not_runtime_approval': True,
    'full_firmware_reproducibility_qualified': False}, indent=2) + '\n')
sources = {repo / n for n in report['source_sha256']}
sources |= {Path(__file__), repo / 'docs/analysis/phase4-frontend-libs.md'}
for source in sorted(sources):
    dest = public / 'source' / source.relative_to(repo)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
shutil.copytree(stage / 'target/usr/share/licenses/muos-frontend-libs', public / 'licenses')
shutil.copyfile(stage / 'target/usr/share/muos-frontend-libs/payload.sha256', public / 'target-payload.sha256')
(public / 'proof.json').write_text(json.dumps({
    'passed': True, 'experiment': 'C65_FRONTEND_LIBRARY_PROVIDER_PROOF',
    'source_license_and_offline_receipts_only': True, 'ELF_or_ROM_or_state_payload_included': False,
    'native_runtime_qualified': False, 'full_firmware_build_qualified': False,
    'historical_recipes_and_C64_image_preserved': True, 'device_contacted': False}, indent=2) + '\n')
for p in public.rglob('*'):
    assert not p.is_symlink()
    if p.is_file():
        assert p.suffix.lower() not in {'.so', '.a', '.o', '.gb', '.gbc', '.img', '.ext4', '.rom',
                                        '.sav', '.srm', '.state', '.bundle', '.gz', '.tar'}
        assert not p.read_bytes().startswith(b'\x7fELF')
(public / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(public)) + '\n'
                                         for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public, out)
for n, h in sums(out / 'SHA256SUMS').items():
    assert sha(out / n) == h, n
print('C65 source/license/offline proof frozen:', out)
