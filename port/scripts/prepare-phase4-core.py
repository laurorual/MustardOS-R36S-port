#!/usr/bin/env python3
"""Prepare pinned sources outside refs, including sparse-checkout Git objects."""
from pathlib import Path
import hashlib
import io
import json
import shutil
import subprocess
import tarfile

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4/core'
source = work / 'source'
work.mkdir(parents=True, exist_ok=True)
if source.exists():
    shutil.rmtree(source)
source.mkdir()
specs = {
    'frontend': ('refs/muos/frontend', '5e8635b3b485eec9ad2ace141c415fd2df47d8f1',
                 ['LICENSE', 'input', 'common', 'module/muvarctl.c', 'module/mulog.c']),
    'internal': ('refs/muos/internal', '550cc58f9cd3449a17f53ca55efcdc6c473b5a89',
                 ['LICENSE', 'script/var/base.sh', 'script/var/config.sh', 'script/var/log.sh',
                  'script/var/audio.sh', 'script/init/S80pipewire.sh', 'script/mux/audio_sink.sh',
                  'share/conf/pipewire.conf', 'share/conf/rootfs/asound.conf', 'share/conf/rootfs/alsa.conf']),
    'tool': ('refs/muos/tool', 'd5edf14a54ae6588355a75c67b2d493590f281dc', ['LICENSE', 'utils/fnv1a.c'])
}
manifest = {'scope': 'limited native muOS core/audio bootstrap, no full sysinit or graphics', 'upstream': {}}
for name, (directory, revision, paths) in specs.items():
    if name == 'internal':
        # git archive can request unrelated .gitattributes blobs in a partial
        # clone. Export only these pinned files, preserving their Git modes.
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w') as stream:
            for path in sorted(paths):
                record = subprocess.check_output(['git', '-C', str(repo / directory), 'ls-tree', revision, path], text=True, timeout=30)
                mode, _, oid = record.split(None, 3)[:3]
                data = subprocess.check_output(['git', '-C', str(repo / directory), 'show', f'{revision}:{path}'], timeout=30)
                blob = f'blob {len(data)}\0'.encode() + data
                assert hashlib.sha1(blob).hexdigest() == oid
                info = tarfile.TarInfo(path)
                info.size = len(data)
                info.mode = int(mode, 8) & 0o777
                stream.addfile(info, io.BytesIO(data))
        archive = buffer.getvalue()
    else:
        archive = subprocess.check_output(['git', '-C', str(repo / directory), 'archive', revision, *paths], timeout=60)
    (work / f'{name}-source.tar').write_bytes(archive)
    target = source / name
    target.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(target, filter='data')
    manifest['upstream'][name] = {'revision': revision, 'archive_sha256': hashlib.sha256(archive).hexdigest()}
for patch in ['0002-muinput-r35s-panel0-profile.patch', '0004-muinput-linux44-uapi.patch']:
    subprocess.run(['git', '-C', str(source / 'frontend'), 'apply', str(repo / 'port/patches' / patch)], check=True)
subprocess.run(['git', '-C', str(source / 'internal'), 'apply', str(repo / 'port/patches/0005-muos-audio-service-logs.patch')], check=True)
overlay = source / 'overlay'
muos = overlay / 'opt/muos'
for directory in ['config', 'device/config', 'config/system', 'device/control', 'share/volume', 'kiosk', 'log']:
    (muos / directory).mkdir(parents=True, exist_ok=True)
config = json.loads((repo / 'port/device/rk-r35s-p0/core-config.json').read_text())
for ns, values in config.items():
    base = {'device': 'device/config', 'global': 'config', 'system': 'config/system'}[ns]
    for key, value in values.items():
        path = muos / base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value + '\n')
for src, dest in [('core-wireplumber.conf', 'wireplumber.conf'), ('core-asound.state', 'asound.state')]:
    shutil.copyfile(repo / 'port/device/rk-r35s-p0' / src, muos / 'device/control' / dest)
shutil.copyfile(repo / 'port/device/rk-r35s-p0/S95muos-core', source / 'S95muos-core')
(overlay / 'etc/default').mkdir(parents=True)
(overlay / 'etc/default/muos-core').write_text('# Bring-up: audio enabled, input opt-in until the frontend is integrated.\naudio=1\ninput=0\n')
(overlay / 'etc/fstab').write_text(
    '# Root is mounted by the kernel; storage layout is not yet integrated.\n'
    '/dev/root / ext4 rw,noauto 0 1\n'
    'proc /proc proc defaults 0 0\n'
    'sysfs /sys sysfs defaults 0 0\n'
    'devpts /dev/pts devpts defaults,gid=5,mode=620,ptmxmode=0666 0 0\n'
    'tmpfs /dev/shm tmpfs mode=1777 0 0\n'
    'tmpfs /tmp tmpfs mode=1777 0 0\n'
    'tmpfs /run tmpfs mode=0755,nosuid,nodev 0 0\n')
inputs = [*sorted((repo / 'port/buildroot').rglob('*')),
          *[repo / 'port/device/rk-r35s-p0' / name for name in
            ['core-config.json', 'core-wireplumber.conf', 'core-asound.state', 'S95muos-core']],
          repo / 'port/patches/0002-muinput-r35s-panel0-profile.patch',
          repo / 'port/patches/0004-muinput-linux44-uapi.patch',
          repo / 'port/patches/0005-muos-audio-service-logs.patch']
manifest['port_input_sha256'] = {str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in inputs if path.is_file()}
(work / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Pinned source snapshots and R35S core profile prepared; refs untouched')
