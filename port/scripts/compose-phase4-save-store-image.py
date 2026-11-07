#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C56: serialize the pinned C55 tree into a private ext4, entirely offline."""
from pathlib import Path
import argparse,importlib.util,json,re,shutil,subprocess,tempfile
from phase4_candidate import inventory,sha,sums,validate

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-composition',type=Path,required=True)
args=parser.parse_args();source=args.source_composition.resolve()
area=work/'save-store-image';area.mkdir(exist_ok=True)
assert source.is_relative_to(work/'save-store-package')
baseline=work/'network-tools/baseline.config'
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
proof=repo/'dist/phase4/save-store-package'
for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,n
assert (source/'analysis.json').read_bytes()==(proof/'composition/analysis.json').read_bytes()
parent=json.loads((source/'analysis.json').read_text());assert parent['passed']
for n,h in parent['source_sha256'].items():assert sha(repo/n)==h,n
base=work/'rootfs-candidate/composition.w59vz7vo'
assert sha(base/'analysis.json')==parent['base_C38_analysis_sha256']
base_image=base/'images/rootfs.ext4'
assert sha(base_image)==parent['base_C38_image_sha256']
original=json.loads((base/'expected-tree.json').read_text())
added=parent['added'];assert not set(original)&set(added)
assert len(added)==7 and sum(v['type']=='file' for v in added.values())==4
assert all(re.fullmatch(r'usr/(libexec|share)/[A-Za-z0-9_./-]+',n) and '..' not in n for n in added)
expected={**original,**added}
planned=source/'target';assert inventory(planned)==expected
assert json.loads((source/'expected-tree.json').read_text())==expected
assert validate(planned)['foundation_files']==97
store_manifest='usr/libexec/muos-save-store/payload.sha256'
for n,h in sums(planned/store_manifest).items():assert sha(planned/n.lstrip('/'))==h
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
# seven added inodes and the root directly, in addition to full file readback.
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
actual=inventory(root);assert actual==expected,'Full image readback differs from C55 tree'
assert root.stat().st_mode&0o777==0o755
validated=validate(root);assert validated['foundation_files']==97
for n,h in sums(root/store_manifest).items():assert sha(root/n.lstrip('/'))==h
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
# All older ELFs/dependencies remain byte-identical; do not replay the 172
# approved C38 loader checks or the native C52 transaction laboratory.
text=run('new-CLI-loader',f'''root={rel(root)}
qemu-aarch64 -cpu cortex-a35 -L / -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$root/lib:$root/usr/lib" --list "$root/usr/libexec/muos-save-store/muos-save-store"
rc=0
qemu-aarch64 -cpu cortex-a35 -L / -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$root/lib:$root/usr/lib" "$root/usr/libexec/muos-save-store/muos-save-store" || rc=$?
[ "$rc" = 64 ]
echo C56_PASS_readback_A35_loader_and_CLI_refusal
''')
assert sha(image)==image_sha and sha(base_image)==parent['base_C38_image_sha256']
assert inventory(planned)==expected and inventory(base/'target')==original
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
sources=[Path(__file__),repo/'port/scripts/phase4_candidate.py',repo/'port/scripts/verify-phase4-rootfs.py',repo/'port/scripts/verify-phase4-modules.py',repo/'port/device/rk-r35s-p0/candidate/boot-checks.sh']
result={**validated,'experiment':'C56_PRIVATE_SAVE_STORE_EXT4','private_only':True,'redistribution_approved':False,
 'source_composition':str(source),'C55_analysis_sha256':sha(source/'analysis.json'),'C55_proof_sha256':sha(proof/'SHA256SUMS'),
 'base_C38_image_sha256':parent['base_C38_image_sha256'],'image_sha256':image_sha,'image_bytes':image.stat().st_size,
 'added_files':4,'added_directories':3,'base_C38_files_changed':0,'readback_items':len(actual),
 'full_readback_inventory_matched':True,'new_inodes_and_root_owned_by_root':True,'root_inode_mode':'0755','fsck_exit':0,
 'ext4_features_unchanged':True,'boot_contract_checked_before_and_after_image':True,'factory_boot_counter':0,
 'store_payload_verified_after_readback':True,'C52_binary_byte_identical':parent['C52_binary_byte_identical'],
 'new_dynamic_ELF_loader_checks':1,'prior_C38_dynamic_ELF_loader_checks_reused':172,
 'candidate_boot_tested':False,'device_contacted':False,'device_written':False,'original_32GB_or_Deck_accessed':False,
 'kernel_DTB_bootloader_partition_changed':False,'full_Buildroot_rebuild':False,'SDK_config_unchanged':True,
 'image_bit_reproducibility_qualified':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');(area/'latest-image').write_text(str(stage)+'\n')
print('C56 private ext4/readback/fsck/boot-contract passed:',stage)
print('Image SHA256:',image_sha)
