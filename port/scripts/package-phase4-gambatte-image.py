#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C78 source and offline validation receipts; exclude private payloads."""
from pathlib import Path
import json, re, shutil, tempfile
from phase4_candidate import inventory, sha, sums
from phase4_card_image import regular_single

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'; area = work / 'gambatte-image'
stage = Path((area / 'latest-image').read_text().strip()).resolve()
assert stage.is_relative_to(area)
r = json.loads((stage / 'analysis.json').read_text())
assert r['passed'] and r['experiment'] == 'C78_PRIVATE_GAMBATTE_EXT4'
assert r['private_only'] and not r['redistribution_approved'] and r['combined_license_review_pending']
for name, digest in r['parent_proofs_sha256'].items():
    proof = repo / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items(): assert sha(proof / n) == h, (name, n)
    assert sha(proof / 'SHA256SUMS') == digest, name
for key in ['full_readback_inventory_matched', 'new_inodes_and_root_owned_by_root',
            'C07_boot_contract_before_and_after', 'all_package_manifests_verified', 'ext4_features_preserved',
            'core_eager_API1_readback_probe_passed', 'C77_native_component_evidence_reused', 'SDK_config_unchanged']:
    assert r[key] is True, key
for key in ['device_contacted', 'device_written', 'original_32GB_or_Deck_accessed', 'candidate_boot_tested',
            'core_initialized', 'ROM_loaded', 'new_native_session_executed', 'diagnostic_caller_included',
            'ROM_saves_credentials_seed_or_hostkeys_included', 'full_Buildroot_rebuild']:
    assert r[key] is False, key
assert r['new_files'] == 9 and r['new_directories'] == 8 and r['existing_items_changed'] == 0
assert r['base_items_preserved'] == 3386 and r['readback_items'] == 3403
assert r['factory_boot_counter'] == r['fsck_exit'] == 0
assert r['written_regular_single_link_files'] == 9 and r['new_and_root_inode_modes_verified'] == 18
image = stage / 'images/rootfs.ext4'; regular_single(image)
assert image.stat().st_size == r['image_bytes'] == 512 * 1024 * 1024
assert sha(image) == r['image_sha256']
source = Path(r['source_build']); assert source.is_relative_to(work / 'gambatte-package')
assert sha(source / 'analysis.json') == r['C75_analysis_sha256']
tree = json.loads((stage / 'expected-tree.json').read_text())
assert inventory(stage / 'target') == tree == json.loads((source / 'expected-tree.json').read_text())
before = json.loads((repo / 'dist/phase4/provider-image/expected-tree.json').read_text())
added = json.loads((repo / 'dist/phase4/gambatte-package/composition-added.json').read_text())
assert tree == {**before, **added} and not set(before) & set(added)
assert tree['opt/muos/share/core/gambatte_libretro.so']['sha256'] == r['core_sha256']
coverage = json.loads((repo / 'dist/phase4/provider-image/loader-coverage.json').read_text())
reuse = json.loads((stage / 'loader-reuse.json').read_text())
assert reuse['passed'] and reuse['programs_reused'] == r['C69_dependency_loader_checks_reused'] == 174
assert reuse['C69_coverage_sha256'] == sha(repo / 'dist/phase4/provider-image/loader-coverage.json')
for name, row in coverage['programs'].items():
    assert name in row['resolved_dependency_sha256']
    assert all(before[n]['sha256'] == tree[n]['sha256'] == h for n, h in row['resolved_dependency_sha256'].items())
inodes = (stage / 'inodes.stdout').read_text()
for n in ['', *sorted(added)]:
    match = re.search(r'debugfs: stat ' + re.escape('/' + n) + r'\n(.*?)(?=debugfs: |\Z)', inodes, re.S)
    assert match and re.search(r'User:\s+0\s+Group:\s+0', match[1]), n
    mode = tree[n]['mode'] if n else 0o755
    assert re.search(r'Mode:\s+0' + f'{mode:o}' + r'\b', match[1]), n
    if n and tree[n]['type'] == 'file':
        assert re.search(r'Type: regular', match[1]) and re.search(r'Links:\s+1\b', match[1]), n
sources = {Path(__file__), repo / 'docs/archive/phase4/phase4-gambatte-image.md'}
for n, h in r['source_sha256'].items():
    assert sha(repo / n) == h, n
    sources.add(repo / n)
public = Path(tempfile.mkdtemp(prefix='public.', dir=area))
for n in ['analysis.json', 'expected-tree.json', 'static-audit.json', 'loader-reuse.json', 'debugfs.commands', 'inode.commands']:
    shutil.copyfile(stage / n, public / n)
for label in ['planned-boot-contract', 'write-image', 'fsck', 'inodes', 'readback', 'readback-boot-contract', 'core-readback-ABI']:
    assert (stage / (label + '.exit')).read_text() == '0\n', label
    for ext in ['sh', 'stdout', 'stderr', 'exit']: shutil.copyfile(stage / (label + '.' + ext), public / (label + '.' + ext))
for source_file in sorted(sources):
    dest = public / 'source' / source_file.relative_to(repo)
    dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source_file, dest)
(public / 'proof.json').write_text(json.dumps({'passed': True, 'experiment': 'C78_OFFLINE_GAMBATTE_IMAGE_PROOF',
    'private_image_or_ELF_included': False, 'new_core_metadata_loader_probe': True,
    'C69_dependency_loader_checks_reused': 174, 'C77_physical_result_reused_for_same_bytes': True,
    'candidate_boot_tested': False, 'device_contacted': False, 'combined_license_review_pending': True}, indent=2) + '\n')
assert (work / 'graphics-config/output/.config').read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
for p in public.rglob('*'):
    assert not p.is_symlink()
    if p.is_file():
        assert p.suffix.lower() not in {'.gb', '.gbc', '.so', '.o', '.a', '.img', '.ext4', '.png', '.wav', '.sav', '.srm', '.state', '.bundle', '.ini', '.gz', '.tar'}
        assert not p.read_bytes().startswith(b'\x7fELF')
(public / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(public)) + '\n' for p in sorted(public.rglob('*')) if p.is_file()))
out = repo / 'dist/phase4/gambatte-image'; assert not out.exists()
shutil.move(public, out)
for n, h in sums(out / 'SHA256SUMS').items(): assert sha(out / n) == h
print('C78 sanitized offline image proof frozen:', out)
