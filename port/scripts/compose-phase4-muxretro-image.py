#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C64: serialize the qualified C60 host over C56, without contacting hardware."""
from pathlib import Path
import argparse,importlib.util,json,re,shutil,subprocess,tempfile
from phase4_candidate import inventory,sha,sums,validate

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-build',type=Path,required=True)
args=parser.parse_args();source=args.source_build.resolve()
area=work/'muxretro-image';area.mkdir(exist_ok=True)
assert source.is_relative_to(work/'muxretro-package')
baseline=work/'network-tools/baseline.config'
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
parents={}
for name in ['save-store-image','muxretro-package','muxretro-installed','installed-host-session']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,(name,n)
 parents[name]=sha(proof/'SHA256SUMS')
proof=repo/'dist/phase4/muxretro-package'
assert (source/'analysis.json').read_bytes()==(proof/'analysis.json').read_bytes()
parent=json.loads((source/'analysis.json').read_text());assert parent['passed']
for n,h in parent['source_sha256'].items():assert sha(repo/n)==h,n
base=work/'save-store-image/image.nlnmgzzb'
assert (base/'analysis.json').read_bytes()==(repo/'dist/phase4/save-store-image/analysis.json').read_bytes()
assert sha(base/'analysis.json')==parent['C56_analysis_sha256']
base_report=json.loads((base/'analysis.json').read_text());assert base_report['passed']
for n,h in base_report['source_sha256'].items():assert sha(repo/n)==h,n
base_image=base/'images/rootfs.ext4'
assert base_image.is_file() and not base_image.is_symlink()
assert sha(base_image)==base_report['image_sha256']
original=json.loads((base/'expected-tree.json').read_text());assert len(original)==3330
assert inventory(base/'target')==original
added=json.loads((proof/'composition-added.json').read_text())
assert (source/'composition-added.json').read_bytes()==(proof/'composition-added.json').read_bytes()
assert not set(original)&set(added) and len(added)==26
files={n:v for n,v in added.items() if v['type']=='file'}
assert len(files)==13 and sum(v['type']=='directory' for v in added.values())==13
assert all(re.fullmatch(r'(opt/muos/frontend/muxretro|usr/share/(licenses/)?muos-muxretro(/[A-Za-z0-9_.-]+)*)',n) and '..' not in Path(n).parts for n in added)
plan=json.loads((repo/'dist/phase4/muxretro-installed/plan.json').read_text())
assert plan['C60_proof_sha256']==parents['muxretro-package']
assert len(plan['files'])==13 and {r['path'] for r in plan['files']}==set(files)
for r in plan['files']:
 assert files[r['path']]=={'type':'file','mode':r['mode'],'sha256':r['sha256']}
qualified=json.loads((repo/'dist/phase4/installed-host-session/analysis.json').read_text())
assert qualified['passed'] and qualified['installed_host_GB_qualified']
assert qualified['physical_image_input_audio_restore_and_return_confirmed']
assert qualified['parent_proofs_sha256']['muxretro-package']==parents['muxretro-package']
assert qualified['parent_proofs_sha256']['muxretro-installed']==parents['muxretro-installed']
assert qualified['new_host_binary_sha256']==parent['binary_sha256']==files['opt/muos/frontend/muxretro']['sha256']
expected={**original,**added};assert len(expected)==3356
planned=source/'composition';assert inventory(planned)==expected
assert validate(planned)['foundation_files']==97
store_manifest='usr/libexec/muos-save-store/payload.sha256'
host_manifest='usr/share/muos-muxretro/payload.sha256'
def check_manifests(tree):
 for name in [store_manifest,host_manifest]:
  for n,h in sums(tree/name).items():assert sha(tree/n.lstrip('/'))==h,(name,n)
 for n,h in sums(tree/'usr/share/muos-muxretro/platform.sha256').items():
  assert sha(tree/'opt/muos/frontend'/n)==h,n
 assert sha(tree/'opt/muos/frontend/muxretro')==parent['binary_sha256']
check_manifests(planned)
stage=Path(tempfile.mkdtemp(prefix='image.',dir=area));(area/'latest-attempt').write_text(str(stage)+'\n')
rel=lambda p:'/work/'+str(p.relative_to(work))
container=(work/'rootfs-container.iid').read_text().strip()
def run(label,code,timeout=60):
 (stage/(label+'.sh')).write_text(code)
 cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
      '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',container,'sh','-eu','-c',code]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
 for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+n)).write_text(v)
 assert r.returncode==0,(stage,label,r.stderr[-2000:],r.stdout[-1000:])
 return r.stdout
boot_script='usr/libexec/muos-candidate-boot-checks'
run('planned-boot-contract',f'. {rel(planned/boot_script)}\ncandidate_boot_check {rel(planned)}\n')
images=stage/'images';images.mkdir();image=images/'rootfs.ext4'
# Only a newly created private regular file is ever opened by debugfs -w.
assert not image.exists();shutil.copyfile(base_image,image)
assert image.is_file() and not image.is_symlink() and image.stat().st_nlink==1
commands=[]
for name,record in sorted(added.items(),key=lambda v:(len(Path(v[0]).parts),v[0])):
 if record['type']=='directory':
  commands.extend([f'mkdir /{name}',f'set_inode_field /{name} mode 040{record["mode"]:03o}',f'set_inode_field /{name} uid 0',f'set_inode_field /{name} gid 0'])
for name,record in sorted(added.items()):
 if record['type']=='file':
  commands.extend([f'write {rel(planned/name)} /{name}',f'set_inode_field /{name} mode 0100{record["mode"]:03o}',f'set_inode_field /{name} uid 0',f'set_inode_field /{name} gid 0'])
 else:assert record['type']=='directory'
(stage/'debugfs.commands').write_text('\n'.join(commands)+'\n')
run('write-image',f'debugfs -w -f {rel(stage/"debugfs.commands")} {rel(image)}\n')
image_sha=sha(image)
run('fsck',f'e2fsck -fn {rel(image)}\n')
assert sha(image)==image_sha,'Read-only fsck changed image'
# Owner metadata cannot be inferred from an unprivileged rdump. Inspect all
# twenty-six added inodes and the root directly, in addition to full file readback.
names=['/',*('/'+n for n in sorted(added))]
(stage/'inode.commands').write_text(''.join('stat '+n+'\n' for n in names)+'stats\n')
text=run('inodes',f'debugfs -f {rel(stage/"inode.commands")} {rel(image)}\n')
for name in names:
 match=re.search(r'debugfs: stat '+re.escape(name)+r'\n(.*?)(?=debugfs: |\Z)',text,re.S);assert match,name
 assert re.search(r'User:\s+0\s+Group:\s+0',match[1]),name
 mode=0o755 if name=='/' else added[name.lstrip('/')]['mode']
 assert re.search(r'Mode:\s+0'+f'{mode:o}'+r'\b',match[1]),name
root=stage/'target';root.mkdir(mode=0o755)
run('readback',f'/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / {rel(root)}" {rel(image)}\n')
actual=inventory(root);assert actual==expected,'Full image readback differs from C60 composition'
assert root.stat().st_mode&0o777==0o755
validated=validate(root);assert validated['foundation_files']==97
check_manifests(root)
(stage/'expected-tree.json').write_text(json.dumps(expected,sort_keys=True,indent=2)+'\n')
(stage/'foundation.sha256').write_bytes((root/'usr/libexec/muos-session/prerequisites.sha256').read_bytes())
(stage/'.config').write_bytes(baseline.read_bytes())
spec=importlib.util.spec_from_file_location('rootfs_audit',repo/'port/scripts/verify-phase4-rootfs.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
static=audit.verify(stage);prior_static=json.loads((base/'static-audit.json').read_text())
for key in ['elf_aarch64_count','userspace_aarch64_count']:assert static[key]==prior_static[key]+1
for key in ['kernel_module_aarch64_et_rel_count','module_release','interpreters','glibc_linux_abi_note']:assert static[key]==prior_static[key]
for key in ['label','bytes','compat','incompat','ro_compat']:assert static['ext4'][key]==prior_static['ext4'][key]
assert static['ext4']['sha256']==image_sha
(stage/'static-audit.json').write_text(json.dumps(static,indent=2)+'\n')
run('readback-boot-contract',f'. {rel(root/boot_script)}\ncandidate_boot_check {rel(root)}\n')
# The full inventory proves every ELF and dependency matches the already
# qualified composition. Reuse C38(172), C56 store(1) and C60 host(1) loader
# receipts; no dynamic binary, core or init is executed for serialization.
assert sha(image)==image_sha and sha(base_image)==base_report['image_sha256']
assert inventory(planned)==expected and inventory(base/'target')==original
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
sources=[Path(__file__),repo/'port/scripts/phase4_candidate.py',repo/'port/scripts/verify-phase4-rootfs.py',repo/'port/scripts/verify-phase4-modules.py',repo/'port/device/rk-r35s-p0/candidate/boot-checks.sh']
result={**validated,'experiment':'C64_PRIVATE_MUXRETRO_EXT4','private_only':True,'redistribution_approved':False,
 'source_build':str(source),'source_composition':str(planned),'C60_analysis_sha256':sha(source/'analysis.json'),
 'parent_proofs_sha256':parents,'base_C56_image_sha256':base_report['image_sha256'],
 'image_sha256':image_sha,'image_bytes':image.stat().st_size,'added_files':13,'added_directories':13,
 'base_C56_items_changed':0,'base_C56_items_preserved':len(original),'readback_items':len(actual),
 'full_readback_inventory_matched':True,'new_inodes_and_root_owned_by_root':True,'root_inode_mode':'0755',
 'fsck_exit':0,'ext4_features_unchanged':True,'boot_contract_checked_before_and_after_image':True,
 'factory_boot_counter':0,'store_and_host_payloads_verified_after_readback':True,
 'host_sha256':parent['binary_sha256'],'C62_installed_bytes_matched':True,'C63_native_host_evidence_reused':True,
 'new_dynamic_ELF_loader_checks':0,'C38_loader_checks_reused':172,'C56_store_loader_checks_reused':1,
 'C60_host_loader_checks_reused':1,'C63_callers_cores_ROMs_saves_included':False,
 'candidate_boot_tested':False,'device_contacted':False,'device_written':False,
 'original_32GB_or_Deck_accessed':False,'kernel_DTB_bootloader_partition_changed':False,
 'full_Buildroot_rebuild':False,'SDK_config_unchanged':True,'image_bit_reproducibility_qualified':False,
 'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');(area/'latest-image').write_text(str(stage)+'\n')
print('C64 private ext4/readback/fsck/boot-contract passed:',stage)
print('Image SHA256:',image_sha)
