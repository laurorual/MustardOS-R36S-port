#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare a private provider source and a new additive firmware overlay."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
out = work / 'foundation'
out.mkdir(exist_ok=True)
assert not (out / 'provider-source').exists(), 'Foundation already prepared'
archive = work / 'mali-r13/rk3326_r13p0_gbm_with_vulkan_and_cl.zip'
with archive.open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == 'ef1a18fabf270d0a6029917d6b0e6237d328613c2f8be4d420ea23e022288dd9'
with zipfile.ZipFile(archive) as stream:
    binary = stream.read('libmali.so_rk3326_gbm_arm64_r13p0_with_vulkan_and_cl')
assert hashlib.sha256(binary).hexdigest() == '2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea'
source = out / 'provider-source'
source.mkdir()
sdk_source = work / 'graphics-config/output/build/rockchip-mali-721653b5b3b525a4f80d15aa7e2f9df7b7e6042'
# Only the API headers and .pc templates are reused, with notices intact.
# No older vendor userspace binary or its EULA is applied to the R13 binary.
shutil.copytree(sdk_source / 'include', source / 'include')
shutil.copytree(sdk_source / 'pkgconfig', source / 'pkgconfig')
library = source / 'lib/aarch64-linux-gnu/libmali-bifrost-g31-rxp0-gbm.so'
library.parent.mkdir(parents=True)
library.write_bytes(binary)
library.chmod(0o755)
(source / 'PRIVATE-NOTICE.txt').write_text(
    'Private RK3326 candidate authorized by the device owner on 2026-10-25.\n'
    'R13 binary: Hardkernel ZIP ef1a18fa..., SHA256 2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea.\n'
    'Its applicable license/EULA and redistribution terms are unresolved. Do not publish this package/image.\n'
    'API SDK: headers/pkg-config from JeffyCN/mirrors 721653b5b3b525a4f80d15aa7e2f9df7b7e60427.\n'
    'GBM header: Intel MIT-style notice; EGL/GLES/KHR headers: Khronos permissive notices, retained in each file.\n'
    'The older binary and its EULA are not used to license the R13 binary.\n')
overlay = out / 'overlay'
shutil.copytree(work / 'menu/assets', overlay)
(overlay / 'etc/default').mkdir(parents=True)
(overlay / 'etc/default/muos-core').write_text('audio=1\ninput=1\n')
core = json.loads((repo / 'port/device/rk-r35s-p0/core-config.json').read_text())
for ns, values in core.items():
    base = overlay / 'opt/muos' / {'device':'device/config','global':'config','system':'config/system'}[ns]
    for name, value in values.items():
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value + '\n')
manifest = {'purpose':'private coherent SDK/target provider and standalone boot contracts',
            'binary_source_sha256':hashlib.sha256(binary).hexdigest(),
            'sdk_revision':'721653b5b3b525a4f80d15aa7e2f9df7b7e60427',
            'redistribution_approved':False,'firmware_boot_tested':False,
            'provider_files':{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(source.rglob('*')) if p.is_file()}}
(out / 'provider-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('Private provider source prepared; target/sysroot will use the same R13; no device changes')
