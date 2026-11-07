#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Install C07 only on the authorized secondary; provision Wi-Fi locally."""
from pathlib import Path
import configparser, hashlib, json, os, re, signal, stat, subprocess, sys, tempfile

assert os.geteuid() == 0
os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'
if sys.argv[-1:] != ['--private']:
    os.execvp('unshare', ['unshare', '--mount', '--propagation', 'private', sys.executable, __file__, *sys.argv[1:], '--private'])
assert Path('/proc/self/ns/mnt').stat().st_ino != Path('/proc/1/ns/mnt').stat().st_ino
def run(*args): return subprocess.check_output(args, text=True).strip()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cid(n): return hashlib.sha256(Path('/sys/block', n, 'device/cid').read_text().strip().lower().encode()).hexdigest()
folder = Path(sys.argv[1]).parent
plan = json.loads(Path(sys.argv[1]).read_text())
revision = plan.get('diagnostic_revision_update', 0)
assert revision in [0, 1, 2, 3]
assert plan['experiment'] == 'MUOS-R35S-NETWORK-P4-C07'
assert plan['authorized_secondary_c07_revision' if revision else 'authorized_secondary_c07_install'] is True
assert plan['installer_sha256'] == sha(Path(__file__))
assert run('uname', '-r') == '4.4.189'
assert run('findmnt', '-rn', '-o', 'SOURCE', '/') == '/dev/mmcblk0p2'
assert run('findmnt', '-rn', '-o', 'SOURCE', '/boot') == '/dev/mmcblk0p1'
assert cid('mmcblk0') == '9b4fc38015ae4a049ecd796ceceb2ef9473f4773c9b3a066ce59b567c516bbef'
assert cid('mmcblk1') == '12d2c78fbc14993fe2f8a00c413a5e3ef8d9659a3eba9a41a77b5c37029aa193'
assert int(Path('/sys/block/mmcblk1/size').read_text()) * 512 == 127934660608
assert run('blkid', '-s', 'PARTUUID', '-o', 'value', '/dev/mmcblk1p2') == '4d554432-02'
assert run('sha256sum', '/boot/Image').split()[0] == '31bdb671d640863448b59f79801277fe486fa6c78c326bd4ebb51a54559b0577'
assert Path('/proc/sys/kernel/tainted').read_text().strip() == '0'
assert all(x.rsplit(None, 1)[1] == '0' for x in run('btrfs', 'device', 'stats', '/').splitlines())
number = Path('/sys/class/block/mmcblk1p2/dev').read_text().strip()
assert not any(x.split()[2] == number for x in Path('/proc/self/mountinfo').read_text().splitlines())
allowed = {'usr/sbin/dropbear', 'usr/bin/dropbearkey', 'usr/sbin/wpa_supplicant', 'usr/sbin/wpa_cli',
           'usr/sbin/usb_modeswitch', 'usr/lib/libcrypt.so.2', 'usr/lib/libnl-3.so.200',
           'usr/lib/libnl-genl-3.so.200', 'usr/lib/libusb-1.0.so.0',
           'usr/libexec/muos-c07-network', 'usr/libexec/muos-c07-usb-mode',
           'usr/libexec/muos-c07-dhcp', 'usr/libexec/muos-c07-run',
           'etc/muos-network-authorized_key', 'etc/muos-network-diagnostic', 'etc/inittab', 'sbin/muos-ext4-diag',
           'usr/share/muos-diagnostic/c07-licenses.txt'}
if revision:
    allowed = {'usr/libexec/muos-c07-network', 'usr/libexec/muos-c07-run'}
    if revision==2: allowed.add('usr/libexec/muos-c07-usb-mode')
    if revision==3: allowed.add('usr/libexec/muos-c07-recover')
assert {e['path'] for e in plan['entries']} == allowed
assert len(plan['entries']) == len(allowed)
assert plan['entries'][-1]['path'] == ('usr/libexec/muos-c07-run' if revision else 'sbin/muos-ext4-diag')
for entry in plan['entries']:
    p = folder / 'assets' / entry['asset']
    assert p.name == entry['path'].replace('/', '_') and stat.S_ISREG(p.lstat().st_mode)
    assert p.stat().st_size < 2 * 1024 * 1024 and sha(p) == entry['sha256']
    assert entry['mode'] in [0o644, 0o755]
result = {'success': False, 'applied': [], 'backup': {}, 'rollback_attempted': False,
          'private_seed_metadata_only': False, 'credentials_collected_in_result': False}
def save():
    p = folder / 'install-result.tmp'; p.write_text(json.dumps(result, indent=2) + '\n'); p.replace(folder / 'install-result.json')
def stop(_sig, _frame): raise TimeoutError('C07 installer terminated')
signal.signal(signal.SIGTERM, stop)
def nm_unescape(value):
    return re.sub(r'\\([sntr\\])', lambda m: {'s':' ', 'n':'\n', 't':'\t', 'r':'\r', '\\':'\\'}[m[1]], value)
def private_network_config():
    uuid = run('nmcli', '-g', 'GENERAL.CON-UUID', 'device', 'show', 'wlan0')
    matches = []
    for p in Path('/etc/NetworkManager/system-connections').iterdir():
        if not p.is_file() or p.is_symlink(): continue
        c = configparser.ConfigParser(interpolation=None); c.read(p)
        if c.get('connection', 'uuid', fallback='') == uuid: matches.append(c)
    assert len(matches) == 1
    c = matches[0]
    sec = 'wifi-security' if c.has_section('wifi-security') else '802-11-wireless-security'
    wifi = 'wifi' if c.has_section('wifi') else '802-11-wireless'
    assert c.get(sec, 'key-mgmt') == 'wpa-psk' and c.get(sec, 'psk-flags', fallback='0') == '0'
    ssid_value = c.get(wifi, 'ssid')
    if re.fullmatch(r'(?:[0-9]+;)+', ssid_value):
        ssid = bytes(int(x) for x in ssid_value.split(';') if x)
    else: ssid = nm_unescape(ssid_value).encode('utf-8')
    assert 1 <= len(ssid) <= 32
    psk = nm_unescape(c.get(sec, 'psk'))
    if not re.fullmatch(r'[0-9a-fA-F]{64}', psk):
        assert 8 <= len(psk.encode('utf-8')) <= 63
        psk = hashlib.pbkdf2_hmac('sha1', psk.encode('utf-8'), ssid, 4096, 32).hex()
    # Contains secrets: device-local RAM -> private card file only, never logs/hash/backup.
    return ('ctrl_interface=/run/muos/c07/wpa\nupdate_config=0\nnetwork={\n ssid=' + ssid.hex() + '\n psk=' + psk + '\n key_mgmt=WPA-PSK\n}\n').encode()
save()
with tempfile.TemporaryDirectory(prefix='muos-c07-install-', dir='/tmp') as temp:
    root = Path(temp); mounted = False; private_created = False
    try:
        if not revision: network_bytes = private_network_config()
        subprocess.run(['mount', '-t', 'ext4', '-o', 'rw,nosuid,nodev,noexec', '/dev/mmcblk1p2', temp], check=True); mounted = True
        assert run('findmnt', '-rn', '-o', 'MAJ:MIN', '--target', temp) == number
        assert (root/'etc/muos-frontend-audio-diagnostic').read_text().strip() == 'MUOS-R35S-FRONTEND-AUDIO-P4-C06'
        assert (root/'etc/muos-ext4-diagnostic').read_text().strip() == 'MUOS-R35S-EXT4-P4-B01'
        for name in ['var', 'var/lib']: assert not (root/name).is_symlink()
        seed = (root/'var/lib/muos-seedrng').lstat()
        assert stat.S_ISDIR(seed.st_mode) and (seed.st_uid, seed.st_gid, stat.S_IMODE(seed.st_mode)) == (0, 0, 0o700)
        result['private_seed_metadata_only'] = True
        if revision:
            assert (root/'etc/muos-network-diagnostic').read_text().strip() == 'MUOS-R35S-NETWORK-P4-C07'
            private = root/'var/lib/muos-network'
            info = private.lstat()
            assert stat.S_ISDIR(info.st_mode) and (info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode)) == (0, 0, 0o700)
            info = (private/'network.conf').lstat()
            assert stat.S_ISREG(info.st_mode) and (info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode)) == (0, 0, 0o600)
            result['private_network_metadata_only'] = True
        else:
            assert not (root/'var/lib/muos-network').exists() and not (root/'var/lib/muos-network').is_symlink()
        for name, expected in plan['unchanged_required'].items():
            assert not (root/name).is_symlink() and sha(root/name) == expected, name
        for entry in plan['entries']:
            p = root/entry['path']
            for parent in p.parents:
                if parent == root: break
                assert not parent.is_symlink()
            if entry['old_sha256'] is None: assert not p.exists() and not p.is_symlink()
            else:
                assert stat.S_ISREG(p.lstat().st_mode) and sha(p) == entry['old_sha256']
                result['backup'][entry['path']] = {'hex': p.read_bytes().hex(), 'mode': stat.S_IMODE(p.stat().st_mode)}
        save()
        if not revision:
            private = root/'var/lib/muos-network'; private.mkdir(mode=0o700); private_created = True
            fd = os.open(private/'network.conf', os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(network_bytes); stream.flush(); os.fchown(stream.fileno(),0,0); os.fsync(stream.fileno())
            del network_bytes
        for i, entry in enumerate(plan['entries']):
            p = root/entry['path']; pending = p.with_name('.muos-c07-' + str(i) + '.tmp')
            fd = os.open(pending, os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW, entry['mode'])
            with os.fdopen(fd, 'wb') as stream:
                stream.write((folder/'assets'/entry['asset']).read_bytes()); stream.flush()
                os.fchmod(stream.fileno(), entry['mode']); os.fchown(stream.fileno(),0,0); os.fsync(stream.fileno())
            pending.replace(p); result['applied'].append(entry['path']); assert sha(p) == entry['sha256']; save()
            parent_fd = os.open(p.parent, os.O_RDONLY|os.O_DIRECTORY)
            try: os.fsync(parent_fd)
            finally: os.close(parent_fd)
        os.sync(); result['success'] = True
        result['private_network_provisioned_on_device_only'] = not bool(revision)
    except Exception as error:
        result['error_type'] = type(error).__name__; result['rollback_attempted'] = True
        if mounted:
            for i, entry in enumerate(plan['entries']):
                (root/entry['path']).with_name('.muos-c07-' + str(i) + '.tmp').unlink(missing_ok=True)
            for name in reversed(result['applied']):
                p=root/name; old=result['backup'].get(name)
                if old: p.write_bytes(bytes.fromhex(old['hex'])); p.chmod(old['mode'])
                else: p.unlink()
            if private_created:
                (root/'var/lib/muos-network/network.conf').unlink(missing_ok=True)
                (root/'var/lib/muos-network').rmdir()
        raise SystemExit('C07 install failed; sanitized result saved') from None
    finally:
        if mounted: subprocess.run(['umount',temp], check=True)
        save()
fsck = subprocess.run(['/usr/sbin/e2fsck','-fn','/dev/mmcblk1p2'], capture_output=True,text=True)
result['fsck'] = {'exit':fsck.returncode,'out':fsck.stdout,'err':fsck.stderr}; save()
assert fsck.returncode == 0
print('C07 revision installed; private configuration preserved; unmounted root and fsck passed' if revision else
      'C07 installed; device-local private provisioning, unmounted root and fsck passed')
