#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Assemble a private monitor image in a fresh regular file; never flash media."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--linux-diagnostic',action='store_true')
parser.add_argument('--ext4-diagnostic',action='store_true')
args=parser.parse_args()
assert not (args.linux_diagnostic and args.ext4_diagnostic)
ext4_diagnostic=args.ext4_diagnostic
diagnostic=args.linux_diagnostic or ext4_diagnostic
work = repo/'build/phase4'
stage = Path((work/'uboot-sd/latest-build').read_text().strip())
package = Path((stage/'latest-package').read_text().strip())
assert stage.is_relative_to(work/'uboot-sd') and package.is_relative_to(stage)
report = json.loads((stage/'audit/report.json').read_text())
pack = json.loads((package/'audit.json').read_text())
assert report['passed'] and report['visual_monitor_prepared']
assert report['automatic_boot'] is diagnostic
assert report['inputs'].get('profile','monitor') == ('ext4-diagnostic' if ext4_diagnostic else ('linux-diagnostic' if diagnostic else 'monitor'))
assert pack['passed'] and not pack['boot_tested']
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
assert pack['manifest']['u_boot_audit_sha256'] == sha(stage/'audit/report.json')
for name, digest in pack['output_sha256'].items():
    assert sha(package/name) == digest, name
tools_id = (work/'media-tools-container.iid').read_text().strip()
assert tools_id == 'sha256:4d5c100835e155188d742a07aa0ae8823bed2fefa26770e23d5cea559b83a8a8'
image_dir = Path(tempfile.mkdtemp(prefix='linux-image.' if diagnostic else 'monitor-image.', dir=stage))
assets = image_dir/'assets'
assets.mkdir()
dtb_name = 'rk3326-muos-r35s-panel0-uboot.dtb'
shutil.copy2(stage/dtb_name, assets/dtb_name)
assert sha(assets/dtb_name) == report['display']['candidate_sha256']
shutil.copy2(stage/'source/Licenses/gpl-2.0.txt', assets/'COPYING.TXT')
(assets/'PROBE.TXT').write_text(
    'PRIVATE R35S / R36S-V12 2023-08-18 Panel 0 monitor only.\n'
    'Automatic kernel boot is OFF. No Linux Image, rootfs or frontend included.\n'
    'Expected screen: muOS - R35S / Panel 0; SD monitor: U-Boot reached.\n'
    'Native display and memory values need physical confirmation.\n'
    'Never install on the existing dArkOSen card. Write only to explicitly identified test media.\n'
    'DDR/miniloader/BL31/BL32 terms remain pending. Private use only.\n')
if diagnostic:
    manifest_path=Path(report['inputs']['diagnostic_assets_manifest'])
    assert sha(manifest_path)==report['inputs']['diagnostic_assets_manifest_sha256']
    linux=json.loads(manifest_path.read_text())
    for name,info in linux['assets'].items():
        assert sha(Path(info['path']))==info['sha256']
        shutil.copy2(info['path'],assets/name)
    (assets/'DIAG.ID').write_text(linux['experiment']+'\n')
    (assets/'PROBE.TXT').write_text(
        'PRIVATE R35S / Panel 0 Linux diagnostic, MUOS-R35S-LINUX-P4-A01.\n'
        'Own Linux + minimal RAM init start automatically. No product rootfs/UI/network.\n'
        'Expected final screen: INIT REACHED / Logs saved: DIAG01 (FAT unmounted).\n'
        'Only the identified test card may receive DIAG01 logs. Keep stock OS card outside.\n'
        'Hold Power to turn off before changing cards. Read DIAG01 after stock-card recovery.\n'
        'Private boot-chain payloads have unresolved terms; no redistribution approval.\n')
    if ext4_diagnostic:
        (assets/'PROBE.TXT').write_text(
            'PRIVATE MUOS-R35S-EXT4-P4-B01. Own kernel + diagnostic PID1 from p2 ext4.\n'
            'No initramfs, product rcS, frontend or networking. UI enabled=0.\n'
            'Only the identified 128-GB test card may be present. Keep stock card outside.\n'
            'Expected: ROOT REACHED / STORAGE_OK / GPIO_KEYS_OK / DIAG02 logs saved.\n'
            'Root restored read-only and FAT unmounted before final marker.\n'
            'Private payloads, unresolved license terms; no redistribution approval.\n')
epoch = report['inputs']['source_date_epoch']
for p in assets.iterdir():
    os.utime(p, (epoch, epoch))
partition_start = 32768*512
partition_bytes = 204800*512
image_bytes = (640 if ext4_diagnostic else 128)*1024*1024
fat = image_dir/'boot.fat'
with fat.open('xb') as stream:
    stream.truncate(partition_bytes)
raw_image = image_dir/('muos-r35s-panel0-ext4-diag.img' if ext4_diagnostic else ('muos-r35s-panel0-linux-diag.img' if diagnostic else 'muos-r35s-panel0-monitor.img'))
disk_signature = 0x4d554432 if ext4_diagnostic else (0x4d554431 if diagnostic else 0x4d553435)
label='MUOSDIAG' if diagnostic else 'MUOSMON'
mbr = bytearray(512)
struct.pack_into('<I', mbr, 440, disk_signature)
mbr[446:462] = struct.pack('<B3sB3sII', 0x80, b'\xfe\xff\xff', 0x0c,
                           b'\xfe\xff\xff', partition_start//512, partition_bytes//512)
if ext4_diagnostic:
    root_info=linux['rootfs'];root_image=Path(root_info['path'])
    assert sha(root_image)==root_info['sha256'] and root_info['bytes']==512*1024*1024
    assert linux['root_partuuid']=='4d554432-02'
    root_offset=128*1024*1024
    assert partition_start+partition_bytes<=root_offset and root_offset+root_info['bytes']==image_bytes
    mbr[462:478]=struct.pack('<B3sB3sII',0,b'\xfe\xff\xff',0x83,b'\xfe\xff\xff',root_offset//512,root_info['bytes']//512)
mbr[510:512] = b'\x55\xaa'
with raw_image.open('xb') as stream:
    stream.truncate(image_bytes)
    stream.write(mbr)
if ext4_diagnostic:
    with raw_image.open('r+b') as target,root_image.open('rb') as source:
        target.seek(root_offset);shutil.copyfileobj(source,target)
regions = [('idbloader.img', 64*512), ('uboot.img', 16384*512), ('trust.img', 24576*512)]
for index, (name, offset) in enumerate(regions):
    limit = regions[index+1][1] if index+1 < len(regions) else partition_start
    assert offset+(package/name).stat().st_size <= limit
    with raw_image.open('r+b') as target, (package/name).open('rb') as source:
        target.seek(offset)
        shutil.copyfileobj(source, target)
container = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
             '--security-opt=no-new-privileges', '--userns=keep-id', '--tmpfs', '/tmp:rw,nosuid,nodev',
             '-v', f'{work}:/work:rw,z', '-e', 'MONITOR_IMAGE_REL='+str(image_dir.relative_to(work)),
             '-e','FS_LABEL='+label,'-e',f'DISK_ID={disk_signature:08x}',
             '-e','RAW_IMAGE_NAME='+raw_image.name,tools_id]
shell = r'''
set -eu
cd "/work/$MONITOR_IMAGE_REL"
mkfs.fat --invariant -F 32 -n "$FS_LABEL" -i "$DISK_ID" boot.fat > mkfs.log 2>&1
mcopy -m -i boot.fat assets/* ::/
fsck.fat -n boot.fat > fsck-fat.log 2>&1
cat /usr/local/share/phase4-media-packages.txt > media-packages.txt
'''
with (image_dir/'tools.log').open('w') as log:
    subprocess.run(container+['sh', '-c', shell], stdout=log, stderr=subprocess.STDOUT, check=True)
with raw_image.open('r+b') as target, fat.open('rb') as source:
    target.seek(partition_start)
    shutil.copyfileobj(source, target)
shell = r'''
set -eu
cd "/work/$MONITOR_IMAGE_REL"
mkdir readback
mdir -i "$RAW_IMAGE_NAME"@@16777216 ::/ > fat-directory.txt
mcopy -m -i "$RAW_IMAGE_NAME"@@16777216 "::/*" readback/
/work/graphics-config/output/host/sbin/fdisk -l "$RAW_IMAGE_NAME" > partition-table.txt
'''
with (image_dir/'readback.log').open('w') as log:
    subprocess.run(container+['sh', '-c', shell], stdout=log, stderr=subprocess.STDOUT, check=True)
assert sorted(p.name for p in (image_dir/'readback').iterdir()) == sorted(p.name for p in assets.iterdir())
for p in assets.iterdir():
    assert sha(p) == sha(image_dir/'readback'/p.name), p.name
with raw_image.open('rb') as stream:
    assert stream.read(512) == mbr
    for name, offset in regions:
        stream.seek(offset)
        assert stream.read((package/name).stat().st_size) == (package/name).read_bytes()
    stream.seek(partition_start)
    assert hashlib.sha256(stream.read(partition_bytes)).hexdigest() == sha(fat)
    if ext4_diagnostic:
        stream.seek(root_offset)
        digest=hashlib.sha256()
        remaining=root_info['bytes']
        while remaining:
            data=stream.read(min(1024*1024,remaining));assert data
            digest.update(data);remaining-=len(data)
        assert digest.hexdigest()==root_info['sha256']
compressed = raw_image.with_suffix('.img.gz')
with raw_image.open('rb') as source, compressed.open('xb') as target:
    with gzip.GzipFile(filename='', mode='wb', fileobj=target, mtime=epoch) as archive:
        shutil.copyfileobj(source, archive)
with gzip.open(compressed, 'rb') as source:
    assert hashlib.file_digest(source, 'sha256').hexdigest() == sha(raw_image)
record = {'scope': 'private host-assembled '+('Linux diagnostic' if diagnostic else 'monitor')+' image; no runtime approval',
          'model': 'R36S-V12 2023-08-18 Panel 0', 'image_bytes': image_bytes,
          'image_sha256': sha(raw_image), 'gzip_sha256': sha(compressed),
          'gzip_bytes': compressed.stat().st_size, 'disk_signature': hex(disk_signature),
          'partition': {'number':1,'type':'0x0c','start_sector':32768,'sectors':204800,'label':label,'filesystem':'FAT32'},
          'regions': {name:{'sector':offset//512,'bytes':(package/name).stat().st_size,'sha256':sha(package/name)} for name,offset in regions},
          'fat_files_sha256':{p.name:sha(p) for p in sorted(assets.iterdir())},
          'container_image_id':tools_id,'tool_versions':(image_dir/'media-packages.txt').read_text().splitlines(),
          'fat_fsck_passed':True,'final_image_fat_readback_passed':True,
          'u_boot_audit_sha256':sha(stage/'audit/report.json'),'package_audit_sha256':sha(package/'audit.json'),
          'port_inputs':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/packaging/phase4-media-tools.Containerfile']},
          'automatic_kernel_boot':diagnostic,'linux_rootfs_included':diagnostic,
          'product_rootfs_included':ext4_diagnostic,'private_only':True,
          'media_written':False,'hardware_boot_tested':False,'bit_reproducibility_tested':False}
(image_dir/'manifest.json').write_text(json.dumps(record, indent=2)+'\n')
if diagnostic:
    record['linux_assets_manifest_sha256']=sha(manifest_path)
    record['diagnostic_experiment']=linux['experiment']
    if ext4_diagnostic:record['root_partition']={'number':2,'type':'0x83','start_sector':root_offset//512,'sectors':root_info['bytes']//512,'partuuid':'4d554432-02','sha256':root_info['sha256'],'readback_verified':True}
    (image_dir/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
(stage/('latest-linux-image' if diagnostic else 'latest-monitor-image')).write_text(str(image_dir)+'\n')
print('Private monitor image built and checked; no media access:', image_dir)
