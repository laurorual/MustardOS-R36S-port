#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Inspect documented GPL container formats; do not execute/disassemble payloads."""
from pathlib import Path
import hashlib
import json
import struct
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rc4_header(data):
    # Public Rockchip header key/layout: tools/rkcommon.c, GPL-2.0+.
    key = bytes([124, 78, 3, 4, 85, 5, 9, 7, 45, 44, 123, 56, 23, 13, 23, 17])
    state = list(range(256))
    j = 0
    for i in range(256):
        j = (j+state[i]+key[i % len(key)]) % 256
        state[i], state[j] = state[j], state[i]
    result = bytearray()
    i = j = 0
    for byte in data:
        i = (i+1) % 256
        j = (j+state[i]) % 256
        state[i], state[j] = state[j], state[i]
        result.append(byte ^ state[(state[i]+state[j]) % 256])
    return result


def crc_rk(data):
    # Non-reflected polynomial used by tools/rockchip/crc32_rk.c; initial zero.
    table = []
    for index in range(256):
        value = index << 24
        for _ in range(8):
            value = ((value << 1) ^ (0x04c10db7 if value & 0x80000000 else 0)) & 0xffffffff
        table.append(value)
    crc = 0
    for byte in data:
        crc = (table[(crc >> 24) ^ byte] ^ (crc << 8)) & 0xffffffff
    return crc


def verify(package):
    stage = package.parent
    manifest = json.loads((package/'manifest.json').read_text())
    assert sha((stage/'audit/report.json').read_bytes()) == manifest['u_boot_audit_sha256']
    report = json.loads((stage/'audit/report.json').read_text())
    assert report['passed']
    expected_payloads = {Path(name).name: digest for name, digest in
                         report['inputs']['upstream']['recipe_payload_sha256'].items()}
    assert manifest['payloads'] == expected_payloads
    for name, digest in manifest['source_built_gpl_tool_sha256'].items():
        assert sha((stage/'output/tools'/name).read_bytes()) == digest, name
    for name, digest in manifest['outputs_sha256'].items():
        assert sha((package/name).read_bytes()) == digest, name
    for name, digest in manifest['payloads'].items():
        assert sha((package/'payloads'/name).read_bytes()) == digest, name
    ddr = (package/'payloads/rk3326_ddr_333MHz_v1.10.bin').read_bytes()
    mini = (package/'payloads/rk3326_miniloader_v1.12.bin').read_bytes()
    idb_ddr = (package/'idb-ddr.img').read_bytes()
    idb = (package/'idbloader.img').read_bytes()
    header = rc4_header(idb_ddr[:512])
    assert struct.unpack_from('<I', header)[0] == 0x0ff0aa55
    assert struct.unpack_from('<I', header, 8)[0] == 1, 'DDR payload must not be RC4-transformed'
    assert struct.unpack_from('<H', header, 12)[0] == 4
    init_size, boot_size = struct.unpack_from('<HH', header, 506)
    assert init_size % 4 == 0 and init_size*512+2048 == len(idb_ddr)
    assert boot_size == init_size+1024
    assert idb_ddr[2048:2048+len(ddr)] == ddr and ddr.startswith(b'RK33')
    assert not any(idb_ddr[2048+len(ddr):])
    assert idb == idb_ddr+mini

    binary = (stage/'output/u-boot.bin').read_bytes()
    assert sha(binary) == report['output_sha256']['u-boot.bin']
    uboot = (package/'uboot.img').read_bytes()
    assert len(uboot) == 4*1024*1024
    chunk = uboot[:1024*1024]
    assert all(uboot[i:i+len(chunk)] == chunk for i in range(0, len(uboot), len(chunk)))
    magic, version, reserved, address, size, crc, hashlen = struct.unpack_from('<8s6I', chunk)
    assert magic == b'LOADER  ' and version == reserved == 0
    assert address == 0x00200000 and size == (len(binary)+3)//4*4 and hashlen == 32
    padded = binary+b'\0'*(size-len(binary))
    assert chunk[2048:2048+size] == padded and not any(chunk[2048+size:])
    assert sha(padded+struct.pack('<III', address, size, hashlen)) == chunk[32:64].hex()
    assert crc_rk(padded) == crc

    trust = (package/'trust.img').read_bytes()
    assert len(trust) == 4*1024*1024 and trust[:2*1024*1024] == trust[2*1024*1024:]
    magic, version, flags, size_field = struct.unpack_from('<4sIII', trust)
    assert magic == b'BL3X' and version == 0x100 and flags == 0x33
    count = size_field >> 16
    sign_offset = (size_field & 0xffff)*4
    assert sign_offset == 800+count*48 and sign_offset+256+count*16 <= 2048
    expected = []
    elf = (package/'payloads/rk3326_bl31_v1.14.elf').read_bytes()
    assert elf[:7] == b'\x7fELF\x02\x01\x01'
    phoff = struct.unpack_from('<Q', elf, 32)[0]
    phsize, phnum = struct.unpack_from('<HH', elf, 54)
    assert phsize == 56
    for i in range(phnum):
        kind, _, offset, vaddr, _, filesz, _, _ = struct.unpack_from('<IIQQQQQQ', elf, phoff+i*phsize)
        if kind == 1:
            assert offset+filesz <= len(elf)
            expected.append((b'BL31', vaddr, elf[offset:offset+filesz]))
    expected.append((b'BL32', 0x08400000, (package/'payloads/rk3326_bl32_v1.10.bin').read_bytes()))
    assert count == len(expected)
    components = []
    next_storage = 2048
    for i, (want_id, want_addr, data) in enumerate(expected):
        component_id, storage, sectors, _ = struct.unpack_from('<4sIII', trust, sign_offset+256+i*16)
        digest = trust[800+i*48:832+i*48]
        load_addr = struct.unpack_from('<I', trust, 832+i*48)[0]
        padded = data+b'\0'*((-len(data)) % 2048)
        assert component_id == want_id and load_addr == want_addr
        assert storage*512 == next_storage and sectors*512 == len(padded)
        assert trust[storage*512:(storage+sectors)*512] == padded
        assert sha(padded) == digest.hex()
        components.append({'id': component_id.decode(), 'address': hex(load_addr),
                           'storage_bytes': storage*512, 'padded_bytes': len(padded), 'sha256': digest.hex()})
        next_storage += len(padded)
    assert not any(trust[next_storage:2*1024*1024])
    # Provisional sector layout from the reference recipe; no MBR/image is made.
    windows = [('idbloader.img', 64*512, 16384*512),
               ('uboot.img', 16384*512, 24576*512), ('trust.img', 24576*512, 32768*512)]
    for name, start, end in windows:
        assert start+(package/name).stat().st_size <= end, name
    installed_trust_hash = '3531668a2f08d4f8583ae9e256177f3404e04f9888d6e2a677613c8dfd4da138'
    return {'scope': 'public container layouts, hashes and copied payload bytes only; no firmware execution/disassembly',
            'passed': True, 'manifest': manifest, 'trust_components': components,
            'idb_ddr_payload_and_miniloader_match': True, 'uboot_crc_sha_and_four_copies_match': True,
            'trust_sha_and_two_copies_match': True,
            'trust_matches_installed_reference': sha(trust) == installed_trust_hash,
            'provisional_regions_do_not_overlap': True,
            'output_sizes': {name: (package/name).stat().st_size for name, _, _ in windows},
            'output_sha256': manifest['outputs_sha256'],
            'private_only': True, 'media_image_assembled': False, 'media_written': False, 'boot_tested': False,
            'verifier_sha256': sha(Path(__file__).read_bytes())}


if __name__ == '__main__':
    print(json.dumps(verify(Path(sys.argv[1])), indent=2))
