#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C75 real Buildroot source/legal hooks and controlled SDK core build offline."""
from pathlib import Path
import json, re, shutil, subprocess, tempfile
from phase4_candidate import inventory, sha, sums, validate

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gambatte-package';area.mkdir(exist_ok=True)
baseline=work/'network-tools/baseline.config'
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
parents={}
for name in ['installed-provider-session','installed-provider-return','provider-image']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
 parents[name]=sha(proof/'SHA256SUMS')
commit='77f2567d718b8973d02caa2daa8dce4953faf811'
archive=work/'gb-core/cache'/('gambatte-'+commit+'.tar.gz')
archive_hash='45e63bc79390093b78de025172ea289ded139f4ecf1e8072242f34d7dd540338'
assert sha(archive)==archive_hash
prior=work/'gb-core/build.lgsx_3c2'
old=json.loads((prior/'analysis.json').read_text());assert old['passed'] and old['archive_sha256']==archive_hash
old_core=Path(old['source_stage'])/'gambatte_libretro.so';assert sha(old_core)==old['core_sha256']
qualified=json.loads((repo/'dist/phase4/installed-provider-session/analysis.json').read_text())
assert qualified['physical_image_input_audio_restore_and_return_confirmed']
session=json.loads((work/'installed-provider-session/load.u8qto9s2/analysis.json').read_text())
core_parent=work/'installed-host-session/load.szcr_1jo/analysis.json'
assert session['passed'] and session['C63_analysis_sha256']==sha(core_parent)
assert json.loads(core_parent.read_text())['core_sha256']==old['core_sha256']
stage=Path(tempfile.mkdtemp(prefix='build.',dir=area));(area/'latest-attempt').write_text(str(stage)+'\n')
download=stage/'downloads/muos-gambatte';download.mkdir(parents=True)
shutil.copyfile(archive,download/(commit+'.tar.gz'))
output=stage/'output';pkg=repo/'port/buildroot-libretro/package/muos-gambatte'
rel=lambda p:'/work/'+str(p.relative_to(work))
container=(work/'rootfs-container.iid').read_text().strip()
def run(label,code,timeout=120):
 (stage/(label+'.sh')).write_text(code)
 cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
      '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev,size=512m','-v',f'{work}:/work:rw,z',
      '-v',f'{repo}/port:/port:ro,z',container,'sh','-eu','-c',code]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
 for ext,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+ext)).write_text(v)
 assert r.returncode==0,(stage,label,r.stderr[-2000:],r.stdout[-1000:])
 return r.stdout
minimal=stage/'minimal.defconfig'
minimal.write_text('BR2_aarch64=y\nBR2_cortex_a35=y\nBR2_TOOLCHAIN_BUILDROOT_GLIBC=y\nBR2_TOOLCHAIN_BUILDROOT_CXX=y\nBR2_DL_DIR="'+rel(stage/'downloads')+'"\n')
make=f'make -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot-libretro'
run('source-and-kconfig',f'''{make} BR2_DEFCONFIG={rel(minimal)} defconfig
cp {rel(output)}/.config {rel(stage)}/default.config
/work/buildroot/utils/config --file {rel(output)}/.config --enable BR2_PACKAGE_MUOS_GAMBATTE
{make} olddefconfig
cp {rel(output)}/.config {rel(stage)}/opt-in.config
{make} muos-gambatte-extract
{make} muos-gambatte-legal-info
make -s --no-print-directory -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot-libretro printvars VARS=MUOS_GAMBATTE_BUILDDIR > {rel(stage)}/build-vars.txt
make -s --no-print-directory -C /work/buildroot O={rel(output)} BR2_EXTERNAL=/port/buildroot-libretro muos-gambatte-show-info > {rel(stage)}/package-info.json
''')
assert 'BR2_PACKAGE_MUOS_GAMBATTE=y' not in (stage/'default.config').read_text().splitlines()
assert 'BR2_PACKAGE_MUOS_GAMBATTE=y' in (stage/'opt-in.config').read_text().splitlines()
match=re.fullmatch(r'MUOS_GAMBATTE_BUILDDIR=(/work/[^\n]+)\n',(stage/'build-vars.txt').read_text());assert match
build=work/match[1].removeprefix('/work/');assert build.is_relative_to(stage)
source_files={str(p.relative_to(build)):sha(p) for p in build.rglob('*') if p.is_file() and not p.name.startswith('.stamp_')}
(stage/'source-files.json').write_text(json.dumps(source_files,indent=2,sort_keys=True)+'\n')
license_names=['COPYING','libgambatte/libretro/cc_resampler.c','libgambatte/libretro/cc_resampler.h',
 'libgambatte/libretro/blipper.c','libgambatte/libretro-common/include/libretro.h','libgambatte/libretro-common/streams/file_stream.c']
for n in license_names:
 assert sha(output/'legal-info/licenses'/('muos-gambatte-'+commit)/n)==sha(build/n),n
assert 'GPLv3' in (build/'libgambatte/libretro/cc_resampler.c').read_text()
assert 'version 2 as' in (build/'libgambatte/src/cpu.cpp').read_text()
run('architecture-refusal',f'''/work/buildroot/utils/config --file {rel(output)}/.config --keep-case --disable BR2_aarch64 --enable BR2_i386
{make} olddefconfig
cp {rel(output)}/.config {rel(stage)}/i386.config
cp {rel(stage)}/opt-in.config {rel(output)}/.config
''')
assert 'BR2_i386=y' in (stage/'i386.config').read_text().splitlines()
assert 'BR2_PACKAGE_MUOS_GAMBATTE=y' not in (stage/'i386.config').read_text().splitlines()
target=stage/'target';target.mkdir()
harness=stage/'recipe.mk'
harness.write_text(f'''TARGET_CC := /work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
TARGET_CXX := /work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-g++
TARGET_CFLAGS := -O2 -mcpu=cortex-a35 -fstack-protector-strong -ffile-prefix-map=/work=.
TARGET_CXXFLAGS := $(TARGET_CFLAGS)
TARGET_LDFLAGS := -Wl,-z,relro,-z,now
TARGET_DIR := {rel(target)}
MUOS_GAMBATTE_PKGDIR := /port/buildroot-libretro/package/muos-gambatte
INSTALL := install
MAKE := make -j4
sep = $(newline)
define newline


endef
generic-package =
include /port/buildroot-libretro/package/muos-gambatte/muos-gambatte.mk
.PHONY: all install-only
all: {rel(build)}/.c75-built
{rel(build)}/.c75-built:
\t$(MUOS_GAMBATTE_BUILD_CMDS)
\t$(MUOS_GAMBATTE_INSTALL_TARGET_CMDS)
install-only: {rel(build)}/.c75-install
{rel(build)}/.c75-install:
\t$(MUOS_GAMBATTE_INSTALL_TARGET_CMDS)
''')
run('recipe',f'make -f {rel(harness)} all\n',timeout=240)
core=target/'opt/muos/share/core/gambatte_libretro.so';core_sha=sha(core)
assert core.stat().st_mode&0o777==0o644
assert all(sha(build/n)==h for n,h in source_files.items())
for n,h in sums(target/'usr/share/muos-gambatte/payload.sha256').items():assert sha(target/n.lstrip('/'))==h
root_stage=work/'provider-image/image.izief28e';base=root_stage/'target'
before=json.loads((root_stage/'expected-tree.json').read_text());assert inventory(base)==before
composition=stage/'composition';shutil.copytree(base,composition,symlinks=True)
run('composition',f'make -f {rel(harness)} install-only TARGET_DIR={rel(composition)}\n')
after=inventory(composition)
assert all(after[n]==v for n,v in before.items())
added={n:v for n,v in after.items() if n not in before}
assert sum(v['type']=='file' for v in added.values())==9
validate(composition)
metadata=run('ABI',f'''sdk=/work/graphics-config/output/host
"$sdk/bin/aarch64-buildroot-linux-gnu-readelf" -h -l -d --wide {rel(core)}
"$sdk/bin/aarch64-buildroot-linux-gnu-gcc" -O2 -mcpu=cortex-a35 -I{rel(build)}/libgambatte/libretro-common/include /port/diagnostics/phase4-gb-identity-check.c -ldl -o {rel(stage)}/identity-check
qemu-aarch64 -cpu cortex-a35 -L {rel(composition)} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={rel(composition)}/usr/lib:{rel(composition)}/lib {rel(stage)}/identity-check {rel(composition)}/opt/muos/share/core/gambatte_libretro.so
"$sdk/bin/aarch64-buildroot-linux-gnu-nm" -D --defined-only {rel(core)} > {rel(stage)}/exports.txt
"$sdk/bin/aarch64-buildroot-linux-gnu-nm" -D --defined-only {rel(old_core)} > {rel(stage)}/prior-exports.txt
''')
assert 'C48_GB_IDENTITY_OK' in metadata and 'Machine:                           AArch64' in metadata
assert 'GNU_RELRO' in metadata and '(BIND_NOW)' in metadata
exports=lambda n:{line.split()[-1] for line in (stage/n).read_text().splitlines()}
assert exports('exports.txt')==exports('prior-exports.txt')
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
assert sha(archive)==archive_hash and sha(old_core)==old['core_sha256'] and inventory(base)==before
(stage/'composition-added.json').write_text(json.dumps(added,indent=2,sort_keys=True)+'\n')
(stage/'expected-tree.json').write_text(json.dumps(after,indent=2,sort_keys=True)+'\n')
sources=[Path(__file__),repo/'port/diagnostics/phase4-gb-identity-check.c',*sorted((repo/'port/buildroot-libretro').rglob('*'))]
sources=[p for p in sources if p.is_file()]
report={'passed':True,'experiment':'C75_BUILDROOT_GAMBATTE_CORE_PACKAGE','core_sha256':core_sha,
 'prior_qualified_core_sha256':old['core_sha256'],'byte_identical_to_C49_C73_core':core_sha==old['core_sha256'],
 'upstream_revision':commit,'source_archive_sha256':archive_hash,'source_files':len(source_files),
 'real_Buildroot_download_extract_Kconfig_legal_info':True,'actual_recipe_macros_built_with_existing_SDK':True,
 'full_Buildroot_dependency_rebuild':False,'default_off':True,'i386_refused':True,
 'RGB565':True,'network_enabled':False,'host_git_revision_injected':False,
 'runtime_path':'/opt/muos/share/core/gambatte_libretro.so','ABI_AArch64_RELRO_NOW_API1_memory_content':True,
 'exports_match_qualified_core':True,'ROM_loaded':False,'ROM_copied':False,'device_contacted':False,'device_written':False,
 'combined_license_review_pending':True,'Buildroot_redistribution_disabled':True,
 'existing_C69_items_preserved':len(before),'composition_items':len(after),
 'files_added':9,'directories_added':sum(v['type']=='directory' for v in added.values()),
 'C07_factory_counter_zero_default_off_preserved':True,'SDK_baseline_preserved':True,
 'parent_proofs_sha256':parents,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-build').write_text(str(stage)+'\n')
print('C75 Gambatte package/composition passed offline:',stage)
print('Core SHA256:',core_sha,'same qualified bytes:',report['byte_identical_to_C49_C73_core'])
