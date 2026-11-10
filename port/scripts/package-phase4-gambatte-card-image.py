#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C79 source/metadata and reused C70 validator evidence; no private payloads."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha, sums
from phase4_card_image import regular_single

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'gambatte-card-image'
stage = Path((area / 'latest-image').read_text().strip())
checks = repo / 'dist/phase4/card-image'
assert stage.is_relative_to(area)
r = json.loads((stage / 'analysis.json').read_text())
c = json.loads((checks / 'checks.json').read_text())
assert r['passed'] and c['passed'] and len(c['cases']) == 27 and all(v['passed'] for v in c['cases'])
assert r['experiment'] == 'C79_PRIVATE_GAMBATTE_PANEL0_CARD_IMAGE'
assert r['FAT_full_file_readback_matched'] and r['extracted_partition_hashes_matched']
assert r['FAT_readback_fsck_exit'] == 0 and r['C78_rootfs_fsck_reused_after_exact_readback']
assert r['UBoot_asset_hashes_matched'] and r['gzip_roundtrip_matched'] and r['SDK_config_unchanged']
assert r['factory_boot_counter'] == 0 and r['provisioning_required_before_network_boot']
for key in ['device_contacted', 'device_written', 'image_hardware_boot_tested', 'ui_autostart',
            'session_autostart', 'preferences_autostart', 'userdata_partition_included',
            'private_network_seed_host_keys_ROM_or_state_included', 'new_validator_fixtures_executed',
            'new_native_session_executed', 'bootchain_rebuilt', 'kernel_DTB_rebuilt']:
    assert r[key] is False, key
for name, digest in r['parent_proofs_sha256'].items():
    proof = repo / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == h, (name, n)
    assert sha(proof / 'SHA256SUMS') == digest, name
root_report = json.loads((repo / 'dist/phase4/gambatte-image/analysis.json').read_text())
old_report = json.loads((repo / 'dist/phase4/card-image/analysis.json').read_text())
assert r['C78_analysis_sha256'] == sha(repo / 'dist/phase4/gambatte-image/analysis.json')
assert r['C78_rootfs_sha256'] == root_report['image_sha256'] == r['regions']['rootfs.ext4']['sha256']
assert r['C78_inventory_items_covered_by_exact_partition_hash'] == 3403
assert r['C70_card_image_preserved_sha256'] == old_report['image_sha256']
assert r['C70_gzip_preserved_sha256'] == old_report['gzip_sha256']
assert r['gambatte_core_included'] and r['combined_license_review_pending']
assert r['core_sha256'] == root_report['core_sha256']
assert r['core_path'] == '/opt/muos/share/core/gambatte_libretro.so'
assert r['C70_validator_cases_reused'] == 27
assert r['only_FAT_asset_changed'] == 'PROBE.TXT'
assert r['bootchain_regions_byte_identical_to_C70'] and r['C78_core_ABI_and_C77_physical_evidence_reused']
assert set(r['fat_files_sha256']) == set(old_report['fat_files_sha256'])
assert {n for n,h in r['fat_files_sha256'].items() if h != old_report['fat_files_sha256'][n]} == {'PROBE.TXT'}
for n,row in r['regions'].items():
 assert (row['offset'],row['bytes']) == (old_report['regions'][n]['offset'],old_report['regions'][n]['bytes'])
 if n not in {'rootfs.ext4','boot.fat'}: assert row == old_report['regions'][n]
for n in ['boot.fat','rootfs.ext4']:
 assert sha(stage/'partition-readback'/n) == r['regions'][n]['sha256']
image = stage / 'muos-r35s-panel0-c79-private.img'
regular_single(image)

assert sha(image) == r['image_sha256']
assert sha(image.with_suffix('.img.gz')) == r['gzip_sha256']
assert r['canonical_MBR'] and r['partition_count'] == 2 and r['payload_regions_hashed'] == 5 and r['all_other_bytes_zero']
out = repo / 'dist/phase4/gambatte-card-image'
assert not out.exists()
public = Path(tempfile.mkdtemp(prefix='public.', dir=area))
sources = {Path(__file__), repo / 'docs/archive/phase4/phase4-gambatte-card-image.md'}
for report in [r, c]:
    for n, h in report['source_sha256'].items():
        assert sha(repo / n) == h, n
        sources.add(repo / n)
shutil.copyfile(stage / 'analysis.json', public / 'analysis.json')
shutil.copyfile(checks / 'checks.json', public / 'checks-reused.json')
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
    'experiment': 'C79_PRIVATE_GAMBATTE_CARD_IMAGE_SOURCE_PROOF', 'source_and_metadata_only': True,
    'image_binary_FAT_or_bootchain_payload_included': False,
    'C70_validator_cases_reused': 27, 'new_validator_fixtures_executed': False,
    'C78_partition_bytes_verified': True, 'combined_license_review_pending': True, 'image_hardware_boot_tested': False}, indent=2) + '\n')
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
print('C79 sources/metadata frozen (no private payload):', out)
