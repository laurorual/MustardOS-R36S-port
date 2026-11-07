#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Clone the audited ext4 and install a diagnostic PID1; host files only."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
out=work/'linux-diagnostic';out.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='ext4.',dir=out));assets=stage/'assets';assets.mkdir()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
base=work/'graphics-config/output/images/rootfs.ext4'
assert sha(base)=='ccdb9c0a7d232f8dc628a86ceb911c53247d74dd0e14802e0907459bddf13fc0'
assert base.stat().st_size==512*1024*1024
shutil.copyfile(base,stage/'rootfs.ext4')
inputs={
 'init':repo/'port/device/rk-r35s-p0/ext4-diagnostic/init',
 'card-guard':repo/'port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh'}
for name,p in inputs.items():shutil.copyfile(p,assets/name)
(assets/'ui-default').write_text('enabled=0\nhotkeys=0\nattempts=60\n')
(assets/'marker').write_text('MUOS-R35S-EXT4-P4-B01\n')
commands=['mkdir /boot']
for name,target,mode in [('init','/sbin/muos-ext4-diag','0100755'),
                         ('card-guard','/usr/libexec/muos-diag-card-guard','0100644'),
                         ('marker','/etc/muos-ext4-diagnostic','0100644')]:
    commands += [f'write assets/{name} {target}',f'set_inode_field {target} mode {mode}']
commands += ['rm /etc/default/muos-ui','write assets/ui-default /etc/default/muos-ui',
             'set_inode_field /etc/default/muos-ui mode 0100644']
(stage/'debugfs.commands').write_text('\n'.join(commands)+'\n')
image=(work/'rootfs-container.iid').read_text().strip()
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
     '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',
     '-e','STAGE_REL='+str(stage.relative_to(work)),image,'sh','-eu','-c',r'''
cd "/work/$STAGE_REL"
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
dumpe2fs -h rootfs.ext4 > superblock.txt 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
debugfs -R 'stat /sbin/muos-ext4-diag' rootfs.ext4 > init-inode.txt 2>&1
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/sbin/muos-ext4-diag"
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/usr/bin/kmod" --version > kmod-version.txt
qemu-aarch64 -cpu cortex-a35 -L "$root" -0 modprobe "$root/usr/bin/kmod" -d "$root" -S 4.4.189-muos-r35s-p4 --show-depends gpio_keys > gpio-keys-dependencies.txt
if qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh "$root/sbin/muos-ext4-diag" > pid-guard.txt 2>&1; then exit 1; else test "$?" = 64; fi
''']
with (stage/'audit.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90)
root=stage/'extracted'
assert (root/'boot').is_dir()
assert sha(root/'sbin/muos-ext4-diag')==sha(inputs['init'])
assert sha(root/'usr/libexec/muos-diag-card-guard')==sha(inputs['card-guard'])
assert (root/'etc/default/muos-ui').read_text()==(assets/'ui-default').read_text()
assert (root/'etc/muos-ext4-diagnostic').read_text().strip()=='MUOS-R35S-EXT4-P4-B01'
assert 'Mode:  0755' in (stage/'init-inode.txt').read_text()
assert 'gpio_keys.ko' in (stage/'gpio-keys-dependencies.txt').read_text()
features=(stage/'superblock.txt').read_text().split('Filesystem features:')[1].splitlines()[0].split()
assert not {'64bit','orphan_file','metadata_csum_seed','fast_commit','casefold','encrypt'} & set(features)
kernel=work/'kernel-output/arch/arm64/boot/Image'
dtb=work/'kernel-output/arch/arm64/boot/dts/rockchip/rk3326-muos-r35s-panel0.dtb'
assert sha(kernel)=='780935823cb8c86e4330c8c8157ebb4005fb5580e68e72c4b0c4e480bab42d2f'
assert sha(dtb)=='496bbe3591f8619f059ebc384277ecdd17fd41f956aef40de20afb46b92d5b49'
record={'scope':'cloned own ext4 with diagnostic PID1, no product rcS/UI startup',
 'experiment':'MUOS-R35S-EXT4-P4-B01','kernel_release':'4.4.189-muos-r35s-p4',
 'assets':{name:{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for name,p in [('Image',kernel),('rk3326-muos-r35s-panel0.dtb',dtb)]},
 'rootfs':{'path':str(stage/'rootfs.ext4'),'bytes':(stage/'rootfs.ext4').stat().st_size,'sha256':sha(stage/'rootfs.ext4'),'base_sha256':sha(base),'features':features},
 'userspace_qemu_checked':True,'frontend_enabled':False,'root_partuuid':'4d554432-02',
 'image_bytes':640*1024*1024,'root_offset':128*1024*1024,
 'container_image_id':image,'native_boot_tested':False,
 'port_inputs':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),*inputs.values()]}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
(out/'latest-ext4').write_text(str(stage)+'\n')
print('Diagnostic ext4 cloned and audited:',stage)
