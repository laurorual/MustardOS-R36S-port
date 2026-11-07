#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the C11 recipe in an isolated harness and create its native test package."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'runtime-session';area.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=work/'network-tools/baseline.config'
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
checks=Path((area/'latest-checks').read_text().strip());assert json.loads((checks/'report.json').read_text())['passed']
profile_checks=Path((work/'runtime-profile/latest-checks').read_text().strip());profile=profile_checks/'recipe-target/usr/share/muos-r35s-profile'
approved=repo/'dist/phase4/runtime-profile-session';digests={n:h for h,n in (r.split('  ',1) for r in (approved/'SHA256SUMS').read_text().splitlines())}
assert sha(approved/'analysis.json')==digests['analysis.json'] and json.loads((approved/'analysis.json').read_text())['passed']
assert sha(profile/'manifest.json')==json.loads((approved/'manifest.json').read_text())['profile_manifest_sha256']
stage=Path(tempfile.mkdtemp(prefix='service.',dir=area));source=stage/'source';service=source/'service';service.mkdir(parents=True)
for name in ['service.sh','worker.sh','chain.sh','runtime.sh','control-functions.sh','preferences.sh']:shutil.copyfile(repo/'port/device/rk-r35s-p0/session'/name,service/name)
shutil.copyfile(repo/'port/device/rk-r35s-p0/preferences/data-functions.sh',service/'data-functions.sh')
shutil.copyfile(repo/'port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh',service/'card-guard.sh')
for name in ['muos-session.default','S98muos-session']:shutil.copyfile(repo/'port/device/rk-r35s-p0/session'/name,source/name)

for n,p in [('muos-run-bounded','port/utils/muos-run-bounded.c'),('muos-rng-ready','port/utils/muos-rng-ready.c'),('muos-root-writers','port/diagnostics/root-writers.c'),('muos-drm-mode-probe','port/diagnostics/drm-mode-probe.c'),('muos-preferences','port/utils/muos-preferences.c')]:shutil.copyfile(repo/p,source/(n+'.c'))
shutil.copyfile(repo/'port/utils/muos-mount-namespace.c',source/'muos-mount-namespace.c');shutil.copyfile(repo/'port/LICENSE',source/'LICENSE')
(service/'profile-source.sha256').write_text(''.join(sha(p)+'  '+str(p.relative_to(profile))+'\n' for p in sorted(profile.rglob('*')) if p.is_file()))
for p in service.iterdir():p.chmod(0o755 if p.name.endswith('.sh') else 0o644)
# Exercise the recipe's actual compilation and installation macros without
# reconfiguring/rebuilding the shared SDK or unrelated dependency packages.
source_copy=stage/'recipe-source';shutil.copytree(source,source_copy);target=stage/'recipe-target';target.mkdir()
rel=lambda p:'/work/'+str(p.relative_to(work))
harness=stage/'recipe.mk';harness.write_text('TARGET_DIR := '+rel(target)+'\nTARGET_CC := /work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc\nTARGET_CFLAGS := -O2 -g0 -mcpu=cortex-a35\nTARGET_LDFLAGS :=\nSTAGING_DIR := /work/graphics-config/output/host/aarch64-buildroot-linux-gnu/sysroot\nINSTALL := install\ngeneric-package =\ninclude /port/buildroot/package/muos-r35s-session/muos-r35s-session.mk\n'+rel(source_copy/'.installed')+':\n\t$(MUOS_R35S_SESSION_BUILD_CMDS)\n\t$(MUOS_R35S_SESSION_INSTALL_TARGET_CMDS)\n\t$(MUOS_R35S_SESSION_INSTALL_INIT_SYSV)\n\ttouch $@\n')
with harness.open('a') as out: out.write('\n'+rel(source_copy/'.reinstalled')+':\n\t$(MUOS_R35S_SESSION_INSTALL_TARGET_CMDS)\n\t$(MUOS_R35S_SESSION_INSTALL_INIT_SYSV)\n')
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip()]
r=subprocess.run(container+['make','-f',rel(harness)],capture_output=True,text=True,timeout=60);(stage/'recipe.stdout').write_text(r.stdout);(stage/'recipe.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
payload_manifest=target/'usr/libexec/muos-session/payload.sha256'
payload_hash=sha(payload_manifest)
r=subprocess.run(container+['make','-f',rel(harness),rel(source_copy/'.reinstalled')],capture_output=True,text=True,timeout=30);(stage/'reinstall.stdout').write_text(r.stdout);(stage/'reinstall.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
assert sha(payload_manifest)==payload_hash
payload_entries={}
for line in payload_manifest.read_text().splitlines():
 digest,name=line.split('  ',1);relative=Path(name)
 assert not relative.is_absolute() and '..' not in relative.parts and name not in payload_entries
 assert sha(payload_manifest.parent/relative)==digest
 payload_entries[name]=digest
assert {str(Path(n)) for n in payload_entries}=={str(p.relative_to(payload_manifest.parent)) for p in payload_manifest.parent.rglob('*') if p.is_file() and p!=payload_manifest}
shutil.copyfile(source_copy/'mount-namespace',source/'mount-namespace')
root=work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted'
code='set -eu\ncd '+rel(stage)+'\nreadelf -h -l -d source/mount-namespace > namespace-elf.txt\nqemu-aarch64 -cpu cortex-a35 -L '+rel(root)+' -E LD_BIND_NOW=1 '+rel(root/'lib/ld-linux-aarch64.so.1')+' --inhibit-cache --library-path '+rel(root/'lib')+':'+rel(root/'usr/lib')+' --list '+rel(source/'mount-namespace')+' > namespace-loader.txt\n'
for p in [*service.glob('*.sh'),source/'S98muos-session']:
 code+='qemu-aarch64 -cpu cortex-a35 -L '+rel(root)+' '+rel(root/'bin/busybox')+' sh -n '+rel(p)+'\n'

for n in ['muos-run-bounded','muos-rng-ready','muos-root-writers','muos-drm-mode-probe','muos-preferences']:
 code+='qemu-aarch64 -cpu cortex-a35 -L '+rel(root)+' -E LD_BIND_NOW=1 '+rel(root/'lib/ld-linux-aarch64.so.1')+' --inhibit-cache --library-path '+rel(root/'lib')+':'+rel(root/'usr/lib')+' --list '+rel(target/'usr/libexec/muos-session/bin'/n)+' > '+n+'-loader.txt\n'
r=subprocess.run(container+['sh','-eu','-c',code],capture_output=True,text=True,timeout=45);(stage/'audit.stdout').write_text(r.stdout);(stage/'audit.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
assert 'Machine:                           AArch64' in (stage/'namespace-elf.txt').read_text()
# No dependency on diagnostic C06/C09 code, network lifecycle or saved-seed loader.
for p in service.glob('*.sh'):
 text=p.read_text();assert not any(n in text for n in ['muos-c06','c06_','c09_','S05muos','S10udev','seedrng','muos-c07-network','/usr/libexec/muos-boot'])
assert (target/'etc/default/muos-session').read_text().splitlines()[1]=='enabled=0'
assert 'preferences_enabled=0' in (target/'etc/default/muos-session').read_text().splitlines()
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
pkg=stage/'package';shutil.copytree(target/'usr/libexec/muos-session',pkg);shutil.copytree(profile,pkg/'profile')
shutil.copyfile(repo/'build/phase4/runtime-profile/session.rxvlawrp/package/prerequisites.sha256',pkg/'prerequisites.sha256')
(pkg/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(pkg))+'\n' for p in sorted(pkg.rglob('*')) if p.is_file()))
with tarfile.open(stage/'deployment.tar','w') as t:
 for p in pkg.iterdir():t.add(p,arcname=p.name)
manifest={'experiment':'MUOS-R35S-SESSION-P4-C11','host_passed':True,'hardware_tested':False,'checks':json.loads((checks/'report.json').read_text()),'profile_manifest_sha256':sha(profile/'manifest.json'),'recipe_macro_compile_install_passed':True,'full_buildroot_dependency_build_performed':False,'runtime_boot_package_dependency':False,'payload_manifest_sha256':payload_hash,'payload_entries':payload_entries,'payload_manifest_reinstall_stable':True,'SDK_baseline_preserved':True,'preferences_default_enabled':False,'historical_native_foundation_manifest_only':True,'diagnostic_C06_C09_dependency':False,'service_default_enabled':False,'lease_seconds_default':180,'namespace_sha256':sha(source/'mount-namespace'),'deployment_sha256':sha(stage/'deployment.tar'),'owned_support_tools':['muos-run-bounded','muos-rng-ready','muos-root-writers','muos-drm-mode-probe','muos-preferences'],'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/scripts/check-phase4-session-service.py',repo/'port/buildroot/package/muos-r35s-session/muos-r35s-session.mk',repo/'port/buildroot/package/muos-r35s-session/Config.in',repo/'port/device/rk-r35s-p0/phase4-session.fragment',repo/'port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh',repo/'port/utils/muos-mount-namespace.c',repo/'port/utils/muos-run-bounded.c',repo/'port/utils/muos-rng-ready.c',repo/'port/utils/muos-preferences.c',repo/'port/device/rk-r35s-p0/preferences/data-functions.sh',repo/'port/diagnostics/root-writers.c',repo/'port/diagnostics/drm-mode-probe.c',repo/'port/LICENSE',*sorted((repo/'port/device/rk-r35s-p0/session').iterdir())]}}
(stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
pending=area/'source.pending';pending.unlink(missing_ok=True);pending.symlink_to(source.relative_to(area),target_is_directory=True);pending.replace(area/'source')
(area/'latest-service').write_text(str(stage)+'\n');print('C11 independent service/recipe/ABI/shell package prepared:',stage)
