#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C10 test package: apply the actual Buildroot payload with the C09 RAM harness."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'runtime-profile'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=work/'linux-diagnostic/network-controls._yj3a8oo';m=json.loads((base/'manifest.json').read_text());assert json.loads((base/'analysis.json').read_text())['passed']
checks=Path((area/'latest-checks').read_text().strip());audit=json.loads((checks/'report.json').read_text());assert audit['passed']
kconfig=Path((area/'latest-kconfig').read_text().strip());assert json.loads((kconfig/'report.json').read_text())['passed']
# Consume the recipe-installed payload, after the real post-overlay hook test.
payload=checks/'recipe-target/usr/share/muos-r35s-profile';profile=json.loads((payload/'manifest.json').read_text())
assert len(profile['files'])>=20 and profile['ui_autostart'] is False
stage=Path(tempfile.mkdtemp(prefix='session.',dir=area));pkg=stage/'package';shutil.copytree(base/'package',pkg);shutil.copytree(payload,pkg/'profile')
for n,v in profile['files'].items():assert sha(pkg/'profile/overlay'/n)==v['sha256']
(pkg/'profile-files.txt').write_text(''.join(n+'\n' for n in sorted(profile['files'])))
(pkg/'profile-effective.sha256').write_text(''.join(v['sha256']+'  /'+n+'\n' for n,v in sorted(profile['files'].items())))
dynamic={'opt/muos/config/settings/general/volume','opt/muos/config/settings/general/brightness'}
(pkg/'profile-static.sha256').write_text(''.join(v['sha256']+'  /'+n+'\n' for n,v in sorted(profile['files'].items()) if n not in dynamic))
def one(s,a,b):
 assert s.count(a)==1,a
 return s.replace(a,b)
s=(pkg/'extension.sh').read_text();s=one(s,'c06_before_core() {','c10_c09_before_core() {');s=one(s,'c09_restore() {','c10_c09_restore() {');(pkg/'extension.sh').write_text(s)
shutil.copyfile(repo/'port/device/rk-r35s-p0/network-controls-diagnostic/profile-extension.sh',pkg/'profile-extension.sh')
s=(pkg/'run.sh').read_text();s=one(s,'. "$package/extension.sh"','. "$package/extension.sh"\n. "$package/profile-extension.sh"');s=s.replace('MUOS-R35S-NETWORK-CONTROLS-P4-C09','MUOS-R35S-RUNTIME-PROFILE-P4-C10').replace('C09: CONTROLS / FRONTEND / AUDIO / SSH OK','C10: PROFILE / FRONTEND / AUDIO / SSH OK');(pkg/'run.sh').write_text(s)
s=(pkg/'c06-session.sh').read_text()
a=s.index("    screen 'muOS - R35S / Panel 0\nC06 A:");b=s.index('    c06_help_start || return 1',a);s=s[:a]+s[b:]
a=s.index('    if [ "$ui_result" = 0 ]; then\n        c06_reference_group reference-44');b=s.index('    if [ "$ui_result" = 0 ]; then\n        read now ignored',a);s=s[:a]+s[b:];(pkg/'c06-session.sh').write_text(s)
root=work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted'
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','-v',f'{work}:/work:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
cmd='\n'.join('qemu-aarch64 -cpu cortex-a35 -L /work/'+str(root.relative_to(work))+' /work/'+str((root/'bin/busybox').relative_to(work))+' sh -n /work/'+str((pkg/n).relative_to(work)) for n in ['run.sh','c06-session.sh','extension.sh','profile-extension.sh'])
r=subprocess.run(args+[cmd],capture_output=True,text=True,timeout=60);(stage/'shell.stdout').write_text(r.stdout);(stage/'shell.stderr').write_text(r.stderr);assert r.returncode==0
(pkg/'SHA256SUMS').unlink();(pkg/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(pkg))+'\n' for p in sorted(pkg.rglob('*')) if p.is_file()))
with tarfile.open(stage/'deployment.tar','w') as t:
 for p in pkg.iterdir():t.add(p,arcname=p.name)
meta={**m,'experiment':'MUOS-R35S-RUNTIME-PROFILE-P4-C10','profile_file_count':len(profile['files']),'profile_manifest_sha256':sha(payload/'manifest.json'),'profile_recipe_checks':audit,'profile_kconfig':json.loads((kconfig/'report.json').read_text()),'profile_payload_from_actual_install_macro_and_posthook':True,'reference_beeps':False,'ui_window_seconds':60,'native_tested':False,'deployment_sha256':sha(stage/'deployment.tar'),'sources':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/device/rk-r35s-p0/network-controls-diagnostic/profile-extension.sh']}}
(stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n');(area/'latest-session').write_text(str(stage)+'\n');print('C10 recipe profile RAM test package prepared:',stage)
