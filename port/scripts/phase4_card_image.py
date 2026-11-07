# SPDX-License-Identifier: MIT
"""Read-only bounds/content checks for the fixed private Panel 0 SD layout."""
from pathlib import Path
import hashlib, os, stat, struct

SECTOR = 512
IMAGE_BYTES = 640 * 1024 * 1024
FAT_OFFSET = 16 * 1024 * 1024
FAT_BYTES = 100 * 1024 * 1024
ROOT_OFFSET = 128 * 1024 * 1024
ROOT_BYTES = 512 * 1024 * 1024
DISK_SIGNATURE = 0x4d554432
BOOT_OFFSETS = {'idbloader.img': 64 * SECTOR, 'uboot.img': 16384 * SECTOR,
                'trust.img': 24576 * SECTOR}


def mbr_bytes():
    mbr = bytearray(SECTOR)
    struct.pack_into('<I', mbr, 440, DISK_SIGNATURE)
    for n, active, kind, offset, length in [(0, 0x80, 0x0c, FAT_OFFSET, FAT_BYTES),
                                           (1, 0, 0x83, ROOT_OFFSET, ROOT_BYTES)]:
        struct.pack_into('<B3sB3sII', mbr, 446 + n * 16, active, b'\xfe\xff\xff',
                         kind, b'\xfe\xff\xff', offset // SECTOR, length // SECTOR)
    mbr[510:512] = b'\x55\xaa'
    return bytes(mbr)


def regular_single(path):
    info = Path(path).lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'Expected regular single-link image'
    return info


def region_digest(stream, offset, length):
    assert offset >= 0 and length > 0
    stream.seek(offset)
    digest = hashlib.sha256()
    remaining = length
    while remaining:
        data = stream.read(min(1024 * 1024, remaining))
        assert data, 'Truncated image region'
        digest.update(data)
        remaining -= len(data)
    return digest.hexdigest()


def verify_image(path, regions):
    """Verify canonical MBR, all five payload spans and every zero-filled gap.

    Caller supplies pinned source hashes, never values learned from the image.
    This accepts only a regular file and performs no writes, mounts or ioctls.
    """
    assert set(regions) == set(BOOT_OFFSETS) | {'boot.fat', 'rootfs.ext4'}
    before = regular_single(path)
    assert before.st_size == IMAGE_BYTES, 'Wrong image size'
    spans = []
    for name, record in regions.items():
        offset, length = record['offset'], record['bytes']
        assert type(offset) is int and type(length) is int and length > 0
        if name in BOOT_OFFSETS:
            assert offset == BOOT_OFFSETS[name]
        elif name == 'boot.fat':
            assert (offset, length) == (FAT_OFFSET, FAT_BYTES)
        else:
            assert (offset, length) == (ROOT_OFFSET, ROOT_BYTES)
        assert len(record['sha256']) == 64 and set(record['sha256']) <= set('0123456789abcdef')
        spans.append((offset, length, name))
    spans.sort()
    cursor = SECTOR
    for offset, length, name in spans:
        assert offset >= cursor and offset + length <= IMAGE_BYTES, 'Overlapping or oversized region'
        cursor = offset + length
    assert cursor == IMAGE_BYTES
    # O_NOFOLLOW also protects the final component between lstat and open.
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        assert (opened.st_dev, opened.st_ino, opened.st_size, opened.st_nlink) == (
            before.st_dev, before.st_ino, before.st_size, 1)
        assert stream.read(SECTOR) == mbr_bytes(), 'Noncanonical partition table'
        cursor = SECTOR
        for offset, length, name in spans:
            stream.seek(cursor)
            remaining = offset - cursor
            while remaining:
                data = stream.read(min(1024 * 1024, remaining))
                assert data and not any(data), 'Nonzero bytes outside declared regions'
                remaining -= len(data)
            assert region_digest(stream, offset, length) == regions[name]['sha256'], name
            cursor = offset + length
        after = os.fstat(stream.fileno())
        assert (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink) == (
            before.st_size, before.st_mtime_ns, before.st_ctime_ns, 1), 'Image changed during audit'
    final = regular_single(path)
    assert (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns, final.st_ctime_ns) == (
        before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    return {'passed': True, 'canonical_MBR': True, 'partition_count': 2,
            'root_partuuid': '4d554432-02', 'image_bytes': IMAGE_BYTES,
            'payload_regions_hashed': len(spans), 'all_other_bytes_zero': True}
