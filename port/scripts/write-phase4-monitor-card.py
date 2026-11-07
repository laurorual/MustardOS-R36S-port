#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Explicit secondary-card operation on the authorized R35S; default is inspect.

Only /dev/mmcblk1 can be written. Require CID/size/root/image bindings and
unmounted children, then exclusive open, fsync, cache invalidation and readback.
Never reread the partition table or restart consumers of the overwritten card.
"""
from pathlib import Path
import argparse
import fcntl
import gzip
import hashlib
import json
import os
import platform
import stat
import struct
import subprocess
import time

TARGET = Path('/dev/mmcblk1')
ROOT_CARD = Path('/sys/block/mmcblk0')
CARD = Path('/sys/block/mmcblk1')
UNITS = ['emulationstation', 'ogage', 'fn-menu-watcher']
MOUNTS = ['/opt/system/Tools', '/roms2']
MODEL = 'R36S-V12 2023-08-18 Panel 0'

def command(*args):
    return subprocess.check_output(args, text=True).strip()

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def cid(directory):
    return hashlib.sha256((directory/'device/cid').read_text().strip().lower().encode()).hexdigest()

def health():
    taint = Path('/proc/sys/kernel/tainted').read_text().strip()
    stats = command('btrfs', 'device', 'stats', '/')
    assert taint == '0', ('tainted kernel', taint)
    assert len(stats.splitlines()) == 5 and all(line.rsplit(None, 1)[1] == '0' for line in stats.splitlines()), stats
    return {'taint': taint, 'btrfs_stats': stats.splitlines()}

def mounted_children():
    device_numbers = {(CARD/'dev').read_text().strip()}
    device_numbers |= {p.read_text().strip() for p in CARD.glob('mmcblk1p*/dev')}
    return [line.split()[4] for line in Path('/proc/self/mountinfo').read_text().splitlines()
            if line.split()[2] in device_numbers]

def inspect():
    assert platform.machine() == 'aarch64' and platform.release() == '4.4.189'
    assert Path('/sys/firmware/devicetree/base/model').read_bytes().rstrip(b'\0').decode() == MODEL
    assert command('findmnt', '-n', '-o', 'SOURCE', '/') == '/dev/mmcblk0p2'
    assert command('findmnt', '-n', '-o', 'SOURCE', '/boot') == '/dev/mmcblk0p1'
    assert stat.S_ISBLK(TARGET.stat().st_mode) and TARGET.resolve() == TARGET
    capacity = int((CARD/'size').read_text())*512
    assert capacity == 127934660608, ('unexpected secondary capacity', capacity)
    primary, secondary = cid(ROOT_CARD), cid(CARD)
    assert primary != secondary
    mounts = mounted_children()
    assert set(mounts) <= set(MOUNTS), ('unexpected secondary mounts', mounts)
    batteries = [p for p in Path('/sys/class/power_supply').iterdir()
                 if (p/'type').is_file() and (p/'type').read_text().strip() == 'Battery']
    assert len(batteries) == 1
    battery = int((batteries[0]/'capacity').read_text())
    assert battery >= 25, ('battery too low for card operation', battery)
    return {'target':str(TARGET), 'capacity_bytes':capacity, 'target_cid_sha256':secondary,
            'protected_root_cid_sha256':primary, 'root_source':'/dev/mmcblk0p2',
            'mounts':mounts, 'battery_percent':battery, 'health':health()}

def stream_gzip(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    with os.fdopen(os.dup(fd), 'rb') as stream:
        with gzip.GzipFile(fileobj=stream) as archive:
            while data := archive.read(1024*1024):
                yield data

def validate_image_plan(plan):
    sizes={'MUOS-R35S-LINUX-P4-A01':128*1024*1024,
           'MUOS-R35S-EXT4-P4-B01':640*1024*1024}
    experiment=plan.get('diagnostic_experiment')
    if experiment is None:
        assert plan['user_authorized_secondary_monitor_write'] is True
        expected=128*1024*1024
    else:
        assert experiment in sizes, 'unknown experiment'
        assert plan['user_authorized_secondary_diagnostic_write'] is True
        expected=sizes[experiment]
    assert plan['image_bytes']==expected and expected%512==0
    assert plan['capacity_bytes']==127934660608 and expected<plan['capacity_bytes']

def execute(plan_path):
    assert os.geteuid() == 0
    plan = json.loads(plan_path.read_text())
    result_path = plan_path.parent/'write-result.json'
    result = {'scope':'authorized secondary microSD preparation', 'started_unix':time.time(),
              'bytes_written':0, 'write_started':False, 'verified':False, 'success':False}
    def record():
        temporary = result_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(result, indent=2)+'\n')
        temporary.replace(result_path)
    record()
    stopped = False
    unmounted = []
    source_fd = target_fd = None
    try:
        assert digest(Path(__file__)) == plan['writer_sha256'], 'writer changed since the plan'
        current = inspect()
        result['before'] = current
        for field in ['target','capacity_bytes','target_cid_sha256','protected_root_cid_sha256','root_source']:
            assert current[field] == plan[field], field
        validate_image_plan(plan)
        result['diagnostic_experiment']=plan.get('diagnostic_experiment')
        assert command('findmnt', '-n', '-o', 'FSTYPE', '-T', str(plan_path.parent)) == 'tmpfs'
        image = plan_path.parent/'monitor.img.gz'
        source_fd = os.open(image, os.O_RDONLY|os.O_NOFOLLOW)
        assert stat.S_ISREG(os.fstat(source_fd).st_mode)
        with os.fdopen(os.dup(source_fd), 'rb') as source:
            assert hashlib.file_digest(source, 'sha256').hexdigest() == plan['gzip_sha256']
        calculated = hashlib.sha256()
        length = 0
        for data in stream_gzip(source_fd):
            length += len(data)
            assert length <= plan['image_bytes']
            calculated.update(data)
        assert length == plan['image_bytes'] and calculated.hexdigest() == plan['image_sha256']
        result['input_validated'] = True
        record()
        subprocess.run(['systemctl','stop',*UNITS], check=True)
        stopped = True
        for mount in MOUNTS:
            if mount in mounted_children():
                subprocess.run(['umount', mount], check=True)
                unmounted.append(mount)
        assert not mounted_children(), 'secondary card still mounted'
        target_fd = os.open(TARGET, os.O_RDWR|os.O_EXCL|os.O_NOFOLLOW)
        assert stat.S_ISBLK(os.fstat(target_fd).st_mode)
        capacity = struct.unpack('Q', fcntl.ioctl(target_fd, 0x80081272, b'\0'*8))[0]  # BLKGETSIZE64
        assert capacity == plan['capacity_bytes']
        assert cid(CARD) == plan['target_cid_sha256'] and cid(ROOT_CARD) == plan['protected_root_cid_sha256']
        assert command('findmnt', '-n', '-o', 'SOURCE', '/') == '/dev/mmcblk0p2'
        result['write_started'] = True
        result['unmounted'] = unmounted
        record()
        os.lseek(target_fd, 0, os.SEEK_SET)
        written_digest = hashlib.sha256()
        for data in stream_gzip(source_fd):
            assert result['bytes_written']+len(data) <= plan['image_bytes']
            written_digest.update(data)
            view = memoryview(data)
            while view:
                written = os.write(target_fd, view)
                assert written > 0
                result['bytes_written'] += written
                assert result['bytes_written'] <= plan['image_bytes']
                view = view[written:]
            if result['bytes_written'] % (8*1024*1024) == 0:
                record()
        assert result['bytes_written'] == plan['image_bytes']
        assert written_digest.hexdigest() == plan['image_sha256']
        os.fsync(target_fd)
        fcntl.ioctl(target_fd, 0x1261)  # BLKFLSBUF: flush and invalidate this card's cache only.
        result['cache_flushed_and_invalidated'] = True
        os.lseek(target_fd, 0, os.SEEK_SET)
        calculated = hashlib.sha256()
        remaining = plan['image_bytes']
        while remaining:
            data = os.read(target_fd, min(1024*1024, remaining))
            assert data
            remaining -= len(data)
            calculated.update(data)
        result['readback_sha256'] = calculated.hexdigest()
        assert calculated.hexdigest() == plan['image_sha256']
        result['verified'] = True
        result['after_health'] = health()
        result['success'] = True
    except Exception as error:
        result['error'] = type(error).__name__+': '+str(error)
        raise
    finally:
        if target_fd is not None:
            os.close(target_fd)
        if source_fd is not None:
            os.close(source_fd)
        # Restore only if no device write was attempted. After writing, keep
        # obsolete partitions unmounted until normal poweroff and card swap.
        if stopped and not result['write_started']:
            try:
                if '/roms2' in unmounted:
                    subprocess.run(['mount','-t','vfat','-o',
                                    'rw,noatime,uid=1000,gid=1000,fmask=0000,dmask=0000',
                                    '/dev/mmcblk1p1','/roms2'], check=True)
                if '/opt/system/Tools' in unmounted:
                    subprocess.run(['mount','--bind','/roms2/tools','/opt/system/Tools'], check=True)
                subprocess.run(['systemctl','start',*UNITS], check=True)
            except Exception as recovery_error:
                result['restore_error'] = str(recovery_error)
        result['finished_unix'] = time.time()
        record()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', type=Path, metavar='PLAN_JSON')
    args = parser.parse_args()
    if args.execute:
        execute(args.execute.resolve())
    else:
        print(json.dumps(inspect(), indent=2))
