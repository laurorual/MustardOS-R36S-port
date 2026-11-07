#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare a pinned module/firmware overlay on the host; never load a module."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

repo = Path(__file__).resolve().parents[2]
work = repo/'build/phase4'
out = work/'modules'
out.mkdir(exist_ok=True)
lock_path = repo/'port/device/rk-r35s-p0/phase4-module-payload.json'
lock = json.loads(lock_path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked(path, digest):
    assert sha(path) == digest, path
    return path


for name, digest in lock['bsp_sha256'].items():
    checked(repo/'dist/phase4/bsp-probe'/name, digest)
checked(work/'kernel-output/System.map', lock['system_map_sha256'])
package = lock['firmware_package']
cache = out/'firmware-source'
cache.mkdir(exist_ok=True)
deb = cache/package['url'].rsplit('/', 1)[1]
if not deb.exists():
    partial = deb.with_suffix('.part')
    with urllib.request.urlopen(package['url'], timeout=60) as source, partial.open('wb') as target:
        shutil.copyfileobj(source, target)
    checked(partial, package['sha256']).replace(deb)
checked(deb, package['sha256'])

stage = Path(tempfile.mkdtemp(prefix='payload.', dir=out))
root = stage/'root'
root.mkdir()
with tarfile.open(repo/'dist/phase4/bsp-probe/modules.tar.gz') as archive:
    for member in archive.getmembers():
        assert (member.name == 'lib' or member.name.startswith('lib/')) and (member.isfile() or member.isdir()), member.name
    archive.extractall(root, filter='data')
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('module_audit', repo/'port/scripts/verify-phase4-modules.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
inventory = audit.verify(root)
assert inventory['release'] == lock['release']
(stage/'inventory.json').write_text(json.dumps(inventory, indent=2)+'\n')
modprobe = root/'etc/modprobe.d'
modprobe.mkdir(parents=True)
assert lock['blocked_autoload'] == ['rtk_btusb']
(modprobe/'r35s-bluetooth.conf').write_text(
    '# Use generic btusb/btrtl with rtl_bt firmware for the observed 0bda:c820.\n'
    '# Vendor rtk_btusb expects a different firmware naming/size contract.\n'
    'blacklist rtk_btusb\n')

container = (work/'rootfs-container.iid').read_text().strip()
relative = stage.relative_to(work)
command = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
           '--security-opt=no-new-privileges', '--userns=keep-id', '--tmpfs', '/tmp:rw,nosuid,nodev',
           '-v', f'{work}:/work:rw,z', container]
# Extract the verified Debian archive in the pinned build container, not with host-installed deps.
subprocess.run(command+['dpkg-deb', '-x', '/work/'+str(deb.relative_to(work)),
                        '/work/'+str(relative/'firmware')], check=True)
extracted = stage/'firmware'
for name, digest in package['files'].items():
    source = checked(extracted/'usr/lib/firmware'/name, digest)
    target = root/'lib/firmware'/name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
license_dir = root/'usr/share/licenses/r35s-module-payload'
license_dir.mkdir(parents=True)
shutil.copy2(extracted/'usr/share/doc/firmware-realtek/copyright', license_dir/'firmware-realtek-copyright')
shutil.copy2(repo/'dist/phase4/bsp-probe/COPYING.linux', license_dir/'COPYING.linux')
shutil.copy2(repo/'dist/phase4/bsp-probe/sources.json', license_dir/'kernel-sources.json')
shutil.copy2(lock_path, license_dir/'payload-lock.json')
# No source-package extras, alternate radios or renamed vendor firmware enter the overlay.
shutil.rmtree(extracted)

shell = r'''
set -eu
stage=$1
release=$2
root=$stage/root
tool=/work/graphics-config/output/host/bin
"$tool/depmod" --version > "$stage/kmod-version.txt"
"$tool/depmod" -e -F /work/kernel-output/System.map -b "$root" "$release" > "$stage/depmod.log" 2>&1
"$tool/modprobe" -C "$root/etc/modprobe.d" -d "$root" -S "$release" -b --show-depends "$3" > "$stage/wifi-dry-run.txt" 2>&1
"$tool/modprobe" -C "$root/etc/modprobe.d" -d "$root" -S "$release" -b --show-depends "$4" > "$stage/bluetooth-dry-run.txt" 2>&1
'''
subprocess.run(command+['sh', '-c', shell, 'module-audit', '/work/'+str(relative), lock['release'],
                        lock['usb_aliases']['wifi'], lock['usb_aliases']['bluetooth']], check=True)
assert '8821cu.ko' in (stage/'wifi-dry-run.txt').read_text()
bt = (stage/'bluetooth-dry-run.txt').read_text()
assert 'btusb.ko' in bt and 'btrtl.ko' in bt and 'rtk_btusb.ko' not in bt, bt
log = (stage/'depmod.log').read_text()
assert 'unknown symbol' not in log.lower(), log
record = {'scope': 'host static preparation and modprobe --show-depends only; no module loaded',
          'lock': lock, 'lock_sha256': sha(lock_path), 'container_image_id': container,
          'aarch64_et_rel_count': inventory['aarch64_et_rel_count'],
          'declared_dependencies_closed': True, 'depmod_system_map_unknown_symbols': False,
          'host_alias_dry_runs_passed': True, 'candidate_kernel_booted': False,
          'optional_firmware_inventory_complete': False,
          'overlay_sha256': {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}}
(stage/'manifest.json').write_text(json.dumps(record, indent=2)+'\n')
(out/'latest-payload').write_text(str(stage)+'\n')
print('Prepared without loading modules:', stage)
