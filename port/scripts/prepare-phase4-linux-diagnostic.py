#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a minimal external initramfs from the already-audited own sysroot."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import shutil
import stat
import struct
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[2]
work = repo/'build/phase4'
target = work/'graphics-config/output/target'
out = work/'linux-diagnostic'
out.mkdir(exist_ok=True)
stage = Path(tempfile.mkdtemp(prefix='initramfs.', dir=out))
root = stage/'root'
root.mkdir()
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
kernel = work/'kernel-output/arch/arm64/boot/Image'
dtb = work/'kernel-output/arch/arm64/boot/dts/rockchip/rk3326-muos-r35s-panel0.dtb'
assert sha(kernel) == '780935823cb8c86e4330c8c8157ebb4005fb5580e68e72c4b0c4e480bab42d2f'
assert sha(dtb) == '496bbe3591f8619f059ebc384277ecdd17fd41f956aef40de20afb46b92d5b49'
config = (work/'kernel-output/.config').read_text().splitlines()
for name in ['BLK_DEV_INITRD','RD_GZIP','DEVTMPFS','VT_CONSOLE','FRAMEBUFFER_CONSOLE',
             'DRM_FBDEV_EMULATION','PROC_FS','SYSFS','VFAT_FS','MMC_BLOCK']:
    assert f'CONFIG_{name}=y' in config, name
header = kernel.read_bytes()[:64]
text_offset, memory_size, flags = struct.unpack_from('<QQQ', header, 8)
assert struct.unpack_from('<I', header, 56)[0] == 0x644d5241
assert (text_offset, memory_size, flags) == (0x80000, 0xe40000, 0xa)
# Copy only BusyBox and its three direct shared-library providers. Dereference
# source symlinks; never import a host binary or an installed Debian library.
for directory in ['bin','lib','dev','proc','sys','run','boot','tmp','etc']:
    (root/directory).mkdir()
(root/'lib64').symlink_to('lib')
sources = {'bin/busybox':target/'bin/busybox'}
for name in ['ld-linux-aarch64.so.1','libc.so.6','libresolv.so.2']:
    sources['lib/'+name] = target/'lib'/name
for name, path in sources.items():
    shutil.copyfile(path, root/name)
    os.chmod(root/name, 0o755)
    data=(root/name).read_bytes()
    assert data[:7] == b'\x7fELF\x02\x01\x01' and struct.unpack_from('<H',data,18)[0] == 183, name
for name in ['init','card-guard.sh']:
    shutil.copyfile(repo/'port/device/rk-r35s-p0/linux-diagnostic'/name, root/name)
    os.chmod(root/name, 0o755)
applets = ['sh','cat','cp','dmesg','echo','mkdir','mount','printf','sha256sum',
           'sleep','sync','tr','umount','uname','test']
for name in applets:
    (root/'bin'/name).symlink_to('busybox')
(root/'etc/passwd').write_text('root:x:0:0:root:/:/bin/sh\n')
(root/'etc/group').write_text('root:x:0:\n')
# newc: emit ownership and device nodes without mknod/root on the build host.
epoch = 1792886400
archive = bytearray()
inode = 0
def entry(name, mode, data=b'', rmajor=0, rminor=0):
    global inode
    inode += 1
    fields = [inode, mode, 0, 0, 1, epoch, len(data), 0, 0, rmajor, rminor,
              len(name.encode())+1, 0]
    archive.extend(b'070701'+''.join(f'{x:08x}' for x in fields).encode())
    archive.extend(name.encode()+b'\0')
    archive.extend(b'\0'*(-len(archive)%4))
    archive.extend(data)
    archive.extend(b'\0'*(-len(archive)%4))
entry('.', stat.S_IFDIR|0o755)
for path in sorted(root.rglob('*')):
    name = str(path.relative_to(root))
    if path.is_symlink():
        entry(name, stat.S_IFLNK|0o777, os.readlink(path).encode())
    elif path.is_dir():
        entry(name, stat.S_IFDIR|0o755)
    else:
        entry(name, stat.S_IFREG|stat.S_IMODE(path.stat().st_mode), path.read_bytes())
entry('dev/console', stat.S_IFCHR|0o600, rmajor=5, rminor=1)
entry('dev/null', stat.S_IFCHR|0o666, rmajor=1, rminor=3)
entry('TRAILER!!!', 0)
archive.extend(b'\0'*(-len(archive)%512))
(stage/'initramfs.cpio').write_bytes(archive)
with (stage/'initramfs.cpio.gz').open('xb') as stream:
    with gzip.GzipFile(fileobj=stream, mode='wb', filename='', mtime=epoch) as zipped:
        zipped.write(archive)
assert (stage/'initramfs.cpio.gz').stat().st_size < 0x800000
assets = {'Image':kernel, 'rk3326-muos-r35s-panel0.dtb':dtb,
          'initramfs.cpio.gz':stage/'initramfs.cpio.gz'}
record = {'scope':'minimal diagnostic initramfs, not the product rootfs',
          'kernel_release':'4.4.189-muos-r35s-p4','experiment':'MUOS-R35S-LINUX-P4-A01',
          'assets':{name:{'path':str(path), 'bytes':path.stat().st_size,'sha256':sha(path)} for name,path in assets.items()},
          'kernel_image_header':{'text_offset':hex(text_offset),'memory_size':hex(memory_size),'flags':hex(flags)},
          'sysroot_files':{name:sha(path) for name,path in sources.items()},
          'initramfs_regular_files':{str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and not p.is_symlink()},
          'port_inputs':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/device/rk-r35s-p0/linux-diagnostic/init',repo/'port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh']},
          'external_ramdisk_address':'0x0a200000','maximum_ramdisk_bytes':0x800000,
          'userspace_qemu_checked':False,'native_boot_tested':False,'product_services_started':False}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
(out/'latest-initramfs').write_text(str(stage)+'\n')
print('Minimal initramfs prepared:',stage)
