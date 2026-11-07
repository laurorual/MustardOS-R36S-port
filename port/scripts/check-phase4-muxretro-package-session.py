#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C61 receipt/host substitution refusals and eager loader with runtime UI lib."""
from pathlib import Path
import ast,copy,json,subprocess,tempfile
from phase4_candidate import sha,sums
from phase4_muxretro_package_session import bind_package_host
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro-package-session';area.mkdir(exist_ok=True)
for name in ['gameboy-installed-store','muxretro-package']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,n
renderer=repo/'port/scripts/prepare-phase4-muxretro-package-session.py'
runner=repo/'port/scripts/run-phase4-muxretro-package-session.py'
analyzer=repo/'port/scripts/analyze-phase4-muxretro-package-session.py'
before={p:p.read_bytes() for p in [runner,analyzer]}
subprocess.run(['python3',str(renderer)],check=True,capture_output=True)
for p,data in before.items():assert p.read_bytes()==data;ast.parse(p.read_text())
text=runner.read_text()
assert text.index('installed_origin=bind_installed_source')<text.index("files['muxretro']=new_host")
assert text.index("assert boot_evidence[0]==source_session_report['kernel_boot_id']")<text.index("directory=remote('allocate'")
assert "'save-store':" not in text and "old_host_checks_historical_only=True" in text
source=work/'gb-installed-session/load.uzlnx4ac'
prior=json.loads((source/'analysis.json').read_text())
clean={k:('private' if k in {'private_identity','ROM_sha256','kernel_boot_id'} else v) for k,v in prior.items()}
proof=repo/'dist/phase4/gameboy-installed-store'
assert clean==json.loads((proof/'load/analysis.json').read_text())
assert (source/'physical-observation.json').read_bytes()==(proof/'load/physical-observation.json').read_bytes()
package=Path((work/'muxretro-package/latest-build').read_text().strip())
report=json.loads((package/'analysis.json').read_text())
assert (package/'analysis.json').read_bytes()==(repo/'dist/phase4/muxretro-package/analysis.json').read_bytes()
provenance=json.loads((package/'target/usr/share/muos-muxretro/provenance.json').read_text())
binary=package/'target/opt/muos/frontend/muxretro';digest=sha(binary)
keys=['host_binary_sha256','core_sha256','ROM_sha256','runner_sha256','worker_sha256','library_sha256',
      'state_inspector_sha256','save_store_binary_sha256','cycle_sha256']
assets={k:prior[k] for k in keys}
def invoke(p=prior,r=report,m=provenance,a=None):
 if a is None:a=dict(boot=prior['boot_sequence'],uuid=prior['kernel_boot_id'],identity=prior['private_identity'],binary=digest,assets=assets)
 return bind_package_host(p,r,m,a['boot'],a['uuid'],a['identity'],a['assets'],a['binary'])
assert invoke()==digest;cases=['pinned-C59-same-boot-new-C60-host']
mutations=[
 ('different-boot',lambda p,r,m,a:a.update(boot=a['boot']+1)),
 ('bool-boot',lambda p,r,m,a:a.update(boot=True)),
 ('different-UUID',lambda p,r,m,a:a.update(uuid='different')),
 ('wrong-identity',lambda p,r,m,a:a.update(identity='wrong')),
 ('wrong-payload-hash',lambda p,r,m,a:a.update(binary='00'*32)),
 ('old-ELF',lambda p,r,m,a:(r.update(binary_sha256=assets['host_binary_sha256']),a.update(binary=assets['host_binary_sha256']))),
 ('wrong-parent-experiment',lambda p,r,m,a:p.update(experiment='C54')),
 ('prior-writer',lambda p,r,m,a:p.update(mode='save')),
 ('prior-failed-outcome',lambda p,r,m,a:p.update(outcome='failed')),
 ('store-ELF-in-RAM',lambda p,r,m,a:p.update(store_ELF_transferred=True)),
 ('preferences-written',lambda p,r,m,a:p.update(preferences_persisted=True)),
 ('different-host-ancestry',lambda p,r,m,a:m.update(C50_binary_sha256='00'*32)),
 ('sources-mismatch',lambda p,r,m,a:m.update(all_prepared_frontend_source_matches_C50=False)),
 ('private-data-packaged',lambda p,r,m,a:m.update(cores_ROMs_saves_or_platform_binaries_packaged=True)),
 ('platform-payload-drift',lambda p,r,m,a:r['private_composition'].update(foundation_files=96)),
 ('base-tree-drift',lambda p,r,m,a:r.update(C56_existing_items_preserved=1)),
 ('new-payload-drift',lambda p,r,m,a:r.update(composition_added_files=14)),
]
for key in ['passed','cleanup_passed','RAM_removed','global_mountinfo_unchanged','root_ro','store_matches_previous_boot','installed_CLI_used']:
 mutations.append(('prior-'+key,lambda p,r,m,a,k=key:p.update({k:False})))
for key in ['passed','default_off','private_SDK_required','real_Kconfig_rsync_legal_info','source_only_legal_archive_verified',
            'frontend_source_matches_C50','clean_source_build','missing_and_changed_SDK_refused_before_compiler',
            'C07_boot_contract_preserved','private_composition_loader_passed','SDK_config_unchanged']:
 mutations.append(('package-'+key,lambda p,r,m,a,k=key:r.update({k:False})))
for key in ['full_frontend_library_provider_integrated','platform_libraries_installed','full_Buildroot_rebuild',
            'device_accessed','new_native_runtime_qualified','new_image_built','C50_binary_byte_identical']:
 mutations.append(('package-'+key,lambda p,r,m,a,k=key:r.update({k:True})))
for key in keys:
 mutations.append(('asset-'+key,lambda p,r,m,a,k=key:a['assets'].update({k:'00'*32})))
for label,mutate in mutations:
 p,r,m=copy.deepcopy(prior),copy.deepcopy(report),copy.deepcopy(provenance)
 a=dict(boot=prior['boot_sequence'],uuid=prior['kernel_boot_id'],identity=prior['private_identity'],binary=digest,assets=copy.deepcopy(assets))
 mutate(p,r,m,a)
 try:invoke(p,r,m,a)
 except AssertionError:pass
 else:raise AssertionError(label)
 cases.append(label)
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
library=Path((work/'app-selection/latest-build').read_text().strip())/'frontend-bin/lib/libmuxmod.so'
assert sha(library)==prior['library_sha256']
rel=lambda p:'/work/'+str(p.relative_to(work))
code=f'''root=/work/rootfs-candidate/composition.w59vz7vo/target
for op in --version --help;do
 qemu-aarch64 -cpu cortex-a35 -L / -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "{rel(library.parent)}:$root/opt/muos/frontend/lib:$root/lib:$root/usr/lib" {rel(binary)} "$op"
done
'''
(stage/'loader.sh').write_text(code)
container=(work/'rootfs-container.iid').read_text().strip()
r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',container,'sh','-eu','-c',code],capture_output=True,text=True,timeout=60)
for ext,data in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('loader.'+ext)).write_text(data)
assert r.returncode==0,(r.stdout,r.stderr)
screen=repo/'port/device/rk-r35s-p0/muxretro-package-session/stopped-screen.sh'
assert screen.read_text()==(repo/'port/device/rk-r35s-p0/gb-installed-session/stopped-screen.sh').read_text().replace('C59','C61')
subprocess.run(['sh','-n',str(screen)],check=True)
sources=[Path(__file__),renderer,runner,analyzer,repo/'port/scripts/phase4_muxretro_package_session.py',screen]
receipt={'passed':True,'experiment':'C61_NEW_HOST_BINDING_CHECKS','case_count':len(cases),'cases':cases,
 'C59_exact_boot_required':True,'C60_payload_binary_sha256':digest,'runtime_libmuxmod_override_sha256':sha(library),
 'runtime_override_eager_QEMU_loader_passed':True,'device_accessed':False,'private_ROM_used':False,
 'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(receipt,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C61 binding/delta/runtime-loader checks passed:',len(cases),stage)
