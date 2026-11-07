#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C55 real Kconfig/rsync/legal-info and recipe macros, with the existing SDK."""
from pathlib import Path
import json,re,shutil,subprocess,tarfile,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'save-store-package';area.mkdir(exist_ok=True)
baseline=work/'network-tools/baseline.config'
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
for name in ['save-store-laboratory','gameboy-after-boot']:
 for n,h in sums(repo/'dist/phase4'/name/'SHA256SUMS').items():assert sha(repo/'dist/phase4'/name/n)==h
approved=Path((work/'save-store/latest-checks').read_text().strip());ar=json.loads((approved/'analysis.json').read_text());assert ar['passed']
for n,h in ar['source_sha256'].items():assert sha(repo/n)==h
pkg=repo/'port/buildroot/package/muos-save-store'
inputs={'muos-save-store.c':repo/'port/utils/muos-save-store.c','LICENSE':repo/'port/LICENSE','contract.json':pkg/'contract.json'}
assert inputs['muos-save-store.c'].read_text().startswith('// SPDX-License-Identifier: MIT')
source=area/'source'
if not source.exists():
 source.mkdir(mode=0o755)
 for n,p in inputs.items():shutil.copyfile(p,source/n)
assert {p.name for p in source.iterdir()}==set(inputs)
for n,p in inputs.items():assert not (source/n).is_symlink() and sha(source/n)==sha(p)
stage=Path(tempfile.mkdtemp(prefix='build.',dir=area));rel=lambda p:'/work/'+str(p.relative_to(work))
(area/'latest-build-attempt').write_text(str(stage)+'\n')
minimal=stage/'minimal.defconfig';minimal.write_text('BR2_aarch64=y\nBR2_cortex_a35=y\nBR2_TOOLCHAIN_BUILDROOT_GLIBC=y\n')
output=stage/'output'
code=f'''
make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot BR2_DEFCONFIG={rel(minimal)} defconfig
! grep -qx BR2_PACKAGE_MUOS_SAVE_STORE=y {rel(output)}/.config
! grep -qx BR2_PACKAGE_ZLIB=y {rel(output)}/.config
cp {rel(output)}/.config {rel(stage)}/default.config
echo C55_PASS_default_off
/work/buildroot/utils/config --file {rel(output)}/.config --enable BR2_PACKAGE_MUOS_SAVE_STORE
make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot olddefconfig
grep -qx BR2_PACKAGE_MUOS_SAVE_STORE=y {rel(output)}/.config
grep -qx BR2_PACKAGE_ZLIB=y {rel(output)}/.config
grep -qx BR2_PACKAGE_LIBZLIB=y {rel(output)}/.config
for key in MUOS_CORE MUOS_R35S_SESSION MUOS_R35S_BOOT MUOS_R35S_LAUNCHER_ONCE;do
 ! grep -qx "BR2_PACKAGE_$key=y" {rel(output)}/.config
done
cp {rel(output)}/.config {rel(stage)}/opt-in.config
echo C55_PASS_opt_in_zlib_without_services
make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot muos-save-store-rsync
make -s --no-print-directory -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot printvars VARS=MUOS_SAVE_STORE_BUILDDIR > {rel(stage)}/build-vars.txt
make -s --no-print-directory -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot muos-save-store-show-info > {rel(stage)}/package-info.json
/work/buildroot/utils/config --file {rel(output)}/.config --keep-case --disable BR2_aarch64 --enable BR2_i386 --enable BR2_PACKAGE_MUOS_SAVE_STORE
make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot olddefconfig
! grep -qx BR2_PACKAGE_MUOS_SAVE_STORE=y {rel(output)}/.config
cp {rel(output)}/.config {rel(stage)}/wrong-arch.config
echo C55_PASS_wrong_arch_refused
'''
container=(work/'rootfs-container.iid').read_text().strip()
def run(label,code,timeout=90):
 (stage/(label+'.sh')).write_text(code)
 cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
      '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',container,'sh','-eu','-c',code]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
 for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+n)).write_text(v)
 assert r.returncode==0,(stage,label,r.stdout[-2000:],r.stderr[-2500:])
 return r.stdout
text=run('kconfig',code)
def selected(name):
 return {line for line in (stage/name).read_text().splitlines() if line.endswith('=y')}
assert 'BR2_PACKAGE_MUOS_SAVE_STORE=y' not in selected('default.config')
assert 'BR2_PACKAGE_ZLIB=y' not in selected('default.config')
assert {'BR2_PACKAGE_MUOS_SAVE_STORE=y','BR2_PACKAGE_ZLIB=y','BR2_PACKAGE_LIBZLIB=y'}<=selected('opt-in.config')
for key in ['MUOS_CORE','MUOS_R35S_SESSION','MUOS_R35S_BOOT','MUOS_R35S_LAUNCHER_ONCE']:
 assert 'BR2_PACKAGE_'+key+'=y' not in selected('opt-in.config')
assert 'BR2_i386=y' in selected('wrong-arch.config')
assert 'BR2_PACKAGE_MUOS_SAVE_STORE=y' not in selected('wrong-arch.config')
match=re.fullmatch(r'MUOS_SAVE_STORE_BUILDDIR=(/work/[^\n]+)\n',(stage/'build-vars.txt').read_text());assert match
build=work/match[1].removeprefix('/work/');assert build.is_relative_to(stage)
assert {p.name for p in build.iterdir() if not p.name.startswith('.')}==set(inputs)
for n,p in inputs.items():assert sha(build/n)==sha(p)
run('legal-info',f'make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot muos-save-store-legal-info\n')
archives=list((output/'legal-info').rglob('muos-save-store-*.tar.gz'));assert len(archives)==1
with tarfile.open(archives[0]) as archive:
 members={Path(m.name).name:archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
assert set(members)==set(inputs)
for n,p in inputs.items():assert members[n]==p.read_bytes()
legal=list((output/'legal-info').glob('licenses/muos-save-store-*/LICENSE'));assert len(legal)==1 and sha(legal[0])==sha(inputs['LICENSE'])
target=stage/'target';target.mkdir()
harness=stage/'recipe.mk'
harness.write_text(f'''BR2_EXTERNAL_MUOS_R35S_PATH := /port/buildroot
TARGET_CC := /work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
TARGET_CFLAGS := -O2 -mcpu=cortex-a35
TARGET_DIR := {rel(target)}
INSTALL := install
generic-package =
include /port/buildroot/package/muos-save-store/muos-save-store.mk
.PHONY: all
all: {rel(build)}/.c55-build
{rel(build)}/.c55-build:
\t$(MUOS_SAVE_STORE_BUILD_CMDS)
\t$(MUOS_SAVE_STORE_INSTALL_TARGET_CMDS)
''')
code=f'''make -f {rel(harness)} all
/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-readelf -h -l -d -n --version-info {rel(target)}/usr/libexec/muos-save-store/muos-save-store > {rel(stage)}/elf.txt
'''
run('recipe',code)
binary=target/'usr/libexec/muos-save-store/muos-save-store'
expected={'usr/libexec/muos-save-store/muos-save-store','usr/libexec/muos-save-store/payload.sha256',
          'usr/share/muos-save-store/contract.json','usr/share/licenses/muos-save-store/LICENSE'}
assert {str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()}==expected
assert binary.stat().st_mode&0o777==0o755
for p in target.rglob('*'):
 assert not p.is_symlink()
 if p.is_file() and p!=binary:assert p.stat().st_mode&0o777==0o644
payload=sums(target/'usr/libexec/muos-save-store/payload.sha256');assert len(payload)==3
for n,h in payload.items():assert n.startswith('/') and sha(target/n.lstrip('/'))==h
elf=(stage/'elf.txt').read_text()
for value in ['AArch64','DYN (Position-Independent Executable file)','/lib/ld-linux-aarch64.so.1','ABI: 4.4.0','libz.so.1']:assert value in elf,value
assert 'RUNPATH' not in elf and 'RPATH' not in elf
identical=sha(binary)==ar['binary_sha256']
# Reuse transaction/remount proof only for the exact already-qualified ELF.
assert identical,(sha(binary),ar['binary_sha256'])
code=f'''root=/work/rootfs-candidate/composition.w59vz7vo/target
rc=0
qemu-aarch64 -cpu cortex-a35 -L / -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$root/lib:$root/usr/lib" {rel(binary)} || rc=$?
[ "$rc" = 64 ]
echo C55_PASS_A35_loader_and_CLI_refusal
'''
text+=run('loader',code)
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
sources=[Path(__file__),*pkg.iterdir(),repo/'port/buildroot/Config.in',repo/'port/LICENSE',repo/'port/utils/muos-save-store.c']
report={'passed':True,'experiment':'C55_BUILDROOT_SAVE_STORE','binary_sha256':sha(binary),'C52_binary_byte_identical':identical,
        'real_Kconfig_rsync_legal_info':True,'MIT_license_and_source_archive_verified':True,
        'default_off':True,'zlib_dependency_selected':True,'service_boot_dependencies_selected':False,'wrong_arch_refused':True,
        'target_files':sorted(expected),'payload_files':3,'SDK_config_unchanged':True,'device_written':False,
        'full_Buildroot_image_built':False,'source_archive_sha256':sha(archives[0]),
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-build').write_text(str(stage)+'\n')
print('C55 real recipe/Kconfig/legal-info/ABI passed:',stage)
