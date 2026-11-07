#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C70: assemble the qualified private boot chain and C69 factory rootfs offline."""
from pathlib import Path
import gzip, hashlib, json, os, re, shutil, subprocess, tempfile
from phase4_candidate import sha, sums, validate
from phase4_card_image import (BOOT_OFFSETS, DISK_SIGNATURE, FAT_BYTES, FAT_OFFSET,
                              IMAGE_BYTES, ROOT_BYTES, ROOT_OFFSET, mbr_bytes,
                              regular_single, verify_image)

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'card-image'
area.mkdir(exist_ok=True)
baseline = work / 'network-tools/baseline.config'
assert (work / 'graphics-config/output/.config').read_bytes() == baseline.read_bytes()
parents = {}
for name in ['provider-image', 'uboot-sd-ext4-diagnostic', 'native-ext4-boot']:
    proof = repo / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == h, (name, n)
    parents[name] = sha(proof / 'SHA256SUMS')
root_stage = work / 'provider-image/image.izief28e'
root_report = json.loads((root_stage / 'analysis.json').read_text())
assert (root_stage / 'analysis.json').read_bytes() == (repo / 'dist/phase4/provider-image/analysis.json').read_bytes()
assert root_report['passed'] and root_report['fsck_exit'] == 0 and not root_report['candidate_boot_tested']
for n, h in root_report['source_sha256'].items():
    assert sha(repo / n) == h, n
root_image = root_stage / 'images/rootfs.ext4'
regular_single(root_image)
assert root_image.stat().st_size == ROOT_BYTES and sha(root_image) == root_report['image_sha256']
factory = validate(root_stage / 'target')
assert (root_stage / 'target/var/lib/muos-diagnostic/boot-seq').read_text() == '0\n'
native = json.loads((repo / 'dist/phase4/native-ext4-boot/native-ext4-analysis.json').read_text())
assert native['passed'] and native['pid1_from_ext4'] and native['root_partuuid'] == '4d554432-02'
uboot = work / 'uboot-sd/probe.3utahq01'
package = uboot / 'package.ou1j44x6'
report = json.loads((uboot / 'audit/report.json').read_text())
pack = json.loads((package / 'audit.json').read_text())
assert report['passed'] and report['inputs']['profile'] == 'ext4-diagnostic'
assert report['automatic_boot'] and not report['inputs']['persistent_environment']
assert pack['passed'] and pack['manifest']['u_boot_audit_sha256'] == sha(uboot / 'audit/report.json')
assert sha(uboot / 'audit/report.json') == sha(repo / 'dist/phase4/uboot-sd-ext4-diagnostic/audit/report.json')
for n, h in pack['output_sha256'].items():
    assert sha(package / n) == h, n
for n, h in report['output_sha256'].items():
    assert sha(uboot / 'output' / n) == h, n
for n, h in report['inputs']['port_inputs'].items():
    assert sha(repo / n) == h, n
manifest = Path(report['inputs']['diagnostic_assets_manifest'])
assert sha(manifest) == report['inputs']['diagnostic_assets_manifest_sha256']
linux = json.loads(manifest.read_text())
assert linux['kernel_release'] == '4.4.189-muos-r35s-p4'
assert linux['root_partuuid'] == '4d554432-02'
assert set(linux['assets']) == {'Image', 'rk3326-muos-r35s-panel0.dtb'}
header = (uboot / 'source/include/configs/muos-r35s-linux-assets.h').read_text()
for name, macro in [('Image', 'IMAGE'), ('rk3326-muos-r35s-panel0.dtb', 'LINUX_FDT')]:
    row = linux['assets'][name]
    assert sha(Path(row['path'])) == row['sha256'] and Path(row['path']).stat().st_size == row['bytes']
    assert f'#define MUOS_{macro}_BYTES {row["bytes"]}UL' in header
    sequence = ','.join('0x' + row['sha256'][i:i+2] for i in range(0, 64, 2))
    assert f'#define MUOS_{macro}_SHA256 {{{sequence}}}' in header
board = (repo / 'port/device/rk-r35s-p0/uboot-ext4/board.h').read_text()
assert 'root=PARTUUID=4d554432-02 rootfstype=ext4 rootwait ro ' in board
assert 'init=/sbin/muos-ext4-diag' in board
assert 'candidate_boot_check || fail' in (root_stage / 'target/sbin/muos-ext4-diag').read_text()
tools = (work / 'media-tools-container.iid').read_text().strip()
assert tools == 'sha256:4d5c100835e155188d742a07aa0ae8823bed2fefa26770e23d5cea559b83a8a8'
stage = Path(tempfile.mkdtemp(prefix='image.', dir=area))
(area / 'latest-attempt').write_text(str(stage) + '\n')
assets = stage / 'assets'
assets.mkdir()
for name, row in linux['assets'].items():
    shutil.copyfile(row['path'], assets / name)
shutil.copyfile(uboot / 'source/Licenses/gpl-2.0.txt', assets / 'COPYING.TXT')
(assets / 'DIAG.ID').write_text('MUOS-R35S-EXT4-P4-B01\n')
(assets / 'PROBE.TXT').write_text(
    'PRIVATE C70 / R35S Panel 0 / RK3326. C69 factory rootfs, C07 diagnostic.\n'
    'Factory counter zero; UI/session/preferences autostart disabled.\n'
    'No Wi-Fi credentials, RNG seed, SSH host keys, ROM, core or saved state.\n'
    'Network/RNG provisioning is required before a supervised network boot.\n'
    'No userdata partition or filesystem resize included.\n'
    'Keep the original 32-GB dArkOSen card outside. Do not flash a running card.\n'
    'This whole image has not booted; boot-chain/GPU licensing remains pending.\n')
epoch = report['inputs']['source_date_epoch']
for p in assets.iterdir():
    os.utime(p, (epoch, epoch))
fat = stage / 'boot.fat'
with fat.open('xb') as stream:
    stream.truncate(FAT_BYTES)
rel = lambda p: '/work/' + str(p.relative_to(work))
container = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
             '--security-opt=no-new-privileges', '--userns=keep-id', '--tmpfs', '/tmp:rw,nosuid,nodev',
             '-v', f'{work}:/work:rw,z', tools]
def run(label, code):
    (stage / (label + '.sh')).write_text(code)
    result = subprocess.run(container + ['sh', '-eu', '-c', code], capture_output=True, text=True, timeout=90)
    for suffix, value in [('stdout', result.stdout), ('stderr', result.stderr), ('exit', str(result.returncode) + '\n')]:
        (stage / (label + '.' + suffix)).write_text(value)
    assert result.returncode == 0, (stage, label, result.stderr[-2000:])

run('fat-create', f'mkfs.fat --invariant -F 32 -n MUOSDIAG -i {DISK_SIGNATURE:08x} {rel(fat)}\n' +
    ''.join(f'mcopy -m -i {rel(fat)} {rel(p)} ::/\n' for p in sorted(assets.iterdir())) +
    f'fsck.fat -n {rel(fat)}\ncat /usr/local/share/phase4-media-packages.txt\n')
regions = {}
for name, offset in BOOT_OFFSETS.items():
    path = package / name
    regions[name] = {'offset': offset, 'bytes': path.stat().st_size, 'sha256': pack['output_sha256'][name]}
regions['boot.fat'] = {'offset': FAT_OFFSET, 'bytes': FAT_BYTES, 'sha256': sha(fat)}
regions['rootfs.ext4'] = {'offset': ROOT_OFFSET, 'bytes': ROOT_BYTES, 'sha256': root_report['image_sha256']}
image = stage / 'muos-r35s-panel0-c70-private.img'
with image.open('xb') as stream:
    stream.truncate(IMAGE_BYTES)
    stream.write(mbr_bytes())
    for name, row in sorted(regions.items(), key=lambda item: item[1]['offset']):
        source = fat if name == 'boot.fat' else root_image if name == 'rootfs.ext4' else package / name
        assert sha(source) == row['sha256']
        stream.seek(row['offset'])
        with source.open('rb') as payload:
            shutil.copyfileobj(payload, stream)
    stream.flush()
    os.fsync(stream.fileno())
verified = verify_image(image, regions)
readback = stage / 'fat-readback'
readback.mkdir()
run('fat-readback', f'mdir -i {rel(image)}@@{FAT_OFFSET} ::/\n' +
    f'mcopy -m -i {rel(image)}@@{FAT_OFFSET} "::/*" {rel(readback)}/\n' +
    f'/work/graphics-config/output/host/sbin/fdisk -l {rel(image)}\n')
assert {p.name for p in readback.iterdir()} == {p.name for p in assets.iterdir()}
asset_hashes = {p.name: sha(p) for p in sorted(assets.iterdir())}
assert {p.name: sha(p) for p in readback.iterdir()} == asset_hashes
# Extract the actual embedded partitions without loop devices or kernel mounts.
# FAT is new and needs fsck; rootfs is byte-identical to C69's fsck=0 image.
extracted = stage / 'partition-readback'
extracted.mkdir()
with image.open('rb') as stream:
    for name in ['boot.fat', 'rootfs.ext4']:
        row = regions[name]
        stream.seek(row['offset'])
        with (extracted / name).open('xb') as output:
            remaining = row['bytes']
            while remaining:
                data = stream.read(min(1024 * 1024, remaining))
                assert data
                output.write(data)
                remaining -= len(data)
        assert sha(extracted / name) == row['sha256']
run('partition-fsck', f'fsck.fat -n {rel(extracted / "boot.fat")}\n')
assert all(sha(extracted / name) == regions[name]['sha256'] for name in ['boot.fat', 'rootfs.ext4'])
compressed = image.with_suffix('.img.gz')
with image.open('rb') as source, compressed.open('xb') as output:
    with gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=epoch) as archive:
        shutil.copyfileobj(source, archive)
image_sha = sha(image)
with gzip.open(compressed, 'rb') as source:
    assert hashlib.file_digest(source, 'sha256').hexdigest() == image_sha
assert sha(root_image) == root_report['image_sha256']
assert (work / 'graphics-config/output/.config').read_bytes() == baseline.read_bytes()
sources = [Path(__file__), repo / 'port/scripts/phase4_card_image.py', repo / 'port/scripts/phase4_candidate.py',
           repo / 'port/device/rk-r35s-p0/uboot-ext4/board.h', repo / 'port/device/rk-r35s-p0/uboot-linux/boot.c']
analysis = {**verified, 'experiment': 'C70_PRIVATE_PANEL0_CARD_IMAGE',
    'private_only': True, 'redistribution_approved': False,
    'parent_proofs_sha256': parents, 'C69_analysis_sha256': sha(root_stage / 'analysis.json'),
    'C69_rootfs_sha256': root_report['image_sha256'], 'image_sha256': image_sha,
    'gzip_sha256': sha(compressed), 'gzip_bytes': compressed.stat().st_size,
    'regions': regions, 'fat_files_sha256': asset_hashes,
    'FAT_full_file_readback_matched': True, 'extracted_partition_hashes_matched': True,
    'FAT_readback_fsck_exit': 0, 'C69_rootfs_fsck_reused_after_exact_readback': True,
    'gzip_roundtrip_matched': True,
    'bootchain_rebuilt': False, 'kernel_DTB_rebuilt': False, 'UBoot_asset_hashes_matched': True,
    'UBoot_package_audit_sha256': sha(package / 'audit.json'),
    'UBoot_build_audit_sha256': sha(uboot / 'audit/report.json'),
    'default_boot': 'C07 via /sbin/muos-ext4-diag', 'factory_boot_counter': 0,
    'ui_autostart': False, 'session_autostart': False, 'preferences_autostart': False,
    'private_network_seed_host_keys_ROM_core_state_included': False,
    'provisioning_required_before_network_boot': True, 'userdata_partition_included': False,
    'device_contacted': False, 'device_written': False, 'image_hardware_boot_tested': False,
    'bit_reproducibility_tested': False, 'SDK_config_unchanged': True,
    'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}
(stage / 'analysis.json').write_text(json.dumps(analysis, indent=2) + '\n')
(area / 'latest-image').write_text(str(stage) + '\n')
print('C70 full private card image composed and read back; no device accessed:', stage)
print('SHA256:', image_sha)
