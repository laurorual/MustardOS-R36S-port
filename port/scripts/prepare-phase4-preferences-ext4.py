#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the C19 ext4 laboratory and format only a new host regular image."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'preferences'
stage=Path(tempfile.mkdtemp(prefix='ext4.',dir=area));stage.chmod(0o755)
previous=Path((area/'latest-checks').read_text().strip())
old=json.loads((previous/'manifest.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert old['host_passed'] and old['case_count']==16
for n,d in old['sources'].items():assert sha(repo/n)==d,n
assert sha(previous/'muos-preferences')==old['production_binary_sha256']
shutil.copyfile(previous/'muos-preferences',stage/'muos-preferences')
source=repo/'port/diagnostics/phase4-preferences-ext4.c'
shutil.copyfile(source,stage/source.name)
baseline=work/'network-tools/baseline.config'
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
container=(work/'rootfs-container.iid').read_text().strip()
relative='/work/'+str(stage.relative_to(work))
cc='/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc'
flags='-O2 -g0 -march=armv8-a -mtune=cortex-a35 -std=c11 -Wall -Wextra -Werror -fPIE -pie -Wl,-z,relro,-z,now'
code=f'''set -eu
cd {relative}
{cc} {flags} phase4-preferences-ext4.c -o phase4-preferences-ext4
readelf -h -l -d -n --version-info phase4-preferences-ext4 > elf.txt
test ! -e data.ext4
truncate -s 16777216 data.ext4
mke2fs -q -F -t ext4 -b 4096 -I 256 -m 0 -L MUOSPREFSLAB \\
 -U 6d756f73-c019-4000-8000-000000000001 \\
 -O none,has_journal,ext_attr,resize_inode,dir_index,filetype,extent,sparse_super,large_file,uninit_bg,dir_nlink,extra_isize \\
 -E lazy_itable_init=0,lazy_journal_init=0 data.ext4
e2fsck -fn data.ext4 > fsck-before.txt 2>&1
dumpe2fs -h data.ext4 > superblock.txt 2>&1
'''
r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
 '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
 '-v',f'{work}:/work:rw,z',container,'sh','-c',code],capture_output=True,text=True,timeout=45)
for n,v in [('build.stdout',r.stdout),('build.stderr',r.stderr)]: (stage/n).write_text(v)
assert r.returncode==0,(stage,r.stdout,r.stderr)
elf=(stage/'elf.txt').read_text()
assert 'AArch64' in elf and 'ABI: 4.4.0' in elf and '/lib/ld-linux-aarch64.so.1' in elf
features=(stage/'superblock.txt').read_text().split('Filesystem features:')[1].splitlines()[0].split()
assert set(features)=={'has_journal','ext_attr','resize_inode','dir_index','filetype','extent',
 'sparse_super','large_file','uninit_bg','dir_nlink','extra_isize'},features
# No CAP_SYS_ADMIN, devices or real mount operations in the host fixtures.
fixture=r'''set -eu
lab() { qemu-aarch64 -cpu cortex-a35 -L / /sysroot/lib/ld-linux-aarch64.so.1 --inhibit-cache --library-path /sysroot/lib:/sysroot/usr/lib /payload/phase4-preferences-ext4 "$@"; }
refuse() { set +e;lab "$@";rc=$?;set -e;test "$rc" = 64; }
refuse;echo 'PASS missing-arguments'
refuse /dev/mmcblk0;echo 'PASS block-path-refused'
refuse /run/muos-prefs-ext4.ABCDEF/../ABCDEF;echo 'PASS traversal-refused'
refuse /run/muos-prefs-ext4.ABCDEF --unknown;echo 'PASS unknown-mode-refused'
mkdir -m 700 /run/real
ln -s /run/real /run/muos-prefs-ext4.ABCDEF
refuse /run/muos-prefs-ext4.ABCDEF;echo 'PASS symlink-lab-refused'
rm /run/muos-prefs-ext4.ABCDEF
mkdir -m 777 /run/muos-prefs-ext4.ABCDEF
refuse /run/muos-prefs-ext4.ABCDEF;echo 'PASS unsafe-owner-mode-refused'
chmod 700 /run/muos-prefs-ext4.ABCDEF
refuse /run/muos-prefs-ext4.ABCDEF;echo 'PASS missing-helper-refused'
cp /payload/muos-preferences /run/muos-prefs-ext4.ABCDEF/muos-preferences
chmod 700 /run/muos-prefs-ext4.ABCDEF/muos-preferences
mkdir -m 700 /run/muos-prefs-ext4.ABCDEF/mnt
truncate -s 4096 /run/muos-prefs-ext4.ABCDEF/data.ext4
chmod 600 /run/muos-prefs-ext4.ABCDEF/data.ext4
before=$(sha256sum /run/muos-prefs-ext4.ABCDEF/data.ext4)
refuse /run/muos-prefs-ext4.ABCDEF
test "$before" = "$(sha256sum /run/muos-prefs-ext4.ABCDEF/data.ext4)"
echo 'PASS wrong-image-size-refused-unchanged'
'''
(stage/'fixture.sh').write_text(fixture)
# Reuse the sysroot that passed the existing production store ABI check.
root=work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted'
r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
 '--security-opt=no-new-privileges','--userns=keep-id','--user=0','--tmpfs','/run:rw,nosuid,nodev',
 '-v',f'{stage}:/payload:ro,z','-v',f'{root}:/sysroot:ro,z',container,'sh','/payload/fixture.sh'],
 capture_output=True,text=True,timeout=30)
for n,v in [('stdout',r.stdout),('stderr',r.stderr)]: (stage/n).write_text(v)
assert r.returncode==0,(stage,r.stdout,r.stderr)
cases=[n[5:] for n in r.stdout.splitlines() if n.startswith('PASS ')];assert len(cases)==8,cases
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
meta={'host_passed':True,'case_count':len(cases),'cases':cases,'SDK_config_unchanged':True,
 'native_tested':False,'persistent_mode_enabled':False,'card_devices_or_partitions_touched':False,
 'flags':flags,'container':container,'image_bytes':16777216,'features':features,
 'production_store_sha256':old['production_binary_sha256'],
 'payloads':{n:sha(stage/n) for n in ['phase4-preferences-ext4','muos-preferences','data.ext4']},
 'sources':{str(p.relative_to(repo)):sha(p) for p in [source,Path(__file__)]}}
(stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
(area/'latest-ext4').write_text(str(stage)+'\n')
print('C19 ext4 lab built; eight host refusal cases and regular-image fsck passed:',stage)
