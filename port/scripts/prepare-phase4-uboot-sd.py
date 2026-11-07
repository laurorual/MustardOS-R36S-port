#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Materialize a new owned source tree for the SD-only host build probe."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tarfile
import tempfile

repo = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--linux-assets', type=Path, help='manifest of the minimal diagnostic initramfs')
args = parser.parse_args()
diagnostic = args.linux_assets is not None
work = repo/'build/phase4'
out = work/'uboot-sd'
out.mkdir(exist_ok=True)
lock = json.loads((repo/'port/device/rk-r35s-p0/phase4-uboot-sources.json').read_text())
base = work/'uboot-base'
revision = subprocess.check_output(['git', '-C', str(base), 'rev-parse', 'HEAD'], text=True).strip()
assert revision == lock['revision']
assert not subprocess.check_output(['git', '-C', str(base), 'status', '--porcelain'], text=True).strip()
assert (work/'kernel-container.iid').read_text().strip() == lock['container_image_id']
kernel_lock = json.loads((repo/'port/device/rk-r35s-p0/phase4-sources.json').read_text())
compiler_revision = subprocess.check_output(['git', '-C', str(work/'linaro6'), 'rev-parse', 'HEAD'], text=True).strip()
assert compiler_revision == kernel_lock['kernel_compiler']['revision']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for name, digest in lock['recipe_payload_sha256'].items():
    assert sha(base/name) == digest, name
stage = Path(tempfile.mkdtemp(prefix='probe.', dir=out))
source = stage/'source'
source.mkdir()
baseline = stage/'baseline.tar'
with baseline.open('wb') as stream:
    subprocess.run(['git', '-C', str(base), 'archive', revision], stdout=stream, check=True)
with tarfile.open(baseline) as archive:
    archive.extractall(source, filter='data')
baseline.unlink()
# A local scratch Git directory makes plain git apply independent of the parent
# workspace. No commit/reset/clean is performed in either reference or base.
subprocess.run(['git', 'init', '-q', str(source)], check=True)
patch = repo/'port/patches/0007-uboot-r35s-sd-probe.patch'
subprocess.run(['git', 'apply', '--check', str(patch)], cwd=source, check=True)
subprocess.run(['git', 'apply', str(patch)], cwd=source, check=True)
owned = {
    'port/device/rk-r35s-p0/uboot-sd/board.c': 'board/rockchip/odroidgoa/muos-r35s-probe.c',
    'port/device/rk-r35s-p0/uboot-sd/board.h': 'include/configs/odroidgoa.h',
    'port/device/rk-r35s-p0/uboot-sd/memory.h': 'include/configs/muos-r35s-memory.h',
    'port/device/rk-r35s-p0/rk3326-muos-r35s-panel0-uboot.dts': 'arch/arm/dts/rk3326-muos-r35s-panel0-uboot.dts',
}
for name, target in owned.items():
    shutil.copy2(repo/name, source/target)
extra_modified = []
ext4_diagnostic = False
if diagnostic:
    asset_path = args.linux_assets.resolve()
    assert asset_path.is_relative_to(work/'linux-diagnostic')
    asset_record = json.loads(asset_path.read_text())
    ext4_diagnostic = asset_record.get('experiment') == 'MUOS-R35S-EXT4-P4-B01'
    assert asset_record['userspace_qemu_checked'], 'audit initramfs before preparing bootloader'
    for asset in asset_record['assets'].values():
        assert sha(Path(asset['path'])) == asset['sha256']
    owned.update({
        'port/device/rk-r35s-p0/uboot-sd/board.h':'include/configs/muos-r35s-monitor.h',
        'port/device/rk-r35s-p0/uboot-linux/board.h':'include/configs/odroidgoa.h',
        'port/device/rk-r35s-p0/uboot-linux/boot.c':'board/rockchip/odroidgoa/muos-r35s-linux.c'})
    if ext4_diagnostic:
        owned['port/device/rk-r35s-p0/uboot-linux/board.h']='include/configs/muos-r35s-linux.h'
        owned['port/device/rk-r35s-p0/uboot-ext4/board.h']='include/configs/odroidgoa.h'
    for name,target_name in owned.items():
        shutil.copy2(repo/name,source/target_name)
    with (source/'arch/arm/dts/rk3326-muos-r35s-panel0-uboot.dts').open('a') as stream:
        stream.write('\n/ { config { bootdelay = <3>; }; };\n')
    with (source/'board/rockchip/odroidgoa/Makefile').open('a') as stream:
        stream.write('\nobj-y += muos-r35s-linux.o\n')
    header = '/* Generated from verified diagnostic assets. */\n'
    names=[('Image','IMAGE'),('rk3326-muos-r35s-panel0.dtb','LINUX_FDT')]
    if not ext4_diagnostic:names.append(('initramfs.cpio.gz','INITRD'))
    for asset,macro in names:
        info=asset_record['assets'][asset]
        header += f'#define MUOS_{macro}_BYTES {info["bytes"]}UL\n'
        header += f'#define MUOS_{macro}_SHA256 {{'+','.join('0x'+info['sha256'][i:i+2] for i in range(0,64,2))+'}\n'
    generated='include/configs/muos-r35s-linux-assets.h'
    (source/generated).write_text(header)
    extra_modified.append(generated)
fragment_path = repo/'port/device/rk-r35s-p0/uboot-sd/config.fragment'
fragment = fragment_path.read_text()
if diagnostic:
    fragment=fragment.replace('CONFIG_BOOTDELAY=-1','CONFIG_BOOTDELAY=3')
def key(line):
    match = re.match(r'(?:# )?(CONFIG_[A-Z0-9_]+)(?:=| is not set)', line)
    return match[1] if match else None
keys = {key(line) for line in fragment.splitlines()} - {None}
config = '\n'.join(line for line in (base/'configs/odroidgoa_defconfig').read_text().splitlines() if key(line) not in keys)
config += '\n'+fragment
target = 'configs/muos_r35s_panel0_sd_defconfig'
(source/target).write_text(config)
# The source revision is captured below; avoid a misleading parent-repo/dirty banner.
(source/'.scmversion').write_text('')
inputs = [*owned, str(patch.relative_to(repo)), str(fragment_path.relative_to(repo)),
          'port/device/rk-r35s-p0/phase4-uboot-sources.json',
          'port/scripts/prepare-phase4-uboot-sd.py', 'port/scripts/build-phase4-uboot-sd.sh']
modified = [*owned.values(), *extra_modified, target, 'board/rockchip/odroidgoa/Makefile',
            'arch/arm/mach-rockchip/board.c', '.scmversion']
record = {'scope': 'host U-Boot SD monitor build only; no boot approval',
          'upstream': lock, 'kernel_compiler': kernel_lock['kernel_compiler'],
          'compiler_revision_verified': compiler_revision,
          'source_date_epoch': int(subprocess.check_output(['git', '-C', str(base), 'show', '-s', '--format=%ct', revision], text=True)),
          'port_inputs': {name: sha(repo/name) for name in inputs},
          'source_files': {name: sha(source/name) for name in modified},
          'profile':'ext4-diagnostic' if ext4_diagnostic else ('linux-diagnostic' if diagnostic else 'monitor'),
          'automatic_boot': diagnostic, 'persistent_environment': False,
          'kernel_boot_arguments': 'diagnostic /bin/sh, ro ext4; not product init',
          'media_written': False, 'device_tested': False}
if diagnostic:
    record['scope']='host build of diagnostic Linux handoff; not boot approval'
    record['kernel_boot_arguments']='rdinit=/init in minimal RAM root; no product services'
    record['diagnostic_assets_manifest']=str(asset_path)
    record['diagnostic_assets_manifest_sha256']=sha(asset_path)
    if ext4_diagnostic:record['kernel_boot_arguments']='ro PARTUUID ext4, init=/sbin/muos-ext4-diag; no initramfs or product rcS'
(stage/'inputs.json').write_text(json.dumps(record, indent=2)+'\n')
(out/'latest-build').write_text(str(stage)+'\n')
print('Prepared owned source tree:', stage)
