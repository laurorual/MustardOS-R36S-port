#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C69 source/metadata receipts, excluding all private image payloads."""
from pathlib import Path
import json, re, shutil, tempfile
from phase4_candidate import inventory, sha, sums

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'provider-image'
out = repo / 'dist/phase4/provider-image'
assert not out.exists()
stage = Path((area / 'latest-image').read_text().strip())
assert stage.is_relative_to(area)
r = json.loads((stage / 'analysis.json').read_text())
assert r['passed'] and r['experiment'] == 'C69_PRIVATE_PROVIDER_CONSUMER_EXT4'
for name, digest in r['parent_proofs_sha256'].items():
    proof = repo / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == h, (name, n)
    assert sha(proof / 'SHA256SUMS') == digest, name
assert r['full_readback_inventory_matched'] and r['fsck_exit'] == 0 and r['factory_boot_counter'] == 0
assert r['readback_items'] == 3386 and r['existing_items_changed'] == 4
assert r['existing_hashes_changed'] == 2 and r['new_files'] == 27 and r['new_directories'] == 29
assert r['written_regular_single_link_files'] == 31 and r['new_inodes_modes_verified'] == 60
assert r['new_inodes_and_root_owned_by_root'] and r['C07_boot_contract_before_and_after']
assert r['C68_native_component_evidence_reused'] and r['SDK_config_unchanged']
for key in ['device_contacted', 'device_written', 'candidate_boot_tested', 'full_Buildroot_rebuild',
            'new_native_session_executed', 'kernel_DTB_bootloader_partition_changed']:
    assert r[key] is False, key
assert sha(stage / 'images/rootfs.ext4') == r['image_sha256']
tree = json.loads((stage / 'expected-tree.json').read_text())
assert inventory(stage / 'target') == tree
source = Path(r['source_build'])
assert sha(source / 'analysis.json') == r['C67_analysis_sha256']
assert tree == json.loads((source / 'expected-tree.json').read_text())
added = json.loads((source / 'composition-added.json').read_text())
changed = json.loads((source / 'composition-changed.json').read_text())
inodes = (stage / 'inodes.stdout').read_text()
for name in set(added) | set(changed) | {''}:
    path = '/' + name
    match = re.search(r'debugfs: stat ' + re.escape(path) + r'\n(.*?)(?=debugfs: |\Z)', inodes, re.S)
    assert match and re.search(r'User:\s+0\s+Group:\s+0', match[1]), path
    mode = tree[name]['mode'] if name else 0o755
    assert re.search(r'Mode:\s+0' + f'{mode:o}' + r'\b', match[1]), path
    if name and tree[name]['type'] == 'file':
        assert re.search(r'Type: regular', match[1]) and re.search(r'Links:\s+1\b', match[1]), name
coverage = json.loads((stage / 'loader-coverage.json').read_text())
fresh, reused = coverage['refreshed'], coverage['reused_identical_C38_C56']
assert coverage['passed'] and len(fresh) == r['new_loader_resolution_checks'] == 4
assert len(reused) == r['identical_C38_C56_loader_checks_reused'] == 170
assert not set(fresh) & set(reused) and set(fresh) | set(reused) == set(coverage['programs'])
assert coverage['dynamic_programs'] == r['dynamic_programs'] == 174
before = json.loads((work / 'save-store-image/image.nlnmgzzb/expected-tree.json').read_text())
for name, row in coverage['programs'].items():
    signature = row['resolved_dependency_sha256']
    assert name in signature
    assert all(tree[n]['sha256'] == h for n, h in signature.items()), name
    differences = [n for n, h in signature.items() if n not in before or before[n].get('sha256') != h]
    assert differences == row['changed_or_new_paths']
    assert bool(differences) == (name in fresh)
assert (stage / 'affected-loaders.stdout').read_text().splitlines() == ['C69_LOADER_PASS_' + n for n in fresh]
sources = {Path(__file__), repo / 'docs/archive/phase4/phase4-provider-image.md'}
for n, h in r['source_sha256'].items():
    assert sha(repo / n) == h, n
    sources.add(repo / n)
public = Path(tempfile.mkdtemp(prefix='public.', dir=area))
for name in ['analysis.json', 'static-audit.json', 'loader-coverage.json', 'expected-tree.json',
             'debugfs.commands', 'inode.commands', 'old-inodes.commands']:
    shutil.copyfile(stage / name, public / name)
for label in ['planned-boot-contract', 'old-inodes', 'write-image', 'fsck', 'inodes', 'readback',
              'readback-boot-contract', 'dynamic-metadata', 'affected-loaders']:
    assert (stage / (label + '.exit')).read_text().strip() == '0', label
    for ext in ['sh', 'exit', 'stdout', 'stderr']:
        name = label + '.' + ext
        shutil.copyfile(stage / name, public / name)
for source in sorted(sources):
    target = public / 'source' / source.relative_to(repo)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
(public / 'proof.json').write_text(json.dumps({
    'passed': True, 'experiment': 'C69_OFFLINE_PROVIDER_CONSUMER_IMAGE_PROOF',
    'private_image_payload_included': False, 'loader_checks_refreshed': 4,
    'identical_dependency_loader_checks_reused': 170,
    'candidate_boot_tested': False, 'device_contacted': False}, indent=2) + '\n')
assert (work / 'graphics-config/output/.config').read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
for p in public.rglob('*'):
    assert not p.is_symlink()
    if p.is_file():
        assert p.suffix.lower() not in {'.gb', '.gbc', '.so', '.img', '.ext4', '.png', '.wav', '.sav', '.srm', '.state', '.bundle', '.ini', '.gz', '.tar'}
        assert not p.read_bytes().startswith(b'\x7fELF')
(public / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(public)) + '\n'
                                         for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public, out)
for n, h in sums(out / 'SHA256SUMS').items():
    assert sha(out / n) == h
print('C69 source/offline-image proof frozen:', out)
