#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Audit new network ELFs against the seedless C06 blueprint; no device access."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
record = work / 'network-tools'
sdk = work / 'graphics-config/output'
base = work / 'linux-diagnostic/frontend-navigation-level.ed62uz58'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inside(root, name):
    """Resolve target-absolute links inside root, never against the host /."""
    parts = list(Path(name).parts)
    current = root
    links = 0
    while parts:
        part = parts.pop(0)
        if part in ('/', '.'):
            continue
        if part == '..':
            assert current != root
            current = current.parent
            continue
        current /= part
        if current.is_symlink():
            links += 1
            assert links < 40
            link = Path(current.readlink())
            current = root if link.is_absolute() else current.parent
            parts = list(link.parts) + parts
    return current


def dependency(root, name):
    assert '/' not in name
    for folder in ('lib', 'usr/lib'):
        path = inside(root, folder + '/' + name)
        if path.is_file():
            return path
    return None


def config(path):
    return dict(line.split('=', 1) for line in path.read_text().splitlines()
                if line.startswith('BR2_') and '=' in line)


assert (record / 'build.exit').read_text().strip() == '0'
assert (record / 'baseline.config').read_bytes() == (sdk / '.config').read_bytes()
assert sha(base / 'rootfs.ext4') == json.loads((base / 'manifest.json').read_text())['rootfs_sha256']
assert not (base / 'extracted/var/lib/muos-seedrng').exists()
a = config(record / 'baseline.config')
b = config(record / 'resolved.config')
for key in a.keys() | b.keys():
    if key.startswith(('BR2_TOOLCHAIN', 'BR2_GCC', 'BR2_BINUTILS', 'BR2_KERNEL_HEADERS', 'BR2_GLIBC')):
        assert a.get(key) == b.get(key), key
assert all(b.get('BR2_PACKAGE_' + name) == 'y' for name in
           ('DROPBEAR', 'WPA_SUPPLICANT', 'WPA_SUPPLICANT_NL80211', 'WPA_SUPPLICANT_WEXT', 'USB_MODESWITCH'))
stage = Path(tempfile.mkdtemp(prefix='audit.', dir=record))
root = stage / 'root'
shutil.copytree(base / 'extracted', root, symlinks=True)
files = {}
reused = {}
queue = []
for name in ('usr/sbin/dropbear', 'usr/sbin/wpa_supplicant', 'usr/sbin/wpa_cli', 'usr/sbin/usb_modeswitch'):
    source = inside(sdk / 'target', name)
    assert source.is_file() and not (root / name).exists(), name
    shutil.copyfile(source, root / name)
    (root / name).chmod(0o755)
    files[name] = {'source_sha256': sha(source)}
    queue.append(name)
shutil.copyfile(root / 'usr/sbin/dropbear', root / 'usr/bin/dropbearkey')
(root / 'usr/bin/dropbearkey').chmod(0o755)
files['usr/bin/dropbearkey'] = {'source_sha256': sha(root / 'usr/sbin/dropbear')}
while queue:
    name = queue.pop(0)
    header = subprocess.check_output(['readelf', '-h', str(root / name)], text=True)
    assert 'AArch64' in header and 'ELF64' in header, name
    dynamic = subprocess.check_output(['readelf', '-d', str(root / name)], text=True)
    rpaths = re.findall(r'\((?:RPATH|RUNPATH)\).*?\[(.*?)\]', dynamic)
    if rpaths:
        # Target finalization normally sanitizes libtool's build-tree RPATH.
        # We intentionally did not run make all; sanitize only these copies.
        assert rpaths == ['/work/graphics-config/output/build/libnl-3.11.0/lib/.libs'], (name, rpaths)
        files[name]['removed_build_rpath'] = rpaths[0]
    for needed in re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic):
        existing = dependency(base / 'extracted', needed)
        source = dependency(sdk / 'target', needed)
        assert source is not None, (name, needed)
        if existing is not None:
            assert sha(existing) == sha(source), ('Existing library changed', needed)
            reused[needed] = sha(existing)
        elif 'usr/lib/' + needed not in files:
            target = 'usr/lib/' + needed
            assert not (root / target).exists()
            shutil.copyfile(source, root / target)
            (root / target).chmod(0o755)
            files[target] = {'source_sha256': sha(source)}
            queue.append(target)

# Work on this host-only clone; no live root or private provisioning is included.
commands = ['set -eu', 'root=/work/' + str(root.relative_to(work)),
            'strip=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-strip',
            'patchelf=/work/graphics-config/output/host/bin/patchelf']
for name in files:
    commands.append('"$patchelf" --remove-rpath "$root/' + name + '"')
    commands.append('"$strip" --strip-unneeded "$root/' + name + '"')
for name in ('usr/sbin/dropbear', 'usr/sbin/wpa_supplicant', 'usr/sbin/wpa_cli', 'usr/bin/dropbearkey', 'usr/sbin/usb_modeswitch'):
    commands.append('qemu-aarch64 -cpu cortex-a35 -L "$root" -E LD_BIND_NOW=1 '
                    '"$root/lib/ld-linux-aarch64.so.1" --list "$root/' + name + '"')
commands += ['qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/usr/sbin/dropbear" -V',
             'qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/usr/sbin/wpa_supplicant" -v',
             'qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/usr/sbin/wpa_cli" -v',
             'qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/usr/sbin/usb_modeswitch" --version']
container = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
             '--security-opt=no-new-privileges', '--userns=keep-id', '--tmpfs', '/tmp:rw,nosuid,nodev',
             '-v', f'{work}:/work:rw,z', (work / 'rootfs-container.iid').read_text().strip(),
             'sh', '-c', '\n'.join(commands)]
with (stage / 'loader-qemu.log').open('w') as output:
    result = subprocess.run(container, stdout=output, stderr=subprocess.STDOUT, timeout=90)
assert result.returncode == 0, stage / 'loader-qemu.log'
for name in files:
    dynamic = subprocess.check_output(['readelf', '-d', str(root / name)], text=True)
    assert '(RPATH)' not in dynamic and '(RUNPATH)' not in dynamic, name
    files[name]['sha256'] = sha(root / name)
    files[name]['bytes'] = (root / name).stat().st_size
licenses = {
    'dropbear': ('dropbear-2026.93', ['LICENSE', 'libtommath/LICENSE', 'libtomcrypt/LICENSE']),
    'wpa_supplicant': ('wpa_supplicant-2.12', ['README']),
    'libnl': ('libnl-3.11.0', ['COPYING']),
    'libxcrypt': ('libxcrypt-4.4.38', ['LICENSING', 'COPYING.LIB']),
    'usb_modeswitch': ('usb_modeswitch-2.6.1', ['COPYING']),
    'libusb': ('libusb-1.0.30', ['COPYING']),
}
for package, (folder, names) in licenses.items():
    for name in names:
        target = stage / 'licenses' / package / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sdk / 'build' / folder / name, target)
report = {'scope': 'C07 host-only ELF/loader/version audit against seedless C06 root; no network/key generation/device test',
          'passed': True, 'stage': str(stage), 'new_files': files, 'existing_libraries_verified': reused,
          'baseline_config_restored': True, 'seed_or_credentials_included': False,
          'config_diff': {k: [a.get(k), b.get(k)] for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k)},
          'base_manifest_sha256': sha(base / 'manifest.json'),
          'build_controller_sha256': sha(repo / 'port/scripts/build-phase4-network-tools.sh'),
          'audit_script_sha256': sha(Path(__file__)),
          'physical_wifi_dhcp_ssh_tested': False}
(stage / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
(record / 'latest-audit').write_text(str(stage) + '\n')
print('C07 network tools host audit passed:', stage)
