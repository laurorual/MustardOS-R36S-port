#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Test the single-card bind contract on fresh tmpfs, without block devices."""
import json


def exercise(command, jail, root):
    service = '/etc/init.d/S90muos-storage'
    assert not any((jail / 'dev').glob('mmcblk*'))
    assert not (jail / 'dev/fb0').exists()
    command(['/bin/sh', '-ec', 'command -v stat; stat -c "%d:%i" /'], capture=True)
    (jail / 'etc/default/muos-storage').write_text('fstype=tmpfs\n')
    command(['/bin/mount', '-t', 'tmpfs', '-o', 'nosuid,nodev,size=16m', 'tmpfs', '/userdata'])
    assert command([service, 'status'], check=False).returncode == 3
    assert command(['/etc/init.d/S95muos-core', 'start'], check=False).returncode == 3
    assert not (jail / 'run/muos/core/ready').exists()
    # An existing, unowned target must survive the failed transaction. No
    # lazy unmounts: all mounts created earlier in that transaction roll back.
    command(['/bin/mkdir', '-p', '/run/muos/storage/save'])
    command(['/bin/mount', '-t', 'tmpfs', '-o', 'size=1m', 'tmpfs', '/run/muos/storage/save'])
    (jail / 'run/muos/storage/save/unowned').write_text('keep\n')
    result = command([service, 'start'], check=False, capture=True)
    assert result.returncode != 0 and 'Unowned mount:' in result.stdout
    assert (jail / 'run/muos/storage/save/unowned').read_text() == 'keep\n'
    assert not (jail / 'run/muos/storage/mount_ready').exists()
    assert command(['/bin/findmnt', '-rn', '-M', '/mnt/mmc'], check=False).returncode != 0
    command(['/bin/umount', '/run/muos/storage/save'])
    command([service, 'start'], capture=True)
    command([service, 'start'], capture=True)
    command([service, 'status'], capture=True)
    assert (jail / 'run/muos/storage/mount_ready').exists()
    (jail / 'run/muos/storage/save/write-through').write_text('native-new-libc\n')
    assert (jail / 'userdata/MUOS/save/write-through').read_text() == 'native-new-libc\n'
    (jail / 'userdata/MUOS/package/config/fixture').write_text('package-config\n')
    assert (jail / 'run/muos/storage/package/config/fixture').read_text() == 'package-config\n'
    rows = (jail / 'run/muos/storage/bindmap').read_text().splitlines()
    assert len(rows) == 21 and len({r.split('|')[0] for r in rows}) == 21, rows
    assert all(r.split('|')[1] == 'ROM' for r in rows)
    # Detect an incorrect bind even if all expected paths still exist.
    command(['/bin/umount', '/run/muos/storage/bios'])
    command(['/bin/mount', '--bind', '/userdata/MUOS/save', '/run/muos/storage/bios'])
    assert command([service, 'status'], check=False).returncode != 0
    assert command([service, 'start'], check=False).returncode != 0
    command([service, 'stop'], capture=True)
    command([service, 'stop'], capture=True)
    assert command([service, 'status'], check=False).returncode == 3
    assert not (jail / 'run/muos/storage/mount_ready').exists()
    assert command(['/bin/findmnt', '-rn', '-M', '/mnt/mmc'], check=False).returncode != 0
    assert (jail / 'userdata/MUOS/save/write-through').read_text() == 'native-new-libc\n'
    command([service, 'start'], capture=True)
    assert (jail / 'run/muos/storage/save/write-through').read_text() == 'native-new-libc\n'
    (root / 'storage-native.json').write_text(json.dumps({
        'passed': True, 'scope': 'native namespace tmpfs bind contract; not ext4 boot or SD2',
        'block_devices_exposed': False, 'frontend_started': False,
        'core_start_blocked_without_storage': True, 'unowned_mount_preserved': True,
        'failed_start_rolled_back': True, 'idempotent_start_stop': True,
        'incorrect_bind_identity_rejected': True,
        'write_through_and_restart_persistence': True, 'bindmap': rows,
    }, indent=2) + '\n')
    print('PHASE4_STORAGE_CONTRACT_PASSED', flush=True)


def cleanup(command, jail, root):
    command(['/etc/init.d/S90muos-storage', 'stop'], capture=True)
    assert command(['/etc/init.d/S90muos-storage', 'status'], check=False).returncode == 3
    command(['/bin/umount', '/userdata'])
    (root / 'storage-cleanup.txt').write_text('Storage stopped; fixture tmpfs unmounted\n')
