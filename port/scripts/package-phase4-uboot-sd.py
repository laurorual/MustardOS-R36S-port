#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pack local files with source-built GPL tools; never access a block device."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[2]
work = repo/'build/phase4'
stage = Path((work/'uboot-sd/latest-build').read_text().strip())
assert stage.is_relative_to(work/'uboot-sd')
report = json.loads((stage/'audit/report.json').read_text())
assert report['passed'] and not report['boot_tested']
output = stage/'output'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
for name, digest in report['output_sha256'].items():
    assert sha(output/name) == digest, name
for name, digest in report['inputs']['port_inputs'].items():
    assert sha(repo/name) == digest, name
lock = report['inputs']['upstream']
package = Path(tempfile.mkdtemp(prefix='package.', dir=stage))
payloads = package/'payloads'
payloads.mkdir()
for name, digest in lock['recipe_payload_sha256'].items():
    source = work/'uboot-base'/name
    assert sha(source) == digest, name
    shutil.copy2(source, payloads/Path(name).name)
control = '''[VERSION]
MAJOR=1
MINOR=0
[BL30_OPTION]
SEC=0
[BL31_OPTION]
SEC=1
PATH=payloads/rk3326_bl31_v1.14.elf
ADDR=0x00010000
[BL32_OPTION]
SEC=1
PATH=payloads/rk3326_bl32_v1.10.bin
ADDR=0x08400000
[BL33_OPTION]
SEC=0
[OUTPUT]
PATH=trust.img
'''
(package/'RK3326TRUST.ini').write_text(control)
tools = {name: sha(output/'tools'/name) for name in ['mkimage', 'loaderimage', 'trust_merger']}
container = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
             '--security-opt=no-new-privileges', '--userns=keep-id', '--tmpfs', '/tmp:rw,nosuid,nodev',
             '-v', f'{work}:/work:rw,z', '-e', 'PACKAGE_REL='+str(package.relative_to(work)),
             '-e', 'UBOOT_REL='+str(stage.relative_to(work)), lock['container_image_id']]
shell = r'''
set -eu
cd /work/$PACKAGE_REL
tools=/work/$UBOOT_REL/output/tools
"$tools/mkimage" -n px30 -T rksd -d payloads/rk3326_ddr_333MHz_v1.10.bin idb-ddr.img > idb-pack.log 2>&1
cat idb-ddr.img payloads/rk3326_miniloader_v1.12.bin > idbloader.img
"$tools/loaderimage" --pack --uboot /work/$UBOOT_REL/output/u-boot.bin uboot.img 0x00200000 --size 1024 4 > uboot-pack.log 2>&1
"$tools/trust_merger" --rsa 3 --sha 3 --size 2048 2 RK3326TRUST.ini > trust-pack.log 2>&1
'''
with (package/'run.log').open('w') as log:
    subprocess.run(container+['sh', '-c', shell], stdout=log, stderr=subprocess.STDOUT, check=True)
record = {'scope': 'private local container packaging only; no image assembled, media written or boot test',
          'u_boot_audit_sha256': sha(stage/'audit/report.json'),
          'source_built_gpl_tool_sha256': tools,
          'payloads': {p.name: sha(p) for p in sorted(payloads.iterdir())},
          'container_image_id': lock['container_image_id'],
          'controls_sha256': sha(package/'RK3326TRUST.ini'),
          'outputs_sha256': {name: sha(package/name) for name in ['idb-ddr.img', 'idbloader.img', 'uboot.img', 'trust.img']},
          'packaging_port_input_sha256': sha(Path(__file__)),
          'vendor_prebuilt_host_tools_executed': False,
          'private_only': True, 'media_written': False, 'boot_tested': False}
(package/'manifest.json').write_text(json.dumps(record, indent=2)+'\n')
(stage/'latest-package').write_text(str(package)+'\n')
print('Packed local files only:', package)
