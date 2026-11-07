#!/usr/bin/env python3
"""Inspect a local Buildroot output; never mount or execute its init scripts."""
from collections import deque
from pathlib import Path, PurePosixPath
import hashlib
import importlib.util
import json
import struct
import sys

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('module_audit', Path(__file__).with_name('verify-phase4-modules.py'))
module_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module_audit)


def root_path(root, name):
    """Resolve absolute target symlinks inside the target, not on the host."""
    remaining = deque(PurePosixPath(name).parts)
    parts = []
    hops = 0
    while remaining:
        part = remaining.popleft()
        if part in ("/", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        current = root.joinpath(*parts, part)
        if current.is_symlink():
            hops += 1
            if hops > 40:
                raise ValueError(f"symlink loop: {name}")
            link = current.readlink()
            if link.is_absolute():
                parts = []
            remaining.extendleft(reversed(PurePosixPath(str(link)).parts))
        else:
            parts.append(part)
    return root.joinpath(*parts)


def elf_info(path):
    data = path.read_bytes()
    if not data.startswith(b"\x7fELF"):
        return None
    assert data[4:7] == bytes((2, 1, 1)), f"not ELF64 little-endian: {path}"
    assert struct.unpack_from("<H", data, 18)[0] == 183, f"not AArch64: {path}"
    assert struct.unpack_from("<H", data, 16)[0] in (2, 3), f"not userspace ET_EXEC/ET_DYN: {path}"
    phoff = struct.unpack_from("<Q", data, 32)[0]
    entsize, count = struct.unpack_from("<HH", data, 54)
    assert entsize == 56 and phoff + count * entsize <= len(data), path
    info = {"interpreter": None, "gnu_linux_abi": None}
    for i in range(count):
        kind, _, offset, _, _, size, _, _ = struct.unpack_from("<IIQQQQQQ", data, phoff + i * entsize)
        assert offset + size <= len(data), path
        if kind == 3:  # PT_INTERP
            info["interpreter"] = data[offset:offset + size].rstrip(b"\0").decode()
        elif kind == 4:  # PT_NOTE / NT_GNU_ABI_TAG
            cursor, end = offset, offset + size
            while cursor + 12 <= end:
                namesize, descsize, note_type = struct.unpack_from("<III", data, cursor)
                cursor += 12
                name = data[cursor:cursor + namesize].rstrip(b"\0")
                cursor += (namesize + 3) & ~3
                desc = data[cursor:cursor + descsize]
                cursor += (descsize + 3) & ~3
                if name == b"GNU" and note_type == 1 and descsize == 16:
                    os_id, major, minor, patch = struct.unpack("<IIII", desc)
                    assert os_id == 0, path
                    info["gnu_linux_abi"] = [major, minor, patch]
    return info


def verify(output):
    root = output / "target"
    config = (output / ".config").read_text()
    assert 'BR2_TOOLCHAIN_HEADERS_AT_LEAST="4.4"' in config
    for name in ("/sbin/init", "/bin/busybox", "/bin/bash", "/sbin/udevd",
                 "/usr/bin/dbus-daemon", "/usr/bin/pipewire", "/usr/bin/wireplumber",
                 "/usr/bin/aplay", "/usr/bin/amixer", "/etc/inittab",
                 "/etc/init.d/rcS", "/etc/init.d/rcK"):
        assert root_path(root, name).is_file(), f"missing {name}"
    assert not (root / "opt/muos/script/init/sysinit").exists(), "unexpected muOS init in headless profile"
    assert "musplash" not in (root / "etc/inittab").read_text()
    elf_count = 0
    module_count = 0
    interpreters = set()
    libc = None
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        # Avoid reading every data file in full.
        with path.open("rb") as source:
            magic = source.read(4)
        if magic != b"\x7fELF":
            continue
        relative = path.relative_to(root)
        if relative.parts[:3] == ('lib', 'modules', module_audit.RELEASE) and path.suffix == '.ko':
            module_audit.module_info(path)
            module_count += 1
            continue
        info = elf_info(path)
        elf_count += 1
        if info["interpreter"]:
            interpreter = info["interpreter"]
            assert interpreter == "/lib/ld-linux-aarch64.so.1", (path, interpreter)
            assert root_path(root, interpreter).is_file(), interpreter
            interpreters.add(interpreter)
        if path.name == "libc.so.6":
            libc = info
    # libc.so.6 may itself be a symlink.
    libc = libc or elf_info(root_path(root, "/lib/libc.so.6"))
    assert libc and libc["gnu_linux_abi"] == [4, 4, 0], libc
    if module_count:
        modules = module_audit.verify(root)
        assert modules['aarch64_et_rel_count'] == module_count
    image = output / "images/rootfs.ext4"
    with image.open("rb") as source:
        source.seek(1024)
        superblock = source.read(1024)
    assert len(superblock) == 1024 and struct.unpack_from("<H", superblock, 56)[0] == 0xEF53
    compat, incompat, ro_compat = struct.unpack_from("<III", superblock, 92)
    # Deliberately narrow bring-up profile; see pinned fs/ext4/ext4.h.
    assert not compat & ~0x23F, f"unreviewed compat features {compat:#x}"
    assert not incompat & ~0x242, f"unreviewed incompat features {incompat:#x}"
    assert not ro_compat & ~0x47F, f"unreviewed ro features {ro_compat:#x}"
    assert not compat & (0x1000 | 0x400), "orphan_file or fast_commit"
    assert not incompat & (0x80 | 0x2000), "64bit or metadata_csum_seed"
    label = superblock[120:136].split(b"\0", 1)[0].decode()
    assert label == "ROOTFS", label
    assert image.stat().st_size == 512 * 1024 * 1024
    sha = hashlib.file_digest(image.open("rb"), "sha256").hexdigest()
    return {"scope": "static headless rootfs audit, not a boot or hardware test",
            "elf_aarch64_count": elf_count + module_count,
            "userspace_aarch64_count": elf_count, "kernel_module_aarch64_et_rel_count": module_count,
            "module_release": module_audit.RELEASE if module_count else None,
            "interpreters": sorted(interpreters),
            "glibc_linux_abi_note": libc["gnu_linux_abi"],
            "ext4": {"label": label, "bytes": image.stat().st_size,
                     "compat": hex(compat), "incompat": hex(incompat),
                     "ro_compat": hex(ro_compat), "sha256": sha},
            "boot_tested": False, "muos_sysinit_integrated": False}


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1])), indent=2))
