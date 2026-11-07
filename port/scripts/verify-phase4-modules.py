#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Inspect AArch64 ET_REL modules without loading them or executing init."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

RELEASE = '4.4.189-muos-r35s-p4'
VERMAGIC = RELEASE + ' SMP mod_unload aarch64'


def module_info(path):
    data = path.read_bytes()
    assert data[:7] == b'\x7fELF\x02\x01\x01', path
    kind, machine = struct.unpack_from('<HH', data, 16)
    assert (kind, machine) == (1, 183), (path, kind, machine)
    phoff = struct.unpack_from('<Q', data, 32)[0]
    phsize, phnum = struct.unpack_from('<HH', data, 54)
    assert phoff == 0 and phnum == 0 and phsize == 0, path
    offset = struct.unpack_from('<Q', data, 40)[0]
    size, count, strings = struct.unpack_from('<HHH', data, 58)
    assert size == 64 and count > 0 and strings < count and offset + count*size <= len(data), path
    sections = [struct.unpack_from('<IIQQQQIIQQ', data, offset+i*size) for i in range(count)]
    sh = sections[strings]
    names = data[sh[4]:sh[4]+sh[5]]
    fields = {}
    for sh in sections:
        if sh[1] != 8:  # SHT_NOBITS occupies no file bytes.
            assert sh[4]+sh[5] <= len(data), path
        name = names[sh[0]:].split(b'\0', 1)[0]
        if name != b'.modinfo':
            continue
        for entry in data[sh[4]:sh[4]+sh[5]].split(b'\0'):
            if b'=' in entry:
                key, value = entry.decode().split('=', 1)
                fields.setdefault(key, []).append(value)
    assert len(fields.get('vermagic', [])) == 1, path
    assert fields['vermagic'][0].strip() == VERMAGIC, (path, fields['vermagic'])
    return fields


def norm(name):
    return name.replace('-', '_')


def verify(root):
    directory = root/'lib/modules'/RELEASE
    assert directory.is_dir()
    modules = {}
    by_name = {}
    for p in sorted(directory.rglob('*.ko')):
        assert not p.is_symlink(), p
        fields = module_info(p)
        name = norm(fields.get('name', [p.stem])[0])
        relative = str(p.relative_to(directory))
        assert name not in by_name, (name, by_name.get(name), relative)
        by_name[name] = relative
        modules[relative] = {'name': name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                             'modinfo': fields}
    assert len(modules) == 555, len(modules)
    builtin = {norm(Path(p).stem) for p in (directory/'modules.builtin').read_text().splitlines()}
    missing = {}
    firmware = {}
    licenses = {}
    for name, record in modules.items():
        fields = record['modinfo']
        dependencies = [d for s in fields.get('depends', []) for d in s.split(',') if d]
        bad = [d for d in dependencies if norm(d) not in by_name and norm(d) not in builtin]
        if bad: missing[name] = bad
        for request in fields.get('firmware', []): firmware.setdefault(request, []).append(name)
        for license_name in fields.get('license', ['MISSING']): licenses.setdefault(license_name, []).append(name)
    assert not missing, missing
    return {'scope':'static module metadata; no loading or hardware validation',
            'release':RELEASE, 'vermagic':VERMAGIC, 'aarch64_et_rel_count':len(modules),
            'builtin_module_names':len(builtin), 'dependencies_closed':True,
            'license_declarations':licenses, 'firmware_requests':firmware, 'modules':modules,
            'module_firmware_tags_are_not_a_complete_runtime_inventory':True,
            'candidate_kernel_booted':False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.root), indent=2))
