#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C60 source-only host recipe with pinned private link SDK and isolated config."""
from pathlib import Path
import json,re,shutil,subprocess,tarfile,tempfile
from phase4_candidate import inventory,sha,sums,validate
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro-package';area.mkdir(exist_ok=True)
baseline=work/'network-tools/baseline.config';assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
for name in ['gameboy-installed-store','gameboy-hotkey-exit']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
approved=work/'gb-exit/host.uuixcmie';ar=json.loads((approved/'analysis.json').read_text());assert ar['passed']
assert sha(approved/'source/bin/muxretro')==ar['binary_sha256']
# Walk the already-qualified ancestry; never rebuild or mutate those stages.
p=approved;chain=[]
while True:
 r=json.loads((p/'analysis.json').read_text());assert r['passed']
 for n,h in r['source_sha256'].items():assert sha(repo/n)==h,n
 chain.append({'stage':p.name,'analysis_sha256':sha(p/'analysis.json')})
 if 'parent_stage' not in r:break
 parent=Path(r['parent_stage']);assert sha(parent/'analysis.json')==r['parent_analysis_sha256'];p=parent
origin=json.loads((work/'menu/source-manifest.json').read_text());archive=work/'menu/frontend-source.tar'
assert sha(archive)==origin['frontend_archive_sha256']
rc_commit='2ad0b8672f68a48148620164510b963039e49eb1';rc_archive=work/'muxretro/cache'/('rcheevos-'+rc_commit+'.tar.gz')
assert sha(rc_archive)=='b8e3e834d15c327085154315c49dea85b081ad48592ba1740f323ac953e1bfec'
stage=Path(tempfile.mkdtemp(prefix='build.',dir=area));(area/'latest-attempt').write_text(str(stage)+'\n')
reconstructed=stage/'reconstructed';reconstructed.mkdir()
with tarfile.open(archive) as tar:tar.extractall(reconstructed,filter='data')
patch_names=['0003-frontend-r35s-panel0-board.patch','0006-frontend-r35s-normalized-volume.patch','0007-muxretro-no-content.patch','0008-muxretro-buildroot-headers.patch','0009-muxretro-diagnostic-deadline.patch','0012-muxretro-diagnostic-content.patch','0015-muxretro-diagnostic-hotkey-exit.patch']
patches=[repo/'port/patches'/n for n in patch_names]
header=repo/'port/diagnostics/phase4-diagnostic-exit.h';shutil.copyfile(header,reconstructed/'retro/core'/header.name)
for patch in patches:subprocess.run(['git','-C',str(reconstructed),'apply',str(patch)],check=True)
def relevant(p):return p.suffix in {'.c','.h','.hpp','.inc','.def','.mk'} or p.name in {'Makefile','LICENSE','COPYING','COPYING.LESSER'}
inputs={str(p.relative_to(reconstructed)):p for p in reconstructed.rglob('*') if p.is_file() and relevant(p)}
old={str(p.relative_to(approved/'source')):p for p in (approved/'source').rglob('*') if p.is_file() and relevant(p) and not p.is_symlink()}
assert set(inputs)==set(old),(set(inputs)-set(old),set(old)-set(inputs))
for n,p in inputs.items():assert sha(p)==sha(old[n]),n
# The local SITE contains only text source/license/provenance. The four SDK
# libraries live outside SITE, so legal-info cannot archive them accidentally.
source=stage/'prepared-source';source.mkdir()
for n,p in inputs.items():
 out=source/'frontend'/n;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
with tarfile.open(rc_archive) as tar:tar.extractall(stage/'rc-unpack',filter='data')
rc=stage/'rc-unpack'/('rcheevos-'+rc_commit)
for p in rc.rglob('*'):
 if p.is_file() and relevant(p):
  out=source/'rcheevos'/p.relative_to(rc);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
assert 'MIT License' in (source/'rcheevos/LICENSE').read_text()
assert 'Version 3, 29 June 2007' in (source/'frontend/LICENSE').read_text()
pkg=repo/'port/buildroot/package/muos-muxretro';shutil.copyfile(pkg/'build-host.sh',source/'build-host.sh')
platform=area/'platform'
root=work/'rootfs-candidate/composition.w59vz7vo/target'
platform_names=['libui.so','libmuxcom.so','libmuxmod.so','libplutosvg.so']
if platform.exists():
 assert not platform.is_symlink()
 assert {str(p.relative_to(platform)) for p in platform.rglob('*') if p.is_file()}=={'lib/'+n for n in platform_names}
else:platform.mkdir();(platform/'lib').mkdir()
for name in platform_names:
 path=root/'opt/muos/frontend/lib'/name;assert path.is_file() and not path.is_symlink()
 out=platform/'lib'/name
 if out.exists():assert not out.is_symlink() and sha(out)==sha(path),out
 else:shutil.copyfile(path,out)
(source/'platform.sha256').write_text(''.join(sha(platform/'lib'/n)+'  lib/'+n+'\n' for n in platform_names))
meta={'frontend_revision':origin['frontend_revision'],'frontend_archive_sha256':sha(archive),
 'rcheevos_commit':rc_commit,'rcheevos_archive_sha256':sha(rc_archive),'patches':{p.name:sha(p) for p in patches},
 'diagnostic_header_sha256':sha(header),'all_prepared_frontend_source_matches_C50':True,'frontend_source_files':len(inputs),
 'C50_binary_sha256':ar['binary_sha256'],'private_platform_manifest_sha256':sha(source/'platform.sha256'),
 'private_only':True,'full_frontend_provider_integrated':False,'activation':'manual private runtime only; no service or defaults',
 'cores_ROMs_saves_or_platform_binaries_packaged':False}
(source/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
license_names=['frontend/LICENSE','rcheevos/LICENSE','frontend/retro/core/libretro.h',*('frontend/vendor/'+n+'/LICENSE' for n in ['miniz','xxhash','stb','mini','json','mdns'])]
(pkg/'muos-muxretro.hash').write_text('# Locally computed from the pinned prepared sources.\n'+''.join('sha256  '+sha(source/n)+'  '+n+'\n' for n in license_names))
expected={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
assert not any((source/n).read_bytes().startswith(b'\x7fELF') for n in expected)
(stage/'source-files.json').write_text(json.dumps(expected,sort_keys=True,indent=2)+'\n')
site=area/'source'
if site.exists():
 assert not site.is_symlink() and not any(p.is_symlink() for p in site.rglob('*'))
 assert {str(p.relative_to(site)):sha(p) for p in site.rglob('*') if p.is_file()}==expected,'Existing SITE differs; preserve it and inspect'
else:shutil.copytree(source,site)
rel=lambda p:'/work/'+str(p.relative_to(work))
container=(work/'rootfs-container.iid').read_text().strip()
def run(label,code,timeout=90):
 (stage/(label+'.sh')).write_text(code)
 cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',container,'sh','-eu','-c',code]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
 for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+n)).write_text(v)
 assert r.returncode==0,(stage,label,r.stderr[-2000:],r.stdout[-1000:])
 return r.stdout
output=stage/'output';minimal=stage/'minimal.defconfig'
minimal.write_text('BR2_aarch64=y\nBR2_cortex_a35=y\nBR2_TOOLCHAIN_BUILDROOT_GLIBC=y\nBR2_TOOLCHAIN_BUILDROOT_CXX=y\nBR2_PACKAGE_ROCKCHIP_MALI=y\n')
code=f'''make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot BR2_DEFCONFIG={rel(minimal)} defconfig
cp {rel(output)}/.config {rel(stage)}/default.config
/work/buildroot/utils/config --file {rel(output)}/.config --enable BR2_PACKAGE_MUOS_MUXRETRO
make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot olddefconfig
cp {rel(output)}/.config {rel(stage)}/without-sdk.config
/work/buildroot/utils/config --file {rel(output)}/.config --enable BR2_MUOS_PRIVATE_FRONTEND_SDK --enable BR2_PACKAGE_MUOS_MUXRETRO
make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot olddefconfig
cp {rel(output)}/.config {rel(stage)}/opt-in.config
make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot muos-muxretro-rsync
make -s --no-print-directory -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot printvars VARS=MUOS_MUXRETRO_BUILDDIR > {rel(stage)}/build-vars.txt
make -s --no-print-directory -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot muos-muxretro-show-info > {rel(stage)}/package-info.json
'''
run('kconfig',code)
def selected(n):return {s for s in (stage/n).read_text().splitlines() if s.endswith('=y')}
assert 'BR2_PACKAGE_MUOS_MUXRETRO=y' not in selected('default.config')
assert 'BR2_MUOS_PRIVATE_FRONTEND_SDK=y' not in selected('default.config')
assert 'BR2_PACKAGE_MUOS_MUXRETRO=y' not in selected('without-sdk.config')
assert 'BR2_PACKAGE_MUOS_MUXRETRO=y' in selected('opt-in.config')
for n in ['SDL2','SDL2_IMAGE','SDL2_MIXER','SDL2_TTF','HARFBUZZ','FREETYPE','LIBPNG','LIBCURL','LIBARCHIVE','OPENSSL','ZLIB']:
 assert 'BR2_PACKAGE_'+n+'=y' in selected('opt-in.config'),n
for n in ['MUOS_CORE','MUOS_R35S_SESSION','MUOS_R35S_BOOT','MUOS_R35S_LAUNCHER_ONCE','MUOS_SAVE_STORE']:
 assert 'BR2_PACKAGE_'+n+'=y' not in selected('opt-in.config'),n
match=re.fullmatch(r'MUOS_MUXRETRO_BUILDDIR=(/work/[^\n]+)\n',(stage/'build-vars.txt').read_text());assert match
build=work/match[1].removeprefix('/work/');assert build.is_relative_to(stage)
actual={str(p.relative_to(build)):sha(p) for p in build.rglob('*') if p.is_file() and not p.name.startswith('.')}
assert actual==expected
run('legal-info',f'make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot muos-muxretro-legal-info\n')
archives=list((output/'legal-info').rglob('muos-muxretro-*.tar.gz'));assert len(archives)==1
with tarfile.open(archives[0]) as tar:
 members={str(Path(m.name).relative_to('muos-muxretro-1')):tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
assert set(members)==set(expected)
for n,data in members.items():assert data==(source/n).read_bytes(),n
for n in license_names:
 legal=output/'legal-info/licenses/muos-muxretro-1'/n;assert sha(legal)==sha(source/n),n
# Real Kconfig rejects wrong ISA as well; preserve the opted-in receipt above.
run('wrong-arch',f'''/work/buildroot/utils/config --file {rel(output)}/.config --keep-case --disable BR2_aarch64 --enable BR2_i386 --enable BR2_PACKAGE_MUOS_MUXRETRO
make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot olddefconfig
cp {rel(output)}/.config {rel(stage)}/wrong-arch.config
''')
assert 'BR2_i386=y' in selected('wrong-arch.config') and 'BR2_PACKAGE_MUOS_MUXRETRO=y' not in selected('wrong-arch.config')
target=stage/'target';target.mkdir();harness=stage/'recipe.mk'
harness.write_text(f'''TARGET_CC := /work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
TARGET_AR := /work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-ar
PKG_CONFIG_HOST_BINARY := /work/graphics-config/output/host/bin/pkg-config
STAGING_DIR := /work/graphics-config/output/host/aarch64-buildroot-linux-gnu/sysroot
TARGET_CFLAGS := -O2 -mcpu=cortex-a35
TARGET_DIR := {rel(target)}
INSTALL := install
sep = $(newline)
define newline


endef
generic-package =
include /port/buildroot/package/muos-muxretro/muos-muxretro.mk
.PHONY: all
all: {rel(build)}/.c60-build
{rel(build)}/.c60-build:
\t$(MUOS_MUXRETRO_BUILD_CMDS)
\t$(MUOS_MUXRETRO_INSTALL_TARGET_CMDS)
{rel(build)}/.c60-install:
\t$(MUOS_MUXRETRO_INSTALL_TARGET_CMDS)
''')
guard_compiler=stage/'compiler-must-not-run.sh'
guard_marker=stage/'compiler-was-run'
guard_compiler.write_text('#!/bin/sh\ntouch '+rel(guard_marker)+'\nexit 94\n');guard_compiler.chmod(0o755)
for label in ['missing-sdk','changed-sdk']:
 guard_platform=stage/label
 if label=='changed-sdk':
  shutil.copytree(platform,guard_platform)
  with (guard_platform/'lib/libui.so').open('ab') as stream:stream.write(b'C60 deliberate corruption\n')
 guard_make=stage/(label+'.mk')
 guard_make.write_text(f'include {rel(harness)}\nTARGET_CC := {rel(guard_compiler)}\nMUOS_MUXRETRO_PLATFORM := {rel(guard_platform)}\n{rel(build)}/.c60-guard:\n\t$(MUOS_MUXRETRO_BUILD_CMDS)\n')
 run(label,f'if make -f {rel(guard_make)} {rel(build)}/.c60-guard;then exit 1;fi\n[ ! -e {rel(guard_marker)} ]\necho C60_PASS_{label}_refused_before_compilation\n')
run('recipe',f'make -f {rel(harness)} all\n',timeout=240)
binary=target/'opt/muos/frontend/muxretro';assert binary.is_file()
run('elf',f'/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-readelf -h -l -d -n {rel(binary)}\n')
elf=(stage/'elf.stdout').read_text()
for n in ['AArch64','DYN (Position-Independent Executable file)','/lib/ld-linux-aarch64.so.1','GNU_RELRO','BIND_NOW','/opt/muos/frontend/lib']:assert n in elf,n
assert '/work/' not in '\n'.join(s for s in elf.splitlines() if 'RUNPATH' in s or 'RPATH' in s)
payload=sums(target/'usr/share/muos-muxretro/payload.sha256')
assert len(payload)==3+len(license_names)
for n,h in payload.items():assert sha(target/n.lstrip('/'))==h
expected_target={n.lstrip('/') for n in payload}|{'usr/share/muos-muxretro/payload.sha256'}
assert {str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()}==expected_target
run('loader',f'''root=/work/rootfs-candidate/composition.w59vz7vo/target
export LD_LIBRARY_PATH="$root/opt/muos/frontend/lib:$root/lib:$root/usr/lib"
for op in --version --help;do
 qemu-aarch64 -cpu cortex-a35 -L / -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$LD_LIBRARY_PATH" {rel(binary)} "$op"
done
''')
# Install with the real macro into a new copy, preserving every C56 item.
# This checks the actual private foundation, not a guessed list of paths.
parent=work/'save-store-image/image.nlnmgzzb'
proof=repo/'dist/phase4/save-store-image'
for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,n
assert (parent/'analysis.json').read_bytes()==(proof/'analysis.json').read_bytes()
before=json.loads((parent/'expected-tree.json').read_text())
assert inventory(parent/'target')==before
composition=stage/'composition';shutil.copytree(parent/'target',composition,symlinks=True)
run('composition',f'make -f {rel(harness)} {rel(build)}/.c60-install TARGET_DIR={rel(composition)}\n')
after=inventory(composition)
assert all(after[n]==record for n,record in before.items())
added={n:v for n,v in after.items() if n not in before}
assert {n for n,v in added.items() if v['type']=='file'}==expected_target
assert all(v['type'] in {'file','directory'} for v in added.values())
for n,v in added.items():assert v['mode']==(0o755 if v['type']=='directory' or n=='opt/muos/frontend/muxretro' else 0o644),n
validated=validate(composition);assert validated['foundation_files']==97
for manifest in ['usr/libexec/muos-save-store/payload.sha256','usr/share/muos-muxretro/payload.sha256']:
 for n,h in sums(composition/manifest).items():assert sha(composition/n.lstrip('/'))==h
for n,h in sums(composition/'usr/share/muos-muxretro/platform.sha256').items():assert sha(composition/'opt/muos/frontend'/n)==h
run('composition-contract',f'''root={rel(composition)}
. "$root/usr/libexec/muos-candidate-boot-checks"
candidate_boot_check "$root"
qemu-aarch64 -cpu cortex-a35 -L / -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$root/opt/muos/frontend/lib:$root/lib:$root/usr/lib" "$root/opt/muos/frontend/muxretro" --help
echo C60_PASS_private_composition_C07_and_loader
''')
assert inventory(parent/'target')==before
(stage/'composition-added.json').write_text(json.dumps(added,sort_keys=True,indent=2)+'\n')
assert sha(approved/'source/bin/muxretro')==ar['binary_sha256']
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
for n in platform_names:assert sha(platform/'lib'/n)==sha(root/'opt/muos/frontend/lib'/n)
sources=[Path(__file__),*pkg.iterdir(),repo/'port/buildroot/Config.in',*patches,header]
report={'passed':True,'experiment':'C60_MUXRETRO_PRIVATE_SDK_PACKAGE','default_off':True,'private_SDK_required':True,
 'full_frontend_library_provider_integrated':False,'real_Kconfig_rsync_legal_info':True,'wrong_arch_refused':True,
 'source_only_legal_archive_verified':True,'frontend_source_matches_C50':True,'source_files':len(expected),
 'missing_and_changed_SDK_refused_before_compiler':True,
 'license_files':len(license_names),'binary_sha256':sha(binary),'C50_binary_byte_identical':sha(binary)==ar['binary_sha256'],
 'target_files':sorted(expected_target),'payload_files':len(payload),'clean_source_build':True,'platform_libraries_installed':False,
 'full_Buildroot_rebuild':False,'device_accessed':False,'new_native_runtime_qualified':False,'SDK_config_unchanged':True,
 'source_archive_sha256':sha(archives[0]),'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
report.update({'private_composition':validated,'C56_analysis_sha256':sha(parent/'analysis.json'),
 'C56_existing_items_preserved':len(before),'composition_added_files':len(expected_target),
 'composition_added_directories':sum(v['type']=='directory' for v in added.values()),
 'C07_boot_contract_preserved':True,'private_composition_loader_passed':True,'new_image_built':False})
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-build').write_text(str(stage)+'\n')
print('C60 real host recipe/source/legal/ABI/CLI passed:',stage)
print('C50 binary identical:',report['C50_binary_byte_identical'])
