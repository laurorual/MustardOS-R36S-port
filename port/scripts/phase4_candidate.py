# SPDX-License-Identifier: MIT
"""Read-only validation helpers for the private C23 rootfs composition."""
from pathlib import Path, PurePosixPath
import hashlib, json, os, re, stat


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def sums(path):
    records = {}
    for line in path.read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert re.fullmatch('[0-9a-f]{64}', digest), name
        parts = PurePosixPath(name).parts
        assert '..' not in parts and name not in records, name
        records[name] = digest
    assert records
    return records


def local(root, name):
    # Resolve target absolute symlinks without traversing the host filesystem.
    pending = list(PurePosixPath(name).parts); parts = []; hops = 0
    while pending:
        part = pending.pop(0)
        if part in ('/', '.'):
            continue
        if part == '..':
            assert parts; parts.pop(); continue
        path = root.joinpath(*parts, part)
        if path.is_symlink():
            hops += 1; assert hops <= 40
            link = path.readlink()
            if link.is_absolute(): parts = []
            pending = list(link.parts) + pending
        else: parts.append(part)
    return root.joinpath(*parts)


def inventory(root):
    records = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(base) / name; info = path.lstat(); rel = path.relative_to(root).as_posix()
            if stat.S_ISLNK(info.st_mode): records[rel] = {'type': 'link', 'target': str(path.readlink())}
            elif stat.S_ISDIR(info.st_mode): records[rel] = {'type': 'directory', 'mode': stat.S_IMODE(info.st_mode)}
            elif stat.S_ISREG(info.st_mode): records[rel] = {'type': 'file', 'mode': stat.S_IMODE(info.st_mode), 'sha256': sha(path)}
            else: records[rel] = {'type': 'special', 'mode': stat.S_IMODE(info.st_mode), 'device': info.st_rdev}
    return records


def validate(root):
    assert root.is_dir() and root.resolve() != Path('/')
    for name in ['var/lib/muos-seedrng', 'var/lib/muos-network', 'var/lib/muos-preferences',
                 'usr/libexec/muos-boot', 'userdata/MUOS/preferences', 'root/.ssh']:
        assert not (root / name).exists() and not (root / name).is_symlink(), name
    for path in root.rglob('*'):
        assert not path.name.endswith('.once'), str(path)
        assert not re.fullmatch(r'c(?:12|25)[.]used(?:[.].*)?',path.name),str(path)
        if not path.is_symlink():
            assert not re.fullmatch(r'dropbear_.*_host_key', path.name), str(path)
    defaults = root / 'etc/default/muos-session'
    assert not defaults.is_symlink()
    assert defaults.read_text() == ('# C23 private composition; no automatic session.\n'
        'enabled=0\npreferences_enabled=0\nlease_seconds=180\n'
        'profile_dir=/usr/share/muos-r35s-profile\n'
        'prerequisites=/usr/libexec/muos-session/prerequisites.sha256\n')
    state = root / 'var/lib/muos-diagnostic'
    assert state.is_dir() and not state.is_symlink() and stat.S_IMODE(state.stat().st_mode) == 0o700
    assert {p.name for p in state.iterdir()} == {'boot-seq'}, 'Factory diagnostic state must contain only the fresh counter'
    assert (state / 'boot-seq').read_text() == '0\n' and stat.S_IMODE((state / 'boot-seq').stat().st_mode) == 0o600
    runner = (root / 'usr/libexec/muos-c07-run').read_text()
    assert 'umask 077' in runner and 'chmod 600 "$sequence_dir/boot-seq.tmp"' in runner
    bootstrap = (root / 'sbin/muos-ext4-diag').read_text()
    assert 'candidate_boot_check || fail' in bootstrap and 'grep -qx audio=0' not in bootstrap
    tab = (root / 'etc/inittab').read_text()
    active = '\n'.join(line for line in tab.splitlines() if line and not line.startswith('#'))
    assert active.count('::sysinit:/usr/libexec/muos-c07-run') == 1
    assert active.count('::shutdown:/usr/libexec/muos-c07-run stop') == 1
    assert not any(name in active for name in ['muos-boot', '/rcS', '/rcK', 'S98', 'S99'])
    profile = root / 'usr/share/muos-r35s-profile'
    meta = json.loads((profile / 'manifest.json').read_text())
    assert sha(profile/'profile.json') == meta['profile_sha256']
    assert len(meta['files']) == 21 and meta['ui_autostart'] is False
    for name, record in meta['files'].items():
        path = root / name
        assert not path.is_symlink() and sha(path) == record['sha256'], name
    assert (root / 'etc/default/muos-ui').read_text() == 'enabled=0\nhotkeys=1\n'
    package = root / 'usr/libexec/muos-session'
    payload = sums(package / 'payload.sha256'); assert len(payload) == 15
    for name, digest in payload.items():
        assert not PurePosixPath(name).is_absolute()
        assert sha(package / name) == digest, name
    for name, digest in sums(package / 'profile-source.sha256').items():
        assert not PurePosixPath(name).is_absolute()
        assert not (profile/name).is_symlink()
        assert sha(profile / name) == digest, name
    foundation = sums(package / 'prerequisites.sha256')
    for name, digest in foundation.items():
        assert PurePosixPath(name).is_absolute()
        assert sha(local(root, name)) == digest, name
    assert '/etc/inittab' in foundation and '/etc/default/muos-session' in foundation
    policy = root / 'etc/modprobe.d/90-muos-r35s-wifi-only.conf'
    assert 'blacklist btusb' in policy.read_text()
    launcher = root/'usr/libexec/muos-c25'
    integrated = launcher.exists()
    if integrated:
        assert not launcher.is_symlink() and launcher.is_dir()
        members={'card-guard.sh','native.sh','policy.sh','select.sh','session.sh'}
        assert {p.name for p in launcher.iterdir()} == members|{'payload.sha256'}
        manifest=sums(launcher/'payload.sha256')
        assert set(manifest)==members
        for name,digest in manifest.items():
            f=launcher/name;assert not f.is_symlink() and sha(f)==digest and stat.S_IMODE(f.stat().st_mode)==0o755
        lines=active.splitlines(); c07='::sysinit:/usr/libexec/muos-c07-run'
        desired=['::sysinit:/usr/libexec/muos-c25/select.sh',c07,'::sysinit:/usr/libexec/muos-c25/session.sh start']
        i=lines.index(c07);assert lines[i-1:i+2]==desired
        c07stop='::shutdown:/usr/libexec/muos-c07-run stop';i=lines.index(c07stop)
        assert lines[i-1]=='::shutdown:/usr/libexec/muos-c25/session.sh stop'
        assert len([v for v in lines if '/usr/libexec/muos-c25/' in v])==3
        irq_policy='/opt/muos/device/control/wireplumber.conf'
        irq_line='      api.alsa.disable-tsched = true'
        irq_config=root/irq_policy.lstrip('/')
        irq_enabled=irq_line in irq_config.read_text().splitlines()
        # C30 adds the board audio configuration to the native foundation.
        # Legacy C25/C27 trees retain their exact 96-file contract.
        if irq_enabled:
            assert len(foundation)==97 and irq_policy in foundation
            assert irq_config.is_file() and not irq_config.is_symlink()
            assert irq_config.read_text().splitlines().count(irq_line)==1
            assert sum('api.alsa.disable-tsched' in line for line in irq_config.read_text().splitlines())==1
            assert sha(irq_config)==foundation[irq_policy]
            if 'api.alsa.disable-mmap' in irq_config.read_text():
                assert irq_config.read_text().splitlines().count('      api.alsa.disable-mmap = true')==1
                assert sum('api.alsa.disable-mmap' in line for line in irq_config.read_text().splitlines())==1
        else:
            assert len(foundation)==96 and irq_policy not in foundation
        assert all('/usr/libexec/muos-c25/'+n in foundation for n in members|{'payload.sha256'})
        assert '/usr/share/licenses/muos-r35s-launcher-once/LICENSE' in foundation
        assert '/etc/init.d/S95muos-core' in foundation
        data=json.loads((profile/'profile.json').read_text())
        assert data['model']=='R36S-V12 2023-08-18 Panel 0' and data['board']=='rk-r35s-p0'
        assert data['audio']['pipewire_quantum']==1024
        if data['name']=='rk-r35s-p0-private-bringup-v3':
            assert data['audio']['codec_gain']==215
            certificate=profile/'speaker-calibration.json'
            assert sha(certificate)==data['speaker_calibration_sha256']
            cert=json.loads(certificate.read_text())
            assert cert['codec_gain']==215 and cert['software_max']==100 and cert['maximum_clean_and_adequate_user_confirmed'] is True
            assert cert['model']==data['model'] and cert['board']==data['board']
            assert 'speaker-calibration.json' in sums(package/'profile-source.sha256')
        else:assert data['name']=='rk-r35s-p0-private-bringup-v2' and data['audio']['codec_gain']==195
        assert (root/'etc/default/muos-core').read_text()=='audio=1\ninput=1\naudio_quantum=1024\n'
        core=(root/'etc/init.d/S95muos-core').read_text()
        assert 'audio_set_quantum' in core and 'pw-metadata -n settings 0 clock.force-quantum' in core
    return {'passed': True, 'profile_files': 21, 'payload_files': 15,
            'foundation_files': len(foundation), 'C07_selected': True,
            'automatic_session': False, 'preferences_default_enabled': False,
            'seed_and_private_network_state_included': False,
            'C25_one_shot_supported':integrated,'C26_audio_profile_integrated':integrated,
            'ALSA_irq_scheduling': integrated and irq_enabled}
