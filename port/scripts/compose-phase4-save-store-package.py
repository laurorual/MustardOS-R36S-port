#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C55 additive private tree: real install macro, unchanged C38 foundation."""
from pathlib import Path
import json,re,shutil,subprocess,tempfile
from phase4_candidate import inventory,sha,sums,validate
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'save-store-package'
build=Path((area/'latest-build').read_text().strip());report=json.loads((build/'analysis.json').read_text());assert report['passed']
for n,h in report['source_sha256'].items():assert sha(repo/n)==h,n
base=work/'rootfs-candidate/composition.w59vz7vo';prior=json.loads((base/'analysis.json').read_text());assert prior['passed']
assert sha(base/'images/rootfs.ext4')==prior['image_sha256']
assert validate(base/'target')['foundation_files']==97
original=inventory(base/'target');assert original==json.loads((base/'expected-tree.json').read_text())
# Keep the legacy composer strict about the exact menu extension, too.
old=repo/'dist/phase4/wifi-only-policy/port-source/Config.in'
suffix=''.join('source "$BR2_EXTERNAL_MUOS_R35S_PATH/package/'+n+'/Config.in"\n' for n in ['muos-r35s-launcher-once','muos-save-store'])
assert (repo/'port/buildroot/Config.in').read_bytes()==old.read_bytes()+suffix.encode()
for config in (repo/'port').rglob('*defconfig'):
 if config.is_file():assert 'BR2_PACKAGE_MUOS_SAVE_STORE=y' not in config.read_text(),config
stage=Path(tempfile.mkdtemp(prefix='composition.',dir=area));(area/'latest-composition-attempt').write_text(str(stage)+'\n')
root=stage/'target';shutil.copytree(base/'target',root,symlinks=True)
rel=lambda p:'/work/'+str(p.relative_to(work))
match=re.fullmatch(r'MUOS_SAVE_STORE_BUILDDIR=(/work/[^\n]+)\n',(build/'build-vars.txt').read_text());assert match
harness=stage/'install.mk';harness.write_text(f'''TARGET_DIR := {rel(root)}
INSTALL := install
generic-package =
include /port/buildroot/package/muos-save-store/muos-save-store.mk
.PHONY: all
all: {match[1].rstrip('/')}/.c55-install
{match[1].rstrip('/')}/.c55-install:
\t$(MUOS_SAVE_STORE_INSTALL_TARGET_CMDS)
''')
code=f'''make -f {rel(harness)} all
root={rel(root)}
rc=0
qemu-aarch64 -cpu cortex-a35 -L / -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$root/lib:$root/usr/lib" "$root/usr/libexec/muos-save-store/muos-save-store" || rc=$?
[ "$rc" = 64 ]
echo C55_PASS_composed_A35_loader_refuses_missing_arguments
'''
(stage/'check.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',
 (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('check.'+n)).write_text(v)
assert r.returncode==0,(stage,r.stderr[-2500:])
current=inventory(root)
assert all(current.get(n)==v for n,v in original.items()),'C38 inventory changed'
assert inventory(base/'target')==original,'C38 base changed'
added={n:v for n,v in current.items() if n not in original}
files={n for n,v in added.items() if v['type']=='file'};assert files==set(report['target_files'])
assert all(v['type'] in ['file','directory'] for v in added.values())
assert all(v['mode']==0o755 for v in added.values() if v['type']=='directory')
for n in files:assert sha(root/n)==sha(build/'target'/n)
for n,h in sums(root/'usr/libexec/muos-save-store/payload.sha256').items():assert sha(root/n.lstrip('/'))==h
validated=validate(root);assert validated['foundation_files']==97
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
(stage/'expected-tree.json').write_text(json.dumps(current,indent=2)+'\n')
result={**validated,'experiment':'C55_PRIVATE_ADDITIVE_TREE','private_only':True,'device_written':False,
 'source_build_analysis_sha256':sha(build/'analysis.json'),'base_C38_analysis_sha256':sha(base/'analysis.json'),
 'base_C38_image_sha256':prior['image_sha256'],'base_C38_files_changed':0,'added':added,
 'C52_binary_byte_identical':report['C52_binary_byte_identical'],'full_image_built':False,
 'candidate_boot_tested':False,'SDK_config_unchanged':True,
 'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/scripts/phase4_candidate.py',repo/'port/scripts/compose-phase4-rootfs-candidate.py']}}
(stage/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');(area/'latest-composition').write_text(str(stage)+'\n')
print('C55 private tree: 4 new files, C38 foundation unchanged:',stage)
