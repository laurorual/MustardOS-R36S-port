#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Populate the private overlay; no device access or automatic frontend start."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import tarfile

parser = argparse.ArgumentParser()
parser.add_argument('--validated-runtime', action='store_true',
                    help='Include the frozen full-frontend proof components, without autostart')
parser.add_argument('--init-services', action='store_true', help='Install the new lifecycle services, disabled by default')
parser.add_argument('--enable-ui', action='store_true', help='Enable UI startup only after the lifecycle and visual approval')
parser.add_argument('--bsp-modules', action='store_true', help='Include pinned candidate modules/firmware; never load them')
args = parser.parse_args()
assert not args.init_services or args.validated_runtime, '--init-services requires --validated-runtime'
assert not args.enable_ui or args.init_services, '--enable-ui requires --init-services'

repo = Path(__file__).resolve().parents[2]
out = repo / 'build/phase4/foundation'
assert (out / 'frontend-compile.exit').read_text().strip() == '0'
overlay = out / 'overlay'
assert args.init_services or not (overlay / 'etc/init.d/S99muos-ui').exists(), \
    'This overlay already owns init services; retain --init-services to avoid mixing profiles'
assert args.bsp_modules or not (overlay / 'lib/modules').exists(), \
    'This overlay already owns BSP modules; retain --bsp-modules to verify their payload'
dest = overlay / 'opt/muos/frontend'
shutil.copytree(out / 'frontend-bin', dest, dirs_exist_ok=True)
for path in dest.rglob('*'):
    if path.is_file():
        path.chmod(0o755)
(overlay / 'etc/init.d').mkdir(parents=True, exist_ok=True)
shutil.copy2(repo / 'port/device/rk-r35s-p0/S90muos-storage', overlay / 'etc/init.d/S90muos-storage')
(overlay / 'etc/init.d/S90muos-storage').chmod(0o755)
(overlay / 'usr/libexec').mkdir(parents=True, exist_ok=True)
shutil.copy2(repo / 'port/device/rk-r35s-p0/S95muos-core', overlay / 'usr/libexec/muos-core-lifecycle')
(overlay / 'usr/libexec/muos-core-lifecycle').chmod(0o755)
shutil.copy2(repo / 'port/device/rk-r35s-p0/S95muos-foundation-core', overlay / 'etc/init.d/S95muos-core')
(overlay / 'etc/init.d/S95muos-core').chmod(0o755)
(overlay / 'etc/muos-private-foundation').write_text('Private R35S Panel 0 foundation; boot not validated\n')
# Persistent data live on this candidate's root partition. No installed Debian
# paths or removable block nodes are read, mounted, or formatted by the adapter.
(overlay / 'userdata').mkdir(exist_ok=True)
(overlay / 'etc/default/muos-storage').write_text('fstype=ext4\n')
(overlay / 'usr/share/licenses/muos-frontend').mkdir(parents=True, exist_ok=True)
shutil.copy2(out / 'frontend-source/LICENSE', overlay / 'usr/share/licenses/muos-frontend/LICENSE')
shutil.copy2(out / 'deps/mojibake-0.3.6/LICENSE', overlay / 'usr/share/licenses/muos-frontend/mojibake-LICENSE')
runtime = None
if args.validated_runtime:
    proof = repo / 'dist/phase4/frontend-full-native'
    # Consume the immutable proof, rather than an edited RAM test directory.
    checksums = {}
    for line in (proof / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        checksums[name] = digest
    def checked(name):
        path = proof / name
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == checksums[name], name
        return path
    approved = json.loads(checked('audio-approved.json').read_text())
    manifest = json.loads(checked('staging-manifest.json').read_text())
    assert approved['user_confirmed'] and approved['result']['returncode'] == 0
    assert approved['staging_sha256'] == manifest['staging_sha256']
    assert manifest['board_delta'].startswith('0006:')
    for path in (proof / 'frontend-bin').rglob('*'):
        if path.is_file():
            name = str(path.relative_to(proof))
            checked(name)
            rel = path.relative_to(proof / 'frontend-bin')
            assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['frontend_overlay_sha256'][str(rel)]
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    resources = out / 'validated-resources'
    resources.mkdir(exist_ok=True)
    with tarfile.open(checked('internal-resources-source.tar.gz')) as archive:
        archive.extractall(resources, filter='data')
    for name, oid in manifest['runtime_resource_blobs'].items():
        data = (resources / name).read_bytes()
        assert hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest() == oid
        target = overlay / 'opt/muos' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o755)
    name = 'share/info/manifest/core.json'
    data = (resources / name).read_bytes()
    assert hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest() == manifest['core_manifest_git_blob']
    target = overlay / 'opt/muos' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    shutil.copy2(checked('helpers/muos-sdl-map'), dest / 'muos-sdl-map')
    (dest / 'muos-sdl-map').chmod(0o755)
    # Keep the four reviewed bring-up bindings, not a complete power policy.
    with tarfile.open(checked('port-source.tar.gz')) as archive:
        stream = archive.extractfile('port/device/rk-r35s-p0/session-hotkeys.json')
        data = stream.read()
    target = overlay / 'opt/muos/share/hotkey/r35s-bringup.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    for ns, key, value in [('device','storage/rom/mount','/mnt/mmc'),
                            ('device','storage/sdcard/mount','/mnt/sdcard'),
                            ('global','settings/advanced/incvolume','5'),
                            ('global','settings/advanced/incbright','5'),
                            ('global','settings/power/idle_display','0'),
                            ('global','settings/power/idle_sleep','0')]:
        base = 'device/config' if ns == 'device' else 'config'
        p = overlay / 'opt/muos' / base / key
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(value + '\n')
    runtime = {'proof':'dist/phase4/frontend-full-native',
               'approved_staging_sha256':approved['staging_sha256'],
               'board_patch':'0006-frontend-r35s-normalized-volume.patch',
               'resource_blobs':manifest['runtime_resource_blobs'],
               'mapper_installed':'/opt/muos/frontend/muos-sdl-map',
               'hotkeys':'four bring-up actions; no Power/hold/idle',
               'diagnostic_help_wave_replacements_included':False,
               'software_boot_volume_changed':False}
if args.init_services:
    build = repo / 'build/phase4/init-services'
    services = json.loads((build / 'build-manifest.json').read_text())
    for name, digest in services['inputs'].items():
        assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest, name
    for name, target in [('muos-ui-supervisor', overlay / 'usr/libexec/muos-ui-supervisor'),
                         ('muos-sdl-map', dest / 'muos-sdl-map')]:
        p = build / 'bin' / name
        assert hashlib.sha256(p.read_bytes()).hexdigest() == services['bin_sha256'][name]
        shutil.copy2(p, target)
        target.chmod(0o755)
    for name in ['S96muos-input-ready', 'S99muos-ui']:
        p = overlay / 'etc/init.d' / name
        shutil.copy2(repo / 'port/device/rk-r35s-p0' / name, p)
        p.chmod(0o755)
    if args.enable_ui:
        approved = json.loads((build / 'ui-approved.json').read_text())
        assert approved['user_confirmed'] and approved['result']['passed']
        assert approved['tested_services'] == services, 'Lifecycle binaries/scripts changed since the approved test'
        lifecycle = json.loads((build / 'lifecycle-approved.json').read_text())
        assert lifecycle['passed']
    (overlay / 'etc/default/muos-ui').write_text(f'enabled={int(args.enable_ui)}\nhotkeys=1\nattempts=60\n')
modules = None
if args.bsp_modules:
    payload = Path((repo / 'build/phase4/modules/latest-payload').read_text().strip())
    assert payload.is_relative_to(repo / 'build/phase4/modules')
    modules = json.loads((payload / 'manifest.json').read_text())
    lock_path = repo / 'port/device/rk-r35s-p0/phase4-module-payload.json'
    assert hashlib.sha256(lock_path.read_bytes()).hexdigest() == modules['lock_sha256']
    assert modules['aarch64_et_rel_count'] == 555 and modules['host_alias_dry_runs_passed']
    assert not modules['candidate_kernel_booted']
    for name, digest in modules['overlay_sha256'].items():
        source = payload / 'root' / name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, name
        target = overlay / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
record = {'scope': 'private candidate overlay; complete UI linked, not runtime-approved',
          'init_order': ['Buildroot eudev', 'Buildroot D-Bus', 'S90muos-storage', 'S95muos-core'] +
                        (['S96muos-input-ready', 'S99muos-ui'] if args.init_services else []),
          'frontend_autostart': args.enable_ui, 'firmware_boot_tested': False,
          'validated_runtime_components': runtime,
          'init_services': services if args.init_services else None,
          'bsp_modules': modules,
          'storage': {'primary': '/userdata on root ext4', 'rom_bind': '/mnt/mmc', 'sd2_enabled': False},
          'overlay_sha256': {str(p.relative_to(overlay)): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted(overlay.rglob('*')) if p.is_file()}}
(out / 'overlay-manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print(f'Private overlay prepared; frontend autostart configured={args.enable_ui}; no device access')
