#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C70 source and metadata only; never boot-chain/image payloads."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha, sums
from phase4_card_image import verify_image

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'card-image'
stage = Path((area / 'latest-image').read_text().strip())
checks = Path((area / 'latest-checks').read_text().strip())
assert stage.is_relative_to(area) and checks.is_relative_to(area)
r = json.loads((stage / 'analysis.json').read_text())
c = json.loads((checks / 'analysis.json').read_text())
assert r['passed'] and c['passed'] and len(c['cases']) == 27 and all(v['passed'] for v in c['cases'])
assert r['experiment'] == 'C70_PRIVATE_PANEL0_CARD_IMAGE'
assert r['FAT_full_file_readback_matched'] and r['extracted_partition_hashes_matched']
assert r['FAT_readback_fsck_exit'] == 0 and r['C69_rootfs_fsck_reused_after_exact_readback']
assert r['UBoot_asset_hashes_matched'] and r['gzip_roundtrip_matched'] and r['SDK_config_unchanged']
assert r['factory_boot_counter'] == 0 and r['provisioning_required_before_network_boot']
for key in ['device_contacted', 'device_written', 'image_hardware_boot_tested', 'ui_autostart',
            'session_autostart', 'preferences_autostart', 'userdata_partition_included',
            'private_network_seed_host_keys_ROM_core_state_included']:
    assert r[key] is False, key
for name, digest in r['parent_proofs_sha256'].items():
    proof = repo / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == h, (name, n)
    assert sha(proof / 'SHA256SUMS') == digest, name
image = stage / 'muos-r35s-panel0-c70-private.img'
assert sha(image) == r['image_sha256']
assert sha(image.with_suffix('.img.gz')) == r['gzip_sha256']
assert verify_image(image, r['regions'])['passed']
out = repo / 'dist/phase4/card-image'
assert not out.exists()
public = Path(tempfile.mkdtemp(prefix='public.', dir=area))
sources = {Path(__file__), repo / 'docs/archive/phase4/phase4-card-image.md'}
for report in [r, c]:
    for n, h in report['source_sha256'].items():
        assert sha(repo / n) == h, n
        sources.add(repo / n)
shutil.copyfile(stage / 'analysis.json', public / 'analysis.json')
shutil.copyfile(checks / 'analysis.json', public / 'checks.json')
for label in ['fat-create', 'fat-readback', 'partition-fsck']:
    assert (stage / (label + '.exit')).read_text().strip() == '0'
    for ext in ['sh', 'stdout', 'stderr', 'exit']:
        name = label + '.' + ext
        shutil.copyfile(stage / name, public / name)
for source in sorted(sources):
    target = public / 'source' / source.relative_to(repo)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
(public / 'proof.json').write_text(json.dumps({'passed': True,
    'experiment': 'C70_PRIVATE_CARD_IMAGE_SOURCE_PROOF', 'source_and_metadata_only': True,
    'image_binary_FAT_or_bootchain_payload_included': False,
    'validator_cases': 27, 'image_hardware_boot_tested': False}, indent=2) + '\n')
assert (work / 'graphics-config/output/.config').read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
for p in public.rglob('*'):
    assert not p.is_symlink()
    if p.is_file():
        assert p.suffix.lower() not in {'.gb', '.gbc', '.so', '.img', '.ext4', '.fat', '.bin', '.dtb', '.png', '.wav', '.sav', '.state', '.bundle', '.ini', '.gz', '.tar'}
        assert not p.read_bytes().startswith(b'\x7fELF')
(public / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(public)) + '\n'
                                         for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public, out)
for n, h in sums(out / 'SHA256SUMS').items():
    assert sha(out / n) == h
print('C70 sources/metadata frozen (no private payload):', out)
